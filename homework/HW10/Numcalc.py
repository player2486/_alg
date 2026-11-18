import numpy as np


# =====================================================================
# 1. 單變數：數值微分與數值積分
# =====================================================================

def derivative(f, x, h=1e-5, method="central"):
    if method == "forward":
        return (f(x + h) - f(x)) / h
    if method == "backward":
        return (f(x) - f(x - h)) / h
    if method == "central":
        return (f(x + h) - f(x - h)) / (2 * h)
    if method == "five_point":
        return (-f(x + 2 * h) + 8 * f(x + h) - 8 * f(x - h) + f(x - 2 * h)) / (12 * h)
    raise ValueError(f"未知的 method: {method}")


def integral_1d(f, a, b, n=1000, method="simpson"):
    h = (b - a) / n
    if method == "left":
        x = a + h * np.arange(n)
        return h * np.sum(f(x))
    if method == "right":
        x = a + h * np.arange(1, n + 1)
        return h * np.sum(f(x))
    if method == "midpoint":
        x = a + h * (np.arange(n) + 0.5)
        return h * np.sum(f(x))
    if method == "trapezoid":
        x = np.linspace(a, b, n + 1)
        y = f(x)
        return h * (y[0] / 2 + np.sum(y[1:-1]) + y[-1] / 2)
    if method == "simpson":
        if n % 2 == 1:
            n += 1
            h = (b - a) / n
        x = np.linspace(a, b, n + 1)
        y = f(x)
        return h / 3 * (y[0] + y[-1] + 4 * np.sum(y[1:-1:2]) + 2 * np.sum(y[2:-1:2]))
    raise ValueError(f"未知的 method: {method}")


# =====================================================================
# 2. 單變數：蒙地卡羅積分
# =====================================================================

def integral_mc_1d(f, a, b, n_samples=1_000_000, seed=None):
    rng = np.random.default_rng(seed)
    x = rng.uniform(a, b, n_samples)
    y = f(x)
    length = b - a
    est = length * y.mean()
    stderr = length * y.std(ddof=1) / np.sqrt(n_samples)
    return est, stderr


# =====================================================================
# 3. n 變數：梯度（數值微分）與黎曼積分（超體積）
# =====================================================================

def gradient(f, x, h=1e-5):
    x = np.asarray(x, dtype=float)
    g = np.empty_like(x)
    for i in range(x.size):
        e = np.zeros_like(x)
        e[i] = h
        g[i] = (f(x + e) - f(x - e)) / (2 * h)
    return g


def integral(f, low, high, k=None, max_points=2_000_000,
             vectorized=True, chunk=200_000):
    low = np.asarray(low, dtype=float).ravel()
    high = np.asarray(high, dtype=float).ravel()
    if low.shape != high.shape:
        raise ValueError("low 與 high 的長度必須相同")
    n = low.size

    if k is None:
        k = int(round(max_points ** (1.0 / n)))
        while (k + 1) ** n <= max_points:
            k += 1
        while k > 1 and k ** n > max_points:
            k -= 1
        if k < 2:
            raise ValueError(
                f"{n} 維時，每維只切 2 格就需要 2^{n} ≈ {float(2 ** n):.3e} 個格點，"
                f"超過上限 {max_points:,}，黎曼格點法不可行（維度災難）。"
                f"可改用蒙地卡羅法，或明確指定 k=1（每維只取 1 點，誤差會很大）。")

    total = k ** n
    if total > max_points:
        raise ValueError(
            f"需要 {k}^{n} ≈ {float(total):.3e} 個格點，超過上限 {max_points:,}。")

    h = (high - low) / k  
    cell_volume = float(np.prod(h)) 

    acc = 0.0
    for start in range(0, total, chunk):
        idx = np.arange(start, min(start + chunk, total), dtype=np.int64)
        X = np.empty((idx.size, n))
        r = idx
        for d in range(n):
            r, digit = np.divmod(r, k)
            X[:, d] = low[d] + (digit + 0.5) * h[d]
        if vectorized:
            vals = f(X)
        else:
            vals = np.apply_along_axis(f, 1, X)
        acc += float(np.sum(vals))
    return acc * cell_volume


# =====================================================================
# 4. n 變數：蒙地卡羅積分（超體積）
# =====================================================================

def integral_mc(f, low, high, n_samples=1_000_000, seed=None,
                vectorized=True, chunk=100_000, return_error=False):
    low = np.asarray(low, dtype=float).ravel()
    high = np.asarray(high, dtype=float).ravel()
    if low.shape != high.shape:
        raise ValueError("low 與 high 的長度必須相同")
    n = low.size
    volume = float(np.prod(high - low))
    rng = np.random.default_rng(seed)

    s1 = 0.0   # Σ f
    s2 = 0.0   # Σ f^2
    done = 0
    while done < n_samples:
        m = min(chunk, n_samples - done)
        X = rng.uniform(low, high, size=(m, n))
        if vectorized:
            vals = np.asarray(f(X), dtype=float)
        else:
            vals = np.apply_along_axis(f, 1, X).astype(float)
        s1 += vals.sum()
        s2 += np.square(vals).sum()
        done += m

    mean = s1 / n_samples
    est = volume * mean
    if not return_error:
        return est
    var = max(s2 / n_samples - mean ** 2, 0.0) * n_samples / (n_samples - 1)
    stderr = volume * np.sqrt(var / n_samples)
    return est, stderr