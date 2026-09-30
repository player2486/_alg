"""
heat_equation.py -- 用迭代法求解 2D 穩態熱傳導問題 (Laplace 方程)

問題描述：
    一個正方形金屬板，四周溫度固定，內部沒有熱源。
    求穩態時板上的溫度分佈。

數學模型：
    ∇²u = 0  （Laplace 方程）
    邊界條件：
       上邊：u = 100°C
       下邊：u = 0°C
       左邊：u = 50°C
       右邊：u = 50°C

數值方法：
    1. 有限差分法：把連續區域離散成網格
    2. Gauss-Seidel 迭代法：求解線性方程組

執行：python heat_equation.py
"""

import numpy as np
import time


def solve_heat_equation(n=20, max_iter=5000, tol=1e-4):
    """
    用 Gauss-Seidel 迭代法求解 2D Laplace 方程
    
    參數：
        n: 網格大小 n x n
        max_iter: 最大迭代次數
        tol: 收斂容差
    
    回傳：
        u: 溫度分佈矩陣
        iterations: 實際迭代次數
        elapsed: 耗時（秒）
    """
    # 初始化溫度場
    u = np.zeros((n, n))
    
    # 邊界條件
    u[0, :] = 100.0   # 上邊
    u[-1, :] = 0.0    # 下邊
    u[:, 0] = 50.0    # 左邊
    u[:, -1] = 50.0   # 右边
    
    # 內部點初始值（取邊界平均）
    u[1:-1, 1:-1] = 37.5
    
    start = time.perf_counter()
    
    for iteration in range(max_iter):
        u_old = u.copy()
        
        # Gauss-Seidel 迭代：每個點更新為四鄰的平均
        for i in range(1, n - 1):
            for j in range(1, n - 1):
                u[i, j] = 0.25 * (u[i+1, j] + u[i-1, j] + u[i, j+1] + u[i, j-1])
        
        # 收斂判定：最大變化量小於容差
        max_change = np.max(np.abs(u - u_old))
        if max_change < tol:
            elapsed = time.perf_counter() - start
            return u, iteration + 1, elapsed
    
    elapsed = time.perf_counter() - start
    return u, max_iter, elapsed


def solve_vectorized(n=20, max_iter=5000, tol=1e-4):
    """
    向量化版本（更快的實作）
    """
    u = np.zeros((n, n))
    u[0, :] = 100.0
    u[-1, :] = 0.0
    u[:, 0] = 50.0
    u[:, -1] = 50.0
    u[1:-1, 1:-1] = 37.5
    
    start = time.perf_counter()
    
    for iteration in range(max_iter):
        u_old = u.copy()
        
        # 向量化更新（使用 slicing）
        u[1:-1, 1:-1] = 0.25 * (
            u[2:, 1:-1] +    # 下
            u[:-2, 1:-1] +   # 上
            u[1:-1, 2:] +    # 右
            u[1:-1, :-2]     # 左
        )
        
        max_change = np.max(np.abs(u - u_old))
        if max_change < tol:
            elapsed = time.perf_counter() - start
            return u, iteration + 1, elapsed
    
    elapsed = time.perf_counter() - start
    return u, max_iter, elapsed


def print_temperature(u, decimals=1):
    """印出溫度分佈"""
    n = u.shape[0]
    print(f"\n溫度分佈 ({n}x{n}):")
    print("-" * (n * 6 + 1))
    for i in range(n):
        row = "|"
        for j in range(n):
            row += f"{u[i, j]:5.{decimals}f}|"
        print(row)
    print("-" * (n * 6 + 1))


def print_ascii_art(u):
    """用 ASCII 字符畫出溫度分佈"""
    chars = " .:-=+*#%@"
    n = u.shape[0]
    print("\n溫度分佈圖（ASCII Art）:")
    print("  " + "-" * n)
    for i in range(n):
        row = "  |"
        for j in range(n):
            idx = int(u[i, j] / 100 * (len(chars) - 1))
            row += chars[idx]
        row += "|"
        print(row)
    print("  " + "-" * n)
    print("  圖例: ' '=0°C  '@'=100°C")


