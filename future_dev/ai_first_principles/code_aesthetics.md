# Code Aesthetics and RAG-Aware Prompting

## Common Interface Principles (GUI and CLI)

| Aspect | GUI | CLI |
|--------|-----|-----|
| **Documentation** | Tooltips, hints, built-in help | --help, man pages, examples in code |
| **Examples** | Demo data, tutorials on first run | Command examples in --help |
| **Error Handling** | Clear messages with action suggestions | Clear messages with exit codes |
| **Progress** | Progress bars, loading indicators | Terminal progress bars, verbose mode |
| **Testing** | Usability testing, A/B tests | All parameter combination testing |

### INTERFACE_SPEC.md Template

```markdown
# Interface Specification

## Type: [GUI / CLI]

## Overview
[Brief description]

## [For GUI] Screens
### Main Screen
- Layout: ...
- Components: ...
- User flows: ...

## [For CLI] Commands
### command-name
- Usage: ...
- Parameters: ...
- Examples: ...

## Error Handling
- Error scenarios: ...
- Error messages: ...
- Recovery actions: ...

## Testing Plan
- Test cases: ...
- Edge cases: ...
```

---

## Phase 3: Implementation Plan

1. **Step-by-step plan**: With justifications for each step
2. **Prioritization**: What to do first
3. **Dependencies**: Dependency graph between tasks
4. **Success metrics**: How to measure success

---

## 6.2 Implementation

1. **Structure**: Create folders, README, specifications
2. **Stubs**: Files with signatures and documentation
3. **Implementation**: Simple code with abundant comments
4. **Logging**: Add logs at every step

## 6.3 Verification

1. **Self-documentation**: Check that code reads as documentation
2. **Logs**: Verify logs tell execution story
3. **Testing**: Functional and integration tests
4. **Reflection**: Update documentation based on implementation

---

## VII. CODE AESTHETICS

### 7.1 Code as Literature

**Code should read like a well-written book:**
- Logical narrative from start to end
- Each "chapter" (function) has introduction (docstring)
- Comments as author's explanations
- Structure reflects plot (architecture)
- **Even non-programmers can solve LeetCode problems** in lowest-level algorithms thanks to 90% text as comments, specs, diagrams

### 7.2 Visual Organization

**Use visual separators:**

```python
# ============================================================================
# SECTION: Data Loading and Preprocessing
# ============================================================================

# ----------------------------------------------------------------------------
# Subsection: File System Operations
# ----------------------------------------------------------------------------

# --- Load configuration ---
```

### 7.3 Emoji for Navigation

**Emoji as visual markers in comments:**
- 🎯 Function goal
- ⚠️ Important warning
- 🔧 Technical detail
- 💡 Improvement idea
- 🐛 Known issue
- ✅ Verified and works

---

## 7.4 RAG-Aware Prompt Principles

**CRITICAL**: When creating system prompts for specs/code generation, consider embedding principles to **automatically pull relevant documentation** in real-time.

### The Problem

When AI generates code, it may lack specific information:
- Library API details
- Internal project conventions
- Specific patterns and best practices
- Technology documentation

### The Solution

Write prompts to **attract** needed documentation through embedding systems (RAG, MCP, API).

---

### What Are Embeddings (Simple Explanation)

> Imagine all project documentation is split into small pieces (paragraphs, sections).
> Each piece has "magnetic properties" — it attracts certain words and phrases.
> When you write a prompt with correct "magnetic words", the system automatically finds and pulls relevant documentation pieces.
>
> **Your task**: Use words and phrases in prompts that will "magnetize" needed information.

**Technical**: RAG systems use vector embeddings to find relevant documentation fragments. When prompt contains specific terms, technologies, patterns — the system finds documentation with similar terms and adds it to context.

---

### Principles for RAG-Aware Prompts

#### Principle 1: Use Specific Terms and Technologies

❌ **Bad** (doesn't attract documentation):
```
Create a search function.
```

✅ **Good** (attracts documentation):
```
Create a hybrid search function using BM25 for keyword matching
and cosine similarity for semantic search with FAISS vector index.
Include score normalization using min-max scaling.
```

#### Principle 2: Reference Patterns and Conventions

❌ **Bad**:
```
Add logging.
```

✅ **Good**:
```
Add paranoid logging following PARANOID_LOGGER_SPEC pattern
with structured metadata and log levels per LOGGING_POLICY.
```

#### Principle 3: Mention Related Files and Components

❌ **Bad**:
```
Create validation.
```

✅ **Good**:
```
Create input validation following patterns from utils/validation.py
and error handling conventions from ERROR_HANDLING_SPEC.md.
```

---

### Summary: Magnetic Keywords

Include in prompts:
- Technology names (FAISS, BM25, Elasticsearch)
- Pattern names (Singleton, Factory, Strategy)
- File references (utils.py, config.yaml)
- Spec references (SPEC.md, PATTERN.md)
- Domain terms (embeddings, tokenization, chunking)

This ensures RAG systems pull relevant context automatically.
