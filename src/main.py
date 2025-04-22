import time
from pydantic import BaseModel
from fastapi import FastAPI
from agent import Agents, PlanType, ChatHistoryItem


app = FastAPI(
    title="Vietnamese Law GraphRAG API",
    description="Vietnamese Law GraphRAG API",
    docs_url="/",
)
agent = Agents()


class ChatRequest(BaseModel):
    question: str
    histories: list[ChatHistoryItem] = []
    plan_type: PlanType = PlanType.FREE


@app.get("/healthcheck")
async def healthcheck():
    """Health check endpoint."""
    return {"response": "ok"}


@app.post("/chat")
async def chat_api(data: ChatRequest):
    """API endpoint for chat."""
    _start_time = time.perf_counter()
    _response = await agent.chat(
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
