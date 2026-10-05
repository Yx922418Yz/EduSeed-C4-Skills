#!/usr/bin/env python3
"""
SymPy solver template: 线性代数（Linear Algebra）
C4C 新增领域。完整实现见 scripts/domain_solvers.py::solve_matrix_ext。
本文件为领域模板：独立可运行的最小实现 + 领域知识注释。
"""

import re
from sympy import Matrix, det, linsolve, symbols, latex, Eq
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)
x, y, z = symbols("x y z")


def parse_matrix_from_latex(latex_str: str) -> Matrix | None:
    """解析 pmatrix/bmatrix 为 SymPy Matrix。"""
    m = re.search(r"\\begin\{(pmatrix|bmatrix|vmatrix|matrix)\}(.*?)\\end\{\1\}", latex_str, re.S)
    if not m:
        return None
    rows = []
    for line in re.split(r"\\\\", m.group(2)):
        cells = [c.strip() for c in line.split("&")]
        if cells and cells[0]:
            rows.append([parse_expr(c, transformations=TRANSFORMATIONS) if c else 0 for c in cells])
    return Matrix(rows)


def solve_determinant(A: Matrix) -> str:
    """行列式。"""
    return f"det(A) = {latex(det(A))}"


def solve_inverse(A: Matrix) -> str:
    """逆矩阵。"""
    return f"A⁻¹ = {latex(A.inv())}"


def solve_eigen(A: Matrix) -> str:
    """特征值与特征向量。"""
    parts = []
    for eig, mult, vecs in A.eigenvects():
        parts.append(f"λ={latex(eig)}（重数 {mult}），v={latex(vecs[0])}" if vecs else f"λ={latex(eig)}")
    return "；".join(parts)


def solve_system(equations: list[Eq]) -> str:
    """线性方程组。"""
    return f"解集 = {latex(linsolve(equations, x, y, z))}"


if __name__ == "__main__":
    # 自检
    A = Matrix([[1, 2], [3, 4]])
    print("行列式:", solve_determinant(A))
    print("逆矩阵:", solve_inverse(A))
    print("特征:", solve_eigen(A))
