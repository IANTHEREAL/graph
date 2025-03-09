from llm.factory import LLMInterface
from typing import Any

block_extraction_prompt = """You are an expert in knowledge extraction and question generation. Your goal is to read a document and create question-answer pairs that effectively capture the most important knowledge within it, addressing the likely interests of someone reading the document to learn.

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

concept_extraction_prompt = """
Based on the following questions and answers, identify the key concepts mentioned.
For each concept, provide:
1. The concept name
2. A brief definition (if possible)

Return the results in JSON format as a list of objects with 'name' and 'definition' fields.

Questions and Answers:
{text}

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

extend_concept_prompt = """Given this question and answer about {concept_name}:
{text}

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
        "description": "the description about which aspect this subconcept contributes to the main concept",
        "knowledge_block_ids": ["he knowledge blocks that are related to this subconcept, ...]
    }},
    ...
]
```"""

extend_relationship_prompt = """I have two concepts that appear in the same QA pairs:
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


class GraphSpec:
    """
    A builder class for constructing knowledge graphs from documents.
    """

    def __init__(self, llm_client: LLMInterface):
        """
        Initialize the builder with a graph instance and specifications.

        Parameters:
        - graph: The knowledge graph to populate
        - graph_spec: Configuration for extraction and analysis processes
        """

        if llm_client is None:
            raise ValueError("LLM client must be set before initializing GraphSpec")

        self.llm_client = llm_client

        # Initialize default processing parameters
        self._processing_parameters = {
            "relationship_discovery": {"min_confidence": 0.6}
        }

        # Initialize extraction prompts
        self._extraction_prompts = {
            "knowledge_block_extraction": block_extraction_prompt,
            "concept_extraction": concept_extraction_prompt,
            "extend_concept": extend_concept_prompt,
            "extend_relationship": extend_relationship_prompt,
        }

    def get_extraction_prompt(self, prompt_name: str) -> str:
        """
        Get an extraction prompt by name.

        Parameters:
        - prompt_name: The name of the prompt to retrieve

        Returns:
        - The prompt template string
        """
        if prompt_name not in self._extraction_prompts:
            raise ValueError(f"Unknown prompt name: {prompt_name}")

        return self._extraction_prompts[prompt_name]

    def get_processing_parameter(self, category: str, parameter: str) -> Any:
        """
        Get a processing parameter by category and name.

        Parameters:
        - category: The parameter category
        - parameter: The specific parameter name

        Returns:
        - The parameter value
        """
        if category not in self._processing_parameters:
            raise ValueError(f"Unknown parameter category: {category}")

        if parameter not in self._processing_parameters[category]:
            raise ValueError(f"Unknown parameter: {parameter} in category {category}")

        return self._processing_parameters[category][parameter]

    def set_processing_parameter(
        self, category: str, parameter: str, value: Any
    ) -> None:
        """
        Set a processing parameter.

        Parameters:
        - category: The parameter category
        - parameter: The specific parameter name
        - value: The new parameter value
        """
        if category not in self._processing_parameters:
            self._processing_parameters[category] = {}

        self._processing_parameters[category][parameter] = value
