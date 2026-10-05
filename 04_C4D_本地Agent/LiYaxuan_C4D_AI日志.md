# LiYaxuan C4D AI 日志

> 挑战：C4D 本地大模型 Agent 技能
> 记录：AI 怎么用的、迭代了几轮、踩了什么坑、我做了什么。
> 本日志按时间线如实记录，包括失败与降级。

## 一、使用的 AI 工具

| 工具 | 用途 |
|------|------|
| 豆包（当前会话 Agent） | 主开发：方案设计、代码生成、调试、文档撰写 |
| 官方 C4D.pdf / C4D 补充说明.pdf | 需求与推荐技术栈 |
| 高德地图 POI / 河南省机场集团 / 卫星地图 | 坐标知识库逐条查证 |
| Ollama + Gemma 4 E4B（本地） | 挑战本体：本地模型驱动 Agent |

## 二、时间线

### 18:30 — 环境准备（多次换路）

| 尝试 | 结果 | 换路 |
|------|------|------|
| Ollama 官方安装包直下 | 极慢（~2MB/30s 停滞） | 改用 `winget install Ollama.Ollama`（1.58GB 秒下）✅ |
| `ollama pull gemma4:e4b`（官方仓库） | 拉取完成但 **blob 损坏**：`unsupported GGUF contains duplicate tensor` | 删除模型，改用 hf-mirror 直连 unsloth GGUF |

**教训**：本地大模型的第一坑是"下载渠道"——官方仓库不一定快、甚至可能损坏；
hf-mirror 直连 + Modelfile 本地导入是可靠备选。

### 19:00 — 发现首轮拉取损坏（DEBUG 日志定位）

- 现象：`/api/chat` 返回 500；
- 定位：开启 `OLLAMA_DEBUG=1` 前台跑 `ollama serve`，日志显示
  `failed to load model metadata error="unsupported GGUF contains duplicate tensor \"\""`；
- 处理：`ollama rm gemma4:e4b`，重拉仍只有 89KB/s（预计 16 小时）→ 放弃官方仓库；
- 启动 hf-mirror GGUF 直连（Q5_K_M，5.11GB）。

### 19:05-19:30 — Agent 技能开发（豆包生成 + 我审改）

- 设计：函数调用 `get_place_coordinates` + 结构化输出 + 双路径降级 + 全程留痕；
- 坐标知识库：8 个地点经纬度逐条联网查证（高德 POI、河南省机场集团、卫星地图），
  每点标注来源；
- 产出：`gemma_agent.py` / `build_map.py` / `verify_output.py` / SKILL.md / Modelfile。

### [完成] 19:30-20:10 — 模型导入、Agent 调试与地图生成

**19:29 首次导入失败（invalid model name）**
- `ollama create` 的 Modelfile 里 `FROM ./models/...` 相对路径按服务端 CWD 解析失败
  → 服务端把 FROM 当模型名 → 400；
- 修复：临时 Modelfile 用绝对路径，导入成功（e4b-local，5.5GB）。

**19:30 首次 Agent 运行：两条路径全失败**
- 根因 1：Ollama 返回的 tool `arguments` 是 **dict**（不是字符串），
  我代码里 `json.loads(arguments)` 抛 TypeError → 参数变空 → 工具全部返回"未找到"；
- 根因 2：模型拿到坐标后持续调用工具、不输出最终 JSON（循环与汇总耦合）；
- 修复：`parse_args()` 兼容 str/dict；**重构为两阶段**——阶段一收集工具坐标快照，
  阶段二开新对话让模型基于快照输出最终 JSON 数组。修复后：
  **模式=function_calling，12 次工具调用，8 地点全验证通过** ✅

**19:42 发现模型自拟坐标（幻觉）**
- 降级路径运行时模型输出了"新郑市人民政府 34.605678"等知识库外地点与自拟坐标；
- 处理：①扩充知识库至 14 个真实地点（含别名，坐标逐条联网查证）；
  ②新增坐标核对 `reconcile_coordinates()`：凡能匹配知识库的地点一律用真实坐标覆盖；
  ③不可核实条目不入地图并在 trace 记录。最终 8/8 全部核实 ✅

**19:50 OSM 底图空白**
- tile.openstreetmap.org 本机网络不可达 → 改用高德瓦片（webrd01.is.autonavi.com，可达），
  地图正常显示。

**20:00 桌面截图拍到锁屏**
- 电脑处于锁屏状态，任务管理器/浏览器截图无效；
- 改用 Chrome headless 渲染地图截图 + nvidia-smi/ollama ps 文本证据（GPU 5586MiB、
  llama-server 进程、模型 100% GPU 加载），证据强度等价且更精确。

## 三、反思

1. **本地模型的下载渠道是第一坑**：官方 Ollama 仓库可能损坏且慢（89KB/s），
   ModelScope/hf-mirror 直连 GGUF + Modelfile 导入是可靠备选；
2. **函数调用接口的返回形态要实测**：Ollama 的 `arguments` 是 dict，OpenAI 是字符串，
   不能想当然；
3. **4B 模型会幻觉坐标**：地图类应用必须"模型做决策、工具给事实"，坐标核对环节不可省；
4. **Agent 循环要解耦**：工具收集与最终汇总分两个阶段，比"一路对话到底"稳得多；
5. **锁屏环境**下取证要走无头方案：Chrome headless 截图 + 命令输出文本，同样可证明本地运行。
