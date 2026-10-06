# -*- coding: utf-8 -*-
"""用 Folium 把 Gemma 4 生成的地点 JSON 渲染成交互式 HTML 地图。"""
import json
from pathlib import Path

import folium

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "output"
places = json.loads((OUT / "sias_places.json").read_text(encoding="utf-8"))

# 地图中心取所有地点的平均坐标
lat = sum(p["latitude"] for p in places) / len(places)
lon = sum(p["longitude"] for p in places) / len(places)

# 底图：高德矢量瓦片（国内可访问；OSM 在本机网络下不可达，见 AI 日志）
AMAP_TILES = ("https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}")

m = folium.Map(location=[lat, lon], zoom_start=11, tiles=None)
folium.TileLayer(AMAP_TILES, attr="© 高德地图", name="高德地图").add_to(m)
m.get_root().html.add_child(folium.Element(
    "<h3 style='text-align:center;margin:8px 0;font-family:sans-serif;'>"
    "SIAS University 周边地图 · 数据由本地 Gemma 4 E4B 生成</h3>"))

for p in places:
    popup_html = (
        f"<b>{p['name_zh']}</b><br>"
        f"{p['name']}<br>"
        f"坐标: {p['latitude']:.5f}, {p['longitude']:.5f}<br>"
        f"<span style='color:#555'>{p['description']}</span><br>"
        f"<small style='color:#999'>坐标来源: {p.get('source', '函数调用')}</small>")
    folium.Marker(
        location=[p["latitude"], p["longitude"]],
        popup=folium.Popup(popup_html, max_width=320),
        tooltip=p["name_zh"],
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(m)

html_path = OUT / "sias_map.html"
m.save(str(html_path))
print(f"地图已生成: {html_path}（{len(places)} 个标记，可缩放/点击）")
