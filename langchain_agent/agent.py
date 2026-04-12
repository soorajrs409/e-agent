from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from typing import Union, Iterator

from langchain_agent.config import MODEL_NAME, OLLAMA_HOST, AGENT_NAME
from langchain_agent.tools import tools


SYSTEM_PROMPT = """You are a helpful AI assistant. You have access to tools.

IMPORTANT: Only use tools when the user asks for specific information or actions.

Use tools ONLY when:
- User asks to read a file → use read_file
- User asks to fetch/visit a URL → use call_api
- User asks to scan/network map → use run_nmap

Do NOT use tools for:
- Greetings ("hello", "hi", "hey")
- Simple questions ("how are you", "what's up")
- General knowledge ("what is DNS", "tell me about X")
- Casual conversation

When not using tools, just respond naturally and helpfully."""


llm = ChatOllama(
    model=MODEL_NAME,
    base_url=OLLAMA_HOST,
)

agent_executor = create_agent(llm, tools, system_prompt=SYSTEM_PROMPT)


def invoke_agent(user_input: str) -> str:
    """Invoke the agent with user input.

    Args:
        user_input: The user's message

    Returns:
        Agent response as string
    """
    try:
        response = agent_executor.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=RunnableConfig(configurable={"thread_id": "main"}),
        )

        messages = response.get("messages", [])
        if not messages:
            return "[ERROR] No messages in response"

        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                content = msg.content
                if content:
                    return content

        return "[ERROR] No response content"

    except ConnectionError as e:
        return f"[OLLAMA ERROR] Connection failed: {str(e)}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {str(e)}"


def stream_agent(user_input: str) -> Iterator[str]:
    """Stream the agent response token by token.

    Args:
        user_input: The user's message

    Yields:
        Response chunks as strings
    """
    try:
        for event in agent_executor.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=RunnableConfig(configurable={"thread_id": "main"}),
        ):
            for node_name, node_data in event.items():
                if isinstance(node_data, dict) and "messages" in node_data:
                    messages = node_data["messages"]
                    for msg in messages:
                        if isinstance(msg, AIMessage):
                            content = msg.content
                            if content:
                                yield content
                        elif hasattr(msg, "name") and msg.name in [
                            "read_file",
                            "call_api",
                            "run_nmap",
                        ]:
                            yield f"\n[Using tool: {msg.name}]\n"

    except ConnectionError as e:
        yield f"[OLLAMA ERROR] Connection failed: {str(e)}"
    except Exception as e:
        yield f"[ERROR] {type(e).__name__}: {str(e)}"