def main():
    print("=" * 60)
    print("  2D 穩態熱傳導問題 - Gauss-Seidel 迭代法")
    print("=" * 60)
    print("\n問題設定：")
    print("  - 正方形金屬板，四周溫度固定")
    print("  - 上邊：100°C，下邊：0°C，左右：50°C")
    print("  - 內部無熱源，求穩態溫度分佈")
    print("\n數值方法：")
    print("  - 有限差分法：∇²u ≈ (u[i+1,j]+u[i-1,j]+u[i,j+1]+u[i,j-1]-4u[i,j])/h² = 0")
    print("  - Gauss-Seidel 迭代：u[i,j] = 四鄰平均")
    
    # 測試不同網格大小
    sizes = [10, 20, 40]
    
    for n in sizes:
        print(f"\n{'='*60}")
        print(f"網格大小：{n}x{n}")
        print(f"{'='*60}")
        
        # 純 Python 版本
        u1, iters1, time1 = solve_heat_equation(n=n, max_iter=10000, tol=1e-4)
        print(f"\n[純 Python 版本]")
        print(f"  迭代次數：{iters1}")
        print(f"  耗時：{time1:.4f} 秒")
        print(f"  中心點溫度：{u1[n//2, n//2]:.2f}°C")
        
        # 向量化版本
        u2, iters2, time2 = solve_vectorized(n=n, max_iter=10000, tol=1e-4)
        print(f"\n[向量化版本]")
        print(f"  迭代次數：{iters2}")
        print(f"  耗時：{time2:.4f} 秒")
        print(f"  中心點溫度：{u2[n//2, n//2]:.2f}°C")
        if time2 > 0:
            print(f"  加速比：{time1/time2:.1f}x")
        else:
            print(f"  加速比：N/A (向量化版本耗時過短)")
    
    # 詳細展示 20x20 的結果
    print(f"\n{'='*60}")
    print("詳細結果（20x20 網格）")
    print(f"{'='*60}")
    
    u, iters, elapsed = solve_vectorized(n=20, max_iter=10000, tol=1e-4)
    print_temperature(u, decimals=1)
    print_ascii_art(u)
    
    # 驗證：檢查 Laplace 方程是否成立
    print(f"\n{'='*60}")
    print("驗證：Laplace 方程殘差")
    print(f"{'='*60}")
    
    # 計算內部點的 Laplacian
    laplacian = np.zeros((20, 20))
    for i in range(1, 19):
        for j in range(1, 19):
            laplacian[i, j] = (u[i+1, j] + u[i-1, j] + u[i, j+1] + u[i, j-1] - 4*u[i, j])
    
    max_residual = np.max(np.abs(laplacian[1:-1, 1:-1]))
    print(f"  最大 Laplacian 殘差：{max_residual:.6f}")
    print(f"  （理論上應接近 0，表示滿足 ∇²u = 0）")
    
    # 收斂歷史
    print(f"\n{'='*60}")
    print("收斂過程")
    print(f"{'='*60}")
    
    u = np.zeros((20, 20))
    u[0, :] = 100.0
    u[-1, :] = 0.0
    u[:, 0] = 50.0
    u[:, -1] = 50.0
    u[1:-1, 1:-1] = 37.5
    
    print(f"{'迭代次數':>10} {'最大變化':>15} {'中心溫度':>12}")
    print("-" * 40)
    
    start = time.perf_counter()
    for iteration in range(1, 201):
        u_old = u.copy()
        u[1:-1, 1:-1] = 0.25 * (
            u[2:, 1:-1] + u[:-2, 1:-1] + u[1:-1, 2:] + u[1:-1, :-2]
        )
        max_change = np.max(np.abs(u - u_old))
        
        if iteration <= 10 or iteration % 20 == 0 or max_change < 1e-4:
            print(f"{iteration:>10} {max_change:>15.6f} {u[10, 10]:>12.2f}")
        
        if max_change < 1e-4:
            elapsed = time.perf_counter() - start
            print(f"\n收斂於迭代 {iteration}，耗時 {elapsed:.4f} 秒")
            break


if __name__ == "__main__":
    main()
