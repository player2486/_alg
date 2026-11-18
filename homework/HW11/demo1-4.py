import math
import numpy as np
from Numcalc import (derivative, integral_1d, integral_mc_1d,
                     gradient, integral, integral_mc)


def title(s):
    print("\n" + "=" * 70)
    print(s)
    print("=" * 70)


# ---------------------------------------------------------------------
# 1. 單變數數值微分與積分
# ---------------------------------------------------------------------
title("1. 單變數數值微分：f(x)=sin(x)，在 x=1 的 f'(1)=cos(1)")
exact = math.cos(1.0)
print(f"精確值 cos(1) = {exact:.12f}")
print(f"{'method':<12}{'h':>8}{'估計值':>20}{'誤差':>14}")
for method in ["forward", "backward", "central", "five_point"]:
    for h in [1e-1, 1e-3, 1e-5]:
        d = derivative(np.sin, 1.0, h=h, method=method)
        print(f"{method:<12}{h:>8.0e}{d:>20.12f}{abs(d - exact):>14.2e}")

title("1. 單變數數值積分：∫_0^π sin(x) dx = 2")
exact = 2.0
print(f"精確值 = {exact}")
print(f"{'method':<12}{'n':>8}{'估計值':>20}{'誤差':>14}")
for method in ["left", "right", "midpoint", "trapezoid", "simpson"]:
    for n in [10, 100, 1000]:
        v = integral_1d(np.sin, 0, math.pi, n=n, method=method)
        print(f"{method:<12}{n:>8}{v:>20.12f}{abs(v - exact):>14.2e}")

# ---------------------------------------------------------------------
# 2. 單變數蒙地卡羅積分
# ---------------------------------------------------------------------
title("2. 單變數蒙地卡羅積分：∫_0^π sin(x) dx = 2")
print(f"{'N':>10}{'估計值':>16}{'標準誤差':>14}{'實際誤差':>14}")
for N in [10 ** 3, 10 ** 4, 10 ** 5, 10 ** 6, 10 ** 7]:
    est, se = integral_mc_1d(np.sin, 0, math.pi, n_samples=N, seed=1)
    print(f"{N:>10}{est:>16.8f}{se:>14.2e}{abs(est - 2):>14.2e}")
print("→ N 增加 100 倍，誤差約縮小 10 倍（O(1/√N)）。")

# ---------------------------------------------------------------------
# 3. n 變數：梯度與超體積（數值法）
# ---------------------------------------------------------------------
title("3. n 變數梯度：g(x,y,z)=x²y + sin(z) + e^(xz)，在 (1, 2, 0.5)")
g = lambda v: v[0] ** 2 * v[1] + np.sin(v[2]) + np.exp(v[0] * v[2])
p = np.array([1.0, 2.0, 0.5])
exact_grad = np.array([
    2 * p[0] * p[1] + p[2] * math.exp(p[0] * p[2]),   # ∂g/∂x
    p[0] ** 2,                                        # ∂g/∂y
    math.cos(p[2]) + p[0] * math.exp(p[0] * p[2]),    # ∂g/∂z
])
num_grad = gradient(g, p)
print("數值梯度 :", np.array2string(num_grad, precision=10))
print("精確梯度 :", np.array2string(exact_grad, precision=10))
print("最大誤差 : %.2e" % np.max(np.abs(num_grad - exact_grad)))

g100 = lambda v: np.sum(v ** 2, axis=-1)          # ∇ = 2x
x100 = np.linspace(0, 1, 100)
err = np.max(np.abs(gradient(g100, x100) - 2 * x100))
print(f"100 維 f=Σxi² 的梯度，與 2x 的最大誤差：{err:.2e}")

title("3. n 變數黎曼積分（超體積）：∫_[0,1]^3 e^(x+y+z) = (e-1)^3")
h3 = lambda X: np.exp(np.sum(X, axis=-1))
exact3 = (math.e - 1) ** 3
print(f"精確值 = {exact3:.10f}")
for k in [5, 20, 100]:
    v = integral(h3, [0, 0, 0], [1, 1, 1], k=k)
    print(f"k={k:<4}估計 {v:.10f}  誤差 {abs(v - exact3):.2e}")

print("\n超長方體的超體積（f=1）：[0,2]×[0,3]×[0,4]×[0,5] = 120")
one = lambda X: np.ones(X.shape[:-1])
print("估計 =", integral(one, [0] * 4, [2, 3, 4, 5], k=5))

# ---------------------------------------------------------------------
# 4. n 變數蒙地卡羅積分（超體積）
# ---------------------------------------------------------------------
title("4. n 變數蒙地卡羅：∫_[0,1]^3 e^(x+y+z) = (e-1)^3")
for N in [10 ** 4, 10 ** 6]:
    est, se = integral_mc(h3, [0, 0, 0], [1, 1, 1], n_samples=N, seed=1,
                          return_error=True)
    print(f"N={N:<9}估計 {est:.8f}  標準誤差 {se:.2e}  實際誤差 {abs(est - exact3):.2e}")

title("4. 蒙地卡羅算單位 n 維球的超體積（f = 球內為 1、球外為 0，範圍 [-1,1]^n）")
ball = lambda X: (np.sum(X ** 2, axis=-1) <= 1.0).astype(float)
exact_ball = {2: math.pi, 3: 4 * math.pi / 3, 5: 8 * math.pi ** 2 / 15,
              10: math.pi ** 5 / math.factorial(5)}
print(f"{'n':>4}{'MC 估計':>14}{'精確值':>14}{'相對誤差':>12}")
for n in [2, 3, 5, 10]:
    est = integral_mc(ball, [-1] * n, [1] * n, n_samples=2_000_000, seed=1)
    print(f"{n:>4}{est:>14.6f}{exact_ball[n]:>14.6f}{abs(est / exact_ball[n] - 1):>12.2e}")