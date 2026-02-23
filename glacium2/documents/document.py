
from ..lineparser import *

LINE_TYPES = [
    LineBlank,
    LineCategory,
    LineComment,
    LineKeyArgs,
]

class Document:
    """
    1.) Document is a base class
    2.) Documents main purpose is to hold a list of the Lines in a file
    3.) The lines are objects and hold the regex strings
    3.) load is an interface method to standardize file reading
    4.) You can load any file with the same method
    5.) Factory would be a possible adaptation
    """
    def __init__(self):
        self.lines = []

    def load(self, fpath: str):
        with open(fpath) as f:
            for raw in f:
                for T in LINE_TYPES:
                    try:
                        self.lines.append(T(raw))
                        break
                    except ValueError:
                        pass
                else:
                    self.lines.append(LineUnknown(raw))


