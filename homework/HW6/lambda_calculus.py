import argparse
import os
import re
import sys
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Var:
    v: Any            


@dataclass(frozen=True)
class Abs:
    param: Optional[str]  
    body: Any


@dataclass(frozen=True)
class App:
    fn: Any
    arg: Any


class LcError(Exception):
    def __init__(self, msg, pos=None, line=None):
        super().__init__(msg)
        self.msg, self.pos, self.line = msg, pos, line


def tokenize(src: str):
    toks, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
        elif c in '().=':
            toks.append((c, None, i)); i += 1
        elif c in 'λ\\':
            toks.append(('lam', None, i)); i += 1
        elif '0' <= c <= '9':
            j = i
            while j < n and '0' <= src[j] <= '9':
                j += 1
            toks.append(('num', int(src[i:j]), i)); i = j
        elif (c.isalpha() or c == '_'):
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] in "_'") and src[j] != 'λ':
                j += 1
            toks.append(('id', src[i:j], i)); i = j
        else:
            raise LcError('無法辨識的字元「%s」' % c, i)
    return toks


def tok_text(k):
    return 'λ' if k[0] == 'lam' else (str(k[1]) if k[0] in ('id', 'num') else k[0])


def church_numeral(n: int):
    if n > 400:
        raise LcError('Church 數 %d 太大 (上限 400)' % n)
    b = Var('x')
    for _ in range(n):
        b = App(Var('f'), b)
    return Abs('f', Abs('x', b))


def parse_tokens(toks, mode, defs):
    pos = 0

    def peek():
        return toks[pos] if pos < len(toks) else None

    def starts_atom(k):
        return k is not None and k[0] in ('id', 'num', '(', 'lam')

    def expr(scope):
        first = peek()
        left = None
        while starts_atom(peek()):
            a = abs_(scope) if peek()[0] == 'lam' else atom(scope)
            left = a if left is None else App(left, a)
        if left is None:
            if first:
                raise LcError('此處需要一個項，卻遇到「%s」' % tok_text(first), first[2])
            raise LcError('運算式不完整，結尾缺少一個項')
        return left

    def abs_(scope):
        nonlocal pos
        lam = toks[pos]; pos += 1
        if mode == 'named':
            params = []
            while peek() and peek()[0] == 'id':
                params.append(toks[pos][1]); pos += 1
            if not params:
                raise LcError('λ 後面需要至少一個參數名稱', lam[2])
            if not peek() or peek()[0] != '.':
                raise LcError('參數列後面需要「.」', peek()[2] if peek() else lam[2])
            pos += 1
            body = expr(list(reversed(params)) + scope)
            for p in reversed(params):
                body = Abs(p, body)
            return body
        if peek() and peek()[0] == '.':
            pos += 1
        return Abs(None, expr(scope + 1))

    def atom(scope):
        nonlocal pos
        k = toks[pos]
        if k[0] == '(':
            pos += 1
            e = expr(scope)
            if not peek() or peek()[0] != ')':
                raise LcError('缺少右括號「)」', k[2])
            pos += 1
            return e
        if k[0] == 'num':
            pos += 1
            return church_numeral(k[1]) if mode == 'named' else Var(k[1])
        pos += 1  # id
        name = k[1]
        if mode == 'named':
            if name in scope:
                return Var(name)
            return defs[name] if name in defs else Var(name)
        if name in defs:
            return defs[name]
        raise LcError('無名模式找不到定義「%s」。無名模式的變數請改用 de Bruijn 索引數字 '
                      '(0 = 最內層的 λ)' % name, k[2])

    if not toks:
        raise LcError('運算式是空的')
    t = expr([] if mode == 'named' else 0)
    if pos < len(toks):
        raise LcError('多餘的符號「%s」(括號不成對？)' % tok_text(toks[pos]), toks[pos][2])
    return t


_NAME = r"([^\W\d][\w']*)"
DEF_RE = re.compile(r'^(?:let\s+)?' + _NAME + r'\s*=\s*(.+)$', re.S)
BARE_DEF_RE = re.compile(r'^(?:let\s+)?' + _NAME + r'\s*=\s*$')


