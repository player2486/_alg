from __future__ import annotations

import heapq
import itertools
from collections import deque

Point = tuple[int, int]
Net = tuple[Point, Point]

ROWS, COLS = 15, 15

WALLS: set[Point] = set()

for r in range(ROWS):
    WALLS.add((r, 0))
    WALLS.add((r, COLS - 1))
for c in range(COLS):
    WALLS.add((0, c))
    WALLS.add((ROWS - 1, c))

for r in (6, 8):
    for c in range(8, 12):
        WALLS.add((r, c))
for r in (6, 7, 8):
    WALLS.add((r, 11))

NETS: dict[str, Net] = {
    "A": ((1, 7), (13, 7)),
    "B": ((7, 10), (13, 13)),
    "C": ((1, 1), (13, 1)),
}

DIRECTIONS = ((0, 1), (1, 0), (0, -1), (-1, 0))


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < ROWS and 0 <= c < COLS


def neighbors(point: Point):
    r, c = point
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
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


def lee_route(
    blocked: set[Point], start: Point, goal: Point
) -> tuple[list[Point], int]:
    if start == goal:
        return [start], 0

    queue: deque[Point] = deque([start])
    parent: dict[Point, Point | None] = {start: None}
    expanded = 0

    while queue:
        current = queue.popleft()
        expanded += 1

        if current == goal:
            return reconstruct(parent, goal), expanded

        for nxt in neighbors(current):
            if nxt in blocked or nxt in parent:
                continue
            parent[nxt] = current
            queue.append(nxt)

    return [], expanded


