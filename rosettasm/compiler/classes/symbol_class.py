from dataclasses import dataclass
from typing import Optional

@dataclass
class Symbol:
    name: str
    kind: str = "var"
    decl_node: Optional[object] = None
    type: Optional[str] = None
    initialized: bool = False