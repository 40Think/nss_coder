# Permission Gates and Testing Strategy

## Regression Testing: Known Bugs

**Problem**: AI may repeat the same mistakes.
**Solution**: Tests for bugs AI has already created.

### Example

```python
def test_regression_empty_query():
    """
    @TAG:REGRESSION-TESTING:bug-123
    
    BUG #123: AI generated code that crashed on empty query.
    FIXED: 2025-11-29
    CAUSE: No validation for empty strings
    """
    engine = HybridSearchEngine()
    results = engine.search("")  # Should return [], not crash
    assert results == []

def test_regression_unicode_normalization():
    """
    @TAG:REGRESSION-TESTING:bug-456
    
    BUG #456: AI didn't normalize Unicode (café vs café).
    FIXED: 2025-11-29
    """
    results1 = engine.search("café")  # NFC
    results2 = engine.search("café")  # NFD
    assert results1 == results2
```

---

## CI/CD Integration

```yaml
# .github/workflows/fuzzy-tests.yml
name: Fuzzy Testing
on: [push, pull_request]

jobs:
  fuzzy-test:
    runs-on: ubuntu-latest
    steps:
      - name: Run fuzzy tests
        run: pytest tests/ --hypothesis-max-examples=1000 -m fuzzy
      
      - name: Run property tests
        run: pytest tests/ -m property
      
      - name: Run metamorphic tests
        run: pytest tests/ -m metamorphic
```

---

## Permission Gates: AI-Controlled Checkpoints

**Philosophy**: Before proceeding, AI must **get permission** to move to next stage.
**Purpose**: Prevents error accumulation, guarantees quality at every stage.

### Gate 1: After Context Understanding

**AI asks**: "Did I understand context correctly? Can I proceed to design?"

| Check | ☐ |
|-------|---|
| Context fully expanded? | |
| Hidden assumptions revealed? | |
| Clarifying questions asked? | |
| NeuroCore confirmed understanding? | |

**If any ☐ unchecked → STOP, return to context clarification.**

---

### Gate 2: After Architecture Design

**AI asks**: "Architecture agreed? Can I proceed to specifications?"

| Check | ☐ |
|-------|---|
| Follows NSS Coder principles? | |
| Extreme decomposition applied? | |
| Cognitive units defined (~700 tokens)? | |
| Hardware-aware aspects considered? | |
| NeuroCore approved? | |

---

### Gate 3: After Specifications

**AI asks**: "Specifications complete? Can I proceed to pseudocode?"

| Check | ☐ |
|-------|---|
| All functional requirements covered? | |
| Edge cases described? | |
| Invariants defined? | |
| Semantic tags added? | |
| Comment ratio ≥ 70%? | |

---

### Gate 4: After Pseudocode

**AI asks**: "Pseudocode correct? Can I proceed to implementation?"

| Check | ☐ |
|-------|---|
| Pseudocode readable? | |
| Algorithm optimal? | |
| Hardware-aware optimizations considered? | |
| NeuroCore approved approach? | |

---

### Gate 5: After Implementation

**AI asks**: "Code ready? Can I proceed to testing?"

| Check | ☐ |
|-------|---|
| Matches specifications? | |
| Comment ratio ≥ 90%? | |
| File size ≤ 150 lines? | |
| Cognitive unit size ≤ 1000 tokens? | |
| Semantic tags added? | |

---

### Gate 6: After Testing

**AI asks**: "All tests passed? Can I consider task complete?"

| Check | ☐ |
|-------|---|
| Unit tests pass? | |
| Integration tests pass? | |
| Fuzzy tests pass? | |
| Property-based tests pass? | |
| Regression tests for known bugs added? | |

---

## VII. Testing Strategy: Point-to-Sphere

**Philosophy**: Pragmatic, economical testing. Fail fast, fix fast.

**Problem**: Full test suite immediately = wasted time/tokens.

### Level 1: Point (Specific)

**What**: Check the specific function/line you changed.

```python
# Changed search() in src/search.py:145
def test_search_empty_query():
    result = search("", documents)
    assert result == []

# Run ONLY this test
pytest tests/test_search.py::test_search_empty_query -v
```

**Time**: Seconds
**Goal**: Verify specific change works

---

### Level 2: Line (Integration)

**What**: Check interaction with neighboring modules.

```bash
# All tests for search module
pytest tests/test_search.py -v

# Tests for dependent modules
pytest tests/test_api.py -v  # API uses search
```

**Time**: Minutes
**Goal**: Verify change didn't break integration

---

### Level 3: Sphere (System)

**What**: Full test suite.
**When**: Only when confident in Point and Line.

```bash
pytest --cov=src --cov-report=html
```

**Time**: Minutes to hours
**Goal**: Verify entire system works

---

### Workflow After Code Change

```
1. [POINT] Micro-test of changed function
   ├─ ✅ Pass → step 2
   └─ ❌ Fail → fix → repeat step 1

2. [LINE] Module and integration tests
   ├─ ✅ Pass → step 3
   └─ ❌ Fail → fix → return to step 1

3. [SPHERE] Full suite (optional)
   ├─ ✅ Pass → commit
   └─ ❌ Fail → analyze → fix → return to step 1
```

### Time Savings

| Approach | Iteration Time |
|----------|----------------|
| Traditional (full suite first) | 20+ minutes |
| Point-to-Sphere | 11 min, most errors found in seconds |
