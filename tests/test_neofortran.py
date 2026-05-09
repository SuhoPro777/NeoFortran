"""NeoFortran Test Suite — 35 tests"""
import sys, io
sys.path.insert(0, '/home/claude/neofortran')
from neofortran import run

def capture(src):
    buf = io.StringIO()
    run(src, output=buf)
    return buf.getvalue().strip()

ok = fail = 0

def test(name, src, expected):
    global ok, fail
    try:
        result = capture(src)
        if result == expected.strip():
            print(f"  ✅ {name}"); ok += 1
        else:
            print(f"  ❌ {name}")
            print(f"     exp: {expected!r}")
            print(f"     got: {result!r}")
            fail += 1
    except Exception as e:
        print(f"  💥 {name}: {e}"); fail += 1

print("NeoFortran Test Suite\n" + "="*40)

test("hello",         'println("Hello!")',                  "Hello!")
test("int arith",     'println(str(3 + 4 * 2))',            "11")
test("float",         'println(str(1.5 + 0.5))',            "2")
test("power",         'println(str(2 ** 10))',              "1024")
test("string +",      'println("foo" + "bar")',             "foobar")
test("let var",       'let x = 42\nprintln(str(x))',        "42")
test("typed var",     'int n = 7\nprintln(str(n))',         "7")
test("const",         'const C = 99\nprintln(str(C))',      "99")
test("bool true",     'println(str(true))',                 "true")
test("bool false",    'println(str(false))',                "false")
test("if true",       'if true\nprintln("yes")\nend',       "yes")
test("if else",       'if false\nprintln("no")\nelse\nprintln("yes")\nend', "yes")
test("elif",          'let x=2\nif x==1\nprintln("a")\nelif x==2\nprintln("b")\nelse\nprintln("c")\nend', "b")
test("for range",     'let s=0\nfor i in 1..5\ns = s + i\nend\nprintln(str(s))', "15")
test("for each",      'let r=""\nfor c in ["a","b","c"]\nr = r + c\nend\nprintln(r)', "abc")
test("while",         'let i=5\nlet f=1\nwhile i > 0\nf = f * i\ni = i - 1\nend\nprintln(str(f))', "120")
test("function",      'function sq(x):int\nreturn x*x\nend\nprintln(str(sq(9)))', "81")
test("subroutine",    'subroutine greet(n)\nprintln("Hi " + n)\nend\ngreet("Ali")', "Hi Ali")
test("lambda",        'let f = x -> x + 1\nprintln(str(f(41)))', "42")
test("recursion",     'function fib(n):int\nif n <= 1\nreturn n\nend\nreturn fib(n-1)+fib(n-2)\nend\nprintln(str(fib(10)))', "55")
test("vector lit",    'vector v = [1.0, 2.0, 3.0]\nprintln(str(v.length))', "3")
test("vector add",    'vector a = [1.0, 2.0]\nvector b = [3.0, 4.0]\nlet c = a + b\nprintln(str(c[0]))', "4")
test("vector norm",   'import linalg\nvector v = [3.0, 4.0]\nprintln(str(linalg.norm(v)))', "5")
test("matrix lit",    'matrix m = [[1.0,2.0],[3.0,4.0]]\nprintln(str(m.rows))', "2")
test("pipe op",       'let f = x -> x * 2\nlet r = 5.0 |> f\nprintln(str(r))', "10")
test("list comp",     'let sq = [x * x for x in [1.0, 2.0, 3.0]]\nprintln(str(sq[0]))', "1")
test("class",         'class Dog\nstring name\nfunction init(n)\nself.name=n\nend\nfunction speak():string\nreturn "Woof " + self.name\nend\nend\nDog d = Dog("Rex")\nprintln(d.speak())', "Woof Rex")
test("inheritance",   'class A\nfunction greet():string\nreturn "Hello from A"\nend\nend\nclass B extends A\nfunction greet():string\nreturn "Hello from B"\nend\nend\nB b = B()\nprintln(b.greet())', "Hello from B")
test("match",         'match 2\ncase 1\nprintln("one")\ncase 2\nprintln("two")\notherwise\nprintln("other")\nend', "two")
test("try except",    'try\nraise "oops"\nexcept Error e\nprintln("Caught: " + str(e))\nend', "Caught: oops")
test("type check",    'println(str(42 is int))', "true")
test("ternary",       'let x = 10\nlet r = x > 5 ? "big" : "small"\nprintln(r)', "big")
test("stdlib math",   'import math\nprintln(str(math.sqrt(25.0)))', "5")
test("stdlib json",   'from json import stringify\nlet d = {"k": "v"}\nprintln(stringify(d))', '{"k": "v"}')
test("string method", 'let s = "hello"\nprintln(s.upper())', "HELLO")

print(f"\n{'='*40}")
print(f"Results: {ok}/{ok+fail} passed {'✅' if fail==0 else '❌'}")
if fail == 0: print("All tests passed! 🎉")
