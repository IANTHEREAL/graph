from llm.factory import LLMInterface
from typing import Any

default_qa_extraction_prompt = """You are an expert in knowledge extraction and question generation. Your goal is to read a document and create question-answer pairs that effectively capture the most important knowledge within it, addressing the likely interests of someone reading the document to learn.

Given the following document:

{text}

Instructions:

1. **Understand the Document's Core Content:** First, read the document thoroughly to grasp its main purpose, key topics, and the most critical information it conveys.  Think about:
    * What is the primary goal of this document? What is it trying to explain or achieve?
    * What are the most important concepts, facts, rules, or policies discussed?
    * If someone wants to understand the key takeaways from this document, what are the absolute must-know pieces of information?

2. **Identify Key Knowledge and User-Relevant Questions:**  From the document's content, determine the essential knowledge a user would want to extract. Think from a user's perspective:
    * What questions would a reader likely have after reading this document if they were trying to understand or use the information?
    * What are the potential points of confusion or areas where clarification would be most helpful?
    * What kind of information would be most valuable for someone trying to apply the knowledge from this document in a real-world scenario?

3. **Generate Comprehensive Question-Answer Pairs:** Create question-answer pairs that directly address the key knowledge and user-relevant questions you've identified.
    * **Quantity:** Generate a sufficient number of question-answer pairs to comprehensively cover the essential knowledge in the document.  For longer, more complex documents, aim for a higher number of pairs (e.g., 20+). For shorter, simpler documents, fewer pairs may suffice (e.g., 10+).  Let the depth and breadth of the document content guide the number of questions.
    * **Focus:** Prioritize questions that explore:
        * Core concepts and definitions
        * Key rules, policies, and procedures
        * Important facts, statistics, and dates
        * Relationships between different entities or ideas
        * Practical implications or applications of the information

4. **Ensure Clarity, Context, and Self-Containment:** Each question and answer MUST be self-contained and understandable even without constant reference back to the original document:
    * **Context in Questions:**  Clearly specify the context within each question itself. Avoid vague pronouns or references. Instead of "What is the effective date?", ask "What is the effective date of the PingCAP Employee Data Privacy Policy?"
    * **Document References in Answers:**  Explicitly ground your answers in the provided document by including specific references. Use phrases like: "According to the [Document Name]," "[Policy Name] states that...", "The document specifies that...", or "Based on the information in [Document Name], ...".
    * **Specificity:** Use specific names, dates, titles, links, and other concrete details directly from the document in your answers. This makes the answers more informative and verifiable.
    * **Avoid Vague Language:** Do not use vague references like "the document," "this policy," or "the company" without clearly specifying *which* document, policy, or company you are referring to in the context of the question.  Imagine someone reading the question-answer pair *without* seeing the original document – would they understand the question and answer fully?

5. **Answer Accuracy and Derivation:**  All answers MUST be derived *exclusively* from the information provided in the document.
    * **No External Knowledge:** Do NOT introduce any information, facts, or opinions that are not explicitly stated or directly implied within the document.
    * **Faithful Representation:** Accurately and thoroughly represent the document's content in your answers.
    * **Detailed Answers:** Provide detailed answers that fully address the questions, using the information available in the document.

Output Format:

Return your response in JSON array format with each item containing "question" and "answer" fields, surrounded by `json and `:

```json
[
  {{
    "question": "Clear, contextual, and self-contained question here",
    "answer": "Your generated answer here with proper context, specific references to the document, and detailed information."
  }},
  {{
    "question": "Another contextual and user-relevant question here",
    "answer": "Another self-contained answer here, grounded in the document."
  }},
  ... (More question-answer pairs as needed)
]
"""

default_concept_extraction_prompt = """Based on the following context, identify the key concepts mentioned.
Context (with source_id):
{text}

Focus on the concepts about: {topic}
Please analyze the context carefully and extract all meaningful concepts about the topic, and ignore the rest.
If the context is not related to the topic, just return an empty list. Don't make your response confusing, far away from the topic.


For each concept, provide:
1. The concept name
2. A meaningful definition (as meaningful as possible)

Return the results in JSON format as a list of objects with 'name', 'definition' and 'reference_ids' fields.
JSON Output (surround with ```json and ```):
```json
[
    {{
        "name": "concept_name",
        "definition": "concept_definition",
        "source_ids": ["id1", "id2", ...]
    }},
    ...
]
```"""

default_extend_relationship_prompt = """I have two concepts that appear in the same QA pairs:
Concept 1: {concept_a_name} - {concept_a_definition}
Concept 2: {concept_b_name} - {concept_b_definition}

These concepts appear together in the following QA pairs:
{text}

Based on these QA pairs, determine the relationship between these two concepts.
Provide:
1. The relationship type {relation_types}
2. A detail description of the relationship
3. A confidence score (0.0-1.0) for this relationship

Return the result in JSON format with 'relation_type', 'description', and 'confidence' fields.

JSON Output (surround with ```json and ```):
```json
{{
    "relation_type": "relationship_type",
    "description": "relationship_description",
    "confidence": 0.0-1.0,
    "knowledge_block_ids": ["the knowledge blocks that are related to this relationship, ..."]
}}
```"""

