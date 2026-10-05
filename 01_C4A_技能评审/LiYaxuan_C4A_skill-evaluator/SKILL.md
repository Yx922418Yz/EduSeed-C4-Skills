---
name: c4-skill-evaluator
description: >
  扫描包含 Elite20 C4 技能提交的本地文件夹（微信群同步目录或任意附件目录），
  识别作者、检查 5 项必备交付物的完整性，并按 C4 四条件（可复用/可执行/可验证/IO明确）
  自动评审技能质量，生成含班级总览、作者详情、排名与改进建议的评审报告（Markdown + Excel）。
  当用户说"评审C4提交"、"检查技能提交"、"C4评审报告"、"evaluate C4 submissions"、
  "review skill submissions"，或提供一个文件夹路径并要求评审其中的技能文件时触发。
  也适用于任何需要按既定规范自动盘点并打分一批技能包/作业提交的场景。
---

# C4 Skill Submission Evaluator（C4 提交自动评审器）

## Purpose

给定一个包含 C4 技能提交的本地文件夹（通常从微信群下载），本技能自动完成
「文件采集 → 作者识别 → 完整性检查 → 四条件质量评审 → 报告生成」的完整流水线，
相当于把收发室升级为自动阅卷系统：不仅统计谁交了、交没交齐，还按评分规则打分并给出改进建议。

## Prerequisites

- Python 3.9+，依赖：`pyyaml`（必需）、`pypdf`（PDF 元数据/内容，可选）、`openpyxl`（Excel 输出，可选）
- 安装：`python -m pip install pyyaml pypdf openpyxl`
- （可选 Level 3 增强）配置国产大模型 API：`DASHSCOPE_API_KEY` 或 `OPENAI_API_KEY`，
  启用 `--llm` 后可对内容做深度评审；未配置时规则引擎仍可完整运行。

## Workflow

### Step 1 — 扫描与作者识别

```bash
python scripts/c4_skill_evaluator.py <文件夹路径> --output <输出目录> [--excel] [--llm]
```

脚本会递归扫描文件夹，识别文件名中的 `_C4_` / `_C4A_` 等标记，并按以下链条提取作者：
1. 文件名规范前缀（`姓名_C4_内容描述.扩展名`）
2. 父文件夹名（文件按作者分目录存放）
3. 文件元数据（PDF/DOCX 作者字段）
4. 文档头部作者标记
5. 无法识别 → 标记 `Unknown` 并列入"需人工确认"

### Step 2 — 完整性检查（5 项必备交付物）

对照 `references/c4_rubric.yaml` 中的信号定义，检查每位作者是否提交齐：
Skill 说明文档 / 可执行内容 / Demo / 教学说明 / AI 日志。
输出 ✅ 齐全 / ⚠️ 部分缺失 / ❌ 严重缺失，并列出具体缺失项与匹配文件。

### Step 3 — 质量评审（C4 四条件）

对通过完整性检查的提交，按四条件自动评审：

| 条件 | 检测内容 |
|------|----------|
| 可复用 | 安装步骤？环境要求？是否含硬编码绝对路径/凭据（负向信号） |
| 可执行 | 有可运行代码/prompt/workflow？.skill 结构完整？YAML frontmatter？ |
| 可验证 | 有测试用例/示例？预期输出？demo 展示真实结果？ |
| IO 明确 | 有"输入____，输出____"一句话描述？输入输出类型清晰？ |

每个条件给出 ✅ / ⚠️ / ❌ 评级 + 评审依据 + 改进建议。
技术选型：**规则 + LLM 混合**——规则引擎确定性快筛（离线可跑、零成本），
LLM 深审（可选）发现规则层漏检问题并生成个性化建议。选型理由见方案设计文档。

### Step 4 — 报告生成

- **Markdown 报告**：班级总览（提交人数/完整率/质量分布）+ 作者详情（完整性矩阵+质量评分+反馈）+ 排名表 + 全班改进建议 + 需人工确认清单
- **Excel 详表**（`--excel`）：作者×条件矩阵、文件清单、缺失项汇总、班级统计
- **JSON**：机器可读结构化结果（stdout），便于上层 Agent 集成
- **版本追踪**：自动识别 `_v2`/`_v3` 迭代版本，展示进步轨迹，评分以最新版本为准

## Edge Cases

| 情况 | 处理 |
|------|------|
| 空文件夹 | 报告"未找到文件"，正常退出 |
| 命名不规范 | 回退到元数据/文件夹/文档头部识别，标记 Unknown 待人工确认 |
| 超大文件（>50MB） | 跳过内容分析，仅按文件名/类型匹配 |
| 二进制文件（.mp4 等） | 仅做文件名匹配，不做内容分析 |
| 非 C4 文件混入 | 过滤后在报告"非 C4 文件"单独列出 |
| 同一作者多版本 | 识别 `_v2`/`_v3`，报告迭代历史，以最新版评分 |
| 中文/编码问题 | 统一 UTF-8 读取，errors=replace 兜底 |
| LLM API 不可用 | 自动降级为纯规则评审，不阻断主流程 |

## Examples

```bash
# 基本评审
python scripts/c4_skill_evaluator.py ~/Desktop/WeChatFiles/C4文件夹 --output report/

# 评审 + Excel 详表
python scripts/c4_skill_evaluator.py ./c4-submissions --output report/ --excel

# 评审 + 国产大模型深度评审
export DASHSCOPE_API_KEY=sk-xxx
python scripts/c4_skill_evaluator.py ./c4-submissions --output report/ --llm
```

## 拿来说明（基于 wechat-doc-mapper 的改造）

- **拿了**：`inventory_folder` 文件采集逻辑、作者识别回退链（文件名→文件夹→元数据→文档头）、
  YAML 驱动的信号评分思想
- **改了**：采集聚焦 C4 命名规范（`_C4_` 标记）；作者识别前移到文件名解析；
  新增完整性检查（5 项必备交付物信号库）、四条件质量评审器（check item 谓词化）、
  版本追踪、Markdown+Excel+JSON 三格式报告生成
- **为什么**：wechat-doc-mapper 只做"分信"（分类盘点），C4A 需要"阅卷"
  （按规范打分评语）——在它的采集与识别基座上叠加评审层，避免重复造轮子
