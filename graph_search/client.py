import logging
import requests
from typing import List, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)

# Define retry strategy
retry_strategy = Retry(
    total=5,  # Total number of retry attempts
    backoff_factor=1,  # Exponential backoff factor
    status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
    allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
    raise_on_status=False,
)

class KnowledgeGraphClient:
    def __init__(self, base_url: str, kb_id: int):
        self.base_url = base_url.rstrip("/")
        self.kb_id = kb_id

        # Create session with retry strategy
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def retrieve_knowledge(
        self, query: str, top_k: int = 10, similarity_threshold: float = 0.5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve knowledge graph data based on a query.
        """
        url = f"{self.base_url}/admin/knowledge_bases/{self.kb_id}/graph/knowledge"
        payload = {
            "query": query,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
        }
        logger.info("retrieve_knowledge with argument: %s", query)

        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RetryError as e:
            logger.error("Max retries exceeded for retrieve_knowledge: %s", str(e))
            raise
        except requests.exceptions.RequestException as e:
            logger.error("Request to retrieve_knowledge failed: %s", str(e))
            raise
        except ValueError as e:
            logger.error(
                "Invalid JSON response received from retrieve_knowledge: %s", str(e)
            )
            raise

    def retrieve_neighbors(
        self,
        entities_ids: List[int],
        query: str,
        max_depth: int = 1,
        max_neighbors: int = 10,
        similarity_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Retrieve neighbor nodes for given entity IDs.
        """
        url = f"{self.base_url}/admin/knowledge_bases/{self.kb_id}/graph/knowledge/neighbors"
        payload = {
            "entities_ids": entities_ids,
            "query": query,
            "max_depth": max_depth,
            "max_neighbors": max_neighbors,
            "similarity_threshold": similarity_threshold,
        }

        logger.info("retrieve_neighbors with arguments: %s, %s", entities_ids, query)

        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RetryError as e:
            logger.error("Max retries exceeded for retrieve_neighbors: %s", str(e))
            raise
        except requests.exceptions.RequestException as e:
            logger.error("Request to retrieve_neighbors failed: %s", str(e))
            raise
        except ValueError as e:
            logger.error(
                "Invalid JSON response received from retrieve_neighbors: %s", str(e)
            )
            raise

    def retrieve_chunks(self, relationships_ids: List[int]):
        """
        Retrieve chunks associated with given relationship IDs.
        """
        url = (
            f"{self.base_url}/admin/knowledge_bases/{self.kb_id}/graph/knowledge/chunks"
        )
        payload = {"relationships_ids": relationships_ids}

        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RetryError as e:
            logger.error("Max retries exceeded for retrieve_chunks: %s", str(e))
            raise
        except requests.exceptions.RequestException as e:
            logger.error("Request to retrieve_chunks failed: %s", str(e))
            raise
        except ValueError as e:
            logger.error(
                "Invalid JSON response received from retrieve_chunks: %s", str(e)
            )
            raise