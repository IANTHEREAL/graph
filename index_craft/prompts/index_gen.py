import json
from typing import Dict, List


def get_faq_index_prompt(faq: str, index_tree: List[Dict]) -> str:
    # Convert the index tree to a JSON string with indentation for readability
    index_tree_json = json.dumps(index_tree, indent=4, ensure_ascii=False)

    # Construct the prompt
    prompt = f"""Your task is to analyze a FAQ, break it down into subquestions, and identify appropriate index paths in a tree-structured index system for each subquestion.

## Current Index Tree

```json
{index_tree_json}
```

## Instructions

1. Subquestion Extraction:
   - Carefully read the FAQ and break it down into distinct subquestions that users might have
   - Each subquestion should capture a single, specific information need
   - Extract both explicit questions and implicit information needs

2. Path Identification:
   - For each subquestion:
     * Start from the root node of the index tree
     * Navigate through the tree to find the most specific path that matches the subquestion
     * Record the complete path from root to the most specific applicable node
     * If no suitable path exists, leave the index_path empty

3. Matching Process:
   - Always prioritize matching with specific categories over general ones
   - Match with leaf nodes when applicable
   - Consider the full context of the subquestion when determining the best path
   - Include clear reasoning about why you selected each path

4. Validation Rules:
   - Have all important subquestions in the FAQ been identified?
   - Does each identified path accurately represent the information needed for the subquestion?
   - Are the paths specific enough (reaching leaf nodes when applicable)?
   - Is your reasoning clear and justifiable?

## FAQ to Analyze

{faq}

Response Format:
Return an array of objects, where each object represents a subquestion found in the FAQ, with the following structure:

```json
[
    {{
        "subquestion": "What is the specific subquestion or information need?",
        "reasoning": "Explanation of why this index path was chosen for this subquestion",
        "index_path": ["Level 1 Node Text", "Level 2 Node Text"]
    }},
    {{
        "subquestion": "Another subquestion extracted from the FAQ",
        "reasoning": "Reasoning for this path selection",
        "index_path": []  // Empty array if no suitable path exists in the current index tree
    }}
]
```

Note: For the index_path, include only the text values of each node in the path, from root to the most specific node.
"""

    return prompt


def get_index_reference_prompt(content: str, index_tree: List[Dict]) -> str:
    # Convert the index tree to a JSON string with indentation for readability
    index_tree_json = json.dumps(index_tree, indent=4, ensure_ascii=False)

    # Construct the prompt
    prompt = f"""Your task is to identify all index paths in a tree-structured index system that are relevant to the given content. Unlike classifying a FAQ into categories, your goal is to find all nodes in the index tree that this content could serve as a reference for.

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
        "relevance": "high|medium|low", 
        "reasoning": "Explanation of why this content is relevant to this index path",
        "index_path": ["Level 1 Node Text", "Level 2 Node Text", "Most Specific Level Node Text"]
    }},
    {{
        "topic": "Another topic from the content",
        "relevance": "medium",
        "reasoning": "Reasoning for this path's relevance",
        "index_path": ["Different Level 1 Node", "Different Level 2 Node"]
    }}
]
```

Note: For each index_path, include only the text values of nodes from root to the most specific relevant node. Remember to always prioritize the most specific (child) nodes over more general (parent) nodes when both are relevant.
"""

    return prompt
