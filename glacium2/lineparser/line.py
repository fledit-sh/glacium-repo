

@dataclass
class Line(ABC):
    raw: str
    result: Any | None = None

    def __post_init__(self):
        self.result = self.process()

    def process(self) -> Any:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.raw.rstrip("\n")
