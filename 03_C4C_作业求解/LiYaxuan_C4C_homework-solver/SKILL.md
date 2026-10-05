---
name: homework-solver
description: >
  作业自动求解与排版技能：摄入作业文件（Markdown/PDF/Word/图片）→ 识别题目
  → SymPy 符号计算自动求解（微积分/线性代数/微分方程/大学物理）→ LaTeX 排版
  → 编译 PDF。当用户说"帮我解作业"、"自动求解作业"、"生成作业解答 PDF"、
  "solve this homework"、或给出作业文件（.md/.pdf/.docx/图片）要求解答与排版时使用。
  内置国产大模型引擎（Qwen/Kimi）可在规则求解失败时降级深解。
---

# Homework Solver（作业自动求解与排版流水线）

## Purpose

把一份作业文件变成一份**带完整解题步骤的 PDF**：
摄入 → 解析 → 自动求解 → LaTeX 排版 → PDF 编译，全程一条命令。

本技能基于 `c4c-homework-solver-starter` 定制，完成两项核心升级：
1. **引擎迁移**：从"仅 Claude 单点"迁移为「SymPy 确定性求解 + 国产大模型（Qwen/Kimi）降级深解」；
2. **领域扩展**：实现 starter 留作"学生扩展点"的线性代数 / 微分方程求解器，并新增大学物理（力学）领域。

## Prerequisites

```bash
python -m pip install sympy pyyaml pdfplumber python-docx
```

LaTeX 编译 PDF（可选）：安装 MiKTeX / TeX Live（Windows 推荐 MiKTeX，含 `xelatex`）。

## Workflow（一条命令）

```bash
python scripts/pipeline.py <作业文件> <输出目录> --compile --course "线性代数" --student "LiYaxuan" --title "作业解答"
```

输出：
```
<输出目录>/
├── 1_ingested.json    # Stage 1 摄入
├── 2_parsed.json      # Stage 2 题目解析（含类型分类）
├── 3_solutions.json   # Stage 3 自动求解
├── homework.tex       # Stage 4 LaTeX 排版
└── homework.pdf       # Stage 5 PDF 编译（--compile）
```

## 支持的领域（C4C 扩展后）

| 领域 | 题目类型 | 求解器 |
|------|----------|--------|
| 微积分 | limit / tangent / epsilon_delta / calculation | starter 保留（SymPy） |
| 线性代数（新增） | matrix：行列式/逆矩阵/特征值/秩/方程组 | `domain_solvers.solve_matrix_ext` |
| 微分方程（新增） | ode：一阶可分离/一阶线性/二阶常系数 | `domain_solvers.solve_ode_ext`（dsolve） |
| 大学物理-力学（新增） | physics：匀变速/自由落体/牛顿定律/圆周运动 | `domain_solvers.solve_physics`（公式模板） |
| 证明/概念题 | proof / conceptual | SymPy 失败时降级 LLM（可选） |

## 国产大模型引擎（C4C 迁移核心）

配置任一环境变量即启用（**优先 Qwen → Kimi → OpenAI 兼容**）：

```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY = "sk-你的通义千问Key"     # 或 QWEN_API_KEY
$env:MOONSHOT_API_KEY = "sk-你的KimiKey"
$env:LLM_BASE_URL = "https://自建代理/v1" ; $env:LLM_MODEL = "qwen3"
```

- 规则求解失败时自动调用 LLM 深解（`scripts/llm_engine.py`）；
- **未配置 API 时自动降级**为纯 SymPy 求解，流水线零云端依赖可跑。

## Input / Output

- **输入**：`.md` / `.pdf` / `.docx` / 图片（OCR 占位）
- **输出**：JSON 中间产物（3 份）+ LaTeX 源文件 + PDF（--compile）

## 验证

- 内置测试：`test_cases/`（starter 极限测试）+ `examples/`（本技能真实作业测试）；
- 建议用 `3_solutions.json` 与标准答案比对，正确率目标 ≥ 90%；
- PDF 编译后用浏览器/阅读器打开核对排版。

## Edge Cases

| 情况 | 处理 |
|------|------|
| 未安装 LaTeX | 跳过编译，提示用 overleaf.com 在线编译 homework.tex |
| 未识别题目 | 检查题号格式（Problem N / 题 N / N. / N) / Q.N） |
| PDF 是扫描件 | 需要 OCR（pytesseract，本技能提供占位） |
| 规则求解失败 | 有 LLM Key 则降级深解；否则标记 unsolved 并给出 reason |
| 中文 LaTeX | 使用 xelatex + ctex 模板（references/homework_template.tex） |
