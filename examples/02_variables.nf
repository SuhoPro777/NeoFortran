// Variables and Types
int    age    = 25
float  pi     = 3.14159
string name   = "NeoFortran"
bool   active = true
let    score  = 99
const  MAX    = 1000

println("Name:   " + name)
println("Age:    " + str(age))
println("Pi:     " + str(pi))
println("Score:  " + str(score))

// Type checking
if age is int
   println("age is integer")
end

// Ternary
let label = score >= 60 ? "pass" : "fail"
println("Result: " + label)
