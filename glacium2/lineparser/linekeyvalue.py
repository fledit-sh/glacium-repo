@dataclass
class LineKeyValue(Line):
    def process(self) -> Any:
        tokens = self.raw.strip().split()
        if not tokens:
            return None
        return {"key": tokens[0], "values": tokens[1:]}
