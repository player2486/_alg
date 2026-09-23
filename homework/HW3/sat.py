#!/usr/bin/env python3
import random
import sys
import time


def compile_cnf(cnf):
    compiled = []
    for clause in cnf:
        pos = 0
        neg = 0
        for lit in clause:
            bit = 1 << (abs(lit) - 1)
            if lit > 0:
                pos |= bit
            else:
                neg |= bit
        compiled.append((pos, neg))
    return compiled


def satisfied(compiled, mask):
    for pos, neg in compiled:
        if not (mask & pos or neg & ~mask):
            return False
    return True


def assignments(n):
    for mask in range(1 << n):
        yield mask


def solve(cnf, n):
    compiled = compile_cnf(cnf)
    start = time.perf_counter()
    for mask in assignments(n):
        if satisfied(compiled, mask):
            return mask, mask + 1, time.perf_counter() - start
    return None, 1 << n, time.perf_counter() - start


def count_models(cnf, n):
    compiled = compile_cnf(cnf)
    count = 0
    start = time.perf_counter()
    for mask in assignments(n):
        if satisfied(compiled, mask):
            count += 1
    return count, 1 << n, time.perf_counter() - start


def human_time(sec):
    if sec < 1e-3:
        return f"{sec * 1e6:.1f} 微秒"
    if sec < 1:
        return f"{sec * 1e3:.3f} 毫秒"
    if sec < 60:
        return f"{sec:.3f} 秒"
    minutes, sec = divmod(sec, 60)
    if minutes < 60:
        return f"{int(minutes)} 分 {sec:.1f} 秒"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{int(hours)} 小時 {minutes} 分"
    days, hours = divmod(hours, 24)
    return f"{int(days)} 天 {hours} 小時"


def model_str(mask, n):
    return "{" + ", ".join(f"x{i}={mask >> (i - 1) & 1}" for i in range(1, n + 1)) + "}"


def clause_str(clause):
    return "(" + " ∨ ".join(f"¬x{abs(l)}" if l < 0 else f"x{l}" for l in clause) + ")"


def cnf_str(cnf):
    return " ∧ ".join(clause_str(c) for c in cnf)


def print_truth_table(cnf, n, limit=64):
    compiled = compile_cnf(cnf)
    total = 1 << n
    if total > limit:
        print(f"  n = {n}，真值表有 {total} 列，超過 {limit} 列不印出")
        return
    headers = [f"x{i}" for i in range(1, n + 1)]
    headers += [f"C{j + 1}" for j in range(len(cnf))]
    headers += ["F"]
    rows = []
    for mask in assignments(n):
        cells = [str(mask >> (i - 1) & 1) for i in range(1, n + 1)]
        cells += [str(int(satisfied([c], mask))) for c in compiled]
        cells += [str(int(satisfied(compiled, mask)))]
        rows.append(cells)
    widths = [max(len(headers[k]), max(len(r[k]) for r in rows)) for k in range(len(headers))]

    def line(cells, dash=False):
        parts = []
        for k, cell in enumerate(cells):
            parts.append("-" * widths[k] if dash else cell.center(widths[k]))
            if k + 1 < len(cells):
                parts.append("-" if dash else "|")
        return "  " + ("-".join(parts) if dash else " ".join(parts))

    print(line(headers))
    print(line(headers, dash=True).rstrip())
    for row in rows:
        print(line(row))


def report(cnf, n, show_table=False):
    print(f"公式 (n = {n} 個變數, {len(cnf)} 個子句)：")
    print(f"  {cnf_str(cnf)}")
    print(f"  搜尋空間 = 2^{n} = {1 << n} 種指派")
    if show_table:
        print_truth_table(cnf, n)
    mask, checked, elapsed = solve(cnf, n)
    if mask is None:
        print(f"  結果：UNSAT（已列舉完 {checked} 種指派，耗時 {human_time(elapsed)}）")
    else:
        print(f"  結果：SAT，模型 {model_str(mask, n)}")
        if elapsed > 1e-3:
            rate = checked / elapsed
            print(f"  列舉到第 {checked} 種指派找到，耗時 {human_time(elapsed)}（{rate:,.0f} 種/秒）")
        else:
            print(f"  列舉到第 {checked} 種指派找到，耗時 {human_time(elapsed)}")
    count, space, t = count_models(cnf, n)
    print(f"  全部解的個數 = {count} / {space}，完整掃描耗時 {human_time(t)}")
    print()


def random_3sat(n, num_clauses, seed=42):
    rng = random.Random(seed)
    solution = rng.getrandbits(n)
    cnf = []
    while len(cnf) < num_clauses:
        vs = rng.sample(range(1, n + 1), 3)
        clause = [v if rng.getrandbits(1) else -v for v in vs]
        if any((lit > 0) == bool(solution >> (abs(lit) - 1) & 1) for lit in clause):
            cnf.append(clause)
    return cnf, solution


def parse_dimacs(text):
    n = 0
    cnf = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("c"):
            continue
        if line.startswith("p"):
            n = int(line.split()[2])
            continue
        lits = [int(x) for x in line.split() if x != "0"]
        if lits:
            cnf.append(lits)
            n = max(n, max(abs(x) for x in lits))
    return cnf, n


def run_demos():
    print("=" * 78)
    print("範例 1：SAT，列出完整真值表")
    cnf1 = [[1, -2], [-1, 2, 3], [-2, -3]]
    report(cnf1, 3, show_table=True)

    print("=" * 78)
    print("範例 2：UNSAT（鴿籠原理：3 隻鴿子關進 2 個洞）")
    n = 3
    holes = 2
    cnf2 = []
    for p in range(n):
        cnf2.append([p * holes + h + 1 for h in range(holes)])
    for h in range(holes):
        for a in range(n):
            for b in range(a + 1, n):
                cnf2.append([-(a * holes + h + 1), -(b * holes + h + 1)])
    report(cnf2, n * holes)

    print("=" * 78)
    print("範例 3：隨機 3-SAT（n = 20，植入一組解）")
    cnf3, solution = random_3sat(20, 160, seed=7)
    print(f"公式 (n = 20 個變數, {len(cnf3)} 個子句)，已知其中一個解 = {model_str(solution, 20)}")
    print(f"  搜尋空間 = 2^20 = {1 << 20} 種指派")
    mask, checked, elapsed = solve(cnf3, 20)
    if mask is None:
        print("  結果：UNSAT")
    else:
        print(f"  結果：SAT，模型 {model_str(mask, 20)}")
        print(f"  列舉到第 {checked} 種指派找到，耗時 {human_time(elapsed)}"
              f"（{checked / elapsed:,.0f} 種/秒）")
    print()

    print("=" * 78)
    print("暴力列舉的極限：n 變大時 2^n 爆炸")
    print(f"{'n':>4}{'搜尋空間 2^n':>44}")
    for k in (10, 20, 30, 40, 50, 100):
        print(f"{k:>4}{1 << k:>44,}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            cnf, n = parse_dimacs(f.read())
        report(cnf, n)
    else:
        run_demos()


if __name__ == "__main__":
    main()
