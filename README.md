# EduSeed C4 Skills · 可协作开源技能集

> **一句话：输入一个真实任务（技能评审 / 公众号排版 / 作业求解 / 本地 Agent），
> 输出一套可直接安装的 `.skill` 技能包 + 可复现的运行证据与完整文档。**
>
> 这是 EduSeed Elite20 **C4 技能 → C5 开源仓库** 的作品集：把我在 C4 完成的四个技能，
> 整理成别人能看懂、能复现、能贡献的开源项目。

## 解决什么问题

- **没有它之前**：AI 技能（prompt + 脚本 + 参考资料）散落在本地电脑里，只有我自己能用，
  换台电脑、过两周就忘了怎么跑；别人想问"你这个技能怎么做的"也无从看起。
- **有了它之后**：每个技能都是一个独立 `.skill` 包（tar.gz，可直接导入），
  旁边带着方案设计、教学说明、真实运行证据、AI 日志与拿来说明——
  任何人 `clone` 下来，照着文档就能复现，也能在我的基础上 fork 改造。

它解决的核心问题是：**把"我电脑上的文件"变成"全世界都能用、能协作的项目"。**

## 快速开始

### 获取

本仓库通过 GitHub REST API 上传。如果你本机 `git` 可用：

```bash
git clone https://github.com/Yx922418Yz/EduSeed-C4-Skills.git
cd EduSeed-C4-Skills
```

> 注：作者本机 `git` 直连 github.com 超时，改用 `api.github.com` 上传；
> 你在自己网络环境下 clone 通常不受影响。

### 安装与使用

这是一组 **Claude 风格 Agent Skill**，不是一个需要 `pip install` 的单体程序。
使用方式：

1. 进入你要用的技能文件夹，例如 `01_C4A_技能评审/`；
2. 同名子目录（如 `LiYaxuan_C4A_skill-evaluator/`）是未打包源码，含 `SKILL.md` / `scripts/` / `references/` / `examples/`；
3. `*.skill` 文件是打包产物（tar.gz），可直接导入你的 Agent 技能系统；
4. 依赖：脚本主要用 Python 3（`openpyxl` 等）；C4D 需要本地 **Ollama + 本地 Gemma 模型**，
   复现步骤见该文件夹内的教学说明。

## 示例

以 **C4C 作业求解** 为例：

- 输入：一道真实作业题（含线性代数 / 常微分方程 / 大学物理）。
- 输出：求解过程 + 排版后的 PDF（`test-output/` 下保留了 run1–run3 的真实产物）。

以 **C4D 本地 Agent** 为例：

- 输入：一个"列出西亚斯学院若干地点"的指令。
- 输出：Agent 通过 10 次函数调用 + 跨阶段记忆，生成 8 个地点的 JSON，
  并渲染成交互地图 HTML（见 `04_C4D_本地Agent/output_screenshots/`）。

## 项目结构

```
EduSeed-C4-Skills/
├── README.md                 ← 本文件
├── LICENSE                   ← MIT（2026 李亚轩 / Li Yaxuan）
├── CHANGELOG.md              ← 版本记录
├── CONTRIBUTING.md           ← 贡献指南
├── AI_LOG.md                 ← 仓库级 AI 协作日志
├── ATTRIBUTION.md            ← 借鉴来源（拿来说明）
├── .gitignore
├── 01_C4A_技能评审/           ← 技能提交自动评审器
│   ├── LiYaxuan_C4A_skill-evaluator.skill   （打包产物）
│   ├── LiYaxuan_C4A_skill-evaluator/        （源码：SKILL.md/scripts/references）
│   ├── test-corpus/                          （测试语料）
│   └── eval-output/                          （真实评审输出）
├── 02_C4B_公众号发布/         ← 公众号文章排版技能
│   ├── LiYaxuan_C4B_wechat-publisher.skill
│   ├── LiYaxuan_C4B_wechat-publisher/
│   ├── LiYaxuan_C4B_output.html             （2345 字真实文章排版产物）
│   └── ...（文章源文件 / 传播追踪 / 方案设计）
├── 03_C4C_作业求解/           ← 作业自动求解与排版
│   ├── LiYaxuan_C4C_homework-solver.skill
│   ├── LiYaxuan_C4C_homework-solver/
│   └── test-output/                          （run1–run3 + 回归证据）
└── 04_C4D_本地Agent/          ← 本地大模型 Agent（函数调用+记忆）
    ├── LiYaxuan_C4D_Agent技能.skill
    ├── LiYaxuan_C4D_Agent技能/
    └── output_screenshots/                    （交互地图截图）
```

## 技术栈

- **语言**：Python 3（脚本主力；`openpyxl` 处理 Excel）。
- **技能格式**：Claude 风格 Agent Skill（`SKILL.md` + `scripts/` + `references/` + `examples/`，打包为 `.skill` = tar.gz）。
- **外部工具**：MiKTeX（LaTeX→PDF 排版）、Ollama（本地 Gemma 推理，C4D）、Node 22（部分前端产物）。
- **AI 集成**：AI 辅助编码 / 文档 / 评审；C4A 预留 LLM 深审适配器（可配国产模型 API，离线亦可跑规则评审）。

## AI 协作说明

本项目 AI-First 开发：用 AI 生成仓库骨架、README 初稿、脚本与测试，再由我逐轮审校、修正边界情况。
完整过程（含环境踩坑、换路、手动反向举证）见 [AI_LOG.md](./AI_LOG.md)。
每个技能文件夹内另有各自的 `AI日志.md`，记录该技能的多轮迭代。

## 借鉴来源

本项目遵循"拿来主义"：在课程示例技能与官方文档基础上改造而成。
详细的"从哪拿、改了什么、为什么"见 [ATTRIBUTION.md](./ATTRIBUTION.md)。

## License

[MIT](./LICENSE) © 2026 李亚轩 (Li Yaxuan)
