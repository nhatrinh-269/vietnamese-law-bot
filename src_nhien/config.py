from dotenv import load_dotenv
import os

load_dotenv()  # Tải các biến từ file .env

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
URI = os.getenv("URI")
NEO4J_USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("PASSWORD")