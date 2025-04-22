import os
from neo4j import GraphDatabase

HOST = os.getenv("NEO4J_HOST", "localhost")
PORT = os.getenv("NEO4J_PORT", "7687")

db = GraphDatabase.driver(f"bolt://{HOST}:{PORT}")
