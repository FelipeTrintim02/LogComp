local x
x = 1 + (1==1) --// Ok
x = 1 and (1==1) --// Ok
x = "a" .. 1 .. (1==1) --// Ok
x = "a" == "b" --// Ok, resultado bool: 0
--x = 1 + "a" --// ERROR: Incompatible types
--x = (1==1) and "a" --// ERROR: Incompatible types