"""NeoFortran Interpreter — Tree-Walking Evaluator"""
import math, cmath, time, sys, os
import concurrent.futures
from typing import Any, Dict, List, Optional
from .ast_nodes import *


# ── Runtime values ────────────────────────────────────────────────────────────
class NeoNull:
    def __repr__(self): return "null"
    def __bool__(self): return False

NULL = NeoNull()

class NeoVec(list):
    """Scientific vector with operator overloading"""
    def __add__(self, o):
        if isinstance(o, NeoVec): return NeoVec(a+b for a,b in zip(self,o))
        return NeoVec(a+o for a in self)
    def __sub__(self, o):
        if isinstance(o, NeoVec): return NeoVec(a-b for a,b in zip(self,o))
        return NeoVec(a-o for a in self)
    def __mul__(self, o):
        if isinstance(o, NeoVec): return sum(a*b for a,b in zip(self,o))  # dot product
        return NeoVec(a*o for a in self)
    def __rmul__(self, o): return NeoVec(a*o for a in self)
    def __truediv__(self, o): return NeoVec(a/o for a in self)
    def __repr__(self): return "[" + ", ".join(str(x) for x in self) + "]"
    def norm(self): return math.sqrt(sum(x*x for x in self))
    def dot(self, o): return sum(a*b for a,b in zip(self,o))

class NeoMatrix(list):
    """Scientific matrix"""
    def __init__(self, rows): super().__init__(NeoVec(r) for r in rows)
    def __add__(self, o):
        return NeoMatrix([[a+b for a,b in zip(r1,r2)] for r1,r2 in zip(self,o)])
    def __sub__(self, o):
        return NeoMatrix([[a-b for a,b in zip(r1,r2)] for r1,r2 in zip(self,o)])
    def __mul__(self, o):
        if isinstance(o, (int,float)):
            return NeoMatrix([[a*o for a in r] for r in self])
        if isinstance(o, NeoMatrix):
            cols = len(o[0]); rows = len(self); n = len(o)
            return NeoMatrix([[sum(self[i][k]*o[k][j] for k in range(n)) for j in range(cols)] for i in range(rows)])
        return NotImplemented
    def __matmul__(self, o): return self.__mul__(o)
    def transpose(self):
        return NeoMatrix([[self[i][j] for i in range(len(self))] for j in range(len(self[0]))])
    def __repr__(self):
        return "[\n" + "\n".join("  "+str(list(r)) for r in self) + "\n]"

class NeoList(list):
    def __repr__(self): return "[" + ", ".join(repr(x) for x in self) + "]"

class NeoMap(dict):
    def __repr__(self): return "{" + ", ".join(f"{repr(k)}: {repr(v)}" for k,v in self.items()) + "}"

class NeoSet(set):
    def __repr__(self): return "{" + ", ".join(repr(x) for x in self) + "}"

class NeoBuiltin:
    def __init__(self, name, fn): self.name = name; self.fn = fn
    def __call__(self, *a): return self.fn(*a)
    def __repr__(self): return f"<builtin {self.name}>"

class NeoFunc:
    def __init__(self, decl, env): self.decl = decl; self.env = env
    def __repr__(self): return f"<function {self.decl.name}>"

class NeoSub:
    def __init__(self, decl, env): self.decl = decl; self.env = env
    def __repr__(self): return f"<subroutine {self.decl.name}>"

class NeoLambda:
    def __init__(self, params, body, env): self.params=params; self.body=body; self.env=env
    def __repr__(self): return "<lambda>"

class NeoClass:
    def __init__(self, decl, env, super_cls=None):
        self.decl=decl; self.env=env; self.super_cls=super_cls; self.methods={}
    def __repr__(self): return f"<class {self.decl.name}>"

class NeoInstance:
    def __init__(self, klass):
        self.klass=klass; self.fields: Dict[str,Any]={}
    def get(self, name):
        if name in self.fields: return self.fields[name]
        cls = self.klass
        while cls:
            if name in cls.methods: return BoundMethod(self, cls.methods[name])
            cls = cls.super_cls
        raise NeoError(f"'{self.klass.decl.name}' has no attribute '{name}'")
    def set(self, name, val): self.fields[name] = val
    def __repr__(self):
        f = ", ".join(f"{k}={repr(v)}" for k,v in self.fields.items())
        return f"{self.klass.decl.name}({f})"

class BoundMethod:
    def __init__(self, inst, method): self.inst=inst; self.method=method
    def __repr__(self): return f"<bound {self.inst.klass.decl.name}.{getattr(getattr(self.method,'decl',None),'name','')}>"

