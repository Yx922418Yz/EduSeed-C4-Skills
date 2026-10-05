#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
domain_solvers.py — C4C 新扩展领域求解器（学生扩展点实现）

Starter 把 solve_matrix / solve_ode 留作"学生扩展点"（返回 _unsolved）。
本模块实现三大新领域，并在 solve.py 中注册：

  1. 线性代数（linear algebra）：行列式 / 逆矩阵 / 特征值与特征向量 / 矩阵乘法 / 秩 / 线性方程组
  2. 微分方程（differential equations）：一阶可分离 / 一阶线性 / 二阶常系数（dsolve）
  3. 大学物理-力学（physics mechanics）：匀变速直线运动 / 牛顿第二定律 / 自由落体 / 圆周运动

所有求解器输出与 starter 的 _make_solution 信封格式兼容：
  {problem_id, problem_text, solved, steps, answer, answer_latex, solver, sub_solutions}
"""

import re
import traceback

import sympy
from sympy import (
    symbols, Symbol, Function, Rational, pi, sqrt, Eq, latex,
    Matrix, det, eye, zeros, linsolve, symbols as sym_symbols,
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application, convert_xor,
)
from sympy import sin, cos, tan, exp, log, simplify

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)

x, y, z, t = symbols("x y z t")
v0_s, a_s, s_s = symbols("v0 a s", real=True)  # 物理：初速度/加速度/位移
g_s = symbols("g", positive=True)


# ═══════════════════════════════════════════════════════════
# 通用工具
# ═══════════════════════════════════════════════════════════

def _latex_items(problem: dict) -> list[str]:
    """收集题目的所有 LaTeX 数学表达式（含子题）。"""
    out = []
    for m in problem.get("math_expressions", []):
        if m.get("latex"):
            out.append(m["latex"])
    for sub in problem.get("sub_problems", []):
        for m in sub.get("math_expressions", []):
            if m.get("latex"):
                out.append(m["latex"])
    return out


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def _parse_matrix_from_latex(latex_str: str):
    """
    从 LaTeX 矩阵（pmatrix/bmatrix/vmatrix/array）解析为 list[list[str]]。
    返回 None 表示不是矩阵。
    """
    m = re.search(r"\\begin\{(pmatrix|bmatrix|vmatrix|matrix|array)\}(.*?)\\end\{\1\}", latex_str, re.S)
    if not m:
        # 尝试简化写法: [[1,2],[3,4]]
        m2 = re.search(r"\[\[.*?\]\]", latex_str, re.S)
        if not m2:
            return None
        rows = []
        for row in re.findall(r"\[(.*?)\]", m2.group(0), re.S):
            rows.append([c.strip() for c in row.split(",")])
        return rows
    body = m.group(2)
    rows = []
    for line in re.split(r"\\\\", body):
        cells = [c.strip() for c in line.split("&")]
        if cells and cells[0]:
            rows.append(cells)
    return rows or None


def _to_sympy_matrix(rows) -> Matrix:
    """把 list[list[str]] 转为 SymPy Matrix，条目支持表达式（如 -1, 1/2, a）。"""
    data = []
    for row in rows:
        data.append([parse_expr(c, local_dict={"x": x, "y": y, "z": z}, transformations=TRANSFORMATIONS)
                     if c.strip() else 0 for c in row])
    return Matrix(data)


def _find_matrix_objects(problem: dict) -> list[tuple[str, Matrix]]:
    """从题目 LaTeX 中找出所有矩阵对象及其标签（如 A = ...）。返回 [(label, matrix)]。"""
    found = []
    for lt in _latex_items(problem):
        rows = _parse_matrix_from_latex(lt)
        if rows is None:
            continue
        try:
            mat = _to_sympy_matrix(rows)
        except Exception:
            continue
        label = None
        m = re.search(r"([A-Z])\s*=\s*\\begin", lt)
        if m:
            label = m.group(1)
        found.append((label, mat))
    return found


def _numbers_from_text(text: str) -> list[float]:
    """从题目文本中提取数字（含小数/负数）。"""
    return [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", text)]


def _make_solution(problem, steps, answer_expr, solver="sympy"):
    """与 solve.py 信封格式一致。answer_expr 可为 SymPy 对象或字符串。"""
    answer_latex = latex(answer_expr) if not isinstance(answer_expr, str) else answer_expr
    return {
        "problem_id": problem["id"],
        "problem_text": problem["text"],
        "solved": True,
        "steps": steps,
        "answer": str(answer_expr),
        "answer_latex": answer_latex,
        "solver": solver,
        "sub_solutions": [],
    }


def _unsolved(problem, reason):
    return {
        "problem_id": problem["id"],
        "problem_text": problem["text"],
        "solved": False,
        "steps": [],
        "answer": None,
        "answer_latex": "",
        "reason": reason,
        "solver": "none",
        "sub_solutions": [],
    }


# ═══════════════════════════════════════════════════════════
# 领域一：线性代数
# ═══════════════════════════════════════════════════════════

def solve_matrix_ext(problem: dict) -> dict:
    """
    线性代数求解器：
    - 行列式（det / 行列式）
    - 逆矩阵（inverse / 逆矩阵 / ^{-1}）
    - 特征值与特征向量（eigenvalue / 特征值）
    - 矩阵乘法（A \\cdot B / AB / 矩阵乘法）
    - 秩（rank / 秩）
    - 线性方程组（solve system / 方程组 / 解下列方程组）
    """
    text = problem["text"]
    items = _latex_items(problem)
    text_lower = text.lower()
    norm_text = _norm(text)

    matrices = _find_matrix_objects(problem)

    # ── 线性方程组：优先尝试 linsolve ──
    if any(k in text_lower for k in ["方程组", "solve the system", "linear system", "system of equations", "联立"]):
        eqs = []
        for lt in items:
            if "=" in lt and ("x" in lt or "y" in lt or "z" in lt):
                lhs, rhs = lt.split("=", 1)
                try:
                    eqs.append(Eq(parse_expr(lhs, transformations=TRANSFORMATIONS),
                                  parse_expr(rhs, transformations=TRANSFORMATIONS)))
                except Exception:
                    pass
        if eqs:
            sol = linsolve(eqs, x, y, z)
            return _make_solution(
                problem,
                [f"列出方程组（{len(eqs)} 个方程），用 linsolve 求解",
                 "解集为 " + latex(sol)],
                sol,
            )

    # ── 单矩阵运算 ──
    if matrices:
        label, mat = matrices[0]
        rows, cols = mat.shape

        # 行列式（方阵）
        if ("det" in text_lower or "行列式" in text) and rows == cols:
            d = det(mat)
            return _make_solution(
                problem,
                [f"对矩阵 {'A' if label else ''} 求行列式（{rows}×{rows}）",
                 "按行展开/直接调用 det：" + latex(d)],
                d,
            )

        # 特征值/特征向量（方阵）
        if ("eigenvalue" in text_lower or "特征值" in text or "特征向量" in text) and rows == cols:
            eigen_data = mat.eigenvects()
            parts = []
            steps = ["求特征多项式 |λI − A| = 0，解特征值"]
            for eig, mult, vecs in eigen_data:
                parts.append(f"特征值 {latex(eig)}（代数重数 {mult}），特征向量 {latex(vecs[0])}" if vecs
                             else f"特征值 {latex(eig)}（代数重数 {mult}），特征向量（待求）")
            steps.append("；".join(parts))
            return _make_solution(problem, steps, "; ".join(parts))

        # 逆矩阵（方阵）
        if ("inverse" in text_lower or "逆矩阵" in text or "^{-1}" in _norm(text)) and rows == cols:
            inv = mat.inv()
            return _make_solution(
                problem,
                ["对矩阵 A 求逆：A⁻¹ = adj(A)/|A|", "行列式 |A| = " + latex(det(mat)),
                 "结果：" + latex(inv)],
                inv,
            )

        # 秩
        if "rank" in text_lower or "秩" in text:
            r = mat.rank()
            return _make_solution(
                problem,
                ["对矩阵做行化简，统计非零行数", f"rank = {r}"],
                r,
            )

        # 矩阵乘法（两矩阵）
        if len(matrices) >= 2 and ("cdot" in text or "\\times" in text or "乘法" in text
                                   or "AB" in norm_text or "product" in text_lower):
            _, m2 = matrices[1]
            prod = mat * m2
            return _make_solution(
                problem,
                [f"矩阵乘法 A·B（{rows}×{cols} · {m2.shape[0]}×{m2.shape[1]}）",
                 "逐行点乘：" + latex(prod)],
                prod,
            )

        # 默认：求矩阵本身/化简
        return _make_solution(problem, ["题目含矩阵，已解析为 " + latex(mat)], mat)

    return _unsolved(problem, "未能从题目中解析出矩阵或方程组（线性代数扩展）")


# ═══════════════════════════════════════════════════════════
# 领域二：微分方程
# ═══════════════════════════════════════════════════════════

def _normalize_ode_equation(raw: str) -> str:
    """
    把常见 ODE 写法转成 sympy dsolve 可解析形式：
      y'' → Derivative(y(x), x, 2)；y' → Derivative(y(x), x)；y → y(x)
    """
    s = raw.strip()
    # 去掉首尾 $ 与多余括号
    s = s.strip("$")
    s = re.sub(r"^\\left|\\right$", "", s)
    # 二阶导数 y'' / y^{\prime\prime}
    s = re.sub(r"y\s*''|y''|y\^\\prime\\prime|y\\prime\\prime", "Derivative(y(x), x, 2)", s)
    # 一阶导数 y' / y^\prime / y^{\prime}
    s = re.sub(r"y\s*'|y'|y\^\\prime|y\\prime", "Derivative(y(x), x)", s)
    # 独立 y（后面不跟 (x) 或导数）→ y(x)
    s = re.sub(r"(?<![A-Za-z_])y(?!\()", "y(x)", s)
    # 显式微分 \frac{dy}{dx}
    s = re.sub(r"\\frac\{dy\}\{dx\}", "Derivative(y(x), x)", s)
    s = re.sub(r"\\frac\{d\{?y\}?\}\{d\{?x\}?\}", "Derivative(y(x), x)", s)
    # 移除 LaTeX 装饰
    s = s.replace("\\,", "")
    return s


def solve_ode_ext(problem: dict) -> dict:
    """
    微分方程求解器（dsolve）：
    - 一阶：可分离变量 / 一阶线性（y' + p(x)y = q(x)）
    - 二阶常系数：齐次 / 非齐次（y'' + ay' + by = f(x)）
    """
    text = problem["text"]
    text_lower = text.lower()

    # 找出含导数的方程
    eq_candidates = []
    for lt in _latex_items(problem):
        if any(k in _norm(lt) for k in ["y'", "dy/dx", "\\frac{d", "y''", "Derivative"]):
            if "=" in lt:
                eq_candidates.append(lt)

    if not eq_candidates:
        # 从文本提取 y'=... 形式
        m = re.search(r"([^\n]*y'[^\n]*=.*)", text)
        if m:
            eq_candidates.append(m.group(1))

    if not eq_candidates:
        return _unsolved(problem, "未能识别微分方程（微分方程扩展）")

    for raw in eq_candidates:
        try:
            lhs_s, rhs_s = raw.split("=", 1)
            lhs = parse_expr(_normalize_ode_equation(lhs_s),
                             local_dict={"Derivative": sympy.Derivative, "y": Function("y"),
                                         "x": x, "exp": exp, "sin": sin, "cos": cos, "log": log},
                             transformations=TRANSFORMATIONS)
            rhs = parse_expr(_normalize_ode_equation(rhs_s),
                             local_dict={"Derivative": sympy.Derivative, "y": Function("y"),
                                         "x": x, "exp": exp, "sin": sin, "cos": cos, "log": log},
                             transformations=TRANSFORMATIONS)
            eq = Eq(lhs, rhs)
            sol = sympy.dsolve(eq, Function("y")(x))
            # 检查常系数二阶特征方程以生成步骤说明
            order = sympy.ode_order(eq, Function("y")(x))
            return _make_solution(
                problem,
                [f"识别为 {order} 阶常微分方程：" + latex(eq),
                 "使用 dsolve 求通解",
                 "通解：" + latex(sol)],
                sol,
            )
        except Exception as e:
            last_err = str(e)
            continue

    return _unsolved(problem, f"微分方程求解失败：{last_err}")


# ═══════════════════════════════════════════════════════════
# 领域三：大学物理（力学）
# ═══════════════════════════════════════════════════════════

def solve_physics(problem: dict) -> dict:
    """
    大学物理-力学求解器（确定性公式模板 + SymPy 数值计算）。
    支持：
    - 匀变速直线运动：v = v0 + at；s = v0·t + ½at²；v² − v0² = 2as
    - 自由落体：s = ½gt²（g=9.8 m/s²）
    - 牛顿第二定律：F = ma
    - 圆周运动：a = v²/r；ω = v/r
    """
    text = problem["text"]
    text_lower = text.lower()
    nums = _numbers_from_text(text)

    # 时间提取：优先匹配 "N 秒" 模式（避免把 g=9.8 等数值当成时间）
    def _time_from_text() -> float | None:
        m = re.search(r"(\d+(?:\.\d+)?)\s*秒", text)
        return float(m.group(1)) if m else None

    # ── 牛顿第二定律 F = ma ──
    if ("牛顿" in text or "newton" in text_lower or "F=ma" in _norm(text)) \
            and ("力" in text or "force" in text_lower or "F" in text):
        # 求力/质量/加速度
        if "加速度" in text or "acceleration" in text_lower or "a" in _norm(text).lower():
            # 已知 m, a 求 F
            if len(nums) >= 2:
                m, acc = nums[0], nums[1]
                F = m * acc
                return _make_solution(
                    problem,
                    [f"牛顿第二定律 F = ma，代入 m={m} kg、a={acc} m/s²",
                     f"F = {m} × {acc} = {F} N"],
                    f"{F} N",
                )

    # ── 匀变速直线运动 / 自由落体 ──
    if ("匀变速" in text or "uniformly accelerated" in text_lower or "初速度" in text
            or "自由落体" in text or "free fall" in text_lower or "fall" in text_lower
            or "直线运动" in text):
        # 自由落体（默认 g = 9.8）
        if "自由落体" in text or "free fall" in text_lower or "从静止下落" in text or "从静止开始下落" in text:
            g = 9.8
            t_val = _time_from_text()
            if t_val is None and len(nums) >= 1:
                t_val = nums[0]
            if t_val is not None:
                v = g * t_val
                s_val = Rational(1, 2) * g * t_val ** 2
                return _make_solution(
                    problem,
                    [f"自由落体：v = gt，s = ½gt²（g = {g} m/s²）",
                     f"t = {t_val} s 时：v = {g}×{t_val} = {v} m/s",
                     f"s = ½×{g}×{t_val}² = {float(s_val)} m"],
                    f"v = {v} m/s，s = {float(s_val)} m",
                )
        # 匀变速：求 v / s / a
        if len(nums) >= 2:
            v0 = nums[0]
            t_val = nums[1] if len(nums) > 1 else nums[0]
            # 求加速度 a = (v − v0)/t
            if len(nums) >= 3 and ("加速度" in text or "acceleration" in text_lower):
                v_final, v0, t_val = nums[0], nums[1], nums[2]
                a_calc = (v_final - v0) / t_val
                s_calc = v0 * t_val + Rational(1, 2) * a_calc * t_val ** 2
                return _make_solution(
                    problem,
                    ["匀变速运动公式：a = (v−v0)/t，s = v0·t + ½at²",
                     f"a = ({v_final}−{v0})/{t_val} = {a_calc} m/s²",
                     f"s = {v0}×{t_val} + ½×{a_calc}×{t_val}² = {float(s_calc)} m"],
                    f"a = {a_calc} m/s²，s = {float(s_calc)} m",
                )
            # 求末速度 v = v0 + at
            if len(nums) >= 3:
                v0, a_val, t_val = nums[0], nums[1], nums[2]
                v_final = v0 + a_val * t_val
                s_calc = v0 * t_val + Rational(1, 2) * a_val * t_val ** 2
                return _make_solution(
                    problem,
                    ["匀变速运动公式：v = v0 + at，s = v0·t + ½at²",
                     f"v = {v0} + {a_val}×{t_val} = {v_final} m/s",
                     f"s = {v0}×{t_val} + ½×{a_val}×{t_val}² = {float(s_calc)} m"],
                    f"v = {v_final} m/s，s = {float(s_calc)} m",
                )

    # ── 圆周运动 ──
    if "圆周" in text or "circular" in text_lower:
        if len(nums) >= 2:
            v_val, r_val = nums[0], nums[1]
            a_c = v_val ** 2 / r_val
            omega = v_val / r_val
            return _make_solution(
                problem,
                ["圆周运动：向心加速度 a = v²/r，角速度 ω = v/r",
                 f"a = {v_val}²/{r_val} = {a_c} m/s²",
                 f"ω = {v_val}/{r_val} = {omega} rad/s"],
                f"a = {a_c} m/s²，ω = {omega} rad/s",
            )

    return _unsolved(problem, "物理题模式未能匹配（大学物理扩展：支持匀变速/自由落体/牛顿定律/圆周运动）")


# ═══════════════════════════════════════════════════════════
# 注册表（供 solve.py 引用）
# ═══════════════════════════════════════════════════════════

EXTENDED_SOLVERS = {
    "matrix": solve_matrix_ext,
    "ode": solve_ode_ext,
    "physics": solve_physics,
}
