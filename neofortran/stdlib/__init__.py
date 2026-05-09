"""NeoFortran Standard Library"""
import math as _m, cmath as _cm, os as _os, sys as _sys
import json as _j, re as _re, random as _r, time as _t
import statistics as _st, itertools as _it, functools as _ft

from ..interpreter import (NeoBuiltin, NeoVec, NeoMatrix, NeoList, NeoMap,
                            NeoNull, NULL, NeoError)

def _b(name, fn): return NeoBuiltin(name, fn)


# ══════════════════════════════════════════════
#  1. math
# ══════════════════════════════════════════════
class math:
    EXPORTS = NeoMap({
        "PI": _m.pi, "E": _m.e, "TAU": _m.tau, "INF": _m.inf,
        "sqrt":    _b("sqrt",   lambda x: _m.sqrt(x)),
        "cbrt":    _b("cbrt",   lambda x: x**(1/3)),
        "abs":     _b("abs",    lambda x: abs(x)),
        "floor":   _b("floor",  lambda x: _m.floor(x)),
        "ceil":    _b("ceil",   lambda x: _m.ceil(x)),
        "round":   _b("round",  lambda x,n=0: round(x,n)),
        "pow":     _b("pow",    lambda x,y: x**y),
        "exp":     _b("exp",    lambda x: _m.exp(x)),
        "log":     _b("log",    lambda x,b=_m.e: _m.log(x,b)),
        "log2":    _b("log2",   lambda x: _m.log2(x)),
        "log10":   _b("log10",  lambda x: _m.log10(x)),
        "sin":     _b("sin",    lambda x: _m.sin(x)),
        "cos":     _b("cos",    lambda x: _m.cos(x)),
        "tan":     _b("tan",    lambda x: _m.tan(x)),
        "asin":    _b("asin",   lambda x: _m.asin(x)),
        "acos":    _b("acos",   lambda x: _m.acos(x)),
        "atan":    _b("atan",   lambda x: _m.atan(x)),
        "atan2":   _b("atan2",  lambda y,x: _m.atan2(y,x)),
        "hypot":   _b("hypot",  lambda x,y: _m.hypot(x,y)),
        "degrees": _b("degrees",lambda x: _m.degrees(x)),
        "radians": _b("radians",lambda x: _m.radians(x)),
        "factorial":_b("factorial",lambda n: _m.factorial(int(n))),
        "gcd":     _b("gcd",    lambda a,b: _m.gcd(int(a),int(b))),
        "lcm":     _b("lcm",    lambda a,b: abs(int(a)*int(b))//_m.gcd(int(a),int(b))),
        "sign":    _b("sign",   lambda x: 1 if x>0 else (-1 if x<0 else 0)),
        "clamp":   _b("clamp",  lambda x,lo,hi: max(lo,min(hi,x))),
        "lerp":    _b("lerp",   lambda a,b,t: a+(b-a)*t),
        "isNaN":   _b("isNaN",  lambda x: _m.isnan(x)),
        "isFinite":_b("isFinite",lambda x: _m.isfinite(x)),
    })


# ══════════════════════════════════════════════
#  2. linalg  — Linear Algebra
# ══════════════════════════════════════════════
def _eye(n):
    return NeoMatrix([[1.0 if i==j else 0.0 for j in range(n)] for i in range(n)])

def _zeros_mat(r,c):
    return NeoMatrix([[0.0]*c for _ in range(r)])

def _det2(m):
    return m[0][0]*m[1][1]-m[0][1]*m[1][0]

def _trace(m):
    return sum(m[i][i] for i in range(min(len(m),len(m[0]))))

def _matnorm(m):
    return _m.sqrt(sum(x*x for row in m for x in row))

def _outer(a,b):
    return NeoMatrix([[x*y for y in b] for x in a])

def _cross(a,b):
    return NeoVec([a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]])

