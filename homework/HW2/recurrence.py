"""
HW2: 遞迴方程式求解與複雜度驗證
使用暴力遞迴驗證精確解的正確性
"""

# ========== 1. T(n) = T(n-1) + 8, T(1) = 1 ==========
def T1_bruteforce(n):
    """暴力遞迴"""
    if n == 1:
        return 1
    return T1_bruteforce(n - 1) + 8

def T1_exact(n):
    """精確解: T(n) = 8n - 7"""
    return 8 * n - 7


# ========== 2. T(n) = 2T(n-1) + 9, T(1) = 1 ==========
def T2_bruteforce(n):
    """暴力遞迴"""
    if n == 1:
        return 1
    return 2 * T2_bruteforce(n - 1) + 9

def T2_exact(n):
    """精確解: T(n) = 5 * 2^n - 9"""
    return 5 * (2 ** n) - 9


# ========== 3. T(n) = 2T(n/2) + 1, T(1) = 1 ==========
def T3_bruteforce(n):
    """暴力遞迴 (n 必須為 2 的冪次)"""
    if n == 1:
        return 1
    return 2 * T3_bruteforce(n // 2) + 1

def T3_exact(n):
    """精確解: T(n) = 2n - 1"""
    return 2 * n - 1


# ========== 4. T(n) = T(n/2) + 1, T(1) = 1 ==========
def T4_bruteforce(n):
    """暴力遞迴 (n 必須為 2 的冪次)"""
    if n == 1:
        return 1
    return T4_bruteforce(n // 2) + 1

def T4_exact(n):
    """精確解: T(n) = log2(n) + 1"""
    import math
    return int(math.log2(n)) + 1


# ========== 驗證 ==========
def verify(name, brute_func, exact_func, test_values):
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    print(f"{'n':>5} | {'暴力遞迴':>12} | {'精確解':>12} | {'吻合':>6}")
    print(f"{'-'*5}-+-{'-'*12}-+-{'-'*12}-+-{'-'*6}")
    all_pass = True
    for n in test_values:
        b = brute_func(n)
        e = exact_func(n)
        ok = "✓" if b == e else "✗"
        if b != e:
            all_pass = False
        print(f"{n:>5} | {b:>12} | {e:>12} | {ok:>6}")
    print(f"\n結果: {'全部通過 ✓' if all_pass else '有錯誤 ✗'}")
    return all_pass


if __name__ == "__main__":
    print("遞迴方程式精確解驗證")
    print("=" * 50)

    # 測試 1: T(n) = T(n-1) + 8
    verify("T(n) = T(n-1) + 8, T(1)=1  →  T(n) = 8n - 7",
           T1_bruteforce, T1_exact, [1, 2, 3, 5, 10, 20, 50])

    # 測試 2: T(n) = 2T(n-1) + 9 (只測小 n，因為 2^n 增長太快)
    verify("T(n) = 2T(n-1) + 9, T(1)=1  →  T(n) = 5·2^n - 9",
           T2_bruteforce, T2_exact, [1, 2, 3, 5, 10, 15])

    # 測試 3: T(n) = 2T(n/2) + 1 (n 必須為 2 的冪次)
    verify("T(n) = 2T(n/2) + 1, T(1)=1  →  T(n) = 2n - 1",
           T3_bruteforce, T3_exact, [1, 2, 4, 8, 16, 32, 64, 128])

    # 測試 4: T(n) = T(n/2) + 1 (n 必須為 2 的冪次)
    verify("T(n) = T(n/2) + 1, T(1)=1  →  T(n) = log2(n) + 1",
           T4_bruteforce, T4_exact, [1, 2, 4, 8, 16, 32, 64, 128, 256])

    # 複雜度比較
    print(f"\n{'='*50}")
    print("複雜度比較 (n=32 時的值)")
    print(f"{'='*50}")
    n = 32
    print(f"  O(n)     → T1({n}) = {T1_exact(n):>10}")
    print(f"  O(n)     → T3({n}) = {T3_exact(n):>10}")
    print(f"  O(log n) → T4({n}) = {T4_exact(n):>10}")
    print(f"  O(2^n)   → T2({n}) = {T2_exact(n):>10}  (n=32 時已超過 21 億!)")
