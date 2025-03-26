from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Node:
    text: str
    id: Optional[str]
    children: List['Node']
