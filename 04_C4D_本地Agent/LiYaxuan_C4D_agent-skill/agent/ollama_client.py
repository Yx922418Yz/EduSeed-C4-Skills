#!/usr/bin/env python3
"""
ollama_client.py — 本地 Ollama（OpenAI 兼容 API）客户端封装
=============================================================
C4D 技能：通过 http://localhost:11434/v1/chat/completions 调用本地 Gemma 4，
零云端依赖。支持：
  - 普通对话（chat）
  - 严格结构化 JSON 输出（structured_json）
  - 原生函数调用 / 工具调用（chat_with_tools）
  - 推理速度统计（tok/s）
"""

import json
import time
import urllib.request
import urllib.error

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "gemma4:e4b"


class OllamaClientError(RuntimeError):
    """Ollama 连接或响应错误。"""


class OllamaClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, model: str = DEFAULT_MODEL,
                 timeout: int = 600):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    # ─────────────────────────────────────────────
    # 底层请求
    # ─────────────────────────────────────────────
    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise OllamaClientError(
                f"无法连接本地 Ollama（{url}）：{e}\n"
                "请确认：1) Ollama 已启动；2) 已执行 `ollama pull gemma4:e4b`；"
                "3) 未占用 11434 端口。"
            ) from e
        except json.JSONDecodeError as e:
            raise OllamaClientError(f"Ollama 返回了非 JSON 响应：{e}") from e

    def _complete(self, messages: list, *, json_mode: bool = False,
                  tools: list = None, temperature: float = 0.2) -> dict:
        """调用 chat/completions，返回 (message_dict, usage, elapsed)。"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
        }
        if json_mode:
            payload["format"] = "json"          # Ollama 原生 JSON 模式
        if tools:
            payload["tools"] = tools

        start = time.time()
        resp = self._post("/chat/completions", payload)
        elapsed = time.time() - start

        if not resp.get("choices"):
            raise OllamaClientError(f"Ollama 未返回 choices：{resp}")

        message = resp["choices"][0]["message"]
        usage = resp.get("usage", {})
        return message, usage, elapsed

    # ─────────────────────────────────────────────
    # 对外能力
    # ─────────────────────────────────────────────
    def chat(self, system: str, user: str, *, temperature: float = 0.2) -> tuple[str, float]:
        """普通对话。返回 (文本, tok/s)。"""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        msg, usage, elapsed = self._complete(messages, temperature=temperature)
        text = (msg.get("content") or "").strip()
        return text, self._tok_per_sec(usage, elapsed)

    def structured_json(self, system: str, user: str, *, temperature: float = 0.1) -> tuple[list, float]:
        """
        严格结构化输出：要求模型返回合法 JSON（数组）。
        返回 (解析后的对象, tok/s)。自动清理 markdown 代码围栏。
        """
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        msg, usage, elapsed = self._complete(messages, json_mode=True, temperature=temperature)
        raw = (msg.get("content") or "").strip()
        parsed = self._parse_json(raw)
        return parsed, self._tok_per_sec(usage, elapsed)

    def chat_with_tools(self, system: str, user: str, tools: list,
                        *, temperature: float = 0.2) -> tuple[dict, float]:
        """工具调用（function calling）。返回 (message, tok/s)。"""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        msg, usage, elapsed = self._complete(messages, tools=tools, temperature=temperature)
        return msg, self._tok_per_sec(usage, elapsed)

    # ─────────────────────────────────────────────
    # 工具函数
    # ─────────────────────────────────────────────
    @staticmethod
    def _tok_per_sec(usage: dict, elapsed: float) -> float:
        total = usage.get("total_tokens") or 0
        return round(total / elapsed, 1) if elapsed > 0 else 0.0

    @staticmethod
    def _parse_json(raw: str):
        """解析模型输出的 JSON，兼容代码围栏与前后杂质文本。"""
        s = raw.strip()
        if s.startswith("```"):
            lines = s.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            s = "\n".join(lines).strip()
        # 截取第一个 [ 或 { 到最后一个 ] 或 }
        start = min([i for i in (s.find("["), s.find("{")) if i >= 0] or [0])
        end = max([i for i in (s.rfind("]"), s.rfind("}")) if i >= 0] or [len(s)])
        s = s[start:end + 1]
        return json.loads(s)


if __name__ == "__main__":
    # 自检：连接本地模型并做一次简单对话
    c = OllamaClient()
    try:
        text, tps = c.chat("You are a helpful assistant.", "Say OK in one word.")
        print(f"模型响应: {text}")
        print(f"推理速度: {tps} tok/s")
    except OllamaClientError as e:
        print(f"[自检失败] {e}")
        raise SystemExit(1)
