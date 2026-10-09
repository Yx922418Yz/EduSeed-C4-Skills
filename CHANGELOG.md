# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 的记录习惯，
版本号采用 语义化版本（SemVer）。

## [Unreleased]

- 计划：为四个技能补充自动化测试（pytest）与 GitHub Actions CI。
- 计划：把 `04_C4D_本地Agent` 的模型加载改为可配置，便于无 GPU 环境降级演示。

## [1.1.0] - 2026-10-09

### Added（C5：从"C4 提交包"升级为"可协作开源项目"）

- 新增 `LICENSE`（MIT，版权行含 2026 李亚轩 / Li Yaxuan）。
- 新增仓库级 `AI_LOG.md`：记录 C5 开源化全过程的 AI 协作与环境踩坑。
- 新增 `ATTRIBUTION.md`：汇总四个 C4 技能各自的"拿来→改造"来源。
- 新增 `CHANGELOG.md`（本文件）。
- 新增 `CONTRIBUTING.md`：外部贡献流程与提交约定。
- `README.md` 由"C4 提交说明"升级为规范开源项目 README：
  一句话输入/输出、解决的问题、快速开始、示例、项目结构、技术栈、
  AI 协作说明、借鉴来源、License。

### Changed

- 仓库定位从"一次性 C4 提交包"明确为"C4 技能 → 可协作开源项目"的作品集。

### Notes

- 四个技能文件夹（`01_`~`04_`）及其内容完整保留，未删除任何交付物。
- 本仓库全部文件通过 GitHub REST API（`api.github.com`）上传；
  本机 `git` 命令连 github.com 超时，故未使用 git push/clone。

## [1.0.0] - 2026-09（C4：技能分享与传播）

### Added

- `01_C4A_技能评审/`：C4 提交自动评审技能（`.skill` 包 + 方案设计 + 评审报告 + 教学说明）。
- `02_C4B_公众号发布/`：公众号文章排版技能（`.skill` 包 + 真实文章 + output.html + 传播追踪）。
- `03_C4C_作业求解/`：作业自动求解与排版技能（`.skill` 包 + 真实作业 run1–run3 证据 + 回归）。
- `04_C4D_本地Agent/`：本地大模型 Agent 技能（函数调用 + 结构化输出 + 记忆）+ 西亚斯学院交互地图。
- `README.md`、`.gitignore`。
