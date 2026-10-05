#!/usr/bin/env python3
"""
tools.py — Agent 工具定义（function calling schema）
=============================================================
C4D 技能：向本地 Gemma 4 暴露可调用的函数工具，
演示"模型调用多个函数"的 Agent 能力（Level 3 多工具调用）。
"""

# Ollama / OpenAI tools schema（Gemma 4 原生函数调用）

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_sias_location_info",
            "description": "查询 SIAS University（郑州西亚斯学院）校内或周边地点信息，用于生成地图标记。",
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name": {
                        "type": "string",
                        "description": "地点名称（中英文均可），如 '图书馆'、'喷泉广场'。"
                    }
                },
                "required": ["place_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "register_map_marker",
            "description": "向地图注册一个标记点。模型应在获得地点坐标后调用此函数提交标记。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "地点英文名"},
                    "name_zh": {"type": "string", "description": "地点中文名"},
                    "latitude": {"type": "number", "description": "纬度"},
                    "longitude": {"type": "number", "description": "经度"},
                    "description": {"type": "string", "description": "一句话描述"}
                },
                "required": ["name", "name_zh", "latitude", "longitude", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_route_time",
            "description": "估算两个地点之间的步行时间（分钟），用于地图导览提示。",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_place": {"type": "string", "description": "起点名称"},
                    "to_place": {"type": "string", "description": "终点名称"}
                },
                "required": ["from_place", "to_place"]
            }
        }
    },
]


def execute_tool(name: str, arguments: dict) -> dict:
    """本地执行工具（确定性实现，非模型幻觉）。"""
    args = json_loads_safe(arguments)
    if name == "get_sias_location_info":
        return {"status": "ok", "hint": "请根据你对 SIAS University 的了解回答，并给出大致经纬度（Xinzheng 约 34.40N, 113.73E）。"}
    if name == "register_map_marker":
        return {"status": "ok", "message": f"已登记标记点 {args.get('name_zh', args.get('name', '?'))}。"}
    if name == "get_route_time":
        return {"status": "ok", "minutes": 8}
    return {"status": "error", "message": f"未知工具 {name}"}


import json as _json


def json_loads_safe(arguments) -> dict:
    if isinstance(arguments, dict):
        return arguments
    try:
        return _json.loads(arguments) if isinstance(arguments, str) else {}
    except Exception:
        return {}
