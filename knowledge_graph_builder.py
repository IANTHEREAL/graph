import pandas as pd
import uuid
import json
import os
from datetime import datetime

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

from utils.json_utils import extract_json_array, extract_json
from llm_inference.interface import LLMInterface


class KnowledgeGraphBuilder:
    def __init__(self, llm_client, storage_path):
        """
        Initialize the knowledge graph builder with a dataframe of QA pairs and documents

        Args:
            df: DataFrame with columns [question, answer, topic, source_name, source_link, is_valid]
            llm_provider: LLM provider to use
            llm_model: LLM model to use
        """

        self.llm_client = llm_client
        self.graph = nx.DiGraph()
        self.entities = {
            "document": {},
            "concept": {},
            "subconcept": {},
            "qa": {},
        }
        self.relationships = []

        if os.path.exists(storage_path):
            self.load_from_disk(storage_path)

    def save_to_disk(self, storage_path):
        """Save the knowledge graph builder to disk"""
        with open(storage_path, "w") as f:
            json.dump(
                {"entities": self.entities, "relationships": self.relationships}, f
            )

    def load_from_disk(self, storage_path):
        """Load the knowledge graph builder from disk"""
        with open(storage_path, "r") as f:
            data = json.load(f)
            self.entities = data["entities"]
            self.relationships = data["relationships"]

    def add_documents(self, df):
        """Extract all entities from the dataframe"""
        self._extract_document_entities(df)
        self._extract_qa_entities(df)

        return
        self._extract_topic_entities()
        self._extract_concept_entities()
        self._extract_subconcept_entities()

    def _extract_document_entities(self, df):
        """Extract document entities from the dataframe"""
        print("Extracting document entities...")

        # Group by source to avoid duplicates
        unique_docs = df[["source_name", "source_link"]].drop_duplicates()

        for _, row in unique_docs.iterrows():
            doc_id = str(uuid.uuid4())
            self.entities["document"][doc_id] = {
                "id": doc_id,
                "name": row["source_name"],
                "doc_link": row["source_link"],
                "is_valid": True,
                "doc_version": "FY2025",
                "created_at": datetime.now().isoformat(),
            }

        print(f"Extracted {len(self.entities['document'])} document entities")

    def _extract_qa_entities(self, df):
        """Extract QA entities from the dataframe"""
        print("Extracting QA entities...")

        for idx, row in df.iterrows():
            qa_id = str(uuid.uuid4())
            source_doc_id = next(
                (
                    doc_id
                    for doc_id, doc in self.entities["document"].items()
                    if doc["name"] == row["source_name"]
                ),
                None,
            )
            self.entities["qa"][qa_id] = {
                "id": qa_id,
                "name": row["question"],
                "definition": f"Q: {row['question']}\nA: {row['answer']}",
                "is_valid": row["is_valid"] if "is_valid" in row else True,
                "doc_version": "FY2025",
                "created_at": datetime.now().isoformat(),
                "source_doc_id": source_doc_id,
            }

            self.relationships.append(
                {
                    "source_id": qa_id,
                    "source_type": "QA",
                    "target_id": source_doc_id,
                    "target_type": "Document",
                    "relation_type": "EXPLAINS",
                    "attributes": {"excerpt": "", "start_pos": 0},
                }
            )

        print(f"Extracted {len(self.entities['qa'])} QA entities")

    def extract_concept(self, df):
        """Extract concept entities using LLM"""
        print("Extracting concept entities using LLM...")

        # Combine all questions and answers for context
        all_qa_text = "\n\n".join(
            [
                f"Question: {row['question']}\nAnswer: {row['answer']}"
                for _, row in df.iterrows()
            ]
        )

        prompt = f"""
Based on the following questions and answers, identify the key concepts mentioned.
For each concept, provide:
1. The concept name
2. A brief definition (if possible)

Return the results in JSON format as a list of objects with 'name' and 'definition' fields.

Questions and Answers:
{all_qa_text}

JSON Output (surround with ```json and ```):
```json
[
    {{
        "name": "concept_name",
        "definition": "concept_definition"
    }},
    ...
]
```"""

        response = self.llm_client.generate(prompt)

        try:
            concepts_json = extract_json_array(response)
            concepts = json.loads(concepts_json)
            for concept in concepts:
                concept_id = str(uuid.uuid4())
                self.entities["concept"][concept_id] = {
                    "id": concept_id,
                    "name": concept["name"],
                    "definition": concept.get("definition", ""),
                    "is_valid": True,
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                }
        except json.JSONDecodeError:
            print("Error parsing LLM response for concepts. Using manual extraction.")
            raise Exception(
                f"Error parsing LLM response for concepts. Using manual extraction. Data {response}"
            )

        print(f"Extracted {len(self.entities['concept'])} concept entities")

    def extract_subconcept_from_faq(self):
        """Extract subconcept entities from documents and QA pairs"""
        print("Extracting subconcept entities from documents and QA pairs...")

        # Get all concepts
        concepts = {
            concept["name"]: concept_id
            for concept_id, concept in self.entities["concept"].items()
        }

        # Process QA pairs to extract subconcepts
        for qa_id, qa in self.entities["qa"].items():
            qa_text = f"Q: {qa['name']}\nA: {qa['definition']}"

            # For each concept, check if it's mentioned in the QA
            for concept_name, concept_id in concepts.items():
                if concept_name.lower() in qa_text.lower():
                    print(f"Extracting subconcepts for {concept_name} in QA {qa_id}")
                    prompt = f"""Given this question and answer about {concept_name}:
{qa_text}

Extract specific aspects or subconcepts of {concept_name} mentioned in this text.
For each subconcept, provide:
1. A name (e.g., "{concept_name} definition", "How to action on {concept_name}", etc.)
2. A brief description extracted from the text
3. The subconcept type (one of: definition, formula, example, note, application)

Return the results in JSON format as a list of objects with 'name', 'definition', and 'sub_type' fields.
If no clear subconcepts are found, return an empty list.

JSON Output: (surround with ```json and ```):
```json
[
    {{
        "name": "concept_name",
        "definition": "concept_definition",
        "sub_type": "sub_type"
    }},
    ...
]
```"""

                    response = self.llm_client.generate(prompt)

                    try:
                        response_json_str = extract_json_array(response)
                        subconcepts = json.loads(response_json_str)
                        for subconcept in subconcepts:
                            subconcept_id = str(uuid.uuid4())
                            self.entities["subconcept"][subconcept_id] = {
                                "id": subconcept_id,
                                "name": subconcept["name"],
                                "definition": subconcept.get("definition", ""),
                                "sub_type": subconcept.get("sub_type", "definition"),
                                "is_valid": True,
                                "version": "1.0",
                                "created_at": datetime.now().isoformat(),
                                "parent_concept_id": concept_id,
                                "source_type": "QA",
                                "source_id": qa_id,
                            }

                            # Add relationship between concept and subconcept
                            self.relationships.append(
                                {
                                    "source_id": concept_id,
                                    "source_type": "Concept",
                                    "target_id": subconcept_id,
                                    "target_type": "SubConcept",
                                    "relation_type": "HAS_SUBCONCEPT",
                                    "attributes": {
                                        "sub_type": subconcept.get(
                                            "sub_type", "definition"
                                        ),
                                        "weight": 1.0,
                                    },
                                }
                            )

                            # Add relationship between subconcept and QA
                            self.relationships.append(
                                {
                                    "source_id": subconcept_id,
                                    "source_type": "SubConcept",
                                    "target_id": qa_id,
                                    "target_type": "QA",
                                    "relation_type": "EXPLAINS",
                                    "attributes": {
                                        "excerpt": qa_text[:100] + "...",
                                        "start_pos": 0,
                                    },
                                }
                            )
                    except json.JSONDecodeError:
                        print(
                            f"Error parsing LLM response for subconcepts of {concept_name} in QA {qa_id}."
                        )

        print(f"Extracted {len(self.entities['subconcept'])} subconcept entities")

    def enhance_subconcept_from_document(self, df):
        """Extract subconcept entities from documents and QA pairs"""
        print("Extracting subconcept entities from documents and QA pairs...")

        # Get all concepts
        concepts = {
            concept["name"]: concept_id
            for concept_id, concept in self.entities["concept"].items()
        }

        # Process document to extract subconcepts
        for doc_id, doc in self.entities["document"].items():
            # todo: read the
            doc_text = f"Document: {doc['name']}"

            # For each concept, check if it's mentioned in the QA
            for concept_name, concept_id in concepts.items():
                subconcepts = [
                    subconcept["name"]
                    for subconcept in self.entities["subconcept"].values()
                    if subconcept["parent_concept_id"] == concept_id
                ]
                # todo: check if the concept is already in the subconcepts
                if concept_name.lower() in doc_text.lower():
                    prompt = f"""Given this document:
{doc_text}

Extract specific aspects or subconcepts of {concept_name} mentioned in this text.

The existing subconcepts are:
{subconcepts}

For each subconcept, provide:
1. A name (e.g., "{concept_name} definition", "How to action on {concept_name}", etc.)
2. A brief description extracted from the text
3. The subconcept type (one of: definition, formula, example, note, application)

Return the results in JSON format as a list of objects with 'name', 'definition', and 'sub_type' fields.
If no clear subconcepts are found, return an empty list.

JSON Output: (surround with ```json and ```):
```json
[
    {{
        "name": "concept_name",
        "definition": "concept_definition",
        "sub_type": "sub_type"
    }},
    ...
]
```"""

                    response = self.llm_client.generate(prompt)

                    try:
                        response_json_str = extract_json_array(response)
                        subconcepts = json.loads(response_json_str)
                        for subconcept in subconcepts:
                            subconcept_id = str(uuid.uuid4())
                            self.entities["subconcept"][subconcept_id] = {
                                "id": subconcept_id,
                                "name": subconcept["name"],
                                "definition": subconcept.get("definition", ""),
                                "sub_type": subconcept.get("sub_type", "definition"),
                                "is_valid": True,
                                "version": "1.0",
                                "created_at": datetime.now().isoformat(),
                                "parent_concept_id": concept_id,
                                "source_type": "Document",
                                "source_id": doc_id,
                            }

                            # Add relationship between concept and subconcept
                            self.relationships.append(
                                {
                                    "source_id": concept_id,
                                    "source_type": "Concept",
                                    "target_id": subconcept_id,
                                    "target_type": "SubConcept",
                                    "relation_type": "HAS_SUBCONCEPT",
                                    "attributes": {
                                        "sub_type": subconcept.get(
                                            "sub_type", "definition"
                                        ),
                                        "weight": 1.0,
                                    },
                                }
                            )

                            # Add relationship between subconcept and QA
                            self.relationships.append(
                                {
                                    "source_id": subconcept_id,
                                    "source_type": "SubConcept",
                                    "target_id": doc_id,
                                    "target_type": "QA",
                                    "relation_type": "EXPLAINS",
                                    "attributes": {
                                        "excerpt": doc_text[:100] + "...",
                                        "start_pos": 0,
                                    },
                                }
                            )
                    except json.JSONDecodeError:
                        print(
                            f"Error parsing LLM response for subconcepts of {concept_name} in QA {doc_id}."
                        )

        # Process documents to extract subconcepts
        # This would require document content, which we don't have directly in the dataframe
        # If you have document content available, you can add similar processing here

        print(f"Extracted {len(self.entities['subconcept'])} subconcept entities")

    def link_concepts_to_concepts(self):
        """Link concept entities based on shared QAs through their subconcepts"""
        print("Linking concepts based on shared QAs through subconcepts...")

        # Get all concepts
        concepts = list(self.entities["concept"].items())
        if len(concepts) < 2:
            return

        # Create a mapping from concept to its subconcepts
        concept_to_subconcepts = {}
        for subconcept_id, subconcept in self.entities["subconcept"].items():
            parent_concept_id = subconcept.get("parent_concept_id")
            if parent_concept_id:
                if parent_concept_id not in concept_to_subconcepts:
                    concept_to_subconcepts[parent_concept_id] = []
                concept_to_subconcepts[parent_concept_id].append(subconcept_id)

        # Create a mapping from subconcept to QAs
        subconcept_to_qas = {}
        for rel in self.relationships:
            if (
                rel["source_type"] == "SubConcept"
                and rel["target_type"] == "QA"
                and rel["relation_type"] == "EXPLAINS"
            ):
                subconcept_id = rel["source_id"]
                qa_id = rel["target_id"]
                if subconcept_id not in subconcept_to_qas:
                    subconcept_to_qas[subconcept_id] = []
                subconcept_to_qas[subconcept_id].append(qa_id)

        # For each pair of concepts, find shared QAs through their subconcepts
        for i, (concept_id1, concept1) in enumerate(concepts):
            for concept_id2, concept2 in concepts[i + 1 :]:
                # Skip if either concept has no subconcepts
                if (
                    concept_id1 not in concept_to_subconcepts
                    or concept_id2 not in concept_to_subconcepts
                ):
                    print(
                        f"Skipping {concept1['name']} and {concept2['name']} because they have no subconcepts"
                    )
                    continue

                print(f"Linking {concept1['name']} and {concept2['name']}")

                # Get QAs for each concept through its subconcepts
                qas_for_concept1 = set()
                for subconcept_id in concept_to_subconcepts[concept_id1]:
                    if subconcept_id in subconcept_to_qas:
                        qas_for_concept1.update(subconcept_to_qas[subconcept_id])

                qas_for_concept2 = set()
                for subconcept_id in concept_to_subconcepts[concept_id2]:
                    if subconcept_id in subconcept_to_qas:
                        qas_for_concept2.update(subconcept_to_qas[subconcept_id])

                # Find shared QAs
                shared_qas = qas_for_concept1.intersection(qas_for_concept2)
                if len(shared_qas) == 0:
                    print(
                        f"Skipping {concept1['name']} and {concept2['name']} because they have no shared QAs"
                    )
                    continue

                if shared_qas:
                    # Collect QA content for analysis
                    shared_qa_texts = []
                    for qa_id in shared_qas:
                        qa = self.entities["qa"].get(qa_id)
                        if qa:
                            shared_qa_texts.append(
                                f"Q: {qa.get('question', '')}\nA: {qa.get('answer', '')}"
                            )

                    # Use LLM to analyze the relationship based on shared QAs
                    shared_qa_texts_str = "\n\n".join(shared_qa_texts)
                    prompt = f"""I have two concepts that appear in the same QA pairs:
    Concept 1: {concept1['name']} - {concept1.get('definition', '')}
    Concept 2: {concept2['name']} - {concept2.get('definition', '')}
    
    These concepts appear together in the following QA pairs:
    {shared_qa_texts_str}
    
    Based on these QA pairs, determine the relationship between these two concepts.
    Provide:
    1. The relationship type (e.g., "is a part of", "is calculated from", "is related to")
    2. A detail description of the relationship
    3. A confidence score (0.0-1.0) for this relationship
    
    Return the result in JSON format with 'relation_type', 'description', and 'confidence' fields.
    
    JSON Output (surround with ```json and ```):
    ```json
    {{
        "relation_type": "relationship_type",
        "description": "relationship_description",
        "confidence": 0.0-1.0
    }}
    ```"""

                    response = self.llm_client.generate(prompt)

                    try:
                        response_json_str = extract_json(response)
                        relationship = json.loads(response_json_str)

                        # Add relationship if confidence is high enough
                        if relationship.get("confidence", 0) > 0.6:
                            self.relationships.append(
                                {
                                    "source_id": concept_id1,
                                    "source_type": "Concept",
                                    "target_id": concept_id2,
                                    "target_type": "Concept",
                                    "relation_type": relationship.get(
                                        "relation_type", "is related to"
                                    ),
                                    "attributes": {
                                        "shared_qa": shared_qas,
                                        "description": relationship.get(
                                            "description", ""
                                        ),
                                        "confidence": relationship.get(
                                            "confidence", 0.7
                                        ),
                                    },
                                }
                            )

                            print(
                                f"Added relationship between {concept1['name']} and {concept2['name']}: {relationship.get('relation_type', 'is related to')}"
                            )
                    except json.JSONDecodeError:
                        print(
                            f"Error parsing LLM response for relationship between {concept1['name']} and {concept2['name']}."
                        )

        print(
            f"Created {sum(1 for rel in self.relationships if rel['relation_type'] == 'RELATED_TO')} concept-to-concept relationships"
        )

    def build_graph(self):
        """Build the knowledge graph using the extracted entities and relationships"""
        print("Building knowledge graph...")

        # Add nodes to the graph
        for entity_type, entities in self.entities.items():
            for entity_id, entity in entities.items():
                self.graph.add_node(entity_id, **entity, entity_type=entity_type)

        # Add edges to the graph
        for rel in self.relationships:
            self.graph.add_edge(
                rel["source_id"],
                rel["target_id"],
                relation_type=rel["relation_type"],
                source_type=rel["source_type"],
                target_type=rel["target_type"],
                # add remain fields in rel
                **{
                    k: v
                    for k, v in rel.items()
                    if k
                    not in [
                        "source_id",
                        "target_id",
                        "relation_type",
                        "source_type",
                        "target_type",
                    ]
                },
            )

        print(
            f"Built graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges"
        )
        return self.graph

    def visualize_graph(self, output_file="knowledge_graph.png", layout_type="grouped"):
        """
        Visualize the knowledge graph

        Args:
            output_file: Path to save the visualization
            layout_type: Type of layout to use ('spring', 'circular', 'grouped', 'hierarchical')
        """
        print("Visualizing knowledge graph...")

        plt.figure(figsize=(30, 30))

        # Define node colors by entity type
        color_map = {
            "document": "skyblue",
            "concept": "lightgreen",
            "subconcept": "lightcoral",
            "qa": "lightyellow",
        }

        # Group nodes by entity type
        node_groups = {}
        for node in self.graph.nodes:
            entity_type = self.graph.nodes[node].get("entity_type", "Unknown")
            if entity_type not in node_groups:
                node_groups[entity_type] = []
            node_groups[entity_type].append(node)

        node_colors = [
            color_map.get(self.graph.nodes[node].get("entity_type", "Unknown"), "gray")
            for node in self.graph.nodes
        ]

        # Define node labels - escape dollar signs to avoid matplotlib math mode
        node_labels = {}
        for node in self.graph.nodes:
            name = str(self.graph.nodes[node]["name"]).replace("$", "\$")
            node_labels[node] = name

        # Define edge labels - escape dollar signs
        edge_labels = {}
        for u, v in self.graph.edges:
            if "description" in self.graph.edges[u, v]:
                label = f"{self.graph.edges[u, v]['relation_type']}({self.graph.edges[u, v]['description']})"
                edge_labels[(u, v)] = label.replace("$", "\$")
            elif "relation_type" in self.graph.edges[u, v]:
                label = str(self.graph.edges[u, v]["relation_type"]).replace("$", "\$")
                edge_labels[(u, v)] = label

        # Choose layout based on layout_type
        if layout_type == "spring":
            # Spring layout with more space between nodes
            pos = nx.spring_layout(self.graph, k=2.0, iterations=100, seed=42)
        elif layout_type == "circular":
            # Circular layout
            pos = nx.circular_layout(self.graph, scale=2.0)
        elif layout_type == "hierarchical":
            # Hierarchical layout (if networkx-compatible)
            try:
                pos = nx.multipartite_layout(self.graph, subset_key="entity_type")
            except:
                pos = nx.spring_layout(self.graph, k=2.0, iterations=100, seed=42)
        elif layout_type == "grouped":
            # Custom grouped layout by entity type
            pos = {}
            radius = 5.0

            # Position nodes in groups by entity type
            for i, (entity_type, nodes) in enumerate(node_groups.items()):
                # Calculate angle for this group
                angle = 2 * 3.14159 * i / len(node_groups)
                # Calculate center position for this group
                group_x = radius * 1.5 * np.cos(angle)
                group_y = radius * 1.5 * np.sin(angle)

                # Position nodes in a circle within their group
                for j, node in enumerate(nodes):
                    if len(nodes) > 1:
                        node_angle = 2 * 3.14159 * j / len(nodes)
                        node_x = group_x + radius * 0.5 * np.cos(node_angle)
                        node_y = group_y + radius * 0.5 * np.sin(node_angle)
                    else:
                        node_x, node_y = group_x, group_y
                    pos[node] = np.array([node_x, node_y])
        else:
            # Default to spring layout
            pos = nx.spring_layout(self.graph, k=2.0, iterations=100, seed=42)

        # Draw the graph with larger nodes and thicker edges
        nx.draw_networkx_nodes(
            self.graph, pos, node_color=node_colors, node_size=1000, alpha=0.8
        )
        nx.draw_networkx_labels(
            self.graph, pos, labels=node_labels, font_size=12, font_weight="bold"
        )
        nx.draw_networkx_edges(
            self.graph, pos, width=2.0, alpha=0.7, arrows=True, arrowsize=20
        )

        # Draw edge labels with better positioning
        nx.draw_networkx_edge_labels(
            self.graph,
            pos,
            edge_labels=edge_labels,
            font_size=10,
            font_color="black",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=3.0),
        )

        # Add a legend for node types
        legend_elements = [
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label=entity_type,
                markerfacecolor=color,
                markersize=15,
            )
            for entity_type, color in color_map.items()
        ]
        plt.legend(handles=legend_elements, loc="upper right", fontsize=12)

        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close()

        # Also generate a simplified version with only concepts and their relationships
        self._visualize_concept_graph(output_file.replace(".png", "_concepts.png"))

        print(f"Saved graph visualization to {output_file}")

    def _visualize_concept_graph(self, output_file):
        """Generate a simplified visualization showing only concepts and their relationships"""
        # Create a subgraph with only Concept nodes
        concept_nodes = [
            n
            for n in self.graph.nodes
            if self.graph.nodes[n].get("entity_type") == "concept"
        ]
        if len(concept_nodes) < 2:
            return

        concept_graph = self.graph.subgraph(concept_nodes).copy()

        plt.figure(figsize=(20, 20))

        # Define node labels
        node_labels = {}
        for node in concept_graph.nodes:
            name = str(concept_graph.nodes[node].get("name", "")).replace("$", "\$")
            node_labels[node] = name

        # Define edge labels
        edge_labels = {}
        for u, v in concept_graph.edges:
            if "description" in concept_graph.edges[u, v]["attributes"]:
                relationship_str = f"{concept_graph.edges[u, v]['relation_type']}({concept_graph.edges[u, v]['attributes']['description'][:20]}...)"
                label = relationship_str.replace("$", "\$")
                edge_labels[(u, v)] = label
            elif "relation_type" in concept_graph.edges[u, v]:
                label = str(concept_graph.edges[u, v]["relation_type"]).replace(
                    "$", "\$"
                )
                edge_labels[(u, v)] = label

        # Use a larger k value for more spacing between nodes
        pos = nx.spring_layout(concept_graph, k=3.0, iterations=100, seed=42)

        # Draw the graph with larger nodes and thicker edges
        nx.draw_networkx_nodes(
            concept_graph, pos, node_color="lightgreen", node_size=2000, alpha=0.8
        )
        nx.draw_networkx_labels(
            concept_graph, pos, labels=node_labels, font_size=14, font_weight="bold"
        )
        nx.draw_networkx_edges(
            concept_graph,
            pos,
            width=3.0,
            alpha=0.7,
            arrows=True,
            arrowsize=25,
            connectionstyle="arc3,rad=0.1",
        )  # Curved edges

        # Draw edge labels with better positioning
        nx.draw_networkx_edge_labels(
            concept_graph,
            pos,
            edge_labels=edge_labels,
            font_size=12,
            font_color="black",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=5.0),
            rotate=False,
        )

        plt.title("Concept Relationships", fontsize=20, pad=20)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"Saved concept graph visualization to {output_file}")

    def visualize_concept_subgraph(
        self, concept_id, output_file="concept_subgraph.png"
    ):
        """
        Visualize a specific concept with its related subconcepts and QA pairs

        Args:
            concept_id: ID of the concept to visualize
            output_file: Path to save the visualization
        """
        print(f"Visualizing concept subgraph for concept ID: {concept_id}...")

        # Check if concept exists
        if (
            concept_id not in self.graph.nodes
            or self.graph.nodes[concept_id].get("entity_type") != "concept"
        ):
            print(
                f"Error: Concept with ID {concept_id} not found or not a concept node"
            )
            return

        # Get concept name
        concept_name = self.graph.nodes[concept_id].get("name", "Unknown Concept")

        # Find all subconcepts related to this concept
        subconcept_nodes = []
        for source, target, edge_data in self.graph.edges(concept_id, data=True):
            if (
                edge_data.get("relation_type") == "HAS_SUBCONCEPT"
                and edge_data.get("target_type") == "SubConcept"
            ):
                if target in self.graph.nodes:
                    subconcept_nodes.append(target)

        # Find all QA nodes related to these subconcepts
        qa_nodes = []
        for subconcept_id in subconcept_nodes:
            for source, target, edge_data in self.graph.edges(subconcept_id, data=True):
                if (
                    edge_data.get("relation_type") == "EXPLAINS"
                    and edge_data.get("target_type") == "QA"
                ):
                    if target in self.graph.nodes:
                        qa_nodes.append(target)

        # Create subgraph with concept, subconcepts, and QAs
        nodes_to_include = [concept_id] + subconcept_nodes + qa_nodes
        subgraph = self.graph.subgraph(nodes_to_include).copy()

        if len(subgraph.nodes) <= 1:
            print(
                f"Warning: No related subconcepts or QAs found for concept '{concept_name}'"
            )
            return

        plt.figure(figsize=(20, 20))

        # Define node colors by entity type
        color_map = {
            "concept": "lightgreen",
            "subconcept": "lightcoral",
            "qa": "lightyellow",
        }

        # Assign colors to nodes
        node_colors = [
            color_map.get(subgraph.nodes[node].get("entity_type", "Unknown"), "gray")
            for node in subgraph.nodes
        ]

        # Define node sizes by entity type
        node_size_map = {
            "concept": 2000,
            "subconcept": 1500,
            "qa": 1000,
        }
        node_sizes = [
            node_size_map.get(subgraph.nodes[node].get("entity_type", "Unknown"), 1000)
            for node in subgraph.nodes
        ]

        # Define node labels - escape dollar signs to avoid matplotlib math mode
        node_labels = {}
        for node in subgraph.nodes:
            entity_type = subgraph.nodes[node].get("entity_type", "Unknown")
            name = str(subgraph.nodes[node].get("name", "")).replace("$", "\$")

            # Truncate QA names if they're too long
            if entity_type == "qa" and len(name) > 50:
                name = name[:47] + "..."

            node_labels[node] = name

        # Define edge labels - escape dollar signs
        edge_labels = {}
        for u, v in subgraph.edges:
            if "description" in subgraph.edges[u, v]:
                label = f"{subgraph.edges[u, v]['relation_type']}({subgraph.edges[u, v]['description'][:20]}...)"
                edge_labels[(u, v)] = label.replace("$", "\$")
            elif "relation_type" in subgraph.edges[u, v]:
                label = str(subgraph.edges[u, v]["relation_type"]).replace("$", "\$")
                edge_labels[(u, v)] = label

        # Use hierarchical layout
        pos = nx.spring_layout(subgraph, k=2.0, iterations=100, seed=42)

        # Draw the graph
        nx.draw_networkx_nodes(
            subgraph, pos, node_color=node_colors, node_size=node_sizes, alpha=0.8
        )
        nx.draw_networkx_labels(
            subgraph, pos, labels=node_labels, font_size=12, font_weight="bold"
        )
        nx.draw_networkx_edges(
            subgraph,
            pos,
            width=2.0,
            alpha=0.7,
            arrows=True,
            arrowsize=20,
            connectionstyle="arc3,rad=0.1",
        )  # Curved edges

        # Draw edge labels
        nx.draw_networkx_edge_labels(
            subgraph,
            pos,
            edge_labels=edge_labels,
            font_size=10,
            font_color="black",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=3.0),
        )

        # Add a legend for node types
        legend_elements = [
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label=entity_type,
                markerfacecolor=color,
                markersize=15,
            )
            for entity_type, color in color_map.items()
        ]
        plt.legend(handles=legend_elements, loc="upper right", fontsize=12)

        plt.title(f"Concept: {concept_name}", fontsize=20, pad=20)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"Saved concept subgraph visualization to {output_file}")

    def export_to_json(self, output_file="knowledge_graph.json"):
        """Export the knowledge graph to JSON format"""
        print("Exporting knowledge graph to JSON...")

        graph_data = {"nodes": [], "edges": []}

        # Export nodes
        for node_id in self.graph.nodes:
            node_data = self.graph.nodes[node_id].copy()
            node_data["id"] = node_id
            graph_data["nodes"].append(node_data)

        # Export edges
        for source, target in self.graph.edges:
            edge_data = self.graph.edges[source, target].copy()
            edge_data["source"] = source
            edge_data["target"] = target
            graph_data["edges"].append(edge_data)

        with open(output_file, "w") as f:
            json.dump(graph_data, f, indent=2)

        print(f"Exported graph data to {output_file}")
        return graph_data
