def sym_diff(expr, var='x'):
    """遞迴計算符號微分"""
    if isinstance(expr, (int, float)):
        return 0
    if isinstance(expr, str):
        return 1 if expr == var else 0

    op = expr[0]

    if op == '+':
        return ('+', sym_diff(expr[1], var), sym_diff(expr[2], var))
    elif op == '-':
        return ('-', sym_diff(expr[1], var), sym_diff(expr[2], var))
    elif op == '*':
        A, B = expr[1], expr[2]
        return ('+', ('*', sym_diff(A, var), B), ('*', A, sym_diff(B, var)))
    elif op == '/':
        A, B = expr[1], expr[2]
        num = ('-', ('*', sym_diff(A, var), B), ('*', A, sym_diff(B, var)))
        den = ('^', B, 2)
        return ('/', num, den)
    elif op == '^':
        A, n = expr[1], expr[2]
        return ('*', ('*', n, ('^', A, n - 1)), sym_diff(A, var))
    elif op == 'sin':
        A = expr[1]
        return ('*', ('cos', A), sym_diff(A, var))
    elif op == 'cos':
        A = expr[1]
        return ('*', ('*', -1, ('sin', A)), sym_diff(A, var))
    else:
        raise ValueError(f"未知的運算子: {op}")

def to_string(expr):
    """將 Tuple 轉換為人類易讀的數學字串"""
    if isinstance(expr, (int, float, str)):
        return str(expr)
    
    op = expr[0]
    if op in ('+', '-', '*', '/', '^'):
        return f"({to_string(expr[1])} {op} {to_string(expr[2])})"
    elif op in ('sin', 'cos'):
        return f"{op}({to_string(expr[1])})"

if __name__ == "__main__":
    expressions = [
        # 1. f(x) = 42 (常數)
        42,
        
        # 2. f(x) = x (單一變數)
        'x',
        
        # 3. f(x) = x + 5 (基本加法)
        ('+', 'x', 5),
        
        # 4. f(x) = x^3 (基本次方)
        ('^', 'x', 3),
        
        # 5. f(x) = 3 * x^2 (係數乘法)
        ('*', 3, ('^', 'x', 2)),
        
        # 6. f(x) = sin(x) (基本三角函數)
        ('sin', 'x'),
        
        # 7. f(x) = x * cos(x) (乘積法則 Product Rule)
        ('*', 'x', ('cos', 'x')),
        
        # 8. f(x) = sin(x) / x (商法則 Quotient Rule)
        ('/', ('sin', 'x'), 'x'),
        
        # 9. f(x) = sin(x^2) (連鎖律 Chain Rule 應用)
        ('sin', ('^', 'x', 2)),
        
        # 10. f(x) = (x^2 + 1) * cos(x) (複合表達式)
        ('*', ('+', ('^', 'x', 2), 1), ('cos', 'x'))
    ]

    print("=== 符號微分測試結果 ===\n")
    for i, expr in enumerate(expressions, 1):
        original_str = to_string(expr)
        
        diff_expr = sym_diff(expr, var='x')
        diff_str = to_string(diff_expr)
        
        print(f"測試 {i}:")
        print(f"  原函數 f(x)  = {original_str}")
        print(f"  微分後 f'(x) = {diff_str}")
        print("-" * 50)