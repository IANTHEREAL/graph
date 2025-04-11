import json
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from pathlib import Path
from math import ceil

from knowledge_graph.models import Concept, KnowledgeBlock, SourceData, Relationship
from knowledge_graph.prompts.hub import PromptHub
from knowledge_graph.utils import gen_situate_context
from utils.json_utils import extract_json_array
from utils.token import calculate_tokens
from setting.db import SessionLocal
from llm.factory import LLMInterface
from knowledge_graph.parser import BaseParser, Block


class KnowledgeBlockBuilder:
    """
    A builder class for constructing knowledge graphs from documents.
    """

    def __init__(
        self, llm_client: LLMInterface, embedding_func: Callable, parser: BaseParser
    ):
        """
        Initialize the builder with a graph instance and specifications.
        """
        self.embedding_func = embedding_func
        self.llm_client = llm_client
        self.prompt_hub = PromptHub()
        self.parser = parser

    def extract_knowledge_blocks(
        self, path: str, attributes: Dict[str, Any], disbale_split=False, **kwargs
    ):
        # Extract basic info
        doc_version = attributes.get("doc_version", "1.0")
        doc_link = attributes.get("doc_link", path)

        doc_knowledge = self.parser.parse(path, **kwargs)
        blocks = doc_knowledge.blocks
        full_content = doc_knowledge.content
        name = doc_knowledge.name

        if disbale_split:
            blocks = [Block(name=name, content=full_content, position=1)]
        else:
            blocks = doc_knowledge.blocks

        # Validate token counts for each section (including parent context)
        for block in blocks:
            content = block.content
            tokens = calculate_tokens(content)
            if tokens > 4096:
                # Consider making 4096 configurable or handling splitting differently
                raise ValueError(
                    f"Section '{block.name}' including parent context has {tokens} tokens, exceeding 4096. Please restructure the document."
                )

        # Generate situated context for each section
        section_context = {}
        for block in blocks:
            # gen_situate_context expects the original doc and the specific block content
            # We provide the full content of the section (including parent context) as the "block"
            # This assumes gen_situate_context can handle this structure appropriately
            section_context[block.name] = gen_situate_context(
                full_content, block.content
            )

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
            else:
                # Optionally update existing source data content/version/attributes if needed
                print(f"Source data already exists for {path}, id: {source_data.id}")
                source_data_id = source_data.id

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

            # If not all exist, or some are missing, consider deleting old ones or handling updates.
            # For simplicity, let's assume we add missing ones or overwrite if behavior demands it.
            # Current logic just checks if *any* blocks exist and skips all if true.
            # Let's refine to add only if the set of names doesn't match exactly.
            print(f"Generating knowledge blocks for {path} version {doc_version}")

            for block in blocks:
                # Skip if this specific block already exists for the version
                # if heading in existing_kb_names:
                #     continue # Or update logic here if needed

                context = section_context.get(block.name, None)
                content_str = block.content
                content_position = block.position

                # Generate embedding based on context + section content
                if context:
                    embedding_input = f"<context>\n{context}</context>\n\n{content_str}"
                else:
                    embedding_input = content_str

                content_vec = self.embedding_func(embedding_input)
                # Assuming embedding_func might return list/tuple, get first element
                kb = KnowledgeBlock(
                    name=block.name,
                    context=context,
                    content=content_str,  # Store the full section content (with parent context)
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
        doc_link = attributes.get("doc_link", path)
        doc_knowledge = self.parser(path, **kwargs)
        doc_content = doc_knowledge.content
        name = doc_knowledge.name

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
                        link=doc_link,
                        version=doc_version,
                        data_type="document",
                        metadata=metadata,
                    )
                    db.add(source_data)
                    db.flush()
                    source_data_id = source_data.id
                    print(f"Source data created for {path}, id: {source_data_id}")
                else:
                    print(
                        f"Source data already exists for {path}, id: {source_data.id}"
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
                    raise ValueError(f"Knowledge blocks already exist for {path}")

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