class linalg:
    EXPORTS = NeoMap({
        "dot":       _b("dot",      lambda a,b: sum(x*y for x,y in zip(a,b))),
        "cross":     _b("cross",    _cross),
        "norm":      _b("norm",     lambda v: _m.sqrt(sum(x*x for x in v))),
        "normalize": _b("normalize",lambda v: NeoVec(x/max(_m.sqrt(sum(x*x for x in v)),1e-12) for x in v)),
        "eye":       _b("eye",      _eye),
        "zeros":     _b("zeros",    lambda r,c=None: _zeros_mat(r,c or r)),
        "ones":      _b("ones",     lambda r,c=None: NeoMatrix([[1.0]*(c or r) for _ in range(r)])),
        "transpose": _b("transpose",lambda m: m.transpose()),
        "trace":     _b("trace",    _trace),
        "det":       _b("det",      _det2),
        "outer":     _b("outer",    _outer),
        "matmul":    _b("matmul",   lambda a,b: a@b),
        "norm_mat":  _b("norm_mat", _matnorm),
        "linspace":  _b("linspace", lambda a,b,n: NeoVec(a+(b-a)*i/(n-1) for i in range(int(n)))),
        "arange":    _b("arange",   lambda a,b,s=1: NeoVec(list(_m.frange(a,b,s)) if hasattr(_m,'frange') else [a+i*s for i in range(int((b-a)/s))])),
        "sum_vec":   _b("sum_vec",  lambda v: sum(v)),
        "mean":      _b("mean",     lambda v: sum(v)/len(v) if v else 0),
        "var":       _b("var",      lambda v: _st.variance(v) if len(v)>1 else 0),
        "std":       _b("std",      lambda v: _st.stdev(v) if len(v)>1 else 0),
    })


# ══════════════════════════════════════════════
#  3. io
# ══════════════════════════════════════════════
class io:
    EXPORTS = NeoMap({
        "readFile":  _b("readFile",  lambda p: open(p).read()),
        "writeFile": _b("writeFile", lambda p,c: open(p,'w').write(c) and NULL),
        "appendFile":_b("appendFile",lambda p,c: open(p,'a').write(c) and NULL),
        "readLines": _b("readLines", lambda p: NeoList(open(p).read().splitlines())),
        "exists":    _b("exists",    lambda p: _os.path.exists(p)),
        "delete":    _b("delete",    lambda p: _os.remove(p) or NULL),
        "stdin":     _b("stdin",     lambda p="": input(p)),
        "stdout":    _b("stdout",    lambda x: print(x,end="") or NULL),
        "stderr":    _b("stderr",    lambda x: print(x,file=_sys.stderr,end="") or NULL),
        "readBin":   _b("readBin",   lambda p: NeoList(open(p,'rb').read())),
        "writeBin":  _b("writeBin",  lambda p,d: open(p,'wb').write(bytes(d)) and NULL),
    })


# ══════════════════════════════════════════════
#  4. os
# ══════════════════════════════════════════════
class os:
    EXPORTS = NeoMap({
        "getcwd":  _b("getcwd",  lambda: _os.getcwd()),
        "listDir": _b("listDir", lambda p='.': NeoList(_os.listdir(p))),
        "mkdir":   _b("mkdir",   lambda p: _os.makedirs(p,exist_ok=True) or NULL),
        "exists":  _b("exists",  lambda p: _os.path.exists(p)),
        "env":     _b("env",     lambda k,d="": _os.environ.get(k,d)),
        "join":    _b("join",    lambda *p: _os.path.join(*p)),
        "basename":_b("basename",lambda p: _os.path.basename(p)),
        "run":     _b("run",     lambda c: _os.system(c)),
        "platform":_sys.platform,
        "sep":     _os.sep,
    })


# ══════════════════════════════════════════════
#  5. json
# ══════════════════════════════════════════════
def _to_neo(v):
    if isinstance(v,dict): return NeoMap({k:_to_neo(vv) for k,vv in v.items()})
    if isinstance(v,list): return NeoList(_to_neo(x) for x in v)
    if v is None: return NULL
    return v

def _from_neo(v):
    if isinstance(v,NeoNull): return None
    if isinstance(v,NeoMap): return {str(k):_from_neo(vv) for k,vv in v.items()}
    if isinstance(v,(NeoList,NeoVec)): return [_from_neo(x) for x in v]
    return v

