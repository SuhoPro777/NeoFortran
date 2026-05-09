// Advanced Features
import algo
import stats
import math

// Higher-order functions + pipe
let double  = x -> x * 2.0
let square  = x -> x * x
let addOne  = x -> x + 1.0

let result = 3.0 |> double |> square |> addOne
println("3 |> double |> square |> addOne = " + str(result))

// List comprehension
vector nums = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
let evens   = [x for x in nums if x % 2.0 == 0.0]
let squares = [x * x for x in nums]
println("Evens:   " + str(evens))
println("Squares: " + str(squares))

// Pattern matching
function classify(n) : string
   match n
   case 0  return "zero"
   case 1  return "one"
   otherwise
      if n < 0
         return "negative"
      end
      return "large"
   end
   return ""
end

for i in -1..3
   println(str(i) + " -> " + classify(i))
end

// Error handling
function safeDivide(a, b) : float
   if b == 0.0
      raise "Cannot divide by zero"
   end
   return a / b
end

try
   println("10/2 = " + str(safeDivide(10.0, 2.0)))
   println("5/0 = " + str(safeDivide(5.0, 0.0)))
except Error msg
   println("Caught: " + str(msg))
end

// Closures
function makeScaler(factor)
   return x -> x * factor
end

let triple = makeScaler(3.0)
let half   = makeScaler(0.5)
println("triple(7) = " + str(triple(7.0)))
println("half(20)  = " + str(half(20.0)))

// Quicksort
let data = [64.0, 34.0, 25.0, 12.0, 22.0, 11.0, 90.0]
let sorted = algo.quickSort(data)
println("Sorted: " + str(sorted))

// Fibonacci
let fibs = algo.fibonacci(10)
println("Fibonacci(10): " + str(fibs))
