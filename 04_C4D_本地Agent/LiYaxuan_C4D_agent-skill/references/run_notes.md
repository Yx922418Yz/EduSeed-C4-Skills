# 运行记录与复现说明（run notes）

## 模型标注（评审关键信息）

| 项 | 值 |
|----|-----|
| 模型 | **Gemma 4 E4B** |
| 量化 | **Q5_K_M**（unsloth GGUF） |
| 运行器 | **Ollama** v0.35.1（本地服务 http://localhost:11434） |
| 设备 | **NVIDIA GeForce RTX 5060 Laptop GPU**（8GB，CUDA 12.8 驱动），CPU i9-14900HX / 32GB |
| 系统 | Windows 11 |

## 模型文件来源（复现用）

- 文件：`gemma-4-E4B-it-Q5_K_M.gguf`（5.11GB，**不入库**，请自行下载）
- 下载地址 1（ModelScope，国内快）：`https://modelscope.cn/models/unsloth/gemma-4-E4B-it-GGUF/resolve/main/gemma-4-E4B-it-Q5_K_M.gguf`
- 下载地址 2（hf-mirror）：`https://hf-mirror.com/unsloth/gemma-4-E4B-it-GGUF/resolve/main/gemma-4-E4B-it-Q5_K_M.gguf`
- 导入命令（Modelfile 见本技能包根目录；`FROM` 必须写 GGUF 在本机的**绝对路径**）：
  ```
  ollama create e4b-local -f Modelfile
  ```
- 模型名：`e4b-local:latest`（ID a7d2e7485558，5.5GB，导入成功）

## 运行步骤（本机实际执行顺序）

1. `ollama serve`（或 Ollama 系统服务）
2. `ollama create e4b-local -f Modelfile`（首次）
3. `python scripts/gemma_agent.py` → 生成 `output/sias_places.json` + `output/agent_trace.json`
4. `python scripts/build_map.py` → 生成 `output/sias_map.html`（高德底图）
5. `python scripts/verify_output.py` → 输出校验结论
6. 浏览器打开 `output/sias_map.html`，截图存档

## 预期时间

- 首次加载模型进显存：约 1-2 分钟；
- Agent 单轮对话：数秒至数十秒（RTX 5060）；
- 全程（下载模型除外）：约 5 分钟。