class json:
    EXPORTS = NeoMap({
        "parse":     _b("parse",     lambda s: _to_neo(_j.loads(s))),
        "stringify": _b("stringify", lambda v,i=None: _j.dumps(_from_neo(v),indent=i,ensure_ascii=False,default=str)),
        "pretty":    _b("pretty",    lambda v: _j.dumps(_from_neo(v),indent=2,ensure_ascii=False)),
        "readFile":  _b("readFile",  lambda p: _to_neo(_j.loads(open(p).read()))),
        "writeFile": _b("writeFile", lambda p,v: open(p,'w').write(_j.dumps(_from_neo(v),indent=2)) and NULL),
    })


# ══════════════════════════════════════════════
#  6. random
# ══════════════════════════════════════════════
class random:
    EXPORTS = NeoMap({
        "int":      _b("int",     lambda a,b: _r.randint(int(a),int(b))),
        "float":    _b("float",   lambda a=0.,b=1.: _r.uniform(a,b)),
        "bool":     _b("bool",    lambda: _r.random()<0.5),
        "choice":   _b("choice",  lambda lst: _r.choice(lst)),
        "sample":   _b("sample",  lambda lst,k: NeoList(_r.sample(lst,k))),
        "shuffle":  _b("shuffle", lambda lst: NeoList(_r.sample(lst,len(lst)))),
        "seed":     _b("seed",    lambda s: _r.seed(s) or NULL),
        "uuid":     _b("uuid",    lambda: str(__import__('uuid').uuid4())),
        "normal":   _b("normal",  lambda mu=0,sigma=1: _r.gauss(mu,sigma)),
        "randn":    _b("randn",   lambda n: NeoVec(_r.gauss(0,1) for _ in range(n))),
        "randvec":  _b("randvec", lambda n,lo=0.,hi=1.: NeoVec(_r.uniform(lo,hi) for _ in range(n))),
    })


# ══════════════════════════════════════════════
#  7. time
# ══════════════════════════════════════════════
class time:
    EXPORTS = NeoMap({
        "now":       _b("now",      lambda: _t.time()),
        "sleep":     _b("sleep",    lambda s: _t.sleep(s) or NULL),
        "clock":     _b("clock",    lambda: _t.perf_counter()),
        "format":    _b("format",   lambda ts,fmt='%Y-%m-%d %H:%M:%S': __import__('datetime').datetime.fromtimestamp(ts).strftime(fmt)),
        "today":     _b("today",    lambda: str(__import__('datetime').date.today())),
        "since":     _b("since",    lambda ts: _t.time()-ts),
        "timestamp": _b("timestamp",lambda: int(_t.time())),
        "SECOND": 1, "MINUTE": 60, "HOUR": 3600, "DAY": 86400,
    })


# ══════════════════════════════════════════════
#  8. string
# ══════════════════════════════════════════════
class string:
    EXPORTS = NeoMap({
        "format":    _b("format",    lambda t,*a: t.format(*a)),
        "upper":     _b("upper",     lambda s: s.upper()),
        "lower":     _b("lower",     lambda s: s.lower()),
        "trim":      _b("trim",      lambda s: s.strip()),
        "split":     _b("split",     lambda s,sep=None: NeoList(s.split(sep))),
        "join":      _b("join",      lambda sep,lst: sep.join(str(x) for x in lst)),
        "replace":   _b("replace",   lambda s,a,b: s.replace(a,b)),
        "contains":  _b("contains",  lambda s,sub: sub in s),
        "startsWith":_b("startsWith",lambda s,p: s.startswith(p)),
        "endsWith":  _b("endsWith",  lambda s,p: s.endswith(p)),
        "reverse":   _b("reverse",   lambda s: s[::-1]),
        "repeat":    _b("repeat",    lambda s,n: s*n),
        "padLeft":   _b("padLeft",   lambda s,n,c=" ": s.rjust(n,c)),
        "padRight":  _b("padRight",  lambda s,n,c=" ": s.ljust(n,c)),
        "isDigit":   _b("isDigit",   lambda s: s.isdigit()),
        "isAlpha":   _b("isAlpha",   lambda s: s.isalpha()),
        "EMPTY": "", "NEWLINE": "\n", "TAB": "\t",
    })


