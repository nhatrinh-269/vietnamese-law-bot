import os
from llama_index.llms.google_genai import GoogleGenAI

API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")
if API_KEY is None:
    raise ValueError("GOOGLE_GENAI_API_KEY environment variable is not set.")

model = GoogleGenAI(
    model="gemini-2.0-flash",
    api_key=API_KEY,
    temperature=0.1,
)
