# Microfunction Assembly and IDE Preview

## Stage 3: Holographic Code Pie (continued)

### File Structure

**At beginning of code:**
- Specification from Stage 2
- Ticket for this function
- How to write AI-native code

**In code:**
All from Stages 1-2 fused with code:
- Comments
- Variable/function names
- CLI commands
- Log templates

**Result:** Code looks like text from distance.
**Goal:** Attract correct tokens, unified vector picture for AI.

---

## 5 Complexity Levels

Use **minimum** level that AI can express essence:

| Level | Description | When to use |
|-------|-------------|-------------|
| **1** | IF/ELSE, loops | Childish code, max simplicity |
| **2** | External packages (import) | If clear and unambiguous |
| **3** | Classes, simple patterns | Moderate complexity |
| **4** | Advanced patterns | Complex abstractions |
| **5** | No restrictions | Standard human practices |

**Selection principle:** Minimum level AI can use to express essence.

---

## Microfunction Assembly

### Stage 1: Generate Microfunctions with Tags

```python
# @assembly:search_pipeline @order:1 @connects_to:rank_results
def fetch_bm25_results_from_keyword_index(query, top_k):
    """
    Gets results from BM25 index (keywords, exact matches)
    
    Why BM25: Finds documents by exact words
    Problem: Doesn't understand synonyms
    """
    keyword_results = bm25_index.search(query, top_k * 2)
    print(f"[LOG] BM25 found {len(keyword_results)} documents")
    return keyword_results

# @assembly:search_pipeline @order:2 @connects_to:rank_results @parallel
def fetch_faiss_results_from_vector_index(query, top_k):
    """Gets results from FAISS (semantics, vectors, synonyms)"""
    vector_results = faiss_index.search(query, top_k * 2)
    return vector_results

# @assembly:search_pipeline @order:3 @depends_on:fetch_bm25,fetch_faiss
def rank_results_via_rrf(bm25_results, faiss_results):
    """Ranks via Reciprocal Rank Fusion (k=60)"""
    return reciprocal_rank_fusion(bm25_results, faiss_results, k=60)
```

### Stage 2: Remove Comments

Script removes all comments except algorithm-readable tags:
- `@assembly:name` — pipeline name
- `@order:N` — execution order
- `@connects_to:func` — connects to which function
- `@depends_on:f1,f2` — dependencies
- `@parallel` — can execute in parallel

### Stage 3: Auto-Assemble

Script analyzes tags and assembles large algorithms:

```python
# Automatically assembled from microfunctions
# @assembly:search_pipeline
def hybrid_search_pipeline(query, top_k):
    bm25_results = fetch_bm25_results_from_keyword_index(query, top_k)  # @order:1 @parallel
    faiss_results = fetch_faiss_results_from_vector_index(query, top_k)  # @order:2 @parallel
    ranked_results = rank_results_via_rrf(bm25_results, faiss_results)   # @order:3
    return ranked_results[:top_k]
```

### Assembly Process (3D Printing Analogy)

1. **Print small parts** (microfunctions with tags)
2. **Break off excess** (remove comments)
3. **Assemble whole by tags** (auto-assembly)
4. **Polish** (optimization, formatting)

---

## IDE Preview Concept

### Core Idea

IDE provides preview of auto-assembled code from microfunctions **without comments** — clean, compact, ready-to-read code formed in background, available on demand.

### Background Auto-Assembly

**When it happens:**
- On file save
- On @assembly tag changes
- Timer (every 30 seconds)
- On demand (hotkey/command)

**Process runs in background**, never blocking developer.

---

## 3 Preview Modes

### Mode 1: "Clean Code"
```python
def hybrid_search_pipeline(query, top_k):
    bm25_results = fetch_bm25_results_from_keyword_index(query, top_k)
    faiss_results = fetch_faiss_results_from_vector_index(query, top_k)
    ranked_results = rank_results_via_rrf(bm25_results, faiss_results)
    return ranked_results[:top_k]
```
- No comments at all
- Minimal volume
- Focus on logic

### Mode 2: "Structural"
```python
# @assembly:search_pipeline
def hybrid_search_pipeline(query, top_k):
    # @order:1 @parallel
    bm25_results = fetch_bm25_results_from_keyword_index(query, top_k)
    # @order:2 @parallel
    faiss_results = fetch_faiss_results_from_vector_index(query, top_k)
    # @order:3 @depends_on:fetch_bm25,fetch_faiss
    ranked_results = rank_results_via_rrf(bm25_results, faiss_results)
    return ranked_results[:top_k]
```
- Assembly tags preserved
- Dependency structure visible

### Mode 3: "Documented"
```python
def hybrid_search_pipeline(query, top_k):
    """Hybrid search: BM25 + FAISS → RRF"""
    # Parallel search in both indexes
    bm25_results = fetch_bm25_results_from_keyword_index(query, top_k)
    faiss_results = fetch_faiss_results_from_vector_index(query, top_k)
    # Merge via Reciprocal Rank Fusion
    ranked_results = rank_results_via_rrf(bm25_results, faiss_results)
    return ranked_results[:top_k]
```
- High-level comments only
- Technical details removed

---

## IDE Interface Options

### A. Split View (Dual Panel)
```
┌─────────────────────┬─────────────────────┐
│ Source microfuncs   │ Assembled code      │
│ (with comments)     │ (without comments)  │
├─────────────────────┼─────────────────────┤
│ # @assembly:...     │ def pipeline():     │
│ def fetch_bm25():   │   bm25 = fetch_bm25 │
│   """Detailed...""" │   faiss = fetch...  │
│   # Step 1: ...     │   return merge(...) │
└─────────────────────┴─────────────────────┘
```
Synchronized scrolling, click highlighting, live updates

### B. Overlay Mode
Toggle button: [👁️ Hide Comments] ↔ [📖 Show Comments]

### C. Preview Tab
Tabs: [Clean] [Structural] [Documented]
Shows: "Generated from 3 microfunctions, last updated: 2s ago"

---

## Optimization Levels

| Level | Type | Actions |
|-------|------|---------|
| **0** | None | Direct microfunction calls |
| **1** | Basic | Inline 1-2 line functions, remove redundant vars |
| **2** | Aggressive | Loop fusion, dead code elimination, constant folding |
