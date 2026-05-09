# NeoFortran 🔬
### *Modern Scientific Programming Language — Fortran, Reborn*

```
  _   _            _____          _
 | \ | | ___  ___ |  ___|__  _ __| |_ _ __ __ _ _ __
 |  \| |/ _ \/ _ \| |_ / _ \| '__| __| '__/ _` | '_ \
 | |\  |  __/ (_) |  _| (_) | |  | |_| | | (_| | | | |
 |_| \_|\___|\___/_|_|  \___/|_|   \__|_|  \__,_|_| |_|
```

> **Python-clean · C++-powerful · Fortran-fast**

NeoFortran is a modern evolution of Fortran — clean free-form syntax, first-class OOP with inheritance, built-in scientific vectors/matrices, parallel computing, AI integration, simulation DSL, and 12 standard library modules.

---

## ✨ What's New vs Classic Fortran

| Classic Fortran | NeoFortran |
|---|---|
| Fixed-format columns | Free-form, indent-based |
| `.GT.` `.LT.` operators | `>` `<` `>=` `<=` |
| `TYPE` + `MODULE` confusion | Unified `class` |
| `GOTO` statements | Structured control flow |
| `COMMON`, `EQUIVALENCE` | Lexical scoping |
| Manual memory (`NEW`/`DELETE`) | Automatic GC |
| No OOP | Full OOP + inheritance + polymorphism |
| No generics | `class Box<T>` |
| No lambdas | `x -> x * x` |
| `END FUNCTION`, `END SUBROUTINE` | Just `end` |
| No AI | `model = ai.load("model.nf")` |
| No simulation DSL | `simulate fluid ... end` |

---

## 📦 Installation

```bash
git clone https://github.com/neofortran/neofortran
cd neofortran
pip install -e .
```

---

## 🏃 Quick Start

```bash
neofortran                    # REPL
neofortran run program.nf     # Run file
neofortran check program.nf   # Syntax check
neofortran ast program.nf     # Print AST
```

---

## 📖 Language Reference

### Hello World
```fortran
println("Hello from NeoFortran!")
```

### Variables
```fortran
// Typed
int    age    = 25
float  pi     = 3.14159
string name   = "NeoFortran"
bool   active = true
double mass   = 9.109e-31

// Auto type
let score = 99
const MAX = 1000

// Nullable
string? nickname = null
let safe = nickname == null ? "anon" : nickname
```

### Operators
```fortran
// Arithmetic
3 + 4 * 2       // 11
2 ** 10         // 1024  (power)
10 / 3          // 3
10.0 / 3.0      // 3.333...
10 % 3          // 1
10 // 3         // 3  (floor div)

// Comparison
x == y   x != y   x < y   x > y   x <= y   x >= y

// Boolean
x > 0 and y > 0
x < 0 or y < 0
not active

// String concat
"Hello" + " " + "World"
"val = " + str(42)

// Vector ops
vector a + vector b   // element-wise add
vector a * 2.0        // scalar multiply
a @ b                 // matrix multiply

// Pipe
5.0 |> sqrt |> log    // pipes left value into right function

// Compound
x += 1   x -= 1   x *= 2   x /= 2
```

### Control Flow
```fortran
// if / elif / else
if score >= 90
   println("A")
elif score >= 80
   println("B")
else
   println("C")
end

// Ternary
let label = score >= 60 ? "pass" : "fail"

// for range (inclusive)
for i in 1..10
   println(str(i))
end

// for range with step
for i in 0..100 : 5
   println(str(i))   // 0, 5, 10...
end

// for each
for item in collection
   println(item)
end

// for indexed
for i, item in collection
   println(str(i) + ": " + str(item))
end

// while
while condition
   doSomething()
end

// break / continue
for i in 1..100
   if i > 10
      break
   end
   if i % 2 == 0
      continue
   end
   println(str(i))
end
```

### Functions & Subroutines
```fortran
// Function (returns value)
function add(float a, float b) : float
   return a + b
end

// Subroutine (no return)
subroutine log(string msg)
   println("[LOG] " + msg)
end

// Default parameters
function power(float base, int exp = 2) : float
   return base ** exp
end

// Variadic
function sum(...nums) : float
   let total = 0.0
   for n in nums
      total += n
   end
   return total
end

// Async
async function fetchData(string url) : string
   return "data"
end

