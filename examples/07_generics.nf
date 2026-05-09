// Generics and Higher-order Functions
class Box<T>
   T value

   function init(v)
      self.value = v
   end

   function get() : T
      return self.value
   end

   function map(f) : T
      return f(self.value)
   end
end

class Pair<T>
   T first
   T second

   function init(a, b)
      self.first  = a
      self.second = b
   end

   function swap()
      let tmp    = self.first
      self.first = self.second
      self.second = tmp
   end
end

Box<int> b1 = Box<int>(42)
println("Box value: " + str(b1.get()))

let doubled = b1.map(x -> x * 2)
println("Doubled:   " + str(doubled))

Box<string> bs = Box<string>("Hello NeoFortran")
println("String box: " + bs.get())

Pair<float> p = Pair<float>(3.14, 2.71)
println("Pair: " + str(p.first) + ", " + str(p.second))
p.swap()
println("Swapped: " + str(p.first) + ", " + str(p.second))
