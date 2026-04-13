from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from typing import Iterator, TypedDict, Literal
import logging

from langchain_agent.config import MODEL_NAME, OLLAMA_HOST
from langchain_agent.tools import (
    tools,
    ToolEvent,
    ToolOutput,
    get_tool_function,
)

logger = logging.getLogger(__name__)

MAX_CHAIN_LENGTH = 5


class AgentState(TypedDict):
    messages: list[BaseMessage]
    tool_results: list[str]
    chain_depth: int
    pending_approval: dict | None
    retry_count: int
    last_error: str | None


llm = ChatOllama(
    model=MODEL_NAME,
    base_url=OLLAMA_HOST,
)

SYSTEM_PROMPT = """You are a security-focused assistant with access to tools for scanning and file operations.

Available tools and their EXACT parameters:
- read_file(file_path: str) - Read a file from the sandbox directory
- call_api(url: str) - Make an HTTP GET request to a URL. The parameter is "url", NOT "target"
- run_nmap(target: str, options: str = "-sV") - Scan a target for open ports. Requires approval
- run_nuclei(target: str, options: str = "-severity critical,high,medium,low") - Scan a target for vulnerabilities. Requires approval

IMPORTANT RULES:
1. Only use tools when the user's request clearly requires a tool action (scanning, reading files, making HTTP requests)
2. For general questions, conversations, greetings, and explanations, respond directly WITHOUT using any tools
3. If you are unsure whether to use a tool, respond in plain text instead of calling a tool
4. Never call a tool with empty or missing required arguments
5. Respond naturally to conversational input like "hey", "hello", "how are you" without tools
6. Use the EXACT parameter names shown above. call_api uses "url", not "target"
7. When a user asks to scan a target and find vulnerabilities, use run_nuclei with the "target" parameter, not call_api"""


