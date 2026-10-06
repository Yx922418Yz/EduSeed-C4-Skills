# LiYaxuan C4D 教学说明

## 目标读者
没跑过本地大模型的同学。照着做，30 分钟内能在自己电脑上跑起 Gemma 4 并生成交互式地图。

## 你需要什么
- 一台电脑：8GB 显存 GPU（推荐）或 16GB+ 内存（CPU 也能跑，慢一点）；
- 约 10GB 磁盘空间；
- Windows / macOS / Linux 均可。

## 第一步：装 Ollama（本地模型运行器）

**Windows**（本机验证过最快的方式）：
```powershell
winget install Ollama.Ollama
```
安装后启动服务：任务栏 Ollama 图标已运行，或命令行执行 `ollama serve`。

验证服务：
```powershell
curl http://localhost:11434/api/tags
```

## 第二步：拿到 Gemma 4 E4B 模型（两种方式）

**方式 A（最省事，网络好时）**：
```powershell
ollama pull gemma4:e4b
```

**方式 B（官方仓库慢/损坏时，本机实际采用）**：
1. 从 ModelScope 下载 Q5_K_M 量化 GGUF（约 5.1GB，国内快）：
```powershell
curl -L -o gemma-4-E4B-it-Q5_K_M.gguf ^
  https://modelscope.cn/models/unsloth/gemma-4-E4B-it-GGUF/resolve/main/gemma-4-E4B-it-Q5_K_M.gguf
```
（hf-mirror 备选：`https://hf-mirror.com/unsloth/gemma-4-E4B-it-GGUF/resolve/main/gemma-4-E4B-it-Q5_K_M.gguf`）
2. 写一个 Modelfile（本技能包已附，`FROM` 用 GGUF 的**绝对路径**），本地导入：
```powershell
ollama create e4b-local -f Modelfile
```
3. 验证模型能说话：
```powershell
ollama run e4b-local "用一句话介绍你自己"
```

## 第三步：跑 Agent 生成地图

```powershell
pip install folium
python scripts/gemma_agent.py    # Agent：函数调用 + 结构化输出 → sias_places.json + 记忆 sias_memory.json
python scripts/build_map.py      # Folium → sias_map.html
python scripts/verify_output.py  # 校验（含记忆校验）
```

浏览器打开 `output/sias_map.html`：可以缩放、点击每个标记看详情。

## 第四步：截图证明"本地运行"

1. 打开任务管理器（Ctrl+Shift+Esc），找到 `ollama` 进程和 GPU 占用；
2. 打开地图页面，缩放/点击两个标记；
3. 截图保存为 `LiYaxuan_C4D_运行截图1_交互地图.png`；
4. 终端执行 `ollama ps` 和 `nvidia-smi`（Windows 需先装 NVIDIA 驱动自带工具），
   截图保存为 `LiYaxuan_C4D_运行截图2_本地GPU证据.png`；
5. 再截一张 `agent_trace.json` 里的工具调用片段。

> 提示：若电脑锁屏导致桌面截图无效，可改用 Chrome 无头截图：
> `chrome --headless --screenshot=out.png --window-size=1600,1000 "file:///.../sias_map.html"`，
> `nvidia-smi` / `ollama ps` 文本输出同样是"本地运行"的硬证据（本机即采用此方案）。

## 常见问题

| 问题 | 解决 |
|------|------|
| `ollama pull` 很慢/卡住 | 换方式 B：ModelScope/hf-mirror 直连 + Modelfile 导入 |
| 模型加载后报 500 | 先 `ollama rm` 再重新拉/导入（本机遇到损坏 blob 即此症状） |
| 首次对话很慢 | 5.5GB 模型在加载进显存，属正常，等 1-2 分钟 |
| Modelfile 导入报"neither 'from' or 'files'" | `FROM` 必须写 GGUF 的**绝对路径**（本机踩过） |
| 函数调用没触发 | Agent 会自动降级到结构化输出路径，依然满足挑战要求 |
| 显存不够（<8GB） | 改用更小量化（Q4_K_M）或让 Ollama 走 CPU |

## 想深入？

- 把 `get_place_coordinates` 换成任意工具（天气、计算器、数据库查询），就是通用 Agent；
- Gemma 4 原生支持多模态，可以给它喂图片做 OCR/看图说话；
- 本技能包的 `agent_trace.json` 展示了 Agent 的完整决策链，是学习 Agent 的最佳教材。
