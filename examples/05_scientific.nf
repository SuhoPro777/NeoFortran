// Scientific Computing
import math
import linalg
import stats

// Math functions
println("=== Math ===")
println("sqrt(144) = " + str(math.sqrt(144)))
println("sin(PI/2) = " + str(math.sin(math.PI / 2.0)))
println("factorial(10) = " + str(math.factorial(10)))
println("log2(1024) = " + str(math.log2(1024.0)))

// Statistics
println("\n=== Statistics ===")
vector data = [4.0, 7.0, 13.0, 2.0, 1.0, 8.0, 9.0, 3.0, 5.0, 11.0]
println("Data: " + str(data))
println("Mean:   " + str(stats.mean(data)))
println("Std:    " + str(stats.stdev(data)))
println("Min:    " + str(stats.min(data)))
println("Max:    " + str(stats.max(data)))
let norm = stats.normalize(data)
println("Normalized: " + str(norm))

// Linear Algebra
println("\n=== Linear Algebra ===")
matrix A = [[2.0, 1.0], [5.0, 3.0]]
matrix B = [[3.0, -1.0], [-5.0, 2.0]]
let AB = A @ B
println("A @ B =")
println(str(AB))
println("Trace(A) = " + str(linalg.trace(A)))

// Simulate
println("\n=== Simulation ===")
simulate heat
   temperature = 500.0
   conductivity = 50.0
   flux = conductivity * temperature
   println("Heat flux = " + str(flux))
end
