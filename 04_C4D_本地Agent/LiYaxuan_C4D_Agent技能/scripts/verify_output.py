# -*- coding: utf-8 -*-
"""校验 Gemma 4 Agent 的产出：
1) sias_places.json 结构完整、字段齐全；
2) 坐标在真实世界范围内（纬度 20-50，经度 100-130，河南新郑附近）；
3) 必须包含 SIAS University 主校区；
4) agent_trace.json 证明数据确由本地模型生成（含调用轨迹）。
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "output"

failures = []


def check(cond, name):
    print(("  ✅ " if cond else "  ❌ ") + name)
    if not cond:
        failures.append(name)


def main():
    places = json.loads((OUT / "sias_places.json").read_text(encoding="utf-8"))
    trace = json.loads((OUT / "agent_trace.json").read_text(encoding="utf-8"))

    print(f"校验地点数: {len(places)}（要求 ≥ 8）")
    check(len(places) >= 8, "至少 8 个地点")

    for p in places:
        need = ("name", "name_zh", "latitude", "longitude", "description")
        check(all(k in p and p[k] not in (None, "") for k in need),
              f"{p.get('name_zh', '?')}: 字段齐全")
        lat, lon = p["latitude"], p["longitude"]
        check(20 < lat < 50 and 100 < lon < 130, f"{p.get('name_zh', '?')}: 坐标在中国范围")
        check(lat and lon, f"{p.get('name_zh', '?')}: 坐标非空")

    check(any("西亚斯" in p["name_zh"] for p in places), "包含 SIAS University（郑州西亚斯学院）")

    mode = trace.get("mode")
    check(mode in ("function_calling", "structured_fallback"), f"trace 模式: {mode}")
    rounds = trace.get("rounds", [])
    tool_rounds = [r for r in rounds if r.get("tool_calls")]
    check(rounds and (trace.get("tool_calls_seen", 0) > 0 or len(tool_rounds) > 0 or mode == "structured_fallback"),
          "存在模型调用轨迹（工具调用或结构化输出）")
    print(f"  （轨迹轮次 {len(rounds)}，工具调用轮 {len(tool_rounds)}，"
          f"工具调用次数 {trace.get('tool_calls_seen', 'N/A')}）")
    check(trace.get("final_json") is not None, "final_json 已记录")

    print("=" * 40)
    if failures:
        print(f"校验失败 {len(failures)} 项")
        sys.exit(1)
    print("全部校验通过 ✔")


if __name__ == "__main__":
    main()
