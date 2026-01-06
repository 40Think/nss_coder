# VoicePal v3 Architecture

**Voice-to-Specification System with Recursive Hypothesis-Driven Search**

> ⚡ **MIGRATION (2025-12-16)**: Whisper backend upgraded from whisper.cpp to **faster-whisper**
> - Performance: **82.7x real-time** on RTX PRO 6000 Blackwell
> - 80 minutes of audio processed in 1 minute
> - See: `voice_whisper_fast.py`

---

## 📊 Visual Architecture

![VoicePal Architecture](file:///home/user/Telegram_Parser/docs/automation/voicepal_architecture.png)

---

## 🔄 System Flow

### Phase 1: Voice Input & Enhancement
```
Voice Audio → faster-whisper (GPU, 82.7x real-time) → Raw Text → Enhancement (vLLM) → Enhanced Text
             ↑ MIGRATED 2025-12-16 from whisper.cpp
```

### Phase 2: Total Recall (Round 1)
```
Enhanced Text → Binary LLM Classification (64 parallel)
    ↓
Scan ALL files (1,254 files in ~25s)
    ↓
YES/NO per file → 5-20 relevant files
```

### Phase 3: Hypothesis Generation (Round 2)
```
Relevant Files → Generate 10 Hypotheses
    ↓
User Selects Hypotheses
    ↓
File Mapping → Refined Search
```

### Phase 4: Dependency Analysis
```
Selected Files → Extract Dependencies
    ↓
Batch Read (64 concurrent)
    ↓
Imports + Callers + Tags + Folder Context
```

### Phase 5: Output Generation
```
Context + Dependencies → Parallel Generation
    ├─ Specification (Markdown)
    ├─ Tickets (10 sub-tasks)
    └─ Documentation
```

### Phase 6: Multi-Agent Execution (Optional)
```
Approved Spec → Task Decomposition
    ↓
10 Sub-tasks → 10 Parallel Agents
    ↓
Code Generation + Logging
```

---

## 📁 File Structure

```
docs/automation/
├── voice_server.py              # Flask server + UI
├── voice_processor.py           # Processing pipeline
├── voice_whisper.py             # Whisper integration (LEGACY - whisper.cpp)
├── voice_whisper_fast.py        # Whisper integration (CURRENT - faster-whisper, 82.7x)
├── whisper_fast.sh              # Wrapper script for LD_LIBRARY_PATH
├── voicepal_architecture.mmd    # Mermaid diagram
├── voicepal_architecture.png    # Visual representation
└── VOICEPAL_INNOVATION_ANALYSIS.md  # Detailed analysis
```

---

## 🔗 Dependencies

### Input Dependencies
- **Audio**: User voice recordings
- **Obsidian Vault**: Ideas/intuitions (optional)
- **Web Search**: External context (optional)

### Core Dependencies
- **faster-whisper**: GPU-accelerated transcription (82.7x real-time) — MIGRATED 2025-12-16
- **vLLM**: LLM inference (localhost:8000)
- **NSS-DOCS**: Dual memory system (embeddings + semantic tags)

### Output Dependencies
- **Specifications**: `docs/specs/`
- **Tickets**: `docs/tickets/`
- **Logs**: `docs/logs/`
- **Documentation**: Updated in NSS-DOCS

---

## 🎯 Key Metrics

| Metric | Value |
|--------|-------|
| **Throughput** | 30,000 tokens/sec (prompt) |
| **Generation** | 2,000-2,500 tokens/sec |
| **Concurrency** | 64 parallel requests |
| **Latency** | ~25s for 1,254 files |
| **Recall** | 95-100% |
| **Precision** | ~90% |

---

## 🚀 Innovation Highlights

1. **Total Recall**: Binary LLM classification instead of embeddings (~25s, 95-100% recall)
2. **Memory Lite**: Fast embedding search with 200 results, first 20 pre-selected (<1s)
3. **Hypothesis-Driven Search**: 10 interpretations → user selection → refinement
4. **Zero Embeddings**: No indexing required for MVP (Total Recall mode)
5. **Voice-First**: Complete workflow from voice to specification
6. **Recursive Refinement**: 2-3 rounds of search with increasing precision

---

## 📖 See Also

- [Innovation Analysis](VOICEPAL_INNOVATION_ANALYSIS.md) - Detailed evaluation (9.2/10)
- [Mermaid Diagram](voicepal_architecture.mmd) - Technical flow diagram
- [Implementation Plan](../../.gemini/antigravity/brain/6cd9df38-9214-476a-a169-455c8a81d993/implementation_plan.md) - Development roadmap

---

**Status**: MVP Complete ✅  
**Version**: 3.0  
**Last Updated**: 2025-12-13
