from loguru import logger
import boto3

from llm.providers.bedrock import BedrockProvider

DOCUMENT_CONTEXT_PROMPT = """
<document>
{doc_content}
</document>
"""

CHUNK_CONTEXT_PROMPT = """
Here is the chunk we want to situate within the whole document
<chunk>
{chunk_content}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk.
Answer only with the succinct context and nothing else.
"""

def gen_situate_context(doc: str, chunk: str, model:str="us.anthropic.claude-3-7-sonnet-20250219-v1:0") -> str:
    credentials = BedrockProvider.get_credentials()
    client = boto3.client("bedrock-runtime", **credentials)

    messages = [
        {
            "role": "user",
            "content": [
                {"text": DOCUMENT_CONTEXT_PROMPT.format(doc_content=doc)},
                {"cachePoint": {"type": "default"}},
                {"text": CHUNK_CONTEXT_PROMPT.format(chunk_content=chunk)},
            ]
        }
    ]

    response = client.converse(
        modelId=model,
        inferenceConfig={
            "maxTokens": 2046,
            "temperature": 0.6,
        },
        messages=messages,
    )
    logger.debug(f"Input tokens: {response['usage']['inputTokens']}")
    logger.debug(f"Output tokens: {response['usage']['outputTokens']}")
    logger.debug(f"Cache creation input tokens: {response['usage']['cacheWriteInputTokens']}")
    logger.debug(f"Cache read input tokens: {response['usage']['cacheReadInputTokens']}")

    answer = None
    reasoning = None
    for message in response["output"]["message"]["content"]:
        if "text" in message:
            answer = message["text"]
        elif "reasoningContent" in message:
            reasoning = message["reasoningContent"]["reasoningText"]["text"]
    if reasoning:
        return f"<think>{reasoning}</think>\n{answer}"
    else:
        return answer
