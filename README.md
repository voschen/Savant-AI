# Savant-AI — Headless Async Agent Server

[![CI](https://img.shields.io/badge/ci-pending-lightgrey)](https://github.com/yourname/repo/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-lightgrey.svg)](https://www.python.org)

> **Goal:** Build a production-grade, streaming backend for a local LLM agent that talks to tools via the Model Context Protocol (MCP). This repo contains a phased, trackable checklist for building a headless async agent server with safety, observability, and concurrency in mind.

---

## Table of contents
- [Why this project](#why-this-project)
- [How to use this checklist](#how-to-use-this-checklist)
- [Roadmap / Objectives](#roadmap--objectives)
- [Quick start](#quick-start)
- [Development notes](#development-notes)
- [Contributing](#contributing)
- [License](#license)

---

## Why this project
This is a one-week, high-intensity project gauntlet designed to make you strong at the 20% of skills that produce 80% of an agent's performance: state management, async IO, streaming, observability, and safety. The design targets local LLMs (Ollama / vLLM / HF pipelines) and prioritizes non-blocking architecture and reproducible tests.

---

## Roadmap / Objectives

### Phase 1 — The Engine (Days 1–2)
- [ ] **Create LangGraph FSM core.**  
  *Acceptance criteria:* States implemented: `Thinking`, `CallingTool`, `ParsingError`, `Responding`. State transitions unit-tested.
- [ ] **Define Typed State container.**  
  *Acceptance criteria:* TypedDict or dataclass with `chat_history`, `current_tool_calls`, `token_usage`.
- [ ] **Tool schemas with Pydantic.**  
  *Acceptance criteria:* Every tool has a `Pydantic BaseModel` input spec and output spec; validation is enforced before execution.
- [ ] **Agent class with Dependency Injection.**  
  *Acceptance criteria:* LLM client passed into agent constructor; mock implementations can be swapped in tests.
- [ ] **Minimal local LLM client adapter.**  
  *Acceptance criteria:* Adapter interface (async) defined; example adapter for a local model (stubbed) included.
- [ ] **Unit tests for FSM routing and tool validation.**  
  *Acceptance criteria:* `pytest` tests that mock LLM JSON output and assert correct tool-call routing.

### Phase 2 — Speed & Communication (Days 3–4)
- [ ] **AsyncIO everywhere (non-blocking).**  
  *Acceptance criteria:* All LLM and tool calls are `async` and use `await`; no use of blocking `requests`.
- [ ] **FastAPI WebSocket streaming endpoint.**  
  *Acceptance criteria:* WebSocket streams model tokens to client in near real-time (token-by-token).
- [ ] **Tool runner concurrency.**  
  *Acceptance criteria:* Concurrent tool calls use `asyncio.gather` and are tested for correctness and time savings.
- [ ] **I/O hygiene: httpx + aiofiles.**  
  *Acceptance criteria:* Network tool implementations use `httpx.AsyncClient`; file I/O uses `aiofiles` or threadpool where needed.
- [ ] **MCP protocol message framing.**  
  *Acceptance criteria:* Implement MCP request/response framing for tools with examples.

### Phase 3 — Bulletproofing (Days 5–6)
- [ ] **Structured JSONL logging.**  
  *Acceptance criteria:* Every LangGraph state transition appends JSONL with `timestamp`, `state`, `active_tool`, `latency`, `token_usage`.
- [ ] **Context (sliding) window memory.**  
  *Acceptance criteria:* Sliding window truncates oldest messages when token estimate exceeds threshold; tests confirm behavior.
- [ ] **In-memory caching (hash map / LRU).**  
  *Acceptance criteria:* Tool calls with identical validated params return cached result; cache hit/miss metrics logged.
- [ ] **Mocked unit/integration tests.**  
  *Acceptance criteria:* Test suite mocks LLM to return a tool-call JSON; asserts the agent executes tool and responds correctly without GPU.
- [ ] **Basic observability metrics.**  
  *Acceptance criteria:* Expose lightweight counters/timings (requests, tool latency, token counts) via logs or simple `/metrics` endpoint.

### Phase 4 — Edge Cases & Safety (Day 7)
- [ ] **Prompt-injection middleware.**  
  *Acceptance criteria:* Incoming prompts checked/sanitized for common injection vectors; suspicious prompts flagged and logged.
- [ ] **Concurrency safety: locks/semaphores.**  
  *Acceptance criteria:* `asyncio.Lock` or `asyncio.Semaphore` around inference; configurable concurrency limit; tests for simultaneous requests.
- [ ] **Error handling & graceful degradation.**  
  *Acceptance criteria:* Tool failures and malformed LLM outputs mapped to `ParsingError` state; client receives helpful error frames instead of crash.
- [ ] **Rate limiting & resource protection (optional).**  
  *Acceptance criteria:* Basic per-connection limits to avoid OOM or denial-of-service.

### Project-wide tasks (cross-phase)
- [ ] **Repository initialization & folder layout.**  
  *Acceptance criteria:* `README.md`, `pyproject.toml`/`requirements.txt`, `src/`, `tests/`, `examples/`, `docs/`.
- [ ] **CI for tests and lint (mypy, flake8/ruff).**  
  *Acceptance criteria:* GitHub Actions run tests, type checks, and lint on PRs.
- [ ] **Developer docs & CONTRIBUTING.**  
  *Acceptance criteria:* Short docs for running locally, swapping LLM adapters, and writing new tools.
- [ ] **License & CODE_OF_CONDUCT.**  
  *Acceptance criteria:* Choose and add a license (MIT/Apache2) and a basic code of conduct.
- [ ] **Example client & demo.**  
  *Acceptance criteria:* Lightweight JS or Python WebSocket client that demonstrates streaming and tool calls.

### Stretch / Nice-to-have
- [ ] **Persistent cache (Redis) + eviction policy.**
- [ ] **Prometheus + Grafana metrics.**
- [ ] **Authentication & scoped API keys for WebSocket connections.**
- [ ] **Dockerfile and devcontainer for reproducible local setup.**
- [ ] **vLLM / Ollama adapter with GPU batching for higher throughput.**

---

## Quick start
```bash
# create virtualenv + install
python -m venv .venv
source .venv/bin/activate    # on Windows use: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# run tests
pytest -q

# run dev server (example)
uvicorn src.app:app --reload
