import os

from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver


def _get_env(name: str, required: bool = False) -> str | None:
    value = os.getenv(name)
    if value is not None:
        value = value.strip()
    if required and not value:
        raise ValueError(f"Missing required env var: {name}")
    return value or None


def get_neo4j_driver() -> Driver:
    """Build and verify Neo4j driver from .env."""
    load_dotenv()

    uri = _get_env("NEO4J_URI", required=True)
    user = _get_env("NEO4J_USER", required=True)
    password = _get_env("NEO4J_PASSWORD", required=True)

    driver = GraphDatabase.driver(uri, auth=(user, password))
    # Fail fast with a clear message if URI/auth is invalid.
    driver.verify_connectivity()
    return driver


def get_neo4j_database() -> str | None:
    """Optional DB name from env (fallback: None => default DB)."""
    load_dotenv()
    return _get_env("NEO4J_DATABASE")
