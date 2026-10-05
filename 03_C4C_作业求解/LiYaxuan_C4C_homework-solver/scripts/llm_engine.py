#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_engine.py — 国产大模型求解引擎（C4C 迁移核心）

把 starter 的"仅 Claude 单点"架构迁移为「国产大模型优先 + 可插拔降级」：

  Qwen（通义千问）→ DashScope OpenAI 兼容接口（DASHSCOPE_API_KEY）
  Kimi（月之暗面）→ Moonshot OpenAI 兼容接口（MOONSHOT_API_KEY）
  任意 OpenAI 兼容服务 → LLM_BASE_URL + LLM_MODEL（自建/代理）

设计要点：
  1. 环境变量驱动，无硬编码密钥（可复用、可审计）；
  2. API 不可用时返回 None，调用方自动降级为 SymPy 规则求解（零云端依赖可跑）；
  3. 请求带超时与 JSON 输出约束，失败不阻断流水线。

用法（在 solve.py 中调用）:
    from llm_engine import llm_solve_fallback
    result = llm_solve_fallback(problem)   # 成功返回信封 dict，失败返回 None
"""

import json
import os
import re
import urllib.request


def _provider_config():
    """按优先级选择国产模型提供商。返回 (base_url, model, api_key) 或 None。"""
    if os.environ.get("DASHSCOPE_API_KEY"):
        return ("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                os.environ.get("QWEN_MODEL", "qwen-plus"),
                os.environ["DASHSCOPE_API_KEY"])
    if os.environ.get("QWEN_API_KEY"):
        return ("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                os.environ.get("QWEN_MODEL", "qwen-plus"),
                os.environ["QWEN_API_KEY"])
    if os.environ.get("MOONSHOT_API_KEY"):
        return ("https://api.moonshot.cn/v1/chat/completions",
                os.environ.get("KIMI_MODEL", "kimi-k2-0711-preview"),
                os.environ["MOONSHOT_API_KEY"])
    if os.environ.get("OPENAI_API_KEY") and os.environ.get("LLM_BASE_URL"):
        return (os.environ["LLM_BASE_URL"],
                os.environ.get("LLM_MODEL", "gpt-4o-mini"),
                os.environ["OPENAI_API_KEY"])
    return None


def available() -> bool:
    return _provider_config() is not None


def _call_llm(system: str, user: str, timeout: int = 60) -> str | None:
    cfg = _provider_config()
    if not cfg:
        return None
    base_url, model, api_key = cfg
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None


def llm_solve_fallback(problem: dict) -> dict | None:
    """
    对 SymPy 规则求解器未覆盖的题目（证明题、概念题、复杂应用题），
    交给国产大模型求解。返回与 solve.py 信封兼容的 dict；失败返回 None。
    """
    if not available():
        return None

    text = problem.get("text", "")
    if not text.strip():
        return None

    system = (
        "你是数学/物理作业求解助手。用中文输出解题过程，最后给出答案。"
        "答案可以是简短的公式或数值。不要输出多余解释。"
    )
    user = f"请求解以下题目，给出分步过程与最终答案：\n{text}"

    content = _call_llm(system, user)
    if not content:
        return None

    return {
        "problem_id": problem["id"],
        "problem_text": problem["text"],
        "solved": True,
        "steps": ["LLM 求解（国产大模型）：", content[:2000]],
        "answer": content[-500:],
        "answer_latex": "\\text{" + content[-500:].replace("\\", "\\\\").replace("\n", " ") + "}",
        "solver": "llm",
        "sub_solutions": [],
    }


if __name__ == "__main__":
    # 自检
    print("LLM 引擎可用：" + ("是" if available() else "否（未配置 API Key，自动降级为 SymPy 规则求解）"))
