import logging
import json
import os
import pandas as pd
from typing import Tuple
import concurrent.futures

from graph_opt.helper import GRAPH_OPTIMIZATION_ACTION_SYSTEM_PROMPT_WO_MR
from graph_opt.evaluator import evaluate_issue
from graph_search.client import KnowledgeGraphClient
from graph_opt.helper import extract_issues
from graph_search.concrete_search import graph_retrieve
from utils.json_utils import extract_json
from llm.factory import LLMInterface
from graph_opt.models.entity import get_entity_model
from graph_opt.models.relationship import get_relationship_model
from graph_opt.optimizer import (
    process_entity_quality_issue,
    process_redundancy_entity_issue,
    process_relationship_quality_issue,
    process_redundancy_relationship_issue,
)
from llm.embedding import (
    get_text_embedding,
    get_entity_description_embedding,
    get_entity_metadata_embedding,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create logger
logger = logging.getLogger(__name__)

optimization_llm_client = LLMInterface("openai_like", "graph_optimization_14b")

gemini_critic_client = LLMInterface("gemini", "gemini-2.5-pro-preview-03-25")
sonnet_critic_client = LLMInterface(
    "bedrock", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
)
deepseek_critic_client = LLMInterface("bedrock", "us.deepseek.r1-v1:0")
critic_clients = {
    "gemini-2.5-pro-critic": gemini_critic_client,
    "sonnet-3.7-critic": sonnet_critic_client,
    "deepseek-R1-critic": deepseek_critic_client,
}

knowledge_client = KnowledgeGraphClient("https://tidb.ai/api/v1", 210001)
Entity = get_entity_model("entities_210001", 1536)
Relationship = get_relationship_model("relationships_210001", 1536)


def get_issue_key(issue: dict) -> Tuple[str, tuple]:
    """Generate a unique key for an issue based on its type and affected IDs."""
    return (issue["issue_type"], tuple(sorted(issue["affected_ids"])))


def improve_graph(query: str, tmp_test_data_file: str = "test_data.pkl"):
    if os.path.exists(tmp_test_data_file):
        issue_df = pd.read_pickle(tmp_test_data_file)
    else:
        issue_df = pd.DataFrame(
            columns=[
                "graph",
                "question",
                "issue",
                "confidence",
                "sonnet-3.7-critic",
                "deepseek-R1-critic",
                "gemini-2.5-pro-critic",
                "resolved",
            ]
        )

    new_issue_list = []
    # if having unresolved issue, we need to handle these issue first
    # if no issue need to be critized, we need to retrieve new issues
    if (
        issue_df[
            (issue_df["resolved"] == False) & (issue_df["confidence"] >= 1.8)
        ].shape[0]
        == 0
        and issue_df[
            ["sonnet-3.7-critic", "deepseek-R1-critic", "gemini-2.5-pro-critic"]
        ]
        .notnull()
        .all()
        .all()
    ):
        print(
            "no unresolved issue and all issues have complete critic evaluations, retrieving new issues"
        )
        retrieval_results = graph_retrieve(
            sonnet_critic_client,
            knowledge_client,
            query,
            top_k=30,
            max_iterations=3,
            similarity_threshold=0.3,
            enable_optimization=False,
        )

        graph_data = {
            "entities": retrieval_results["entities"],
            "relationships": retrieval_results["relationships"],
        }

        prompt = (
            GRAPH_OPTIMIZATION_ACTION_SYSTEM_PROMPT_WO_MR
            + " Now Optimize the following graph:\n"
            + json.dumps(graph_data, indent=2, ensure_ascii=False)
        )
        response = optimization_llm_client.generate(prompt)

        analysis_list = extract_issues(response)
        print("analysis:", analysis_list)
        for analysis in analysis_list.values():
            for issue in analysis:
                issue_data = {
                    "graph": graph_data,
                    "question": "what is write hotspot?",
                    "issue": issue,
                    "confidence": 0.0,
                    "sonnet-3.7-critic": None,
                    "deepseek-R1-critic": None,
                    "gemini-2.5-pro-critic": None,
                    "resolved": False,
                }
                new_issue_list.append(issue_data)

        if len(new_issue_list) > 0:
            issue_df = pd.concat([issue_df, pd.DataFrame(new_issue_list)])

    issue_df.to_pickle(tmp_test_data_file)

    print(f"Found new issues {len(new_issue_list)}, total issues {issue_df.shape[0]}")

    for row in new_issue_list:
        print(index, row["issue"])

    print("=" * 60)

    # if there are issue that need to be critized, we need to evaluate them
    while (
        issue_df[["sonnet-3.7-critic", "deepseek-R1-critic", "gemini-2.5-pro-critic"]]
        .isnull()
        .any()
        .any()
    ):
        issue_df = evaluate_issue(critic_clients, issue_df)
    print(f"Identified {issue_df[issue_df['confidence'] >= 1.8].shape[0]} valid issues")

    issue_cache = {}
    for index, row in issue_df.iterrows():
        if row["resolved"] is not True:
            continue

        if (
            row["issue"]["issue_type"] == "entity_quality_issue"
            or row["issue"]["issue_type"] == "relationship_quality_issue"
        ):
            for affected_id in row["issue"]["affected_ids"]:
                issue = {
                    "issue_type": row["issue"]["issue_type"],
                    "affected_ids": [affected_id],
                    "reasoning": row["issue"]["reasoning"],
                }
                issue_cache[get_issue_key(issue)] = True
        else:
            issue_cache[get_issue_key(row["issue"])] = True

    print("issue is resolved", issue_cache, len(issue_cache))

    ## process entity quality issue

    pending_entity_quality_issue_list = {}
    for index, row in issue_df.iterrows():
        if (
            row["issue"]["issue_type"] != "entity_quality_issue"
            or row["confidence"] < 1.8
            or row["resolved"] is True
        ):
            continue

        # Check if any entities need processing
        for affected_id in row["issue"]["affected_ids"]:
            issue = {
                "issue_type": row["issue"]["issue_type"],
                "reasoning": row["issue"]["reasoning"],
                "affected_ids": [affected_id],
                "row_index": index,
            }
            issue_key = get_issue_key(issue)
            if (
                issue_cache.get(issue_key, False)
                or pending_entity_quality_issue_list.get(issue_key, None) is not None
            ):
                continue
            issue["issue_key"] = issue_key
            pending_entity_quality_issue_list[issue_key] = issue

    print(
        "pendding entity quality issues number", len(pending_entity_quality_issue_list)
    )

    parallel_count = 5
    while True:
        # Find up to 3 issues that need processing
        keys_for_batch = []
        for key in pending_entity_quality_issue_list:
            if len(keys_for_batch) < parallel_count:
                keys_for_batch.append(key)
            else:
                break

        # Exit if no more rows to process
        if len(keys_for_batch) == 0:
            break

        batch_issues = []
        for key in keys_for_batch:
            batch_issues.append(pending_entity_quality_issue_list.pop(key))

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(batch_issues)
        ) as executor:
            futures = {}
            for row_issue in batch_issues:
                futures[
                    executor.submit(
                        process_entity_quality_issue,
                        optimization_llm_client,
                        Entity,
                        Relationship,
                        row_issue["row_index"],
                        row_issue,
                    )
                ] = row_issue["issue_key"]

            # Process results and update dataframe
            for future in concurrent.futures.as_completed(futures):
                issue_key = futures[future]
                success = future.result()
                if success:
                    issue_cache[issue_key] = True

    for index, row in issue_df.iterrows():
        if (
            row["issue"]["issue_type"] != "entity_quality_issue"
            or row["confidence"] < 1.8
            or row["resolved"] is True
        ):
            continue
        success = True
        for affected_id in row["issue"]["affected_ids"]:
            tmp_key = get_issue_key(
                {
                    "issue_type": row["issue"]["issue_type"],
                    "reasoning": row["issue"]["reasoning"],
                    "affected_ids": [affected_id],
                }
            )
            if issue_cache.get(tmp_key, False) is False:
                success = False
                break
        if success:
            print(f"Success to resolve entity {index}")
            issue_df.at[index, "resolved"] = True

    # Save dataframe after each batch
    issue_df.to_pickle(tmp_test_data_file)

    ## process redundancy entity issue

    pending_redundancy_entity_issue_list = {}
    for index, row in issue_df.iterrows():
        if (
            row["issue"]["issue_type"] != "redundancy_entity"
            or row["confidence"] < 1.8
            or row["resolved"] is True
        ):
            continue

        affected_ids = set(row["issue"]["affected_ids"])
        need_merge_ids = set(affected_ids)
        need_merge_reasoning = set([row["issue"]["reasoning"]])
        handled_index = set([index])

        found = True
        while found:
            found = False
            for other_row_index, other_row in issue_df.iterrows():
                if other_row_index == index or other_row_index in handled_index:
                    continue
                if (
                    other_row["issue"]["issue_type"] != "redundancy_entity"
                    or other_row["confidence"] < 1.8
                    or other_row["resolved"] is True
                ):
                    continue
                other_affected_ids = set(other_row["issue"]["affected_ids"])
                if need_merge_ids.isdisjoint(other_affected_ids):
                    continue

                handled_index.add(other_row_index)
                need_merge_ids.update(other_row["issue"]["affected_ids"])
                need_merge_reasoning.add(other_row["issue"]["reasoning"])
                found = True

        if len(need_merge_ids) > 1:
            redundancy_entity_issue = {
                "issue_type": "redundancy_entity",
                "affected_ids": list(need_merge_ids),
                "reasoning": "\n".join(list(need_merge_reasoning)),
                "row_indexes": list(handled_index),
            }

            issue_key = get_issue_key(redundancy_entity_issue)
            if pending_redundancy_entity_issue_list.get(
                issue_key, None
            ) is not None or issue_cache.get(issue_key, False):
                continue

            redundancy_entity_issue["issue_key"] = issue_key
            pending_redundancy_entity_issue_list[issue_key] = redundancy_entity_issue

    print(
        "pendding redundancy entity number", len(pending_redundancy_entity_issue_list)
    )

    # Main processing loop with batched concurrency
    parallel_count = 3
    while True:
        # Find up to 3 issues that need processing
        keys_for_batch = []
        for key in pending_redundancy_entity_issue_list:
            if len(keys_for_batch) < parallel_count:
                keys_for_batch.append(key)
            else:
                break

        # Exit if no more rows to process
        if len(keys_for_batch) == 0:
            break

        batch_issues = {}
        for key in keys_for_batch:
            batch_issues[key] = pending_redundancy_entity_issue_list.pop(key)

        # Process batch concurrently
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(batch_issues)
        ) as executor:
            futures = {}
            for row_issue in batch_issues.values():
                futures[
                    executor.submit(
                        process_redundancy_entity_issue,
                        optimization_llm_client,
                        Entity,
                        Relationship,
                        row_issue["issue_key"],
                        row_issue,
                    )
                ] = row_issue["issue_key"]

            # Process results and update dataframe
            for future in concurrent.futures.as_completed(futures):
                issue_key = futures[future]
                success = future.result()
                if success:
                    issue = batch_issues[issue_key]
                    issue_cache[issue_key] = True
                    row_indexes = issue["row_indexes"]
                    for row_index in row_indexes:
                        issue_df.at[row_index, "resolved"] = True

        issue_df.to_pickle(tmp_test_data_file)

    ## process relationship quality issue

    pending_relationship_quality_issue_list = {}
    for index, row in issue_df.iterrows():
        if (
            row["issue"]["issue_type"] != "relationship_quality_issue"
            or row["confidence"] < 1.8
            or row["resolved"] is True
        ):
            continue

        # Check if any entities need processing
        for affected_id in row["issue"]["affected_ids"]:
            issue = {
                "issue_type": row["issue"]["issue_type"],
                "reasoning": row["issue"]["reasoning"],
                "affected_ids": [affected_id],
                "row_index": index,
            }
            issue_key = get_issue_key(issue)
            if (
                issue_cache.get(issue_key, False)
                or pending_relationship_quality_issue_list.get(issue_key, None)
                is not None
            ):
                continue
            issue["issue_key"] = issue_key
            pending_relationship_quality_issue_list[issue_key] = issue

    print(
        "pendding relationship quality issues number",
        len(pending_relationship_quality_issue_list),
    )

    parallel_count = 5
    while True:
        # Find up to 3 issues that need processing
        keys_for_batch = []
        for key in pending_relationship_quality_issue_list:
            if len(keys_for_batch) < parallel_count:
                keys_for_batch.append(key)
            else:
                break

        # Exit if no more rows to process
        if len(keys_for_batch) == 0:
            break

        batch_issues = []
        for key in keys_for_batch:
            batch_issues.append(pending_relationship_quality_issue_list.pop(key))

        # Process batch concurrently

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(batch_issues)
        ) as executor:
            futures = {}
            for row_issue in batch_issues:
                futures[
                    executor.submit(
                        process_relationship_quality_issue,
                        optimization_llm_client,
                        Relationship,
                        row_issue["row_index"],
                        row_issue,
                    )
                ] = row_issue["issue_key"]

            # Process results and update dataframe
            for future in concurrent.futures.as_completed(futures):
                issue_key = futures[future]
                success = future.result()
                if success:
                    print(f"Success to resolve relationship {issue_key}")
                    issue_cache[issue_key] = True

    for index, row in issue_df.iterrows():
        if (
            row["issue"]["issue_type"] != "relationship_quality_issue"
            or row["confidence"] < 1.8
            or row["resolved"] is True
        ):
            continue
        success = True
        for affected_id in row["issue"]["affected_ids"]:
            tmp_key = get_issue_key(
                {
                    "issue_type": row["issue"]["issue_type"],
                    "reasoning": row["issue"]["reasoning"],
                    "affected_ids": [affected_id],
                }
            )
            if issue_cache.get(tmp_key, False) is False:
                success = False
                break
        if success:
            print(f"Success to resolve entity {index}")
            issue_df.at[index, "resolved"] = True

    # Save dataframe after each batch
    issue_df.to_pickle(tmp_test_data_file)

    ## process redundancy relationship issue

    pending_redundancy_relationships_issue_list = {}
    for index, row in issue_df.iterrows():
        if (
            row["issue"]["issue_type"] != "redundancy_relationship"
            or row["confidence"] < 1.8
            or row["resolved"] is True
        ):
            continue

        affected_ids = set(row["issue"]["affected_ids"])
        need_merge_ids = set(affected_ids)
        need_merge_reasoning = set([row["issue"]["reasoning"]])
        handled_index = set([index])

        found = True
        while found:
            found = False
            for other_row_index, other_row in issue_df.iterrows():
                if other_row_index == index or other_row_index in handled_index:
                    continue
                if (
                    other_row["issue"]["issue_type"] != "redundancy_relationship"
                    or other_row["confidence"] < 1.8
                    or other_row["resolved"] is True
                ):
                    continue
                other_affected_ids = set(other_row["issue"]["affected_ids"])
                if need_merge_ids.isdisjoint(other_affected_ids):
                    continue

                handled_index.add(other_row_index)
                need_merge_ids.update(other_row["issue"]["affected_ids"])
                need_merge_reasoning.add(other_row["issue"]["reasoning"])
                found = True

        if len(need_merge_ids) > 1:
            redundancy_relationship_issue = {
                "issue_type": "redundancy_relationship",
                "affected_ids": list(need_merge_ids),
                "reasoning": "\n".join(list(need_merge_reasoning)),
                "row_indexes": list(handled_index),
            }

            issue_key = get_issue_key(redundancy_relationship_issue)
            if pending_redundancy_relationships_issue_list.get(
                issue_key, None
            ) is not None or issue_cache.get(issue_key, False):
                continue

            redundancy_relationship_issue["issue_key"] = issue_key
            pending_redundancy_relationships_issue_list[issue_key] = (
                redundancy_relationship_issue
            )

    print(
        "pendding redundancy relationships number",
        len(pending_redundancy_relationships_issue_list),
    )

    # Main processing loop with batched concurrency

    parallel_count = 5
    while True:
        # Find up to 3 issues that need processing
        keys_for_batch = []
        for key in pending_redundancy_relationships_issue_list:
            if len(keys_for_batch) < parallel_count:
                keys_for_batch.append(key)
            else:
                break

        # Exit if no more rows to process
        if len(keys_for_batch) == 0:
            break

        batch_issues = {}
        for key in keys_for_batch:
            batch_issues[key] = pending_redundancy_relationships_issue_list.pop(key)

        # Process batch concurrently
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(batch_issues)
        ) as executor:
            futures = {}
            for row_issue in batch_issues.values():
                futures[
                    executor.submit(
                        process_redundancy_relationship_issue,
                        optimization_llm_client,
                        Relationship,
                        row_issue["issue_key"],
                        row_issue,
                    )
                ] = row_issue["issue_key"]

            # Process results and update dataframe
            for future in concurrent.futures.as_completed(futures):
                issue_key = futures[future]
                success = future.result()
                if success:
                    issue = batch_issues[issue_key]
                    issue_cache[issue_key] = True
                    row_indexes = issue["row_indexes"]
                    for row_index in row_indexes:
                        issue_df.at[row_index, "resolved"] = True

        issue_df.to_pickle(tmp_test_data_file)
