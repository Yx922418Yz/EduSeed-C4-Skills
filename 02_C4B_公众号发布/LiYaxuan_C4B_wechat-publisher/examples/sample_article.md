# 把 AI 装进自己电脑：本地大模型 Agent 完全入门指南

> [!note]
> 本文由我的自研公众号排版技能（C4B wechat-publisher）一键生成。
> 想了解这个技能本身，欢迎看到最后。

## 为什么要在本地跑大模型

云端 AI 很强大，但它有一个被很多人忽略的真相：**能力是租来的**。

- 云端 API 会断——某个服务商临时故障，你的产品全线瘫痪；
- 云端 API 会涨价——你辛辛苦苦做的应用，成本可能一夜翻倍；
- 云端 API 会审查——你的数据离开设备的那一刻，就不再只属于你。

而本地模型不同。一台笔记本 + 一个开源模型 + 你的工程能力 = **完全自主的 AI Agent**。
数据不出设备、推理零成本、断网也能用——这就是 AI 数字主权。

## 你需要准备什么

以我现在用的这套配置为例，给你一个真实的参考：

| 项目 | 配置 |
|------|------|
| 设备 | Windows 笔记本（i9-14900HX + RTX 5060 + 32GB 内存） |
| 运行工具 | Ollama v0.35.1 |
| 模型 | Gemma 4 E4B（Q5_K_M 量化，约 5.1 GB） |
| 驱动方式 | Ollama 自带 OpenAI 兼容 API |

> [!warning]
> 内存不足 16GB 的同学建议选 E2B 或 E4B 的低量化版本；
> 24GB+ 显存可以上 26B MoE，体验会再上一个台阶。

## 第一步：装 Ollama

Ollama 是目前最省心的本地模型运行器，一行命令装好，自带 OpenAI 兼容 API：

```bash
# Windows 直接下载安装包，或：
winget install Ollama.Ollama
```

装好后在终端里拉取模型：

```bash
ollama pull gemma4:e4b
```

> [!tip]
> 如果官方源下载很慢（国内常见），可以改用镜像站手动下载 GGUF 文件，
> 再用 `ollama create` 本地创建——速度能快几十倍。

## 第二步：验证模型能跑

```bash
ollama list
```

看到 `gemma4:e4b` 出现，模型就绪。先做一次最简单的对话测试：

```bash
ollama run gemma4:e4b "用一句话介绍你自己"
```

> [!note]
> 截图时记得包含模型名、工具版本、设备信息和推理速度（tok/s），
> 这些是评审"是否真的在本地跑"的关键证据。

## 第三步：让模型干活——结构化输出

本地模型最大的价值不是聊天，而是**作为 Agent 的大脑**。
要让模型产出程序可解析的数据，最稳的方式是"结构化 JSON 输出"：

```python
import requests

resp = requests.post("http://localhost:11434/v1/chat/completions", json={
    "model": "gemma4:e4b",
    "format": "json",   # 强制 JSON
    "messages": [
        {"role": "system", "content": "Always respond with valid JSON only."},
        {"role": "user", "content": "List 5 landmarks near SIAS University ..."},
    ],
})
data = resp.json()["choices"][0]["message"]["content"]
```

模型返回的 JSON 直接就能喂给程序——这就是"模型生成数据，程序负责渲染"的 Agent 分工。

## 第四步：函数调用——Agent 的"手"

比结构化输出更进一步的是**函数调用（function calling）**：
模型不直接输出结果，而是决定"我要调用哪个工具、传什么参数"，由你的程序真正执行。

```json
{
  "type": "function",
  "function": {
    "name": "get_sias_location_info",
    "description": "查询西亚斯学院校园地点信息",
    "parameters": {
      "type": "object",
      "properties": {"place_name": {"type": "string"}},
      "required": ["place_name"]
    }
  }
}
```

模型发起调用 → 程序执行 → 结果回填 → 模型继续推理。
这就是多步 Agent 的最小闭环。

> [!tip]
> 工具的参数 schema 一定要写清楚描述，小模型（E4B 级别）对描述质量极其敏感。

## 实战：让本地模型生成一张校园地图

把上面几步串起来，一个真实的 Agent 任务就完成了：

1. 本地模型生成西亚斯学院周边 8 个地点的 JSON（名称/坐标/描述）；
2. 程序校验坐标合法性（过滤全零和越界数据）；
3. Folium（Leaflet.js）渲染交互式 HTML 地图；
4. 浏览器打开 → 可缩放、可点击标记、中英双语标注。

```python
import folium
m = folium.Map(location=[34.3935, 113.7338], zoom_start=15)
for loc in data:
    folium.Marker(
        [loc["latitude"], loc["longitude"]],
        popup=f"<b>{loc['name_zh']}</b><br>{loc['description']}",
    ).add_to(m)
m.save("sias_map.html")
```

全程零 API 费用、数据不出设备、断网可跑。

## 这套东西能做什么

| 场景 | 说明 |
|------|------|
| 隐私敏感数据处理 | 病历、合同、内部文档，绝不外传 |
| 离线环境部署 | 教室、机房、飞机上照常工作 |
| 批量低成本推理 | 无限次调用，无按量计费焦虑 |
| 学习模型原理 | 真正理解模型怎么跑，而不是黑盒调 API |

## 写在最后

本地跑大模型这件事，最大的门槛不是技术，而是"觉得很难"的预设。
实际上从装 Ollama 到跑通一个 Agent 任务，一个下午足够。

> [!warning]
> 我的实践来自 EduSeed C4D 挑战：在自有设备上运行 Gemma 4，驱动 Agent 技能并生成交互式地图。
> 挑战教会我最重要的一件事：**AI 不是只能"用"，还能"拥有"。**

---

*本文由 LiYaxuan 编写，使用自研 C4B 公众号排版技能生成。
如果对本地模型部署或 Agent 开发感兴趣，欢迎留言交流。*
