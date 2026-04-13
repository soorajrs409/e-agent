## 1. Tool Event Emission

- [x] 1.1 Add tool lifecycle events to tools.py (started/completed/failed)
- [x] 1.2 Create ToolEvent class with status and metadata
- [x] 1.3 Modify each tool to emit events at execution boundaries

## 2. Streaming Infrastructure

- [x] 2.1 Update stream_agent to emit tool events to caller
- [x] 2.2 Add event formatting in main.py for consistent display
- [x] 2.3 Test single-tool streaming end-to-end

## 3. Chain Detection

- [x] 3.1 Add multi-tool intent detection in agent.py prompt
- [x] 3.2 Detect when LLM requests 2+ tools in single response
- [x] 3.3 Parse tool order and dependencies from LLM response

## 4. Sequential Execution

- [x] 4.1 Add chain executor that runs tools in sequence
- [x] 4.2 Pass tool outputs to next tool via context injection
- [x] 4.3 Implement max chain length (5 tools) enforcement
- [x] 4.4 Add error passthrough for fallback decisions

## 5. Approval Integration

- [x] 5.1 Modify approval queue to store chain state
- [x] 5.2 Add chain state persistence (which tool, args, next steps)
- [x] 5.3 Update handle_approve to resume from stored state (via re-execute)
- [x] 5.4 Handle /deny to terminate chain

## 6. Error Recovery

- [x] 6.1 Add LLM fallback prompt on tool error
- [x] 6.2 Implement single alternate retry logic
- [x] 6.3 Chain termination with partial results reporting

## 7. Integration Testing

- [x] 7.1 Test read_file → run_nmap chain
- [x] 7.2 Test run_nmap → run_nuclei chain
- [x] 7.3 Test approval mid-chain pause/resume
- [x] 7.4 Test error recovery with alternate
- [x] 7.5 Test chain truncation at 5 tools