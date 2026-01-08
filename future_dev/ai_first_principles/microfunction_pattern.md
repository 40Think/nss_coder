# Microfunction Pattern: Extreme Context-to-Code Ratio

## Core Concept

A microfunction is 1-10 lines of executable code surrounded by 80+ lines of semantic context.

---

## Example 1: 3 Lines of Code, 40+ Lines of Context

```python
# ============================================================================
# SEMANTIC CONTEXT: Vector Similarity Search with Cosine Distance
# ============================================================================
# 
# PURPOSE: Find most similar documents in vector space
# DOMAIN: Information Retrieval, Semantic Search, RAG
# RELATED CONCEPTS: embeddings, cosine similarity, nearest neighbors, FAISS
# ARCHITECTURE POSITION: Core retrieval layer
# 
# ALTERNATIVES CONSIDERED:
# - Euclidean distance (less effective for normalized vectors)
# - Dot product (equivalent to cosine for unit vectors)
# - Learned similarity metrics (too complex for current requirements)
#
# WHY THIS APPROACH:
# Cosine similarity is invariant to vector scale, ideal for text embeddings
# where semantic proximity matters, not absolute magnitude
# ============================================================================

def find_similar_documents(query_embedding, document_embeddings, top_k=5):
    """
    Search for top-K most semantically similar documents.
    
    Uses cosine distance in embedding space.
    Standard approach in semantic search and RAG systems.
    
    Args:
        query_embedding: Query vector (numpy array, shape: [embedding_dim])
        document_embeddings: Document matrix (shape: [num_docs, embedding_dim])
        top_k: Number of most similar documents to return
        
    Returns:
        List[int]: Indices of top-K documents, sorted by descending similarity
    """
    # Compute cosine similarity: dot(q, d) / (||q|| * ||d||)
    # For normalized vectors this is just dot product
    similarities = document_embeddings @ query_embedding  # 3 lines of code
    
    # Find top-K indices
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    return top_indices
```

**Observations:**
- 3 lines of executable code
- ~40 lines of semantic context
- Any AI reading this code gets dense cloud of related concepts
- When generating similar code, AI attracts correct solutions thanks to this context

---

## Example 2: 1 Line of Business Logic, 80+ Lines of Context

```python
# ============================================================================
# TICKET: Implement safe division with zero handling
# ============================================================================
# Created: 2025-11-29
# Author: AI Agent (Overlay ASI)
# Component: math_utils/safe_operations
# Related: error_handling.py, validation.py
# ============================================================================

# ============================================================================
# SPECIFICATION
# ============================================================================
# Function: safe_divide
# Purpose: Perform division with zero protection
# Input: two numbers (dividend, divisor)
# Output: division result or default_value on division by zero
# Edge cases: 
#   - divisor == 0 → returns default_value
#   - divisor very close to 0 (< epsilon) → returns default_value
#   - infinity handling → returns default_value
# ============================================================================

# ============================================================================
# PSEUDOCODE (Human-readable logic)
# ============================================================================
# FUNCTION safe_divide(dividend, divisor, default_value=0, epsilon=1e-10):
#     IF absolute_value(divisor) < epsilon THEN
#         LOG warning about division by near-zero
#         RETURN default_value
#     END IF
#     
#     TRY
#         result = dividend / divisor
#         IF result is infinity THEN
#             RETURN default_value
#         END IF
#         RETURN result
#     CATCH any_error
#         RETURN default_value
#     END TRY
# END FUNCTION
# ============================================================================

# ============================================================================
# ARCHITECTURE DIAGRAM (ASCII)
# ============================================================================
#
#   Input (dividend, divisor)
#        |
#        v
#   [Check divisor ≈ 0?] --Yes--> [Return default_value]
#        |
#        No
#        v
#   [Perform division]
#        |
#        v
#   [Check infinity?] --Yes--> [Return default_value]
#        |
#        No
#        v
#   [Return result]
#
# ============================================================================

# ============================================================================
# PATTERNS & OPTIMIZATIONS
# ============================================================================
# Pattern: Guard Clause (early return on invalid input)
# CPU-level: Branch prediction friendly (common case is valid division)
# Memory: No allocations, stack-only operation
# Complexity: O(1) time, O(1) space
# ============================================================================

def safe_divide(dividend, divisor, default_value=0.0, epsilon=1e-10):
    """
    Safe division with zero protection.
    
    Examples:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)
        0.0
        >>> safe_divide(10, 1e-15, default_value=-1)
        -1.0
    """
    if abs(divisor) < epsilon:  # Guard clause: protect from ÷~0
        return default_value
    
    try:
        result = dividend / divisor  # SINGLE LINE of business logic
        return default_value if math.isinf(result) else result
    except (ZeroDivisionError, OverflowError):
        return default_value
```

**Observations:**
- **1 line** of core business logic: `result = dividend / divisor`
- **80+ lines** of semantic glue
- Human without Python knowledge can understand via pseudocode
- AI gets full context for modification or debugging
- Everything needed for understanding is in one file
