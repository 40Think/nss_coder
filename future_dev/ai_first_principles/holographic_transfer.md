# Holographic Transfer of Mental Model

## Core Concept

**Mental model transfers from primary input and global architecture into code through tokens that are NOT part of executable code.**

---

## Transfer Channels

### 1. Comments
```python
# WHY: We use numpy for cache locality
# CONTEXT: This is part of the search pipeline
# DECISION: Chose partial sort over full sort because...
```

### 2. Logging
```python
logger.info("Starting batch processing", {"batch_size": 1000, "reason": "memory constraint"})
```

### 3. Function and Variable Names
```python
def search_with_cache_locality(query, documents):
    prefetched_embeddings = preload_contiguous_array(documents)
```

### 4. Terminal Output
```python
print(f"[PERF] Cache hit rate: {hit_rate:.2%}")
print(f"[DEBUG] Using SIMD path: {simd_available}")
```

### 5. Documentation Alongside Code
```python
"""
This module implements semantic search with hardware optimizations.

HARDWARE CONTEXT:
- Designed for 100K+ documents
- Uses numpy for contiguous memory
- SIMD-friendly operations

ARCHITECTURAL CONTEXT:
- Part of the RAG pipeline
- Called by QueryProcessor
- Feeds into ResultRanker
"""
```

### 6. Tickets and Specs in File Headers
```python
"""
# TICKET: SEARCH-001
# TITLE: Implement HybridSearchEngine
# CONTEXT: Part of RAG pipeline...
# REQUIREMENTS: FR1, FR2, NFR1...
# DESIGN DECISIONS: ...
# TESTING STRATEGY: ...
"""
```

---

## Goal

**Reading these tokens, one can understand the function's essence without knowing the entire project.**

---

## Holographic Property

Each part contains information about the whole:

```
┌─────────────────────────────────────┐
│ FUNCTION FILE                       │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Ticket Header (200+ lines)      │ │
│ │ - Full context                  │ │
│ │ - All requirements              │ │
│ │ - Design decisions              │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Executable Code (50-70 lines)   │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Semantic Glue (comments)        │ │
│ │ - Every line explained          │ │
│ │ - WHY, not just WHAT            │ │
│ └─────────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

---

## Ratio

**Ideal file composition:**
- 10-20% executable code
- 80-90% context, comments, documentation

This inverts traditional ratio but optimizes for AI understanding and maintenance.
