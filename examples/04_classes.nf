// OOP — Classes, Inheritance, Polymorphism
class Animal
   string name
   float  weight

   function init(n, w)
      self.name   = n
      self.weight = w
   end

   function speak() : string
      return self.name + " makes a sound"
   end

   function info() : string
      return self.name + " (" + str(self.weight) + " kg)"
   end
end

class Dog extends Animal
   string breed

   function init(n, w, b)
      super.init(n, w)
      self.breed = b
   end

   function speak() : string
      return self.name + " says: Woof!"
   end

   function info() : string
      return super.info() + " [" + self.breed + "]"
   end
end

class Cat extends Animal
   function init(n, w)
      super.init(n, w)
   end

   function speak() : string
      return self.name + " says: Meow~"
   end
end

// Instantiation
Dog d = Dog("Rex", 30.5, "Labrador")
Cat c = Cat("Whiskers", 4.2)

println(d.speak())
println(c.speak())
println(d.info())
println(c.info())

// Polymorphism
let animals = [d, c]
for a in animals
   println(a.speak())
end
