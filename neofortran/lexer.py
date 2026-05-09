"""NeoFortran Lexer - Tokenizer"""
import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TT(Enum):
    # Literals
    INT = auto(); FLOAT = auto(); STRING = auto(); BOOL = auto(); NULL = auto()
    COMPLEX = auto()
    # Identifiers
    ID = auto()
    # Keywords
    CLASS = auto(); END = auto(); EXTENDS = auto(); IMPLEMENTS = auto()
    INTERFACE = auto(); ABSTRACT = auto(); FUNCTION = auto(); SUBROUTINE = auto()
    RETURN = auto(); IF = auto(); ELIF = auto(); ELSE = auto(); THEN = auto()
    FOR = auto(); WHILE = auto(); DO = auto(); IN = auto(); BREAK = auto(); CONTINUE = auto()
    LET = auto(); CONST = auto(); NEW = auto(); IMPORT = auto(); FROM = auto()
    TRY = auto(); EXCEPT = auto(); FINALLY = auto(); RAISE = auto()
    MATCH = auto(); CASE = auto(); OTHERWISE = auto()
    PARALLEL = auto(); ASYNC = auto(); AWAIT = auto(); YIELD = auto()
    SIMULATE = auto(); MODEL = auto(); PRINT = auto(); PRINTLN = auto()
    MODULE = auto(); USE = auto(); EXPORT = auto(); PUBLIC = auto(); PRIVATE = auto()
    STATIC = auto(); OVERRIDE = auto(); SUPER = auto(); SELF = auto()
    AND = auto(); OR = auto(); NOT = auto(); IS = auto(); AS = auto(); OF = auto()
    # Types
    T_INT = auto(); T_FLOAT = auto(); T_DOUBLE = auto(); T_STRING = auto()
    T_BOOL = auto(); T_COMPLEX = auto(); T_VOID = auto(); T_AUTO = auto()
    T_VECTOR = auto(); T_MATRIX = auto(); T_ARRAY = auto(); T_ANY = auto()
    # Operators
    ASSIGN = auto()    # =
    PLUS = auto(); MINUS = auto(); STAR = auto(); SLASH = auto()
    PERCENT = auto(); POWER = auto(); FLOORDIV = auto()
    EQ = auto(); NEQ = auto(); LT = auto(); GT = auto(); LTE = auto(); GTE = auto()
    ARROW = auto(); DOTDOT = auto(); DOTDOTDOT = auto()
    PIPE = auto(); CONCAT = auto()
    PLUS_EQ = auto(); MINUS_EQ = auto(); STAR_EQ = auto(); SLASH_EQ = auto()
    DOT = auto(); AT = auto(); QUESTION = auto(); HASH = auto()
    # Brackets
    LPAREN = auto(); RPAREN = auto()
    LBRACKET = auto(); RBRACKET = auto()
    LBRACE = auto(); RBRACE = auto()
    COMMA = auto(); COLON = auto(); SEMICOLON = auto(); NEWLINE = auto()
    EOF = auto()


KEYWORDS = {
    'class': TT.CLASS, 'end': TT.END, 'extends': TT.EXTENDS,
    'implements': TT.IMPLEMENTS, 'interface': TT.INTERFACE, 'abstract': TT.ABSTRACT,
    'function': TT.FUNCTION, 'subroutine': TT.SUBROUTINE, 'sub': TT.SUBROUTINE,
    'return': TT.RETURN, 'if': TT.IF, 'elif': TT.ELIF, 'else': TT.ELSE, 'then': TT.THEN,
    'for': TT.FOR, 'while': TT.WHILE, 'do': TT.DO, 'in': TT.IN,
    'break': TT.BREAK, 'continue': TT.CONTINUE,
    'let': TT.LET, 'const': TT.CONST, 'import': TT.IMPORT, 'from': TT.FROM,
    'try': TT.TRY, 'except': TT.EXCEPT, 'finally': TT.FINALLY, 'raise': TT.RAISE,
    'match': TT.MATCH, 'case': TT.CASE, 'otherwise': TT.OTHERWISE,
    'parallel': TT.PARALLEL, 'async': TT.ASYNC, 'await': TT.AWAIT, 'yield': TT.YIELD,
    'simulate': TT.SIMULATE, 'model': TT.MODEL,
    'print': TT.PRINT, 'println': TT.PRINTLN,
    'module': TT.MODULE, 'use': TT.USE, 'export': TT.EXPORT,
    'public': TT.PUBLIC, 'private': TT.PRIVATE, 'static': TT.STATIC,
    'override': TT.OVERRIDE, 'super': TT.SUPER, 'self': TT.SELF,
    'and': TT.AND, 'or': TT.OR, 'not': TT.NOT, 'is': TT.IS, 'as': TT.AS, 'of': TT.OF,
    'true': TT.BOOL, 'false': TT.BOOL, 'null': TT.NULL,
    # Types
    'int': TT.T_INT, 'integer': TT.T_INT, 'float': TT.T_FLOAT,
    'double': TT.T_DOUBLE, 'string': TT.T_STRING, 'str': TT.T_STRING,
    'bool': TT.T_BOOL, 'boolean': TT.T_BOOL, 'complex': TT.T_COMPLEX,
    'void': TT.T_VOID, 'auto': TT.T_AUTO, 'var': TT.T_AUTO,
    'vector': TT.T_VECTOR, 'matrix': TT.T_MATRIX, 'array': TT.T_ARRAY, 'any': TT.T_ANY,
}