class NeoAIModel:
    """Simulated AI model"""
    def __init__(self, path): self.path=path; self.loaded=True
    def predict(self, data):
        if isinstance(data, NeoVec): return NeoVec(x*1.1 for x in data)
        if isinstance(data, NeoMatrix): return NeoMatrix([[x*1.1 for x in r] for r in data])
        return data
    def __repr__(self): return f"<AIModel path={self.path!r}>"

class NeoSimulation:
    def __init__(self, domain, results):
        self.domain=domain; self.results=results
    def __repr__(self): return f"<Simulation domain={self.domain!r} steps={len(self.results)}>"

# ── Signals ───────────────────────────────────────────────────────────────────
class RetSig(Exception):
    def __init__(self, v): self.v = v
class BreakSig(Exception): pass
class ContSig(Exception):  pass
class NeoError(Exception):
    def __init__(self, msg, line=0): super().__init__(msg); self.neo_msg=msg; self.line=line
class NeoUserError(Exception):
    def __init__(self, v): self.v=v; super().__init__(str(v))

# ── Environment ───────────────────────────────────────────────────────────────
class Env:
    def __init__(self, parent=None):
        self.vars: Dict[str,Any]={}; self.parent=parent
    def get(self, n):
        if n in self.vars: return self.vars[n]
        if self.parent: return self.parent.get(n)
        raise NeoError(f"Undefined: '{n}'")
    def set(self, n, v):
        if n in self.vars: self.vars[n]=v; return
        if self.parent and self.parent.has(n): self.parent.set(n,v); return
        self.vars[n]=v
    def define(self, n, v): self.vars[n]=v
    def has(self, n): return n in self.vars or (self.parent.has(n) if self.parent else False)
    def child(self): return Env(self)


