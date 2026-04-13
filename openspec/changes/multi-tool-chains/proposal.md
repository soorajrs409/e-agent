## Why

The agent currently executes tools one-at-a-time in isolation. Users cannot request multi-step workflows (e.g., "scan this IP then run vulnerability checks on the results") without making separate requests. Additionally, tool outputs are hidden until completion, making it difficult to track progress on long-running operations.

## What Changes

- **Tool chaining**: Agent can execute multiple tools in sequence based on user intent
- **Live streaming**: Tool outputs stream in real-time as each tool executes
- **Adaptive execution**: LLM decides tool order and dependencies on-the-fly
- **Approval handling**: Mid-chain approvals pause execution until granted
- **Error recovery**: Alternate options attempted, but stops on failure

## Capabilities

### New Capabilities

- `multi-tool-chains`: Agent executes sequential tool chains, passing outputs between tools as needed
- `live-tool-streaming`: Real-time streaming of tool execution progress and output

### Modified Capabilities

- (none - new capabilities)

## Impact

- `langchain_agent/agent.py`: New chain orchestration logic
- `langchain_agent/tools.py`: Tool event emission for streaming
- `main.py`: Streaming output handling in CLI loop