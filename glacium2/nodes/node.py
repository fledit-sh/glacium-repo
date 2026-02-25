from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


class Context:
    def __init__(self, strategy: Strategy) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> Strategy:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: Strategy) -> None:
        self._strategy = strategy

    def compute(self) -> None:
        result = self._strategy.compute(["a", "b", "c", "d", "e"])


class Strategy(ABC):
    @abstractmethod
    def compute(self):
        pass

class PassThrough(Strategy):
    def compute(self):
        pass


class Multiply(Strategy):
    def compute(self):
        pass


@dataclass
class Node(ABC):
    """
    - Hält eine Function, diese function kann als state/methodpattern implementiert werden.
    - Brauche eine nodefactory in welcher die nodes instanziiert werden.
    - Kann entspannt gespeichert werden. Inputs und Outputs.
    """
    def strategy(self):
        pass

    @abstractmethod
    def add_in(self, ConfigVar):
        pass

    @abstractmethod
    def add_out(self, ConfigVar):
        pass

    @abstractmethod
    def compute(self):
        pass





