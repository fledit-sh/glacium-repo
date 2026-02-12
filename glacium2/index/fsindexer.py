@dataclass
class FsIndexer(Indexer):

    root: Path
    files: List[FileMeta] = field(default_factory=list)

    def __post_init__(self):
        self.files = self.index()

    def acquire(self, fpath: Path) -> FileMeta | None:
        if not fpath.is_file():
            return None

        tokens = fpath.name.split(".")

        shot: int | None = None
        filetype_tokens: list[str] = []

        for tok in tokens:
            if tok.isdigit() and len(tok) == 6 and shot is None:
                shot = int(tok)
            else:
                filetype_tokens.append(tok)

        return FileMeta(
            fpath=fpath,
            ftype=tuple(filetype_tokens),
            fdate=datetime.fromtimestamp(fpath.stat().st_mtime),
            shot=shot,
        )

    def index(self) -> List[FileMeta]:
        files: List[FileMeta] = []

        for p in self.root.rglob("*"):
            meta = self.acquire(p)
            if meta is not None:
                files.append(meta)

        return files