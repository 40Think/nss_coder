# Documentation Patterns

## 4.1 Tickets at Start of Code

**At the start of each file — commented ticket:**
- Why this file was created
- What problem it solves
- How it fits into overall architecture
- Connection with other modules

---

## 4.2 Logging as Documentation

**Code is covered with logging and comments:**
- Each significant operation is logged
- Logs read as narrative about program work
- Log levels reflect operation importance
- Logs contain context, not just facts

### Log Level Guidelines

| Level | Use For |
|-------|---------|
| DEBUG | Variable values, step-by-step flow |
| INFO | Important operations, state changes |
| WARNING | Edge cases, fallbacks, degraded mode |
| ERROR | Failures that need attention |
| CRITICAL | System-breaking issues |

### Example

```python
logger.info("Starting hybrid search", {
    "query": query[:50],
    "top_k": top_k,
    "alpha": alpha,
    "context": "Called from RAG pipeline, user session #12345"
})

logger.debug("Semantic search completed", {
    "results_count": len(semantic_results),
    "top_score": semantic_results[0].score if semantic_results else None,
    "elapsed_ms": elapsed_time
})

logger.warning("No keyword matches found", {
    "query": query,
    "fallback": "Using semantic-only mode",
    "impact": "May miss exact term matches"
})
```

---

## 4.3 Self-Documenting Names

**Comments, function names, terminal output, log entries — all reflect essence with project context:**

### ❌ Bad

```python
def process_data(d):
    return d * 2
```

### ✅ Good

```python
def amplify_embedding_vector_for_semantic_search(embedding_vector):
    """
    Amplify embedding vector by 2x for improved semantic search.
    
    Context: Part of document processing pipeline (stage 3/7).
    Called after normalization, before vector DB indexing.
    
    Args:
        embedding_vector: Normalized vector from sentence-transformers model
        
    Returns:
        Amplified vector for indexing
    """
    return embedding_vector * 2
```

---

## 4.4 Semantic Glue and Vector Sugar

**80-90% of file content is not executable code, but semantic context:**

### Traditional Code
- 80% executable code
- 10-20% comments and documentation

### Our Approach
- 10-20% executable code
- 80-90% **semantic glue and vector sugar**

---

## What is Semantic Glue

- Comments explaining not only "what", but "why" and "how it connects"
- References to specifications, plans, architecture
- Logical descriptions of what happens at each step
- Alternative formulations of the same idea
- Related terms and concepts from domain
- Usage examples directly in comments

---

## File Content Ratio Visualization

```
┌─────────────────────────────────────────────────────┐
│ TRADITIONAL CODE FILE                               │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Executable Code (80%)                           │ │
│ │ ...                                             │ │
│ │ ...                                             │ │
│ │ ...                                             │ │
│ └─────────────────────────────────────────────────┘ │
│ ┌─────────────┐                                     │
│ │ Docs (20%) │                                     │
│ └─────────────┘                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ NSS CODER FILE                                      │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Semantic Glue (80-90%)                          │ │
│ │ - Ticket header                                 │ │
│ │ - Context                                       │ │
│ │ - Requirements                                  │ │
│ │ - Design decisions                              │ │
│ │ - Comments on every line                        │ │
│ └─────────────────────────────────────────────────┘ │
│ ┌───────────┐                                       │
│ │Code (10%) │                                       │
│ └───────────┘                                       │
└─────────────────────────────────────────────────────┘
```

---

## Why This Ratio

1. **AI Context**: All information available for AI processing
2. **Self-Contained**: File understandable without external docs
3. **Regenerable**: Easy to regenerate code from embedded context
4. **Maintainable**: Changes documented alongside code
5. **Holographic**: Each file contains project essence
