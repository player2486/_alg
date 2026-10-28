import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from TSP import *


def setup_cjk_font():
    candidates = [
        r"C:\Windows\Fonts\msjh.ttc",
        r"C:\Windows\Fonts\msjh.ttf",
        r"C:\Windows\Fonts\msyh.ttc",  
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            fm.fontManager.addfont(path)
            plt.rcParams["font.family"] = fm.FontProperties(fname=path).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False


setup_cjk_font()

g = greedy()
results = [
    ("1. 改良法 (2-opt)", two_opt_improve(g)),
    ("2. 爬山演算法", hill_climbing(seed=0)),
    ("3. 模擬退火法", simulated_annealing(seed=0)),
    ("4. 梯度下降法", gradient_descent(seed=0)),
    ("5. 貪婪演算法", g),
]
lens = [tour_length(t) for _, t in results]
best = min(lens)
xy = np.array(CITIES)

fig, axes = plt.subplots(1, 5, figsize=(25, 5.6))
for ax, (name, t), L in zip(axes, results, lens):
    p = xy[t + [t[0]]]
    ax.plot(p[:, 0], p[:, 1], "-", color="#3b6fb6", lw=1.6, zorder=1)
    ax.scatter(xy[:, 0], xy[:, 1], s=36, color="#d9534f", zorder=2)
    for i, (x, y) in enumerate(CITIES):
        ax.annotate(str(i), (x, y), xytext=(3, 3), textcoords="offset points", fontsize=7)
    ax.scatter(*xy[t[0]], s=220, facecolors="none", edgecolors="green", lw=2.5, zorder=3)
    tag = "  (best)" if abs(L - best) < 1e-6 else ""
    ax.set_title(f"{name}\n長度 = {L:.2f}{tag}", fontsize=12)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])

fig.suptitle("旅行推銷員問題：五種方法比較（20 城市，綠圈＝起點）", fontsize=14)
plt.tight_layout(rect=[0, 0, 1, 0.92])
plt.savefig("tsp_results.png", dpi=110)
print("已儲存 tsp_results.png")
plt.show() 