import json
import copy
from typing import Dict, List, Any, Union, Callable

from knowledge_graph.models import Concept, Relationship, KnowledgeBlock, SourceData
from knowledge_graph.utils import gen_situate_context
from utils.json_utils import extract_json_array, extract_json
from utils.token import calculate_tokens
from setting.db import SessionLocal
from llm.factory import LLMInterface
from knowledge_graph.parser import Block, get_parser
from knowledge_graph.prompts.hub import PromptHub


class KnowledgeBuilder:
    """
    A builder class for constructing knowledge graphs from documents.
    """

    def __init__(self, llm_client: LLMInterface, embedding_func: Callable):
        """
        Initialize the builder with a graph instance and specifications.
        """
        self.embedding_func = embedding_func
        self.llm_client = llm_client
        self.prompt_hub = PromptHub()

    def extract_knowledge_blocks(self, path: str, attributes: Dict[str, Any], **kwargs):
        # Extract basic info of source
        doc_version = attributes.get("doc_version", "1.0")
        doc_link = attributes.get("doc_link", path)

        # find suitable parser to parse knowledge
        parser = get_parser(path)
        doc_knowledge = parser.parse(path, **kwargs)

        blocks = doc_knowledge.blocks
        full_content = doc_knowledge.content
        name = doc_knowledge.name

        if doc_knowledge.blocks is None or len(doc_knowledge.blocks) == 0:
            blocks = [Block(name=name, content=full_content, position=1)]
        else:
            blocks = doc_knowledge.blocks

        for block in blocks:
            content = block.content
            tokens = calculate_tokens(content)
            if tokens > 4096:
                # TODO: Consider making 4096 configurable or handling splitting differently
                raise ValueError(
                    f"Section '{block.name}' including parent context has {tokens} tokens, exceeding 4096. Please restructure the document."
                )

        # Generate situated context for each section\
        # Add document and knowledge blocks to database
        section_context = {}
        with SessionLocal() as db:
            source_data = (
                db.query(SourceData)
                .filter(
                    SourceData.link == doc_link and SourceData.version == doc_version
                )
                .first()
            )
            if not source_data:
                for block in blocks:
                    # gen_situate_context expects the original doc and the specific block content
                    # We provide the full content of the section (including parent context) as the "block"
                    # This assumes gen_situate_context can handle this structure appropriately
                    section_context[block.name] = gen_situate_context(
                        full_content, block.content
                    )
            else:
                print(f"Source data already exists for {path}, id: {source_data.id}")
                return blocks

        # Add document and knowledge blocks to database
        with SessionLocal() as db:
            source_data = (
                db.query(SourceData).filter(SourceData.link == doc_link).first()
            )
            if not source_data:
                source_data = SourceData(
                    name=name,
                    content=full_content,  # Store original full content
                    link=doc_link,
                    version=doc_version,
                    data_type="document",
                    attributes=attributes,
                )
                db.add(source_data)
                db.flush()  # Flush to get the ID
                source_data_id = source_data.id
                print(f"Source data created for {path}, id: {source_data_id}")
            elif source_data.version != doc_version:
                print(f"Update source data - path: {path}, id: {source_data.id}")
                source_data.content = full_content
                source_data.version = doc_version
                source_data.attributes = attributes
                db.add(source_data)
                db.flush()
                source_data_id = source_data.id
            else:
                raise ValueError(
                    f"Source data already exists for {path}, id: {source_data.id}"
                )

            # Check if knowledge blocks for this version already exist
            existing_kbs = (
                db.query(KnowledgeBlock.name)
                .filter(
                    KnowledgeBlock.source_id == source_data_id,
                    KnowledgeBlock.knowledge_type == "paragraph",
                    KnowledgeBlock.source_version == doc_version,
                )
                .all()
            )
            existing_kb_names = {kb.name for kb in existing_kbs}

            if existing_kb_names == set([block.name for block in blocks]):
                print(
                    f"Knowledge blocks already exist for {path} version {doc_version}"
                )
                return blocks  # Return the newly structured blocks

            print(f"Generating knowledge blocks for {path} version {doc_version}")

            for block in blocks:
                context = section_context.get(block.name, None)
                content_str = block.content
                content_position = block.position

                # Generate embedding based on context + block content
                if context:
                    embedding_input = f"<context>\n{context}</context>\n\n{content_str}"
                else:
                    embedding_input = content_str

                content_vec = self.embedding_func(embedding_input)
                kb = KnowledgeBlock(
                    name=block.name,
                    context=context,
                    content=content_str,
                    knowledge_type="paragraph",
                    content_vec=content_vec,
                    source_version=doc_version,
                    source_id=source_data_id,
                    position_in_source=content_position,
                )
                db.add(kb)

            db.commit()

        return blocks  # Return the sections dictionary

    def extract_qa_blocks(
        self, file_path: Union[str, List[str]], attributes: Dict[str, Any], **kwargs
    ) -> List[KnowledgeBlock]:
        doc_version = attributes.get("doc_version", "1.0")
        doc_link = attributes.get("doc_link", file_path)
        doc_knowledge = self.parser(file_path, **kwargs)
        doc_content = doc_knowledge.content
        name = doc_knowledge.name

        # Extract knowledge blocks using LLM
        prompt_template = self.prompt_hub.get_prompt("knowledge_qa_extraction")
        prompt = prompt_template.format(text=doc_content)
        response = self.llm_client.generate(prompt)

        try:
            response_json_str = extract_json_array(response)
            # Parse JSON response
            extracted_qa_pairs = json.loads(response_json_str)

            with SessionLocal() as db:
                source_data = (
                    db.query(SourceData).filter(SourceData.link == file_path).first()
                )
                if not source_data:
                    source_data = SourceData(
                        name=name,
                        content=doc_content,
                        link=doc_link,
                        version=doc_version,
                        data_type="document",
                        attributes=attributes,
                    )
                    db.add(source_data)
                    db.flush()
                    source_data_id = source_data.id
                    print(f"Source data created for {file_path}, id: {source_data_id}")
                else:
                    print(
                        f"Source data already exists for {file_path}, id: {source_data.id}"
                    )
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
                    raise ValueError(f"Knowledge blocks already exist for {file_path}")

                # Create and add knowledge blocks
                for block_data in extracted_qa_pairs:
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
                db.commit()

        except (json.JSONDecodeError, TypeError):
            print(f"Failed to parse knowledge blocks from {file_path}")

        return extracted_qa_pairs

    def extract_knowledge_index(self, path: str, attributes: Dict[str, Any], **kwargs):
        # Extract basic info
        doc_version = attributes.get("doc_version", "1.0")
        doc_link = attributes.get("doc_link", path)
        # find suitable parser to parse knowledge
        parser = get_parser(path)
        kb = parser.parse(path, **kwargs)

        def get_node_attributes(node):
            references = []
            for child in node.children:
                if len(child.children) > 0:
                    raise ValueError(
                        "Reference node should be the leaf node without any children"
                    )

                references.append(child.name)

            return references

        def depth_traversal(root, current_path: list):
            if root.name == "Reference":
                return [
                    {
                        "path": copy.deepcopy(current_path),
                        "references": get_node_attributes(root),
                    }
                ]
            elif root.name == "Definition":
                return [
                    {
                        "path": copy.deepcopy(current_path),
                        "definition": get_node_attributes(root),
                    }
                ]
            elif root.name == "Annotation":
                return [
                    {
                        "path": copy.deepcopy(current_path),
                        "annotation": get_node_attributes(root),
                    }
                ]

            all_paths = []
            for child in root.children:
                curent_path_copy = copy.deepcopy(current_path)
                all_paths.extend(depth_traversal(child, curent_path_copy + [root.name]))

            return all_paths

        # Process all knowledge indexes
        all_knowledges = {}
        for index in kb.indexes:
            paths = depth_traversal(index, [])
            for path_data in paths:
                if not path_data:  # Skip empty results
                    continue
                path_str = "->".join(path_data["path"])
                if path_str not in all_knowledges:
                    all_knowledges[path_str] = {}

                for key, value in path_data.items():
                    all_knowledges[path_str][key] = value

        # No knowledge found
        if not all_knowledges:
            print("No knowledge extracted from the file")
            return None

        # Collect all reference sources in one pass
        reference_source_names = set()
        for knowledge in all_knowledges.values():
            reference_source_names.update(knowledge.get("references", []))

        print("all knowledge", all_knowledges)

        # Get all sources in a single database query
        source_map = {}
        if reference_source_names:
            with SessionLocal() as db:
                sources = (
                    db.query(SourceData)
                    .where(SourceData.name.in_(list(reference_source_names)))
                    .all()
                )

            # Create a lookup map for sources
            source_map = {
                source.name: {
                    "id": source.id,
                    "name": source.name,
                    "link": source.link,
                    "version": source.version,
                    "content": source.content,
                }
                for source in sources
            }

        print("source", source_map)

        # Process each knowledge item
        results = []
        for knowledge in all_knowledges.values():
            invalid_references = []
            valid_references = []

            if "references" in knowledge:
                for reference in knowledge["references"]:
                    if reference not in source_map:
                        invalid_references.append(reference)
                    else:
                        valid_references.append(source_map[reference])

            if invalid_references:
                print(
                    f"skip knowledge {knowledge}, caused by lack of references {invalid_references}"
                )
                continue

            prompt_template = self.prompt_hub.get_prompt(
                "from_knowledge_index_graph_extraction"
            )
            prompt = prompt_template.format(
                knowledge=knowledge, reference_documents=valid_references
            )

            response = self.llm_client.generate(prompt)
            subgraph_json_str = extract_json(response)
            subgraph = json.loads(subgraph_json_str)

            with SessionLocal() as db:
                # First check if concepts with these names already exist
                existing_concepts = {}
                concept_names = [entity["name"] for entity in subgraph["entities"]]
                if concept_names:
                    for existing in (
                        db.query(Concept).filter(Concept.name.in_(concept_names)).all()
                    ):
                        existing_concepts[existing.name] = existing

                # Create new concepts only for those that don't exist
                new_concepts = []
                concept_map = (
                    {}
                )  # Will map concept names to their IDs (either existing or new)

                for entity in subgraph["entities"]:
                    if entity["name"] in existing_concepts:
                        # Use existing concept
                        concept = existing_concepts[entity["name"]]
                        concept_map[entity["name"]] = concept.id
                        print(f"Using existing concept: {entity['name']}")
                    else:
                        # Create new concept
                        concept = Concept(
                            name=entity["name"],
                            definition=entity["definition"],
                            definition_vec=self.embedding_func(entity["definition"]),
                            version="1.0",
                        )
                        new_concepts.append(concept)
                        print(f"Creating new concept: {entity['name']}")

                # Add new concepts to database
                if new_concepts:
                    db.add_all(new_concepts)
                    db.flush()
                    # Update concept_map with IDs of new concepts
                    for concept in new_concepts:
                        concept_map[concept.name] = concept.id

                # Check for existing concept->source relationships
                existing_relationships = {}
                concept_ids = list(concept_map.values())
                source_ids = [source["id"] for source in valid_references]

                if concept_ids and source_ids:
                    for rel in (
                        db.query(Relationship)
                        .filter(
                            Relationship.source_id.in_(concept_ids),
                            Relationship.source_type == "Concept",
                            Relationship.target_id.in_(source_ids),
                            Relationship.target_type == "SourceData",
                            Relationship.relationship_type == "SOURCE_OF",
                        )
                        .all()
                    ):
                        # Key by (source_id, target_id) tuple
                        existing_relationships[(rel.source_id, rel.target_id)] = rel

                # Create only new relationships
                source_rel = []
                for concept_name, concept_id in concept_map.items():
                    for source in valid_references:
                        if (concept_id, source["id"]) not in existing_relationships:
                            print(
                                f"Creating new relationship: {concept_name} -> {source['name']}"
                            )
                            rel = Relationship(
                                source_id=concept_id,
                                source_type="Concept",
                                target_id=source["id"],
                                target_type="SourceData",
                                relationship_type="SOURCE_OF",
                            )
                            source_rel.append(rel)
                        else:
                            print(
                                f"Relationship already exists: {concept_name} -> {source['name']}"
                            )

                if source_rel:
                    db.add_all(source_rel)

                # Check for existing concept-to-concept relationships
                concept_to_concept_rels = {}
                if concept_ids:
                    for rel in (
                        db.query(Relationship)
                        .filter(
                            Relationship.source_id.in_(concept_ids),
                            Relationship.source_type == "Concept",
                            Relationship.target_id.in_(concept_ids),
                            Relationship.target_type == "Concept",
                        )
                        .all()
                    ):
                        # Key by (source_id, target_id, relationship_type) tuple to handle different relationship types
                        concept_to_concept_rels[
                            (rel.source_id, rel.target_id, rel.relationship_type)
                        ] = rel

                # Create new concept-to-concept relationships
                concept_rels = []
                for relationship in subgraph["relationships"]:
                    source_name = relationship["source_entity"]
                    target_name = relationship["target_entity"]
                    rel_type = relationship.get("relationship_type", "REFERENCES")
                    rel_desc = relationship.get("definition", None)

                    # Skip if either concept is missing
                    if source_name not in concept_map or target_name not in concept_map:
                        print(
                            f"Skipping relationship: {source_name} -> {target_name} (missing concept)"
                        )
                        continue

                    source_id = concept_map[source_name]
                    target_id = concept_map[target_name]

                    # Check if this relationship already exists
                    if (source_id, target_id, rel_type) not in concept_to_concept_rels:
                        print(
                            f"Creating new concept relationship: {source_name} ({rel_type}) -> {target_name}"
                        )
                        rel = Relationship(
                            source_id=source_id,
                            source_type="Concept",
                            target_id=target_id,
                            target_type="Concept",
                            relationship_type=rel_type,
                            relationship_desc=rel_desc,
                            relationship_desc_vec=(
                                self.embedding_func(rel_desc) if rel_desc else None
                            ),
                            knowledge_bundle=[
                                {
                                    "id": k["id"],
                                    "name": k["name"],
                                    "link": k["link"],
                                    "version": k["version"],
                                }
                                for k in valid_references
                            ],
                        )
                        concept_rels.append(rel)
                    else:
                        print(
                            f"Relationship already exists: {source_name} ({rel_type}) -> {target_name}"
                        )

                if concept_rels:
                    db.add_all(concept_rels)

                db.commit()

            results.append(response)

        # Return all results or first result to maintain backward compatibility
        return results
