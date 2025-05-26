from sqlmodel import Session
from sqlalchemy import text

from setting.db import SessionLocal


def query_entities_by_ids(db: Session, entities_id: list[int]):
    sql = text(
        f"""
        SELECT id, name, description, meta from entities_210001 where id in :entities_id
    """
    )
    res = db.execute(sql, {"entities_id": entities_id})
    entities = {}

    try:
        for row in res.fetchall():
            entities[row.id] = {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "meta": row.meta,
            }
    except Exception as e:
        print("Failed to query entities", e)
        return {}

    return entities


def get_relationship_by_entity_ids(db: Session, entity_ids: list[int]):
    sql = text(
        f"""
        SELECT rel.id, source_entity.name as source_entity_name, target_entity.name as target_entity_name, rel.description, rel.chunk_id
               FROM relationships_210001 as rel
               LEFT JOIN entities_210001 as source_entity ON rel.source_entity_id = source_entity.id
               LEFT JOIN entities_210001 as target_entity ON rel.target_entity_id = target_entity.id
        where rel.source_entity_id in :entity_ids or rel.target_entity_id in :entity_ids
    """
    )
    res = db.execute(sql, {"entity_ids": entity_ids})
    background_relationships = {}

    try:
        for row in res.fetchall():
            background_relationships[row.id] = {
                "id": row.id,
                "source_entity_name": row.source_entity_name,
                "target_entity_name": row.target_entity_name,
                "description": row.description,
                "chunk_id": row.chunk_id,
            }
    except Exception as e:
        print("Failed to get relationships", e)
        return {}

    return background_relationships


def get_relationship_by_ids(db: Session, relationship_ids: list[int]):
    sql = text(
        f"""
        SELECT 
            rel.id, 
            source_entity.name as source_entity_name,
            source_entity.id as source_entity_id,
            target_entity.name as target_entity_name,
            target_entity.id as target_entity_id,
            rel.description, rel.chunk_id, rel.meta, rel.document_id
        FROM relationships_210001 as rel
        LEFT JOIN entities_210001 as source_entity ON rel.source_entity_id = source_entity.id
        LEFT JOIN entities_210001 as target_entity ON rel.target_entity_id = target_entity.id
        where rel.id in :relationship_ids
    """
    )
    res = db.execute(sql, {"relationship_ids": relationship_ids})
    background_relationships = {}

    try:
        for row in res.fetchall():
            background_relationships[row.id] = {
                "id": row.id,
                "source_entity_name": row.source_entity_name,
                "target_entity_name": row.target_entity_name,
                "source_entity_id": row.source_entity_id,
                "target_entity_id": row.target_entity_id,
                "description": row.description,
                "chunk_id": row.chunk_id,
                "document_id": row.document_id,
                "meta": row.meta,
            }
    except Exception as e:
        print("Failed to get relationships", e)
        return {}

    return background_relationships


def get_chunks_by_ids(db: Session, chunk_ids: list[int]):
    if len(chunk_ids) == 0:
        return []

    sql = text(
        f"""
        SELECT id, text, source_uri, document_id from chunks_210001 where id in :chunk_ids
    """
    )
    res = db.execute(sql, {"chunk_ids": chunk_ids})
    background_chunks = []

    try:
        for row in res.fetchall():
            background_chunks.append(
                {
                    "id": row.id,
                    "source_uri": row.source_uri,
                    "text": row.text,
                    "document_id": row.document_id,
                }
            )
    except Exception as e:
        print("Failed to get chunks", e)
        return []

    return background_chunks


def get_documents_by_ids(db: Session, document_ids: list[int]):
    sql = text(
        f"""
        SELECT id, content from documents where id in :document_ids
    """
    )

    try:
        res = db.execute(sql, {"document_ids": document_ids})
        return res.fetchall()
    except Exception as e:
        print("Failed to get documents", e)
        return []


def query_entities_before_date(
    last_modified_before: str, limit: int = 10, table_name: str = "entities_210001"
) -> list[dict]:
    """
    Query entities modified before a specific date.

    Args:
        last_modified_before: Date string in format "YYYY-MM-DD HH:MM:SS"
        limit: Maximum number of results to return (default: 10)
        table_name: Name of the entities table (default: "entities_210001")

    Returns:
        List of dictionaries containing entity name and description

    Example:
        entities = query_entities_before_date("2025-05-26 03:40:00", limit=10)
        for entity in entities:
            print(f"Name: {entity['name']}, Description: {entity['description']}")
    """

    sql_query = f"""
    SELECT name, description
    FROM {table_name}
    WHERE last_modified_at < :last_modified_before
    ORDER BY last_modified_at ASC
    LIMIT :limit
    """

    try:
        with SessionLocal() as db:
            sql = text(sql_query)
            result = db.execute(
                sql, {"last_modified_before": last_modified_before, "limit": limit}
            )

            entities = []
            for row in result.fetchall():
                entity_data = {"name": row.name, "description": row.description}
                entities.append(entity_data)

            print(
                f"Found {len(entities)} entities modified before {last_modified_before}"
            )
            return entities

    except Exception as e:
        print(f"Failed to query entities: {e}")
        return []
