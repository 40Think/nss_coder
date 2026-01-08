# Holographic Ticket Template

## Core Concept

Tickets for AI programmers must be **so detailed** that they generate exactly the code needed.

---

## Holographic Principle

Even if the AI programmer **lost from view** all previous context:
- All our specifications
- All our conversations
- All details
- All project architecture

**The meaning is so deeply packed, so holographic** in what's written in the ticket, that AI will still:
- Create correct code
- Use correct function names
- Apply correct patterns
- Integrate code in correct architecture location

---

## Priority: Density of Meaning, Not Volume

- **Don't limit yourself** in ticket page count
- Main thing is not **text volume**, but **meaning volume** packed inside
- Better 10 pages of dense meaning than 1 page of shallow description
- Each sentence should carry maximum information

---

## Language: AI for AI

You write **in AI language for another AI**, not for humans:
- Use terms that activate correct patterns in latent space
- Include semantic anchors and related concepts
- Describe not only "what to do", but "why exactly this way"
- Add alternatives that were considered and rejected
- Explain connections with other system parts

---

## Template Structure

```python
# ============================================================================
# @TAG:TICKET:implement-semantic-search-with-hybrid-scoring
# @TAG:GLOBAL-PROJECT:stage-1-mind-refactoring
# @TAG:DIGITAL-TWIN:knowledge-retrieval-module
# @TAG:ASI-COMPONENT:semantic-understanding-pattern
# ============================================================================
# TICKET: Implement Semantic Search with Hybrid Scoring
# ============================================================================
# Created: 2025-11-29
# Author: AI Architect (Overlay ASI)
# Priority: High
# Complexity: Medium-High
# Estimated effort: 3-5 hours of focused implementation
# ============================================================================

# ============================================================================
# CONTEXT: Why this exists
# ============================================================================
# This module is part of the global project to refactor human thinking into code.
# Specifically, it models the human ability to find relevant information by 
# combining semantic understanding (meaning) with keyword matching (precision).
#
# In the Digital Twin architecture, this becomes the knowledge retrieval module.
# In the ASI evolution, this pattern contributes to semantic understanding.
#
# Current state: We have basic vector search working, but it misses exact matches.
# Problem: User searches for "Python 3.11 features" but gets results about "Python"
# Root cause: Pure semantic search doesn't prioritize exact keyword matches
# Solution: Hybrid scoring that combines semantic similarity + keyword matching
# ============================================================================

# ============================================================================
# PROBLEM STATEMENT
# ============================================================================
# Users need to find documents that are:
# 1. Semantically relevant to their query (meaning-based)
# 2. Contain exact keyword matches (precision-based)
# 3. Ranked by a combination of both factors
#
# Example query: "machine learning optimization techniques"
# Expected behavior:
#   - High rank: Documents about "ML optimization" (semantic + keywords)
#   - Medium rank: Documents about "neural network training" (semantic only)
#   - Low rank: Documents about "code optimization" (keyword only, wrong context)
# ============================================================================

# ============================================================================
# ARCHITECTURAL CONTEXT
# ============================================================================
# Position in system:
#   User Query → Query Processor → [THIS MODULE] → Result Ranker → User
#
# Dependencies:
#   - Upstream: query_processor.py (provides normalized query + embeddings)
#   - Downstream: result_ranker.py (receives scored results)
#   - Sibling: vector_index.py (provides semantic search)
#   - Sibling: keyword_index.py (provides keyword search)
#
# Integration points:
#   - Must accept QueryContext object (defined in query_processor.py)
#   - Must return ScoredResults list (defined in result_ranker.py)
#   - Must use VectorIndex.search() and KeywordIndex.search()
# ============================================================================

# ============================================================================
# REQUIREMENTS
# ============================================================================
# Functional:
#   FR1: Accept query string and return ranked document IDs
#   FR2: Combine semantic similarity scores (0-1) with keyword match scores (0-1)
#   FR3: Support configurable weighting (alpha for semantic, 1-alpha for keyword)
#   FR4: Handle edge cases: no semantic matches, no keyword matches, no matches
#   FR5: Return top-K results (configurable, default K=10)
#
# Non-functional:
#   NFR1: Performance: < 100ms for 10K documents
#   NFR2: Memory: O(K) space complexity for results
#   NFR3: Accuracy: Hybrid should outperform pure semantic by 15-20%
#   NFR4: Maintainability: Clear separation of scoring logic
# ============================================================================

# ============================================================================
# DESIGN DECISIONS
# ============================================================================
# Decision 1: Hybrid scoring formula
#   Options considered:
#     A) Simple average: (semantic + keyword) / 2
#     B) Weighted sum: alpha * semantic + (1-alpha) * keyword
#     C) Multiplicative: semantic * keyword
#     D) Learned combination: ML model to combine scores
#   
#   Chosen: B (Weighted sum)
#   Reasoning:
#     - Allows tuning via alpha parameter
#     - Preserves score range [0, 1]
#     - Computationally cheap
#     - Interpretable results
#   
#   Rejected A: No flexibility
#   Rejected C: Penalizes documents strong in one dimension
#   Rejected D: Overkill for current needs
#
# Decision 2: Score normalization
#   Semantic scores from cosine similarity are already [0, 1]
#   Keyword scores from BM25 need normalization to [0, 1]
#   Method: Min-max normalization per query
#
# Decision 3: Handling missing matches
#   If no semantic matches: Use keyword-only (alpha=0)
#   If no keyword matches: Use semantic-only (alpha=1)
#   If no matches at all: Return empty list with warning log
# ============================================================================

# ============================================================================
# IMPLEMENTATION GUIDANCE
# ============================================================================
# Suggested approach:
#   1. Create HybridSearchEngine class
#   2. Initialize with VectorIndex, KeywordIndex, default_alpha=0.7
#   3. Implement search(query, top_k, alpha) method
#   4. Inside search():
#      a. Get semantic results: vector_index.search(query, top_k * 2)
#      b. Get keyword results: keyword_index.search(query, top_k * 2)
#      c. Normalize keyword scores to [0, 1]
#      d. Merge results: for each doc, compute hybrid_score
#      e. Sort by hybrid_score descending
#      f. Return top K
#
# Function signatures:
#   def search(query: str, top_k: int = 10, alpha: float = 0.7) -> List[ScoredResult]
#   def _normalize_scores(scores: List[float]) -> List[float]
#   def _compute_hybrid_score(semantic: float, keyword: float, alpha: float) -> float
#   def _merge_results(semantic_results, keyword_results, alpha) -> List[ScoredResult]
# ============================================================================

# ============================================================================
# TESTING STRATEGY
# ============================================================================
# Unit tests:
#   - test_hybrid_search_normal_case()
#   - test_hybrid_search_no_semantic_matches()
#   - test_hybrid_search_no_keyword_matches()
#   - test_hybrid_search_no_matches()
#   - test_score_normalization()
#   - test_alpha_parameter_effect()
#
# Integration tests:
#   - test_integration_with_query_processor()
#   - test_integration_with_result_ranker()
#
# Performance tests:
#   - test_search_performance_10k_docs()
# ============================================================================

# ============================================================================
# EXPECTED OUTCOME
# ============================================================================
# After implementing this ticket, we should have:
#   1. HybridSearchEngine class with clean API
#   2. Configurable alpha parameter for tuning
#   3. Robust handling of edge cases
#   4. Performance < 100ms for 10K docs
#   5. Test coverage > 90%
#   6. Documentation with usage examples
#
# Success criteria:
#   - All unit tests pass
#   - Integration tests pass
#   - Performance benchmark meets NFR1
#   - Code review approved
#   - Accuracy improvement verified on test set
# ============================================================================
```

---

## Key Observations

- **~200 lines** of context for one function
- Even without spec access, AI knows what to do
- Includes: context, problem, architecture, requirements, decisions, patterns, tests
- Language optimized for AI understanding
- Semantic anchors through tags
- Alternatives and decision rationales

**Result**: AI programmer creates exactly the code needed, even if they never saw rest of project.
