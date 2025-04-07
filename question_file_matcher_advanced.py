import os
import json
import glob
from typing import List, Dict, Any
from llm.factory import LLMInterface
from utils.json_utils import extract_json_array

def read_file_content(file_path: str) -> str:
    """Read the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def create_file_index(docs_dir: str) -> List[Dict[str, Any]]:
    """Create an index of files in the docs directory."""
    file_index = []
    file_paths = glob.glob(os.path.join(docs_dir, "**/*.*"), recursive=True)
    
    for file_path in file_paths:
        if os.path.isfile(file_path) and not os.path.basename(file_path).startswith('.'):
            # Skip non-text files
            if file_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf')):
                continue

              # Skip files in the FAQ directory
            if '/FAQ/' in file_path.replace('\\', '/'):
                continue
                
            # Also skip files with -FAQ in the name (as seen in the output)
            if '-FAQ' in os.path.basename(file_path):
                continue
                
            file_index.append({
                "path": file_path,
                "title": os.path.basename(file_path),
                "content": read_file_content(file_path)
            })
    
    return file_index

def get_matching_prompt(question: str, file_index: List[Dict[str, Any]]) -> str:
    """Create a prompt following the structure of get_faq_index_prompt."""
    # Create a simplified file list for the prompt
    files_json = json.dumps([{
        "id": i+1,
        "title": file["title"],
        "preview": file["content"][:300] + "..." if len(file["content"]) > 300 else file["content"]
    } for i, file in enumerate(file_index)], indent=2, ensure_ascii=False)
    
    prompt = f"""Your task is to identify which documents contain information that DIRECTLY answers the given question. Be very strict in your evaluation.

## Question to Answer
{question}

## Available Documents
```json
{files_json}
```

## Instructions

1. Strict Document Analysis:
   - Carefully analyze each document to determine if it contains information that DIRECTLY answers the question
   - Only consider a document relevant if it contains explicit information addressing the question
   - Require clear, specific content that answers the question with minimal inference

2. Relevance Determination:
   - If a document contains information that directly answers the question:
     * Set "relevant" to true
     * In "reasoning", explain EXACTLY what information in the document directly addresses the question
   - If a document does not contain direct answers:
     * Set "relevant" to false
     * Briefly explain why it's not directly relevant

3. Confidence Level:
   - Provide a confidence level based strictly on how directly the document addresses the question:
     * high: Document contains explicit, comprehensive answers to the question
     * medium: Document contains direct but partial answers
     * low: Document contains minimal direct information relevant to the question. Ignore it. Don't include it in the response.

Response Format:
Return an array of objects with the following structure:

```json
[
    {{
        "document_id": 1,
        "title": "Document Title",
        "relevant": true,
        "confidence": "high|medium|low",
        "reasoning": "This document specifically states X on page Y, which directly answers the question."
    }},
    {{
        "document_id": 2,
        "title": "Another Document Title",
        "relevant": false,
        "confidence": "high",
        "reasoning": "This document discusses related topics but does not provide direct answers to the question."
    }}
]
```

