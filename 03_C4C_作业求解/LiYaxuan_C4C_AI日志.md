# C4C AI 日志：作业自动求解与排版流水线（LiYaxuan_C4C_homework-solver）

> 本日志如实记录从 starter 到成品过程中**每一步真实发生的事**，包括失败与迭代。

## 时间线

### 2026-10-05 10:20 — 起步：读 starter、定方案

- 完整解压 `c4c-homework-solver-starter`，通读 pipeline / parse / classify / solve / render 全部脚本；
- 确认 starter 缺失：① PDF/Word 摄入未实现（NotImplementedError）；② 线性代数、微分方程求解器未实现（"学生扩展点"）；③ 引擎仅 Claude 单点（C4C 要求迁移）；
- 定方案：`ingest` 补 PDF/Word；`domain_solvers.py` 新写三个领域求解器；`llm_engine.py` 新写国产大模型引擎；`classify` 加新领域路由；SKILL.md 重写为中文迁移版。

### 10:35 — 实现 ingest 扩展

- `read_pdf_text`：用 pdfplumber 逐页 `extract_text()`；
- `read_docx`：python-docx 读段落（Heading 样式转 Markdown 标题）+ 表格；
- 依赖缺失时抛 RuntimeError 并给出安装命令（比 starter 的 NotImplementedError 更友好）。

### 10:50 — 实现 domain_solvers.py（三求解器）

- `solve_matrix_ext`：`\begin{pmatrix}` 正则 → SymPy Matrix；det / inv / eigenvects / rank / linsolve 五个分支；
- `solve_ode_ext`：正则把 `y''`、`y'`、`dy/dx` 归一化为 `Derivative(y(x),x,2)` 等，交给 `dsolve`；
- `solve_physics`：四个公式模板（匀变速 v=v₀+at、自由落体 v=gt、F=ma、圆周运动 a=v²/r），带单位说明。

### 11:05 — 第一轮真实作业测试（run1）→ **失败**

构造 6 题真实作业（极限/行列式/方程组/特征值/ODE/自由落体）跑全流水线：

```
Problem 1: [limit]        ✅ 解出
Problem 2-6: [conceptual] ❌ 全部误分类！
已解: 1/6 (17%)
```

**根因排查**（读 `2_parsed.json`）：
- 文本解析完全正确（矩阵、方程组、ODE、物理关键词都在）；
- 但 `parse_problems` 走了 `classify_to_legacy_type`（T-box bridge），**T-box 本体只覆盖微积分极限领域**，不认识 matrix/ode/physics → 全部返回 conceptual → 被 solve_conceptual 判"概念题需 LLM"。

**修复**：在 `classify.py` 的 bridge 函数开头加入新领域关键词快速路由（矩阵/微分方程/物理），命中即返回，不经过 T-box。**这正对应 C4C 的"引擎迁移"精神：新领域不能只靠 T-box。**

### 11:15 — 第二轮测试（run2）→ 5/6

```
已解: 5/6 (83%)
```

读 `3_solutions.json` 发现两个新问题：
1. **Problem 3（方程组）仍失败**：`reason: 概念题需要 LLM 求解器`。原因：我的 matrix 快速路由关键词漏了"方程组/线性方程组/linear system"——方程组题文本里没有"矩阵"二字。
2. **Problem 6（物理）答案错误**：`t = 9.8 s 时 v = 96.04 m/s`。原因：`_numbers_from_text` 提取到 `[9.8, 3]`，我按 `nums[0]` 取时间，**把 g=9.8 当成了时间**！

**修复**：
1. matrix 路由关键词补充 `方程组`、`线性方程组`、`linear system`；
2. `solve_physics` 增加时间提取正则 `(\d+(?:\.\d+)?)\s*秒` 优先匹配"N 秒"，找不到才退回数字列表。

### 11:25 — 第三轮测试（run3）→ 6/6 ✅

```
已解: 6 道 (100%)
```

**答案逐题核对**（手算/代回验证）：
| 题 | 系统答案 | 核对 |
|----|---------|------|
| P1 极限 | 1 | ✅ 标准极限 |
| P2 行列式 | 1 | ✅ 手算展开 =1 |
| P3 方程组 | (x,y,z)=(1,2,3) | ✅ 代回三式全等 |
| P4 特征值 | λ=1(v=[-1,1])、λ=3(v=[1,1]) | ✅ 代入验证 Av=λv |
| P5 ODE | y=(C₁+C₂eˣ)e²ˣ = C₁e²ˣ+C₂e³ˣ | ✅ 特征根 2,3 |
| P6 自由落体 | v=29.4 m/s、s=44.1 m | ✅ t=3s 计算正确 |

PDF 由 MiKTeX pdflatex 编译成功（≈115KB）。

### 11:35 — 回归测试（starter 自带 test2_limits）

- 结果 9/10：极限相关题全部解出；**AP3（ε-δ 证明题）unsolved（无法提取极限表达式）**；
- 结论：属**设计内降级**——starter 基线靠 Claude 解证明题，本技能无 LLM Key 时按设计标记 unsolved 并给 reason；配置 Qwen/Kimi Key 即可兜底。极限领域功能未被新路由破坏。

## 失败与修复统计

| # | 失败 | 根因 | 修复 |
|---|------|------|------|
| 1 | 6 题中 5 题误分类 conceptual | T-box 仅覆盖极限领域，bridge 不认识新领域 | classify bridge 增加关键词快速路由 |
| 2 | 方程组题不路由到 matrix | 路由关键词漏"方程组" | 补充 3 个关键词 |
| 3 | 物理题把 g=9.8 当时间 | 数字提取顺序错误 | "N 秒"正则优先 |

## 诚实声明

- run1/run2 的失败输出（`test-output/run1`、`run2`）**保留在交付目录中**，可查证迭代过程；
- 无 LLM Key，证明/概念题按设计降级，不虚报 100% 覆盖；
- 物理公式为力学四类模板，未覆盖电磁学等其它分支（超出本次扩展范围，已注明）。
