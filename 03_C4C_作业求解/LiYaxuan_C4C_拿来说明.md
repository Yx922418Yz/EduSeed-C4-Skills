# C4C 拿来说明：作业自动求解与排版流水线（LiYaxuan_C4C_homework-solver）

> 依据 C4 挑战规则，本技能是 **starter kit 的"拿来主义"改造**。本文说明：拿了什么、改了什么、为什么这样改、哪些是原样保留。

## 一、我拿了 starter 的什么

| starter 组件 | 使用方式 |
|--------------|----------|
| `c4c-homework-solver-starter` 全量代码 | 复制为技能根目录，作为可运行底座 |
| `scripts/pipeline.py` | 原样保留（五阶段编排） |
| `scripts/parse_problems.py` 主体 | 保留（题目识别/数学公式提取/题号分割） |
| `scripts/solve.py` 微积分求解 | 保留（limit/tangent/epsilon_delta 的 SymPy 实现） |
| `scripts/render*.py` + `references/homework_template.tex` | 保留（LaTeX 排版与中文模板） |
| `scripts/classify.py` T-box 分类器 | 保留（微积分领域） |
| `domain_skills/calculus_limits.yaml` + `solver_templates/` | 保留（极限领域知识） |
| `test_cases/` | 保留（回归测试用） |

## 二、我改了什么

| 文件 | 改动 |
|------|------|
| `SKILL.md` | 重写为中文迁移版：新增领域表、国产大模型引擎说明、输入输出规范 |
| `scripts/ingest.py` | **实现** starter 未实现的 `read_pdf_text`（pdfplumber）、`read_docx`（python-docx） |
| `scripts/parse_problems.py` | TYPE_KEYWORDS 新增 `physics` 类别，priority 加入 physics |
| `scripts/classify.py` | bridge 函数新增 matrix/ode/physics 关键词快速路由（先于 T-box） |
| `scripts/solve.py` | 注册三个新求解器到 SOLVERS；规则失败自动走 LLM 降级 |

## 三、我新增了什么（starter 没有的）

| 文件 | 内容 |
|------|------|
| `scripts/domain_solvers.py` | `solve_matrix_ext`（行列式/逆/特征值/秩/linsolve）、`solve_ode_ext`（dsolve 归一化）、`solve_physics`（四类力学公式模板） |
| `scripts/llm_engine.py` | 国产大模型引擎：Qwen(DashScope) → Kimi(Moonshot) → OpenAI 兼容，环境变量驱动，未配置自动降级 |
| `domain_skills/linear_algebra.yaml` | 线性代数领域知识（Strang + 同济教材蒸馏） |
| `domain_skills/differential_equations.yaml` | 微分方程领域知识（Boyce & DiPrima + 同济高数） |
| `domain_skills/physics_mechanics.yaml` | 大学物理力学领域知识（Halliday + 马文蔚） |
| `solver_templates/sympy_solvers/linear_algebra.py` | 可独立运行的矩阵模板 |
| `solver_templates/sympy_solvers/ode.py` | 可独立运行的 ODE 模板 |
| `solver_templates/sympy_solvers/physics.py` | 可独立运行的物理公式模板 |
| `examples/real_homework.md` | 四领域 6 题真实作业（测试证据） |

## 四、关键决策与理由

1. **为什么迁移引擎**：starter 唯一推理源是 Claude（私有、有配额、不透明）。迁移为「SymPy 确定性求解 + 国产大模型降级」后：可审计、可离线、Key 可选、失败有 reason——这正是 C4C 挑战"引擎迁移"的意图。
2. **为什么保留 T-box**：极限领域已打磨完整，重写是浪费；新领域用快速路由并行为主，T-box 继续处理极限，两者无冲突（回归 9/10 证明兼容）。
3. **为什么新增物理领域**：挑战要求"新增能力"；用户（李亚轩）为软件工程专业，大学物理是必修公共课，力学部分公式确定性强，最适合确定性求解。

## 五、验证结果（改造前后对比）

| 指标 | starter 基线 | 本技能 |
|------|-------------|--------|
| 极限测试（test2） | 17/18（94.4%，靠 Claude） | 9/10（90%，纯 SymPy；AP3 证明题需 LLM，配置 Key 即恢复） |
| 真实四领域作业 | 不支持（无矩阵/ODE/物理求解器） | **6/6（100%）答案全部正确** |
| PDF 编译 | ✅ | ✅ |
| 离线可用 | ❌（必须 Claude） | ✅（纯 SymPy 零依赖） |

## 六、引用来源

- Gilbert Strang, *Introduction to Linear Algebra*, 5th ed.
- 同济大学《线性代数》第六版
- Boyce & DiPrima, *Elementary Differential Equations*, 10th ed.
- 同济大学《高等数学》下册（微分方程章节）
- Halliday, Resnick & Walker, *Fundamentals of Physics*, 10th ed.
- 马文蔚《物理学》第七版上册
- starter kit: `c4c-homework-solver-starter`（来源：EduSeed C4 挑战资料）
