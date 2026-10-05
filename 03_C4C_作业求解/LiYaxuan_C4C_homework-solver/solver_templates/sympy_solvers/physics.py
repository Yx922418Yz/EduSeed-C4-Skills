#!/usr/bin/env python3
"""
SymPy solver template: 大学物理（力学）University Physics — Mechanics
C4C 新增领域。完整实现见 scripts/domain_solvers.py::solve_physics。
本文件为领域模板：确定性公式模板 + 数值计算。
"""

from sympy import Rational, sqrt, pi

G = 9.8  # m/s² 重力加速度（题目另行给出时以其为准）


def free_fall(t: float) -> tuple[float, float]:
    """自由落体：v = gt，h = ½gt²。返回 (v, h)。"""
    return G * t, Rational(1, 2) * G * t ** 2


def kinematics(v0: float, a: float, t: float) -> tuple[float, float]:
    """匀变速直线运动：v = v0 + at，s = v0·t + ½at²。返回 (v, s)。"""
    v = v0 + a * t
    s = v0 * t + Rational(1, 2) * a * t ** 2
    return v, s


def newton_second(m: float, a: float) -> float:
    """牛顿第二定律：F = ma（单位 N）。"""
    return m * a


def circular_motion(v: float, r: float) -> tuple[float, float]:
    """圆周运动：a = v²/r，ω = v/r。返回 (a, ω)。"""
    return v ** 2 / r, v / r


if __name__ == "__main__":
    # 自检
    v, s = kinematics(2.0, 3.0, 4.0)
    print(f"匀变速 t=4s: v={v} m/s, s={float(s)} m")
    v2, h = free_fall(3.0)
    print(f"自由落体 t=3s: v={float(v2)} m/s, h={float(h)} m")
    print(f"牛顿定律 m=5,a=2: F={newton_second(5, 2)} N")
