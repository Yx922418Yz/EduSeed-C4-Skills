# LiYaxuan C4D AAR 七维复盘

> 挑战：C4D 本地大模型 Agent 技能
> 复盘时间：2026-10-05
> 事实来源：本目录 `LiYaxuan_C4D_AI日志.md`、`LiYaxuan_C4D_验证报告.md`、`output_screenshots/` 原始证据。
> 说明：本文所有数据与结论均取自本人上述交付物，未新增任何未发生的事实。

## 一、学到了什么（Knowledge）

1. **本地大模型落地是一条链**：模型文件 + 量化格式 + 运行器 + 导入方式，任一环错位都跑不起来。官方 Ollama 仓库拉下来的 `gemma4:e4b` blob 损坏（`unsupported GGUF contains duplicate tensor`），且重拉只有 89KB/s；改 hf-mirror 直连 unsloth GGUF + Modelfile 本地导入才成功。
2. **`ollama create` 的 `FROM` 按服务端 CWD 解析**：写 `./models/...` 相对路径会被当成模型名直接 400，必须用绝对路径。
3. **函数调用接口的返回形态必须实测**：Ollama 的 tool `arguments` 是 **dict**，不是字符串；`json.loads(arguments)` 直接抛 TypeError。
4. **4B 级模型会幻觉坐标**：模型能"选择"地点，但精确经纬度不可信，必须"模型做决策、工具给事实"。
5. **Agent 循环要解耦**：工具收集与最终汇总分两阶段，比"一路对话到底"稳定得多。
6. **取证要走无头方案**：OSM 瓦片本机不可达（改高德瓦片）、锁屏时桌面截图无效（改 Chrome headless 截图 + `nvidia-smi`/`ollama ps` 文本证据）。

## 二、流程（Process）

- **18:30** 环境准备：`winget install Ollama.Ollama` → 官方模型拉取损坏 → 改 hf-mirror GGUF（Q5_K_M，5.11GB）。
- **19:00** 开 `OLLAMA_DEBUG=1` 前台跑 `ollama serve`，用 DEBUG 日志定位 blob 损坏。
- **19:05-19:30** 技能开发：fn-calling `get_place_coordinates` + 结构化输出 + 双路径降级 + 全程留痕；8 个地点坐标逐条联网查证（高德 POI / 河南省机场集团 / 卫星地图）。
- **19:30-20:10** Modelfile 导入（e4b-local，5.5GB）→ Agent 调试（两轮失败后重构）→ 生成交互地图 → 采集 GPU 证据。
- 全流程约 1 小时 40 分，每步坚持"先复现 → 再定位 → 再修 → 再验证"。

## 三、与 AI 协作（AI Collaboration）

| 环节 | 我（学生）做的 | AI（豆包）做的 |
|------|----------------|----------------|
| 需求定义 | 定出函数调用 + 结构化输出 + 双路径降级 + 留痕四条硬要求 | 无 |
| 代码生成 | 审阅接口、确认两阶段架构 | 生成 `gemma_agent.py` / `build_map.py` / `verify_output.py` / SKILL.md / Modelfile |
| 调试 | 构造测试、读 `agent_trace.json`、判定根因 | 解读 DEBUG 日志、给修复方案 |
| 事实核对 | 坐标知识库逐条联网查证、判定是否入图 | 无（AI 不联网核坐标） |
| 验证 | 逐项核对 `verify_output.py` 输出与截图证据 | 无 |

关键判断：AI 给出的两条初始实现（相对路径 `FROM`、`json.loads(arguments)`）都是错的，是我实测报错后才定位修复 —— 说明"AI 生成 + 人工验证"缺一不可。

## 四、完成了什么（Results）

- **本地运行**：Ollama v0.35.1 + Gemma 4 E4B（Q5_K_M，5.5GB），`ollama ps` 100% GPU、3.7GB 显存驻留、context 4096；`nvidia-smi` 显示 llama-server.exe 占用 5586MiB/8151MiB。
- **Agent 能力**：模式 = `function_calling`（未降级），12 次工具调用，3 轮工具轮 + 1 轮汇总，产出 8 个地点**全部坐标核对通过**（8/8）。
- **交互地图**：Folium + 高德底图，8 个标记，可缩放/点击弹窗（含坐标与描述）。
- **自动校验**：`verify_output.py` 全部通过（地点数 ≥ 8、字段齐全、坐标在中国境内、含郑州西亚斯学院、模式正确、有调用轨迹、final_json 已记录）。
- **证据**：运行截图 2 张 + `nvidia-smi_证据.txt` / `ollama-ps_证据.txt` 原始输出 + `agent_trace.json` + `sias_places.json`。

