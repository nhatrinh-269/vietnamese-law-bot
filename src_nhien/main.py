import json
import time
from enum import Enum
from fastapi import FastAPI
from pydantic import BaseModel
from llama_index.core.llms import MessageRole
from extract_data_from_graph import extract_data_from_graph
from answer_generator import generate_answer
from query_generator import generate_cypher_query_from_keywords, extract_keywords_with_llm
from database import LawGraphQuery
from config import URI


# Initialize FastAPI app
app = FastAPI(
    docs_url="/"
)

graph_query = LawGraphQuery(URI)


class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"


class ChatHistoryItem(BaseModel):
    role: MessageRole
    content: str


# Define the request model for FastAPI
class ChatRequest(BaseModel):
    question: str
    histories: list[ChatHistoryItem] = []
    plan_type: PlanType = PlanType.FREE


# Function to process a question
async def process_question(
    question: str,
    histories: list[ChatHistoryItem] = [],
    plan_type: PlanType = PlanType.FREE
):
    """
    Function to process a question and return an answer.
    """
    # Initialize the graph database connection
    if not graph_query.test_connection():
        return "Error: Unable to connect to the database."

    # Generate Cypher query based on the question
    keywords = extract_keywords_with_llm(question)
    keywords = json.loads(keywords)
    print("Keywords extracted:", keywords)
    dan_su_query, hinh_su_query = generate_cypher_query_from_keywords(keywords)

    # Extract data from the graph database using the generated query
    results_ds, results_hs = extract_data_from_graph(
        dan_su_query, hinh_su_query)

    # Format histories as string
    histories_str = "\n".join(
        [f"{item.role}: {item.content}" for item in histories])

    # Generate an answer based on the question and query results
    answer = generate_answer(
        question,
        histories_str,
        results_ds=str(results_ds),
        results_hs=str(results_hs)
    )

    return answer


@app.post("/chat")
async def process_question_endpoint(data: ChatRequest):
    """
    Endpoint to process a question and return an answer.
    """
    _start_time = time.perf_counter()
    _response = await process_question(
        question=data.question,
        histories=data.histories,
        plan_type=data.plan_type
    )

    return {
        "response": _response,
        "error": None,
        "time": time.perf_counter() - _start_time
    }


@app.exception_handler(Exception)
async def exception_handler(_, exc):
    """Global exception handler."""
    return {
        "response": None,
        "error": str(exc),
        "time": 0
    }
