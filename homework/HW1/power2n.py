#!/usr/bin/env python3
import sys
import time
from decimal import Decimal, getcontext

getcontext().prec = 15

N = 100
CALL_LIMIT = 2_000_000


class CallLimitExceeded(Exception):
    pass


class Counter:
    def __init__(self, limit=CALL_LIMIT):
        self.calls = 0
        self.limit = limit

    def tick(self):
        self.calls += 1
        if self.calls > self.limit:
            raise CallLimitExceeded(self.calls)


counter = Counter()


def reset_counter(limit=CALL_LIMIT):
    counter.calls = 0
    counter.limit = limit


def power2n_builtin(n):
    return 2 ** n


def power2n_double(n):
    counter.tick()
    if n == 0:
        return 1
    return power2n_double(n - 1) + power2n_double(n - 1)


def power2n_times2(n):
    counter.tick()
    if n == 0:
        return 1
    return 2 * power2n_times2(n - 1)


_TABLE = {0: 1}


def power2n_memo(n):
    counter.tick()
    if n in _TABLE:
        return _TABLE[n]
    value = power2n_memo(n - 1) + power2n_memo(n - 1)
    _TABLE[n] = value
    return value


def reset_table():
    _TABLE.clear()
    _TABLE[0] = 1


def bench(fn, n, setup=None, repeat=None, sample_time=0.05, max_repeat=100_000):
    if setup:
        setup()
    reset_counter()
    start = time.perf_counter()
    try:
        result = fn(n)
    except Exception as e:
        elapsed = time.perf_counter() - start
        return None, 0, None, (e, elapsed)
    one = time.perf_counter() - start

    if repeat is None:
        repeat = max(1, min(max_repeat, int(sample_time / one))) if one > 0 else max_repeat

    total = 0.0
    for _ in range(repeat):
        if setup:
            setup()
            reset_counter()
        start = time.perf_counter()
        result = fn(n)
        total += time.perf_counter() - start
    return total / repeat, repeat, result, None


def sci(x):
    if isinstance(x, int):
        if x == 0:
            return "0.000e+0"
        return f"{Decimal(x):.3e}"
    return f"{x:.3e}"


def human_time(seconds):
    seconds = Decimal(seconds)
    if seconds < 1000:
        if seconds < Decimal("1e-3"):
            return f"{float(seconds * Decimal('1e6')):.1f} 微秒"
        if seconds < 1:
            return f"{float(seconds * Decimal('1e3')):.3f} 毫秒"
        return f"{float(seconds):.3f} 秒"
    total_minutes = seconds / 60
    if total_minutes < 60:
        return f"{int(total_minutes)} 分 {float(seconds % 60):.1f} 秒"
    total_hours = seconds / 3600
    if total_hours < 24:
        return f"{int(total_hours)} 小時 {int(total_minutes % 60)} 分"
    total_days = seconds / Decimal(86400)
    if total_days < 365:
        return f"{int(total_days)} 天 {int(total_hours % 24)} 小時"
    years = total_days / Decimal("365.25")
    if years < 1_000_000:
        return f"{int(years):,} 年"
    return f"{years:.3e} 年"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else N
    answer = 2 ** n
    print(f"測試 n = {n}，2^{n} = {answer}（共 {len(str(answer))} 位數）")
    print("=" * 78)

    methods = [
        ("方法 1  2**n",              power2n_builtin, None),
        ("方法 2a 遞迴+遞迴 (2a+2a)", power2n_double,  None),
        ("方法 2b 2*power2n(n-1)",    power2n_times2,  None),
        ("方法 3  遞迴+查表",         power2n_memo,    reset_table),
    ]

    print(f"{'方法':<34}{'耗時/次':>16}{'重複':>8}  結果")
    print("-" * 78)

    rate_2a = None
    for name, fn, setup in methods:
        per_call, repeat, result, err = bench(fn, n, setup=setup)
        if err is not None:
            e, elapsed = err
            if isinstance(e, CallLimitExceeded):
                rate_2a = (counter.calls - 1) / elapsed if elapsed > 0 else None
                note = (f"失敗：超過 {counter.calls - 1:,} 次呼叫仍算不完"
                        f"（耗時 {human_time(elapsed)}）")
            elif isinstance(e, RecursionError):
                note = "失敗：Python 遞迴深度上限 (RecursionError)"
            else:
                note = f"失敗：{type(e).__name__}: {e}"
            print(f"{name:<34}{'--':>16}{'--':>8}  {note}")
            continue

        ok = "[OK] 正確" if result == answer else "[NG] 錯誤"
        print(f"{name:<34}{human_time(per_call):>16}{repeat:>8}  {ok}")

    print("-" * 78)
    total_calls = 2 ** n - 1
    if rate_2a:
        est = Decimal(total_calls) / Decimal(str(rate_2a))
        print(f"方法 2a 呼叫次數 = 2^{n} - 1 = {sci(total_calls)} 次"
              f"，實測速率 {sci(rate_2a)} 次/秒")
        print(f"→ 估算跑完 n = {n} 需要約 {human_time(est)}（永遠跑不出來）")
    else:
        print(f"方法 2a 呼叫次數 = 2^{n} - 1 = {sci(total_calls)} 次")

    if n >= 8:
        print("-" * 78)
        print("方法 2a 小 n 實測（呼叫次數 2^n - 1，每增加 1 就 x2）：")
        print(f"{'n':>4}{'呼叫次數':>14}{'耗時':>14}{'倍數':>10}")
        prev = None
        for k in range(8, min(n, 21) + 1):
            t0 = time.perf_counter()
            reset_counter(limit=float("inf"))
            power2n_double(k)
            t = time.perf_counter() - t0
            ratio = f"{t / prev:.2f}x" if prev else "-"
            print(f"{k:>4}{2 ** k - 1:>14,}{human_time(t):>14}{ratio:>10}")
            prev = t


if __name__ == "__main__":
    main()
