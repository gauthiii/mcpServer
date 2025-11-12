import os
from typing import List, Dict, Any

from neo4j import GraphDatabase
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------
# Neo4j config – from env
# -------------------------------------------------

NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# Single global driver (lazy init)
_driver = None


def _get_driver():
    """Return a singleton Neo4j driver, create it on first use."""
    global _driver

    if _driver is None:
        if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
            raise RuntimeError(
                "NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD must be set in environment"
            )
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        )

    return _driver


def _sanitize_label_or_type(value: str) -> str:
    """Very simple safety: keep only letters, numbers, and underscore."""
    safe = "".join(ch for ch in value if ch.isalnum() or ch == "_")
    if not safe:
        raise ValueError(f"Invalid label/type: {value!r}")
    return safe


# -------------------------------------------------
# MCP server + tools
# -------------------------------------------------

mcp = FastMCP("Neo4j Graph Server")


@mcp.tool()
def init_neo4j() -> str:
    """
    Initialize and verify the Neo4j connection.
    Use this once to check that the MCP server can reach the database.
    """
    driver = _get_driver()
    driver.verify_connectivity()
    return "✅ Connected to Neo4j successfully."


@mcp.tool()
def create_node(label: str, properties: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Create a node with any label and properties.

    Example:
      create_node(
        label="Cartoon",
        properties={"name": "Tom", "role": "cat"}
      )
    """
    driver = _get_driver()
    properties = properties or {}
    safe_label = _sanitize_label_or_type(label)

    query = f"""
    CREATE (n:{safe_label})
    SET n += $props
    RETURN properties(n) AS node
    """

    with driver.session() as session:
        result = session.run(query, props=properties)
        record = result.single()
        return record["node"] if record else {}


@mcp.tool()
def get_nodes(label: str, match: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """
    Get nodes for a label with optional exact-match properties.

    Example:
      get_nodes(label="Cartoon", match={"name": "Tom"})

    If match is empty or null, returns all nodes with that label.
    """
    driver = _get_driver()
    match = match or {}
    safe_label = _sanitize_label_or_type(label)

    base = f"MATCH (n:{safe_label})"
    params: Dict[str, Any] = {}

    if match:
        where_clauses = [f"n.{key} = $props.{key}" for key in match.keys()]
        query = base + " WHERE " + " AND ".join(where_clauses) + " RETURN properties(n) AS node"
        params = {"props": match}
    else:
        query = base + " RETURN properties(n) AS node"

    with driver.session() as session:
        result = session.run(query, **params)
        return [record["node"] for record in result]


@mcp.tool()
def create_relationship(
    from_label: str,
    from_match: Dict[str, Any],
    rel_type: str,
    to_label: str,
    to_match: Dict[str, Any],
    rel_properties: Dict[str, Any] | None = None,
) -> int:
    """
    Create a relationship between two nodes.

    Example:
      create_relationship(
        from_label="Cartoon",
        from_match={"name": "Tom"},
        rel_type="FRIENDS_WITH",
        to_label="Cartoon",
        to_match={"name": "Jerry"},
        rel_properties={"since": 1940}
      )

    Returns the number of relationships created.
    """
    driver = _get_driver()
    rel_properties = rel_properties or {}

    safe_from_label = _sanitize_label_or_type(from_label)
    safe_to_label = _sanitize_label_or_type(to_label)
    safe_rel_type = _sanitize_label_or_type(rel_type)

    if not from_match or not to_match:
        raise ValueError("from_match and to_match must have at least one property each")

    from_where = " AND ".join(f"a.{k} = $from_props.{k}" for k in from_match.keys())
    to_where = " AND ".join(f"b.{k} = $to_props.{k}" for k in to_match.keys())

    query = f"""
    MATCH (a:{safe_from_label})
    WHERE {from_where}
    MATCH (b:{safe_to_label})
    WHERE {to_where}
    CREATE (a)-[r:{safe_rel_type}]->(b)
    SET r += $rel_props
    RETURN count(r) AS relationships_created
    """

    with driver.session() as session:
        result = session.run(
            query,
            from_props=from_match,
            to_props=to_match,
            rel_props=rel_properties,
        )
        record = result.single()
        return record["relationships_created"] if record else 0


@mcp.tool()
def run_cypher(query: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """
    Run any Cypher query.

    Example:
      run_cypher(
        query="MATCH (c:Cartoon) RETURN c.name AS name",
        params={}
      )

    Returns a list of record dicts.
    """
    driver = _get_driver()
    params = params or {}

    with driver.session() as session:
        result = session.run(query, **params)
        return [record.data() for record in result]
    

@mcp.tool()
def delete_nodes(
    label: str,
    match: Dict[str, Any] | None = None,
    detach: bool = True,
) -> int:
    """
    Delete nodes for a label with optional exact-match properties.

    Args:
      label: Node label to match.
      match: Dict of properties to filter nodes (e.g. {"name": "Tom"}).
             If empty/null, deletes ALL nodes with this label.
      detach: If true, use DETACH DELETE to also remove relationships.

    Returns:
      Number of nodes deleted.
    """
    driver = _get_driver()
    match = match or {}
    safe_label = _sanitize_label_or_type(label)

    base = f"MATCH (n:{safe_label})"
    params: Dict[str, Any] = {}

    if match:
        where_clauses = [f"n.{key} = $props.{key}" for key in match.keys()]
        query = base + " WHERE " + " AND ".join(where_clauses)
        params = {"props": match}
    else:
        query = base

    delete_clause = "DETACH DELETE n" if detach else "DELETE n"

    # We have to count BEFORE deleting; we do that via WITH
    query = f"""
    {query}
    WITH collect(n) AS ns, count(n) AS c
    FOREACH (n IN ns | {delete_clause})
    RETURN c AS deleted_count
    """

    with driver.session() as session:
        result = session.run(query, **params)
        record = result.single()
        return record["deleted_count"] if record else 0


@mcp.tool()
def delete_relationship(
    from_label: str,
    from_match: Dict[str, Any],
    rel_type: str,
    to_label: str,
    to_match: Dict[str, Any],
) -> int:
    """
    Delete relationships of a given type between two matched node sets.

    Example:
      delete_relationship(
        from_label="Cartoon",
        from_match={"name": "Tom"},
        rel_type="FRIENDS_WITH",
        to_label="Cartoon",
        to_match={"name": "Jerry"}
      )

    Returns:
      Number of relationships deleted.
    """
    driver = _get_driver()

    safe_from_label = _sanitize_label_or_type(from_label)
    safe_to_label = _sanitize_label_or_type(to_label)
    safe_rel_type = _sanitize_label_or_type(rel_type)

    if not from_match or not to_match:
        raise ValueError("from_match and to_match must have at least one property each")

    from_where = " AND ".join(f"a.{k} = $from_props.{k}" for k in from_match.keys())
    to_where = " AND ".join(f"b.{k} = $to_props.{k}" for k in to_match.keys())

    query = f"""
    MATCH (a:{safe_from_label})
    WHERE {from_where}
    MATCH (b:{safe_to_label})
    WHERE {to_where}
    MATCH (a)-[r:{safe_rel_type}]->(b)
    WITH collect(r) AS rels, count(r) AS c
    FOREACH (r IN rels | DELETE r)
    RETURN c AS deleted_count
    """

    with driver.session() as session:
        result = session.run(
            query,
            from_props=from_match,
            to_props=to_match,
        )
        record = result.single()
        return record["deleted_count"] if record else 0

@mcp.tool()
def list_labels() -> List[str]:
    """
    List all node labels in the database.
    """
    driver = _get_driver()

    # Neo4j 4.x/5.x: CALL db.labels()
    query = "CALL db.labels() YIELD label RETURN label"

    with driver.session() as session:
        result = session.run(query)
        return [record["label"] for record in result]


@mcp.tool()
def list_relationship_types() -> List[str]:
    """
    List all relationship types in the database.
    """
    driver = _get_driver()

    # Neo4j 4.x/5.x: CALL db.relationshipTypes()
    query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"

    with driver.session() as session:
        result = session.run(query)
        return [record["relationshipType"] for record in result]


@mcp.tool()
def get_schema_overview() -> Dict[str, Any]:
    """
    Return a simple schema overview: node labels + relationship types.

    This is safe for agents to call to understand the graph structure.
    """
    driver = _get_driver()

    labels_query = "CALL db.labels() YIELD label RETURN label"
    rels_query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"

    with driver.session() as session:
        labels_result = session.run(labels_query)
        labels = [r["label"] for r in labels_result]

        rels_result = session.run(rels_query)
        rel_types = [r["relationshipType"] for r in rels_result]

    return {
        "labels": labels,
        "relationship_types": rel_types,
    }



if __name__ == "__main__":
    # Example local quick test (uncomment to test without MCP client)
    # print(create_node("Cartoon", {"name": "Spike", "role": "dog"}))
    # print(get_nodes("Cartoon"))
    mcp.run(transport="stdio")
