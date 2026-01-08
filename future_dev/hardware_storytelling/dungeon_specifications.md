# Specifications from the Dungeon

## Core Concept

The result of hardware-level analysis is **low-level specifications** that influence code from below.

---

## Example: Search Function for 100K Documents

```
SPECIFICATION FROM THE DUNGEON

CONTEXT:
  Function search() with loop over 100K documents
  Computing cosine similarity for each document

ANALYSIS AT HARDWARE LEVEL:

  CPU:
    - 100K loop iterations
    - Each iteration: load document, compute similarity
    - Question: Where are documents stored? Contiguous memory or scattered?

  Cache:
    - If documents in Python list → scattered in memory
    - Each iteration → potential cache miss (100+ cycles)
    - Solution: Store embeddings in contiguous NumPy array

  SIMD:
    - Cosine similarity = dot product + norms
    - Perfect for SIMD vectorization
    - NumPy uses BLAS → already optimized

  Branch:
    - Early exit if similarity < threshold?
    - If threshold varies → unpredictable branches
    - Better: compute all, then filter

  Memory:
    - 100K documents × 384 dimensions × 4 bytes = 150MB
    - Fits in RAM but not in L3 cache
    - Sequential access pattern is key

SPECIFICATIONS (BOTTOM-UP CORRECTIONS):

  1. DATA STRUCTURE:
     - Store embeddings as np.ndarray, not List[List[float]]
     - Contiguous memory → 100x better cache performance

  2. ALGORITHM:
     - Use np.dot for similarity (SIMD-optimized)
     - Avoid Python loops → use vectorized operations
     - Batch computation: all similarities at once

  3. MEMORY LAYOUT:
     - Shape: (N, D) not (D, N) for cache-friendly access
     - dtype: float32 (sufficient precision, half memory)

  4. EARLY TERMINATION:
     - Don't use if threshold variable
     - Compute top-K using np.argpartition (O(N) not O(N log N))

FINAL CODE IMPACT:

  Before (naive):
    similarities = []
    for doc in documents:  # Python loop
        sim = cosine_similarity(query, doc)  # Individual call
        similarities.append(sim)

  After (hardware-aware):
    # Contiguous array, SIMD-optimized
    embeddings = np.array(documents, dtype=np.float32)  
    # Vectorized dot product
    similarities = np.dot(embeddings, query)  
    # O(N) top-K selection
    top_k_indices = np.argpartition(similarities, -k)[-k:]

  Performance Impact:
    - 50-100x speedup from vectorization
    - 10x speedup from cache optimization
    - Total: 500-1000x faster
```

---

## Specification Template

```markdown
# SPECIFICATION FROM THE DUNGEON

## Context
- [What function/component]
- [What operation]
- [Data size and characteristics]

## Hardware Analysis

### CPU
- [Instruction patterns]
- [Loop characteristics]
- [Dependencies]

### Cache
- [Data layout]
- [Access patterns]
- [Expected hit/miss ratio]

### SIMD
- [Vectorization opportunities]
- [Data alignment]
- [Available instructions]

### Branch Prediction
- [Conditional patterns]
- [Predictability]
- [Alternatives]

### Memory
- [Allocation patterns]
- [Total size]
- [Fragmentation risk]

### Security
- [Sensitive data]
- [Side channel risks]
- [Cleanup requirements]

## Bottom-Up Corrections

1. **[Area]**: [Correction]
2. **[Area]**: [Correction]
...

## Final Code Impact

### Before
```python
# naive code
```

### After
```python
# hardware-aware code
```

### Performance Impact
- [Metric]: [Improvement]
```

---

## When to Create Dungeon Specifications

| Scenario | Create Spec? | Reason |
|----------|--------------|--------|
| Hot path (called frequently) | ✅ Yes | Performance critical |
| Large data processing | ✅ Yes | Cache/memory impact |
| Security-sensitive | ✅ Yes | Side channel risks |
| Simple CRUD | ❌ No | Overhead not justified |
| One-time scripts | ❌ No | Not worth optimization |
| Prototyping | ❌ No | Premature optimization |
