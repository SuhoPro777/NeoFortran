// Scientific Simulation DSL
import math
import stats

// Fluid dynamics simulation
println("=== Fluid Simulation ===")
simulate fluid
   density  = 1000.0
   velocity = 2.5
   pressure = 101325.0
   viscosity = 0.001

   let Re = density * velocity / viscosity
   println("Reynolds number: " + str(Re))

   let dP = 0.5 * density * velocity * velocity
   println("Dynamic pressure: " + str(dP))
end

// Heat transfer simulation
println("\n=== Heat Simulation ===")
simulate heat
   temperature = 800.0
   conductivity = 45.0
   thickness    = 0.01

   let flux = conductivity * (temperature - 300.0) / thickness
   println("Heat flux: " + str(flux) + " W/m^2")
end

// Particle simulation
println("\n=== Particle Simulation ===")
simulate particle
   mass     = 1.0
   velocity = 10.0
   force    = 5.0
   dt       = 0.01

   let acceleration = force / mass
   let v_new = velocity + acceleration * dt
   let energy = 0.5 * mass * velocity * velocity

   println("Acceleration: " + str(acceleration) + " m/s^2")
   println("New velocity: " + str(v_new) + " m/s")
   println("Kinetic energy: " + str(energy) + " J")
end

// Quantum state simulation
println("\n=== Quantum Simulation ===")
simulate quantum
   let hbar = 1.055e-34
   let mass = 9.109e-31
   let L    = 1.0e-9

   // Particle in a box energy levels
   for n in 1..4
      let E = (n * n * 3.14159 * 3.14159 * hbar * hbar) / (2.0 * mass * L * L)
      println("E_" + str(n) + " = " + str(E) + " J")
   end
end