Important: Be extremely strict in your evaluation. Only mark documents as relevant if they contain DIRECT answers.
"""
    
    return prompt

def find_relevant_files(question: str, file_index: List[Dict[str, Any]], llm_client) -> List[Dict[str, Any]]:
    """Find files relevant to a question using the LLM."""
    # Process files in batches to avoid context limit issues
    batch_size = 5
    file_batches = [file_index[i:i+batch_size] for i in range(0, len(file_index), batch_size)]
    
    all_relevant_files = []
    
    for batch in file_batches:
        if not batch:
            continue
        
        # Generate the prompt for this batch
        prompt = get_matching_prompt(question, batch)
        
        # Get response from LLM
        response = llm_client.generate(prompt)
        
        # Extract and parse JSON
        json_str = extract_json_array(response)
        try:
            results = json.loads(json_str)
            
            # Process results
            for result in results:
                doc_id = result.get("document_id")
                if isinstance(doc_id, int) and 1 <= doc_id <= len(batch):
                    file_info = batch[doc_id-1]
                    if result.get("relevant", False):
                        all_relevant_files.append({
                            "path": file_info["path"],
                            "title": file_info["title"],
                            "confidence": result.get("confidence", "medium"),
                            "reasoning": result.get("reasoning", "")
                        })
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response: {json_str}")
    
    return all_relevant_files

def process_questions(questions: List[str], docs_dir: str, llm_client) -> Dict[str, Any]:
    """Process a list of questions and find relevant files for each."""
    # Create file index once
    print("Creating file index...")
    file_index = create_file_index(docs_dir)
    print(f"Indexed {len(file_index)} files.")
    
    results = {}
    
    for i, question in enumerate(questions, 1):
        print(f"\nProcessing question {i}/{len(questions)}: {question}")
        all_relevant_files = find_relevant_files(question, file_index, llm_client)
        
        # Sort by confidence level (high > medium > low)
        confidence_rank = {"high": 3, "medium": 2, "low": 1}
        sorted_files = sorted(
            all_relevant_files, 
            key=lambda x: confidence_rank.get(x.get("confidence", "low"), 0), 
            reverse=True
        )
        
        # Determine if these documents are sufficient to answer the question
        sufficient = False
        if len(sorted_files) <= 3:
            sufficient = True
        
        results[question] = {
            "files": sorted_files,
            "sufficient": sufficient,
            "total_found": len(all_relevant_files)
        }
        
        # Print progress
        print(f"Found {len(all_relevant_files)} relevant files")
        if not sufficient:
            print("⚠️ The available documents may not sufficiently answer this question")
    
    return results

def main():
    # Initialize LLM client
    llm_client = LLMInterface("bedrock", "us.deepseek.r1-v1:0")
    
    # Get questions from user input or use sample questions
    questions = ['What is Compensation Metrics?',
 'What is compensation plan structure?',
 'What will happen if windfall is triggered?',
 'How different kind of product contributes to Compensation?',
 'What is the Cloud Commitment Plan in SPIFF?',
 'What is Level 3 SPIFF?',
 'What is Cloud Commitment Plan?',
 'How does ACV factor into SPIFF bonus calculations?',
 'How is commission calculated for professional services deals?',
 'Compensation -> How to calculate compensation? -> Request ops for help',
 'What is Collection?',
 'What is Revenue?',
 'What is ACV?',
 'How to calculate ACV?',
 'What is baseline ARR?',
 'What is starting ARR?',
 'What affect baseline ARR?',
 'What are the different Net ARR scenarios?',
 'What are the criteria for revenue to be included in ARR?',
 'Does TiDB Serverless Revenue meet ARR inclusion criteria?',
 'What is the impact of applying credits on ARR?',
 'How is NetARR calculated?',
 'How is ARR calculated for a contract starting in a future fiscal period?',
 'Why does NetARR differ from Contract Price (CP)?',
 'What is Lead in SFDC?',
 'What is lead assignment process?',
 'What is SKA/KA criterion?',
 'How does ARR relate to customer classification?',
 'Which companies are included in the SKA/KA list?',
 'Which companies are included in the ICP list?',
 'Which industry are included in the ICP list?',
 "What ARR threshold qualifies a customer as 'brand new'?",
 'How to create account?',
 'What fields are the Opportunity contain?',
 'How to create Opportunity?',
 'What are the Opportunity stages in Salesforce?',
 'How to create a quote for a Salesforce opportunity?',
 'How to handle Usage Issue?',
 'What is the definition of the Commit pipeline?',
 'How to register Salesforce Authenticator?',
 'How to apply for Salesforce access?',
 'What is credits?',
 'Ops Portal -> Credits -> How to apply credits? -> External Use',
 'Ops Portal -> Credits -> How to apply credits? -> Internal Use',
 'Who is the Sales ops representative for the EMEA team?',
 'How to download salesforce in China?']
    # Path to docs directory
    docs_dir = "./docs"
    
    # Process questions
    results = process_questions(questions, docs_dir, llm_client)
    
    # Display results
    print("\n\nFinal Results:")
    print("====================")
    for question, result in results.items():
        print(f"\nQuestion: {question}")
        
        if not result["files"]:
            print("  No relevant files found.")
            print("  ⚠️ Information is too scattered. Consider optimizing documentation.")
            continue
            
        print(f"  Found {result['total_found']} relevant documents, showing top {len(result['files'])}")
        
        if not result["sufficient"]:
            print("  ⚠️ Information is too scattered. Consider optimizing documentation.")
        
        print("  Top relevant files:")
        for file in result["files"]:
            confidence = file.get("confidence", "medium")
            confidence_marker = "🟢" if confidence == "high" else "🟡" if confidence == "medium" else "🟠"
            print(f"    {confidence_marker} {os.path.basename(file['path'])}")
            print(f"       Reason: {file.get('reasoning', 'No reasoning provided')[:100]}..." if len(file.get('reasoning', '')) > 100 else f"       Reason: {file.get('reasoning', 'No reasoning provided')}")
    
    # Save detailed results to JSON file
    with open("question_file_matches_index.json", "w", encoding="utf-8") as f:
        # Convert the results to a serializable format
        serializable_results = {}
        for question, result in results.items():
            serializable_results[question] = {
                "files": [{
                    "file": os.path.basename(file["path"]),
                    "confidence": file.get("confidence", "medium"),
                    "reasoning": file.get("reasoning", "")
                } for file in result["files"]],
                "sufficient": result["sufficient"],
                "total_found": result["total_found"]
            }
        
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    print("\nDetailed results saved to question_file_matches_top3.json")

if __name__ == "__main__":
    main() 