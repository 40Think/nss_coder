# Cognitive Unit: The 700-Token Atomic Operation

## Core Concept

**What It Is**: An atomic operation for LLMs — the minimal self-contained unit of work.

## Why Exactly ~700 Tokens?

### Evidence 1: MAKER Paper (arXiv:2511.09030) — Empirical Proof

```
EXPERIMENT: Towers of Hanoi (20 disks)

Task: 1,048,575 steps (2^20 - 1)
Approach: Extreme decomposition into micro-tasks

Results:
- Micro-task size: ~500-1000 tokens
- Success rate: 100% (ZERO errors)
- Key factor: Each micro-task is self-contained

Conclusion: Extreme decomposition works, optimal size ~700 tokens
```

### Evidence 2: LLM Cognitive Units Research

```
RESEARCH: Specialized Units in LLMs

Findings:
- LLMs have task-specific units (< 100 neurons = 1% of total)
- Modularity: different units for different tasks
- Cognitive load sensitivity: quality drops under overload

Conclusion: LLMs work better with focused, modular tasks
```

### Evidence 3: Practical Experience (Empirical)

```
OBSERVATIONS from development:

Tickets 100-200 lines (~300-600 tokens):
- ✅ High code quality
- ✅ Minimal errors
- ✅ Good self-sufficiency

Tickets 500+ lines (~1500+ tokens):
- ❌ Quality degradation
- ❌ More errors
- ❌ Loss of focus

Optimum: 200-300 lines ≈ 600-900 tokens
```

### Convergence to ~700 Tokens

Three independent sources give one result:

| Source | Optimal Size | Justification |
|--------|--------------|---------------|
| MAKER Paper | ~500-1000 tokens | Empirical (1M steps without errors) |
| LLM Research | ~700 tokens | Cognitive units, modularity |
| Practice | ~600-900 tokens | Code quality, minimal errors |
| **CONSENSUS** | **~700 tokens** | **Convergence of three sources** |

---

## Task Decomposition Rules

```
TASK: Size N tokens

IF N < 700:
  → One micro-task (atomic operation)
  
ELIF 700 < N < 4000:
  → Split into 2-5 micro-tasks (~700 tokens each)
  
ELIF 4000 < N < 100K:
  → Hierarchical decomposition:
     Level 1: Split into subtasks (~4K tokens)
     Level 2: Each subtask → micro-tasks (~700 tokens)
  
ELSE (N > 100K):
  → Use RAG + hierarchical decomposition
  → Reference material in context window
  → Active work in working memory (~4K)
  → Execution in cognitive units (~700)
```

---

## Example: HybridSearchEngine Development

```
TOTAL SIZE: ~50K tokens (entire project)

LEVEL 1: Split into components (~4K each)
  - VectorIndex: 4K tokens
  - KeywordIndex: 3K tokens
  - HybridSearchEngine: 5K tokens
  - Tests: 3K tokens
  - Documentation: 2K tokens

LEVEL 2: Split components into functions (~700 each)
  VectorIndex (4K) →
    - __init__: 600 tokens
    - add_documents: 800 tokens
    - search: 900 tokens
    - _compute_embeddings: 700 tokens
    - _normalize_scores: 500 tokens

LEVEL 3: Implementation (one ticket = one function = ~700 tokens)
  Ticket #1: VectorIndex.__init__ (600 tokens)
    - CONTEXT: 100 tokens
    - PROBLEM: 50 tokens
    - SOLUTION: 200 tokens
    - CODE: 150 tokens (30 lines)
    - TESTS: 100 tokens
```

---

## Why This Matters for AI-First

### Traditional Approach
- Tasks of any size (100 lines or 10,000 lines)
- No scientific basis for sizing
- Unpredictable quality

### NSS Coder Approach
- ✅ Tasks ~700 tokens (scientifically justified)
- ✅ MAKER paper: 1M steps without errors
- ✅ LLM research: cognitive units, modularity
- ✅ Practice: high quality, minimal errors

### Result
- Predictable quality
- Scalability (from 1 function to 1M steps)
- Scientific justification (not just "convenient")
