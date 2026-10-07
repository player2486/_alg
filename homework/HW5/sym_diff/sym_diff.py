def sym_diff(expr, var='x'):
    """
    遞迴計算符號微分
    expr: 數學表達式 (Tuple 結構)
    var: 要求導的變數 (預設為 'x')
    """
    # 基本情況 1：常數的微分為 0
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
        return ('+', 
                ('*', sym_diff(A, var), B), 
                ('*', A, sym_diff(B, var)))
    
    elif op == '/':
        A, B = expr[1], expr[2]
        num = ('-', 
               ('*', sym_diff(A, var), B), 
               ('*', A, sym_diff(B, var)))
        den = ('^', B, 2)
        return ('/', num, den)
    
    elif op == '^':
        A, n = expr[1], expr[2]
        return ('*', 
                ('*', n, ('^', A, n - 1)), 
                sym_diff(A, var))
    
    elif op == 'sin':
        A = expr[1]
        return ('*', ('cos', A), sym_diff(A, var))
    
    elif op == 'cos':
        A = expr[1]
        return ('*', 
                ('*', -1, ('sin', A)), 
                sym_diff(A, var))
    
    else:
        raise ValueError(f"未知的運算子: {op}")


def to_string(expr):
    if isinstance(expr, (int, float, str)):
        return str(expr)
    
    op = expr[0]
    if op in ('+', '-', '*', '/', '^'):
        return f"({to_string(expr[1])} {op} {to_string(expr[2])})"
    elif op in ('sin', 'cos'):
        return f"{op}({to_string(expr[1])})"

if __name__ == "__main__":
    f_x = ('*', ('^', 'x', 2), ('sin', 'x'))
    
    print(f"原函數 f(x) = {to_string(f_x)}")
    
    df_dx = sym_diff(f_x)
    
    print(f"微積分結果 f'(x) = {to_string(df_dx)}")