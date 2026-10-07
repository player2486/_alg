def hanoi_recursive(n, source, target, auxiliary):
    """
    遞迴解法
    n: 圓盤數量
    source: 來源柱
    target: 目標柱
    auxiliary: 輔助柱
    """
    if n > 0:
        hanoi_recursive(n - 1, source, auxiliary, target)
        
        print(f"將圓盤 {n} 從 {source} 移至 {target}")
        
        hanoi_recursive(n - 1, auxiliary, target, source)

print("--- 遞迴解法 ---")
hanoi_recursive(3, 'A', 'C', 'B')