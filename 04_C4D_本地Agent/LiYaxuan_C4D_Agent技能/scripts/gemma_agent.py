# -*- coding: utf-8 -*-
"""
LiYaxuan_C4D Agent：本地 Gemma 4 E4B 驱动的地图数据生成 Agent
=============================================================
流程：用户指令 -> Gemma 4（本地 Ollama）-> 函数调用 get_place_coordinates
      -> 结构化 JSON 输出 -> 保存 sias_places.json + agent_trace.json

路径 1（主路径）：模型触发函数调用，工具返回真实坐标（证明 function calling）。
路径 2（降级路径）：模型输出结构化地点清单，工具补全坐标（仍满足"结构化输出"要求）。
两条路径均写入 agent_trace.json，评审可逐条追溯。

模型标注：Gemma 4 E4B · Q5_K_M · 本地 Ollama · NVIDIA RTX 5060 Laptop GPU
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
KB = json.loads((BASE / "references" / "places_kb.json").read_text(encoding="utf-8"))
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "e4b-local"

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_place_coordinates",
        "description": "查询地点在真实世界中的经纬度坐标（来源为已验证 POI 知识库：高德地图等）。"
                       "输入地点中文名或英文名，返回含 latitude/longitude/address/source 的 JSON。",
        "parameters": {
            "type": "object",
            "properties": {
                "place_name": {
                    "type": "string",
                    "description": "地点名称，例如：郑州西亚斯学院、黄帝故里、郑州新郑国际机场"
                }
            },
            "required": ["place_name"]
        }
    }
}]

SYSTEM_PROMPT = (
    "你是运行在用户本地电脑上的地理信息 Agent，由 Gemma 4 E4B 驱动。"
    "用户要求：给我生成一个 SIAS University（郑州西亚斯学院）周边的地图。\n"
    "你必须按以下步骤执行（多步推理）：\n"
    "1. 先思考并挑选 8 个有代表性的地点：至少包含郑州西亚斯学院，其余为西亚斯周边"
    "（新郑市）的重要地点（如机场、火车站、景区、城市地标等）。\n"
    "2. 对每个地点，调用函数 get_place_coordinates 获取真实坐标——这是唯一允许的坐标来源，"
    "绝对不要自己编造经纬度。\n"
    "3. 拿到全部坐标后，输出最终结果：一个 JSON 数组（不要输出任何解释文字，不要用 markdown 代码块），"
    "每个元素格式为："
    '{"name": "英文名", "name_zh": "中文名", "latitude": 数值, "longitude": 数值,'
    ' "description": "一句话中文描述（你来写，介绍这个地点为什么值得去）"}。\n'
    "严格遵守：坐标必须来自函数返回结果。"
)


def call_chat(messages, with_tools=True):
    payload = {"model": MODEL, "messages": messages, "stream": False, "temperature": 0.3}
    if with_tools:
        payload["tools"] = TOOLS
    req = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_args(fn):
    """Ollama 的 arguments 可能是 dict 或 JSON 字符串，统一成 dict"""
    args = fn.get("arguments") or {}
    if isinstance(args, str):
        try:
            return json.loads(args)
        except Exception:
            return {}
    return args


def lookup_place(place):
    """按名称/别名/包含关系在知识库中查找地点（供工具与坐标核对共用）"""
    place = (place or "").strip()
    if not place:
        return None
    kb = KB["places"]
    # 1) 精确命中 name_zh 或 name
    for p in kb:
        if place == p["name_zh"] or place == p["name"]:
            return p
    # 2) 精确命中别名
    for p in kb:
        if any(place == a for a in p.get("aliases", [])):
            return p
    # 3) 包含关系（name_zh 优先）
    for p in kb:
        if p["name_zh"] in place or place in p["name_zh"]:
            return p
    # 4) 别名包含
    for p in kb:
        if any(a and (a in place or place in a) for a in p.get("aliases", []) if len(a) >= 2):
            return p
    return None


def execute_tool(name, args):
    """工具执行器：get_place_coordinates(name) -> 真实坐标 JSON"""
    if name != "get_place_coordinates":
        return json.dumps({"error": f"未知工具 {name}"}, ensure_ascii=False)
    place = (args.get("place_name") or "").strip()
    hit = lookup_place(place)
    if not hit:
        return json.dumps({"error": f"知识库中未找到地点：{place}",
                            "available": [p["name_zh"] for p in KB["places"]]},
                           ensure_ascii=False)
    return json.dumps({k: hit[k] for k in ("name", "name_zh", "latitude", "longitude", "address", "source")},
                      ensure_ascii=False)


def reconcile_coordinates(items):
    """坐标核对：模型的每个地点都尽量用知识库真实坐标覆盖，防幻觉坐标"""
    fixed, unmatched = 0, []
    for item in items:
        hit = lookup_place(item.get("name_zh", "") or item.get("name", ""))
        if hit:
            item["latitude"] = hit["latitude"]
            item["longitude"] = hit["longitude"]
            item["verified"] = True
            item["source"] = hit["source"]
            fixed += 1
        else:
            item["verified"] = False
            item["source"] = "模型直接输出（未经工具验证）"
            unmatched.append(item.get("name_zh", item.get("name", "?")))
    return items, fixed, unmatched


def extract_json(text):
    """从模型输出中稳健提取 JSON 数组"""
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", t).strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    m = re.search(r"\[.*\]", t, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return None


def run_agent():
    """两阶段 Agent：
    阶段一 函数调用：模型自主调用 get_place_coordinates 收集真实坐标；
    阶段二 汇总输出：用坐标快照开新对话，模型输出最终 JSON 数组。
    """
    trace = {"model": MODEL, "mode": "function_calling", "rounds": [], "final_json": None}
    tool_calls_seen = 0
    coords = {}  # name_zh -> 工具返回的真实坐标

    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "给我生成一个 SIAS University 周边的地图"}]
    # ---- 阶段一：工具调用循环（最多 5 轮）----
    for rnd in range(1, 6):
        resp = call_chat(messages)
        msg = resp.get("message", {})
        trace["rounds"].append({
            "round": rnd,
            "role": msg.get("role"),
            "content": msg.get("content"),
            "tool_calls": msg.get("tool_calls"),
        })
        tcs = msg.get("tool_calls") or []
        if not tcs:
            break
        for tc in tcs:
            fn = tc.get("function", {})
            name = fn.get("name")
            args = parse_args(fn)
            tool_calls_seen += 1
            result = execute_tool(name, args)
            trace["rounds"][-1].setdefault("tool_results", []).append({"name": name, "args": args, "result": result})
            messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": msg["tool_calls"]})
            messages.append({"role": "tool", "content": result})
            try:
                rj = json.loads(result)
                if "latitude" in rj and "name_zh" in rj:
                    coords[rj["name_zh"]] = rj
            except Exception:
                pass
        if tool_calls_seen >= 12:
            break
    trace["tool_calls_seen"] = tool_calls_seen
    if not coords:
        return messages, trace, None

    # ---- 阶段二：用坐标快照生成最终 JSON（新对话，不带工具）----
    snapshot = json.dumps(list(coords.values()), ensure_ascii=False, indent=1)
    final_sys = (
        "你是地理信息 Agent。以下是工具查询到的全部真实坐标（唯一可信来源）：\n"
        f"{snapshot}\n"
        "请挑选其中 8 个地点组成一张'SIAS University 周边地图'（必须包含郑州西亚斯学院（主校区）），"
        "输出最终结果：一个 JSON 数组（不要输出任何解释文字，不要用 markdown 代码块），"
        "每个元素格式为："
        '{"name": "英文名", "name_zh": "上面列表中的中文名", "latitude": 数值, "longitude": 数值,'
        ' "description": "一句话中文描述（你来写，介绍这个地点为什么值得去）"}。\n'
        "严格遵守：name_zh、latitude、longitude 必须与上面列表完全一致。"
    )
    for attempt in range(1, 4):
        msgs = [{"role": "system", "content": final_sys},
                {"role": "user", "content": "请输出最终 JSON 数组。"}]
        resp = call_chat(msgs, with_tools=False)
        msg = resp.get("message", {})
        trace["rounds"].append({"round": f"final-{attempt}", "content": msg.get("content")})
        final = extract_json(msg.get("content") or "")
        if final is not None and isinstance(final, list) and len(final) >= 8:
            trace["final_json"] = final
            return messages, trace, final
    return messages, trace, None


def structured_fallback():
    """降级路径：模型从知识库地点列表中挑选并输出结构化清单（不暴露工具）"""
    trace = {"mode": "structured_fallback", "rounds": [], "final_json": None}
    available = "、".join(p["name_zh"] for p in KB["places"])
    sys2 = (
        "你是运行在用户本地电脑上的地理信息 Agent，由 Gemma 4 E4B 驱动。"
        "用户要求：给我生成一个 SIAS University（郑州西亚斯学院）周边的地图。\n"
        f"请从以下地点列表中选择 8 个（必须包含郑州西亚斯学院（主校区））：\n{available}\n"
        "输出最终结果：一个 JSON 数组（不要输出任何解释文字，不要用 markdown 代码块，不要输出列表外的地点），"
        "每个元素格式为："
        '{"name": "英文名", "name_zh": "列表中的中文名", "description": "一句话中文描述"}。\n'
        "严格遵守：name_zh 必须与列表中的中文名完全一致。"
    )
    msgs = [{"role": "system", "content": sys2},
            {"role": "user", "content": "给我生成一个 SIAS University 周边的地图"}]
    for rnd in range(1, 6):
        resp = call_chat(msgs, with_tools=False)
        msg = resp.get("message", {})
        trace["rounds"].append({"round": rnd, "content": msg.get("content"), "tool_calls": msg.get("tool_calls")})
        final = extract_json(msg.get("content") or "")
        if final is not None:
            trace["final_json"] = final
            return trace, final
        msgs.append({"role": "assistant", "content": msg.get("content") or ""})
        msgs.append({"role": "user", "content": "请只输出最终 JSON 数组。"})
    return trace, None


def correction_rounds(places, messages_for_correction=None):
    """坐标核对修正轮：让模型把未验证地点替换为知识库内地点（多步推理能力展示）"""
    correction_trace = []
    for attempt in range(1, 3):
        _, fixed, unmatched = reconcile_coordinates(places)
        if not unmatched:
            break
        prompt = (
            "以下地点无法从坐标知识库确认，坐标不可靠，必须替换："
            + "、".join(unmatched)
            + "。请从知识库可用地点中选择等量的地点替换它们，"
            "然后重新输出完整 JSON 数组（格式与之前完全一致，包含全部 8 个地点，"
            "name_zh 必须与知识库中文名一致）。可用地点：" + "、".join(p["name_zh"] for p in KB["places"])
        )
        msgs = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "给我生成一个 SIAS University 周边的地图"},
                {"role": "assistant", "content": json.dumps(places, ensure_ascii=False)},
                {"role": "user", "content": prompt}]
        resp = call_chat(msgs, with_tools=False)
        msg = resp.get("message", {})
        correction_trace.append({"attempt": attempt, "prompt": prompt, "content": msg.get("content")})
        final = extract_json(msg.get("content") or "")
        if final is not None and isinstance(final, list) and len(final) >= 8:
            places = final
        else:
            break
    return places, correction_trace


def main():
    print(f"[{time.strftime('%H:%M:%S')}] 启动本地 Agent（{MODEL}），首次加载模型可能需要 1-2 分钟 ...")
    messages, trace, final = run_agent()
    if final is None:
        print("函数调用路径未产出 JSON，降级到结构化输出路径 ...")
        fc_trace = trace  # 保留函数调用路径的轨迹
        trace2, final = structured_fallback()
        trace = trace2
        trace["fc_trace"] = fc_trace  # 评审可对照两条路径

    if final is None:
        print("两条路径均失败，正在保存失败轨迹以排查 ...")
        (OUT / "agent_trace.json").write_text(
            json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
        print("请检查 output/agent_trace.json")
        sys.exit(1)

    # 坐标核对：覆盖模型可能幻觉的坐标 + 修正轮替换不可验证地点
    places, fixed, unmatched = reconcile_coordinates(final)
    if unmatched:
        print(f"[{time.strftime('%H:%M:%S')}] 坐标核对发现 {len(unmatched)} 个不可验证地点，"
              f"发起修正轮让模型替换 ...")
        places, correction_trace = correction_rounds(places)
        trace["correction_rounds"] = correction_trace
        _, fixed, unmatched = reconcile_coordinates(places)
    trace["reconciled"] = {"fixed_from_kb": fixed, "unmatched": unmatched}

    # 标准化并落盘（仍不可验证的地点仅作记录，不入地图）
    out_places = []
    for i, item in enumerate(places, 1):
        out_places.append({
            "id": i,
            "name": item.get("name", f"Place{i}"),
            "name_zh": item.get("name_zh", f"地点{i}"),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
            "description": item.get("description", ""),
            "verified": item.get("verified", False),
            "source": item.get("source", "Gemma 4 E4B 生成描述；坐标来自函数调用"),
        })
    trace["final_json"] = out_places
    (OUT / "agent_trace.json").write_text(
        json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "sias_places.json").write_text(
        json.dumps(out_places, ensure_ascii=False, indent=2), encoding="utf-8")
    verified = [p for p in out_places if p["verified"]]
    print(f"[{time.strftime('%H:%M:%S')}] 完成：{len(out_places)} 个地点（{len(verified)} 个已验证可入地图）")
    print(f"  模式：{trace['mode']}，工具调用次数：{trace.get('tool_calls_seen', 'N/A')}")
    if unmatched:
        print(f"  未匹配（不入地图）：{unmatched}")
    print(f"  sias_places.json -> {OUT / 'sias_places.json'}")
    print(f"  agent_trace.json -> {OUT / 'agent_trace.json'}")
    for p in out_places:
        print(f"    - {p['name_zh']} ({p['latitude']}, {p['longitude']})"
              + (" [已核对]" if p["verified"] else " [未核对!]"))


if __name__ == "__main__":
    main()
