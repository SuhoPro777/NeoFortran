// Parallel Computing
import math
import stats

println("=== Parallel For ===")

let results = []
parallel for i in 1..10
   let val = math.sqrt(i * 1.0) * math.sin(i * 1.0)
   results.push(val)
end

println("Parallel computed " + str(results.length) + " values")

// Serial for comparison
let serial = []
for i in 1..10
   serial.push(math.sqrt(i * 1.0))
end
println("Serial:   " + str(serial))
println("Mean:     " + str(stats.mean(serial)))
println("Std:      " + str(stats.stdev(serial)))
