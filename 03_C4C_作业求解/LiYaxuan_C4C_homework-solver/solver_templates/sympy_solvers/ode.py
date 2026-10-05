#!/usr/bin/env python3
"""
SymPy solver template: 微分方程（Differential Equations）
C4C 新增领域。完整实现见 scripts/domain_solvers.py::solve_ode_ext。
本文件为领域模板：可独立运行的最小实现 + 领域知识注释。
"""

import re
import sympy
from sympy import symbols, Function, Eq, latex, exp, sin, cos, log
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)
x = symbols("x")
y = Function("y")


def normalize_ode(raw: str) -> str:
    """把常见 ODE 写法转为 dsolve 可解析形式。"""
    s = raw.strip().strip("$")
    s = re.sub(r"y\s*''|y''|y\^\\prime\\prime", "Derivative(y(x), x, 2)", s)
    s = re.sub(r"y\s*'|y'|y\^\\prime", "Derivative(y(x), x)", s)
    s = re.sub(r"(?<![A-Za-z_])y(?!\()", "y(x)", s)
    s = re.sub(r"\\frac\{dy\}\{dx\}", "Derivative(y(x), x)", s)
    s = re.sub(r"\\frac\{d\{?y\}?\}\{d\{?x\}?\}", "Derivative(y(x), x)", s)
    return s


def solve_ode_equation(ode_str: str) -> str:
    """解一个形如 y'' + ay' + by = f(x) 或 y' = g(x,y) 的方程。"""
    lhs_s, rhs_s = ode_str.split("=", 1)
    local = {"Derivative": sympy.Derivative, "y": y, "x": x,
             "exp": exp, "sin": sin, "cos": cos, "log": log}
    lhs = parse_expr(normalize_ode(lhs_s), local_dict=local, transformations=TRANSFORMATIONS)
    rhs = parse_expr(normalize_ode(rhs_s), local_dict=local, transformations=TRANSFORMATIONS)
    sol = sympy.dsolve(Eq(lhs, rhs), y(x))
    return latex(sol)


if __name__ == "__main__":
    # 自检：一阶线性 y' - 2y = 3e^x
    print("y' - 2y = 3e^x →", solve_ode_equation("y' - 2*y - 3*exp(x)"))
