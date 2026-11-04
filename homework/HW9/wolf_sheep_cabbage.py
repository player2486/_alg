from __future__ import annotations

from collections import deque

LEFT, RIGHT = 0, 1
ITEM_NAMES = ("狼", "羊", "甘藍菜")
START = (LEFT, LEFT, LEFT, LEFT)
GOAL = (RIGHT, RIGHT, RIGHT, RIGHT)

State = tuple[int, int, int, int]


def is_safe(state: State) -> bool:
    farmer, wolf, sheep, cabbage = state

    if farmer != wolf and wolf == sheep:
        return False

    if farmer != sheep and sheep == cabbage:
        return False

    return True


def next_states(state: State):
    farmer = state[0]
    destination = RIGHT if farmer == LEFT else LEFT

    alone = list(state)
    alone[0] = destination
    yield tuple(alone), None

    for index, name in enumerate(ITEM_NAMES, start=1):
        if state[index] == farmer:
            carried = list(state)
            carried[0] = destination
            carried[index] = destination
            yield tuple(carried), name


def solve() -> tuple[list[State], list[str | None]]:
    queue: deque[State] = deque([START])
    parent: dict[State, State | None] = {START: None}
    action: dict[State, str | None] = {START: None}

    while queue:
        current = queue.popleft()

        if current == GOAL:
            break

        for nxt, carried in next_states(current):
            if nxt in parent:
                continue
            if not is_safe(nxt):
                continue
            parent[nxt] = current
            action[nxt] = carried
            queue.append(nxt)

    if GOAL not in parent:
        return [], []

    states: list[State] = []
    actions: list[str | None] = []
    node: State | None = GOAL
    while node is not None:
        states.append(node)
        actions.append(action[node])
        node = parent[node]
    states.reverse()
    actions.reverse()
    return states, actions


def bank_contents(state: State, bank: int) -> str:
    items = [name for index, name in enumerate(ITEM_NAMES, start=1) if state[index] == bank]
    farmer = "農夫" if state[0] == bank else ""
    contents = ([farmer] if farmer else []) + items
    return "、".join(contents) if contents else "（空）"


def main() -> None:
    states, actions = solve()

    print("狼、羊、甘藍菜過河問題（BFS）")
    print("=" * 58)

    if not states:
        print("無解。")
        return

    print(f"最少需要渡河 {len(states) - 1} 次。\n")
    print(f"初始：左岸 = {bank_contents(states[0], LEFT)}；"
          f"右岸 = {bank_contents(states[0], RIGHT)}\n")

    for step in range(1, len(states)):
        before, after = states[step - 1], states[step]
        carried = actions[step]
        direction = "左岸 → 右岸" if before[0] == LEFT else "右岸 → 左岸"

        if carried is None:
            move = f"農夫獨自划船（{direction}）"
        else:
            move = f"農夫帶「{carried}」（{direction}）"

        print(f"第 {step} 步：{move}")
        print(f"        左岸：{bank_contents(after, LEFT)}")
        print(f"        右岸：{bank_contents(after, RIGHT)}")
        print()

    print("完成！所有東西都平安到達右岸。")
    print("\n狀態表示法（farmer, wolf, sheep, cabbage）：")
    print("  ", " → ".join(str(state) for state in states))


if __name__ == "__main__":
    main()
