"""NeoFortran AST Nodes"""
from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class Node:
    line: int = 0; col: int = 0
    def accept(self, v): return getattr(v,'visit_'+self.__class__.__name__, v.generic)(self)

# Literals
@dataclass
class IntLit(Node):    value: int = 0
@dataclass
class FloatLit(Node):  value: float = 0.0
@dataclass
class StrLit(Node):    value: str = ""
@dataclass
class BoolLit(Node):   value: bool = True
@dataclass
class NullLit(Node):   pass
@dataclass
class ComplexLit(Node): value: complex = 0j

# Collections
@dataclass
class VectorLit(Node):  elements: List[Node] = field(default_factory=list)
@dataclass
class MatrixLit(Node):  rows: List[List[Node]] = field(default_factory=list)
@dataclass
class ArrayLit(Node):   elements: List[Node] = field(default_factory=list)
@dataclass
class MapLit(Node):     pairs: List[tuple] = field(default_factory=list)

# Access
@dataclass
class Ident(Node):      name: str = ""
@dataclass
class Member(Node):     obj: Node = None; attr: str = ""
@dataclass
class Index(Node):      obj: Node = None; idx: Node = None
@dataclass
class Slice(Node):      obj: Node = None; start: Optional[Node] = None; stop: Optional[Node] = None; step: Optional[Node] = None
@dataclass
class SafeMember(Node): obj: Node = None; attr: str = ""

# Ops
@dataclass
class BinOp(Node):   left: Node = None; op: str = ""; right: Node = None
@dataclass
class UnOp(Node):    op: str = ""; operand: Node = None
@dataclass
class Ternary(Node): cond: Node = None; then_e: Node = None; else_e: Node = None
@dataclass
class Pipe(Node):    val: Node = None; fn: Node = None
@dataclass
class MatMul(Node):  left: Node = None; right: Node = None   # @ operator
@dataclass
class VecAdd(Node):  left: Node = None; right: Node = None
@dataclass
class VecMul(Node):  left: Node = None; right: Node = None; scalar: bool = False

# Calls
@dataclass
class Arg(Node):     val: Node = None; kw: Optional[str] = None
@dataclass
class Call(Node):    callee: Node = None; args: List[Arg] = field(default_factory=list)
@dataclass
class Lambda(Node):  params: List[str] = field(default_factory=list); body: Node = None
@dataclass
class Await(Node):   expr: Node = None
@dataclass
class Yield(Node):   expr: Optional[Node] = None
@dataclass
class SuperCall(Node): method: Optional[str]=None; args: List[Arg]=field(default_factory=list)

# Types
@dataclass
class TypeAnn(Node):  name: str = ""; generics: List['TypeAnn'] = field(default_factory=list); nullable: bool = False
@dataclass
class Cast(Node):     expr: Node = None; target: TypeAnn = None

# Declarations
@dataclass
class Param(Node):   name: str=""; type_ann: Optional[TypeAnn]=None; default: Optional[Node]=None; vararg: bool=False
@dataclass
class VarDecl(Node): name: str=""; type_ann: Optional[TypeAnn]=None; init: Optional[Node]=None; is_const: bool=False

@dataclass
class FuncDecl(Node):
    name: str=""; params: List[Param]=field(default_factory=list)
    ret: Optional[TypeAnn]=None; body: Optional['Block']=None
    is_async: bool=False; is_static: bool=False; modifiers: List[str]=field(default_factory=list)

@dataclass
class SubDecl(Node):
    name: str=""; params: List[Param]=field(default_factory=list)
    body: Optional['Block']=None; is_async: bool=False; is_static: bool=False
    modifiers: List[str]=field(default_factory=list)

@dataclass
class ClassDecl(Node):
    name: str=""; generics: List[str]=field(default_factory=list)
    superclass: Optional[str]=None; interfaces: List[str]=field(default_factory=list)
    body: List[Node]=field(default_factory=list); is_abstract: bool=False

@dataclass
class InterfaceDecl(Node):
    name: str=""; extends: List[str]=field(default_factory=list); body: List[Node]=field(default_factory=list)

@dataclass
class ModuleDecl(Node):
    name: str=""; body: List[Node]=field(default_factory=list)

# Statements
@dataclass
class Block(Node):    stmts: List[Node] = field(default_factory=list)
@dataclass
class Assign(Node):   target: Node=None; val: Node=None; op: str="="
@dataclass
class Return(Node):   val: Optional[Node]=None
@dataclass
class Break(Node):    pass
@dataclass
class Continue(Node): pass
@dataclass
class Raise(Node):    expr: Optional[Node]=None
@dataclass
class ExprStmt(Node): expr: Node=None
@dataclass
class Import(Node):   module: str=""; names: List[str]=field(default_factory=list); alias: Optional[str]=None; is_from: bool=False

# Control
@dataclass
class If(Node):
    cond: Node=None; then_b: Block=None
    elifs: List[tuple]=field(default_factory=list); else_b: Optional[Block]=None

@dataclass
class ForRange(Node): var: str=""; start: Node=None; stop: Node=None; step: Optional[Node]=None; body: Block=None; parallel: bool=False
@dataclass
class ForEach(Node):  var: str=""; iterable: Node=None; body: Block=None; parallel: bool=False
@dataclass
class ForIdx(Node):   ivar: str=""; vvar: str=""; iterable: Node=None; body: Block=None
@dataclass
class While(Node):    cond: Node=None; body: Block=None
@dataclass
class MatchCase(Node): pattern: Node=None; guard: Optional[Node]=None; body: Block=None
@dataclass
class Match(Node):    subject: Node=None; cases: List[MatchCase]=field(default_factory=list); otherwise: Optional[Block]=None
@dataclass
class Try(Node):      try_b: Block=None; excepts: List[tuple]=field(default_factory=list); finally_b: Optional[Block]=None

# Scientific / special
@dataclass
class Simulate(Node): domain: str=""; body: Block=None
@dataclass
class ParallelFor(Node): var: str=""; start: Node=None; stop: Node=None; body: Block=None
@dataclass
class AILoad(Node):   path: Node=None
@dataclass
class AIPredict(Node): model: Node=None; data: Node=None
@dataclass
class New(Node):      cls: str=""; args: List[Arg]=field(default_factory=list); generics: List[str]=field(default_factory=list)
@dataclass
class TypeCheck(Node):expr: Node=None; tname: str=""
@dataclass
class NullCoal(Node): expr: Node=None; default: Node=None
@dataclass
class Spread(Node):   expr: Node=None
@dataclass
class ListComp(Node): expr: Node=None; var: str=""; iterable: Node=None; cond: Optional[Node]=None
