import google.generativeai as genai
from src_nhien.config import GENAI_API_KEY

def LLM_gemini(prompt):
    """
    This function takes a prompt and generates a Cypher query using the Gemini LLM.
    """
    # Set the API key for Google Generative AI
    genai.configure(api_key=GENAI_API_KEY)
    # Call the Gemini LLM with the provided prompt
    model = genai.GenerativeModel("gemini-2.0-flash")
    # Set the model settings (e.g., temperature, max output tokens, etc.)
    model.temperature = 0.7  # Adjusts randomness of the output
    # Generate content based on the prompt
    response = model.generate_content(prompt)
    response = response.text.strip()
    return response