import json
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path

from graph.models import Concept, SubConcept, KnowledgeBlock, SourceData, Relationship
from graph.graph import KnowledgeGraph
from graph.spec import GraphSpec
from utils.json_utils import extract_json_array

from llm.factory import LLMInterface


class DocBuilder:
    """
    A builder class for constructing knowledge graphs from documents.
    """

    def __init__(self, llm_client: LLMInterface, graph: Optional[KnowledgeGraph] = None):
        """
        Initialize the builder with a graph instance and specifications.
        """

        self.graph = graph
        self.llm_client = llm_client
        self.discovered_concepts = []
        self.knowledge_blocks = []
        self.sources = []
        self.graph_spec = GraphSpec()

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

            source_data = SourceData(
                name=name,
                definition=f"Document: {name}{extension}",
                link=path,
                version=metadata.get("doc_version", "1.0"),
            )

            # Add document to graph
            source_data_id = self.graph.add_source_data(source_data)
            self.sources.append(source_data)

            # Extract knowledge blocks using LLM
            prompt_template = self.graph_spec.get_extraction_prompt(
                "knowledge_block_extraction"
            )
            prompt = prompt_template.format(text=doc_content)
            response = self.llm_client.generate(prompt)

            try:
                response_json_str = extract_json_array(response)
                # Parse JSON response
                extracted_blocks = json.loads(response_json_str)

                # Create and add knowledge blocks
                for block_data in extracted_blocks:
                    kb = KnowledgeBlock(
                        name=block_data.get("name") or block_data.get("question", ""),
                        definition=block_data.get("definition", "")
                        or block_data.get("answer", ""),
                        source_version=metadata.get("doc_version", "1.0"),
                        source_ids=[source_data_id],
                    )

                    # Add knowledge block to graph
                    self.graph.add_knowledge_block(kb)
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

                self.discovered_concepts.extend(concepts)
                return concepts

            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error loading concepts from file: {e}")

        if not self.knowledge_blocks:
            print("No knowledge blocks available for concept extraction")
            return []

        # Combine knowledge blocks for analysis
        combined_blocks = "\n\n".join(
            [
                f"Block: {kb.name}\nContent: {kb.definition}"
                for kb in self.knowledge_blocks
            ]
        )

        # Extract concepts using LLM
        prompt_format = self.graph_spec.get_extraction_prompt("concept_extraction")
        prompt = prompt_format.format(text=combined_blocks)
        response = self.llm_client.generate(prompt)

        try:
            response_json_str = extract_json_array(response)
            # Parse JSON response
            extracted_concepts = json.loads(response_json_str)

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

        self.discovered_concepts.extend(concepts)
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
                    f"Block {kb.id}, name: {kb.name}\nContent: {kb.definition}"
                    for kb in self.knowledge_blocks
                ]
            )

            # Extract subconcepts using LLM
            prompt_format = self.graph_spec.get_extraction_prompt("extend_concept")
            prompt = prompt_format.format(
                concept_name=concept.name,
                concept_definition=concept.definition,
                text=combined_blocks,
            )

            response = self.llm_client.generate(prompt)

            try:
                # Parse JSON response
                response_json_str = extract_json_array(response)
                extracted_subconcepts = json.loads(response_json_str)

                # Create and add subconcepts
                for subconcept_data in extracted_subconcepts:
                    subconcept = SubConcept(
                        name=subconcept_data.get("name", ""),
                        definition=subconcept_data.get("definition", ""),
                        parent_concept_id=concept.id,
                        aspect_descriptor=subconcept_data.get("description", ""),
                        knowledge_block_ids=subconcept_data.get(
                            "knowledge_block_ids", []
                        ),
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

        combined_blocks = "\n\n".join(
            [
                f"Block {kb.id}, name: {kb.name}\nContent: {kb.definition}"
                for kb in self.knowledge_blocks
            ]
        )

        # Extract relationship using LLM
        prompt_format = self.graph_spec.get_extraction_prompt("extend_relationship")
        prompt = prompt_format.format(
            concept_a_name=concept_a.name,
            concept_a_definition=concept_a.definition,
            concept_b_name=concept_b.name,
            concept_b_definition=concept_b.definition,
            relation_types=relation_types,
            text=combined_blocks,
        )

        response = self.llm_client.complete(prompt=prompt)

        try:
            response_json_str = extract_json_array(response)
            # Parse JSON response
            extracted_relationship = json.loads(response_json_str)

            # Only add if relationship is found
            if extracted_relationship and "relation_type" in extracted_relationship:
                relation_type = extracted_relationship.get("relation_type")
                description = extracted_relationship.get("description", "")
                confidence = extracted_relationship.get("confidence", 0.0)
                knowledge_block_ids = extracted_relationship.get(
                    "knowledge_block_ids", []
                )

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
                            "knowledge_block_ids": knowledge_block_ids,
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
