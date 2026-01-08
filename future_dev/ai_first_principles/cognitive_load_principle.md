# Cognitive Load Principle

## Core Rule

**One function = One cognitive operation**

---

## Observation from AI Model Practice

The smaller the AI model, the simpler the task should be:
- **Trillion-parameter model**: Can handle dozens of tasks, huge context — it will do everything
- **2-8 billion parameter models**: Require segmentation to level "one task = one cognitive operation"

---

## Human Analogy

Humans also cannot solve dozens of operations simultaneously in one pass. We think sequentially, step by step.

---

## Two Degrees of Simplification

### 1. Formal Simplicity
- IF/ELSE instead of complex patterns
- Loops instead of functional programming
- Flat code instead of abstractions

### 2. Algorithmic Simplicity (NEW)
- Minimize algorithm entanglement
- Minimize "hidden layers of meaning"
- Minimize cognitive load

---

## Hidden Layers of Meaning

A function can have:
- **10 hidden layers** — need to hold many concepts simultaneously
- **1 hidden layer** — one simple idea, easy to understand

**Strive for minimum.**

---

## LeetCode Difficulty Analogy

| Level | Description | Our Approach |
|-------|-------------|--------------|
| **Easy** | Simple algorithms, straightforward logic | ✅ **Use this** |
| **Medium** | Requires data structure knowledge, multiple steps | ⚠️ Use if necessary |
| **Hard** | Complex algorithms, dynamic programming | ❌ Avoid at function level |
| **Very Hard** | Requires deep understanding, many edge cases | ❌ Avoid |
| **Nightmare** | Extremely complex algorithms | ❌ **ONLY at planning level** |

---

## Key Principle

> **Nightmare-level complexity should appear at planning level in human mind, NOT in specific code solutions.**

**Don't write code that takes a week to understand.**

---

## Minimizing Cognitive Load

Minimize load on the mind:
- **For human** who will study this code
- **For AI** that plans this code

**Don't need to hold hundreds of elements in mind simultaneously.**

Each function should be understandable in isolation, without needing to hold entire project in memory.

---

## Elevator Button Design Analogy

### Bad Designer (shows off)
- Arranges buttons in a spiral
- Makes zigzags
- Uses non-standard shapes
- Tries to show "creativity"

### Good Designer (keeps simple)
- Arranges buttons in familiar order (1, 2, 3... bottom to top)
- Uses standard shapes
- Makes intuitive
- Doesn't make you think

---

## Code Examples

### ❌ Bad (Entangled Algorithm)

```python
def find_max(arr):
    # Uses recursive divide-and-conquer with memoization
    # and bit operations for optimization
    memo = {}
    def helper(l, r, depth):
        key = (l, r, depth)
        if key in memo:
            return memo[key]
        if l == r:
            return arr[l]
        mid = (l + r) >> 1  # Bit shift instead of division
        left_max = helper(l, mid, depth + 1)
        right_max = helper(mid + 1, r, depth + 1)
        result = left_max if left_max > right_max else right_max
        memo[key] = result
        return result
    return helper(0, len(arr) - 1, 0)
```

**Cognitive Load:**
- Need to understand recursion
- Need to understand memoization
- Need to understand bit operations
- Need to understand divide-and-conquer
- **4-5 concepts simultaneously** = high load

### ✅ Good (Simple Algorithm)

```python
def find_max(arr):
    """
    Find maximum element in array.
    
    ALGORITHM: Simple linear scan
    COMPLEXITY: O(n) time, O(1) space
    COGNITIVE LOAD: Minimal - one simple concept
    """
    # STEP 1: Start with first element as current max
    max_value = arr[0]
    
    # STEP 2: Compare each element with current max
    for element in arr:
        if element > max_value:
            max_value = element
    
    # STEP 3: Return the maximum value found
    return max_value
```

**Cognitive Load:**
- Simple loop
- Simple comparison
- **1 concept** = minimal load

---

## Summary Principle

> Don't complicate algorithms without need.
> Use simplest algorithm that solves the problem.
> Complexity should be in architecture (planning), not in code (implementation).
> One function = one cognitive operation.
> All genius is simple.
