import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List
import json

from .base import BaseParser, Block, FileData
from .utils import read_file_content, extract_file_info


class FreemindParser(BaseParser):
    """
    Parses Freemind (.mm) files into a hierarchical Block structure
    and provides a clean JSON representation of the mind map.
    """

    def _parse_node(self, node_elem: ET.Element) -> Block:
        """
        Recursively parse an XML element representing a node into a Block.
        """
        text = node_elem.get("TEXT", "").strip()
        node_id = node_elem.get("ID", None)

        children = [self._parse_node(child) for child in node_elem.findall("node")]

        return Block(content=text, name=text, children=children)

    def parse(self, path: str, **kwargs: Any) -> FileData:
        """
        Parse the Freemind file located at the given path.

        Parameters:
        - path: Path to the .mm file.
        - **kwargs: Not used in this parser.

        Returns:
        - FileData with:
            - name: Filename without extension
            - blocks: Root Block of the parsed mind map tree
            - content: JSON string representation of the mind map (without XML tags)
        """
        name, _ = extract_file_info(path)

        try:
            # Parse the XML file directly
            tree = ET.parse(path)
            root = tree.getroot()

            map_node = root.find("node")
            if map_node is None:
                raise ValueError("Could not find the root node in the Freemind file.")

            # Parse the mind map structure into Block objects
            root_block = self._parse_node(map_node)

            # Convert the Block structure to a dictionary for JSON serialization
            def block_to_dict(block: Block) -> Dict:
                return {
                    "text": block.content,
                    "children": [block_to_dict(child) for child in block.children],
                }

            # Create a clean representation and convert to JSON
            clean_map = block_to_dict(root_block)
            json_content = json.dumps(clean_map, indent=2, ensure_ascii=False)

            # Return FileData with the parsed structure and JSON content
            return FileData(
                name=name,
                content=json_content,  # JSON string instead of raw XML
                blocks=root_block,
            )

        except ET.ParseError as e:
            raise ValueError(f"Error parsing XML content from file {path}: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Freemind file not found at {path}")
        except Exception as e:
            raise RuntimeError(f"Error processing {path}: {e}")