// Recursive
function fib(int n) : int
   if n <= 1
      return n
   end
   return fib(n-1) + fib(n-2)
end
```

### Lambdas & Functional
```fortran
// Lambda
let square = x -> x * x
let add    = (a, b) -> a + b

// Pipe operator
let result = 3.0 |> square |> (x -> x + 1.0)
// 3 → 9 → 10

// Higher-order
function apply(f, x) : float
   return f(x)
end
println(str(apply(square, 5.0)))   // 25

// List comprehension
let squares = [x * x for x in nums]
let evens   = [x for x in nums if x % 2.0 == 0.0]

// Map / filter
let doubled = nums.map(x -> x * 2.0)
let pos     = nums.filter(x -> x > 0.0)
let total   = nums.reduce((a, b) -> a + b)

// Closures
function makeAdder(float n)
   return x -> x + n
end
let add10 = makeAdder(10.0)
println(str(add10(5.0)))   // 15
```

### Classes & OOP
```fortran
class Shape
   string color
   float  area

   function init(string c)
      self.color = c
      self.area  = 0.0
   end

   function describe() : string
      return self.color + " shape"
   end
end

class Circle extends Shape
   float radius

   function init(string c, float r)
      super.init(c)
      self.radius = r
      self.area   = 3.14159 * r * r
   end

   function describe() : string
      return "Circle[r=" + str(self.radius) + ", area=" + str(self.area) + "]"
   end
end

class Rectangle extends Shape
   float width
   float height

   function init(string c, float w, float h)
      super.init(c)
      self.width  = w
      self.height = h
      self.area   = w * h
   end
end

Circle    circ = Circle("red", 5.0)
Rectangle rect = Rectangle("blue", 4.0, 6.0)

println(circ.describe())
println(rect.area)

// Polymorphism
let shapes = [circ, rect]
for s in shapes
   println(s.describe())
end
```

### Generics
```fortran
class Box<T>
   T value
   function init(v)
      self.value = v
   end
   function get() : T
      return self.value
   end
end

Box<int>    ib = Box<int>(42)
Box<string> sb = Box<string>("hello")
println(str(ib.get()))   // 42
println(sb.get())        // hello

class Stack<T>
   T[] data
   function init()
      self.data = []
   end
   function push(T v)
      self.data.push(v)
   end
   function pop() : T
      return self.data.pop()
   end
end
```

### Interfaces
```fortran
interface Drawable
   function draw() : string
   function area()  : float
end

interface Serializable
   function serialize() : string
end

class Square implements Drawable
   float side
   function draw() : string
      return "Square[" + str(self.side) + "]"
   end
   function area() : float
      return self.side * self.side
   end
end
```

### Vectors & Matrices
```fortran
import linalg

// Vectors
vector a = [1.0, 2.0, 3.0]
vector b = [4.0, 5.0, 6.0]

let c    = a + b            // [5, 7, 9]
let d    = a * 2.0          // [2, 4, 6]
let dp   = linalg.dot(a, b) // 32.0
let n    = linalg.norm(a)   // 3.74...
let cr   = linalg.cross(a, b)

// Matrices
matrix m = [[1.0, 2.0], [3.0, 4.0]]
let t  = linalg.transpose(m)
let mm = m @ m              // matrix multiply
let tr = linalg.trace(m)

// Scientific utilities
let xs = linalg.linspace(0.0, 1.0, 100)
let zs = linalg.zeros(3)
let id = linalg.eye(3)
```

### Pattern Matching
```fortran
match status
case 200
   println("OK")
case 404
   println("Not Found")
case 500
   println("Server Error")
otherwise
   println("Unknown: " + str(status))
end
```

### Error Handling
```fortran
function divide(float a, float b) : float
   if b == 0.0
      raise "Division by zero"
   end
   return a / b
end

try
   let r = divide(10.0, 0.0)
except Error msg
   println("Error: " + str(msg))
finally
   println("Done.")
end
```

### Parallel Computing
```fortran
// Parallel for loop — runs concurrently
parallel for i in 1..1000
   compute(i)
end
```

### Simulation DSL
```fortran
// Built-in scientific domains
simulate fluid
   density   = 1000.0
   velocity  = 2.5
   viscosity = 0.001
   let Re = density * velocity / viscosity
   println("Re = " + str(Re))
end

