import json
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from pathlib import Path
from math import ceil


from graph.models import Concept, SubConcept, KnowledgeBlock, SourceData, Relationship
from graph.graph import KnowledgeGraph
from graph.spec import GraphSpec
from utils.json_utils import extract_json_array
from utils.token import calculate_tokens
from setting.db import SessionLocal
from llm.factory import LLMInterface


class DocBuilder:
    """
    A builder class for constructing knowledge graphs from documents.
    """

    def __init__(
        self,
        llm_client: LLMInterface,
        embedding_func: Callable,
    ):
        """
        Initialize the builder with a graph instance and specifications.
        """
        self.embedding_func = embedding_func
        self.llm_client = llm_client
        self.graph_spec = GraphSpec(llm_client)

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

    def split_markdown_by_heading(
        self, path: str, metadata: Dict[str, Any], heading_level=2
    ):
        # Split content by lines
        name, extension = self._extract_file_info(path)
        doc_content = self._read_file(path)
        doc_version = metadata.get("doc_version", "1.0")

        markdown_content = self._read_file(path)
        lines = markdown_content.split("\n")

        sections = {}
        current_section = []
        current_title = "default"

        for line in lines:
            # Check if line is a h2 heading
            if line.startswith("#" * heading_level + " "):
                # Save current section if it has content
                if current_section:
                    sections[current_title] = "\n".join(current_section)
                    current_section = []

                # Update current title (remove '## ' prefix)
                current_title = line[3:].strip()
            else:
                current_section.append(line)

        # Save the last section
        if current_section:
            sections[current_title] = "\n".join(current_section)

        for heading, content in sections.items():
            tokens = calculate_tokens(content)
            if tokens > 4096:
                raise ValueError(
                    f"Heading {heading} has {tokens} tokens, please split it into smaller chunks manually"
                )

        # Add document and knowledge blocks to database
        with SessionLocal() as db:
            source_data = db.query(SourceData).filter(SourceData.link == path).first()
            if not source_data:
                source_data = SourceData(
                    name=name,
                    content=markdown_content,
                    link=path,
                    version=doc_version,
                    data_type="document",
                    metadata=metadata,
                )
                db.add(source_data)
                db.flush()
                source_data_id = source_data.id
                print(f"Source data created for {path}, id: {source_data_id}")
            else:
                print(f"Source data already exists for {path}, id: {source_data.id}")
                source_data_id = source_data.id

            knowledge_blocks = (
                db.query(KnowledgeBlock)
                .filter(
                    KnowledgeBlock.source_id == source_data_id,
                    KnowledgeBlock.knowledge_type == "paragraph",
                    KnowledgeBlock.source_version == doc_version,
                )
                .all()
            )
            if knowledge_blocks:
                print(f"Knowledge blocks already exist for {path}")
                return sections

            for heading, content in sections.items():
                kb = KnowledgeBlock(
                    name=heading,
                    content="#" * heading_level + f" {heading}\n{content}",
                    knowledge_type="paragraph",
                    content_vec=self.embedding_func(content),
                    source_version=metadata.get("doc_version", "1.0"),
                    source_id=source_data_id,
                )
                db.add(kb)

            db.commit()

        return sections

    def extract_qa_blocks(
        self, file_path: Union[str, List[str]], metadata: Dict[str, Any]
    ) -> List[KnowledgeBlock]:
        # Handle single file or list of files
        if isinstance(file_path, str):
            file_paths = [file_path]
        else:
            file_paths = file_path

        doc_version = metadata.get("doc_version", "1.0")
        blocks = []
        for path in file_paths:
            # Create document entity
            name, extension = self._extract_file_info(path)
            doc_content = self._read_file(path)


            # Extract knowledge blocks using LLM
            prompt_template = self.graph_spec.get_extraction_prompt(
                "knowledge_qa_extraction"
            )
            prompt = prompt_template.format(text=doc_content)
            response = self.llm_client.generate(prompt)

            try:
                response_json_str = extract_json_array(response)
                # Parse JSON response
                extracted_blocks = json.loads(response_json_str)

                with SessionLocal() as db:
                    source_data = (
                        db.query(SourceData).filter(SourceData.link == path).first()
                    )
                    if not source_data:
                        source_data = SourceData(
                            name=name,
                            content=doc_content,
                            link=path,
                            version=doc_version,
                            data_type="document",
                            metadata=metadata,
                        )
                        db.add(source_data)
                        db.flush()
                        source_data_id = source_data.id
                        print(f"Source data created for {path}, id: {source_data_id}")
                    else:
                        print(f"Source data already exists for {path}, id: {source_data.id}")
                        source_data_id = source_data.id

                    knowledge_blocks = (
                        db.query(KnowledgeBlock)
                        .filter(
                            KnowledgeBlock.source_id == source_data_id,
                            KnowledgeBlock.knowledge_type == "qa",
                            KnowledgeBlock.source_version == doc_version,
                        )
                        .all()
                    )
                    if knowledge_blocks:
                        print(f"Knowledge blocks already exist for {path}")
                        continue

                    # Create and add knowledge blocks
                    for block_data in extracted_blocks:
                        question = block_data.get("question", "")
                        answer = block_data.get("answer", "")
                        qa_content = question + "\n" + answer
                        qa_block = KnowledgeBlock(
                            name=question,
                            definition=qa_content,
                            source_version=doc_version,
                            source_id=source_data_id,
                            knowledge_type="qa",
                            content_vec=self.embedding_func(qa_content),
                        )
                        db.add(qa_block)
                        blocks.append(qa_content)
                    db.commit()

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

                with SessionLocal() as db:
                    for concept_data in predefined_concepts:
                        concept = Concept(
                            name=concept_data.get("name", ""),
                            definition=concept_data.get("definition", ""),
                            definition_vec=self.embedding_func(concept_data.get("definition", "")),
                            version=concept_data.get("version", "1.0"),
                        )
                        db.add(concept)

                    db.commit()

                return predefined_concepts
            except Exception as e:
                raise ValueError(f"Error loading concepts from file: {e}")

        with SessionLocal() as db:
            knowledge_blocks = db.query(KnowledgeBlock.name, KnowledgeBlock.content).filter().all()
            if not knowledge_blocks:
                print("No knowledge blocks available for concept extraction")
                return []


            # split knowledges block into batches that have 10000 tokens
            total_tokens = 0
            for i, kb in enumerate(knowledge_blocks):
                tokens = calculate_tokens(kb.content)
                total_tokens += tokens

            knowledge_blocks_batches = []
            index = 0
            batch_size = ceil(total_tokens/(ceil(total_tokens/10000)))
            for kb in knowledge_blocks:
                if total_tokens > batch_size:
                    knowledge_blocks_batches.append(knowledge_blocks[index:i+1])
                    index = i+1
                    total_tokens = 0

            if index < len(knowledge_blocks):
                knowledge_blocks_batches.append(knowledge_blocks[index:])

            print(f"Splitted {len(knowledge_blocks_batches)} batches")

            for batches in knowledge_blocks_batches:
                # Combine knowledge blocks for analysis
                combined_blocks = "\n\n".join(
                    [
                        f"Block: {kb.name}\nContent: {kb.content}"
                        for kb in batches
                    ]
                )

                if combined_blocks.strip() == "":
                    print(f"Skipping empty batch")
                    continue

                # Extract concepts using LLM
                prompt_format = self.graph_spec.get_extraction_prompt("concept_extraction")
                prompt = prompt_format.format(text=combined_blocks)
                try:
                    response = self.llm_client.generate(prompt)
                except Exception as e:
                    print(f"Failed to extract concepts from {combined_blocks}, error: {e}")
                    import time
                    time.sleep(60)
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
                            definition_vec=self.embedding_func(concept_data.get("definition", "")),
                            version="1.0",
                        )
                        db.add(concept)
                    concepts.append(extracted_concepts)
                    print(f"Extracted {len(extracted_concepts)} concepts")
                except (json.JSONDecodeError, TypeError):
                    print("Failed to parse concepts from LLM response")
            db.commit()

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

        # Create a mapping from concept to its subconcepts
        concept_to_subconcepts = {}
        for subconcept_id, subconcept in self.graph.subconcepts.items():
            parent_concept_id = subconcept.parent_concept_id
            if parent_concept_id:
                if parent_concept_id not in concept_to_subconcepts:
                    concept_to_subconcepts[parent_concept_id] = []
                concept_to_subconcepts[parent_concept_id].append(subconcept_id)

        # Create a mapping from subconcept to knowledge blocks
        subconcept_to_blocks = {}
        for subconcept_id, subconcept in self.graph.subconcepts.items():
            knowledge_block_ids = subconcept.knowledge_block_ids
            if knowledge_block_ids:
                subconcept_to_blocks[subconcept_id] = knowledge_block_ids

        # Skip if either concept has no subconcepts
        if (concept_a.id not in concept_to_subconcepts) or (
            concept_b.id not in concept_to_subconcepts
        ):
            return

        # Get knowledge blocks for each concept through its subconcepts
        blocks_for_concept_a = set()
        for subconcept_id in concept_to_subconcepts[concept_a.id]:
            if subconcept_id in subconcept_to_blocks:
                blocks_for_concept_a.update(subconcept_to_blocks[subconcept_id])

        blocks_for_concept_b = set()
        for subconcept_id in concept_to_subconcepts[concept_b.id]:
            if subconcept_id in subconcept_to_blocks:
                blocks_for_concept_b.update(subconcept_to_blocks[subconcept_id])

        # Find shared knowledge blocks
        shared_blocks = blocks_for_concept_a.intersection(blocks_for_concept_b)
        if not shared_blocks:
            return

        # Collect knowledge block content for analysis
        shared_blocks_content = []
        for block_id in shared_blocks:
            kb = self.graph.get_knowledge_block(block_id)
            if kb:
                shared_blocks_content.append(
                    f"Block {kb.id}, name: {kb.name}\nContent: {kb.definition}"
                )

        # Analyze relationship using LLM if shared blocks are found
        if shared_blocks_content:
            shared_blocks_text = "\n\n".join(shared_blocks_content)

            # Get available relation types
            relation_types = ", ".join(self.graph_spec.get_relation_types())

            # Extract relationship using LLM
            prompt_format = self.graph_spec.get_extraction_prompt("extend_relationship")
            prompt = prompt_format.format(
                concept_a_name=concept_a.name,
                concept_a_definition=concept_a.definition,
                concept_b_name=concept_b.name,
                concept_b_definition=concept_b.definition,
                relation_types=relation_types,
                text=shared_blocks_text,
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
                                "knowledge_block_ids": list(shared_blocks),
                            },
                        )

                        # Add relationship to graph
                        self.graph.add_relationship(relationship)
                        relationship_count += 1
                        print(
                            f"Added relationship between '{concept_a.name}' and '{concept_b.name}': {relation_type}"
                        )

            except (json.JSONDecodeError, TypeError):
                print(
                    f"Failed to parse relationship between {concept_a.name} and {concept_b.name}"
                )

        print(
            f"Created {relationship_count} concept-to-concept relationships based on shared knowledge"
        )
        return self.graph
