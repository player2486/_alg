from __future__ import annotations

import argparse


def solve_n_queens(n: int) -> tuple[list[tuple[int, ...]], int]:
    if n < 1:
        raise ValueError("N 必須是正整數")

    solutions: list[tuple[int, ...]] = []
    placement: list[int] = []
    used_cols: set[int] = set()
    used_diag_sum: set[int] = set()
    used_diag_diff: set[int] = set()
    nodes = 0

    def backtrack(row: int) -> None:
        nonlocal nodes
        nodes += 1

        if row == n:
            solutions.append(tuple(placement))
            return

        for col in range(n):
            if (
                col in used_cols
                or (row + col) in used_diag_sum
                or (row - col) in used_diag_diff
            ):
                continue

            placement.append(col)
            used_cols.add(col)
            used_diag_sum.add(row + col)
            used_diag_diff.add(row - col)

            backtrack(row + 1)

            placement.pop()
            used_cols.remove(col)
            used_diag_sum.remove(row + col)
            used_diag_diff.remove(row - col)

    backtrack(0)
    return solutions, nodes


def render_board(solution: tuple[int, ...]) -> str:
    n = len(solution)
    lines = []
    for row in range(n):
        lines.append(" ".join("Q" if col == solution[row] else "." for col in range(n)))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="以 DFS 回溯法解 N 皇后問題")
    parser.add_argument("n", nargs="?", type=int, default=8, help="棋盤大小（預設 8）")
    parser.add_argument(
        "--show",
        type=int,
        default=1,
        metavar="K",
        help="顯示前 K 組解（預設 1）",
    )
    args = parser.parse_args()

    solutions, nodes = solve_n_queens(args.n)

    print(f"{args.n} 皇后問題（DFS + 回溯）")
    print("=" * 50)
    print(f"解的總數：{len(solutions)}")
    print(f"DFS 遞迴節點數：{nodes}")

    show = max(0, min(args.show, len(solutions)))
    for index in range(show):
        solution = solutions[index]
        print(f"\n第 {index + 1} 組解（row → col）：{solution}")
        print(render_board(solution))



if __name__ == "__main__":
    main()
