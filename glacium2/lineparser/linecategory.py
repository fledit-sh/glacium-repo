@dataclass
class LineCategory(Line):
    def process(self) -> Any:
        # expects '# Category: <name>'
        s = self.raw.lstrip()
        text = s[1:].strip() if s.startswith("#") else s.strip()  # remove '#'

        # robust split: 'Category: xyz' -> xyz
        _, rhs = text.split(":", 1)
        name = rhs.strip()
        return {"category": name}