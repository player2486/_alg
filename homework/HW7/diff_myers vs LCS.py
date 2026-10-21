def diff_dp(file_a, file_b):
    m, n = len(file_a), len(file_b)
    
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if file_a[i - 1] == file_b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    i, j = m, n
    diff_result = []
    
    while i > 0 or j > 0:
        if i > 0 and j > 0 and file_a[i - 1] == file_b[j - 1]:
            diff_result.append(f"  {file_a[i - 1]}")
            i -= 1
            j -= 1
        elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):
            diff_result.append(f"+ {file_b[j - 1]}")
            j -= 1
        elif i > 0 and (j == 0 or dp[i][j - 1] < dp[i - 1][j]):
            diff_result.append(f"- {file_a[i - 1]}")
            i -= 1
            
    return diff_result[::-1]


def diff_myers(file_a, file_b):
    m, n = len(file_a), len(file_b)
    max_d = m + n
    
    v = {1: 0} 
    trace = []
    
    for d in range(max_d + 1):
        trace.append(v.copy())
        
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
                x = v.get(k + 1, 0)
            else:
                x = v.get(k - 1, 0) + 1
                
            y = x - k
            
            while x < m and y < n and file_a[x] == file_b[y]:
                x += 1
                y += 1
                
            v[k] = x
            
            if x >= m and y >= n:
                return backtrack_myers(file_a, file_b, trace)
    return []

def backtrack_myers(file_a, file_b, trace):
    x, y = len(file_a), len(file_b)
    diff_result = []
    
    for d in range(len(trace) - 1, -1, -1):
        v = trace[d]
        k = x - y
        
        if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
            prev_k = k + 1
        else:
            prev_k = k - 1
            
        prev_x = v.get(prev_k, 0)
        prev_y = prev_x - prev_k
        
        while x > prev_x and y > prev_y:
            diff_result.append(f"  {file_a[x - 1]}")
            x -= 1
            y -= 1
            
        if d > 0:
            if x == prev_x:
                diff_result.append(f"+ {file_b[y - 1]}")
            else:
                diff_result.append(f"- {file_a[x - 1]}")
                
        x, y = prev_x, prev_y
        
    return diff_result[::-1]

if __name__ == "__main__":
    file_old = [
        "def hello():", 
        "    print('hi')", 
        "    return 0"
    ]
    file_new = [
        "def hello():", 
        "    print('hello world')", 
        "    return 0"
    ]

    print("====================================")
    print("1. 動態規劃 (LCS) 的輸出結果：")
    print("====================================")
    result_dp = diff_dp(file_old, file_new)
    for line in result_dp:
        print(line)

    print("\n====================================")
    print("2. 非動態規劃 (Myers) 的輸出結果：")
    print("====================================")
    result_myers = diff_myers(file_old, file_new)
    for line in result_myers:
        print(line)