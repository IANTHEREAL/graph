import json
from typing import Dict, List


def get_question_index_prompt(question: str, index_tree: List[Dict]) -> str:
    # Convert the index tree to a JSON string with indentation for readability
    index_tree_json = json.dumps(index_tree, indent=4, ensure_ascii=False)

    # Construct the prompt
    prompt = f"""Your task is to analyze a question, break it down into subquestions, and determine the most appropriate index path for each subquestion in the provided hierarchical index tree.

## Current Index Tree

```json
{index_tree_json}
```

## Index Tree Structure
- Each parent index node contains all documents that its child nodes have
- The tree is hierarchical - higher nodes are more general, leaf nodes are more specific
- When matching, prefer the most specific (deepest) node that can answer the question

## Instructions

1. Subquestion Extraction:
   - Carefully read the question and break it down into distinct subquestions
   - Each subquestion should capture a single, specific information need

2. Index Matching Process:
   - For each subquestion, find the MOST SPECIFIC node whose documents would best answer it
   - Start from leaf nodes and work upward:
     * First check if any leaf node directly addresses the subquestion
     * If no leaf node matches, check intermediate nodes
     * If no specific node matches, you can use a more general parent node
   - Always prefer the deepest/most specific applicable node

3. Match Evaluation:
   - If ANY node in the tree contains documents that would answer the subquestion:
     * Set "matched" to true
     * Provide the complete "index_path" from root to the most specific matching node
     * Explain in "reasoning" why this is the most appropriate node
   - If NO node in the entire tree would contain relevant documents:
     * Set "matched" to false
     * Leave "index_path" as an empty array
     * Explain why no node in the current index tree would have relevant information

## question to Analyze

{question}

Response Format:
Return an array of objects with the following structure:

```json
[
    {{
        "subquestion": "What is the specific subquestion?",
        "reasoning": "This node is the most specific location for documents about X. While parent nodes would also contain this information, this node specifically focuses on the requested details.",
        "matched": true,
        "index_path": ["Root Node", "Intermediate Node", "Most Specific Node"]
    }},
    {{
        "subquestion": "Another subquestion from the question",
        "reasoning": "While no leaf node specifically addresses this topic, this parent node contains broader documentation that would include the answer to this question. More specific child nodes focus on different aspects.",
        "matched": true,
        "index_path": ["Root Node", "Parent Node"]
    }},
    {{
        "subquestion": "A third subquestion without matches",
        "reasoning": "No nodes in the current index tree, at any level, appear to contain documents related to this specific topic. The index structure doesn't include categories for this type of information.",
        "matched": false,
        "index_path": []
    }}
]
```

Important: Always try to find the most specific appropriate node for each subquestion, but recognize that sometimes a parent node might be the best match if it contains the relevant information and no more specific child node is suitable.
"""

    return prompt


def get_index_reference_prompt(content: str, index_tree: List[Dict]) -> str:
    # Convert the index tree to a JSON string with indentation for readability
    index_tree_json = json.dumps(index_tree, indent=4, ensure_ascii=False)

    # Construct the prompt
    prompt = f"""Your task is to identify all index paths in a tree-structured index system that are relevant to the given content. Unlike classifying a question into categories, your goal is to find all nodes in the index tree that this content could serve as a reference for.

## Current Index Tree

```json
{index_tree_json}
```

## Instructions

1. Content Analysis:
   - Carefully read the provided content and identify all key topics, concepts, and information it contains
   - Consider both explicit and implicit knowledge in the content
   - Note specific technical terms, processes, definitions, or explanations

2. Index Path Identification:
   - For each identified topic/concept in the content:
     * Search through the index tree to find all nodes that relate to this topic
     * A single piece of content may be relevant to multiple index paths
     * Record complete paths from root to each relevant node
     * Important: If both a parent node and its child node are relevant, always choose the child node 
       (the more specific classification) and omit the parent node from your results

3. Relevance Determination:
   - Content is relevant to an index node if:
     * It directly explains or addresses the topic represented by the node
     * It provides information that would help answer questions related to that node
     * It contains examples, context, or details about the node's topic
   - Consider different levels of relevance (high, medium, low) based on how central the topic is to the content
   - Prefer specificity: When content relates to multiple levels in the same branch, always prioritize 
     the most specific (deepest) relevant node

4. Validation Rules:
   - Has every significant topic in the content been matched to appropriate index paths?
   - Are the identified paths appropriately specific? (Always choose child over parent when both are relevant)
   - Is the reasoning for each path's relevance clear and justified?
   - Have you considered both obvious and less obvious connections?

## Content to Analyze

{content}

Response Format:
Return an array of objects, where each object represents a relevant index path found for the content, with the following structure:

```json
[
    {{
        "topic": "Specific topic/concept from the content that matches this path",
        "reasoning": "Explanation of why this content is relevant to this index path",
        "relevance": "high|medium|low", 
        "index_path": ["Level 1 Node Text", "Level 2 Node Text", "Most Specific Level Node Text"]
    }},
    {{
        "topic": "Another topic from the content",
        "reasoning": "Explanation of why this content is relevant to this index path",
        "relevance": "medium",
        "index_path": ["Different Level 1 Node", "Different Level 2 Node"]
    }}
]
```

Note: For each index_path, include only the text values of nodes from root to the most specific relevant node. Remember to always prioritize the most specific (child) nodes over more general (parent) nodes when both are relevant.
"""

    return prompt
