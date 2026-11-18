import time
import numpy as np
from Numcalc import integral, integral_mc

DIMS = [1, 2, 5, 100]


def f(x):
    return np.sum(np.asarray(x) ** 2, axis=-1)


def title(s):
    print("\n" + "=" * 72)
    print(s)
    print("=" * 72)


# ---------------------------------------------------------------------
# 第 5 題：黎曼積分
# ---------------------------------------------------------------------
title("5. 黎曼積分（中點法）：integral(f, low, high)")
print(f"{'n':>4}{'每維格數 k':>12}{'總格點數':>14}{'估計值':>16}{'精確值':>12}"
      f"{'誤差':>12}{'秒':>8}")
for n in DIMS:
    low, high = np.zeros(n), np.ones(n)
    exact = n / 3
    try:
        t0 = time.perf_counter()
        v = integral(f, low, high)
        dt = time.perf_counter() - t0
        k = int(round(2_000_000 ** (1 / n)))
        while (k + 1) ** n <= 2_000_000:
            k += 1
        while k > 1 and k ** n > 2_000_000:
            k -= 1
        print(f"{n:>4}{k:>12}{k ** n:>14,}{v:>16.8f}{exact:>12.6f}"
              f"{abs(v - exact):>12.2e}{dt:>8.2f}")
    except ValueError as e:
        print(f"{n:>4}  無法計算：{e}")

print("\n--- 100 維：強制每維只取 1 個點（k=1，只算超方塊中心 1 點）---")
v = integral(f, np.zeros(100), np.ones(100), k=1)
print(f"k=1 的結果 = {v:.6f}，精確值 = {100 / 3:.6f}，誤差 = {abs(v - 100 / 3):.4f}")
print("（即使只有 1 個點也有明顯誤差；要變準就得增加格數，但 k=2 就要 2^100 個點。）")

print("\n--- 收斂性：2 維，增加每維格數 k ---")
print(f"{'k':>6}{'估計值':>16}{'誤差':>12}")
for k in [2, 5, 10, 100, 1000]:
    v = integral(f, [0, 0], [1, 1], k=k)
    print(f"{k:>6}{v:>16.10f}{abs(v - 2 / 3):>12.2e}")
print("（中點法每維誤差 = h²/12，所以 k 加 10 倍，誤差約縮小 100 倍。）")

# ---------------------------------------------------------------------
# 第 6 題：蒙地卡羅法
# ---------------------------------------------------------------------
title("6. 蒙地卡羅法：integral_mc(f, low, high)，N = 1,000,000")
print(f"{'n':>4}{'估計值':>16}{'精確值':>12}{'標準誤差':>12}{'實際誤差':>12}{'秒':>8}")
for n in DIMS:
    low, high = np.zeros(n), np.ones(n)
    t0 = time.perf_counter()
    est, se = integral_mc(f, low, high, n_samples=1_000_000, seed=2026,
                          return_error=True)
    dt = time.perf_counter() - t0
    print(f"{n:>4}{est:>16.6f}{n / 3:>12.6f}{se:>12.2e}"
          f"{abs(est - n / 3):>12.2e}{dt:>8.2f}")

print("\n--- 100 維：蒙地卡羅誤差隨取樣數 N 的變化 ---")
print(f"{'N':>10}{'估計值':>14}{'標準誤差':>12}{'實際誤差':>12}")
for N in [10 ** 3, 10 ** 4, 10 ** 5, 10 ** 6, 10 ** 7]:
    est, se = integral_mc(f, np.zeros(100), np.ones(100), n_samples=N,
                          seed=2026, return_error=True)
    print(f"{N:>10}{est:>14.5f}{se:>12.2e}{abs(est - 100 / 3):>12.2e}")