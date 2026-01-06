# Deep Research Request: Web Framework Architecture for Local AI Operating System

**Target Agent Role:** Senior Full-Stack Architect with expertise in Django ecosystem, Real-time systems, and AI infrastructure.

---

## 1. Executive Summary (What is NSS?)

**NSS (Neuro-Symbolic System)** is a **local-first AI Operating System for developers**. It's a collection of Python scripts that form an intelligent memory, search, and code analysis pipeline — all running locally on GPU hardware (no cloud APIs).

**The Vision:** An AI-native development environment where:
- Voice becomes the primary input modality
- LLMs analyze, search, and generate code based on total project understanding
- Every script, spec, and document is indexed and semantically searchable
- Multi-agent orchestration handles complex tasks through 10-stage pipelines

**Current State:** We have ~20 Python scripts in `docs/automation/` that work as CLI tools. They need a **unified Web UI** to become an actual "IDE" experience.

---

## 2. Core Subsystems (Scripts That Need Web Integration)

### A. Memory & Indexing Layer
| Script | Purpose | Key Capabilities |
|--------|---------|------------------|
| `index_project.py` | Vector embeddings + Knowledge Graph builder | sentence-transformers, vLLM embeddings, AST parsing |
| `chunk_documents.py` | Semantic document chunking | RAG-ready chunks with metadata |
| `docs_dual_memory.py` | Unified vector search interface | Dual-index (descriptions + code), FAISS-like |

### B. Search & Context Assembly Layer
| Script | Purpose | Key Capabilities |
|--------|---------|------------------|
| `semantic_search.py` | Hybrid keyword/vector search | RRF fusion, fallback modes |
| `search_dependencies.py` | Code dependency graph traversal | LRU cache, NetworkX, transitive deps |
| `search_by_tag.py` | Semantic tag search | `<!--TAG:-->` markers in code |
| `assemble_context.py` | Intelligent context assembly | Multi-source aggregation with scoring |
| `summarize_docs.py` | Document summarization | Extractive summaries |

### C. Voice & LLM Processing Layer
| Script | Purpose | Key Capabilities |
|--------|---------|------------------|
| `voice_server.py` | **THE MONOLITH** (3000+ lines) | Flask, embedded HTML/JS, polling |
| `voice_whisper.py` | Local Whisper.cpp wrapper | GPU transcription, 16kHz WAV |
| `voice_processor.py` | LLM-based text enhancement | vLLM, translate, format as spec/ticket |

### D. Future: Multi-Agent Orchestration (Planned)
- **NSS-Spec IDE:** 10-stage pipeline (Context → Needs → Research → Architecture → Spec → Tickets → Code)
- **Total Recall:** Parallel LLM classification of entire codebase
- **Hypothesis Generator:** LLM generates 10 interpretations of user intent

---

## 3. The Problem: Why Refactor?

### Current Architecture Flaws
1. **God Object:** `voice_server.py` = 3300 lines of Flask + embedded HTML/CSS/JS
2. **Synchronous Blocking:** Flask blocks on Whisper (5-30 sec) and vLLM (2-10 sec)
3. **Global State Hell:** Context, variants, search results stored in Python globals
4. **No Real-time:** Polling every 500ms instead of WebSockets
5. **Fragmented CLI Tools:** Each script is independent, no unified orchestration

### Target State
- **Unified Web UI** with Premium UX (dark theme, visualizations, voice waveforms)
- **Async-first** architecture that doesn't block on heavy AI tasks
- **Modular Django Apps** that encapsulate each subsystem cleanly
- **Scalable** to Multi-Agent workflows (10+ concurrent LLM tasks)

---

## 4. Research Questions (Deliverables)

### A. Framework Selection
1. **Django vs FastAPI:** Given heavy CPU/GPU blocking (Whisper, vLLM), which is better?
   - Django: Mature, ORM, admin, but historically sync
   - FastAPI: Native async, but less "batteries included"
   - **Hybrid?** FastAPI for real-time + Django for CRUD?

2. **ASGI Server:** Daphne vs Uvicorn vs Hypercorn for Django Channels?

### B. Architecture Blueprint
1. **Django Apps Structure:** Propose 4-6 apps with clear boundaries:
   - `apps.memory` (indexing, embeddings, knowledge graph)
   - `apps.search` (semantic, dependencies, tags)
   - `apps.voice` (Whisper, voice_processor)
   - `apps.brain` (vLLM interface, Total Recall)
   - `apps.pipeline` (NSS-Spec stages, multi-agent)
   
2. **Singleton Management:** How to load `VoiceWhisper` (3GB model) and `vLLM` (14GB) once across all workers?
   - Celery workers with pre-fork loading?
   - Separate microservices (FastAPI) for inference?
   - `AppConfig.ready()` pattern?

### C. Real-time Communication
1. **WebSocket Strategy:**
   - Audio streaming from browser → server
   - Progress updates (transcription %, LLM tokens/sec)
   - Search result streaming
   
2. **Celery vs Channels Workers:** For 30-second tasks (Whisper), use Celery or Channels consumer with `run_in_executor`?

### D. Frontend Strategy
Given:
- Need premium, animated UI (not basic form submissions)
- Real-time audio visualization (waveforms)
- Complex state (selected files, hypotheses, context items)
- Developer audience (Electron-like feel)

Options:
1. **Django Templates + HTMX + Alpine.js** (Server-side, simple)
2. **Django Ninja (REST/WebSocket API) + Vue 3** (Decoupled, more work)
3. **Django Ninja + Inertia.js + Vue** (Middle ground)

**Question:** Which gives best balance of dev speed + premium UX?

### E. Data Model Sketch
Propose Django models for:
- `Session` (user interaction session)
- `Transcription` (raw + enhanced + translated)
- `ContextSnapshot` (assembled context for a task)
- `SearchResult` (cached search with scores)
- `Hypothesis` (LLM-generated interpretations)
- `PipelineRun` (NSS-Spec 10-stage execution)

### F. Migration Strategy
How to migrate incrementally without breaking existing CLI workflows?
- Phase 1: Web UI calls existing Python modules directly
- Phase 2: Extract to proper Django services
- Phase 3: Add Celery/Channels async layer

---

## 5. Constraints & Context

### Hardware
- Single workstation with RTX 4090 (24GB VRAM)
- vLLM server always running on localhost:8000
- Whisper.cpp compiled with CUDA

### Non-Negotiables
- **100% Local:** No cloud API calls
- **Preserve CLI:** Scripts must remain usable standalone
- **Voice-first:** Microphone → Text → LLM is the primary flow

### Developer Profile
- Solo developer
- Python expert, Django intermediate, Frontend novice
- Prioritizes: Fast iteration > Enterprise architecture

---

## 6. Expected Output Format

Please provide a **Markdown report** containing:

1. **High-Level Architecture Diagram** (Mermaid)
2. **Django Apps Breakdown** (with responsibilities and boundaries)
3. **Technology Stack Recommendations** (with justification)
4. **Data Model Draft** (Django model skeletons)
5. **WebSocket Flow Diagram** (for voice recording → transcription → response)
6. **Migration Roadmap** (3 phases with milestones)
7. **Code Snippets** for critical patterns:
   - `celery.py` configuration
   - `consumers.py` for WebSocket handling
   - Model singleton registry pattern

---

**End of Research Request**
