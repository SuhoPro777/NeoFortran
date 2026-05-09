"""NeoFortran Parser — Recursive Descent"""
from typing import List, Optional
from .lexer import Token, TT, TYPE_TOKENS, Lexer
from .ast_nodes import *


class ParseError(Exception):
    def __init__(self, msg, tok):
        super().__init__(f"[Line {tok.line}:{tok.col}] Parse Error: {msg}")
        self.tok = tok


class Parser:
    def __init__(self, tokens: List[Token]):
        self.toks = [t for t in tokens if t.type != TT.NEWLINE]
        self.pos = 0

    def peek(self, n=0):
        i = self.pos+n
        return self.toks[i] if i < len(self.toks) else self.toks[-1]

    def cur(self): return self.peek(0)
    def adv(self):
        t = self.toks[self.pos]
        if self.pos < len(self.toks)-1: self.pos += 1
        return t

    def check(self, *types): return self.cur().type in types
    def match(self, *types):
        if self.cur().type in types: return self.adv()
        return None

    def expect(self, tt, msg=None):
        if self.cur().type == tt: return self.adv()
        raise ParseError(msg or f"Expected {tt.name}, got {self.cur().value!r}", self.cur())

    def expect_id(self, msg=""):
        t = self.cur()
        if t.type in (TT.ID,) or t.type in TYPE_TOKENS or t.type in {
            TT.PRINT, TT.PRINTLN, TT.MODEL, TT.SIMULATE,
        }:
            self.adv(); return t.value
        raise ParseError(msg or f"Expected identifier, got {t.value!r}", t)

    def skip(self): 
        while self.match(TT.SEMICOLON, TT.NEWLINE): pass

    def is_type(self):
        return self.cur().type in TYPE_TOKENS

    # ── Top level ────────────────────────────────────────────────────────────

    def parse(self) -> Block:
        stmts = []; self.skip()
        while not self.check(TT.EOF):
            s = self.parse_top(); stmts.append(s) if s else None; self.skip()
        return Block(stmts=stmts)

    def parse_top(self) -> Node:
        if self.check(TT.MODULE):   return self.parse_module()
        if self.check(TT.CLASS):    return self.parse_class()
        if self.check(TT.ABSTRACT): return self.parse_class()
        if self.check(TT.INTERFACE):return self.parse_interface()
        if self.check(TT.FUNCTION): return self.parse_func()
        if self.check(TT.SUBROUTINE):return self.parse_sub()
        if self.check(TT.ASYNC):    return self.parse_async_fn()
        if self.check(TT.IMPORT) or self.check(TT.FROM): return self.parse_import()
        if self.check(TT.PARALLEL): return self.parse_parallel()
        if self.check(TT.SIMULATE): return self.parse_simulate()
        return self.parse_stmt()

    # ── Module ───────────────────────────────────────────────────────────────

    def parse_module(self) -> ModuleDecl:
        tok = self.expect(TT.MODULE)
        name = self.expect_id("Expected module name")
        self.skip()
        body = self.parse_body()
        return ModuleDecl(name=name, body=body, line=tok.line, col=tok.col)

    # ── Class ────────────────────────────────────────────────────────────────

    def parse_class(self) -> ClassDecl:
        is_abstract = bool(self.match(TT.ABSTRACT))
        tok = self.expect(TT.CLASS)
        name = self.expect_id("Expected class name")
        generics = self.parse_generics_decl()
        super_cls = None; interfaces = []
        if self.match(TT.EXTENDS): super_cls = self.expect_id()
        if self.match(TT.IMPLEMENTS):
            interfaces.append(self.expect_id())
            while self.match(TT.COMMA): interfaces.append(self.expect_id())
        self.skip()
        body = self.parse_class_body()
        return ClassDecl(name=name, generics=generics, superclass=super_cls,
                         interfaces=interfaces, body=body, is_abstract=is_abstract,
                         line=tok.line, col=tok.col)

    def parse_generics_decl(self) -> List[str]:
        if not self.match(TT.LT): return []
        gens = [self.expect_id()]
        while self.match(TT.COMMA): gens.append(self.expect_id())
        self.expect(TT.GT if hasattr(TT,'GT') else TT.GT)
        return gens

    def parse_class_body(self) -> List[Node]:
        body = []; self.skip()
        while not self.check(TT.END, TT.EOF):
            mods = self.parse_mods()
            if self.check(TT.FUNCTION):
                n = self.parse_func(); n.modifiers = mods; body.append(n)
            elif self.check(TT.SUBROUTINE):
                n = self.parse_sub(); n.modifiers = mods; body.append(n)
            elif self.check(TT.ASYNC):
                n = self.parse_async_fn(); n.modifiers = mods; body.append(n)
            elif self.is_type() and self.peek(1).type in (TT.ID,):
                body.append(self.parse_field())
            else:
                body.append(self.parse_stmt())
            self.skip()
        self.expect(TT.END)
        return body

    def parse_field(self) -> VarDecl:
        tok = self.cur()
        ta = self.parse_type_ann()
        name = self.expect_id()
        init = None
        if self.match(TT.ASSIGN): init = self.parse_expr()
        self.match(TT.SEMICOLON)
        return VarDecl(name=name, type_ann=ta, init=init, line=tok.line, col=tok.col)

    def parse_mods(self) -> List[str]:
        mods = []
        mod_tt = {TT.PUBLIC, TT.PRIVATE, TT.STATIC, TT.OVERRIDE, TT.ABSTRACT, TT.ASYNC}
        while self.cur().type in mod_tt: mods.append(self.adv().value)
        return mods

    # ── Interface ────────────────────────────────────────────────────────────

    def parse_interface(self) -> InterfaceDecl:
        tok = self.expect(TT.INTERFACE)
        name = self.expect_id()
        extends = []
        if self.match(TT.EXTENDS):
            extends.append(self.expect_id())
            while self.match(TT.COMMA): extends.append(self.expect_id())
        self.skip()
        body = []
        while not self.check(TT.END, TT.EOF):
            if self.check(TT.FUNCTION):
                body.append(self.parse_func_sig()); self.skip()
            elif self.check(TT.SUBROUTINE):
                body.append(self.parse_sub_sig()); self.skip()
            else: self.adv()
        self.expect(TT.END)
        return InterfaceDecl(name=name, extends=extends, body=body, line=tok.line, col=tok.col)

    def parse_func_sig(self) -> FuncDecl:
        tok = self.expect(TT.FUNCTION)
        name = self.expect_id(); params = self.parse_params()
        ret = None
        if self.match(TT.COLON): ret = self.parse_type_ann()
        return FuncDecl(name=name, params=params, ret=ret, body=None, line=tok.line, col=tok.col)

    def parse_sub_sig(self) -> SubDecl:
        tok = self.expect(TT.SUBROUTINE)
        name = self.expect_id(); params = self.parse_params()
        return SubDecl(name=name, params=params, body=None, line=tok.line, col=tok.col)

    # ── Functions ─────────────────────────────────────────────────────────────

    def parse_async_fn(self) -> FuncDecl:
        self.expect(TT.ASYNC)
        if self.check(TT.FUNCTION): n = self.parse_func(); n.is_async = True; return n
        n = self.parse_sub(); n.is_async = True; return n

    def parse_func(self) -> FuncDecl:
        tok = self.expect(TT.FUNCTION)
        name = self.expect_id(); params = self.parse_params()
        ret = None
        if self.match(TT.COLON): ret = self.parse_type_ann()
        self.skip()
        body = self.parse_body()
        return FuncDecl(name=name, params=params, ret=ret, body=body, line=tok.line, col=tok.col)

    def parse_sub(self) -> SubDecl:
        tok = self.expect(TT.SUBROUTINE)
        name = self.expect_id(); params = self.parse_params()
        self.skip(); body = self.parse_body()
        return SubDecl(name=name, params=params, body=body, line=tok.line, col=tok.col)

    def parse_params(self) -> List[Param]:
        if not self.match(TT.LPAREN): return []
        params = []
        if not self.check(TT.RPAREN):
            params.append(self.parse_param())
            while self.match(TT.COMMA):
                if self.check(TT.RPAREN): break
                params.append(self.parse_param())
        self.expect(TT.RPAREN); return params

    def parse_param(self) -> Param:
        tok = self.cur(); vararg = bool(self.match(TT.DOTDOTDOT))
        ta = None
        if self.is_type() and self.peek(1).type == TT.ID:
            ta = self.parse_type_ann()
        name = self.expect_id()
        default = None
        if self.match(TT.ASSIGN): default = self.parse_expr()
        return Param(name=name, type_ann=ta, default=default, vararg=vararg, line=tok.line, col=tok.col)

    def parse_body(self) -> Block:
        stmts = []; self.skip()
        while not self.check(TT.END, TT.EOF, TT.ELSE, TT.ELIF, TT.EXCEPT, TT.FINALLY, TT.CASE, TT.OTHERWISE):
            stmts.append(self.parse_stmt()); self.skip()
        self.match(TT.END)
        return Block(stmts=stmts)

    def parse_inner_body(self) -> Block:
        stmts = []; self.skip()
        while not self.check(TT.END, TT.EOF, TT.ELSE, TT.ELIF, TT.EXCEPT, TT.FINALLY, TT.CASE, TT.OTHERWISE):
            stmts.append(self.parse_stmt()); self.skip()
        return Block(stmts=stmts)

    # ── Type Annotation ───────────────────────────────────────────────────────

    def parse_type_ann(self) -> TypeAnn:
        tok = self.cur(); name = self.adv().value
        gens = []
        if self.match(TT.LT):
            gens.append(self.parse_type_ann())
            while self.match(TT.COMMA): gens.append(self.parse_type_ann())
            self.adv()  # >
        nullable = bool(self.match(TT.QUESTION))
        return TypeAnn(name=name, generics=gens, nullable=nullable, line=tok.line, col=tok.col)

    # ── Statements ────────────────────────────────────────────────────────────

    def parse_stmt(self) -> Node:
        tok = self.cur()
        if self.check(TT.IF):       return self.parse_if()
        if self.check(TT.FOR):      return self.parse_for()
        if self.check(TT.PARALLEL): return self.parse_parallel()
        if self.check(TT.WHILE):    return self.parse_while()
        if self.check(TT.MATCH):    return self.parse_match()
        if self.check(TT.TRY):      return self.parse_try()
        if self.check(TT.RETURN):   return self.parse_return()
        if self.check(TT.RAISE):
            self.adv()
            e = self.parse_expr() if not self.check(TT.NEWLINE, TT.SEMICOLON, TT.EOF) else None
            return Raise(expr=e, line=tok.line, col=tok.col)
        if self.check(TT.BREAK):    self.adv(); return Break(line=tok.line)
        if self.check(TT.CONTINUE): self.adv(); return Continue(line=tok.line)
        if self.check(TT.IMPORT) or self.check(TT.FROM): return self.parse_import()
        if self.check(TT.FUNCTION): return self.parse_func()
        if self.check(TT.SUBROUTINE): return self.parse_sub()
        if self.check(TT.CLASS):    return self.parse_class()
        if self.check(TT.SIMULATE): return self.parse_simulate()
        if self.check(TT.LET) or self.check(TT.CONST): return self.parse_let()
        if self.is_type() and self.peek(1).type == TT.ID: return self.parse_typed_decl()
        return self.parse_expr_stmt()

    def parse_let(self) -> VarDecl:
        tok = self.cur(); is_const = self.cur().type == TT.CONST; self.adv()
        name = self.expect_id()
        ta = None
        if self.match(TT.COLON): ta = self.parse_type_ann()
        init = None
        if self.match(TT.ASSIGN): init = self.parse_expr()
        return VarDecl(name=name, type_ann=ta, init=init, is_const=is_const, line=tok.line, col=tok.col)

    def parse_typed_decl(self) -> VarDecl:
        tok = self.cur(); ta = self.parse_type_ann()
        name = self.expect_id()
        init = None
        if self.match(TT.ASSIGN): init = self.parse_expr()
        return VarDecl(name=name, type_ann=ta, init=init, line=tok.line, col=tok.col)

    def parse_expr_stmt(self) -> Node:
        tok = self.cur(); expr = self.parse_expr()
        assign_ops = {TT.ASSIGN:'=', TT.PLUS_EQ:'+=', TT.MINUS_EQ:'-=',
                      TT.STAR_EQ:'*=', TT.SLASH_EQ:'/='}
        if self.cur().type in assign_ops:
            op = assign_ops[self.adv().type]
            val = self.parse_expr()
            return Assign(target=expr, val=val, op=op, line=tok.line, col=tok.col)
        return ExprStmt(expr=expr, line=tok.line, col=tok.col)

    # ── Control Flow ──────────────────────────────────────────────────────────

    def parse_if(self) -> If:
        tok = self.expect(TT.IF); cond = self.parse_expr()
        self.match(TT.THEN); self.skip()
        then_b = self.parse_inner_body()
        elifs = []; else_b = None
        while self.check(TT.ELIF):
            self.adv(); ec = self.parse_expr(); self.match(TT.THEN); self.skip()
            eb = self.parse_inner_body(); elifs.append((ec, eb))
        if self.match(TT.ELSE): self.skip(); else_b = self.parse_inner_body()
        self.expect(TT.END)
        return If(cond=cond, then_b=then_b, elifs=elifs, else_b=else_b, line=tok.line, col=tok.col)

    def parse_for(self) -> Node:
        tok = self.expect(TT.FOR)
        var1 = self.expect_id()
        if self.match(TT.COMMA):
            var2 = self.expect_id(); self.expect(TT.IN)
            it = self.parse_expr(); self.skip()
            body = self.parse_inner_body(); self.expect(TT.END)
            return ForIdx(ivar=var1, vvar=var2, iterable=it, body=body, line=tok.line, col=tok.col)
        self.expect(TT.IN); start = self.parse_expr()
        if self.match(TT.DOTDOT):
            stop = self.parse_expr(); step = None
            if self.match(TT.COLON): step = self.parse_expr()
            self.skip(); body = self.parse_inner_body(); self.expect(TT.END)
            return ForRange(var=var1, start=start, stop=stop, step=step, body=body, line=tok.line, col=tok.col)
        self.skip(); body = self.parse_inner_body(); self.expect(TT.END)
        return ForEach(var=var1, iterable=start, body=body, line=tok.line, col=tok.col)

    def parse_parallel(self) -> Node:
        tok = self.expect(TT.PARALLEL)
        self.expect(TT.FOR); var = self.expect_id()
        self.expect(TT.IN); start = self.parse_expr(); self.expect(TT.DOTDOT)
        stop = self.parse_expr(); self.skip()
        body = self.parse_inner_body(); self.expect(TT.END)
        return ParallelFor(var=var, start=start, stop=stop, body=body, line=tok.line, col=tok.col)

    def parse_while(self) -> While:
        tok = self.expect(TT.WHILE); cond = self.parse_expr(); self.skip()
        body = self.parse_inner_body(); self.expect(TT.END)
        return While(cond=cond, body=body, line=tok.line, col=tok.col)

    def parse_match(self) -> Match:
        tok = self.expect(TT.MATCH); subj = self.parse_expr(); self.skip()
        cases = []; otherwise = None
        while not self.check(TT.END, TT.EOF):
            if self.check(TT.CASE):
                self.adv(); pat = self.parse_expr()
                guard = None
                if self.cur().value == 'if': self.adv(); guard = self.parse_expr()
                self.skip(); body = self.parse_inner_body()
                cases.append(MatchCase(pattern=pat, guard=guard, body=body))
            elif self.check(TT.OTHERWISE):
                self.adv(); self.skip(); otherwise = self.parse_inner_body()
            else: break
            self.skip()
        self.expect(TT.END)
        return Match(subject=subj, cases=cases, otherwise=otherwise, line=tok.line, col=tok.col)

    def parse_try(self) -> Try:
        tok = self.expect(TT.TRY); self.skip()
        try_b = self.parse_inner_body(); excepts = []; fin = None
        while self.check(TT.EXCEPT):
            self.adv(); et = None; ev = None
            if self.check(TT.ID): et = self.adv().value
            if self.check(TT.ID): ev = self.adv().value
            self.skip(); eb = self.parse_inner_body()
            excepts.append((et, ev, eb))
        if self.match(TT.FINALLY): self.skip(); fin = self.parse_inner_body()
        self.expect(TT.END)
        return Try(try_b=try_b, excepts=excepts, finally_b=fin, line=tok.line, col=tok.col)

    def parse_return(self) -> Return:
        tok = self.expect(TT.RETURN)
        val = None
        if not self.check(TT.NEWLINE, TT.SEMICOLON, TT.EOF, TT.END):
            val = self.parse_expr()
        return Return(val=val, line=tok.line, col=tok.col)

    def parse_simulate(self) -> Simulate:
        tok = self.expect(TT.SIMULATE)
        domain = self.expect_id("Expected simulation domain"); self.skip()
        body = self.parse_inner_body(); self.expect(TT.END)
        return Simulate(domain=domain, body=body, line=tok.line, col=tok.col)

    def parse_import(self) -> Import:
        is_from = False
        if self.check(TT.FROM):
            self.adv(); module = self.expect_id()
            self.expect(TT.IMPORT); is_from = True
        else:
            self.expect(TT.IMPORT); module = self.expect_id()
        names = []; alias = None
        if is_from:
            names.append(self.expect_id())
            while self.match(TT.COMMA): names.append(self.expect_id())
        elif self.check(TT.AS):
            self.adv(); alias = self.expect_id()
        return Import(module=module, names=names, alias=alias, is_from=is_from)

    # ── Expressions ───────────────────────────────────────────────────────────

    def parse_expr(self) -> Node: return self.parse_ternary()

    def parse_ternary(self) -> Node:
        e = self.parse_null_coal()
        if self.match(TT.QUESTION):
            then = self.parse_expr(); self.expect(TT.COLON); else_e = self.parse_expr()
            return Ternary(cond=e, then_e=then, else_e=else_e, line=e.line, col=e.col)
        return e

    def parse_null_coal(self) -> Node:
        e = self.parse_or()
        while self.cur().value == '??':
            self.adv(); r = self.parse_or()
            e = NullCoal(expr=e, default=r, line=e.line, col=e.col)
        return e

    def parse_or(self) -> Node:
        l = self.parse_and()
        while self.check(TT.OR): self.adv(); r = self.parse_and(); l = BinOp(left=l,op='or',right=r,line=l.line,col=l.col)
        return l

    def parse_and(self) -> Node:
        l = self.parse_not()
        while self.check(TT.AND): self.adv(); r = self.parse_not(); l = BinOp(left=l,op='and',right=r,line=l.line,col=l.col)
        return l

    def parse_not(self) -> Node:
        if self.check(TT.NOT): tok=self.adv(); return UnOp(op='not',operand=self.parse_not(),line=tok.line,col=tok.col)
        return self.parse_cmp()

    def parse_cmp(self) -> Node:
        l = self.parse_pipe()
        cmp = {TT.EQ:'==',TT.NEQ:'!=',TT.LT:'<',TT.GT:'>',TT.LTE:'<=',TT.GTE:'>='}
        while self.cur().type in cmp:
            op = cmp[self.adv().type]; r = self.parse_pipe()
            l = BinOp(left=l, op=op, right=r, line=l.line, col=l.col)
        if self.check(TT.IS): self.adv(); tn = self.expect_id(); l = TypeCheck(expr=l, tname=tn, line=l.line, col=l.col)
        return l

    def parse_pipe(self) -> Node:
        e = self.parse_add()
        while self.check(TT.PIPE): self.adv(); fn = self.parse_add(); e = Pipe(val=e, fn=fn, line=e.line, col=e.col)
        return e

    def parse_add(self) -> Node:
        l = self.parse_mul()
        while self.check(TT.PLUS, TT.MINUS, TT.CONCAT):
            op = self.adv().value; r = self.parse_mul()
            l = BinOp(left=l, op=op, right=r, line=l.line, col=l.col)
        return l

    def parse_mul(self) -> Node:
        l = self.parse_pow()
        while self.check(TT.STAR, TT.SLASH, TT.PERCENT, TT.FLOORDIV, TT.AT):
            op = self.adv().value; r = self.parse_pow()
            if op == '@': l = MatMul(left=l, right=r, line=l.line, col=l.col)
            else: l = BinOp(left=l, op=op, right=r, line=l.line, col=l.col)
        return l

    def parse_pow(self) -> Node:
        b = self.parse_unary()
        if self.check(TT.POWER): self.adv(); e = self.parse_pow(); return BinOp(left=b,op='**',right=e,line=b.line,col=b.col)
        return b

    def parse_unary(self) -> Node:
        tok = self.cur()
        if self.check(TT.MINUS): self.adv(); return UnOp(op='-',operand=self.parse_unary(),line=tok.line,col=tok.col)
        if self.check(TT.NOT):   self.adv(); return UnOp(op='not',operand=self.parse_unary(),line=tok.line,col=tok.col)
        return self.parse_postfix()

    def parse_postfix(self) -> Node:
        e = self.parse_primary()
        while True:
            tok = self.cur()
            if self.check(TT.DOT):
                self.adv()
                if self.check(TT.QUESTION): self.adv(); m = self.expect_id(); e = SafeMember(obj=e,attr=m,line=tok.line,col=tok.col)
                else: m = self.expect_id(); e = Member(obj=e,attr=m,line=tok.line,col=tok.col)
            elif self.check(TT.LPAREN):
                args = self.parse_args(); e = Call(callee=e,args=args,line=tok.line,col=tok.col)
            elif self.check(TT.LBRACKET):
                self.adv()
                if self.check(TT.COLON):
                    self.adv()
                    stop = self.parse_expr() if not self.check(TT.RBRACKET) else None
                    self.expect(TT.RBRACKET); e = Slice(obj=e,stop=stop,line=tok.line,col=tok.col)
                else:
                    idx = self.parse_expr()
                    if self.match(TT.COLON):
                        stop = self.parse_expr() if not self.check(TT.RBRACKET) else None
                        self.expect(TT.RBRACKET); e = Slice(obj=e,start=idx,stop=stop,line=tok.line,col=tok.col)
                    else: self.expect(TT.RBRACKET); e = Index(obj=e,idx=idx,line=tok.line,col=tok.col)
            elif self.check(TT.AS):
                self.adv(); ta = self.parse_type_ann(); e = Cast(expr=e,target=ta,line=tok.line,col=tok.col)
            else: break
        return e

    def parse_args(self) -> List[Arg]:
        self.expect(TT.LPAREN); args = []
        if not self.check(TT.RPAREN):
            args.append(self.parse_arg())
            while self.match(TT.COMMA):
                if self.check(TT.RPAREN): break
                args.append(self.parse_arg())
        self.expect(TT.RPAREN); return args

    def parse_arg(self) -> Arg:
        tok = self.cur()
        if self.cur().type == TT.ID and self.peek(1).type == TT.ASSIGN:
            kw = self.adv().value; self.adv(); v = self.parse_expr()
            return Arg(val=v, kw=kw, line=tok.line, col=tok.col)
        if self.match(TT.DOTDOTDOT):
            v = self.parse_expr(); return Arg(val=Spread(expr=v,line=tok.line,col=tok.col),line=tok.line,col=tok.col)
        return Arg(val=self.parse_expr(), line=tok.line, col=tok.col)

    # ── Primary ───────────────────────────────────────────────────────────────

    def parse_primary(self) -> Node:
        tok = self.cur()
        if self.check(TT.INT):     self.adv(); return IntLit(value=int(tok.value),line=tok.line,col=tok.col)
        if self.check(TT.FLOAT):   self.adv(); return FloatLit(value=float(tok.value),line=tok.line,col=tok.col)
        if self.check(TT.COMPLEX): self.adv(); return ComplexLit(value=complex(tok.value),line=tok.line,col=tok.col)
        if self.check(TT.STRING):  self.adv(); return StrLit(value=tok.value,line=tok.line,col=tok.col)
        if self.check(TT.BOOL):    self.adv(); return BoolLit(value=tok.value.lower()=='true',line=tok.line,col=tok.col)
        if self.check(TT.NULL):    self.adv(); return NullLit(line=tok.line,col=tok.col)

        if self.check(TT.LPAREN):
            self.adv()
            e = self.parse_expr()
            self.expect(TT.RPAREN)
            return e

        if self.check(TT.LBRACKET): return self.parse_vector_or_matrix()
        if self.check(TT.LBRACE):   return self.parse_map_lit()

        # Lambda: x -> expr
        if self.cur().type == TT.ID and self.peek(1).type == TT.ARROW:
            p = self.adv().value; self.adv()
            return Lambda(params=[p], body=self.parse_expr(), line=tok.line, col=tok.col)

        if self.check(TT.AWAIT):
            self.adv(); return Await(expr=self.parse_expr(), line=tok.line, col=tok.col)
        if self.check(TT.YIELD):
            self.adv()
            e = self.parse_expr() if not self.check(TT.NEWLINE,TT.SEMICOLON,TT.EOF,TT.END) else None
            return Yield(expr=e, line=tok.line, col=tok.col)
        if self.check(TT.SUPER):
            self.adv(); m = None; args = []
            if self.match(TT.DOT): m = self.expect_id()
            if self.check(TT.LPAREN): args = self.parse_args()
            return SuperCall(method=m, args=args, line=tok.line, col=tok.col)
        if self.check(TT.SELF):
            self.adv(); return Ident(name='self', line=tok.line, col=tok.col)

        # Identifier or New
        if self.cur().type in (TT.ID,) or self.cur().type in TYPE_TOKENS or \
           self.cur().type in {TT.PRINT, TT.PRINTLN, TT.MODEL, TT.SIMULATE}:
            name = self.adv().value
            # Generics instantiation: Box<int>(val)
            if self.cur().value == '<' and self.peek(1).type in TYPE_TOKENS|{TT.ID}:
                try:
                    saved = self.pos
                    self.adv()
                    gens = [self.expect_id()]
                    while self.match(TT.COMMA): gens.append(self.expect_id())
                    self.adv()  # >
                    if self.check(TT.LPAREN):
                        args = self.parse_args()
                        return New(cls=name, args=args, generics=gens, line=tok.line, col=tok.col)
                    self.pos = saved
                except: self.pos = saved
            return Ident(name=name, line=tok.line, col=tok.col)

        raise ParseError(f"Unexpected token: {tok.value!r}", tok)

    def parse_vector_or_matrix(self) -> Node:
        tok = self.expect(TT.LBRACKET)
        if self.check(TT.RBRACKET): self.adv(); return VectorLit(elements=[],line=tok.line,col=tok.col)
        first = self.parse_expr()
        # Matrix: [[...], ...]
        if isinstance(first, VectorLit) or self.check(TT.COMMA) and isinstance(first, VectorLit):
            rows = [first.elements if isinstance(first, VectorLit) else [first]]
            while self.match(TT.COMMA):
                if self.check(TT.RBRACKET): break
                row = self.parse_expr()
                rows.append(row.elements if isinstance(row, VectorLit) else [row])
            self.expect(TT.RBRACKET)
            if len(rows) > 1 or (rows and isinstance(rows[0], list)):
                return MatrixLit(rows=rows, line=tok.line, col=tok.col)
        # Check for comprehension
        if self.cur().type == TT.FOR:
            self.adv(); var = self.expect_id(); self.expect(TT.IN)
            it = self.parse_expr(); cond = None
            if self.cur().value == 'if': self.adv(); cond = self.parse_expr()
            self.expect(TT.RBRACKET)
            return ListComp(expr=first, var=var, iterable=it, cond=cond, line=tok.line, col=tok.col)
        elems = [first]
        while self.match(TT.COMMA):
            if self.check(TT.RBRACKET): break
            elems.append(self.parse_expr())
        self.expect(TT.RBRACKET)
        return VectorLit(elements=elems, line=tok.line, col=tok.col)

    def parse_map_lit(self) -> MapLit:
        tok = self.expect(TT.LBRACE); pairs = []
        if not self.check(TT.RBRACE):
            k = self.parse_expr(); self.expect(TT.COLON); v = self.parse_expr()
            pairs.append((k,v))
            while self.match(TT.COMMA):
                if self.check(TT.RBRACE): break
                k = self.parse_expr(); self.expect(TT.COLON); v = self.parse_expr()
                pairs.append((k,v))
        self.expect(TT.RBRACE)
        return MapLit(pairs=pairs, line=tok.line, col=tok.col)


def parse(src: str, fname="<stdin>") -> Block:
    toks = Lexer(src, fname).tokenize()
    return Parser(toks).parse()
