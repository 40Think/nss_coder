# LLM-Centric Programming Paradigm

## Token Gravity Code Example

### Bad (Weak Gravity)
```python
def f(q, k):
    r1 = bm25.s(q, k*2)
    r2 = faiss.s(q, k*2)
    return rrf(r1, r2)[:k]
```

### Good (Strong Gravity)
```python
def hybrid_search_combining_keyword_and_semantic_search(query, top_k):
    # Get results from BM25 index (keywords, exact matches)
    keyword_search_results = bm25_index.search(query, top_k * 2)
    
    # Get results from FAISS index (semantics, vectors, synonyms)
    semantic_search_results = faiss_index.search(query, top_k * 2)
    
    # Combine via Reciprocal Rank Fusion (standard algorithm)
    combined_results = reciprocal_rank_fusion(keyword_search_results, semantic_search_results)
    
    return combined_results[:top_k]
```

**Difference:** Second code magnetizes correct tokens during generation.

> When you create gigantic token gravity very consistently, very thoughtfully — AI cannot ignore it. Even when asked to translate, it starts executing instead.

---

## 18.5 Prompts as Code

**Idea:** Write system prompt as pseudocode or real code with comments and instructions — this creates resonance.

```python
class CodeGenerationPhilosophy:
    """Philosophy of code generation for AI"""
    
    def __init__(self):
        self.beliefs = {
            "simplicity": "Code must be understandable to child",
            "clarity": "Clarity more important than brevity",
            "naturalness": "Code looks like text"
        }
    
    def plan_like_philosopher(self):
        """Plan like philosopher who understands tasks
        but doesn't know programming"""
        self.understand_deep_purpose()
        self.think_about_meaning()
        # Philosopher asks: "Why?" not "How?"
        return self.purpose
    
    def code_like_child(self):
        """Program like child who expresses everything simply"""
        self.use_if_else()  # Not complex patterns
        self.use_simple_loops()  # Not recursion
        # Child says: "If X, then Y" not "Apply Strategy pattern"
        return self.simple_code
    
    def reason_like_ai(self):
        """Reason like AI — amalgam of all expertise"""
        self.combine_all_knowledge()
        self.think_in_vectors()
        # AI sees vector connections, token fields, semantic graphs
        return self.holographic_understanding
```

**Advantages:** Resonance, structure, strong token gravity.

---

## 18.6 Unique Ideas Require 1-3 A4 Pages

**Key insight:**
> When your idea is absolutely unique (not in datasets), AI won't understand from 2-3 lines. Need minimum 1 A4 page, better 2-3.

| Idea Type | Text Needed |
|-----------|-------------|
| **Banal** | 2-3 lines, AI guesses |
| **Unique** | 1-3 A4 pages, multiple messages |

**Paradox:**
- Complex scientific idea → may understand quickly (if in datasets)
- Simple everyday idea → may not understand at all (if unique)

> When AI doesn't understand, it pretends thought didn't exist.

---

## 18.7 Thought-Code Results

1. **Declarative prompts**: Beliefs instead of commands
2. **Compressed beliefs**: Unfold fractally
3. **Token gravity**: Smart words → smart tokens
4. **Prompts as code**: Resonance and structure
5. **Understanding unique ideas**: 1-3 A4 pages

**Key principle:**
> You command nothing, but AI does what you want.

---

## 18.8 Vector Connectivity and Thought-Code

**Principle:** Thought-code works better when LLM can build coherent vector picture of reasoning.

**System prompt must be:**
- Sequential (one follows from another)
- Non-contradictory
- Coherent vector picture

**Problems of vector breaks:**

| Problem | Consequence |
|---------|-------------|
| Jumps between thoughts | Different vector representations |
| Style changes | Token break |
| Contradictions | Cannot build picture |
| Unclear formulations | Ignoring chunks |

**Result:** Thought-code + vector connectivity = maximum effectiveness.

---

## XIX. LLM-Centric Programming Paradigm

**KEY IDEA:** Programming should be built not around human, but around how LLM works. Not human-centric, but **machine-centric** and **LLM-centric**.

---

## 19.1 Vector Coherence of Reasoning

**Fundamental problem:**
> If you start with one thought, jump to second, then third — they're in different vector representations, different words, tokens. You change style, insert code chunks out of place. All this pollutes LLM thinking, reduces quality.

**Principle:**
> If LLM can build coherent vector picture, even very large thought understood better than 5-10x shorter garbage.

**What happens with unclear formulation:**
1. Ignores chunks (no token chains for reasoning)
2. Not enough space to close gaps
3. Doesn't see connections human sees
4. Hallucinations start

---

## 19.2 Semantic Gap: Code ↔ Specification

**Fundamental hypothesis:**
> Code tokens have too large semantic/vector distance relative to high-level tokens in specification.

**Why this happens:**
- Code often separate from documentation
- Minimal comments
- Only README with essence
- No link between business logic and implementation

**Result:** Code tokens not vectorially connected to what's being thought.

### Semantic Bridge

**Idea:** Create semantic bridge from human thoughts, mental models to code.

**Text types for bridge (20+):**
1. Specifications
2. Documentation
3. Textbooks
4. Algorithmic examples
5. Educational lectures
6. Code comments
7. Tickets
8. Bug reports
9. Technical articles
10. API documentation
11. Architectural diagrams
12. Pseudocode
13. Step-by-step tutorials
14. Code reviews
15. Pull request descriptions
16. Commit messages
17. Changelog
18. Release notes
19. Troubleshooting guides
20. FAQ

**And more...**
