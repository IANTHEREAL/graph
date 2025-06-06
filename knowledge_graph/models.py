import uuid
from sqlalchemy import (
    BigInteger,
    Column,
    String,
    Text,
    ForeignKey,
    DateTime,
    Enum,
    Index,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from tidb_vector.sqlalchemy import VectorType

Base = declarative_base()


class SourceData(Base):
    """Source document entity"""

    __tablename__ = "source_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    content = Column(LONGTEXT, nullable=True)
    link = Column(String(512), nullable=True)
    version = Column(String(50), nullable=True)
    data_type = Column(
        Enum("document", "code", "image", "video"), nullable=False, default="document"
    )
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    # Relationships
    knowledge_blocks = relationship("KnowledgeBlock", back_populates="source")

    __table_args__ = (
        Index("idx_source_link", "link", unique=True),
        Index("idx_source_name", "name"),
        Index("idx_version", "version"),
        Index("idx_data_type", "data_type"),
    )

    def __repr__(self):
        return f"<SourceData(id={self.id}, name={self.name}, link={self.link})>"


class KnowledgeBlock(Base):
    """Block of knowledge extracted from a source"""

    __tablename__ = "knowledge_blocks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    knowledge_type = Column(
        Enum("qa", "paragraph", "synopsis", "image", "video", "code"), nullable=False
    )
    content = Column(LONGTEXT, nullable=True)
    context = Column(Text, nullable=True)
    content_vec = Column(VectorType(1536), nullable=True)
    attributes = Column(JSON, nullable=True)
    position_in_source = Column(BigInteger, default=0)
    source_version = Column(String(50), nullable=True)
    source_id = Column(String(36), ForeignKey("source_data.id"), nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    # Relationships
    source = relationship("SourceData", back_populates="knowledge_blocks")

    __table_args__ = (
        Index("idx_kb_source_version", "source_version"),
        Index("idx_kb_knowledge_type", "knowledge_type"),
    )

    def __repr__(self):
        return f"<KnowledgeBlock(id={self.id}, name={self.name})>"


class Concept(Base):
    """Core concept entity in the knowledge graph"""

    __tablename__ = "concepts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    definition = Column(Text, nullable=True)
    definition_vec = Column(VectorType(1536), nullable=True)
    version = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    __table_args__ = (
        Index("idx_name", "name"),
        Index("idx_version", "version"),
    )

    def __repr__(self):
        return f"<Concept(id={self.id}, name={self.name})>"


# Define standard relation types
STANDARD_RELATION_TYPES = [
    "SOURCE_OF",
    "EXPLAINS",
    "DEPENDS_ON",
    "REFERENCES",
    "PART_OF",
    "SIMILAR_TO",
]


class Relationship(Base):
    """Relationship between entities in the knowledge graph"""

    __tablename__ = "relationships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), nullable=False)
    source_type = Column(String(50), nullable=False)
    target_id = Column(String(36), nullable=False)
    target_type = Column(String(50), nullable=False)
    relationship_type = Column(String(255), nullable=False, default="REFERENCES")
    relationship_desc = Column(Text, nullable=True)
    relationship_desc_vec = Column(
        VectorType(1536), nullable=True
    )  # Vector column for embeddings
    knowledge_bundle = Column(JSON, nullable=True)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    __table_args__ = (
        Index("idx_relationship_source", "source_type", "source_id"),
        Index("idx_relationship_target", "target_type", "target_id"),
        Index("idx_relationship_type", "relationship_type"),
    )

    def __repr__(self):
        return f"<Relationship(source={self.source_id}, target={self.target_id}, desc={self.relationship_desc})>"


class BestPractice(Base):
    __tablename__ = "best_practices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("source_data.id"), nullable=True)
    labels = Column(String(255), nullable=True)
    guideline = Column(Text, nullable=True)
    guideline_vec = Column(VectorType(1536), nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    __table_args__ = (
        Index("idx_bp_source_id", "source_id"),
        Index("idx_bp_labels", "labels"),
    )

    def __repr__(self):
        return f"<BestPractice(id={self.id}, source_id={self.source_id}, tag={self.labels})>"
