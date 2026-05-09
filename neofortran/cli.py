#!/usr/bin/env python3
"""NeoFortran CLI + REPL"""
import sys, os, argparse, traceback

BANNER = r"""
  _   _            _____          _
 | \ | | ___  ___ |  ___|__  _ __| |_ _ __ __ _ _ __
 |  \| |/ _ \/ _ \| |_ / _ \| '__| __| '__/ _` | '_ \
 | |\  |  __/ (_) |  _| (_) | |  | |_| | | (_| | | | |
 |_| \_|\___|\___/|_|  \___/|_|   \__|_|  \__,_|_| |_|

 NeoFortran v1.0.0  |  Scientific · Safe · Modern
 Type 'help' for commands, 'exit' to quit.
"""

HELP = """
Commands:  help · exit · clear · version · ast <code>

Quick Reference:
  int x = 10              typed variable
  let y = 3.14            auto variable
  const N = 100           constant
  print("hello")          output (no newline)
  println("hello")        output + newline

  vector v = [1,2,3]      scientific vector
  matrix m = [[1,2],[3,4]] matrix
  v + v  /  v * 2         vector arithmetic
  m @ m                   matrix multiply

  class Point              class
     float x; float y
     function dist() : float
        return sqrt(x*x + y*y)
     end
  end
  Point p = Point()
  p.x = 3.0; p.y = 4.0

  class Circle extends Point
     float radius
  end

  for i in 1..10           range loop
     println(i)
  end

  parallel for i in 1..100  parallel loop
     compute(i)
  end

  simulate fluid           scientific DSL
     velocity = 10.0
     pressure = 101325.0
  end

  model = ai.load("model.nf")  AI integration
  result = model.predict(data)

  import linalg            stdlib modules:
  from stats import mean    math linalg io os json
  from algo import quickSort random time string stats
                            algo regex test
"""


class REPL:
    def __init__(self):
        from neofortran.interpreter import Interpreter
        self.interp = Interpreter()
        self.buf = []; self.depth = 0

    def run(self):
        print(BANNER)
        while True:
            try:
                prompt = "... " if self.depth > 0 else ">>> "
                line = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye! 👋"); break

            s = line.strip()
            if not self.depth:
                if s in ("exit","quit","bye"): print("Goodbye! 👋"); break
                if s == "help": print(HELP); continue
                if s == "clear": os.system("cls" if os.name=="nt" else "clear"); print(BANNER); continue
                if s == "version": print("NeoFortran v1.0.0"); continue
                if s.startswith("ast "):
                    self._show_ast(s[4:]); continue
                if s == "": continue

            self.buf.append(line)
            openers = {"class","if","for","while","try","simulate","function","subroutine","sub","module","interface","parallel"}
            sl = s.lower().split()[0] if s else ""
            if sl in openers: self.depth += 1
            if s.lower() == "end": self.depth = max(0, self.depth - 1)

            if self.depth == 0:
                code = "\n".join(self.buf); self.buf = []
                self._exec(code)

    def _exec(self, code):
        from neofortran.parser import parse, ParseError
        from neofortran.lexer import LexError
        from neofortran.interpreter import NeoError, NeoNull, RetSig
        try:
            ast = parse(code, "<repl>")
            result = self.interp.execute(ast, self.interp.glob)
            if result is not None and not isinstance(result, NeoNull):
                self._show(result)
        except (LexError, ParseError) as e: print(f"🔴 Syntax: {e}")
        except NeoError as e: print(f"🔴 Runtime: {e}")
        except Exception as e:
            print(f"🔴 Error: {e}")
            if os.environ.get("NF_DEBUG"): traceback.print_exc()

    def _show(self, v):
        from neofortran.interpreter import NeoNull
        if isinstance(v, NeoNull): return
        if isinstance(v, str): print(f'"{v}"')
        elif isinstance(v, bool): print("true" if v else "false")
        else: print(repr(v))

    def _show_ast(self, code):
        from neofortran.parser import parse
        try:
            ast = parse(code, "<ast>")
            self._print_node(ast, 0)
        except Exception as e: print(f"🔴 {e}")

    def _print_node(self, node, depth):
        indent = "  " * depth
        if node is None: return
        cls = node.__class__.__name__
        print(f"{indent}{cls}")
        for k, v in vars(node).items():
            if k in ("line","col"): continue
            if hasattr(v,"__dict__") and hasattr(v,"line"):
                print(f"{indent}  .{k}:"); self._print_node(v, depth+2)
            elif isinstance(v, list) and v and hasattr(v[0],"line" if v else None):
                print(f"{indent}  .{k}: [{len(v)}]")
                for item in v[:4]: self._print_node(item, depth+2)
            else: print(f"{indent}  .{k}: {v!r}")


def main():
    ap = argparse.ArgumentParser(prog="neofortran", description="NeoFortran Language")
    ap.add_argument("--version", "-v", action="store_true")
    ap.add_argument("--debug", "-d", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    rp = sub.add_parser("run");   rp.add_argument("file")
    cp = sub.add_parser("check"); cp.add_argument("file")
    ap2= sub.add_parser("ast");   ap2.add_argument("file")
    args = ap.parse_args()

    if args.debug: os.environ["NF_DEBUG"] = "1"
    if args.version: print("NeoFortran v1.0.0"); return

    if args.cmd == "run":
        from neofortran import run_file
        from neofortran.interpreter import NeoError
        try: run_file(args.file)
        except NeoError as e: print(f"🔴 Runtime: {e}", file=sys.stderr); sys.exit(1)
        except FileNotFoundError: print(f"🔴 File not found: {args.file}", file=sys.stderr); sys.exit(1)

    elif args.cmd == "check":
        from neofortran.parser import parse
        from neofortran.lexer import LexError
        try:
            src = open(args.file).read(); ast = parse(src, args.file)
            print(f"✅ OK — {len(ast.stmts)} statements")
        except Exception as e: print(f"🔴 {e}", file=sys.stderr); sys.exit(1)

    elif args.cmd == "ast":
        REPL()._show_ast(open(args.file).read())

    else:
        REPL().run()


if __name__ == "__main__":
    main()