simulate heat
   temperature  = 800.0
   conductivity = 45.0
   thickness    = 0.01
   let flux = conductivity * (temperature - 300.0) / thickness
end

simulate quantum
   let hbar = 1.055e-34
   let mass = 9.109e-31
   // particle in a box...
end

simulate particle    // classical mechanics
simulate circuit     // electrical circuits
```

### AI Integration
```fortran
// Load and use AI model
let model = ai.load("weather_model.nf")

// Single prediction
vector features = [22.5, 65.0, 1013.0]
let prediction  = model.predict(features)

// Batch prediction with matrix
matrix batch = [[20.0, 60.0, 1010.0],
                [25.0, 70.0, 1015.0]]
for i in 0..1
   let row  = batch.row(i)
   let pred = model.predict(row)
   println("Sample " + str(i) + ": " + str(pred))
end
```

---

## 📚 Standard Library — 12 Modules

| Module | Description | Key Functions |
|---|---|---|
| `math` | Mathematics | `sqrt sin cos log factorial gcd PI E` |
| `linalg` | Linear Algebra | `dot cross norm eye transpose linspace matmul` |
| `io` | File I/O | `readFile writeFile readLines stdin stdout` |
| `os` | Operating System | `getcwd listDir mkdir env join run` |
| `json` | JSON | `parse stringify pretty readFile writeFile` |
| `random` | Randomness | `int float bool choice shuffle normal randn uuid` |
| `time` | Time & Date | `now sleep format today since SECOND MINUTE` |
| `string` | Strings | `format upper lower trim split join replace` |
| `stats` | Statistics | `mean median variance stdev normalize zscore` |
| `algo` | Algorithms | `quickSort binarySearch fibonacci isPrime pipe` |
| `regex` | Regex | `match search findAll replace split test` |
| `test` | Unit Testing | `describe it expect toBe toEqual report` |

### Usage
```fortran
import math
from stats import mean, stdev
from algo import quickSort, binarySearch

println(str(math.sqrt(144.0)))      // 12
println(str(mean([1.0, 2.0, 3.0]))) // 2
let sorted = quickSort([5,3,1,4,2])
```

### Unit Testing
```fortran
from test import describe, it, expect, report

describe("Vector ops", () ->
   it("dot product", () ->
      vector a = [1.0, 2.0]
      vector b = [3.0, 4.0]
      expect(a.dot(b)).toBe(11.0)
   end)
end)

describe("Math", () ->
   it("sqrt", () ->
      import math
      expect(math.sqrt(25.0)).toBe(5.0)
   end)
end)

report()
```

---

## 📁 Project Structure

```
neofortran/
├── neofortran/
│   ├── __init__.py        ← Public API (run, run_file)
│   ├── lexer.py           ← Tokenizer
│   ├── ast_nodes.py       ← 45+ AST nodes
│   ├── parser.py          ← Recursive descent parser
│   ├── interpreter.py     ← Tree-walking evaluator
│   ├── cli.py             ← CLI + REPL
│   └── stdlib/
│       └── __init__.py    ← 12 standard library modules
├── examples/
│   ├── 01_hello.nf
│   ├── 02_variables.nf
│   ├── 03_vectors.nf
│   ├── 04_classes.nf
│   ├── 05_scientific.nf
│   ├── 06_parallel.nf
│   ├── 07_generics.nf
│   ├── 08_ai.nf
│   ├── 09_simulate.nf
│   └── 10_advanced.nf
├── tests/
│   └── test_neofortran.py  ← 35 tests (100% pass)
├── setup.py
└── README.md
```

---

## 🧪 Tests

```
Results: 35/35 passed ✅

✅ hello          ✅ int arith      ✅ float
✅ power          ✅ string +       ✅ let var
✅ typed var      ✅ const          ✅ bool true
✅ bool false     ✅ if true        ✅ if else
✅ elif           ✅ for range      ✅ for each
✅ while          ✅ function       ✅ subroutine
✅ lambda         ✅ recursion      ✅ vector lit
✅ vector add     ✅ vector norm    ✅ matrix lit
✅ pipe op        ✅ list comp      ✅ class
✅ inheritance    ✅ match          ✅ try except
✅ type check     ✅ ternary        ✅ stdlib math
✅ stdlib json    ✅ string method
```

---

## 📄 License

MIT License © 2025 NeoFortran Team

---

*NeoFortran — Where scientific power meets modern elegance.*
