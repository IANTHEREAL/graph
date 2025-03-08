import json
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path

from graph.models import Concept, SubConcept, KnowledgeBlock, Document, Relationship
from graph.graph import KnowledgeGraph

from llm.interface import LLMInterface

class DocBuilder:
    """
    A builder class for constructing knowledge graphs from documents.
    """

    def __init__(
        self, graph: KnowledgeGraph, llm_client: LLMInterface
    ):
        """
        Initialize the builder with a graph instance and specifications.

        Parameters:
        - graph: The knowledge graph to populate
        - graph_spec: Configuration for extraction and analysis processes
        """
        self.graph = graph
        self.llm_client = llm_client
        self.discovered_concepts = []
        self.knowledge_blocks = []
        self.documents = []

    def _read_file(self, file_path: str) -> str:
        """
        Read a file and return its contents.

        Parameters:
        - file_path: Path to the file

        Returns:
        - File contents as string
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _extract_file_info(self, file_path: str) -> Tuple[str, str]:
        """
        Extract file name and extension from a file path.

        Parameters:
        - file_path: Path to the file

        Returns:
        - Tuple of (file_name, file_extension)
        """
        path = Path(file_path)
        return path.stem, path.suffix

    def extract_knowledge_blocks(
        self, file_path: Union[str, List[str]], metadata: Dict[str, Any]
    ) -> List[KnowledgeBlock]:
        """
        Extract structured knowledge blocks from documents.

        Parameters:
        - file_path: Path to single file or list of files
        - metadata: Additional information to attach to blocks, including:
            - doc_version: Tracks document version for multi-version knowledge management
            - visible_labels: Defines access rules for derived knowledge (e.g., "public", "internal-team")

        Returns:
        - List of extracted KnowledgeBlock objects
        """
        if self.llm_client is None:
            raise ValueError(
                "LLM client must be set before extracting knowledge blocks"
            )

        # Handle single file or list of files
        if isinstance(file_path, str):
            file_paths = [file_path]
        else:
            file_paths = file_path

        blocks = []
        for path in file_paths:
            # Create document entity
            name, extension = self._extract_file_info(path)
            doc_content = self._read_file(path)

            document = Document(
                name=name,
                definition=f"Document: {name}{extension}",
                link=path,
                version=metadata.get("doc_version", "1.0"),
            )

            # Add document to graph
            doc_id = self.graph.add_document(document)
            self.documents.append(document)

            # Extract knowledge blocks using LLM
            prompt = self.graph_spec.get_extraction_prompt("knowledge_block_extraction")
            response = self.llm_client.complete(
                prompt=f"{prompt}\n\nText:\n{doc_content[:10000]}"  # Limit text size
            )

            try:
                # Parse JSON response
                extracted_blocks = json.loads(response)

                # Create and add knowledge blocks
                for block_data in extracted_blocks:
                    kb = KnowledgeBlock(
                        name=block_data.get("name", ""),
                        definition=block_data.get("definition", ""),
                        source_version=metadata.get("doc_version", "1.0"),
                        source_type="document",
                        source_id=doc_id,
                    )

                    # Add knowledge block to graph
                    kb_id = self.graph.add_knowledge_block(kb)
                    blocks.append(kb)
                    self.knowledge_blocks.append(kb)

            except (json.JSONDecodeError, TypeError):
                print(f"Failed to parse knowledge blocks from {path}")

        return blocks

    def analyze_concepts(self, concept_file: Optional[str] = None) -> List[Concept]:
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
        concepts = []

        # Load predefined concepts if provided
        if concept_file:
            try:
                with open(concept_file, "r") as f:
                    predefined_concepts = json.load(f)

                for concept_data in predefined_concepts:
                    concept = Concept(
                        name=concept_data.get("name", ""),
                        definition=concept_data.get("definition", ""),
                        version=concept_data.get("version", "1.0"),
                    )

                    # Add concept to graph
                    self.graph.add_concept(concept)
                    concepts.append(concept)

                self.discovered_concepts = concepts
                return concepts

            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error loading concepts from file: {e}")

        # If no concept file or error loading, discover concepts from knowledge blocks
        if self.llm_client is None:
            raise ValueError("LLM client must be set before analyzing concepts")

        if not self.knowledge_blocks:
            print("No knowledge blocks available for concept extraction")
            return []

        # Combine knowledge blocks for analysis
        combined_blocks = "\n\n".join(
            [
                f"Block: {kb.name}\nContent: {kb.definition}"
                for kb in self.knowledge_blocks[:10]  # Limit to avoid token limits
            ]
        )

        # Extract concepts using LLM
        prompt = self.graph_spec.get_extraction_prompt("concept_extraction")
        response = self.llm_client.complete(
            prompt=f"{prompt}\n\nKnowledge Blocks:\n{combined_blocks}"
        )

        try:
            # Parse JSON response
            extracted_concepts = json.loads(response)

            # Create and add concepts
            for concept_data in extracted_concepts:
                concept = Concept(
                    name=concept_data.get("name", ""),
                    definition=concept_data.get("definition", ""),
                    version="1.0",
                )

                # Add concept to graph
                self.graph.add_concept(concept)
                concepts.append(concept)

        except (json.JSONDecodeError, TypeError):
            print("Failed to parse concepts from LLM response")

        self.discovered_concepts = concepts
        return concepts

    def extend_concepts(
        self, concepts: Optional[List[Concept]] = None
    ) -> KnowledgeGraph:
        """
        Expand concepts into related sub-concepts.

        Parameters:
        - concepts: List of concepts to expand, or None to use previously discovered concepts

        Returns:
        - Enhanced knowledge graph with sub-concepts
        """
        if self.llm_client is None:
            raise ValueError("LLM client must be set before extending concepts")

        # Use provided concepts or previously discovered ones
        target_concepts = concepts or self.discovered_concepts

        if not target_concepts:
            print("No concepts available to extend")
            return self.graph

        for concept in target_concepts:
            # Skip if no knowledge blocks
            if not self.knowledge_blocks:
                continue

            # Combine knowledge blocks for analysis
            combined_blocks = "\n\n".join(
                [
                    f"Block: {kb.name}\nContent: {kb.definition}"
                    for kb in self.knowledge_blocks[:5]  # Limit to avoid token limits
                ]
            )

            # Extract subconcepts using LLM
            prompt = self.graph_spec.format_extraction_prompt(
                "subconcept_extraction",
                concept_name=concept.name,
                concept_definition=concept.definition,
            )

            response = self.llm_client.complete(
                prompt=f"{prompt}\n\nKnowledge Blocks:\n{combined_blocks}"
            )

            try:
                # Parse JSON response
                extracted_subconcepts = json.loads(response)

                # Create and add subconcepts
                for subconcept_data in extracted_subconcepts:
                    # Assign to a random knowledge block for now (this could be improved)
                    kb_id = self.knowledge_blocks[0].id if self.knowledge_blocks else ""

                    subconcept = SubConcept(
                        name=subconcept_data.get("name", ""),
                        definition=subconcept_data.get("definition", ""),
                        parent_concept_id=concept.id,
                        subconcept_kind=subconcept_data.get("subconcept_kind", ""),
                        knowledge_block_id=kb_id,
                    )

                    # Add subconcept to graph
                    self.graph.add_subconcept(subconcept)

            except (json.JSONDecodeError, TypeError):
                print(f"Failed to parse subconcepts for concept: {concept.name}")

        return self.graph

    def extend_relationships(
        self,
        source_concept: Optional[Concept] = None,
        target_concept: Optional[Concept] = None,
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
        if self.llm_client is None:
            raise ValueError("LLM client must be set before extending relationships")

        # Determine which concepts to analyze
        all_concepts = list(self.graph.concepts.values())

        if source_concept and target_concept:
            # Analyze specific pair
            self._analyze_concept_pair(source_concept, target_concept)

        elif source_concept:
            # Analyze relationships between source and all other concepts
            for other_concept in all_concepts:
                if other_concept.id != source_concept.id:
                    self._analyze_concept_pair(source_concept, other_concept)

        elif target_concept:
            # Analyze relationships between target and all other concepts
            for other_concept in all_concepts:
                if other_concept.id != target_concept.id:
                    self._analyze_concept_pair(other_concept, target_concept)

        else:
            # Analyze all pairs of concepts (up to a reasonable limit)
            max_pairs = min(len(all_concepts) * (len(all_concepts) - 1) // 2, 20)
            pairs_analyzed = 0

            for i, concept_a in enumerate(all_concepts):
                for concept_b in all_concepts[i + 1 :]:
                    if pairs_analyzed >= max_pairs:
                        break

                    self._analyze_concept_pair(concept_a, concept_b)
                    pairs_analyzed += 1

                if pairs_analyzed >= max_pairs:
                    break

        return self.graph

    def _analyze_concept_pair(self, concept_a: Concept, concept_b: Concept) -> None:
        """
        Analyze the relationship between two concepts and add any discovered relationships.

        Parameters:
        - concept_a: First concept
        - concept_b: Second concept
        """
        # Get available relation types
        relation_types = ", ".join(self.graph_spec.get_relation_types())

        # Extract relationship using LLM
        prompt = self.graph_spec.format_extraction_prompt(
            "relationship_extraction",
            concept_a_name=concept_a.name,
            concept_a_definition=concept_a.definition,
            concept_b_name=concept_b.name,
            concept_b_definition=concept_b.definition,
            relation_types=relation_types,
        )

        response = self.llm_client.complete(prompt=prompt)

        try:
            # Parse JSON response
            extracted_relationship = json.loads(response)

            # Only add if relationship is found
            if extracted_relationship and "relation_type" in extracted_relationship:
                relation_type = extracted_relationship.get("relation_type")
                description = extracted_relationship.get("description", "")
                confidence = extracted_relationship.get("confidence", 0.0)

                # Check confidence threshold
                min_confidence = self.graph_spec.get_processing_parameter(
                    "relationship_discovery", "min_confidence"
                )

                if confidence >= min_confidence:
                    # Add new relation type to config if it doesn't exist
                    relation_types_list = self.graph_spec.get_relation_types()
                    if relation_type not in relation_types_list:
                        self.graph_spec.add_relation_type(
                            relation_type,
                            f"Auto-discovered relationship: {description}",
                        )

                    relationship = Relationship(
                        source_id=concept_a.id,
                        source_type="concept",
                        target_id=concept_b.id,
                        target_type="concept",
                        relation_type=relation_type,
                        attributes={
                            "description": description,
                            "confidence": confidence,
                        },
                    )

                    # Add relationship to graph
                    self.graph.add_relationship(relationship)

        except (json.JSONDecodeError, TypeError):
            print(
                f"Failed to parse relationship between {concept_a.name} and {concept_b.name}"
            )

    def generate_graph(self) -> KnowledgeGraph:
        """Convenience method to generate the complete graph"""
        return self.graph