def create_langgraph_agent(event_callback=None):
    """Create a LangGraph-based agent with tool chaining."""

    llm_with_tools = llm.bind_tools(tools)

    tool_map = {t.name: t for t in tools}

    def should_continue(state: AgentState) -> Literal["continue", "end"]:
        """Decide whether to continue chaining or end."""
        messages = state["messages"]
        last_message = messages[-1] if messages else None

        if state.get("pending_approval"):
            return "end"

        last_error = state.get("last_error")
        if last_error:
            return "end"

        if (
            last_message
            and hasattr(last_message, "tool_calls")
            and last_message.tool_calls
        ):
            chain_depth = state.get("chain_depth", 0)
            if chain_depth >= MAX_CHAIN_LENGTH:
                return "end"
            return "continue"

        return "end"

    def greeting_check(state: AgentState) -> Literal["greeting", "continue"]:
        """Check if user is just greeting - no tools needed."""
        messages = state["messages"]
        if not messages:
            return "continue"

        first_msg = messages[0]
        if not hasattr(first_msg, "content"):
            return "continue"

        content = first_msg.content.lower().strip()

        # Words that indicate casual greeting/conversation
        greeting_words = [
            "yo",
            "hi",
            "hey",
            "hello",
            "howdy",
            "greetings",
            "sup",
            "wassup",
            "what's up",
            "whats up",
        ]

        # Phrases about how someone is doing / casual conversation
        casual_words = [
            "how are you",
            "how ya doing",
            "how you doing",
            "how's it going",
            "how is it going",
            "hows it going",
            "what's up",
            "whats up",
            "good morning",
            "good afternoon",
            "good evening",
            "good night",
            "how's life",
            "how is life",
            "wassup",
        ]

        # If it's just a greeting word followed by optional words
        words = content.split()
        if words and words[0] in greeting_words:
            return "greeting"

        # If it's exactly a casual phrase (or close enough)
        for phrase in casual_words:
            if content == phrase or phrase in content:
                return "greeting"

        # If it's a question asking about wellbeing (ends with ?, <=6 words)
        if content.endswith("?") and len(words) <= 6:
            wellbeing_words = ["how", "doing", "going", "feeling"]
            if any(w in words for w in wellbeing_words):
                return "greeting"

        return "continue"

    def greeting_response(state: AgentState) -> AgentState:
        """Respond directly without tools (for greetings)."""
        messages = state["messages"]
        user_msg = messages[0] if messages else None

        responses = {
            "hello": "Hello! How can I help you today?",
            "hi": "Hi there! What can I do for you?",
            "hey": "Hey! Ready to help - what do you need?",
            "howdy": "Howdy! What can I help with?",
            "greetings": "Greetings! How may I assist you?",
            "yo": "Yo! What's up?",
            "sup": "Sup! What can I help you with?",
            "wassup": "Hey! What's going on?",
        }

        if user_msg and hasattr(user_msg, "content"):
            content = user_msg.content.lower().strip()
            words = content.split()
            first_word = words[0] if words else ""

            response_text = "Hey! What can I help you with?"
            if first_word in responses:
                response_text = responses[first_word]
            elif content in responses:
                response_text = responses[content]

            response = AIMessage(content=response_text)
            return {
                "messages": messages + [response],
                "retry_count": 0,
                "last_error": None,
                "chain_depth": 0,
                "pending_approval": None,
                "tool_results": [],
            }

        return call_llm(state)

    def call_llm(state: AgentState) -> AgentState:
        """Call the LLM with current messages."""
        messages = state["messages"]
        system_msg = SystemMessage(content=SYSTEM_PROMPT)
        messages_with_system = [system_msg] + messages

        response = llm_with_tools.invoke(
            messages_with_system,
            config=RunnableConfig(configurable={"thread_id": "main"}),
        )
        return {
            "messages": messages + [response],
            "retry_count": 0,
            "last_error": None,
            "chain_depth": state.get("chain_depth", 0),
            "pending_approval": state.get("pending_approval"),
            "tool_results": state.get("tool_results", []),
        }

    def execute_tool_node(state: AgentState) -> AgentState:
        """Execute a tool and emit events."""
        messages = state["messages"]
        last_message = messages[-1] if messages else None

        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return state

        tool_calls = last_message.tool_calls
        tool_results = list(state.get("tool_results", []))

        last_error = None
        approval_needed = None

        for tc in tool_calls:
            tool_name = tc["name"]
            tool_args = tc.get("args", {})

            if event_callback:
                event_callback(ToolEvent(tool_name, "started"))

            try:
                tool_func = tool_map.get(tool_name)
                if not tool_func:
                    if event_callback:
                        event_callback(ToolEvent(tool_name, "failed", "not found"))
                    result = ToolOutput(
                        status="error",
                        tool=tool_name,
                        output=f"Tool {tool_name} not found",
                    )
                else:
                    result = tool_func.invoke(tool_args)

                if hasattr(result, "status"):
                    if result.status == "approval_required":
                        approval_needed = {
                            "request_id": result.request_id,
                            "tool": tool_name,
                            "args": tool_args,
                        }
                        if event_callback:
                            event_callback(
                                ToolEvent(tool_name, "failed", "approval required")
                            )
                        tool_results.append(f"[approval_required] {result.message}")
                        break

                    if result.status == "success":
                        if event_callback:
                            event_callback(ToolEvent(tool_name, "completed"))
                        tool_results.append(result.output)
                    else:
                        if event_callback:
                            event_callback(
                                ToolEvent(tool_name, "failed", result.output)
                            )
                        tool_results.append(f"[error] {result.output}")
                        last_error = result.output
                        break
                else:
                    if event_callback:
                        event_callback(ToolEvent(tool_name, "completed"))
                    tool_results.append(str(result))

            except Exception as e:
                error_msg = str(e)
                if event_callback:
                    event_callback(ToolEvent(tool_name, "failed", error_msg))
                tool_results.append(f"[error] {error_msg}")
                last_error = error_msg
                break

        if tool_results:
            result_msg = AIMessage(
                content="\n\n".join(tool_results),
                tool_calls=[],
            )
            messages = messages + [result_msg]

        return {
            "messages": messages,
            "tool_results": tool_results,
            "chain_depth": state.get("chain_depth", 0) + len(tool_calls),
            "retry_count": 0,
            "last_error": last_error,
            "pending_approval": approval_needed,
        }

    workflow = StateGraph(AgentState)

    workflow.add_node("greeting_check", lambda s: s)
    workflow.add_node("greeting_response", greeting_response)
    workflow.add_node("llm", call_llm)
    workflow.add_node("tools", execute_tool_node)

    workflow.set_entry_point("greeting_check")

    workflow.add_conditional_edges(
        "greeting_check",
        greeting_check,
        {
            "greeting": "greeting_response",
            "continue": "llm",
        },
    )

    workflow.add_conditional_edges(
        "greeting_response",
        lambda _: END,
        {
            END: END,
        },
    )

    workflow.add_conditional_edges(
        "llm",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "tools",
        should_continue,
        {
            "continue": "llm",
            "end": END,
        },
    )

    return workflow.compile()


