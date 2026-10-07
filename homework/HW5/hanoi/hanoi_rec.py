def hanoi_iterative(n, source, target, auxiliary):
    """
    非遞迴解法 (使用堆疊模擬)
    """
    stack = [(0, n, source, target, auxiliary)]

    while stack:
        state, disks, src, tgt, aux = stack.pop()

        if disks == 0:
            continue

        if state == 1:
            print(f"將圓盤 {disks} 從 {src} 移至 {tgt}")
        elif state == 0:
            stack.append((0, disks - 1, aux, tgt, src))
            
            stack.append((1, disks, src, tgt, aux))
            
            stack.append((0, disks - 1, src, aux, tgt))

print("\n--- 非遞迴解法 (堆疊模擬) ---")
hanoi_iterative(3, 'A', 'C', 'B')