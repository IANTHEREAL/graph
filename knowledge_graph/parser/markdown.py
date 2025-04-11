import json
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from pathlib import Path
from math import ceil

from .base import BaseParser, FileData, Block
from .utils import read_file_content, extract_file_info


class MarkdownParser:
    """
    A builder class for constructing knowledge graphs from documents.
    """

    def parse(self, path: str, heading_level=2) -> FileData:
        # Extract basic info
        name, extension = extract_file_info(path)
        markdown_content = read_file_content(path)
        lines = markdown_content.split("\n")

        blocks = []
        current_block_position = 0
        current_higher_level_context = []
        current_block_content = []
        current_block_title = None

        for line in lines:
            is_target_heading = line.startswith("#" * heading_level + " ")
            is_higher_heading = False
            # Check if the line is a heading with a level strictly less than heading_level
            for level in range(1, heading_level):
                if line.startswith("#" * level + " "):
                    is_higher_heading = True
                    break

            if is_higher_heading:
                # Finalize the previous target-level block if it exists, adding parent context
                if current_block_title is not None:
                    full_block_content = "\n".join(
                        current_higher_level_context + current_block_content
                    )
                    blocks.append(
                        Block(
                            name=current_block_title,
                            content=full_block_content,
                            position=current_block_position,
                        )
                    )
                    # Reset for the next block under the *new* higher context
                    current_block_content = []
                    current_block_title = None
                    current_block_position += 1

                # Start new higher-level context, including the heading line itself
                current_higher_level_context = [line]

            elif is_target_heading:
                # Finalize the previous target-level block if it exists, adding parent context
                if current_block_title is not None:
                    full_block_content = "\n".join(
                        current_higher_level_context + current_block_content
                    )
                    blocks.append(
                        Block(
                            name=current_block_title,
                            content=full_block_content,
                            position=current_block_position,
                        )
                    )
                    current_block_content = []
                    current_block_title = None
                    current_block_position += 1

                # Start new target-level block
                current_block_title = line[heading_level + 1 :].strip()  # +1 for space
                current_block_content = [line]  # Start block content with its heading

            else:
                # Append line to the appropriate context
                if current_block_title is not None:
                    current_block_content.append(line)
                elif current_higher_level_context:
                    current_higher_level_context.append(line)
                else:
                    raise ValueError(f"not found suitable block for {line}")

        # Save the last block after the loop
        if current_block_title is not None:
            full_block_content = "\n".join(
                current_higher_level_context + current_block_content
            )
            blocks.append(
                Block(
                    name=current_block_title,
                    content=full_block_content,
                    position=current_block_position,
                )
            )

        return FileData(name=name, content=markdown_content, blocks=blocks)
