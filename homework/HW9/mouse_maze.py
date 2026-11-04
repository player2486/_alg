"""老鼠走迷宮 — DFS（Depth-First Search，深度優先搜尋）

以遞迴回溯法在二維迷宮中尋找從 S 到 E 的路徑。
DFS 會盡可能往深處走，遇到死路才回溯；找到的路徑不保證最短。

符號說明：
    #  牆壁
    .  可通行
    S  起點
    E  終點
    *  找到的路徑
"""

from __future__ import annotations

MAZE: list[str] = [
    "#########",
    "#S..#...#",
    "#.###.#.#",
    "#.#...#.#",
    "#.#####.#",
    "#.......#",
    "#.#####.#",
    "#......E#",
    "#########",
]

DIRECTIONS = ((0, 1), (1, 0), (0, -1), (-1, 0))  # 右、下、左、上


def find_symbol(maze: list[str], symbol: str) -> tuple[int, int]:
    """回傳 symbol 在迷宮中的 (row, col)。"""
    for r, row in enumerate(maze):
        for c, ch in enumerate(row):
            if ch == symbol:
                return r, c
    raise ValueError(f"迷宮中找不到 {symbol!r}")


def solve_maze(
    maze: list[str],
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """用 DFS 求解迷宮。

    回傳：
        path        從 S 到 E 的座標串列；無解時為空串列。
        visit_order 實際拜訪過的座標順序（可用來觀察 DFS 的走法）。
    """
    if not maze or not maze[0]:
        raise ValueError("迷宮不可為空")

    rows, cols = len(maze), len(maze[0])
    start = find_symbol(maze, "S")
    goal = find_symbol(maze, "E")

    visited = [[False] * cols for _ in range(rows)]
    visit_order: list[tuple[int, int]] = []
    path: list[tuple[int, int]] = []

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < rows and 0 <= c < cols

    def dfs(r: int, c: int) -> bool:
        if not in_bounds(r, c) or visited[r][c] or maze[r][c] == "#":
            return False

        visited[r][c] = True
        visit_order.append((r, c))
        path.append((r, c))

        if (r, c) == goal:
            return True

        for dr, dc in DIRECTIONS:
            if dfs(r + dr, c + dc):
                return True

        # 死路：回溯，把目前格從路徑中移除
        path.pop()
        return False

    found = dfs(*start)
    return (path if found else []), visit_order


def render(maze: list[str], path: list[tuple[int, int]]) -> str:
    """把路徑畫在迷宮上。"""
    path_set = set(path)
    lines: list[str] = []
    for r, row in enumerate(maze):
        line = []
        for c, ch in enumerate(row):
            if (r, c) in path_set and ch not in ("S", "E"):
                line.append("*")
            else:
                line.append(ch)
        lines.append("".join(line))
    return "\n".join(lines)


def main() -> None:
    path, visit_order = solve_maze(MAZE)

    print("原始迷宮：")
    print("\n".join(MAZE))

    if not path:
        print("\n找不到從 S 到 E 的路徑。")
        return

    print("\nDFS 找到的路徑：")
    print(render(MAZE, path))
    print(f"\n路徑長度（步數）：{len(path) - 1}")
    print(f"路徑座標：{path}")
    print(f"DFS 共拜訪 {len(visit_order)} 個格子（含回溯前的探索）。")


if __name__ == "__main__":
    main()