## 五、卡点与突破（Blockers & Breakthroughs）

| # | 卡点 | 根因 | 突破 |
|---|------|------|------|
| 1 | 模型拉下来报 500 | 官方 GGUF blob 损坏（duplicate tensor） | 改 hf-mirror 直连下载 + Modelfile 导入 |
| 2 | `ollama create` 400 | `FROM` 相对路径按服务端 CWD 解析 | 改绝对路径，导入成功 |
| 3 | Agent 两条路径全失败 | `arguments` 是 dict，`json.loads` 报错致参数为空，工具全返回"未找到" | `parse_args()` 兼容 str/dict |
| 4 | 模型持续调工具、不出最终 JSON | 工具循环与汇总耦合 | 重构为两阶段：先收集坐标快照 → 新对话输出 JSON |
| 5 | 模型自拟坐标（如"新郑市人民政府 34.605678"） | 4B 模型对精确经纬度记忆不可靠 | 知识库扩至 14 个真实地点 + `reconcile_coordinates()` 强制核对，不可核实条目不入图并记入 trace；最终 8/8 全核实 |
| 6 | 地图底图空白 | 本机网络不可达 OSM 瓦片 | 改高德瓦片（webrd01.is.autonavi.com） |
| 7 | 截图拍到锁屏 | 电脑处于锁屏状态 | 改 Chrome headless 渲染 + 命令输出文本证据（证据强度等价且更精确） |

**最大突破**：把"模型能力"和"事实来源"分离 —— 模型只负责选点与描述，坐标一律由知识库工具给，并强制核对。这使 8/8 全部可验证，而不是"看起来对"。

## 六、改进方向（Next）

1. 加入自检回路：Agent 跑完自动调用 `verify_output.py` 并回读失败项，形成闭环。
2. 坐标知识库从 14 个地点扩展到河南省主要 POI，并写自动查证脚本替代人工联网查证。
3. 对比更大参数量的本地模型（12B/27B）在同等任务下的幻觉率，量化"参数量—准确性"关系。
4. 把"两阶段"模式沉淀为技能内的固定模板，减少每次重写。
5. 将本次失败清单（7 条）反向写进 SKILL.md 的"常见坑"章节，让技能可复用。

## 七、ΔR 归因（Result-change Attribution）

| 阶段 | ΔR | 变化 | 归因（我做了什么） |
|------|-----|------|--------------------|
| R1 能跑起来 | 0 → 1 | 本地模型可对话（14.9s 生成 461 token） | 换下载渠道（hf-mirror GGUF）+ `winget` 安装 + Modelfile 绝对路径导入 |
| R2 Agent 可用 | 1 → 1 | 从"两条路径全失败"到 function_calling 12 次工具调用 | `parse_args()` 兼容 dict + 两阶段重构（收集与汇总解耦） |
| R3 结果可信 | 1 → 1 | 从"模型自拟坐标"到 8/8 全部核实 | 知识库扩至 14 地点 + `reconcile_coordinates()` 强制核对 + 不可核实不入图 |
| R4 证据合规 | 1 → 1 | 从"锁屏截图无效"到可验证 GPU 证据 | Chrome headless 截图 + `nvidia-smi`/`ollama ps` 原始文本输出 |

**总归因**：本挑战的 R 提升不来自"让模型更聪明"，而来自**把不确定性挡在事实入口**（下载渠道、接口形态、坐标来源、取证方式）——四处"入口治理"各自解决了一类会导致整体失败的隐患。


---

## 附录：2026-10-06 高水平增强复验（记忆机制）

> 依据：对照 C4D 评审维度中"Agent 能力（功能可用/有记忆/有技能）"信号，
> 对初版 Agent 增加显式记忆后复验。本文其余部分保持初次复盘原文。

| 项 | 初版（上文） | 增强版（复验） |
|----|------------|--------------|
| 工具调用次数 | 12 次 | 10 次（模型更精准） |
| 记忆 | 无显式记忆（仅会话内快照） | **output/sias_memory.json**：坐标快照持久化，阶段二"从记忆读取"，跨会话复用 |
| 校验 | 无记忆校验 | erify_output.py 新增 4 项记忆校验（文件存在/类型/条数/复用标记）全部通过 |
| 地点 | 8 个全核对（含二七纪念馆） | 8 个全核对（本次含郑州站），坐标真实性不受影响 |

增强后复验结果：模式 unction_calling，8 地点全部 erified=true，
记忆文件写入 8 条坐标并被阶段二复用，erify_output.py 全部校验通过 ✔。
（本附录数据与 LiYaxuan_C4D_验证报告.md 同步更新。）