"""
NeoFortran v1.0.0 — Modern Scientific Programming Language
Inspired by Fortran. Python-clean, C++-powerful, Fortran-fast.
"""
from .lexer import Lexer, Token, TT
from .parser import parse, Parser
from .interpreter import Interpreter, NeoError

__version__ = "1.0.0"
__author__  = "NeoFortran Team"
__all__ = ["run", "run_file", "parse", "Interpreter"]


def run(source: str, filename="<stdin>", output=None):
    ast = parse(source, filename)
    interp = Interpreter(output=output)
    return interp.execute(ast)


def run_file(path: str, output=None):
    with open(path, encoding="utf-8") as f:
        return run(f.read(), filename=path, output=output)
