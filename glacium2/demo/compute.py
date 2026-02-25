import math

OPS={
    "add": lambda a, b: a + b,
    "mul": lambda a, b: a * b,
    "sub": lambda a, b: a - b,
    "div": lambda a, b: a / b,
    "sin": lambda x: math.sin(x),
    "cos": lambda x: math.cos(x),
    "passthrough": lambda x: x,
}