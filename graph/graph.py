import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Optional, Dict, Any
import json
import os

from graph.models import Concept, SubConcept, KnowledgeBlock, SourceData, Relationship


class KnowledgeGraph:
    """
    Knowledge graph representation and operations
    """

    def __init__(self):
        self.G = nx.MultiDiGraph()
        self.concepts = {}
        self.subconcepts = {}
        self.knowledge_blocks = {}
        self.source_data = {}  # Changed from documents to source_data
        self.relationships = []

    def add_concept(self, concept: Concept) -> str:
        """Add a concept to the graph"""
        self.concepts[concept.id] = concept
        self.G.add_node(
            concept.id,
            type="concept",
            name=concept.name,
            definition=concept.definition,
            version=concept.version,
        )
        return concept.id

    def add_subconcept(self, subconcept: SubConcept) -> str:
        """Add a subconcept to the graph"""
        self.subconcepts[subconcept.id] = subconcept
        self.G.add_node(
            subconcept.id,
            type="subconcept",
            name=subconcept.name,
            definition=subconcept.definition,
        )

        # Add edge from parent concept to subconcept
        if subconcept.parent_concept_id:
            self.add_relationship(
                Relationship(
                    source_id=subconcept.parent_concept_id,
                    source_type="concept",
                    target_id=subconcept.id,
                    target_type="subconcept",
                    relation_type="EXPLAINS",
                    attributes={"description": subconcept.aspect_descriptor},
                )
            )

        # Add edges from subconcept to each knowledge block
        for kb_id in subconcept.knowledge_block_ids:
            if kb_id:
                self.add_relationship(
                    Relationship(
                        source_id=subconcept.id,
                        source_type="subconcept",
                        target_id=kb_id,
                        target_type="knowledge_block",
                        relation_type="DEPENDS_ON",
                        attributes={"description": "Derived from knowledge block"},
                    )
                )

        return subconcept.id

    def add_knowledge_block(self, knowledge_block: KnowledgeBlock) -> str:
        """Add a knowledge block to the graph"""
        self.knowledge_blocks[knowledge_block.id] = knowledge_block
        self.G.add_node(
            knowledge_block.id,
            type="knowledge_block",
            name=knowledge_block.name,
            definition=knowledge_block.definition,
            source_version=knowledge_block.source_version,
        )

        # Add edges from each source to the knowledge block
        for source_id in knowledge_block.source_ids:
            if source_id:
                self.add_relationship(
                    Relationship(
                        source_id=source_id,
                        source_type="source_data",
                        target_id=knowledge_block.id,
                        target_type="knowledge_block",
                        relation_type="REFERENCES",
                        attributes={"description": "Source of knowledge"},
                    )
                )

        return knowledge_block.id

    def add_source_data(self, source_data: SourceData) -> str:
        """Add a source data to the graph"""
        self.source_data[source_data.id] = source_data
        self.G.add_node(
            source_data.id,
            type="source_data",
            name=source_data.name,
            definition=source_data.definition,
            link=source_data.link,
            version=source_data.version,
            data_type=source_data.type,
        )
        return source_data.id

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship (edge) to the graph"""
        self.relationships.append(relationship)
        self.G.add_edge(
            relationship.source_id,
            relationship.target_id,
            type=relationship.relation_type,
            **relationship.attributes,
        )

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Get a concept by ID"""
        return self.concepts.get(concept_id)

    def get_subconcept(self, subconcept_id: str) -> Optional[SubConcept]:
        """Get a subconcept by ID"""
        return self.subconcepts.get(subconcept_id)

    def get_knowledge_block(self, block_id: str) -> Optional[KnowledgeBlock]:
        """Get a knowledge block by ID"""
        return self.knowledge_blocks.get(block_id)

    def get_source_data(self, source_id: str) -> Optional[SourceData]:
        """Get a source data by ID"""
        return self.source_data.get(source_id)

    def get_concepts_by_name(self, name: str) -> List[Concept]:
        """Get concepts by name (case-insensitive partial match)"""
        return [c for c in self.concepts.values() if name.lower() in c.name.lower()]

    def get_related_concepts(self, concept_id: str) -> List[Concept]:
        """Get concepts related to the given concept"""
        related_ids = []
        for rel in self.relationships:
            if rel.source_id == concept_id and rel.target_type == "concept":
                related_ids.append(rel.target_id)
            elif rel.target_id == concept_id and rel.source_type == "concept":
                related_ids.append(rel.source_id)

        return [self.concepts[cid] for cid in related_ids if cid in self.concepts]

    def save_to_disk(self, storage_path: str) -> None:
        """
        Save the knowledge graph data to disk.

        Parameters:
        - storage_path: Path where to save the data
        """
        # Convert all model objects to serializable dictionaries
        data = {
            "concepts": {},
            "subconcepts": {},
            "knowledge_blocks": {},
            "source_data": {},
            "relationships": [],
        }

        # Save concepts
        for concept_id, concept in self.concepts.items():
            data["concepts"][concept_id] = concept.to_dict()

        # Save subconcepts
        for subconcept_id, subconcept in self.subconcepts.items():
            data["subconcepts"][subconcept_id] = subconcept.to_dict()

        # Save knowledge blocks
        for block_id, block in self.knowledge_blocks.items():
            data["knowledge_blocks"][block_id] = block.to_dict()

        # Save source data
        for source_id, source in self.source_data.items():
            data["source_data"][source_id] = source.to_dict()

        # Save relationships
        for relationship in self.relationships:
            data["relationships"].append(relationship.to_dict())

        # Ensure directory exists
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

        # Save to file
        with open(storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Knowledge graph saved to {storage_path}")

    def load_from_disk(self, storage_path: str) -> None:
        """
        Load the knowledge graph data from disk.

        Parameters:
        - storage_path: Path from where to load the data
        """
        try:
            with open(storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Clear existing data
            self.concepts = {}
            self.subconcepts = {}
            self.knowledge_blocks = {}
            self.source_data = {}
            self.relationships = []
            self.G = nx.MultiDiGraph()

            # Load source data first (they have no dependencies)
            for source_id, source_dict in data.get("source_data", {}).items():
                source = SourceData.from_dict(source_dict)
                self.source_data[source_id] = source
                self.G.add_node(
                    source_id,
                    type="source_data",
                    name=source.name,
                    definition=source.definition,
                    link=source.link,
                    version=source.version,
                    data_type=source.type,
                )

            # Load knowledge blocks (they depend on source data)
            for block_id, block_dict in data.get("knowledge_blocks", {}).items():
                kb = KnowledgeBlock.from_dict(block_dict)
                self.knowledge_blocks[block_id] = kb
                self.G.add_node(
                    block_id,
                    type="knowledge_block",
                    name=kb.name,
                    definition=kb.definition,
                    source_version=kb.source_version,
                )

            # Load concepts
            for concept_id, concept_dict in data.get("concepts", {}).items():
                concept = Concept.from_dict(concept_dict)
                self.concepts[concept_id] = concept
                self.G.add_node(
                    concept_id,
                    type="concept",
                    name=concept.name,
                    definition=concept.definition,
                    version=concept.version,
                )

            # Load subconcepts (they depend on concepts and knowledge blocks)
            for subconcept_id, subconcept_dict in data.get("subconcepts", {}).items():
                subconcept = SubConcept.from_dict(subconcept_dict)
                self.subconcepts[subconcept_id] = subconcept
                self.G.add_node(
                    subconcept_id,
                    type="subconcept",
                    name=subconcept.name,
                    definition=subconcept.definition,
                )

            # Load relationships (they depend on all entities)
            for rel_dict in data.get("relationships", []):
                relationship = Relationship.from_dict(rel_dict)
                self.relationships.append(relationship)
                self.G.add_edge(
                    relationship.source_id,
                    relationship.target_id,
                    type=relationship.relation_type,
                    **relationship.attributes,
                )

            print(f"Knowledge graph loaded from {storage_path}")
            print(
                f"Loaded {len(self.concepts)} concepts, {len(self.subconcepts)} subconcepts, "
                f"{len(self.knowledge_blocks)} knowledge blocks, {len(self.source_data)} sources, "
                f"and {len(self.relationships)} relationships"
            )

        except FileNotFoundError:
            print(f"No graph file found at {storage_path}")
        except json.JSONDecodeError:
            print(f"Error parsing graph file at {storage_path}")
        except Exception as e:
            print(f"Error loading graph: {str(e)}")

    def visualize(self, output_file="knowledge_graph.png", layout="spring"):
        """Visualize the knowledge graph"""
        plt.figure(figsize=(12, 8))

        # Create position layout
        if layout == "spring":
            pos = nx.spring_layout(self.G)
        elif layout == "circular":
            pos = nx.circular_layout(self.G)
        else:
            pos = nx.kamada_kawai_layout(self.G)

        # Draw nodes by type
        concept_nodes = [
            n for n, attr in self.G.nodes(data=True) if attr.get("type") == "concept"
        ]
        subconcept_nodes = [
            n for n, attr in self.G.nodes(data=True) if attr.get("type") == "subconcept"
        ]
        kb_nodes = [
            n
            for n, attr in self.G.nodes(data=True)
            if attr.get("type") == "knowledge_block"
        ]
        source_nodes = [
            n
            for n, attr in self.G.nodes(data=True)
            if attr.get("type") == "source_data"
        ]

        nx.draw_networkx_nodes(
            self.G,
            pos,
            nodelist=concept_nodes,
            node_color="green",
            node_size=500,
            alpha=0.8,
        )
        nx.draw_networkx_nodes(
            self.G,
            pos,
            nodelist=subconcept_nodes,
            node_color="blue",
            node_size=300,
            alpha=0.7,
        )
        nx.draw_networkx_nodes(
            self.G,
            pos,
            nodelist=kb_nodes,
            node_color="orange",
            node_size=200,
            alpha=0.6,
        )
        nx.draw_networkx_nodes(
            self.G,
            pos,
            nodelist=source_nodes,
            node_color="red",
            node_size=400,
            alpha=0.8,
        )

        # Draw edges with different styles by type
        for u, v, data in self.G.edges(data=True):
            edge_type = data.get("type", "")
            if edge_type == "EXPLAINS":
                nx.draw_networkx_edges(
                    self.G, pos, edgelist=[(u, v)], edge_color="blue", width=2
                )
            elif edge_type == "DEPENDS_ON":
                nx.draw_networkx_edges(
                    self.G, pos, edgelist=[(u, v)], edge_color="red", width=2
                )
            elif edge_type == "REFERENCES":
                nx.draw_networkx_edges(
                    self.G, pos, edgelist=[(u, v)], edge_color="green", width=2
                )
            else:
                nx.draw_networkx_edges(
                    self.G, pos, edgelist=[(u, v)], edge_color="gray", width=1
                )

        # Add labels with truncated text for better visualization
        labels = {}
        for node in self.G.nodes():
            node_attrs = self.G.nodes[node]
            name = node_attrs.get("name", "")
            if len(name) > 20:
                name = name[:17] + "..."
            labels[node] = name

        nx.draw_networkx_labels(self.G, pos, labels=labels, font_size=10)

        plt.title("Knowledge Graph Visualization")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_file, format="PNG", dpi=300)
        plt.close()

        print(f"Graph visualization saved to {output_file}")
