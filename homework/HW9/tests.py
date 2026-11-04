from __future__ import annotations

from eight_queens import solve_n_queens
from ic_routing import (
    COLS,
    NETS,
    ROWS,
    WALLS,
    astar_route,
    lee_route,
    ripup_reroute,
    route_all,
)
from mouse_maze import MAZE, solve_maze
from npc_astar import GAME_MAP, astar, bfs, find_symbol
from wolf_sheep_cabbage import GOAL, START, is_safe, solve


def adjacent(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def check_path(
    path: list[tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    blocked,
) -> None:
    assert path, "路徑不可為空"
    assert path[0] == start, f"起點錯誤：{path[0]} != {start}"
    assert path[-1] == goal, f"終點錯誤：{path[-1]} != {goal}"
    assert len(path) == len(set(path)), "路徑不可重複經過同一格"
    for cell in path:
        assert cell not in blocked, f"路徑穿過障礙物：{cell}"
    for a, b in zip(path, path[1:]):
        assert adjacent(a, b), f"路徑不連續：{a} -> {b}"


def test_mouse_maze() -> None:
    path, visit_order = solve_maze(MAZE)
    start, goal = (1, 1), (7, 7)
    walls = {
        (r, c)
        for r, row in enumerate(MAZE)
        for c, ch in enumerate(row)
        if ch == "#"
    }
    check_path(path, start, goal, walls)
    assert len(visit_order) >= len(path), "拜訪順序應包含路徑"
    print(f"[PASS] 老鼠走迷宮：找到 {len(path) - 1} 步路徑，拜訪 {len(visit_order)} 格")


def test_wolf_sheep_cabbage() -> None:
    states, actions = solve()
    assert states[0] == START and states[-1] == GOAL
    assert len(states) == 8, "最少渡河次數應為 7"
    for before, after, carried in zip(states, states[1:], actions[1:]):
        assert is_safe(before) and is_safe(after), "出現不安全的狀態"
        changed = [i for i in range(4) if before[i] != after[i]]
        assert before[0] != after[0], "農夫一定要過河"
        assert 1 <= len(changed) <= 2, "一次只能帶一樣東西"
        if len(changed) == 2:
            item_index = changed[1]
            assert carried is not None
            assert before[item_index] == before[0], "只能帶走和農夫同岸的東西"
    print(f"[PASS] 狼羊甘藍菜：最少 {len(states) - 1} 步，且每步狀態都安全")


def test_eight_queens() -> None:
    solutions, nodes = solve_n_queens(8)
    assert len(solutions) == 92, f"8 皇后應有 92 解，得到 {len(solutions)}"
    assert nodes == 2057, f"DFS 節點數預期 2057，得到 {nodes}"
    for solution in solutions:
        assert sorted(solution) == list(range(8)), "每列只能有一個皇后"
        for r1 in range(8):
            for r2 in range(r1 + 1, 8):
                assert solution[r1] != solution[r2]
                assert abs(solution[r1] - solution[r2]) != r2 - r1
    four_queens, _ = solve_n_queens(4)
    assert len(four_queens) == 2, "4 皇后應有 2 解"
    print(f"[PASS] 八皇后：{len(solutions)} 組解，DFS 節點數 {nodes}，皆無衝突")


def test_npc_astar() -> None:
    start = find_symbol(GAME_MAP, "N")
    goal = find_symbol(GAME_MAP, "P")
    astar_path, _ = astar(GAME_MAP, start, goal)
    bfs_path, _ = bfs(GAME_MAP, start, goal)
    walls = {
        (r, c)
        for r, row in enumerate(GAME_MAP)
        for c, ch in enumerate(row)
        if ch == "#"
    }
    check_path(astar_path, start, goal, walls)
    check_path(bfs_path, start, goal, walls)
    assert len(astar_path) == len(bfs_path), "A* 應找到和 BFS 一樣短的路徑"
    print(f"[PASS] NPC A*：最短路徑 {len(astar_path) - 1} 步，與 BFS 長度相同")


def test_ic_routing() -> None:
    _, failed, _ = route_all(NETS, ["A", "B", "C"], lee_route)
    assert failed == ["B"], f"預期 B 失敗，實際 {failed}"

    routes, failed, _, _, _, _ = ripup_reroute(NETS, lee_route)
    assert not failed, f"Rip-up 後仍失敗：{failed}"
    assert set(routes) == set(NETS)

    occupied: dict[tuple[int, int], str] = {}
    for name, path in routes.items():
        start, goal = NETS[name]
        check_path(path, start, goal, WALLS)
        assert len(path) <= ROWS * COLS
        for cell in path:
            assert 0 <= cell[0] < ROWS and 0 <= cell[1] < COLS
            assert cell not in occupied, f"{name} 與 {occupied.get(cell)} 在 {cell} 重疊"
            occupied[cell] = name

    lee_routes, _, _ = route_all(NETS, ["A", "B", "C"], lee_route)
    astar_routes, _, _ = route_all(NETS, ["A", "B", "C"], astar_route)
    assert sum(len(p) for p in lee_routes.values()) == sum(
        len(p) for p in astar_routes.values()
    )
    print(
        "[PASS] IC 繞線：循序 A→B→C 會擋住 B；"
        f"Rip-up 後 {len(routes)}/{len(NETS)} 條全部成功且不重疊"
    )


def main() -> None:
    print("HW9 自動檢查")
    print("=" * 60)
    test_mouse_maze()
    test_wolf_sheep_cabbage()
    test_eight_queens()
    test_npc_astar()
    test_ic_routing()
    print("=" * 60)
    print("全部測試通過！")


if __name__ == "__main__":
    main()
