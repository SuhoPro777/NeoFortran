// Scientific Vectors and Matrices
import linalg

vector a = [1.0, 2.0, 3.0]
vector b = [4.0, 5.0, 6.0]

// Vector arithmetic
let c = a + b
println("a + b = " + str(c))

let d = a * 2.0
println("a * 2 = " + str(d))

// dot product
let dp = linalg.dot(a, b)
println("dot(a,b) = " + str(dp))

// norm
let n = linalg.norm(a)
println("norm(a) = " + str(n))

// cross product
let cross = linalg.cross(a, b)
println("cross(a,b) = " + str(cross))

// Matrix
matrix m1 = [[1.0, 2.0], [3.0, 4.0]]
matrix m2 = [[5.0, 6.0], [7.0, 8.0]]

// Matrix multiply
let result = m1 @ m2
println("m1 @ m2 =")
println(str(result))

// Transpose
let t = linalg.transpose(m1)
println("transpose =")
println(str(t))

// linspace
let xs = linalg.linspace(0.0, 1.0, 5)
println("linspace(0,1,5) = " + str(xs))
