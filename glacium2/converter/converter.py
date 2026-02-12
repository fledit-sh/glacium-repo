from abc import ABC, abstractmethod
from typing import Iterator, Any, Iterable

class Converter(ABC):
    """
    Streaming converter:
    - feed_line(): optional output line (None => skip)
    - finalize(): optional tail (e.g., if you buffered header info)
    - convert(): wraps a whole stream
    """

    @abstractmethod
    def feed_line(self, line: str) -> Any:
        raise NotImplementedError

    def finalize(self) -> Iterator[str]:
        # default: nothing to flush
        if False:
            yield ""  # pragma: no cover

    def convert(self, lines: Iterable[str]) -> Iterator[str]:
        for line in lines:
            out = self.feed_line(line.rstrip("\n"))
            if out is not None:
                yield out
        yield from self.finalize()