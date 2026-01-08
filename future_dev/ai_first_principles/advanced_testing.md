# Advanced Testing Strategies

## TDD Red/Green Phases

### Step-by-Step TDD Example

**Step 1**: Write tests FIRST
```python
def test_search_returns_results(self):
    engine = HybridSearchEngine()
    results = engine.search("machine learning", top_k=10)
    assert isinstance(results, list)
    assert len(results) <= 10

def test_search_empty_query_returns_empty_list(self):
    results = engine.search("", top_k=10)
    assert results == []
```

**Step 2**: User approval → "Tests look correct. Approved."

**Step 3**: Run tests (Red Phase)
```bash
$ pytest tests/test_hybrid_search.py
FAILED - ImportError: cannot import name 'HybridSearchEngine'
```
✅ Tests fail — this is correct!

**Step 4**: ONLY NOW write implementation

**Step 5**: Run tests (Green Phase) → All tests passed!

---

## Article IX: Integration-First Testing

**Principle:**
> Tests MUST use realistic environments.

**Priorities:**
- Prefer real databases over mocks
- Use real service instances over stubs
- Contract tests mandatory before implementation

### Real Services vs Mocks

❌ **Bad** (mocks):
```python
def test_search_with_mock():
    mock_index = Mock()
    mock_index.search.return_value = [Mock(score=0.9)]
    # May pass but not work in reality
```

✅ **Good** (real services):
```python
@pytest.fixture
def real_search_engine():
    vector_index = faiss.IndexFlatL2(768)
    bm25_index = BM25Index()
    # Load real test data
    return HybridSearchEngine(vector_index, bm25_index)

def test_search_with_real_indices(real_search_engine):
    results = real_search_engine.search("machine learning")
    assert len(results) > 0
    assert results[0].score >= results[-1].score  # Sorted
```

### Contract Tests

```python
def test_search_contract():
    """Contract test — defines API contract."""
    results = engine.search("test", top_k=10)
    assert isinstance(results, list)
    assert all(isinstance(r, SearchResult) for r in results)
    assert all(hasattr(r, 'doc_id') and hasattr(r, 'score') for r in results)
    assert all(0.0 <= r.score <= 1.0 for r in results)
```

---

## Fuzzy Testing

**Problem**: AI may generate code with non-obvious bugs.
**Solution**: Feed random/incorrect data and check if code crashes.

### Types of Fuzzy Tests

| Type | What it tests | Example |
|------|---------------|---------|
| **Random strings** | Any text input | `@given(st.text())` |
| **Type confusion** | Wrong types | `@given(st.integers())` |
| **Extreme values** | Huge inputs | 10K-100K character strings |
| **Unicode** | Special characters | All Unicode categories |

### Example with Hypothesis

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_search_with_random_strings(query):
    """Search should not crash on any string."""
    engine = HybridSearchEngine()
    try:
        results = engine.search(query)
        assert isinstance(results, list)
    except Exception as e:
        pytest.fail(f"Crashed on '{query}': {e}")

@given(st.text(min_size=10000, max_size=100000))
def test_search_with_huge_queries(huge_query):
    """Search should handle or reject huge queries."""
    try:
        results = engine.search(huge_query)
        assert isinstance(results, list)
    except ValueError as e:
        assert "too long" in str(e).lower()
```

---

## Property-Based Testing

**Principle**: Verify that certain properties (invariants) ALWAYS hold.

### Key Properties

| Property | Description | Test |
|----------|-------------|------|
| **Sorted results** | Results always sorted by score desc | `scores == sorted(scores, reverse=True)` |
| **Score range** | Score always in [0, 1] | `0.0 <= result.score <= 1.0` |
| **Idempotence** | Same query = same results | `results1 == results2` |
| **Monotonicity** | More docs ≥ more results | `len(after) >= len(before)` |

### Example

```python
@given(st.text(min_size=1))
def test_search_results_are_sorted(query):
    """PROPERTY: Results ALWAYS sorted by score descending."""
    results = engine.search(query)
    if len(results) > 1:
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

@given(st.text(min_size=1))
def test_search_is_idempotent(query):
    """PROPERTY: Same query always returns same results."""
    results1 = engine.search(query)
    results2 = engine.search(query)
    assert results1 == results2
```

---

## Metamorphic Testing

**Principle**: Verify that input transformations produce predictable output changes.

### Example: Word Order Invariance

```python
@given(st.text(min_size=5))
def test_search_word_order_invariance(query):
    """
    METAMORPHIC: Word permutation should not drastically 
    change results (for semantic search).
    """
    results1 = engine.search(query)
    
    # Permute words
    words = query.split()
    permuted = " ".join(reversed(words))
    results2 = engine.search(permuted)
    
    # Results should overlap significantly (semantic similarity)
    overlap = set(r.doc_id for r in results1) & set(r.doc_id for r in results2)
    assert len(overlap) / max(len(results1), 1) > 0.5
```

---

## Gate Checks Summary

| Article | Gate Questions |
|---------|----------------|
| **TDD** | ☐ Tests before impl? ☐ User approved? ☐ Red? ☐ Green? |
| **Integration** | ☐ Real services? ☐ Contract tests? ☐ Real scenarios? |
| **Fuzzy** | ☐ Random strings? ☐ Extreme values? ☐ Unicode? |
| **Property** | ☐ Invariants defined? ☐ Properties verified? |