def astar_route(
    blocked: set[Point], start: Point, goal: Point
) -> tuple[list[Point], int]:
    counter = itertools.count()
    open_heap: list[tuple[int, int, int, Point]] = [
        (manhattan(start, goal), 0, next(counter), start)
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

        for nxt in neighbors(current):
            if nxt in blocked:
                continue
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


def route_all(
    nets: dict[str, Net],
    order: list[str],
    router,
) -> tuple[dict[str, list[Point]], list[str], int]:
    routes: dict[str, list[Point]] = {}
    occupied: dict[Point, str] = {}
    failed: list[str] = []
    expanded_total = 0

    for name in order:
        start, goal = nets[name]
        other_terminals = {
            cell
            for other, (a, b) in nets.items()
            if other != name
            for cell in (a, b)
        }
        blocked = WALLS | set(occupied) | other_terminals
        blocked.discard(start)
        blocked.discard(goal)

        path, expanded = router(blocked, start, goal)
        expanded_total += expanded

        if path:
            routes[name] = path
            for cell in path:
                occupied[cell] = name
        else:
            failed.append(name)

    return routes, failed, expanded_total


def wirelength(routes: dict[str, list[Point]]) -> int:
    return sum(len(path) - 1 for path in routes.values())


def ripup_reroute(
    nets: dict[str, Net],
    router,
    max_iterations: int = 20,
) -> tuple[
    dict[str, list[Point]],
    list[str],
    int,
    list[str],
    list[str],
    int,
]:
    order = list(nets)
    best_routes: dict[str, list[Point]] = {}
    best_failed = list(nets)
    best_expanded = 0
    best_order = order.copy()
    history: list[str] = []
    iterations = 0
    seen_orders: set[tuple[str, ...]] = {tuple(order)}

    for iteration in range(1, max_iterations + 1):
        iterations = iteration
        routes, failed, expanded = route_all(nets, order, router)

        if (len(failed), wirelength(routes)) < (
            len(best_failed),
            wirelength(best_routes),
        ):
            best_routes = {name: path[:] for name, path in routes.items()}
            best_failed = failed[:]
            best_expanded = expanded
            best_order = order.copy()

        order_text = "→".join(order)
        if failed:
            history.append(
                f"迭代 {iteration}：順序 {order_text}，失敗 {', '.join(failed)}"
            )
        else:
            history.append(f"迭代 {iteration}：順序 {order_text}，全部成功")
            return routes, failed, expanded, order, history, iteration

        target = failed[0]
        start, goal = nets[target]
        other_terminals = {
            cell
            for other, (a, b) in nets.items()
            if other != target
            for cell in (a, b)
        }
        escape, _ = router(WALLS | other_terminals, start, goal)
        if not escape:
            history.append(f"          {target} 連忽略其他走線都無路可走，停止。")
            break

        occupied = {
            cell: name for name, path in routes.items() for cell in path
        }
        victims = {
            occupied[cell]
            for cell in escape
            if cell in occupied and occupied[cell] != target
        }
        if not victims:
            history.append(f"          {target} 找不到可拆的線，停止。")
            break

        new_order = (
            [target]
            + [name for name in order if name in victims]
            + [name for name in order if name != target and name not in victims]
        )
        history.append(
            f"          拆掉 {', '.join(sorted(victims))}，"
            f"新順序 {'→'.join(new_order)}"
        )

        if tuple(new_order) in seen_orders:
            history.append("          順序開始循環，停止搜尋。")
            break
        seen_orders.add(tuple(new_order))
        order = new_order

    return best_routes, best_failed, best_expanded, best_order, history, iterations


def render(routes: dict[str, list[Point]], failed: list[str]) -> str:
    canvas = [
        ["#" if (r, c) in WALLS else "." for c in range(COLS)]
        for r in range(ROWS)
    ]

    for name, path in routes.items():
        for r, c in path:
            canvas[r][c] = name

    for name, (start, goal) in NETS.items():
        for r, c in (start, goal):
            canvas[r][c] = name

    lines = ["   " + "".join(str(c % 10) for c in range(COLS))]
    for r, row in enumerate(canvas):
        lines.append(f"{r:2d} " + "".join(row))
    if failed:
        lines.append(f"\n未成功：{', '.join(failed)}")
    return "\n".join(lines)


def route_summary(routes: dict[str, list[Point]]) -> str:
    parts = []
    for name in NETS:
        if name in routes:
            parts.append(f"{name}={len(routes[name]) - 1}")
        else:
            parts.append(f"{name}=X")
    return "  ".join(parts)


def main() -> None:
    lee_routes, lee_failed, lee_expanded = route_all(
        NETS, ["A", "B", "C"], lee_route
    )

    astar_routes, astar_failed, astar_expanded = route_all(
        NETS, ["A", "B", "C"], astar_route
    )

    alt_routes, alt_failed, alt_expanded = route_all(
        NETS, ["B", "A", "C"], lee_route
    )

    rip_routes, rip_failed, rip_expanded, rip_order, history, iterations = (
        ripup_reroute(NETS, lee_route)
    )

    print("IC 電路繞線：多種搜尋方法比較")
    print("=" * 70)
    print("地圖（# = 障礙物，A/B/C = net 端點；B 的端點在只有單一出口的口袋內）")
    print(render({}, []))

    rows = [
        ("Lee 循序 A→B→C", lee_routes, lee_failed, lee_expanded),
        ("A* 循序 A→B→C", astar_routes, astar_failed, astar_expanded),
        ("Lee 循序 B→A→C", alt_routes, alt_failed, alt_expanded),
        ("Lee + Rip-up & Reroute", rip_routes, rip_failed, rip_expanded),
    ]

    print("\n結果比較")
    print("-" * 70)
    print(f"{'方法':<28}{'成功':>8}{'總線長':>8}{'展開節點':>10}   各 net 線長")
    print("-" * 70)
    for label, routes, failed, expanded in rows:
        success = f"{len(NETS) - len(failed)}/{len(NETS)}"
        print(
            f"{label:<28}{success:>8}{wirelength(routes):>8}"
            f"{expanded:>10}   {route_summary(routes)}"
        )
    print("-" * 70)
    print("線長 = 路徑邊數；X 表示該 net 繞線失敗。")

    print("\n【Lee 循序 A→B→C】的結果（B 被 A 擋住）")
    print(render(lee_routes, lee_failed))

    print("\n【Rip-up & Reroute】的過程")
    for line in history:
        print("  " + line)
    print(f"  最終順序：{'→'.join(rip_order)}，共 {iterations} 次迭代。")

    print("\n【Rip-up & Reroute】的最終走線")
    print(render(rip_routes, rip_failed))


if __name__ == "__main__":
    main()