# ── Interpreter ───────────────────────────────────────────────────────────────
class Interpreter:
    def __init__(self, output=None):
        self.out = output or sys.stdout
        self.glob = Env()
        self._setup()

    def _setup(self):
        e = self.glob
        def _p(*a): print(*[self._disp(x) for x in a], end="", file=self.out); return NULL
        def _pl(*a): print(*[self._disp(x) for x in a], file=self.out); return NULL
        e.define("print",   NeoBuiltin("print", _p))
        e.define("println", NeoBuiltin("println", _pl))
        e.define("input",   NeoBuiltin("input", lambda p="": input(p)))
        e.define("len",     NeoBuiltin("len", lambda x: len(x)))
        e.define("range",   NeoBuiltin("range", lambda *a: NeoList(range(*[int(x) for x in a]))))
        e.define("str",     NeoBuiltin("str", lambda x: self._disp(x)))
        e.define("int",     NeoBuiltin("int", lambda x: int(float(x)) if not isinstance(x,bool) else int(x)))
        e.define("float",   NeoBuiltin("float", lambda x: float(x)))
        e.define("bool",    NeoBuiltin("bool", lambda x: bool(x)))
        e.define("complex", NeoBuiltin("complex", lambda r,i=0: complex(r,i)))
        e.define("abs",     NeoBuiltin("abs", lambda x: abs(x)))
        e.define("round",   NeoBuiltin("round", lambda x,n=0: round(x,n)))
        e.define("min",     NeoBuiltin("min", lambda *a: min(a[0]) if len(a)==1 else min(*a)))
        e.define("max",     NeoBuiltin("max", lambda *a: max(a[0]) if len(a)==1 else max(*a)))
        e.define("sum",     NeoBuiltin("sum", lambda x: sum(x)))
        e.define("sorted",  NeoBuiltin("sorted", lambda x: NeoList(sorted(x))))
        e.define("reversed",NeoBuiltin("reversed", lambda x: NeoList(reversed(list(x)))))
        e.define("type",    NeoBuiltin("type", self._type_of))
        e.define("assert",  NeoBuiltin("assert", lambda c,m="Assertion failed": None if c else (_ for _ in ()).throw(NeoError(str(m)))))
        e.define("sqrt",    NeoBuiltin("sqrt", lambda x: math.sqrt(x)))
        e.define("PI",      math.pi)
        e.define("E",       math.e)
        e.define("INF",     math.inf)
        # Scientific
        e.define("dot",     NeoBuiltin("dot", lambda a,b: sum(x*y for x,y in zip(a,b))))
        e.define("norm",    NeoBuiltin("norm", lambda v: math.sqrt(sum(x*x for x in v))))
        e.define("zeros",   NeoBuiltin("zeros", lambda n: NeoVec([0.0]*n)))
        e.define("ones",    NeoBuiltin("ones", lambda n: NeoVec([1.0]*n)))
        e.define("linspace",NeoBuiltin("linspace", lambda a,b,n: NeoVec(a+(b-a)*i/(n-1) for i in range(n))))
        e.define("transpose",NeoBuiltin("transpose", lambda m: m.transpose() if isinstance(m,NeoMatrix) else m))
        # AI
        e.define("ai",      NeoBuiltin("ai", lambda: NeoMap({"load": NeoBuiltin("load", lambda p: NeoAIModel(p))})))
        e.define("vector",  NeoBuiltin("vector", lambda *a: NeoVec(a) if a else NeoVec()))
        e.define("matrix",  NeoBuiltin("matrix", lambda *rows: NeoMatrix(rows)))
        e.define("map",     NeoBuiltin("map", lambda fn,it: NeoList(self._call(fn,[x]) for x in it)))
        e.define("filter",  NeoBuiltin("filter", lambda fn,it: NeoList(x for x in it if self._call(fn,[x]))))
        e.define("reduce",  NeoBuiltin("reduce", lambda fn,it,init=None: self._reduce(fn,it,init)))
        e.define("zip",     NeoBuiltin("zip", lambda *a: NeoList(NeoList(x) for x in zip(*a))))
        e.define("enumerate",NeoBuiltin("enumerate", lambda x: NeoList(NeoList([i,v]) for i,v in enumerate(x))))

    def _disp(self, v):
        if isinstance(v, bool): return "true" if v else "false"
        if isinstance(v, NeoNull): return "null"
        if isinstance(v, float): return str(int(v)) if v==int(v) else str(v)
        if isinstance(v, str): return v
        return repr(v)

    def _type_of(self, v):
        if isinstance(v, bool): return "bool"
        if isinstance(v, int): return "int"
        if isinstance(v, float): return "float"
        if isinstance(v, complex): return "complex"
        if isinstance(v, str): return "string"
        if isinstance(v, NeoNull): return "null"
        if isinstance(v, NeoVec): return "vector"
        if isinstance(v, NeoMatrix): return "matrix"
        if isinstance(v, NeoList): return "array"
        if isinstance(v, NeoMap): return "map"
        if isinstance(v, NeoInstance): return v.klass.decl.name
        if isinstance(v, NeoAIModel): return "AIModel"
        return type(v).__name__

    def _reduce(self, fn, it, init):
        lst = list(it)
        acc = lst[0] if init is None else init
        for x in (lst[1:] if init is None else lst): acc = self._call(fn,[acc,x])
        return acc

    def execute(self, ast: Block, env=None):
        env = env or self.glob
        r = NULL
        for s in ast.stmts: r = self.ev(s, env)
        return r

    def ev(self, node: Node, env: Env) -> Any:
        if node is None: return NULL
        m = 'ev_' + node.__class__.__name__
        fn = getattr(self, m, None)
        if fn: return fn(node, env)
        raise NeoError(f"Unknown node: {node.__class__.__name__}", getattr(node,'line',0))

    # Literals
    def ev_IntLit(self,n,e):     return n.value
    def ev_FloatLit(self,n,e):   return n.value
    def ev_StrLit(self,n,e):     return n.value
    def ev_BoolLit(self,n,e):    return n.value
    def ev_NullLit(self,n,e):    return NULL
    def ev_ComplexLit(self,n,e): return n.value

    def ev_VectorLit(self, n, e):
        return NeoVec(self.ev(x,e) for x in n.elements)

    def ev_MatrixLit(self, n, e):
        rows = []
        for row in n.rows:
            if isinstance(row, list): rows.append([self.ev(x,e) for x in row])
            else: rows.append([self.ev(row,e)])
        return NeoMatrix(rows)

    def ev_ArrayLit(self, n, e):
        return NeoList(self.ev(x,e) for x in n.elements)

    def ev_MapLit(self, n, e):
        return NeoMap({self.ev(k,e): self.ev(v,e) for k,v in n.pairs})

    def ev_ListComp(self, n, e):
        res = NeoList()
        for item in self.ev(n.iterable,e):
            ch = e.child(); ch.define(n.var, item)
            if n.cond and not self.ev(n.cond,ch): continue
            res.append(self.ev(n.expr,ch))
        return res

    # Access
    def ev_Ident(self, n, e):
        try: return e.get(n.name)
        except NeoError: raise NeoError(f"Undefined variable: '{n.name}'", n.line)

    def ev_Member(self, n, e):
        obj = self.ev(n.obj, e); return self._get_attr(obj, n.attr, n.line)

    def ev_SafeMember(self, n, e):
        obj = self.ev(n.obj, e)
        return NULL if isinstance(obj, NeoNull) else self._get_attr(obj, n.attr, n.line)

    def ev_Index(self, n, e):
        obj = self.ev(n.obj,e); idx = self.ev(n.idx,e)
        try:
            if isinstance(obj, NeoMap): return obj.get(idx, NULL)
            return obj[idx]
        except (IndexError,KeyError) as ex: raise NeoError(f"Index error: {ex}", n.line)

    def ev_Slice(self, n, e):
        obj = self.ev(n.obj,e)
        s = self.ev(n.start,e) if n.start else None
        t = self.ev(n.stop,e)  if n.stop  else None
        sp = self.ev(n.step,e) if n.step  else None
        r = obj[s:t:sp]
        return NeoVec(r) if isinstance(obj,NeoVec) else NeoList(r)

    def _get_attr(self, obj, name, line=0):
        if isinstance(obj, NeoInstance): return obj.get(name)
        if isinstance(obj, NeoClass):
            if name in obj.methods: return obj.methods[name]
        if isinstance(obj, NeoMap):
            if name in obj: return obj[name]
            return self._map_method(obj, name, line)
        if isinstance(obj, str):    return self._str_method(obj, name, line)
        if isinstance(obj, NeoVec): return self._vec_method(obj, name, line)
        if isinstance(obj, NeoMatrix): return self._mat_method(obj, name, line)
        if isinstance(obj, NeoList): return self._list_method(obj, name, line)
        if isinstance(obj, NeoAIModel):
            if name == "predict": return NeoBuiltin("predict", obj.predict)
            if name == "loaded":  return obj.loaded
        raise NeoError(f"No attribute '{name}' on {type(obj).__name__}", line)

    def _str_method(self, s, name, line):
        m = {
            "upper": NeoBuiltin("upper", lambda: s.upper()),
            "lower": NeoBuiltin("lower", lambda: s.lower()),
            "trim":  NeoBuiltin("trim",  lambda: s.strip()),
            "split": NeoBuiltin("split", lambda sep=" ": NeoList(s.split(sep))),
            "replace": NeoBuiltin("replace", lambda a,b: s.replace(a,b)),
            "contains": NeoBuiltin("contains", lambda sub: sub in s),
            "startsWith": NeoBuiltin("startsWith", lambda p: s.startswith(p)),
            "endsWith":   NeoBuiltin("endsWith",   lambda p: s.endswith(p)),
            "indexOf":    NeoBuiltin("indexOf",    lambda sub: s.find(sub)),
            "length": len(s), "size": len(s),
            "isEmpty": len(s)==0,
        }
        if name in m: return m[name]
        raise NeoError(f"String has no attribute '{name}'", line)

    def _vec_method(self, v, name, line):
        m = {
            "length": len(v), "size": len(v),
            "norm":   NeoBuiltin("norm", lambda: v.norm()),
            "dot":    NeoBuiltin("dot",  lambda o: v.dot(o)),
            "sum":    NeoBuiltin("sum",  lambda: sum(v)),
            "mean":   NeoBuiltin("mean", lambda: sum(v)/len(v) if v else 0),
            "max":    NeoBuiltin("max",  lambda: max(v)),
            "min":    NeoBuiltin("min",  lambda: min(v)),
            "push":   NeoBuiltin("push", lambda x: v.append(x) or NULL),
            "map":    NeoBuiltin("map",  lambda fn: NeoVec(self._call(fn,[x]) for x in v)),
            "filter": NeoBuiltin("filter", lambda fn: NeoVec(x for x in v if self._call(fn,[x]))),
            "toList": NeoBuiltin("toList", lambda: NeoList(v)),
            "normalize": NeoBuiltin("normalize", lambda: v/v.norm() if v.norm()!=0 else v),
            "slice":  NeoBuiltin("slice", lambda a,b=None: NeoVec(v[a:b])),
        }
        if name in m: return m[name]
        raise NeoError(f"Vector has no attribute '{name}'", line)

    def _mat_method(self, m, name, line):
        attrs = {
            "rows":    len(m),
            "cols":    len(m[0]) if m else 0,
            "transpose": NeoBuiltin("transpose", lambda: m.transpose()),
            "row":     NeoBuiltin("row", lambda i: m[i]),
            "col":     NeoBuiltin("col", lambda j: NeoVec(m[i][j] for i in range(len(m)))),
            "sum":     NeoBuiltin("sum", lambda: sum(sum(r) for r in m)),
            "map":     NeoBuiltin("map", lambda fn: NeoMatrix([[self._call(fn,[x]) for x in r] for r in m])),
        }
        if name in attrs: return attrs[name]
        raise NeoError(f"Matrix has no attribute '{name}'", line)

    def _list_method(self, lst, name, line):
        m = {
            "push":    NeoBuiltin("push", lambda x: lst.append(x) or NULL),
            "pop":     NeoBuiltin("pop",  lambda *a: lst.pop(*[int(x) for x in a])),
            "length":  len(lst), "size": len(lst),
            "isEmpty": len(lst)==0,
            "contains":NeoBuiltin("contains", lambda x: x in lst),
            "indexOf": NeoBuiltin("indexOf", lambda x: lst.index(x) if x in lst else -1),
            "map":     NeoBuiltin("map", lambda fn: NeoList(self._call(fn,[x]) for x in lst)),
            "filter":  NeoBuiltin("filter", lambda fn: NeoList(x for x in lst if self._call(fn,[x]))),
            "reduce":  NeoBuiltin("reduce", lambda fn,i=None: self._reduce(fn,lst,i)),
            "sort":    NeoBuiltin("sort", lambda: lst.sort() or NeoList(lst)),
            "reverse": NeoBuiltin("reverse", lambda: NeoList(reversed(lst))),
            "join":    NeoBuiltin("join", lambda sep="": sep.join(self._disp(x) for x in lst)),
            "slice":   NeoBuiltin("slice", lambda a,b=None: NeoList(lst[a:b])),
            "first":   lst[0] if lst else NULL,
            "last":    lst[-1] if lst else NULL,
            "sum":     NeoBuiltin("sum", lambda: sum(lst)),
            "mean":    NeoBuiltin("mean", lambda: sum(lst)/len(lst) if lst else 0),
        }
        if name in m: return m[name]
        raise NeoError(f"List has no attribute '{name}'", line)

    def _map_method(self, d, name, line):
        m = {
            "get":    NeoBuiltin("get", lambda k,dflt=NULL: d.get(k,dflt)),
            "set":    NeoBuiltin("set", lambda k,v: d.update({k:v}) or NULL),
            "has":    NeoBuiltin("has", lambda k: k in d),
            "remove": NeoBuiltin("remove", lambda k: d.pop(k,NULL)),
            "keys":   NeoBuiltin("keys", lambda: NeoList(d.keys())),
            "values": NeoBuiltin("values", lambda: NeoList(d.values())),
            "size":   len(d), "length": len(d),
        }
        if name in m: return m[name]
        raise NeoError(f"Map has no attribute '{name}'", line)

    # Operators
    def ev_BinOp(self, n, e):
        if n.op=='and':
            l=self.ev(n.left,e); return l if not l else self.ev(n.right,e)
        if n.op=='or':
            l=self.ev(n.left,e); return l if l else self.ev(n.right,e)
        l=self.ev(n.left,e); r=self.ev(n.right,e)
        try:
            if n.op=='+':
                if isinstance(l,str) or isinstance(r,str): return self._disp(l)+self._disp(r)
                if isinstance(l,NeoVec) and isinstance(r,NeoVec): return l+r
                return l+r
            if n.op=='-': return l-r
            if n.op=='*':
                if isinstance(l,NeoVec) and isinstance(r,(int,float)): return l*r
                return l*r
            if n.op=='/':
                if r==0: raise NeoError("Division by zero", n.line)
                return l/r
            if n.op=='%': return l%r
            if n.op=='**': return l**r
            if n.op=='//': return l//r
            if n.op=='++':
                if isinstance(l,str): return l+self._disp(r)
                if isinstance(l,(NeoList,NeoVec)): return NeoList(list(l)+list(r))
                return str(l)+str(r)
            if n.op=='==': return l==r
            if n.op=='!=': return l!=r
            if n.op=='<':  return l<r
            if n.op=='>':  return l>r
            if n.op=='<=': return l<=r
            if n.op=='>=': return l>=r
        except TypeError as ex: raise NeoError(f"Type error '{n.op}': {ex}", n.line)
        raise NeoError(f"Unknown op: {n.op}", n.line)

    def ev_UnOp(self, n, e):
        v=self.ev(n.operand,e)
        if n.op=='-': return -v
        if n.op=='not': return not v
        raise NeoError(f"Unknown unary: {n.op}")

    def ev_MatMul(self, n, e):
        l=self.ev(n.left,e); r=self.ev(n.right,e)
        if isinstance(l,NeoMatrix) and isinstance(r,NeoMatrix): return l@r
        if isinstance(l,NeoMatrix) and isinstance(r,NeoVec):
            return NeoVec(sum(l[i][j]*r[j] for j in range(len(r))) for i in range(len(l)))
        raise NeoError("@ operator requires matrix operands", n.line)

    def ev_Ternary(self,n,e):
        return self.ev(n.then_e if self.ev(n.cond,e) else n.else_e, e)

    def ev_Pipe(self,n,e):
        v=self.ev(n.val,e); fn=self.ev(n.fn,e); return self._call(fn,[v])

    def ev_TypeCheck(self,n,e):
        v=self.ev(n.expr,e)
        if isinstance(v,NeoInstance): return v.klass.decl.name==n.tname
        type_map={'int':int,'float':float,'string':str,'bool':bool,'null':NeoNull,
                  'vector':NeoVec,'matrix':NeoMatrix,'array':NeoList,'map':NeoMap}
        t=type_map.get(n.tname.lower())
        return isinstance(v,t) if t else False

    def ev_NullCoal(self,n,e):
        v=self.ev(n.expr,e); return self.ev(n.default,e) if isinstance(v,NeoNull) else v

    def ev_Cast(self,n,e):
        v=self.ev(n.expr,e); t=n.target.name.lower()
        try:
            if t=='int':    return int(float(v))
            if t=='float':  return float(v)
            if t=='string': return self._disp(v)
            if t=='bool':   return bool(v)
            if t=='complex':return complex(v)
            if t in ('vector','array'): return NeoVec(v) if t=='vector' else NeoList(v)
        except: raise NeoError(f"Cannot cast to {t}", n.line)
        return v

    # Calls
    def ev_Call(self, n, e):
        callee = self.ev(n.callee, e)
        args = [self.ev(a.val, e) for a in n.args]
        return self._call(callee, args, n)

    def _call(self, callee, args, node=None):
        line = getattr(node,'line',0)
        if isinstance(callee, NeoBuiltin):
            try: return callee.fn(*args)
            except NeoError: raise
            except Exception as ex: raise NeoError(f"Builtin '{callee.name}': {ex}", line)
        if isinstance(callee, BoundMethod):
            return self._call_method(callee.inst, callee.method, args, line)
        if isinstance(callee, NeoFunc):
            return self._call_func(callee, args, line)
        if isinstance(callee, NeoSub):
            return self._call_sub(callee, args, line)
        if isinstance(callee, NeoLambda):
            return self._call_lambda(callee, args, line)
        if isinstance(callee, NeoClass):
            return self._instantiate(callee, args, line)
        if callable(callee): return callee(*args)
        raise NeoError(f"'{callee}' is not callable", line)

    def _bind(self, params, args, env, line):
        for i,p in enumerate(params):
            if p.vararg: env.define(p.name, NeoList(args[i:])); return
            if i < len(args): env.define(p.name, args[i])
            elif p.default: env.define(p.name, self.ev(p.default, env))
            else: raise NeoError(f"Missing argument '{p.name}'", line)

    def _call_func(self, fn, args, line):
        ch = fn.env.child(); ch.define('self', NULL)
        self._bind(fn.decl.params, args, ch, line)
        try: self.ev(fn.decl.body, ch); return NULL
        except RetSig as r: return r.v

    def _call_sub(self, sub, args, line):
        ch = sub.env.child()
        self._bind(sub.decl.params, args, ch, line)
        try: self.ev(sub.decl.body, ch)
        except RetSig: pass
        return NULL

    def _call_lambda(self, lam, args, line):
        ch = lam.env.child()
        for p,v in zip(lam.params, args): ch.define(p,v)
        return self.ev(lam.body, ch)

    def _call_method(self, inst, method, args, line):
        decl = method.decl
        ch = method.env.child() if hasattr(method,'env') else self.glob.child()
        ch.define('self', inst)
        self._bind(decl.params, args, ch, line)
        try: self.ev(decl.body, ch); return NULL
        except RetSig as r: return r.v

    def _instantiate(self, klass, args, line):
        inst = NeoInstance(klass)
        # Collect fields + methods from class hierarchy
        cls = klass
        while cls:
            for m in cls.decl.body:
                if isinstance(m, VarDecl):
                    if m.name not in inst.fields:
                        inst.fields[m.name] = self.ev(m.init, klass.env) if m.init else NULL
                elif isinstance(m, (FuncDecl, SubDecl)):
                    if m.name not in klass.methods:
                        fn = NeoFunc(m, klass.env) if isinstance(m, FuncDecl) else NeoSub(m, klass.env)
                        klass.methods[m.name] = fn
            cls = cls.super_cls
        if 'init' in klass.methods:
            self._call_method(inst, klass.methods['init'], args, line)
        return inst

    def ev_New(self, n, e):
        try: klass = e.get(n.cls)
        except NeoError: raise NeoError(f"Unknown class: '{n.cls}'", n.line)
        args = [self.ev(a.val, e) for a in n.args]
        return self._call(klass, args, n)

    def ev_Lambda(self, n, e):
        return NeoLambda(n.params, n.body, e)

    def ev_Await(self, n, e): return self.ev(n.expr, e)
    def ev_Yield(self, n, e):
        v = self.ev(n.expr, e) if n.expr else NULL; raise RetSig(v)
    def ev_Spread(self, n, e): return self.ev(n.expr, e)
    def ev_Arg(self, n, e):    return self.ev(n.val, e)

    def ev_SuperCall(self, n, e):
        inst = e.get('self')
        if not isinstance(inst, NeoInstance): raise NeoError("'super' outside class", n.line)
        sup = inst.klass.super_cls
        if not sup: raise NeoError("No superclass", n.line)
        args = [self.ev(a.val, e) for a in n.args]
        if n.method:
            m = sup.methods.get(n.method)
            if not m: raise NeoError(f"Superclass has no '{n.method}'", n.line)
            return self._call_method(inst, m, args, n.line)
        init = sup.methods.get('init')
        if init: self._call_method(inst, init, args, n.line)
        return NULL

    # Declarations
    def ev_VarDecl(self, n, e):
        v = self.ev(n.init, e) if n.init else NULL
        e.define(n.name, v); return v

    def ev_FuncDecl(self, n, e):
        fn = NeoFunc(n, e); e.define(n.name, fn); return fn

    def ev_SubDecl(self, n, e):
        s = NeoSub(n, e); e.define(n.name, s); return s

    def ev_ClassDecl(self, n, e):
        sup = None
        if n.superclass:
            try: sup = e.get(n.superclass)
            except: raise NeoError(f"Unknown superclass: '{n.superclass}'", n.line)
        klass = NeoClass(n, e, sup); e.define(n.name, klass); return klass

    def ev_InterfaceDecl(self, n, e):
        e.define(n.name, {"__interface__": n.name}); return NULL

    def ev_ModuleDecl(self, n, e):
        child = e.child()
        for s in n.body: self.ev(s, child)
        e.define(n.name, NeoMap({k:v for k,v in child.vars.items()}))
        return NULL

    # Statements
    def ev_Block(self, n, e):
        r = NULL
        for s in n.stmts: r = self.ev(s, e)
        return r

    def ev_ExprStmt(self, n, e): return self.ev(n.expr, e)

    def ev_Assign(self, n, e):
        v = self.ev(n.val, e)
        if n.op != '=':
            cur = self.ev(n.target, e)
            ops = {'+=':lambda a,b:a+b, '-=':lambda a,b:a-b,
                   '*=':lambda a,b:a*b, '/=':lambda a,b:a/b}
            v = ops[n.op](cur, v)
        t = n.target
        if isinstance(t, Ident): e.set(t.name, v)
        elif isinstance(t, Member):
            obj = self.ev(t.obj, e)
            if isinstance(obj, NeoInstance): obj.set(t.attr, v)
            elif isinstance(obj, NeoMap):    obj[t.attr] = v
            else: raise NeoError(f"Cannot set member on {type(obj).__name__}", n.line)
        elif isinstance(t, Index):
            obj = self.ev(t.obj, e); idx = self.ev(t.idx, e); obj[idx] = v
        else: raise NeoError("Invalid assignment target", n.line)
        return v

    def ev_Return(self, n, e):
        raise RetSig(self.ev(n.val, e) if n.val else NULL)

    def ev_Break(self, n, e):    raise BreakSig()
    def ev_Continue(self, n, e): raise ContSig()

    def ev_Raise(self, n, e):
        v = self.ev(n.expr, e) if n.expr else NULL; raise NeoUserError(v)

    def ev_Import(self, n, e):
        from . import stdlib as _std
        mod = n.module
        if hasattr(_std, mod):
            obj = getattr(_std, mod)
            exports = obj.EXPORTS if hasattr(obj,'EXPORTS') else {}
            if n.is_from:
                for nm in n.names:
                    if nm in exports: e.define(nm, exports[nm])
                    else: raise NeoError(f"'{nm}' not in module '{mod}'")
            else:
                alias = n.alias or mod
                e.define(alias, NeoMap(exports))
        else: raise NeoError(f"Module '{mod}' not found")
        return NULL

    # Control Flow
    def ev_If(self, n, e):
        if self.ev(n.cond, e): return self.ev(n.then_b, e.child())
        for c,b in n.elifs:
            if self.ev(c, e): return self.ev(b, e.child())
        if n.else_b: return self.ev(n.else_b, e.child())
        return NULL

    def ev_ForRange(self, n, e):
        s=self.ev(n.start,e); t=self.ev(n.stop,e); st=self.ev(n.step,e) if n.step else 1
        i=s
        while (st>0 and i<=t) or (st<0 and i>=t):
            ch=e.child(); ch.define(n.var,i)
            try: self.ev(n.body,ch)
            except BreakSig: break
            except ContSig: pass
            i+=st
        return NULL

    def ev_ForEach(self, n, e):
        for item in self.ev(n.iterable,e):
            ch=e.child(); ch.define(n.var,item)
            try: self.ev(n.body,ch)
            except BreakSig: break
            except ContSig: continue
        return NULL

    def ev_ForIdx(self, n, e):
        for i,v in enumerate(self.ev(n.iterable,e)):
            ch=e.child(); ch.define(n.ivar,i); ch.define(n.vvar,v)
            try: self.ev(n.body,ch)
            except BreakSig: break
            except ContSig: continue
        return NULL

    def ev_ParallelFor(self, n, e):
        s=int(self.ev(n.start,e)); t=int(self.ev(n.stop,e))
        results = []
        with concurrent.futures.ThreadPoolExecutor() as pool:
            futs = {}
            for i in range(s, t+1):
                ch=e.child(); ch.define(n.var,i)
                futs[pool.submit(self.ev, n.body, ch)] = i
            for f in concurrent.futures.as_completed(futs):
                try: results.append(f.result())
                except: pass
        return NeoList(results)

    def ev_While(self, n, e):
        while self.ev(n.cond,e):
            ch=e.child()
            try: self.ev(n.body,ch)
            except BreakSig: break
            except ContSig: continue
        return NULL

    def ev_Match(self, n, e):
        subj=self.ev(n.subject,e)
        for case in n.cases:
            pat=self.ev(case.pattern,e)
            if subj==pat or pat=='_':
                if case.guard and not self.ev(case.guard,e): continue
                return self.ev(case.body,e.child())
        if n.otherwise: return self.ev(n.otherwise,e.child())
        return NULL

    def ev_Try(self, n, e):
        try: self.ev(n.try_b, e.child())
        except NeoUserError as ex:
            for et,ev,eb in n.excepts:
                ch=e.child()
                if ev: ch.define(ev, ex.v)
                self.ev(eb,ch); break
        except NeoError as ex:
            for et,ev,eb in n.excepts:
                ch=e.child()
                if ev: ch.define(ev, str(ex))
                self.ev(eb,ch); break
            else: raise
        finally:
            if n.finally_b: self.ev(n.finally_b, e.child())
        return NULL

    def ev_Simulate(self, n, e):
        ch=e.child()
        domains = {
            "fluid":    {"viscosity":0.001,"density":1000,"velocity":0.0,"pressure":101325},
            "heat":     {"temperature":300,"conductivity":50,"flux":0.0},
            "quantum":  {"hbar":1.055e-34,"mass":9.11e-31,"psi":complex(1,0)},
            "particle": {"mass":1.0,"velocity":0.0,"force":0.0,"energy":0.0},
            "circuit":  {"voltage":0.0,"current":0.0,"resistance":1.0,"power":0.0},
        }
        params = domains.get(n.domain.lower(), {})
        for k,v in params.items(): ch.define(k, v)
        ch.define("time", 0.0); ch.define("dt", 0.001); ch.define("step", 0)
        results = []
        try: self.ev(n.body, ch); results.append(dict(ch.vars))
        except RetSig as r: results.append(r.v)
        return NeoSimulation(n.domain, results)

    def ev_MatchCase(self, n, e): return NULL
    def generic(self, node): raise NeoError(f"Unhandled: {node.__class__.__name__}")