TYPE_TOKENS = {TT.T_INT, TT.T_FLOAT, TT.T_DOUBLE, TT.T_STRING, TT.T_BOOL,
               TT.T_COMPLEX, TT.T_VOID, TT.T_AUTO, TT.T_VECTOR, TT.T_MATRIX,
               TT.T_ARRAY, TT.T_ANY}


@dataclass
class Token:
    type: TT
    value: str
    line: int
    col: int
    def __repr__(self): return f"Token({self.type.name},{self.value!r})"


class LexError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"[Line {line}:{col}] Lex Error: {msg}")


class Lexer:
    def __init__(self, src: str, fname="<stdin>"):
        self.src = src; self.fname = fname
        self.pos = 0; self.line = 1; self.col = 1

    def peek(self, n=0): 
        i = self.pos + n
        return self.src[i] if i < len(self.src) else None

    def adv(self):
        ch = self.src[self.pos]; self.pos += 1
        if ch == '\n': self.line += 1; self.col = 1
        else: self.col += 1
        return ch

    def match(self, c):
        if self.pos < len(self.src) and self.src[self.pos] == c:
            self.adv(); return True
        return False

    def skip_ws(self):
        while self.pos < len(self.src) and self.src[self.pos] in ' \t\r':
            self.adv()

    def skip_line(self):
        while self.pos < len(self.src) and self.src[self.pos] != '\n':
            self.adv()

    def skip_block(self):
        while self.pos < len(self.src):
            if self.src[self.pos] == '*' and self.peek(1) == '/':
                self.adv(); self.adv(); return
            self.adv()

    def read_str(self, q):
        ln, col = self.line, self.col; buf = []
        while self.pos < len(self.src):
            ch = self.adv()
            if ch == '\\':
                esc = self.adv()
                buf.append({'n':'\n','t':'\t','\\':'\\','"':'"',"'":"'"}.get(esc, esc))
            elif ch == q:
                return Token(TT.STRING, ''.join(buf), ln, col)
            else: buf.append(ch)
        raise LexError("Unterminated string", ln, col)

    def read_num(self):
        ln, col = self.line, self.col
        start = self.pos - 1; is_float = False
        while self.pos < len(self.src) and (self.src[self.pos].isdigit() or self.src[self.pos]=='_'):
            self.adv()
        if self.pos < len(self.src) and self.src[self.pos]=='.' and self.peek(1) != '.':
            is_float = True; self.adv()
            while self.pos < len(self.src) and self.src[self.pos].isdigit():
                self.adv()
        if self.pos < len(self.src) and self.src[self.pos] in 'eEdD':
            is_float = True; self.adv()
            if self.pos < len(self.src) and self.src[self.pos] in '+-': self.adv()
            while self.pos < len(self.src) and self.src[self.pos].isdigit(): self.adv()
        # Complex: 3.14j
        if self.pos < len(self.src) and self.src[self.pos] == 'j':
            self.adv()
            return Token(TT.COMPLEX, self.src[start:self.pos].replace('_',''), ln, col)
        raw = self.src[start:self.pos].replace('_','')
        return Token(TT.FLOAT if is_float else TT.INT, raw, ln, col)

    def read_id(self):
        ln, col = self.line, self.col; start = self.pos - 1
        while self.pos < len(self.src) and (self.src[self.pos].isalnum() or self.src[self.pos]=='_'):
            self.adv()
        word = self.src[start:self.pos]
        tt = KEYWORDS.get(word.lower(), TT.ID)
        return Token(tt, word, ln, col)

    def tokenize(self) -> List[Token]:
        toks = []
        while self.pos < len(self.src):
            self.skip_ws()
            if self.pos >= len(self.src): break
            ln, col = self.line, self.col
            ch = self.adv()

            if ch == '\n':
                toks.append(Token(TT.NEWLINE, '\\n', ln, col)); continue
            if ch == '!' and self.peek() == '!':
                self.adv(); self.skip_line(); continue
            if ch == '!' and self.peek() == '-':
                self.adv(); self.skip_line(); continue
            if ch in ('!', ) and self.peek() != '=':
                self.skip_line(); continue
            if ch == '#': self.skip_line(); continue
            if ch == '/' and self.peek() == '/': self.adv(); self.skip_line(); continue
            if ch == '/' and self.peek() == '*': self.adv(); self.skip_block(); continue
            if ch in ('"', "'"): toks.append(self.read_str(ch)); continue
            if ch.isdigit(): self.pos-=1; self.col-=1; self.adv(); toks.append(self.read_num()); continue
            if ch.isalpha() or ch=='_':
                self.pos-=1; self.col-=1; self.adv()
                toks.append(self.read_id()); continue

            # Operators
            if ch == '=':
                if self.match('='): toks.append(Token(TT.EQ,'==',ln,col))
                elif self.match('>'): toks.append(Token(TT.ARROW,'=>',ln,col))
                else: toks.append(Token(TT.ASSIGN,'=',ln,col))
            elif ch == '!':
                if self.match('='): toks.append(Token(TT.NEQ,'!=',ln,col))
            elif ch == '<':
                if self.match('='): toks.append(Token(TT.LTE,'<=',ln,col))
                else: toks.append(Token(TT.LT,'<',ln,col))
            elif ch == '>':
                if self.match('='): toks.append(Token(TT.GTE,'>=',ln,col))
                else: toks.append(Token(TT.GT,'>',ln,col))
            elif ch == '+':
                if self.match('='): toks.append(Token(TT.PLUS_EQ,'+=',ln,col))
                elif self.match('+'): toks.append(Token(TT.CONCAT,'++',ln,col))
                else: toks.append(Token(TT.PLUS,'+',ln,col))
            elif ch == '-':
                if self.match('='): toks.append(Token(TT.MINUS_EQ,'-=',ln,col))
                elif self.match('>'): toks.append(Token(TT.ARROW,'->',ln,col))
                else: toks.append(Token(TT.MINUS,'-',ln,col))
            elif ch == '*':
                if self.match('*'): toks.append(Token(TT.POWER,'**',ln,col))
                elif self.match('='): toks.append(Token(TT.STAR_EQ,'*=',ln,col))
                else: toks.append(Token(TT.STAR,'*',ln,col))
            elif ch == '/':
                if self.match('/'): toks.append(Token(TT.FLOORDIV,'//',ln,col))
                elif self.match('='): toks.append(Token(TT.SLASH_EQ,'/=',ln,col))
                else: toks.append(Token(TT.SLASH,'/',ln,col))
            elif ch == '%': toks.append(Token(TT.PERCENT,'%',ln,col))
            elif ch == '.':
                if self.match('.'):
                    if self.match('.'): toks.append(Token(TT.DOTDOTDOT,'...',ln,col))
                    else: toks.append(Token(TT.DOTDOT,'..',ln,col))
                else: toks.append(Token(TT.DOT,'.',ln,col))
            elif ch == '|':
                if self.match('>'): toks.append(Token(TT.PIPE,'|>',ln,col))
                else: toks.append(Token(TT.ID,'|',ln,col))
            elif ch == '(': toks.append(Token(TT.LPAREN,'(',ln,col))
            elif ch == ')': toks.append(Token(TT.RPAREN,')',ln,col))
            elif ch == '[': toks.append(Token(TT.LBRACKET,'[',ln,col))
            elif ch == ']': toks.append(Token(TT.RBRACKET,']',ln,col))
            elif ch == '{': toks.append(Token(TT.LBRACE,'{',ln,col))
            elif ch == '}': toks.append(Token(TT.RBRACE,'}',ln,col))
            elif ch == ',': toks.append(Token(TT.COMMA,',',ln,col))
            elif ch == ':': toks.append(Token(TT.COLON,':',ln,col))
            elif ch == ';': toks.append(Token(TT.SEMICOLON,';',ln,col))
            elif ch == '@': toks.append(Token(TT.AT,'@',ln,col))
            elif ch == '?': toks.append(Token(TT.QUESTION,'?',ln,col))
            # else: skip unknown

        toks.append(Token(TT.EOF,'',self.line,self.col))
        return self._clean(toks)

    def _clean(self, toks):
        skip_after = {TT.COMMA, TT.PLUS, TT.MINUS, TT.STAR, TT.SLASH,
                      TT.ASSIGN, TT.COLON, TT.NEWLINE, TT.LBRACKET, TT.LPAREN,
                      TT.ARROW, TT.PIPE}
        result = []; prev = None
        for t in toks:
            if t.type == TT.NEWLINE:
                if prev is None or prev.type in skip_after: continue
            result.append(t); prev = t if t.type != TT.NEWLINE else prev
        return result
