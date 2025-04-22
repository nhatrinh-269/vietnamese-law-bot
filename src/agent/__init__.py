from llama_index.core.llms import ChatMessage
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.workflow import Context
from agent.prompt import SYSTEM_PROMPT
from agent.tools import (
    get_chapters_tool,
    get_articles_tool,
    get_articles_content_and_references_tool,
    get_articles_content_tool
)
from configs.gemini import model
from agent.models import *


agent_configs = {
    "name": "Luật sư",
    "description": "Bạn là luật sư chuyên nghiệp.",
    "system_prompt": SYSTEM_PROMPT,
    "llm": model
}


class Agents:
    def __init__(self):
        # Agent for free users
        self.free_agent = ReActAgent(
            **agent_configs,
            tools=[
                get_chapters_tool,
                get_articles_tool,
                get_articles_content_tool
            ]
        )

        # Agent for pro users
        self.pro_agent = ReActAgent(
            **agent_configs,
            tools=[
                get_chapters_tool,
                get_articles_tool,
                get_articles_content_and_references_tool
            ]
        )

    async def chat(
        self,
        question: str,
        histories: list[ChatHistoryItem] = [],
        plan_type: PlanType = PlanType.FREE,
    ) -> str:
        # 1. Get the agent based on the plan type
        agent = self.free_agent if plan_type == PlanType.FREE else self.pro_agent

        # 2. Construct the histories
        chat_histories = []
        for history in histories:
            chat_histories.append(
                ChatMessage(
                    role=history.role,
                    content=history.content.strip()
                )
            )

        # 3. Create a context for the agent
        ctx = Context(agent)

        # 4. Call the agent to get the response
        response = await agent.run(question, chat_history=chat_histories, ctx=ctx)

        # DEBUG: Print context
        for c in ctx.data['memory'].chat_store.store['chat_history']:
            print("\033[90m", c.content, "\033[0m")

        return str(response).strip()
