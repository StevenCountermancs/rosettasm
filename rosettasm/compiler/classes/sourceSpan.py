from dataclasses import dataclass

@dataclass(frozen=True)
class SourceSpan:
    line: int
    start_col: int
    end_col: int