def parse_program(src: str, mode: str):
    """回傳 (defs: dict, def_list: [(name, term)], exprs: [(原文, 項, 行號)])"""
    logical, buf, start, depth = [], '', 0, 0
    for li, line in enumerate(src.split('\n'), 1):
        cuts = [i for i in (line.find('--'), line.find('#')) if i >= 0]
        if cuts:
            line = line[:min(cuts)]
        if buf == '' and line.strip() == '':
            continue
        if buf == '':
            start = li
        buf += (' ' if buf else '') + line.strip()
        depth += line.count('(') - line.count(')')
        if depth > 0:
            continue
        logical.append((buf, start))
        buf, depth = '', 0
    if buf:
        raise LcError('括號沒有閉合', None, start)

    defs: Dict[str, Any] = {}
    def_list: List[Tuple[str, Any]] = []
    exprs: List[Tuple[str, Any, int]] = []
    for text, line in logical:
        try:
            m = BARE_DEF_RE.match(text)
            if m:
                raise LcError('定義「%s」的「=」右邊沒有內容' % m.group(1))
            m = DEF_RE.match(text)
            if m:
                term = parse_tokens(tokenize(m.group(2)), mode, defs)
                defs[m.group(1)] = term
                def_list.append((m.group(1), term))
            else:
                exprs.append((text, parse_tokens(tokenize(text), mode, defs), line))
        except LcError as e:
            if e.line is None:
                e.line = line
            raise
    if not exprs:
        if 'main' in defs:
            exprs.append(('main', defs['main'], 0))
        elif def_list:
            exprs.append((def_list[-1][0], def_list[-1][1], 0))
        else:
            raise LcError('沒有可以執行的運算式')
    return defs, def_list, exprs


NAME_POOL = ['x', 'y', 'z', 'u', 'v', 'w', 'a', 'b', 'c', 'd']


