# Attribution（拿来说明）

> 拿来主义原则：本仓库不羞于借鉴，反而把"从哪拿的、改了什么、为什么"
> 全部写清楚。四个 C4 技能各自的子拿来说明见各文件夹；本文件是仓库级汇总。

## 一、整体来源

本仓库的四个技能均诞生于 EduSeed Elite20 C4（技能分享与传播）训练，
核心方法论是"拿来 → 理解 → 改造 → 超越"。它们共同借鉴了以下基座：

| 来源 | 拿来了什么 | 怎么用（adopted / improved） |
|------|-----------|------------------------------|
| 课程示例技能 `wechat-doc-mapper` | 文件夹递归采集、扩展名白名单、作者识别链（文件名→文件夹→元数据→文档头）、openpyxl 多 Sheet 输出框架 | **adopted** 其采集与识别骨架；**improved** 把"分信/缺口分析"升级为"阅卷/评审"（C4A） |
| 课程示例技能 `skill-explainer` | D1–D4 四维评审矩阵的思路 | **adopted** 四维评估思想；**improved** 翻译成可计算的 check-item 谓词，让评分透明可复算 |
| `c4-skill-evaluator-starter` | `SKILL.md` 脚手架、`c4_rubric.yaml` 信号库（5 项交付物 + 4 条件 + 评分公式） | **adopted** 评分规则文件；**improved** 实现全部逻辑并新增班级总览、版本追踪、LLM 深审适配器 |
| Anthropic 官方 Agent Skills 文档 | "技能三层加载"（SKILL.md 主指令 / scripts / references / examples）的目录约定 | **adopted** 目录结构约定；**improved** 按本课程命名规范 `LiYaxuan_C4X_*` 落地 |
| Claude 内置 `file-reading` / `xlsx` 技能 | 文件类型分发逻辑、openpyxl 样式与自动列宽写法 | **adopted** 作为实现参考 |
| Python 官方文档（`pathlib` / `argparse` / `subprocess`） | 命名规范正则、子进程调用外部工具（MiKTeX / Ollama）的写法 | **adopted** 标准库用法 |

## 二、逐技能对应

- `01_C4A_技能评审/` → 详见 `LiYaxuan_C4A_拿来说明.md`
  （基座 wechat-doc-mapper；新增完整性三通道检测、check-item 谓词化质量评审、版本追踪）。
- `02_C4B_公众号发布/` → 详见该文件夹 `LiYaxuan_C4B_拿来说明.md`
  （公众号 HTML 排版规范参考微信公众平台官方格式与既有 callout/TOC 实践）。
- `03_C4C_作业求解/` → 详见该文件夹 `LiYaxuan_C4C_拿来说明.md`
  （作业求解的"读题→求解→排版"流水线设计参考通用作业自动化实践）。
- `04_C4D_本地Agent/` → 详见该文件夹 `LiYaxuan_C4D_拿来说明.md`
  （函数调用 / 结构化输出 / 记忆机制参考 OpenAI function-calling 范式与 Ollama 本地推理实践）。

## 三、C5 开源化阶段借鉴

- 开源 README 模板结构：参考本课程 C5 CHALLENGE.md 给出的标准模板
  （一句话输入/输出 → 解决什么问题 → 快速开始 → 示例 → 项目结构 → 技术栈 → AI 说明 → 借鉴来源 → License）。
- `CHANGELOG.md` 格式：参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。
- MIT License 文本：直接采用 OSI 标准 MIT 模板，版权行填写 2026 李亚轩 / Li Yaxuan。
