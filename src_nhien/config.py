import os

GOOGLE_GENAI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")
HOST = os.getenv("NEO4J_HOST", "localhost")
PORT = os.getenv("NEO4J_PORT", "7687")
URI = f"bolt://{HOST}:{PORT}"
