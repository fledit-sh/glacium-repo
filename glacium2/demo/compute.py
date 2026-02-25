import logging
import math
import inspect
from glacium2.scheme import ConfigVar as CoV

OPS = {
    "add": lambda a, b: a + b,
    "mul": lambda a, b: a * b,
    "sub": lambda a, b: a - b,
    "div": lambda a, b: a / b,
    "sin": lambda x: math.sin(x),
    "cos": lambda x: math.cos(x),
    "passthrough": lambda x: x,
}

class Rule:

    def __init__(self, dst: CoV, function: str, *args: CoV, **kwargs):
        self.dst = dst
        self.function = OPS[function]
        self.args = args
        self.kwargs = kwargs
        self.compute()

    def compute(self):

        # extract values
        values = [arg.value for arg in self.args]
        # print(self.dst.value)

        kwvalues = {
            key: float(var.value)
            for key, var in self.kwargs.items()
        }

        result = self.function(*values, **kwvalues)

        self.dst.value = result

        return result

