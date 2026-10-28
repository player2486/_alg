import math, random, time
import numpy as np

N_CITIES = 20
rng = random.Random(42)
CITIES = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(N_CITIES)]
DIST = np.array([[math.dist(a, b) for b in CITIES] for a in CITIES])


def tour_length(tour):
    return sum(DIST[tour[i], tour[(i + 1) % len(tour)]] for i in range(len(tour)))

def two_opt_improve(tour):
    tour, n = tour[:], len(tour)
    while True:
        best_delta, best = -1e-12, None
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                a, b = tour[i], tour[i + 1]
                c, d = tour[j], tour[(j + 1) % n]
                delta = DIST[a, c] + DIST[b, d] - DIST[a, b] - DIST[c, d]
                if delta < best_delta:
                    best_delta, best = delta, (i, j)
        if best is None:
            return tour
        i, j = best
        tour[i + 1:j + 1] = reversed(tour[i + 1:j + 1])


def hill_climbing(iters=20000, seed=0):
    r = random.Random(seed)
    tour = list(range(N_CITIES)); r.shuffle(tour)
    cur = tour_length(tour)
    for _ in range(iters):
        i, j = r.sample(range(N_CITIES), 2)
        tour[i], tour[j] = tour[j], tour[i]
        new = tour_length(tour)
        if new < cur:
            cur = new
        else:
            tour[i], tour[j] = tour[j], tour[i]
    return tour


def simulated_annealing(T0=100, T_end=1e-3, alpha=0.995, per_temp=100, seed=0):
    r = random.Random(seed)
    tour = list(range(N_CITIES)); r.shuffle(tour)
    cur = tour_length(tour)
    best, best_len = tour[:], cur
    T = T0
    while T > T_end:
        for _ in range(per_temp):
            i, j = sorted(r.sample(range(N_CITIES), 2))
            cand = tour[:i] + tour[i:j + 1][::-1] + tour[j + 1:]
            d = tour_length(cand) - cur
            if d < 0 or r.random() < math.exp(-d / T):
                tour, cur = cand, cur + d
                if cur < best_len:
                    best, best_len = tour[:], cur
        T *= alpha
    return best


def gradient_descent(steps=3000, lr=0.05, lam=1.0, seed=0):
    n = N_CITIES
    Dn = DIST / DIST.mean()
    W = np.random.RandomState(seed).randn(n, n) * 0.01
    for t in range(steps):
        E = np.exp(W - W.max(1, keepdims=True))
        P = E / E.sum(1, keepdims=True)
        gP = np.roll(P, -1, 0) @ Dn + np.roll(P, 1, 0) @ Dn
        col = P.sum(0) - 1.0
        gP += 2 * lam * col[None, :]
        gW = P * (gP - (gP * P).sum(1, keepdims=True))
        W -= lr * (1 - t / steps * 0.9) * gW * 10
    E = np.exp(W - W.max(1, keepdims=True))
    Pm = E / E.sum(1, keepdims=True)
    tour = [None] * n
    for _ in range(n):                       # 貪婪解碼
        k, i = np.unravel_index(np.argmax(Pm), Pm.shape)
        tour[k] = int(i)
        Pm[k, :] = -1; Pm[:, i] = -1
    return tour

def greedy(start=0):
    unvisited = set(range(N_CITIES)) - {start}
    tour = [start]
    while unvisited:
        nxt = min(unvisited, key=lambda c: DIST[tour[-1], c])
        tour.append(nxt)
        unvisited.remove(nxt)
    return tour


if __name__ == "__main__":
    runs = [("1. 改良法 (2-opt)", lambda: two_opt_improve(greedy())),
            ("2. 爬山演算法", hill_climbing),
            ("3. 模擬退火法", simulated_annealing),
            ("4. 梯度下降法", gradient_descent),
            ("5. 貪婪演算法", greedy)]
    for name, f in runs:
        t0 = time.time(); tour = f(); dt = time.time() - t0
        assert sorted(tour) == list(range(N_CITIES))
        print(f"{name:18s} 長度 = {tour_length(tour):8.2f}  耗時 = {dt:6.3f}s")