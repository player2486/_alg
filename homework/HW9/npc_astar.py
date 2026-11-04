"""NPC 搜尋玩家 — A*（A-star，啟發式最佳優先搜尋）

情境：
    地圖上有一個 NPC（N）和玩家（P），中間有牆壁（#）。
    NPC 要找出到玩家的最短路徑並沿著路走過去。

A* 的評估函式：
    f(n) = g(n) + h(n)
    g(n)：從起點走到 n 的實際成本
    h(n)：從 n 到終點的估計成本（本程式用曼哈頓距離）

只要 h(n) 不高估真實成本（admissible），A* 就能找到最短路徑，
而且通常比 BFS 展開更少的節點。

執行：
    python npc_astar.py
"""

from __future__ import annotations

import heapq
import itertools
from collections import deque

# N = NPC 起點，P = 玩家，'#' = 牆壁，'.' = 可通行
GAME_MAP: list[str] = [
    "################",
    "#N.............#",
    "#.####.#####.#.#",
    "#....#.....#.#.#",
    "####.#.###.#.#.#",
    "#....#...#...#.#",
    "#.######.#.###.#",
    "#........#....P#",
    "################",
]

DIRECTIONS = ((0, 1), (1, 0), (0, -1), (-1, 0))  # 右、下、左、上
Point = tuple[int, int]


def find_symbol(grid: list[str], symbol: str) -> Point:
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == symbol:
                return r, c
    raise ValueError(f"地圖中找不到 {symbol!r}")


def in_bounds(grid: list[str], r: int, c: int) -> bool:
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])


def neighbors(grid: list[str], point: Point):
    r, c = point
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if in_bounds(grid, nr, nc) and grid[nr][nc] != "#":
            yield nr, nc


def manhattan(a: Point, b: Point) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruct(parent: dict[Point, Point | None], goal: Point) -> list[Point]:
    path: list[Point] = []
    node: Point | None = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def astar(grid: list[str], start: Point, goal: Point) -> tuple[list[Point], int]:
    """A* 搜尋，回傳 (路徑, 展開節點數)。"""
    counter = itertools.count()
    # heap 元素：(f, h, 順序, 座標)。h 當第二鍵可在 f 相同時優先靠近終點。
    open_heap: list[tuple[int, int, int, Point]] = [
        (manhattan(start, goal), manhattan(start, goal), next(counter), start)
    ]
    g_cost: dict[Point, int] = {start: 0}
    parent: dict[Point, Point | None] = {start: None}
    closed: set[Point] = set()
    expanded = 0

    while open_heap:
        _, _, _, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)
        expanded += 1

        if current == goal:
            return reconstruct(parent, goal), expanded

        for nxt in neighbors(grid, current):
            new_cost = g_cost[current] + 1
            if new_cost < g_cost.get(nxt, float("inf")):
                g_cost[nxt] = new_cost
                parent[nxt] = current
                h = manhattan(nxt, goal)
                heapq.heappush(
                    open_heap,
                    (new_cost + h, h, next(counter), nxt),
                )

    return [], expanded


def bfs(grid: list[str], start: Point, goal: Point) -> tuple[list[Point], int]:
    """BFS 對照組，回傳 (路徑, 展開節點數)。"""
    queue: deque[Point] = deque([start])
    parent: dict[Point, Point | None] = {start: None}
    expanded = 0

    while queue:
        current = queue.popleft()
        expanded += 1

        if current == goal:
            return reconstruct(parent, goal), expanded

        for nxt in neighbors(grid, current):
            if nxt not in parent:
                parent[nxt] = current
                queue.append(nxt)

    return [], expanded


def render(grid: list[str], path: list[Point]) -> str:
    path_set = set(path)
    lines: list[str] = []
    for r, row in enumerate(grid):
        line = []
        for c, ch in enumerate(row):
            if (r, c) in path_set and ch not in ("N", "P"):
                line.append("*")
            else:
                line.append(ch)
        lines.append("".join(line))
    return "\n".join(lines)


def main() -> None:
    start = find_symbol(GAME_MAP, "N")
    goal = find_symbol(GAME_MAP, "P")

    astar_path, astar_expanded = astar(GAME_MAP, start, goal)
    bfs_path, bfs_expanded = bfs(GAME_MAP, start, goal)

    print("NPC 搜尋玩家（A* vs BFS）")
    print("=" * 52)
    print("原始地圖：")
    print("\n".join(GAME_MAP))

    if not astar_path:
        print("\nNPC 找不到通往玩家的路徑。")
        return

    print("\nA* 找到的路徑：")
    print(render(GAME_MAP, astar_path))
    print(f"\n起點 N = {start}，玩家 P = {goal}")
    print(f"最短路徑步數：{len(astar_path) - 1}")
    print(f"A* 展開節點數：{astar_expanded}")
    print(f"BFS 展開節點數：{bfs_expanded}")

    if bfs_expanded > astar_expanded:
        saved = (1 - astar_expanded / bfs_expanded) * 100
        print(f"A* 比 BFS 少展開約 {saved:.1f}% 的節點。")

    print("\n路徑座標：", astar_path)
    print("\n說明：BFS 只使用 g(n)，像水波一樣均勻擴散；")
    print("      A* 額外使用 h(n) 指向終點，因此能更快聚焦到正確方向。")


if __name__ == "__main__":
    main()