# ══════════════════════════════════════════════
#  9. stats  — Statistics
# ══════════════════════════════════════════════
class stats:
    EXPORTS = NeoMap({
        "mean":     _b("mean",     lambda v: _st.mean(v)),
        "median":   _b("median",   lambda v: _st.median(v)),
        "mode":     _b("mode",     lambda v: _st.mode(v)),
        "variance": _b("variance", lambda v: _st.variance(v) if len(v)>1 else 0.0),
        "stdev":    _b("stdev",    lambda v: _st.stdev(v) if len(v)>1 else 0.0),
        "min":      _b("min",      lambda v: min(v)),
        "max":      _b("max",      lambda v: max(v)),
        "range":    _b("range",    lambda v: max(v)-min(v)),
        "sum":      _b("sum",      lambda v: sum(v)),
        "count":    _b("count",    lambda v: len(v)),
        "percentile":_b("percentile",lambda v,p: sorted(v)[int(len(v)*p/100)]),
        "normalize":_b("normalize",lambda v: NeoVec((x-min(v))/(max(v)-min(v)+1e-12) for x in v)),
        "zscore":   _b("zscore",   lambda v: NeoVec((x-_st.mean(v))/(_st.stdev(v) or 1) for x in v)),
        "covariance":_b("covariance",lambda a,b: _st.covariance(a,b) if len(a)>1 else 0.0),
        "correlation":_b("correlation",lambda a,b: _st.correlation(a,b) if len(a)>1 else 0.0),
        "histogram":_b("histogram",lambda v,n=10: NeoList(NeoList([i*(max(v)-min(v))/n+min(v), sum(1 for x in v if x>=i*(max(v)-min(v))/n+min(v) and x<(i+1)*(max(v)-min(v))/n+min(v))]) for i in range(n))),
    })


