# Advanced Non-Code Token Patterns

## Category 8: Logging and Print Statements

### Influence on Code Quality
- Logs show AI what's important to track
- Log structure influences code structure
- Log levels (DEBUG, INFO, WARNING, ERROR) set priorities

### Example

```python
def search(query, top_k):
    logger.info(f"Starting search: query='{query}', top_k={top_k}")
    
    # AI understands validation is important (has log)
    if not query:
        logger.warning("Empty query received, returning empty results")
        return []
    
    # AI understands this is critical step (has log)
    logger.debug(f"Searching vector index...")
    semantic_results = vector_index.search(query, top_k * 2)
    logger.debug(f"Found {len(semantic_results)} semantic results")
    
    # AI understands merging is key step
    logger.info(f"Merging results...")
    merged = merge_results(semantic_results, keyword_results)
    
    logger.info(f"Search completed: returned {len(merged)} results")
    return merged
```

**Result**: AI generates code with correct checks, error handling, and logging of critical steps.

---

## Category 9: Embedded Tutorials

### Influence on Code Quality
- Usage examples show AI how code should work
- Docstrings with examples activate correct patterns
- Embedded tutorials serve as specification

### Example

```python
def hybrid_search(query: str, top_k: int = 10, alpha: float = 0.7):
    """
    Performs hybrid search combining semantic and keyword matching.
    
    TUTORIAL:
    --------
    This function combines two types of search:
    1. Semantic search (vector similarity)
    2. Keyword search (BM25)
    
    EXAMPLES:
    ---------
    >>> # Example 1: Balanced search
    >>> results = hybrid_search("python tutorial", top_k=5, alpha=0.7)
    >>> print(results[0].title)
    'Introduction to Python Programming'
    
    >>> # Example 2: Keyword-focused search
    >>> results = hybrid_search("exact phrase match", top_k=10, alpha=0.3)
    
    EDGE CASES:
    -----------
    - Empty query → returns []
    - top_k = 0 → returns []
    - alpha < 0 or alpha > 1 → raises ValueError
    
    ALGORITHM:
    ----------
    1. Get semantic results (vector similarity)
    2. Get keyword results (BM25)
    3. Normalize scores to [0, 1] range
    4. Combine using RRF: score = 1 / (k + rank)
    5. Sort by combined score
    6. Return top K
    """
    # AI generates code exactly matching documentation
    ...
```

**Result**: AI generates code fully matching examples and handling all edge cases.

---

## Category 10: Visual Structure

### Influence on Code Quality
- Blank lines between logical blocks
- Comment alignment
- Grouping related operations

### Example

```python
# BAD (no visual structure):
def process(data):
    if not data:
        return []
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

# GOOD (clear visual structure):
def process(data):
    # VALIDATION
    if not data:
        return []
    
    # INITIALIZATION
    result = []
    
    # PROCESSING
    for item in data:
        if item > 0:
            doubled = item * 2
            result.append(doubled)
    
    # RETURN
    return result
```

**Result**: AI generates code with clear structure and correct operation grouping.

---

## Category 11: Metadata (Type Hints)

### Influence on Code Quality
- Type hints direct AI to correct types
- Decorators activate patterns
- Annotations provide additional context

### Example

```python
from typing import List, Optional, Dict
from dataclasses import dataclass

@dataclass
class SearchResult:
    """Single search result with score."""
    doc_id: str
    score: float
    metadata: Dict[str, any]

def hybrid_search(
    query: str,
    top_k: int = 10,
    alpha: float = 0.7,
    filters: Optional[Dict[str, any]] = None
) -> List[SearchResult]:
    """
    AI understands from type hints:
    - query — string
    - top_k — integer
    - alpha — float
    - filters — optional dict
    - returns list of SearchResult
    """
    results: List[SearchResult] = []
    # ...
    return results
```

**Result**: AI generates code with correct types, no type errors.

---

## Category 12: Inline Examples and Tests

### Influence on Code Quality
- Examples show expected behavior
- Tests serve as specification
- Doctest-style examples activate correct patterns

### Example

```python
def normalize_scores(scores):
    """
    Normalizes scores to [0, 1] range using min-max normalization.
    
    EXAMPLES:
    >>> normalize_scores([1, 2, 3, 4, 5])
    [0.0, 0.25, 0.5, 0.75, 1.0]
    
    >>> normalize_scores([10, 10, 10])
    [1.0, 1.0, 1.0]  # All same → all 1.0
    
    >>> normalize_scores([5])
    [1.0]  # Single value → 1.0
    
    >>> normalize_scores([])
    []  # Empty → empty
    """
    # AI generates code handling all examples
    if not scores:
        return []
    if len(scores) == 1:
        return [1.0]
    min_score, max_score = min(scores), max(scores)
    if min_score == max_score:
        return [1.0] * len(scores)
    return [(s - min_score) / (max_score - min_score) for s in scores]
```

**Result**: AI generates code correctly handling all examples and edge cases.

---

## Summary Table: Non-Code Token Influence

| Element | Quality Influence | Priority |
|---------|-------------------|----------|
| Comments (WHY, STEP) | Direct logic, prevent errors | ⭐⭐⭐⭐⭐ |
| Diagrams (ASCII/Mermaid) | Visualize architecture | ⭐⭐⭐⭐ |
| Tickets (Embedded) | Connect to requirements | ⭐⭐⭐⭐⭐ |
| Pseudocode | Set algorithm | ⭐⭐⭐⭐⭐ |
| Comment Language | Activate patterns | ⭐⭐⭐ |
| Formatting | Improve structure | ⭐⭐⭐⭐ |
| Naming | Activate correct patterns | ⭐⭐⭐⭐⭐ |
| Logging | Show important steps | ⭐⭐⭐⭐ |
| Embedded Tutorials | Serve as specification | ⭐⭐⭐⭐ |
| Visual Structure | Improve readability | ⭐⭐⭐ |
| Metadata (type hints) | Prevent type errors | ⭐⭐⭐⭐⭐ |
| Examples in Comments | Show expected behavior | ⭐⭐⭐⭐⭐ |

---

## Code Formatting Principles for AI

✅ **Maximum context**: 80-90% non-code tokens
✅ **Clear structure**: Separators, sections, hierarchy
✅ **Self-documentation**: Long descriptive names
✅ **Examples everywhere**: In docstrings, comments, tests
✅ **Visual clarity**: Blank lines, alignment, grouping
✅ **Metadata**: Type hints, decorators, annotations
✅ **Logging**: Shows important steps and decisions
✅ **Diagrams**: ASCII/Mermaid for visualization
✅ **Pseudocode**: Before implementation
✅ **Tickets**: At start of each file

**Result**: AI generates high-quality code matching all requirements, with correct edge case handling and optimal structure.
