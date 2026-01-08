# Non-Code Tokens: What Influences AI Code Quality

## Critical Question

What, besides executable code itself, influences its quality during AI generation?

## Answer

**Non-code tokens** — everything that surrounds code and creates context for AI.

---

## Category 1: Comments

### Influence on Code Quality
- Direct AI attention to important aspects
- Activate relevant patterns in latent space
- Prevent typical errors through explicit warnings
- Improve understanding of intentions

### Comment Types
- `# WHY:` — decision justification
- `# STEP X:` — algorithm structuring
- `# EDGE CASE:` — warning about non-standard situations
- `# ALTERNATIVE CONSIDERED:` — rejected options
- `# PERFORMANCE:` — optimization notes
- `# TODO:` — future plans
- `# FIXME:` — known problems

### Example

```python
# WITHOUT comments (AI may generate suboptimally):
result = [x * 2 for x in data if x > 0]

# WITH comments (AI understands context):
# STEP 1: Filter positive numbers
# WHY: Negative numbers represent errors in our domain
# PERFORMANCE: List comprehension is 2x faster than loop for this size
# EDGE CASE: Empty list returns empty list (expected behavior)
result = [x * 2 for x in data if x > 0]
```

**Result**: AI generates code with correct edge case handling and optimal structure.

---

## Category 2: Diagrams (ASCII/Mermaid)

### Influence on Code Quality
- Visualize data flow and logic
- Help AI understand architecture
- Activate spatial thinking in LLM
- Prevent errors in complex interactions

### Diagram Types
- ASCII flow diagrams (data flows)
- Mermaid sequence diagrams (call sequences)
- State machines (finite automata)
- Tree structures (hierarchies)

### Example

```python
# FLOW DIAGRAM:
#   Input → Validate → Transform → Filter → Output
#     ↓         ↓          ↓         ↓        ↓
#   [data]   [valid?]  [process]  [keep?]  [result]

def process_pipeline(data):
    # AI generates code following the diagram
    validated = validate(data)
    transformed = transform(validated)
    filtered = filter_results(transformed)
    return filtered
```

**Result**: AI generates code exactly matching architecture.

---

## Category 3: Embedded Tickets

### Influence on Code Quality
- Provide full task context
- Connect code with business requirements
- Activate relevant solution patterns
- Ensure decision traceability

### Example

```python
# ============================================================================
# @TAG:TICKET:implement-hybrid-search
# TICKET: Implement Hybrid Search Engine
# ============================================================================
# CONTEXT: Part of RAG pipeline, combines semantic + keyword search
# REQUIREMENTS:
#   - FR1: Accept query, return top-K ranked results
#   - NFR1: < 100ms latency for 10K documents
# DESIGN DECISION: Use Reciprocal Rank Fusion (RRF)
# ALTERNATIVES REJECTED: Simple weighted average (less robust)
# ============================================================================

class HybridSearchEngine:
    # AI generates code considering all ticket requirements
    ...
```

**Result**: AI generates code fully matching requirements.

---

## Category 4: Pseudocode

### Influence on Code Quality
- Sets clear logical structure
- Prevents deviations from algorithm
- Simplifies transformation to executable code
- Serves as specification for AI

### Example

```python
# PSEUDOCODE:
#   FUNCTION search(query, top_k, alpha):
#     IF query is empty THEN RETURN empty list
#     semantic_results = vector_index.search(query, top_k * 2)
#     keyword_results = keyword_index.search(query, top_k * 2)
#     merged = merge_with_rrf(semantic_results, keyword_results)
#     RETURN top K from merged
#   END FUNCTION

def search(self, query: str, top_k: int = 10, alpha: float = 0.7):
    # AI generates code exactly following pseudocode
    if not query:
        return []
    semantic_results = self.vector_index.search(query, top_k * 2)
    keyword_results = self.keyword_index.search(query, top_k * 2)
    merged = self._merge_with_rrf(semantic_results, keyword_results)
    return sorted(merged, key=lambda x: x.score, reverse=True)[:top_k]
```

**Result**: AI generates code perfectly matching algorithm.

---

## Category 5: Comment Language

### Influence on Code Quality
- English activates more technical patterns in LLM
- Russian may be better for domain specifics
- Mixed language creates unique token space

### Recommendation
- **Technical terms**: English (`# STEP 1: Validate input`)
- **Domain logic**: Russian (`# Проверяем обязательные пункты договора`)
- **Mixed approach**: Best of both worlds

### Example

```python
# MIXED (best of both):
# STEP 1: Инициализация connection pool
# WHY: Переиспользование connections для performance
# PATTERN: Object pool pattern
pool = ConnectionPool(max_size=10)
```

**Result**: Mixed approach gives best quality for domain-specific projects.

---

## Category 6: Formatting & Markup

### Influence on Code Quality
- Visual structure helps AI understand hierarchy
- Separators create clear boundaries between sections
- Indents and blank lines improve readability for AI

### Formatting Elements

```python
# ============================================================================
# SECTION HEADER (very noticeable for AI)
# ============================================================================

# ----------------------------------------------------------------------------
# Subsection (medium visibility)
# ----------------------------------------------------------------------------

# --- Small separator (low visibility) ---

# Regular comment

# ВАЖНО: Critical information (stands out with caps)
# TODO: Future task
# FIXME: Needs fixing
```

**Result**: AI clearly understands structure and generates code with correct hierarchy.

---

## Category 7: Naming

### Influence on Code Quality
- Self-documenting names activate correct patterns
- Long descriptive names better for AI than short
- Naming convention consistency is critical

### Examples

```python
# ❌ BAD: Short, cryptic
def proc(d):
    return d * 2

# ✅ GOOD: Long, descriptive
def double_positive_values_for_preprocessing_stage(data_list):
    return [value * 2 for value in data_list if value > 0]
```

**Result**: AI generates code with correct patterns and clear intent.
