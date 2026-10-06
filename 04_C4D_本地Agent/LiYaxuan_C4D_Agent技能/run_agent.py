#!/usr/bin/env python3
"""
run_agent.py — C4D 主入口：本地 Gemma 4 Agent → 交互式地图
=============================================================
一条命令完成：
  1. 检查本地 Ollama + e4b-local（Gemma 4 E4B Q5_K_M，本地导入）
  2. 让本地模型生成 SIAS University 周边地点 JSON（严格结构化输出）
  3. 展示一次函数调用（function calling）——Agent 能力证据
  4. 校验地点数据
  5. 用 Folium 渲染交互式 HTML 地图
  6. 保存模型输出日志 + 性能统计

用法:
  python run_agent.py [--model e4b-local] [--out 输出目录] [--open]
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent.ollama_client import OllamaClient, OllamaClientError
from agent.tools import TOOLS
from agent import map_renderer

# ─────────────────────────────────────────────
# 提示词（强制结构化 JSON）
# ─────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a geography assistant for SIAS University (郑州西亚斯学院, 河南省郑州市新郑市). "
    "You know the campus and its surroundings very well. "
    "IMPORTANT: Always respond with a valid JSON array only, no markdown, no extra text. "
    "Each element must have exactly these fields: "
    "name (English), name_zh (Chinese), latitude (number), longitude (number), description (one sentence in Chinese). "
    "Coordinates must be real and plausible for Xinzheng, Henan (around 34.39N, 113.73E)."
)

USER_PROMPT = (
    "List 8 notable locations at or near SIAS University in Xinzheng, Henan, China. "
    "Include the university's main gate, library, gymnasium, student dormitory, teaching buildings, "
    "dining hall, fountain plaza, and one famous nearby place. "
    "Return a JSON array with fields: name, name_zh, latitude, longitude, description."
)


def check_ollama(model: str) -> None:
    """快速连接测试。"""
    c = OllamaClient(model=model)
    text, tps = c.chat(
        "You are a tiny test assistant. Reply with exactly: READY",
        "Are you ready?",
    )
    print(f"[检查] 本地 Ollama 连接成功 | 模型: {model}")
    print(f"[检查] 测试响应: {text[:60]} | {tps} tok/s")


def main():
    parser = argparse.ArgumentParser(description="本地 Gemma 4 Agent → SIAS 交互地图")
    parser.add_argument("--model", default="e4b-local", help="Ollama 模型名（Gemma 4 E4B Q5_K_M 本地导入）")
    parser.add_argument("--out", default=".", help="输出目录")
    parser.add_argument("--open", action="store_true", help="生成后打开浏览器")
    parser.add_argument("--skip-check", action="store_true", help="跳过连通性测试")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    client = OllamaClient(model=args.model)

    # 1. 连通性检查
    if not args.skip_check:
        try:
            check_ollama(args.model)
        except OllamaClientError as e:
            print(f"[错误] {e}")
            sys.exit(1)

    # 2. 结构化输出：生成地点数据
    print("\n[Step 1] 请求本地模型生成地点 JSON（结构化输出）...")
    t0 = time.time()
    locations, tps = client.structured_json(SYSTEM_PROMPT, USER_PROMPT)
    gen_seconds = time.time() - t0
    print(f"[Step 1] 模型返回 {len(locations)} 个地点 | 推理速度 {tps} tok/s | 耗时 {gen_seconds:.1f}s")

    # 3. 函数调用演示（Agent 能力）
    print("\n[Step 2] 函数调用演示（function calling）...")
    tool_msg, tps2 = client.chat_with_tools(
        "You are a helpful campus navigation agent. When asked about a place, call get_sias_location_info; "
        "after you know its coordinates, call register_map_marker to submit it.",
        "请查一下 SIAS University 图书馆的信息，并登记为地图标记。",
        TOOLS,
    )
    tool_calls = tool_msg.get("tool_calls") or []
    print(f"[Step 2] 模型发起 {len(tool_calls)} 次工具调用")
    for tc in tool_calls:
        fn = tc.get("function", {})
        print(f"        → {fn.get('name')}({json.dumps(fn.get('arguments', {}), ensure_ascii=False)})")
    if not tool_calls:
        print("        （模型未发起工具调用——记录于日志，供质量评估）")

    # 4. 校验地点
    print("\n[Step 3] 校验地点数据...")
    valid = map_renderer.validate_locations(locations)
    print(f"[Step 3] 有效地点 {len(valid)}/{len(locations)}")
    if len(valid) < 5:
        print("[警告] 有效地点少于 5 个，地图标记偏少。")
    for v in valid:
        print(f"   - {v.get('name_zh', v.get('name'))} ({v['latitude']:.4f}, {v['longitude']:.4f})")

    # 5. 渲染地图
    print("\n[Step 4] 渲染交互式地图（Folium / Leaflet）...")
    html_path = map_renderer.render_map(valid, out_dir / "LiYaxuan_C4D_map.html")
    print(f"[Step 4] 地图已生成: {html_path}")

    # 6. 保存日志与性能数据
    log = {
        "model": args.model,
        "runtime": "Ollama (OpenAI-compatible API)",
        "generated_by": "local e4b-local (Gemma 4 E4B Q5_K_M)",
        "step1_structured_output": {
            "n_locations_raw": len(locations),
            "n_locations_valid": len(valid),
            "tokens_per_sec": tps,
            "elapsed_seconds": round(gen_seconds, 2),
        },
        "step2_function_calling": {
            "n_tool_calls": len(tool_calls),
            "tools": [tc.get("function", {}).get("name") for tc in tool_calls],
        },
        "locations": valid,
    }
    log_path = out_dir / "LiYaxuan_C4D_模型输出日志.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[完成] 模型输出日志: {log_path}")

    if args.open:
        map_renderer.open_in_browser(str(html_path))
    print(f"\n✅ 全部完成。地图: {html_path}")


if __name__ == "__main__":
    main()
