# Knowledge Graph Builder Design Document

A lightweight yet powerful framework for constructing knowledge graphs, supporting automated concept extraction, relationship discovery, and flexible knowledge representation.

## Graph Schema

### Core Entities

**Concept**
- id: UUID  
- name: String
- definition: Text
- version: String

**SubConcept**
- id: UUID  
- name: String
- definition: Text
- parent_concept_id: UUID
- subconcept_kind: String
- knowledge_block_id: UUID

**KnowledgeBlock**
- id: UUID
- name: String
- definition: Text
- source_version: String
- source_type: "document"|...
- source_id: UUID

**Document**
- id: UUID  
- name: String
- definition: Text
- link: String
- version: String

**Relationship**
- source_id: UUID
- source_type: String
- target_id: UUID
- target_type: String
- relation_type: "EXPLAINS"|"DEPENDS_ON"|"REFERENCES"|...
- attributes: {
    "excerpt": String,
    "start_pos": Integer,
    "end_pos": Integer,
    "weight": Float,
    "description": String,
    "confidence": Float,
} # attributes vary based on relation_type

## Configuration Mechanism

Users can customize the graph construction process through natural language configuration:

1. **Graph Definition**
   - Core concept definitions 
   - Knowledge domain specifications
   - Entity and relationship taxonomies

2. **Processing Instructions**
   - Knowledge block extraction parameters
   - Concept to SubConcept expansion methods
   - Relationship discovery guidelines and thresholds

3. **Default Processing**
   - When specific configurations aren't provided, the system uses standard extraction and discovery methods

## Core API

```python
class DocBuilder:
    
    def __init__(self, graph, graph_spec):
        """
        Initialize the builder with a graph instance and specifications.
        
        Parameters:
        - graph: The knowledge graph to populate
        - graph_spec: Configuration for extraction and analysis processes
        """
    
    def extract_knowledge_blocks(
        self,
        file_path: str | list[str],
        metadata: dict
    ) -> None:
        """
        Extract structured knowledge blocks from documents.
        
        Parameters:
        - file_path: Path to single file or list of files
        - metadata: Additional information to attach to blocks, including:
            - doc_version: Tracks document version for multi-version knowledge management
            - visible_labels: Defines access rules for derived knowledge (e.g., "public", "internal-team")
        """
    
    def analyze_concepts(
        self, 
        concept_file: str | None = None
    ) -> list[Concept]:
        """
        Identify core concepts within the knowledge blocks.
        
        Parameters:
        - concept_file: Optional path to file with predefined concepts
        
        Returns:
        - List of discovered or defined concepts
        
        Notes:
        - Auto-discovers concepts from knowledge blocks when concept_file=None
        - Loads predefined concepts from file when provided
        """

    def extend_concepts(
        self,
        concepts: list[Concept] | None = None,
    ) -> KnowledgeGraph:
        """
        Expand concepts into related sub-concepts.
        
        Parameters:
        - concepts: List of concepts to expand, or None to use previously discovered concepts
        
        Returns:
        - Enhanced knowledge graph with sub-concepts
        """
    
    def extend_relationships(
        self,
        source_concept: Concept | None = None,
        target_concept: Concept | None = None
    ) -> KnowledgeGraph:
        """
        Discover and create relationships between concepts.
        
        Parameters:
        - source_concept: Optional concept to use as relationship source
        - target_concept: Optional concept to use as relationship target
        
        Returns:
        - Enhanced knowledge graph with relationships
        
        Notes:
        - When parameters are None, discovers relationships among all concepts
        - When specified, focuses on relationships involving those concepts
        """
```

## Usage Example

```python
# Initialize with configuration
builder = DocBuilder(Graph(), graph_spec)

# Extract knowledge from documents with version control
builder.extract_knowledge_blocks("spec.pdf", metadata={
    "doc_version": "2023Q4",
    "visible_labels": "engineering"
})

# Perform concept analysis - combination of automatic and manual
auto_concepts = builder.analyze_concepts()
manual_concepts = [Concept("legacy-system")]

# Enhance the graph with subconcepts
graph = builder.extend_concepts(
    concepts=manual_concepts + auto_concepts
)

# Discover relationships between concepts
complete_graph = builder.extend_relationships()

# Or focus on specific concept relationships
specific_graph = builder.extend_relationships(
    source_concept=Concept("system-architecture"),
    target_concept=Concept("performance-requirements")
)
```

## Features and Benefits

- **Hybrid Knowledge Discovery**: Combines automated extraction with manual curation
- **Versioned Knowledge**: Tracks document versions and knowledge evolution
- **Flexible Configuration**: Adapts to different domains through natural language configuration
- **Rich Relationships**: Captures context, confidence, and metadata in relationships
- **Access Control**: Supports visibility labels for secure knowledge management
