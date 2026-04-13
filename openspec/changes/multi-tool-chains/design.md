## Context

The agent uses LangChain's `create_agent` which executes tools one-at-a-time and returns output to the LLM. This is adequate for single-tool calls but insufficient for multi-tool workflows where outputs from one tool feed into the next.

**Current flow:**
```
User → LLM decides tool → Execute tool → Return to LLM → LLM responds
```

**Desired flow:**
```
User → LLM decides chain → Tool 1 executes + streams → [approval if needed]
→ Tool 2 executes + streams → ... → LLM responds
```

## Goals / Non-Goals

**Goals:**
- Agent can chain multiple tools sequentially based on user intent
- Each tool's output streams live as it executes
- LLM decides tool order and dependencies adaptively on-the-fly
- Mid-chain approvals pause execution until granted
- Alternate tool on error, but stop if no alternatives work

**Non-Goals:**
- Parallel tool execution (not in scope)
- User-defined pipelines/predefined workflows
- Rollback mechanics
- Automatic retry with backoff

## Decisions

### D1: LangGraph-based orchestration vs custom loop

**Decision**: Use LangGraph

**Rationale**:
- Already in dependencies (`langgraph`)
- Provides explicit state management for tool chains
- Supports streaming via `stream` method
- Easier to maintain than custom orchestration code

**Alternative considered**: Custom agent loop with manual state tracking
- Rejected: Higher complexity, reinventing wheel

### D2: How to pass tool outputs to next tool

**Decision**: Context injection via tool description parsing

**Approach**:
1. Execute tool 1, capture output in state
2. Include output in next tool's invocation context via modified prompt/args
3. For file-reading → nmap chains: extract IPs/hosts from output text

**Rationale**: Simple, works with existing tools without modification

**Alternative**: Create wrapper tools like `read_then_scan`
- Rejected: Explodes combinatorially, not scalable

### D3: Streaming architecture

**Decision**: Event-based streaming with tool lifecycle hooks

```
Tool starts  → yield "[*] Running tool_name..."
Tool output  → yield content chunks
Tool ends    → yield "[✓] Completed"
```

**Rationale**:
- Clean separation between tool execution and display
- Matches existing streaming pattern in main.py
- Easy to add progress indicators

### D4: Approval handling in chains

**Decision**: Yield-and-pause with state persistence

**Flow**:
1. Tool requests approval → yield approval message
2. Store pending chain state (which tool, args, next steps)
3. On `/approve` → resume from stored state
4. On `/deny` → terminate chain, report failure

**Rationale**: Matches existing approval system, minimal changes

### D5: Error recovery - alternate options

**Decision**: LLM-driven fallback with single retry

**Flow**:
1. Execute tool → error returned
2. Pass error to LLM with prompt: "Try alternate tool?"
3. If LLM suggests alternate → execute alternate
4. If no alternate or alternate fails → terminate chain

**Rationale**:
- LLM has context to make smart fallback decisions
- Single retry prevents infinite loops

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|---------|------------|
| Tool output format varies, hard to parse for next tool | Chain breaks | LLM uses text extraction, accept imperfect passthrough |
| Infinite tool loops | Resource exhaustion | Max 5 tools per chain, then force end |
| Approval during chain confuses user | Poor UX | Clear message: "waiting for approval, N tools pending" |
| Partial results lost on error | Debugging hard | Log each tool's output before proceeding |

## Migration Plan

1. **Phase 1**: Add tool event emission (started/completed)
2. **Phase 2**: Update stream_agent to show tool events
3. **Phase 3**: Add chain detection (LLM requests 2+ tools)
4. **Phase 4**: Implement sequential execution with streaming
5. **Phase 5**: Add approval pausing in chains
6. **Phase 6**: Add error recovery with fallback

Rollback: Revert to single-tool execution, disable chaining flag

## Open Questions

- **Q1**: Should we expose chain status via a command like `/chain-status`?
- **Q2**: Max chain length? Currently suggest 5, is that reasonable?
- **Q3**: Should we log each tool's output to a separate file in `scans/` for traceability?