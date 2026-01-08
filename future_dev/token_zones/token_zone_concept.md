# Token Zone Concept: Scientific Basis for Optimal Task Size

## The Problem

Why exactly ~700 tokens? Why not 10K or 100K?

## The Answer

Three different levels of working with tokens, each with scientific justification.

---

## Level 1: Context Window (100K-2M tokens)

### What It Is
Technical maximum of the model — how many tokens it can "see" simultaneously.

### Examples
| Model | Context Window |
|-------|----------------|
| GPT-4 Turbo | 128K tokens |
| Claude 3 | 200K tokens |
| Gemini 1.5 Pro | 2M tokens |

### What It's Used For
- Reference material (documentation, project code)
- Long-form context (entire dialogue history)
- Retrieval-Augmented Generation (RAG)

### The Problem
**Context window ≠ Effective reasoning length**

### Research Shows
- Performance degradation begins LONG BEFORE maximum
- "Lost in the middle" problem — model works worse with information in the middle of context
- Attention dilution — the larger the context, the weaker attention to each token

---

## Level 2: Working Memory (~4K tokens)

### What It Is
Active information processing — what the model "holds in mind" for the current task.

### Human Analogy
| System | Capacity |
|--------|----------|
| Human working memory | 7±2 chunks (Miller's Law) |
| LLM working memory | ~4K tokens effective processing |

### Scientific Basis

```
RESEARCH: LLM Performance vs Input Length

Results:
- 0-4K tokens: Excellent performance (95-100%)
- 4K-16K tokens: Moderate degradation (85-95%)
- 16K-64K tokens: Noticeable degradation (70-85%)
- 64K+ tokens: Significant degradation (50-70%)

Conclusion:
Optimal active processing happens in the ~4K token zone
```

### Implications
- Keep active task description within ~4K tokens
- Use rest of context for reference, not active reasoning
- Chunk complex problems into 4K-sized pieces

---

## Level 3: Cognitive Unit (~700 tokens)

### What It Is
Optimal size for single coherent thought or action.

### Why 700 Tokens

This is the "Goldilocks zone":
- **Too small (< 200)**: Fragmented, lacks context
- **Too large (> 1500)**: Diluted attention, error-prone
- **~700 tokens**: Perfect balance of context and focus

### Scientific Basis

From MAKER paper (arXiv:2511.09030):
- Agents can execute 1M+ steps without errors
- When each step is one "cognitive operation"
- Cognitive operation ≈ 700 tokens ≈ 50-70 lines of Python

### Practical Rules

| Artifact | Target Size |
|----------|-------------|
| Single function | ~50-70 lines |
| Single file section | ~700 tokens |
| Single task/ticket | One cognitive operation |
| Single commit | One logical change |

---

## Practical Application

### Structuring Work

```
TOTAL PROJECT: 100K+ tokens of context
    ↓
WORKING MEMORY: ~4K tokens active
    ↓
COGNITIVE UNIT: ~700 tokens per task
```

### Task Decomposition

1. **Break down** complex tasks into 700-token units
2. **Focus** working memory on one unit at a time
3. **Use** context window for reference material
4. **Maintain** token connectivity between units

### Quality Assurance

If a task feels too complex:
- It's probably > 700 tokens
- Break it down further
- Each piece should be one coherent thought

---

## The Token Zone Model

```
┌─────────────────────────────────────────────────────┐
│            CONTEXT WINDOW (100K-2M)                 │
│  ┌───────────────────────────────────────────────┐  │
│  │         Reference Material                     │  │
│  │  • Documentation                              │  │
│  │  • Previous code                              │  │
│  │  • Dialogue history                           │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │         WORKING MEMORY (~4K)                  │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │    COGNITIVE UNIT (~700)                │  │  │
│  │  │    • Current task                       │  │  │
│  │  │    • Active reasoning                   │  │  │
│  │  │    • Immediate context                  │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  │                                               │  │
│  │  Supporting context for current task          │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Key Takeaways

1. **Context window** is for storage, not active reasoning
2. **Working memory** is for the current task context
3. **Cognitive unit** is for single coherent operations
4. **700 tokens** is the optimal size for reliable execution
5. **Break down** everything larger into 700-token pieces
