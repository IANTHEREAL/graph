import uuid
from typing import Dict, List, Literal, Optional, Any, Union
from dataclasses import dataclass, field


@dataclass
class Concept:
    """Core concept entity in the knowledge graph"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    definition: str = ""
    version: str = ""


@dataclass
class SubConcept:
    """Sub-concept entity that relates to a parent concept"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    definition: str = ""
    parent_concept_id: str = ""
    aspect_descriptor: str = (
        ""  # Describes what aspect/dimension of the parent concept this subconcept covers
    )
    knowledge_block_ids: List[str] = field(default_factory=list)


@dataclass
class KnowledgeBlock:
    """Block of knowledge extracted from a source"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    definition: str = ""
    source_version: str = ""
    source_ids: List[str] = field(default_factory=list)


@dataclass
class SourceData:
    """Source document entity"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    definition: str = ""
    link: str = ""
    version: str = ""
    type: Literal["document", "code"] = "document"


# Define standard relation types
STANDARD_RELATION_TYPES = [
    "EXPLAINS",
    "DEPENDS_ON",
    "REFERENCES",
    "PART_OF",
    "SIMILAR_TO",
]


@dataclass
class Relationship:
    """Relationship between entities in the knowledge graph"""

    source_id: str
    source_type: str
    target_id: str
    target_type: str
    relation_type: str = "REFERENCES"  # Supports both standard and custom types
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate relation_type if it's a standard type"""
        if self.relation_type in STANDARD_RELATION_TYPES:
            # It's a standard type, no validation needed
            pass
        else:
            # It's a custom type, ensure it's a valid string
            if not isinstance(self.relation_type, str) or not self.relation_type:
                raise ValueError(
                    f"Custom relation_type must be a non-empty string, got: {self.relation_type}"
                )

    @property
    def is_standard_relation(self) -> bool:
        """Check if the relation type is a standard type"""
        return self.relation_type in STANDARD_RELATION_TYPES
