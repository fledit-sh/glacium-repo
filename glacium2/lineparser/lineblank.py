@dataclass
class LineBlank(Line):
    def process(self) -> Any:
        return None