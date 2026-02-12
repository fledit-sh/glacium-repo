@dataclass
class VarPool:
    name: str = "Unnamed Variable Pool"
    _vars: Dict[str, ControlledVar] = field(default_factory=dict)

    def attach(self, v: ControlledVar[Any]):
        self._vars[v.key] = v

    def __getitem__(self, item):
        return self._vars[item]

    def __setitem__(self, key, value):
        self._vars[key].value = value