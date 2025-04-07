import xml.etree.ElementTree as ET
from index_craft.model import Node

def parse_freemind(file_path: str) -> Node:
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    def parse_node(node_elem) -> Node:
        # Extract node attributes
        text = node_elem.get('TEXT', '').strip()
        node_id = node_elem.get('ID', None)
        
        # Recursively parse children
        children = []
        for child in node_elem.findall('node'):
            children.append(parse_node(child))
            
        return Node(text=text, id=node_id, children=children)
    
    # Find the root node and parse the tree
    root_node = root.find('node')
    return parse_node(root_node)
