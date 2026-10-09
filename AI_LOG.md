# AI_LOG.md（仓库级 AI 协作日志）

> 本文件记录 C5（把 C4 技能升级为可协作开源项目）阶段，AI 如何被使用、
> 踩过哪些坑、换了什么路。四个技能在 C4 阶段各自的 AI 日志见对应文件夹。

## 环境事实（先探明，再动手）

- 本机为 Windows 原生，只有 PowerShell 可用（Bash 被禁用）；Python 3.13 在 `D:\HJY\python.exe`。
- **坑 1**：`git` 命令（libcurl 栈）直连 github.com 超时，`127.0.0.1:7897` 代理无服务。
  → **换路**：绝不使用 `git push/clone/fetch`；改走 `api.github.com`（Python urllib 可达），
  用组织者预置的 `gh_helper.py` 统一做 GitHub REST API 操作（自动读 `%TEMP%\gh_token.txt`）。
- **验证方式**：每次 `upload` 后都用 `get` / `list` 反向拉取，确认文件确实存在且内容正确。

## 迭代记录（多轮，非一句话直出）

### 第 1 轮：现状盘点（只读）

- 用 `gh_helper whoami` 确认 token 有效（login = Yx922418Yz）。
- 用 `repo-exists` + `list` 确认 `Yx922418Yz/EduSeed-C4-Skills`（main）已含：
  `.gitignore`、`README.md`、四个技能文件夹（`01_`~`04_`）。
- 用 `get` 拉取现有 `README.md` 与 `.gitignore` 全文，逐文件夹 `list` 内部结构，
  作为升级 README 的事实依据——**不凭想象写目录树**。

### 第 2 轮：补齐工程文件

- 手写脚本 `c5_local/write_c5_files.py`，一次性生成：
  `LICENSE`（MIT，版权行 2026 李亚轩/Li Yaxuan）、`CHANGELOG.md`、
  `CONTRIBUTING.md`、`ATTRIBUTION.md`、本 `AI_LOG.md`。
- **决策**：四个技能文件夹及其内容一个不删（题目硬性要求），只新增仓库级文件。

### 第 3 轮：升级 README

- 把原"C4 提交说明"README 重写为开源项目 README，保留原有"四个技能对照表"的有效信息，
  再补：一句话输入/输出、解决的问题、快速开始、示例、项目结构、技术栈、
  AI 协作说明、借鉴来源（指向 ATTRIBUTION）、License。

### 第 4 轮：上传与逐一验证

- 通过 `gh_helper upload ... --branch main` 推送全部新文件与新 README。
- 每推一个文件用 `get` 反向 GET 校验存在；最后 `list` 根目录核对清单。

## 手动步骤的反向举证

- `LICENSE` 的版权行、`CHANGELOG` 的版本号与日期、`README` 中四个技能的目录树：
  均由我对照 `list`/`get` 的真实返回逐条核对后填写，未让 AI 凭空编造文件名。
- 不使用 `git push` 是网络环境决定的（见"坑 1"），不是跳过版本管理；
  所有提交都经 REST API 产生了真实 commit，可在仓库 commit history 中查到。

## 已知边界

- 受网络限制，本仓库未启用 GitHub Actions CI（可选加分项），已在 CHANGELOG 的 Unreleased 中列为后续计划。
- 仓库主页截图：优先用 headless 浏览器渲染线上仓库页；若线上页无法渲染，
  则退化为"本地 README 渲染截图 + API 拉取证据"，并在交付文件中诚实标注截图来源。
