from index_craft.model import Node
from index_craft.loader import parse_freemind

def normalize_tree(node: Node) -> Node:
    tree_dict = {
        "entry": node.text,
        "children": {}
    }

    for child in node.children:
        tree_dict["children"][child.text] = normalize_tree(child)

    return tree_dict

def print_index(node: Node, level: int = 0):
    # Print the current node with proper indentation
    indent = "  " * level
    print(f"{indent}- {node.text}")
    
    # Print all children recursively
    for child in node.children:
        print_index(child, level + 1)
