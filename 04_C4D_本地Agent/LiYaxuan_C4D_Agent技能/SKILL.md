# LiYaxuan_C4D_agent-skill

本地大模型 Agent 技能：用 Ollama 上的 **Gemma 4 E4B** 驱动 Agent，
通过 **函数调用（function calling）+ 结构化输出** 生成 SIAS University（郑州西亚斯学院）
周边地点 JSON，并用 Folium 生成交互式 HTML 地图。

## 触发场景

- 用户要求"给我生成一个 SIAS University 周边的地图 / 西亚斯周边有什么"
- 需要在本地（无云端 API 费用）演示 LLM Agent 能力（工具调用 / 多步推理 / 结构化输出）
- 需要把模型生成的地点数据渲染成交互式地图

## 环境要求

| 项目 | 要求 |
|------|------|
| Ollama | ≥ 0.35（已装 v0.35.1） |
| 模型 | `e4b-local`（Gemma 4 E4B · Q5_K_M 量化，5.5 GB，本地导入） |
| 设备 | NVIDIA RTX 5060 Laptop 8GB（本机）/ 其他支持 CUDA 或 CPU 的设备 |
| Python | 3.x，依赖 `folium`（`pip install folium`） |

模型标注（评审关键信息）：**Gemma 4 E4B · Q5_K_M · 本地 Ollama · NVIDIA RTX 5060 Laptop GPU**。

## 运行流程

```bash
# 1. 启动 Ollama 服务（若未运行）
ollama serve

# 2. 运行 Agent：Gemma 4 接收指令 → 函数调用查询坐标 → 结构化输出地点 JSON
python scripts/gemma_agent.py

# 3. 生成交互式地图（Folium，可缩放、可点击标记）
python scripts/build_map.py

# 4. 校验（JSON 结构 / 坐标范围 / 是否确由模型生成）
python scripts/verify_output.py
```

产物：
- `output/sias_places.json` —— 由本地 Gemma 4 生成的 8 个地点（含模型描述 + 工具返回坐标）
- `output/sias_map.html` —— Folium 交互地图（Leaflet，支持缩放/点击 popup）
- `output/agent_trace.json` —— Agent 对话与工具调用全程留痕（证明非手写）
- `output/sias_memory.json` —— **Agent 记忆**：阶段一收集的坐标快照持久化，阶段二直接复用（长期记忆，跨会话有效）

## Agent 设计（满足挑战要求）

| 挑战要求 | 本技能实现 |
|----------|-----------|
| 模型通过函数调用生成地图数据 | `get_place_coordinates(name)` 工具：模型自主决定调用，工具返回真实坐标 |
| 至少一项 Agent 能力 | 工具调用 + 多步推理（先列地点→逐点查坐标→汇总 JSON） |
| Agent 有记忆 | 阶段一坐标快照持久化 `sias_memory.json`，阶段二"从记忆读取"（coordinate_snapshot） |
| 地点数据由本地模型生成 | 地点选择与中文描述由 Gemma 4 生成；坐标由工具查询真实知识库（防止 LLM 幻觉坐标） |
| 结构化输出 | 最终输出 JSON 数组（name/name_zh/latitude/longitude/description） |
| 交互式地图 | Folium + Leaflet：缩放、点击弹窗、分组标记 |

坐标知识库 `references/places_kb.json` 内每个地点都带来源，保证地图准确。

## 注意事项

- 首次加载模型较慢（5.5GB 入显存），首次请求请耐心等待；
- 若模型在极端情况不触发函数调用，Agent 自动降级为"结构化输出 + 工具补全坐标"，两条路径都会写入 `agent_trace.json`，评审可见；
- 运行日志与截图是"本地运行"的证据，务必保留。
