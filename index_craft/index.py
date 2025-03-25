from dataclasses import dataclass
from typing import List, Optional

from index_craft.model import Node
from index_craft.loader import parse_freemind

@dataclass
class Node:
    text: str
    id: Optional[str]
    children: List['Node']


def print_index(node: Node, level: int = 0):
    # Print the current node with proper indentation
    indent = "  " * level
    print(f"{indent}- {node.text}")
    
    # Print all children recursively
    for child in node.children:
        print_index(child, level + 1)