default_extract_graph_from_knowledge_index = """You are an expert knowledge graph architect. Your task is to analyze the provided 'knowledge' object and its referenced document content ('reference_documents') to create concept node entities and their relationships for a knowledge graph.

**Inputs:**

1.  **`knowledge` Object:** Contains the `path` (representing the topic's context or hierarchy) and `references` (names of source documents).
    {knowledge}

2.  **`reference_documents` List:** A list of objects, each containing the `id`, `name`, `link`, `version`, and `content` of the documents referenced in the `knowledge` object.
    {reference_documents}

**Task:**

Based *strictly* on the information found within the `content` of the provided `reference_documents` that correspond to the `knowledge` object's topic (indicated by its `path`), generate concept node entities and their relationships.

1.  **Analyze Complexity:** Evaluate the information related to the `knowledge['path']` topic within the document `content`.
    * Consider a topic SIMPLE if: it can be fully explained in 1-2 paragraphs, has a single clear definition, and doesn't contain distinct subtopics.
    * Consider a topic COMPLEX if: it requires extensive explanation, contains multiple aspects or dimensions, has hierarchical components, or is discussed from different perspectives in the documents.

2.  **For Each Entity:**
    * **Generate a `name`:** Create a concise, descriptive, and accurate name for the concept represented by the entity. Use terminology found in the documents or derived logically from the `knowledge['path']` and content.
    * **Generate a `definition`:** Write a professional, clear, detailed, coherent, and logically structured definition (or description) for the entity. This definition MUST:
        * Be derived *exclusively* from the provided `content` of the relevant `reference_documents`. Do not infer information or use external knowledge.
        * Accurately synthesize the relevant information from the source(s).
        * Explain the concept thoroughly.
        * Include explanations of domain-specific terms within the definition when necessary.

3.  **Information Prioritization Guidelines:**
    * Prioritize more recent versions of documents when available.
    * Look for consensus across multiple sources.
    * If conflicting information exists, note the discrepancy in the definition and present the most supported view.

4.  **Validation Requirements:**
    * Ensure all key points from the source documents are represented.
    * Verify that no information contradicts the source material.
    * Include only information that is explicitly stated or directly implied in the source documents.

5.  **Relationship Identification and Definition:**
    * Identify meaningful relationships between entities based on the document content.
    * For each relationship:
        * Determine the source and target entities.
        * Assign an appropriate relationship type that best describes the connection.
        * Create a detailed definition explaining the nature of the relationship.
    * Common relationship types include (but are not limited to):
        * Hierarchical (is_part_of, contains, belongs_to)
        * Causal (causes, results_in, depends_on)
        * Functional (interacts_with, supports, enables)
        * Temporal (precedes, follows, occurs_during)
        * Comparative (is_similar_to, differs_from)
    * Relationship definitions should:
        * Be as detailed and professional as entity definitions
        * Explain the specific nature of how entities interact or relate
        * Be derived exclusively from the source documents
        * Include directional clarity (how source affects target and vice versa)
    * Ensure all relationships are explicitly supported by information in the source documents.

6.  **Edge Case Handling:**
    * If the referenced documents contain insufficient information:
        * Create a minimal entity with the available information.
        * Note in the definition that the information is limited based on the provided documents.
    * If the topic is not clearly addressed in the documents:
        * Create an entity based on any relevant information that can be found.
        * Indicate areas where more information would be beneficial.
    * If relationships are implied but not explicitly stated:
        * Only create relationships with reasonable confidence based on the text.
        * Note the level of certainty in the relationship definition.

**Output Format:**

Provide the output as a JSON object with two main sections:

1. **`entities`**: A list of objects, each representing a concept node with:
   * `name`: (String) The generated name for the entity.
   * `definition`: (String) The generated professional definition for the entity.

2. **`relationships`**: A list of objects, each representing a relationship between entities with:
   * `source_entity`: (String) The name of the source entity.
   * `target_entity`: (String) The name of the target entity.
   * `type`: (String) A concise label describing the type of relationship (e.g., "is_part_of", "depends_on", "influences").
   * `definition`: (String) A detailed, professional description of the relationship, explaining how the source entity relates to the target entity, based strictly on the provided document content.

**Example Output Structure:**

```json
{{
  "entities": [
    {{
      "name": "Entity Name 1",
      "definition": "Detailed, professional definition for Entity 1 based strictly on the provided document content..."
    }},
    {{
      "name": "Entity Name 2",
      "definition": "Detailed, professional definition for Entity 2 based strictly on the provided document content..."
    }}
  ],
  "relationships": [
    {{
      "source_entity": "Entity Name 1",
      "target_entity": "Entity Name 2",
      "type": "is_component_of",
      "definition": "Detailed explanation of how Entity 1 functions as a component of Entity 2, including specific interactions and dependencies described in the source documents..."
    }}
  ]
}}
```
Remember: Quality over quantity. It's better to have fewer well-defined entities and relationships than many superficial ones. Your entities and relationships should represent distinct, meaningful concepts that would be valuable in a knowledge graph. All information must be derived exclusively from the provided documents.
"""


class PromptHub:
    """
    A builder class for prompt hub.
    """

    def __init__(self):
        # Initialize extraction prompts
        self._extraction_prompts = {
            "knowledge_qa_extraction": default_qa_extraction_prompt,
            "concept_extraction": default_concept_extraction_prompt,
            "extend_relationship": default_extend_relationship_prompt,
            "from_knowledge_index_graph_extraction": default_extract_graph_from_knowledge_index,
        }

    def get_prompt(self, prompt_name: str) -> str:
        """
        Get an prompt by name.

        Parameters:
        - prompt_name: The name of the prompt to retrieve

        Returns:
        - The prompt template string
        """
        if prompt_name not in self._extraction_prompts:
            raise ValueError(f"Unknown prompt name: {prompt_name}")

        return self._extraction_prompts[prompt_name]
