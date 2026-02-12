@dataclass
class LineComment(Line):
    def process(self) -> Any:
        # keep comment text without leading '#'
        s = self.raw.lstrip()
        text = s[1:].strip() if s.startswith("#") else s.strip()
        return {"comment": text}