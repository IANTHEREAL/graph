from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Union


@dataclass
class Block:
    name: str
    content: str
    children: Optional[List["Block"]] = None
    position: Optional[int] = 0


@dataclass
class FileData:
    name: str
    content: str
    blocks: Union[Block, List[Block], None]


class BaseParser(ABC):
    """
    Abstract base class for document parsers.
    """

    @abstractmethod
    def parse(self, path: str, **kwargs: Any) -> FileData:
        """
        Parse the document located at the given path.

        Parameters:
        - path: Path to the document file.
        - **kwargs: Additional keyword arguments specific to the parser implementation.

        Returns: FileData
        """
        pass
