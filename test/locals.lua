function foo(x)
   print (x)
   local g = function (x) print (x) end
   g(x)
end

foo("aaa")

   
