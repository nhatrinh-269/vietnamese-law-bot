import sys
import os
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from threading import Thread
import gradio as gr
import json
from dotenv import load_dotenv

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import GENAI_API_KEY, URI, NEO4J_USER, PASSWORD
from src.database import LawGraphQuery
from src.query_generator import generate_cypher_query_from_keywords, extract_keywords_with_llm
from src.answer_generator import generate_answer
from src.extract_data_from_graph import extract_data_from_graph

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Define the request model for FastAPI
class QuestionRequest(BaseModel):
    question: str

# Function to process a question
def process_question(question):
    """
    Function to process a question and return an answer.
    """
    # Check if the required environment variables are set
    if not GENAI_API_KEY or not URI or not NEO4J_USER or not PASSWORD:
        return "Error: Environment variables not set."

    # Initialize the graph database connection
    graph_query = LawGraphQuery(URI, NEO4J_USER, PASSWORD)
    if not graph_query.test_connection():
        return "Error: Unable to connect to the database."

    # Generate Cypher query based on the question
    keywords = extract_keywords_with_llm(question)
    keywords = json.loads(keywords)
    print("Keywords extracted:", keywords)
    dan_su_query, hinh_su_query = generate_cypher_query_from_keywords(keywords)

    # Extract data from the graph database using the generated query
    results_ds, results_hs = extract_data_from_graph(dan_su_query, hinh_su_query)

    # Generate an answer based on the question and query results
    answer = generate_answer(question, str(results_ds), str(results_hs))

    return answer

# FastAPI endpoint
@app.post("/process_question/")
async def process_question_endpoint(request: QuestionRequest):
    """
    Endpoint to process a question and return an answer.
    """
    answer = process_question(request.question)
    return {"question": request.question, "answer": answer}

# Define a function for Gradio UI
def ask_question_gradio(question):
    """
    Function to process a question and return an answer for Gradio UI.
    """
    return process_question(question)

# Create Gradio interface
gr_interface = gr.Interface(
    fn=ask_question_gradio,  # Function to process the question
    inputs="text",           # Input type: text box
    outputs="text",          # Output type: text box
    title="LawHelper",       # Title of the UI
    description="Hãy cho tôi biết bạn cần giúp đỡ gì về pháp lý. Tôi sẽ giúp bạn!"  # Description
)

if __name__ == "__main__":
    # Start FastAPI server
    def run_fastapi():
        uvicorn.run(app, host="0.0.0.0", port=8000)

    # Start Gradio interface
    def run_gradio():
        gr_interface.launch(server_name="0.0.0.0", server_port=7860, share=True)

    # Run both servers in parallel
    Thread(target=run_fastapi).start()
    Thread(target=run_gradio).start()