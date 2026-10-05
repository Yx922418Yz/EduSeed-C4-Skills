#!/usr/bin/env python3
"""
map_renderer.py — 交互式地图渲染（Folium）
=============================================================
把本地 Gemma 4 生成的地点 JSON 渲染为 Leaflet 交互式 HTML 地图：
  - 可缩放、可拖拽
  - 标记点可点击（popup：名称 + 描述 + 坐标）
  - tooltip 悬浮提示
  - 中英双语标注（Level 3 多语言地图）
"""

import json
import subprocess
import sys
from pathlib import Path

try:
    import folium
except ImportError:
    print("需要 folium: python -m pip install folium")
    sys.exit(1)


def validate_locations(data: list) -> list:
    """校验模型输出的地点数据，过滤非法项。"""
    valid = []
    for loc in data:
        if not isinstance(loc, dict):
            continue
        lat = loc.get("latitude")
        lng = loc.get("longitude")
        try:
            lat = float(lat)
            lng = float(lng)
        except (TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            continue
        if abs(lat) < 1e-6 and abs(lng) < 1e-6:
            continue  # 全零坐标视为无效
        loc["latitude"] = lat
        loc["longitude"] = lng
        valid.append(loc)
    return valid


def render_map(locations: list, output_html: str,
               center: tuple = (34.3950, 113.7350), zoom: int = 15,
               title: str = "SIAS University 周边地图（由本地 Gemma 4 生成）") -> str:
    """
    生成交互式地图 HTML。
    返回保存路径。
    """
    m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap")

    # 标题
    title_html = (
        f'<div style="position:fixed;top:10px;left:50%;transform:translateX(-50%);'
        f'z-index:9999;background:rgba(255,255,255,.92);padding:8px 18px;'
        f'border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.2);'
        f'font:600 16px/1.4 sans-serif;text-align:center;">'
        f'{title}</div>'
    )
    m.get_root().html.add_child(folium.Element(title_html))

    # SIAS University 主标记
    folium.Marker(
        [34.3935, 113.7338],
        popup=(
            "<b>SIAS University 郑州西亚斯学院</b><br>"
            "河南省郑州市新郑市人民路168号<br>"
            "坐标: 34.3935, 113.7338"
        ),
        tooltip="SIAS University 🏫",
        icon=folium.Icon(color="red", icon="university", prefix="fa"),
    ).add_to(m)

    # 模型生成的标记点
    for loc in locations:
        name = loc.get("name", "")
        name_zh = loc.get("name_zh", "")
        desc = loc.get("description", "")
        lat = loc["latitude"]
        lng = loc["longitude"]

        label = name_zh or name
        popup_html = (
            f"<b>{label}</b><br>"
            f"{desc}<br>"
            f"<small>{name}<br>坐标: {lat:.5f}, {lng:.5f}</small>"
        )
        folium.Marker(
            [lat, lng],
            popup=popup_html,
            tooltip=label,
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(m)

    # 缩放控件与比例尺
    folium.plugins.Fullscreen().add_to(m)
    m.fit_bounds([[min(l["latitude"] for l in locations) - 0.01,
                   min(l["longitude"] for l in locations) - 0.01],
                  [max(l["latitude"] for l in locations) + 0.01,
                   max(l["longitude"] for l in locations) + 0.01]]) \
        if locations else None

    out = Path(output_html)
    out.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out))
    return str(out)


def open_in_browser(html_path: str) -> None:
    """在默认浏览器打开地图（用于截图验证）。"""
    import webbrowser
    webbrowser.open(Path(html_path).resolve().as_uri())


if __name__ == "__main__":
    # 自检：用内置示例数据渲染
    demo = [
        {"name": "Demo Library", "name_zh": "示例图书馆", "latitude": 34.3930,
         "longitude": 113.7345, "description": "自检数据"},
    ]
    p = render_map(demo, "demo_map.html")
    print(f"自检地图已生成: {p}")