agent_executor = None


def get_agent_executor():
    global agent_executor
    if agent_executor is None:
        agent_executor = create_langgraph_agent()
    return agent_executor


def invoke_agent(user_input: str, event_callback=None) -> str:
    """Invoke the agent with user input."""
    try:
        executor = create_langgraph_agent(event_callback)

        response = executor.invoke(
            {
                "messages": [HumanMessage(content=user_input)],
                "tool_results": [],
                "chain_depth": 0,
                "pending_approval": None,
                "retry_count": 0,
                "last_error": None,
            },
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


def stream_agent(user_input: str, event_callback=None) -> Iterator[str]:
    """Stream the agent response with tool events."""
    try:
        executor = create_langgraph_agent(event_callback)

        for event in executor.stream(
            {
                "messages": [HumanMessage(content=user_input)],
                "tool_results": [],
                "chain_depth": 0,
                "pending_approval": None,
                "retry_count": 0,
                "last_error": None,
            },
            config=RunnableConfig(configurable={"thread_id": "main"}),
        ):
            for node_name, node_data in event.items():
                if node_name == "llm":
                    if isinstance(node_data, dict) and "messages" in node_data:
                        messages = node_data["messages"]
                        for msg in messages:
                            if isinstance(msg, AIMessage):
                                content = msg.content
                                if content:
                                    yield content
                elif node_name == "tools":
                    if isinstance(node_data, dict) and "tool_results" in node_data:
                        results = node_data["tool_results"]
                        for result in results:
                            if result.startswith("[approval_required]"):
                                yield f"\n{result}\n"
                            elif result.startswith("[error]"):
                                yield f"\n{result}\n"
                            elif result.strip():
                                yield f"\n{result}\n"
                            else:
                                yield "\n(empty result)\n"
                elif node_name == "greeting_response":
                    if isinstance(node_data, dict) and "messages" in node_data:
                        messages = node_data["messages"]
                        for msg in messages:
                            if isinstance(msg, AIMessage):
                                content = msg.content
                                if content:
                                    yield content

    except ConnectionError as e:
        yield f"[OLLAMA ERROR] Connection failed: {str(e)}"
    except Exception as e:
        yield f"[ERROR] {type(e).__name__}: {str(e)}"


def execute_tool_chain(
    tool_sequence: list, initial_input: str, event_callback=None
) -> Iterator[str]:
    """Execute a sequence of tools with streaming output."""
    context = initial_input

    for i, (tool_name, tool_args) in enumerate(tool_sequence):
        if i >= MAX_CHAIN_LENGTH:
            yield f"\n[chain truncated at {MAX_CHAIN_LENGTH} tools - re-run for remaining steps]\n"
            break

        if event_callback:
            event_callback(ToolEvent(tool_name, "started"))
        yield f"\n[*] Running {tool_name}...\n"

        try:
            tool_func = get_tool_function(tool_name)
            if not tool_func:
                if event_callback:
                    event_callback(ToolEvent(tool_name, "failed", "not found"))
                yield f"\n[✗] {tool_name} not found\n"
                continue

            args = {**tool_args}
            if "input" in args and args["input"] == "__chain__":
                args["input"] = context
            elif "target" in args and args["target"] == "__chain__":
                args["target"] = context

            result = tool_func.invoke(args)

            if hasattr(result, "status"):
                if result.status == "approval_required":
                    if event_callback:
                        event_callback(
                            ToolEvent(tool_name, "failed", "approval required")
                        )
                    yield f"\n[approval_required] {result.request_id}\n"
                    yield result.message
                    return

                if result.status == "success":
                    if event_callback:
                        event_callback(ToolEvent(tool_name, "completed"))
                    context = result.output
                    yield f"{result.output}\n"
                else:
                    if event_callback:
                        event_callback(ToolEvent(tool_name, "failed", result.output))
                    yield f"\n[✗] {tool_name} error: {result.output}\n"
                    break
            else:
                if event_callback:
                    event_callback(ToolEvent(tool_name, "completed"))
                yield f"{str(result)}\n"
                context = str(result)

        except Exception as e:
            if event_callback:
                event_callback(ToolEvent(tool_name, "failed", str(e)))
            yield f"\n[✗] {tool_name} failed: {str(e)}\n"
            break