def binder_name(d: int) -> str:
    return NAME_POOL[d % len(NAME_POOL)] + "'" * (d // len(NAME_POOL))


def to_db(t, bound: List[str], free_ctx: List[str]):
    """具名 -> 無名。free_ctx 記錄自由變數的編號 (跨呼叫共用以保持一致)。"""
    if isinstance(t, Var):
        if t.v in bound:
            return Var(bound.index(t.v))
        if t.v not in free_ctx:
            free_ctx.append(t.v)
        return Var(len(bound) + free_ctx.index(t.v))
    if isinstance(t, Abs):
        return Abs(None, to_db(t.body, [t.param] + bound, free_ctx))
    return App(to_db(t.fn, bound, free_ctx), to_db(t.arg, bound, free_ctx))


def from_db(t, depth: int = 0):
    """無名 -> 具名。綁定變數依深度命名 x,y,z…；自由變數叫 fv0, fv1…"""
    if isinstance(t, Var):
        return Var(binder_name(depth - 1 - t.v)) if t.v < depth else Var('fv%d' % (t.v - depth))
    if isinstance(t, Abs):
        return Abs(binder_name(depth), from_db(t.body, depth + 1))
    return App(from_db(t.fn, depth), from_db(t.arg, depth))


def free_vars(t) -> set:
    out, cnt = set(), {}

    def go(t):
        if isinstance(t, Var):
            if not cnt.get(t.v):
                out.add(t.v)
        elif isinstance(t, Abs):
            cnt[t.param] = cnt.get(t.param, 0) + 1
            go(t.body)
            cnt[t.param] -= 1
        else:
            go(t.fn); go(t.arg)
    go(t)
    return out


def subst_named(t, x: str, s, notes: List[str], fv_s: set):
    """t[x := s]；發生 α-轉換時把說明寫入 notes。"""
    if isinstance(t, Var):
        return s if t.v == x else t
    if isinstance(t, App):
        f = subst_named(t.fn, x, s, notes, fv_s)
        a = subst_named(t.arg, x, s, notes, fv_s)
        return t if (f is t.fn and a is t.arg) else App(f, a)
    if t.param == x:
        return t
    fv_b = free_vars(t.body)
    if x not in fv_b:
        return t
    if t.param in fv_s:
        avoid = fv_s | fv_b | {x}
        y2 = t.param
        while y2 in avoid:
            y2 += "'"
        notes.append('λ%s 會捕獲被代入項中的自由變數 %s，先把它改名為 %s' % (t.param, t.param, y2))
        body2 = subst_named(t.body, t.param, Var(y2), notes, {y2})
        return Abs(y2, subst_named(body2, x, s, notes, fv_s))
    b = subst_named(t.body, x, s, notes, fv_s)
    return t if b is t.body else Abs(t.param, b)


def beta_named(redex: App, notes: List[str]):
    return subst_named(redex.fn.body, redex.fn.param, redex.arg, notes, free_vars(redex.arg))


def shift(d: int, c: int, t):
    if isinstance(t, Var):
        return Var(t.v + d) if t.v >= c else t
    if isinstance(t, Abs):
        return Abs(None, shift(d, c + 1, t.body))
    return App(shift(d, c, t.fn), shift(d, c, t.arg))


def subst_db(j: int, s, t):
    if isinstance(t, Var):
        return s if t.v == j else t
    if isinstance(t, Abs):
        return Abs(None, subst_db(j + 1, shift(1, 0, s), t.body))
    return App(subst_db(j, s, t.fn), subst_db(j, s, t.arg))


def beta_db(redex: App):
    """(λ. M) N  →  ↓1( M[0 := ↑1 N] )"""
    return shift(-1, 0, subst_db(0, shift(1, 0, redex.arg), redex.fn.body))


STRATEGIES = {
    'normal':      ('正規序 (最左最外)', '先規約最左、最外層的 redex；只要正規形存在就一定找得到。'),
    'applicative': ('應用序 (最左最內)', '先規約最內層的 redex，等於先算引數；可能在有正規形的項上無限迴圈。'),
    'cbn':         ('傳名呼叫 (不進入 λ)', '同正規序，但不會規約 λ 內部，停在弱頭正規形。'),
    'cbv':         ('傳值呼叫 (不進入 λ)', '先算引數、不規約 λ 內部，是多數程式語言的求值方式。'),
}


def find_redex(t, strat: str):
    under_lam = strat in ('normal', 'applicative')
    inner = strat in ('applicative', 'cbv')

    def go(t, path):
        if isinstance(t, Var):
            return None
        if isinstance(t, Abs):
            return go(t.body, path + ('b',)) if under_lam else None
        if not inner:
            if isinstance(t.fn, Abs):
                return path
            r = go(t.fn, path + ('f',))
            return r if r is not None else go(t.arg, path + ('a',))
        r = go(t.fn, path + ('f',))
        if r is None:
            r = go(t.arg, path + ('a',))
        if r is not None:
            return r
        return path if isinstance(t.fn, Abs) else None
    return go(t, ())


def get_at(t, path):
    for k in path:
        t = t.fn if k == 'f' else t.arg if k == 'a' else t.body
    return t


def replace_at(t, path, sub, i=0):
    if i == len(path):
        return sub
    k = path[i]
    if k == 'f':
        return App(replace_at(t.fn, path, sub, i + 1), t.arg)
    if k == 'a':
        return App(t.fn, replace_at(t.arg, path, sub, i + 1))
    return Abs(t.param, replace_at(t.body, path, sub, i + 1))


class Ann:
    __slots__ = ('src', 'key', 'fl', 'fn', 'arg', 'body')

    def __init__(self, src, key, fl, fn=None, arg=None, body=None):
        self.src, self.key, self.fl, self.fn, self.arg, self.body = src, key, fl, fn, arg, body


INF = float('inf')


def annotate(t, bound: List[str], mode: str) -> Ann:
    if isinstance(t, Var):
        if mode == 'named':
            if t.v in bound:
                i = bound.index(t.v)
                return Ann(t, str(i), i + 1)
            return Ann(t, 'F' + t.v, INF)
        return Ann(t, str(t.v), t.v + 1)
    if isinstance(t, Abs):
        b = annotate(t.body, ([t.param] + bound) if mode == 'named' else bound, mode)
        return Ann(t, 'L' + b.key, max(0, b.fl - 1), body=b)
    f, a = annotate(t.fn, bound, mode), annotate(t.arg, bound, mode)
    return Ann(t, '(' + f.key + ' ' + a.key + ')', max(f.fl, a.fl), fn=f, arg=a)


def term_key(t, mode: str) -> str:
    return annotate(t, [], mode).key


_NUM_RE = re.compile(r'^LL((?:\(1 )*)0(\)*)$')


def numeral_of_key(key: str) -> Optional[int]:
    m = _NUM_RE.match(key)
    if m and len(m.group(1)) // 3 == len(m.group(2)):
        return len(m.group(2))
    return None


def build_name_table(def_list, mode: str) -> Dict[str, List[str]]:
    table: Dict[str, List[str]] = {}
    for name, term in def_list:
        a = annotate(term, [], mode)
        if a.fl != 0 or isinstance(term, Var):
            continue
        names = table.setdefault(a.key, [])
        if name not in names:
            names.append(name)
    return table


@dataclass
class Step:
    term: Any
    rdx: Optional[tuple]  
    res: Optional[tuple]  
    redex: Any = None       
    notes: Optional[List[str]] = None


def evaluate(term, mode: str, strategy: str, max_steps: int, max_key: int = 120000):
    steps: List[Step] = []
    seen: Dict[str, int] = {}
    cur, res, status, loop_to = term, None, 'done', -1
    i = 0
    while True:
        path = find_redex(cur, strategy)
        key = term_key(cur, mode)
        if path is None:
            steps.append(Step(cur, None, res)); status = 'done'; break
        if key in seen:
            steps.append(Step(cur, path, res)); status = 'loop'; loop_to = seen[key]; break
        if len(key) > max_key:
            steps.append(Step(cur, path, res)); status = 'big'; break
        if i >= max_steps:
            steps.append(Step(cur, path, res)); status = 'limit'; break
        seen[key] = i
        redex, notes = get_at(cur, path), []
        result = beta_named(redex, notes) if mode == 'named' else beta_db(redex)
        steps.append(Step(cur, path, res, redex, notes))
        cur, res = replace_at(cur, path, result), path
        i += 1
    return steps, status, loop_to

RESET = '\x1b[0m'


class Style:
    """mark: 'none' 不標示 | 'text' 用 «» ‹› | 'ansi' 用終端機顏色"""

    def __init__(self, mark: str):
        self.mark = mark

    def _ansi(self, code, s):
        o = '\x1b[%sm' % code
        return o + s.replace(RESET, RESET + o) + RESET

    def rdx(self, s):
        return {'none': s, 'text': '«' + s + '»'}.get(self.mark) or self._ansi('30;43', s)

    def res(self, s):
        return {'none': s, 'text': '‹' + s + '›'}.get(self.mark) or self._ansi('30;42', s)

    def nm(self, s):
        return self._ansi('35;1', s) if self.mark == 'ansi' else s


def print_term(term, mode: str, style: Style, fold=False, numerals=False,
               name_table=None, rdx=None, res=None) -> str:
    root = annotate(term, [], mode)

    def prefix(a, b):
        return len(a) <= len(b) and b[:len(a)] == a

    def fold_at(n: Ann, path):
        if not (fold or numerals) or isinstance(n.src, Var) or n.fl != 0:
            return None
        if rdx is not None and prefix(path, rdx):
            return None
        if res is not None and len(path) < len(res) and prefix(path, res):
            return None
        if fold and name_table and n.key in name_table:
            return name_table[n.key][0]
        if numerals:
            k = numeral_of_key(n.key)
            if k is not None:
                return str(k)
        return None

    def pr(n: Ann, path):
        fname = fold_at(n, path)
        if fname is not None:
            s, kind = style.nm(fname), 'atom'
        elif isinstance(n.src, Var):
            s, kind = (n.src.v if mode == 'named' else str(n.src.v)), 'atom'
        elif isinstance(n.src, Abs):
            if mode == 'named':
                params, cur, cp = [n.src.param], n, path
                while isinstance(cur.body.src, Abs):
                    bp = cp + ('b',)
                    if bp == rdx or bp == res or fold_at(cur.body, bp) is not None:
                        break
                    params.append(cur.body.src.param)
                    cur, cp = cur.body, bp
                s = 'λ' + ' '.join(params) + '. ' + pr(cur.body, cp + ('b',))[0]
            else:
                s = 'λ.' + pr(n.body, path + ('b',))[0]
            kind = 'abs'
        else:
            f, fk = pr(n.fn, path + ('f',))
            a, ak = pr(n.arg, path + ('a',))
            s = ('(' + f + ')' if fk == 'abs' else f) + ' ' + (a if ak == 'atom' else '(' + a + ')')
            kind = 'app'
        if res is not None and path == res:
            s = style.res(s)
        if rdx is not None and path == rdx:
            s = style.rdx(s)
        return s, kind

    return pr(root, ())[0]


def describe_result(term, mode: str, name_table) -> List[str]:
    a = annotate(term, [], mode)
    if a.fl != 0:
        return ['含有自由變數 (開放項)']
    out = []
    names = name_table.get(a.key) if name_table else None
    if names:
        out.append('與定義 ' + '、'.join(names) + ' α-等價')
    n = numeral_of_key(a.key)
    if n is not None:
        out.append('Church 數 %d' % n)
    if a.key == 'LL1':
        out.append('Church 布林 TRUE (λx y. x)')
    if a.key == 'LL0':
        out.append('Church 布林 FALSE (λx y. y)，同時也是 Church 數 0')
    return out


def run_program(src: str, mode: str = 'named', strategy: str = 'normal', max_steps: int = 500,
                fold: bool = True, numerals: bool = False, dual: bool = False,
                notes: bool = True, mark: str = 'text', step_mode: bool = False,
                out=print) -> str:
    """執行並印出完整過程，回傳 Markdown 版本的過程文件。"""
    defs, def_list, exprs = parse_program(src, mode)
    table = build_name_table(def_list, mode)
    weak = strategy in ('cbn', 'cbv')
    style, plain = Style(mark), Style('none')
    alt_mode = 'db' if mode == 'named' else 'named'
    alt_label = '無名' if mode == 'named' else '具名'
    md = ['# λ 演算規約過程', '',
          '- 記法：' + ('具名' if mode == 'named' else '無名 (de Bruijn)'),
          '- 策略：' + STRATEGIES[strategy][0], '', '## 程式', '', '```', src.strip(), '```', '']
    fk = dict(fold=fold, numerals=numerals, name_table=table)
    show_all = not step_mode

    def pause():
        nonlocal show_all
        if show_all:
            return
        try:
            ans = input('    ── Enter 下一步 / a 全部 / q 離開 ▸ ').strip().lower()
        except EOFError:
            ans = 'a'
        if ans == 'q':
            raise SystemExit(0)
        if ans == 'a':
            show_all = True

    for ei, (text, term, _line) in enumerate(exprs, 1):
        ctx: List[str] = []
        steps, status, loop_to = evaluate(term, mode, strategy, max_steps)
        last_i = len(steps) - 1
        out('')
        out('═' * 72)
        out('式 %d：%s' % (ei, text))
        out('記法：%s　策略：%s' % ('具名' if mode == 'named' else '無名 (de Bruijn)', STRATEGIES[strategy][0]))
        out('─' * 72)
        md += ['## 式 %d：`%s`' % (ei, text), '']
        for i, st in enumerate(steps):
            out('[%3d] %s' % (i, print_term(st.term, mode, style, rdx=st.rdx, res=st.res, **fk)))
            plain_s = print_term(st.term, mode, plain, **fk)
            alt_plain = None
            if dual:
                t2 = to_db(st.term, [], ctx) if mode == 'named' else from_db(st.term)
                out('      %s：%s' % (alt_label, print_term(t2, alt_mode, style, rdx=st.rdx, res=st.res, **fk)))
                alt_plain = print_term(t2, alt_mode, plain, **fk)
            md.append('%d. `%s`' % (i, plain_s) + ('　(%s：`%s`)' % (alt_label, alt_plain) if alt_plain else ''))
            if st.redex is not None:
                m_ = print_term(st.redex.fn.body, mode, plain, fold=fold, numerals=numerals, name_table=table)
                n_ = print_term(st.redex.arg, mode, plain, fold=fold, numerals=numerals, name_table=table)
                if mode == 'named':
                    line = 'β：把 %s 換成 %s，作用在主體 %s' % (st.redex.fn.param, n_, m_)
                else:
                    line = 'β：在主體 %s 把索引 0 換成 ↑%s，再整體 ↓1' % (m_, n_)
                if notes:
                    out('      ' + line)
                    for nt in st.notes:
                        out('      α：' + nt)
                md.append('   - ' + line)
                md += ['   - α-轉換：' + nt for nt in st.notes]
            if i == last_i:
                if status == 'done':
                    msg = ('✓ 沒有可規約的 redex。此策略不進入 λ 內部，所以這是弱頭正規形。' if weak
                           else '✓ 沒有可規約的 redex，這就是正規形。')
                elif status == 'loop':
                    msg = '∞ 這一項與第 %d 步 α-等價，再規約一步又會回到相同的項，此策略下不會終止。' % loop_to
                elif status == 'limit':
                    msg = '⚠ 已達步數上限 %d，停止規約 (可用 --max 調高)。' % max_steps
                else:
                    msg = '⚠ 項已經變得太大，停止規約。'
                out('      ' + msg)
                md += ['', msg, '']
            elif not show_all:
                pause()

        last = steps[-1]
        label = ('結果 (弱頭正規形)' if weak else '結果 (正規形)') if status == 'done' else '最後的項'
        out('─' * 72)
        out('%s：%s' % (label, print_term(last.term, mode, style, fold=fold, numerals=numerals, name_table=table)))
        t2 = to_db(last.term, [], ctx) if mode == 'named' else from_db(last.term)
        out('%s記法：%s' % (alt_label, print_term(t2, alt_mode, style, fold=fold, numerals=numerals, name_table=table)))
        if status == 'done':
            d = describe_result(last.term, mode, table)
            if d:
                out('說明：' + '；'.join(d))
        out('β 規約共 %d 步' % last_i)
        md.append('**%s**：`%s`　(β 規約 %d 步)' % (
            label, print_term(last.term, mode, plain, fold=fold, numerals=numerals, name_table=table), last_i))
        md.append('')
        show_all = not step_mode or show_all
    return '\n'.join(md)


LIB_NUM = """\
-- Church 數的基本運算 (數字 2、3 會自動展開成 λf x. f (f x))
SUCC = λn f x. f (n f x)
ADD  = λm n. m SUCC n
MULT = λm n f. m (n f)
PRED = λn f x. n (λg h. h (g f)) (λu. x) (λu. u)
"""

EXAMPLES: Dict[str, Dict[str, Any]] = {
    'num': dict(title='Church 數：加、乘、前驅', mode='named', strategy='normal', max=500, nums=True,
                note='數字 n 會自動變成 Church 數；加上 --nums 會把結果還原成數字。',
                code=LIB_NUM + "\nADD 2 3\nMULT 2 3\nPRED 3\n"),
    'bool': dict(title='Church 布林：AND / OR / NOT', mode='named', strategy='normal', max=200,
                 note='布林值就是「二選一」的函數：TRUE 取第一個、FALSE 取第二個。',
                 code="""\
TRUE  = λx y. x
FALSE = λx y. y
NOT = λp. p FALSE TRUE
AND = λp q. p q p
OR  = λp q. p p q

AND TRUE FALSE
OR FALSE TRUE
NOT (AND TRUE TRUE)
"""),
    'alpha': dict(title="α-轉換：避免變數被捕獲", mode='named', strategy='normal', max=100, dual=True,
                  note="代入的 y 若直接放進 λy 底下就會被捕獲，所以先把內層 y 改名成 y'。--dual 可看到無名版完全不需要改名。",
                  code="""\
-- 自由變數 y 被代入到 λy 之下，必須 α-轉換
(λx. λy. x y) y

-- 再多一個例子
(λx. λy. y x) (y y)
"""),
    'ski': dict(title='SKI 組合子：S K K a = a', mode='named', strategy='normal', max=100,
                note='S K K 的行為跟恆等函數 I 一樣。',
                code="""\
S = λx y z. x z (y z)
K = λx y. x
I = λx. x

S K K a
S K K (S K K) b
"""),
    'lazy': dict(title='K z Ω：正規序會終止', mode='named', strategy='normal', max=100,
                 note='正規序不計算沒用到的引數 Ω，所以直接得到 z。改用 -s applicative 看看。',
                 code="Ω = (λx. x x) (λx. x x)\nK = λx y. x\nK z Ω\n"),
    'eager': dict(title='K z Ω：應用序不會終止', mode='named', strategy='applicative', max=100,
                  note='應用序先算引數 Ω，Ω 規約後還是 Ω，解譯器偵測到「回到同一個項」就停止。',
                  code="Ω = (λx. x x) (λx. x x)\nK = λx y. x\nK z Ω\n"),
    'omega': dict(title='Ω：無窮迴圈', mode='named', strategy='normal', max=100,
                  note='Ω 規約一步又變回自己。',
                  code="(λx. x x) (λx. x x)\n"),
    'cbv': dict(title='傳值呼叫：停在 λ 之前', mode='named', strategy='cbv', max=100, nums=True,
                note='傳值/傳名呼叫不進入 λ 內部，結果是弱頭正規形，不一定是完整的正規形。',
                code=LIB_NUM + "\nADD 2 3\nMULT 2 3\n"),
    'fact': dict(title='Y 組合子：階乘 FACT 3', mode='named', strategy='normal', max=1000, nums=True,
                 note='用 Y 組合子做遞迴，正規序約 700 步算出 6。步驟很多，建議搭配 --md 存檔或 --step。',
                 code="""\
Y      = λf. (λx. f (x x)) (λx. f (x x))
IF     = λp a b. p a b
ISZERO = λn. n (λx. λa b. b) (λa b. a)
MULT   = λm n f. m (n f)
PRED   = λn f x. n (λg h. h (g f)) (λu. x) (λu. u)

FACT = Y (λf n. IF (ISZERO n) 1 (MULT n (f (PRED n))))

FACT 3
"""),
    'db-basic': dict(title='無名：索引與自由變數', mode='db', strategy='normal', max=100, dual=True,
                     note='0 代表最內層的 λ，1 代表再外一層。超出 λ 數量的索引是自由變數 (第二式中的 1)。',
                     code="""\
-- λx. x  與  λx y. x
(λ. 0) (λ. λ. 1)

-- 索引 1 在 λ 之外，是自由變數；代入後要 shift
(λ. 0 1) (λ. 0)
"""),
    'db-bool': dict(title='無名：Church 布林', mode='db', strategy='normal', max=100, dual=True,
                    note='TRUE = λx y. x 寫成 λ.λ.1；FALSE = λx y. y 寫成 λ.λ.0。',
                    code="""\
TRUE  = λ.λ.1
FALSE = λ.λ.0
NOT   = λ. 0 FALSE TRUE
AND   = λ.λ. 1 0 1

AND TRUE FALSE
NOT FALSE
"""),
    'db-add': dict(title='無名：Church 數 2 + 3', mode='db', strategy='normal', max=100, dual=True, nums=True,
                   note='ADD = λm n f x. m f (n f x)，寫成 λ.λ.λ.λ. 3 1 (2 1 0)。',
                   code="""\
SUCC  = λ.λ.λ. 1 (2 1 0)
ADD   = λ.λ.λ.λ. 3 1 (2 1 0)
TWO   = λ.λ. 1 (1 0)
THREE = λ.λ. 1 (1 (1 0))

ADD TWO THREE
"""),
    'db-ski': dict(title='無名：SKI 組合子', mode='db', strategy='normal', max=100, dual=True,
                   note='S = λx y z. x z (y z) 寫成 λ.λ.λ. 2 0 (1 0)。',
                   code="""\
S = λ.λ.λ. 2 0 (1 0)
K = λ.λ. 1

S K K (λ. 0)
"""),
    'db-omega': dict(title='無名：Ω 無窮迴圈', mode='db', strategy='normal', max=100,
                     note='無名版用索引直接比較 α-等價，不需要重新命名，偵測循環特別簡單。',
                     code="(λ. 0 0) (λ. 0 0)\n"),
}


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    ap = argparse.ArgumentParser(
        description='Lambda Calculus 解譯器：顯示完整的規約過程 (具名 / 無名 de Bruijn)',
        epilog='不給任何參數時，會執行內建範例 num。語法與用法請看檔案開頭的說明。')
    ap.add_argument('file', nargs='?', help='程式檔 (用 - 代表從標準輸入讀)')
    ap.add_argument('-e', '--expr', help='直接執行這段程式')
    ap.add_argument('--example', metavar='名稱', help='執行內建範例 (--list 查看)')
    ap.add_argument('--list', action='store_true', help='列出內建範例')
    ap.add_argument('-m', '--mode', choices=['named', 'db'], help='named 具名 / db 無名 (預設 named)')
    ap.add_argument('-s', '--strategy', choices=list(STRATEGIES), help='規約策略 (預設 normal)')
    ap.add_argument('--max', type=int, help='步數上限 (預設 500)')
    ap.add_argument('--no-fold', action='store_true', help='不要把已定義的名稱折疊顯示')
    ap.add_argument('--nums', action='store_true', help='把 Church 數顯示成數字')
    ap.add_argument('--dual', action='store_true', help='每一步同時顯示另一種記法')
    ap.add_argument('--no-notes', action='store_true', help='不顯示每一步的 β/α 說明')
    ap.add_argument('--step', action='store_true', help='單步執行 (按 Enter 看下一步)')
    ap.add_argument('--md', metavar='檔名', help='把過程文件存成 Markdown')
    ap.add_argument('--color', dest='color', action='store_true', default=None, help='強制使用顏色標示')
    ap.add_argument('--no-color', dest='color', action='store_false', help='不使用顏色，改用 «» ‹› 標示')
    args = ap.parse_args(argv)

    if args.list:
        print('內建範例 (用 --example 名稱 執行)：')
        for name, e in EXAMPLES.items():
            print('  %-9s [%s] %s' % (name, '具名' if e['mode'] == 'named' else '無名', e['title']))
        return 0

    opt: Dict[str, Any] = {}
    if args.expr is not None:
        src = args.expr
    elif args.file:
        try:
            src = sys.stdin.read() if args.file == '-' else open(args.file, encoding='utf-8').read()
        except OSError as e:
            print('讀不到檔案：%s' % e, file=sys.stderr)
            return 2
    else:
        name = args.example or 'num'
        if name not in EXAMPLES:
            print('沒有這個範例「%s」。用 --list 查看。' % name, file=sys.stderr)
            return 2
        e = EXAMPLES[name]
        src, opt = e['code'], e
        print('範例 %s：%s\n%s' % (name, e['title'], e.get('note', '')))

    mode = args.mode or opt.get('mode', 'named')
    strategy = args.strategy or opt.get('strategy', 'normal')
    max_steps = args.max or opt.get('max', 500)
    use_color = args.color if args.color is not None else (sys.stdout.isatty() and not os.environ.get('NO_COLOR'))

    result: Dict[str, Any] = {}

    def work():
        try:
            result['md'] = run_program(
                src, mode, strategy, max_steps, fold=not args.no_fold,
                numerals=args.nums or opt.get('nums', False), dual=args.dual or opt.get('dual', False),
                notes=not args.no_notes, mark='ansi' if use_color else 'text', step_mode=args.step)
        except LcError as e:
            where = '第 %d 行：' % e.line if e.line else ''
            print('錯誤：%s%s' % (where, e.msg), file=sys.stderr)
            result['err'] = 1
        except (SystemExit, BrokenPipeError):
            result['err'] = 0

    sys.setrecursionlimit(200000)
    for size in (512, 128, 32):
        try:
            threading.stack_size(size * 1024 * 1024)
            break
        except (ValueError, RuntimeError):
            continue
    th = threading.Thread(target=work)
    th.start()
    th.join()
    if result.get('err') is not None:
        return result['err']
    if args.md:
        with open(args.md, 'w', encoding='utf-8') as f:
            f.write(result['md'] + '\n')
        print('\n過程文件已存到 %s' % args.md)
    return 0


if __name__ == '__main__':
    sys.exit(main())
