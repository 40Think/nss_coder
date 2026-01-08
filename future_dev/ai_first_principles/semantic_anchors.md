# Semantic Anchors System

## Overview

During all generation stages, special unique tags are used.

These tags work as **semantic anchors** and **references for LLM**, allowing:
- Connecting specifications, documentation, tickets and code
- Finding relevant context through project search
- Increasing generation coherence through transformer attention mechanisms
- Activating relevant memories through external memory system (RAG)

---

## Tag Creation Principles

### 1. Uniqueness and Searchability
- Tags must be unique within project
- Easily found through grep/terminal search
- Format: `@TAG:category:specific-name`

### 2. Semantic Load
- Tags contain domain keywords
- Trigger relevant associations in LLM latent space
- Activate transformer attention mechanisms

### 3. Hierarchical Structure
- Reflect abstraction level (feature → component → function)
- Show connections between components
- Enable dependency tree navigation

---

## Tag Types

```python
# @TAG:FEATURE:semantic-search-engine
# Feature tag - highest level

# @TAG:COMPONENT:vector-similarity-calculator
# Component tag - middle level

# @TAG:FUNCTION:cosine-distance-compute
# Function tag - low level

# @TAG:SPEC:semantic-search-requirements-v2
# Specification tag

# @TAG:TICKET:implement-safe-division-zero-handling
# Ticket tag

# @TAG:PATTERN:guard-clause-early-return
# Design pattern tag

# @TAG:OPTIMIZATION:cpu-branch-prediction-friendly
# Optimization tag

# @TAG:RELATED:error-handling-module
# Related module tag

# @TAG:GLOBAL-PROJECT:stage-1-mind-refactoring
# Global project stage tag

# @TAG:DIGITAL-TWIN:knowledge-retrieval-module
# Digital Twin architecture tag

# @TAG:ASI-COMPONENT:semantic-understanding-pattern
# ASI evolution component tag
```

---

## How LLM Uses Tags

### 1. Through Attention Mechanisms
- Seeing tag `@TAG:FEATURE:semantic-search-engine`, LLM activates all related concepts
- Increases probability of generating relevant code
- Tags work as "magnets" for related tokens

### 2. Through External Memory (RAG)
- Tags used as queries for vector DB search
- Related context retrieved and added to prompt
- Historical decisions and patterns activated

### 3. Through Cross-References
- Tags create explicit links between files
- Enable dependency tracing
- Support impact analysis for changes

---

## Tag Usage Example

```python
# ============================================================================
# @TAG:TICKET:implement-semantic-search-with-hybrid-scoring
# @TAG:GLOBAL-PROJECT:stage-1-mind-refactoring
# @TAG:DIGITAL-TWIN:knowledge-retrieval-module
# @TAG:ASI-COMPONENT:semantic-understanding-pattern
# ============================================================================
# TICKET: Implement Semantic Search with Hybrid Scoring
# ============================================================================

# ============================================================================
# RELATED TAGS & CROSS-REFERENCES
# ============================================================================
# @TAG:RELATED:query-processor-module
# @TAG:RELATED:result-ranker-module
# @TAG:RELATED:vector-index-module
# @TAG:PATTERN:strategy-pattern
# @TAG:PATTERN:dependency-injection
# @TAG:SPEC:hybrid-search-requirements-v2
# ============================================================================

class HybridSearchEngine:
    """
    @TAG:FUNCTION:hybrid-search-engine-main
    @TAG:OPTIMIZATION:gpu-acceleration
    @TAG:OPTIMIZATION:approximate-search
    """
    def search(self, query: str, top_k: int = 10):
        # @TAG:STEP:validation-phase
        if not query:
            return []
        
        # @TAG:STEP:semantic-search-phase
        semantic_results = self.vector_index.search(query, top_k)
        
        # @TAG:STEP:keyword-search-phase
        keyword_results = self.keyword_index.search(query, top_k)
        
        # @TAG:STEP:merge-phase
        return self._merge_results(semantic_results, keyword_results)
```

---

## Benefits

1. **Discoverability**: Easy to find all related code via grep
2. **Coherence**: LLM generates consistent code across files
3. **Traceability**: Requirements → specs → tickets → code linked
4. **Navigation**: Jump between related components
5. **RAG Enhancement**: Better retrieval of relevant context
