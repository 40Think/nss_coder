# Micro-Operations Architecture

## Vector Sugar and Semantic Glue (19.7)

### New Terms

**Vector Sugar** (by analogy with syntactic sugar):
> Additional words, comments, names that create vector connectivity and attract correct tokens.

**Semantic Glue**:
> Extracellular matrix, code cytoskeleton that stabilizes tokens and eliminates interpretation variations.

### Semantic Glue Functions

1. **Token stabilization**: fixes meaning
2. **Variation elimination**: one interpretation
3. **Predictability**: always one behavior
4. **Vector connectivity**: continuity in latent space
5. **Token gravity**: attracts correct tokens

### Vector Sugar Types

| Type | Example | Function |
|------|---------|----------|
| **Long names** | `fetch_bm25_results_from_keyword_index` | Intent clarity |
| **Detailed docstrings** | Args, Returns, Raises | Context & examples |
| **Inline comments** | `# Why top_k*2: ...` | Decision explanation |
| **Header comments** | `# PROBLEM: ... SOLUTION: ...` | Architectural context |
| **Usage examples** | `>>> hybrid_search(...)` | Concreteness |
| **References** | `# REFERENCES: ...` | Authority |
| **Complexity** | `# COMPLEXITY: O(n log n)` | Technical depth |
| **History** | `# AUTHOR: ... DATE: ...` | Provenance |

**Principle:**
> Code looks like text. From distance seems like normal text, not a program.

---

## XX. Micro-Operations Architecture

**KEY IDEA:** One cognitive operation at a time, ~700 tokens generation → 1M steps without errors.

---

## 20.1 One Cognitive Operation = One File

**Key principle:**
> One function in one file per one generation, doing only one cognitive operation.

**Problem with agent systems:**
> When agent generates 300 lines with dozens of functions, semantic capacity drops 2-3x compared to manual generation.

**Why this happens:**
1. Context window fills with garbage
2. Half of specs lost along the way
3. Compression → information loss
4. Cognitive break between functions
5. Token break between concepts

### Solution

**Not this:**
```
One file = 300 lines = 10-20 functions = many cognitive operations
```

**But this:**
```
One file = one function = one cognitive operation = ~700 tokens
```

**Result:**
- 50-60 separate small files in project
- High saturation of each file
- Removes cognitive breaks
- Removes token breaks

**Proportion:**
```
1 file = 1 function = 100 lines semantic glue + 5 lines code
```

---

## 20.2 Micro-Operations ~700 Tokens

**Key principle:**
> One cognitive operation at a time, ~700 tokens → 1M steps without errors.

**Why 700 tokens** — the **adequate answers zone**:
- Not primitive (2-3 lines)
- Not overload (10-100 pages)
- One cognitive operation
- One page of text
- Can comprehend in one pass

### Quality Zones by Generation Size

| Size | Zone | Quality |
|------|------|---------|
| 2-3 lines | Primitive | ⚠️ Low |
| **~700 tokens** | **Adequate** | ✅ **High** |
| 10-100 pages | Overload | ❌ Low |

### Micro-Operations Advantages

1. **Quality preservation**: in adequate answers zone
2. **Human text access**: don't go into synthetic
3. **Lower LLM requirements**: can use smaller models
4. **Lower costs**: fewer tokens per call
5. **High semantic capacity**: 2-3x higher

**Result:**
> 700 tokens generation → 1M steps without errors.

---

## 20.3 Hierarchical Task Breakdown

**Key principle:**
> AI and agent systems don't do everything through one context, one pass of hundreds of steps.

**Instead:**
> Hierarchical breakdown into tasks, subtasks, sub-subtasks. Clear action plan.

### Process

1. **Generate document** at top level
2. **Write to dev diary** (formalized, like in lab)
3. **Descend to next level**
4. **Generate prompts** for next level
5. **Repeat** on many levels
6. **Generate artifacts** in natural language

---

## Crystallization Rule (6.1.1)

**Problem:** Deep thinking can lead to verbose answers that lose focus.

**Solution:** Bridge between inner world and external communication.

### Principle

1. **Think wide**: Use full power of intellect, associative thinking, philosophy during analysis
2. **Speak narrow**: Before action (tool call), you MUST **crystallize** intentions to 1-2 phrases

### Format

**Internal dialogue** (in your "mind"):
```
[Deep analysis]
I see several approaches...
On one hand, X gives advantage A...
On other hand, Y provides flexibility B...
Considering project context and NSS Coder philosophy...
I choose approach Z because...
```

**Crystal (Preamble)** — what user sees:
```
I analyzed the task and decided to use approach Z 
(vectorization via numpy for cache locality). 
Now I'm modifying search() in src/search.py:145-167.
```

### When to Apply

**MANDATORY before:**
- Calling `view_file`, `write_to_file`, `run_command`
- Any code changes
- Running checks

**Crystal template:**
```
I [what analyzed] and decided [what to do]. 
Now I [specific action with file:line reference].
```

### Why Important

**For user:**
- Creates clarity and predictability
- Sees thinking process compressed
- Understands what's next

**For you:**
- Forces clear intention formulation
- Prevents aimless actions
- Serves as self-check before action

**Analogy:**
> Surgeon before operation says aloud: "I'm making incision at point X for access to Y". Not for patient (under anesthesia), but for team and for himself — moment of intention crystallization.

---

## Phase 2: Context Expansion Through Questions (6.2)

**Book writing analogy:**

1. **Title** (top level)
2. **Annotation** (general description)
3. **Abstract** (key ideas)
4. **Introduction** (context)
5. **Table of contents** (structure)
6. **Sections** (large parts)
7. **Subsections** (details)
8. **Paragraphs** (specifics)

**At each level:**
- Own prompt
- Own context
- Own generation
