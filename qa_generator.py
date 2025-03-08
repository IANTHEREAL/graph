import json
import logging
import os
from typing import List, Dict, Any, Optional

from utils.json_utils import extract_json_array, extract_json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QAGenerator:
    """
    A class for generating question-answer pairs from markdown content using an LLM.
    """

    def __init__(self, llm_client):
        """
        Initialize the QA Generator with an LLM client.

        Args:
            llm_client: A client for calling the language model
        """
        self.llm_client = llm_client

    def read_markdown_file(self, file_path: str) -> str:
        """
        Read content from a markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            The content of the markdown file as a string
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return ""

    def extract_qa(self, content: str) -> Optional[List[Dict[str, Any]]]:

        prompt = f"""You are an expert in knowledge extraction and question generation. Your goal is to read a document and create question-answer pairs that effectively capture the most important knowledge within it, addressing the likely interests of someone reading the document to learn.

Given the following document:

{content}

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

        try:
            response = self.llm_client.generate(
                prompt=prompt,
            )
            extracted_json = extract_json_array(response)
            return json.loads(extracted_json)
        except Exception as e:
            logger.error(
                f"Error generating QA for document: {str(e)}, data: {response}"
            )
            return None

    def generate_faq_file(self, file_path: str) -> Optional[List[Dict[str, Any]]]:

        # Read the markdown file
        document = self.read_markdown_file(file_path)
        if not document:
            return None

        prompt = f"""Transform a document into a comprehensive and user-friendly FAQ format. Follow these guidelines:

Objective: Reorganize the document content into intuitive question-answer pairs that preserve all key information while enhancing readability and practical utility.

Given the following document:

{document}

Process:
1. Read the entire document thoroughly to understand its main concepts, definitions, processes, and key points.

2. Create effective Q&A pairs:
   - Formulate questions that are natural and reflect how users would actually ask them
   - Ensure each question is self-contained and clearly identifies its subject
   - Avoid ambiguous pronouns (this, it, that) - specify the exact concept, process, or term
   - When referring to "this document" or similar phrases, explicitly name the document
   - Focus each question on a single topic or concept
   - Make answers self-contained so they can be understood without reading other Q&As
   - Provide clear explanations for specialized terminology

3. Organize Q&A pairs logically:
   - Begin with the document's basic information and purpose
   - Group Q&A pairs by topic or concept
   - Progress from fundamental to advanced concepts
   - Add a glossary section at the end for key terminology

4. Formatting requirements:
   - Employ clear headings to separate different sections
   - Simplify complex tables or diagrams by explaining their core meaning in text
   - Ensure examples are concise and illustrative

5. Quality assurance:
   - Verify all critical information from the original document is covered
   - Confirm each Q&A pair can stand alone meaningfully
   - Ensure consistent terminology usage
   - Verify answers accurately reflect the original document content

The final output should enable someone unfamiliar with the original document to understand its key content through the FAQ alone. And in markdown format."""

        try:
            return self.llm_client.generate(
                prompt=prompt,
            )
        except Exception as e:
            logger.error(f"Error generating QA for document: {str(e)}")
            return None

    def extract_qa_from_faq(
        self, file_path: str
    ) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        Extract question-answer pairs from an FAQ document and categorize them based on self-containment.

        Args:
            file_path: Path to the FAQ markdown file

        Returns:
            A dictionary with 'clear_qa_pairs' and 'qa_needing_context' lists
        """
        # Read the markdown file
        document = self.read_markdown_file(file_path)
        if not document:
            return None

        prompt = f"""Extract and Categorize Question-Answer Pairs from an FAQ Document

Objective:  Process the provided Frequently Asked Questions (FAQ) document to identify all question-answer pairs.  Each extracted pair must be presented in a JSON format, ensuring clarity and independent understandability.

Input:
FAQ Document:
{document}

Instructions:

1. **Verbatim Extraction (No Modifications):**
   - Identify each question and its corresponding answer within the FAQ document.
   - Copy the question and answer **exactly as they appear in the document**.
   - **Do not alter, rephrase, or summarize** the questions or answers in any way.  Maintain the original wording completely.

2. **Independent Understandability and Contextual Enrichment:**
   - Evaluate each extracted question-answer pair in isolation, **separate from the original FAQ document and other pairs**.
   - Determine if each question and answer is **fully understandable on its own**, without relying on surrounding context within the document.
   - If a question or answer is **not clear or lacks necessary context** when viewed independently, you **must add the minimum required contextual information** to make it fully understandable.  This might involve adding a short phrase or clarifying word to the question or answer.
   - Prioritize clarity and self-contained meaning for each individual question-answer pair.

3. **JSON Output Format:**
   - Present the extracted and (if necessary) contextually enriched question-answer pairs as a **JSON array**.
   - Each element in the JSON array should be a **JSON object** representing a single question-answer pair.
   - Each JSON object must have the following structure:
     ```json
     {{
       "question": "The complete and independently understandable question",
       "answer": "The complete and independently understandable answer"
     }}
     ```

Example Output Format:
```json
[
    {{
      "question": "Shipping costs are calculated how?",
      "answer": "Shipping costs are calculated based on weight and destination.  (This is in reference to order shipping.)"
    }},
    ...
]```"""

        try:
            response = self.llm_client.generate(prompt=prompt)
            extracted_json = extract_json_array(response)
            return json.loads(extracted_json)
        except Exception as e:
            logger.error(f"Error extracting QA pairs from FAQ document: {str(e)}")
            return None
