# C4C 方案设计：作业自动求解与排版流水线（LiYaxuan_C4C_homework-solver）

## 一、挑战要求与我的目标

C4C 挑战要求：**拿 starter kit 做"拿来主义"改造，交付一个可运行的作业自动求解技能**。
starter（`c4c-homework-solver-starter`）是"微积分极限领域 + 仅 Claude 引擎"的最小骨架，
两份核心缺失留作学生扩展点：① PDF/Word 摄入（Level 2）；② 线性代数 / 微分方程求解器。

我的目标（三件事）：
1. **引擎迁移**：把"仅 Claude 单点"迁移为「SymPy 确定性求解 + 国产大模型（Qwen/Kimi）降级深解」，零云端依赖也能跑；
2. **领域扩展**：补全 starter 留作扩展点的线性代数、微分方程求解器，并**新增大学物理（力学）领域**；
3. **真实验证**：用一份覆盖四个领域的 6 题真实作业跑通全流水线并编译 PDF。

## 二、总体架构（五阶段流水线）

```
作业文件(.md/.pdf/.docx/图片)
   │  Stage 1 摄入 ingest.py        ← C4C扩展：实现 read_pdf_text/pdfplumber、read_docx/python-docx
   ▼
结构化文本(1_ingested.json)
   │  Stage 2 解析 parse_problems.py ← C4C扩展：TYPE_KEYWORDS 新增 matrix/ode/physics
   ▼
题目+分类(2_parsed.json)
   │  Stage 3 求解 solve.py          ← C4C扩展：注册新领域求解器 + LLM降级
   │           └ domain_solvers.py   ← C4C新增：solve_matrix_ext / solve_ode_ext / solve_physics
   │           └ llm_engine.py       ← C4C新增：Qwen→Kimi→OpenAI兼容，环境变量驱动
   ▼
解答(3_solutions.json)
   │  Stage 4 排版 render  → homework.tex
   │  Stage 5 编译 xelatex/pdflatex → homework.pdf
   ▼
可提交 PDF
```

## 三、设计决策与理由

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 求解引擎 | SymPy 为主、LLM 降级 | 确定性、可审计、可离线；LLM 只兜底证明/概念题 |
| LLM 选型 | 通义千问(Qwen) → Kimi → OpenAI 兼容 三级降级 | 国产大模型、环境变量驱动、不锁死单点 |
| 领域扩展方式 | `domain_solvers.py` 一个模块挂三个求解器 + 独立领域 YAML/T-box | 与 starter 的 T-box 架构一致，可插拔 |
| 分类路由 | 新增领域关键词快速路由优先于 T-box | T-box 本体仅覆盖极限，先快路由再 T-box 兜底 |
| 物理题数值提取 | 正则优先匹配 "N 秒" 模式 | 避免把 g=9.8 误当时间（实测踩坑，见 AI 日志） |
| 交付形态 | 技能文件夹 + .skill 打包 + 五类交付文件 | 符合 C4 挑战 hammer 规范 |

## 四、交付物清单

| 文件 | 作用 |
|------|------|
| `SKILL.md` | 技能主指令（迁移说明 + 使用流程） |
| `scripts/pipeline.py` 等 | 五阶段流水线（starter 保留） |
| `scripts/ingest.py` | C4C 扩展：PDF/Word 摄入 |
| `scripts/parse_problems.py` | C4C 扩展：physics 分类关键词 |
| `scripts/classify.py` | C4C 扩展：新领域关键词快速路由 |
| `scripts/solve.py` | C4C 扩展：注册新求解器 + LLM 降级 |
| `scripts/domain_solvers.py` | **C4C 新增**：三个领域求解器（矩阵/ODE/物理） |
| `scripts/llm_engine.py` | **C4C 新增**：国产大模型引擎 |
| `domain_skills/linear_algebra.yaml` | **C4C 新增**：线性代数领域知识 |
| `domain_skills/differential_equations.yaml` | **C4C 新增**：微分方程领域知识 |
| `domain_skills/physics_mechanics.yaml` | **C4C 新增**：大学物理力学领域知识 |
| `solver_templates/sympy_solvers/{linear_algebra,ode,physics}.py` | **C4C 新增**：领域模板（可独立运行） |
| `examples/real_homework.md` | 真实作业测试样例 |

## 五、验证方案与结果

| 测试 | 结果 |
|------|------|
| 真实作业（6 题：极限/行列式/方程组/特征值/ODE/自由落体） | **6/6 解出（100%）且答案全部正确** |
| 答案核对 | P1=1 ✓；P2 det=1 ✓；P3 (x,y,z)=(1,2,3) ✓；P4 λ=1,3 ✓；P5 y=(C1+C2eˣ)e²ˣ ✓；P6 v=29.4 m/s, s=44.1 m ✓ |
| PDF 编译 | MiKTeX pdflatex 编译成功（homework.pdf ≈115KB） |
| 回归（starter 自带 test2 极限测试 10 题） | 9/10（AP3 ε-δ 证明题需 LLM，属设计内降级） |

## 六、边界与已知限制

- 无 LLM Key 时证明/概念题标记 unsolved 并给出 reason（starter 基线靠 Claude 才能解，本技能降级为纯 SymPy）；
- 扫描版 PDF 需 OCR（pytesseract 占位）；
- 物理公式模板覆盖力学四类（匀变速/自由落体/牛顿定律/圆周运动）。