# ══════════════════════════════════════════════
#  10. algo  — Algorithms
# ══════════════════════════════════════════════
def _qsort(lst):
    if len(lst)<=1: return NeoList(lst)
    p=lst[len(lst)//2]
    return NeoList(list(_qsort(NeoList(x for x in lst if x<p)))+[x for x in lst if x==p]+list(_qsort(NeoList(x for x in lst if x>p))))

def _bsearch(lst,t):
    lo,hi=0,len(lst)-1
    while lo<=hi:
        m=(lo+hi)//2
        if lst[m]==t: return m
        elif lst[m]<t: lo=m+1
        else: hi=m-1
    return -1

def _fib(n):
    a,b=0,1; r=[]
    for _ in range(n): r.append(a); a,b=b,a+b
    return NeoList(r)

class algo:
    EXPORTS = NeoMap({
        "quickSort":    _b("quickSort",    lambda lst: _qsort(NeoList(lst))),
        "mergeSort":    _b("mergeSort",    lambda lst: NeoList(sorted(lst))),
        "binarySearch": _b("binarySearch", lambda lst,t: _bsearch(lst,t)),
        "isPrime":      _b("isPrime",      lambda n: n>1 and all(n%i!=0 for i in range(2,int(n**.5)+1))),
        "primes":       _b("primes",       lambda n: NeoList(x for x in range(2,n+1) if all(x%i!=0 for i in range(2,int(x**.5)+1)))),
        "fibonacci":    _b("fibonacci",    lambda n: _fib(n)),
        "gcd":          _b("gcd",          lambda a,b: _m.gcd(int(a),int(b))),
        "lcm":          _b("lcm",          lambda a,b: abs(int(a)*int(b))//_m.gcd(int(a),int(b))),
        "permutations": _b("permutations", lambda lst: NeoList(NeoList(p) for p in _it.permutations(lst))),
        "combinations": _b("combinations", lambda lst,r: NeoList(NeoList(c) for c in _it.combinations(lst,r))),
        "pipe":         _b("pipe",         lambda *fns: lambda x: _ft.reduce(lambda v,f: f(v),fns,x)),
        "compose":      _b("compose",      lambda *fns: lambda x: _ft.reduce(lambda v,f: f(v),reversed(fns),x)),
        "memoize":      _b("memoize",      lambda fn: _ft.lru_cache()(fn)),
    })


# ══════════════════════════════════════════════
#  11. regex
# ══════════════════════════════════════════════
class regex:
    EXPORTS = NeoMap({
        "match":   _b("match",   lambda p,s: bool(_re.match(p,s))),
        "search":  _b("search",  lambda p,s: bool(_re.search(p,s))),
        "findAll": _b("findAll", lambda p,s: NeoList(_re.findall(p,s))),
        "replace": _b("replace", lambda p,r,s: _re.sub(p,r,s)),
        "split":   _b("split",   lambda p,s: NeoList(_re.split(p,s))),
        "test":    _b("test",    lambda p,s: bool(_re.search(p,s))),
        "escape":  _b("escape",  lambda s: _re.escape(s)),
        "EMAIL":   r'^[\w.-]+@[\w.-]+\.\w{2,}$',
        "URL":     r'https?://\S+',
        "NUMBER":  r'-?\d+(\.\d+)?',
    })


# ══════════════════════════════════════════════
#  12. test  — Unit Testing
# ══════════════════════════════════════════════
_results = []; _suite = ["default"]

def _describe(name, fn): _suite[0]=name; fn(); return NULL
def _it(name, fn):
    try:
        fn(); _results.append({"name":name,"ok":True,"suite":_suite[0]})
        print(f"  ✅ {name}")
    except AssertionError as ex:
        _results.append({"name":name,"ok":False,"err":str(ex),"suite":_suite[0]})
        print(f"  ❌ {name}: {ex}")
    return NULL

class _Exp:
    def __init__(self,v): self.v=v
    def toBe(self,e):       assert self.v==e,     f"Expected {e!r}, got {self.v!r}"; return NULL
    def toEqual(self,e):    assert self.v==e,     f"Expected {e!r}, got {self.v!r}"; return NULL
    def toBeTrue(self):     assert bool(self.v),  f"Expected truthy, got {self.v!r}"; return NULL
    def toBeFalse(self):    assert not bool(self.v),f"Expected falsy, got {self.v!r}"; return NULL
    def toContain(self,x):  assert x in self.v,   f"Expected {self.v!r} to contain {x!r}"; return NULL
    def toHaveLength(self,n):assert len(self.v)==n,f"Expected length {n}, got {len(self.v)}"; return NULL
    def toBeGreaterThan(self,n): assert self.v>n, f"Expected {self.v} > {n}"; return NULL
    def toBeLessThan(self,n):    assert self.v<n, f"Expected {self.v} < {n}"; return NULL
    def toBeNull(self):     assert isinstance(self.v,NeoNull), f"Expected null"; return NULL
    def toBeClose(self,e,d=1e-6): assert abs(self.v-e)<d, f"Expected ~{e}, got {self.v}"; return NULL

def _expect(v): return _Exp(v)

def _report():
    ok=sum(1 for r in _results if r["ok"]); tot=len(_results)
    print(f"\n{'='*40}\n{ok}/{tot} passed {'✅' if ok==tot else '❌'}")
    return NeoMap({"passed":ok,"failed":tot-ok,"total":tot})

class test:
    EXPORTS = NeoMap({
        "describe": _b("describe", _describe),
        "it":       _b("it",       _it),
        "test":     _b("test",     _it),
        "expect":   _b("expect",   _expect),
        "assert":   _b("assert",   lambda c,m="Assertion failed": None if c else (_ for _ in ()).throw(AssertionError(m))),
        "report":   _b("report",   _report),
        "skip":     _b("skip",     lambda name,fn: print(f"  ⏭  {name} (skipped)") or NULL),
        "mock":     _b("mock",     lambda v: lambda *a: v),
    })
