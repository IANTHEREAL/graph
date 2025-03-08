# Knowledge Graph Builder Design Document

A lightweight builder for constructing knowledge graphs, supporting core concept extraction and relationship discovery.

## Core Components

1. DocBuilder: Central class encapsulating graph construction workflow with minimal dependencies.
2. Metadata Attributes: Key-value pairs attached to knowledge elements:

    - doc_version: Tracks document version for multi-version knowledge management
    - visible_labels: Defines access rules for derived knowledge (e.g., "public", "internal-team")
    - Custom fields: Allow extension with domain-specific properties

## Essential Methods

```python
class DocBuilder:
    
    def extract_blocks(
        self,
        file_path: str | list[str],
        metadata: dict = {"doc_version": "", "visible_scope": "default"}
    ) -> None:
        """
        Extract structured knowledge blocks from documents
        - Accepts single/multiple files
        - Attaches metadata to all extracted blocks
        """
    
    def analyze_concepts(
        self, 
        concept_file: str | None = None
    ) -> list[Concept]:
        """
        Core concept analysis:
        - Auto-discovers concepts when concept_file=None
        - Loads predefined concepts if file provided
        Returns list of validated concepts
        """

    def extend_concepts(
        self,
        concepts: list[Concept] | None = None,
    ) -> KnowledgeGraph:
        """
        Enhance graph construction:
        - extend extra sub-concepts for provided concepts
        Returns immutable graph snapshot
        """

    
    def extend_relationships(
        self,
        source_concept: Concept | None = None,
        target_concept: Concept | None = None
    ) -> KnowledgeGraph:
        """
        Enhance graph construction:
        - auto-discovered relationships
        Returns immutable graph snapshot
        """
    
```


## Usage

```
builder = DocBuilder()

# Extract with version control
builder.extract_blocks("spec.pdf", metadata={
    "doc_version": "2023Q4",
    "visible_scope": "engineering"
})

# Hybrid concept analysis
auto_concepts = builder.analyze_concepts()
manual_concepts = [Concept("legacy-system")]

# enahnce graph
graph = builder.extend_entities(
    concepts=manual_concepts,
)

graph = builder.extend_relationships(
    source_concept=source_concept,
    target_concept=target_concept,
)
```
