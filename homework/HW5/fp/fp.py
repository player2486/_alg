def my_map(func, lst):
    """自製 map：將 func 應用於 lst 的每個元素"""
    if not lst:
        return []
    return [func(lst[0])] + my_map(func, lst[1:])

def my_filter(func, lst):
    """自製 filter：保留 func 判斷為 True 的元素"""
    if not lst:
        return []
    head = [lst[0]] if func(lst[0]) else []
    return head + my_filter(func, lst[1:])

def my_reduce(func, lst, initial=None):
    """自製 reduce：將 lst 元素不斷與累加器進行 func 運算"""
    if not lst:
        return initial
    if initial is None:
        return my_reduce(func, lst[1:], lst[0])
    return my_reduce(func, lst[1:], func(initial, lst[0]))

def bubble_step(acc, x):
    """
    單次比較的 Reducer 函數
    acc 是一個 Tuple: (目前累積的清單, 目前遇到的最大值)
    x 是下一個要比較的元素
    """
    sorted_part, current_max = acc
    
    if current_max is None:
        return (sorted_part, x)
        
    if x < current_max:
        return (sorted_part + [x], current_max)
    else:
        return (sorted_part + [current_max], x)

def single_pass(lst):
    """執行一趟泡沫排序，將最大的元素推到最後面"""
    if not lst:
        return []
    sorted_part, max_val = my_reduce(bubble_step, lst, ([], None))
    return sorted_part + [max_val]

def bubble_sort(lst):
    """
    無迴圈泡沫排序主函數
    利用 my_reduce 將 single_pass 執行 len(lst) 次
    """
    return my_reduce(lambda acc, _: single_pass(acc), lst, lst)

if __name__ == "__main__":
    unsorted_list = [64, 34, 25, 12, 22, 11, 90]
    
    print("原始陣列:", unsorted_list)
    sorted_list = bubble_sort(unsorted_list)
    print("排序後陣列:", sorted_list)

    mapped_list = my_map(lambda x: x * 2, sorted_list)
    filtered_list = my_filter(lambda x: x > 50, mapped_list)
    
    print("\n[測試 my_map] 每個元素乘 2:", mapped_list)
    print("[測試 my_filter] 篩選大於 50:", filtered_list)