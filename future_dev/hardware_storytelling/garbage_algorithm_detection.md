# Garbage Algorithm Detection

## Core Concept

**Many algorithms that look good on paper are terrible on hardware.**

Hardware analysis **filters them out BEFORE code is written**.

---

## Common Garbage Patterns Detected by Hardware

| Pattern | Why It's Bad (Hardware Perspective) | Hardware Recommendation |
|---------|---------------------------------------|------------------------|
| **Deep recursion** | Stack overflow + poor cache locality | Iterative approach or tail recursion |
| **Frequent small allocations** | Memory fragmentation + allocator overhead | Memory pool or stack allocation |
| **Conditions in hot loops** | Branch misprediction (15-20 cycle penalty) | Branchless programming or lookup table |
| **Random array access** | Cache miss on each access (100+ cycles) | Sequential access or prefetching |
| **Multiple passes over data** | Data evicted from cache between passes | Single-pass algorithm or fusion |
| **Unaligned data** | Two cache line loads instead of one | Alignment to 16/32/64 bytes |
| **Scalar operations in loop** | SIMD not utilized (4-16x slowdown) | Vectorization through intrinsics or libraries |

---

## Example: Recursive Fibonacci

### Traditional Code (Without Hardware Analysis)

```python
def fibonacci(n: int) -> int:
    """Compute n-th Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Looks elegant, but...
```

### Hardware Analysis

```
STACK ANALYZER:
  - Recursion depth: n levels
  - Stack frame size: ~64 bytes (return address, parameters, locals)
  - For n=40: 64 * 2^40 bytes = STACK OVERFLOW
  
CACHE ANALYZER:
  - Each function call: new stack frame
  - Stack frames scattered in memory
  - Cache locality: TERRIBLE
  - Most accesses: cache miss
  
BRANCH PREDICTOR:
  - Condition `if n <= 1`: unpredictable for different n
  - Branch misprediction at each recursion level
  
COMPLEXITY ANALYZER:
  - Time complexity: O(2^n) - exponential growth
  - For n=40: ~1 trillion function calls
  
VERDICT: ❌ GARBAGE ALGORITHM
  - Stack overflow risk
  - Poor cache locality
  - Exponential complexity
  - Branch mispredictions
```

### Code After Correction from Dungeon

```python
def fibonacci(n: int) -> int:
    """
    Compute n-th Fibonacci number.
    
    HARDWARE-AWARE OPTIMIZATION:
    - Iterative approach (no stack overflow)
    - O(n) complexity instead of O(2^n)
    - Excellent cache locality (3 variables on stack)
    - Predictable branches (one loop)
    
    @TAG:HARDWARE-OPTIMIZED:iterative
    @TAG:HARDWARE-OPTIMIZED:cache-friendly
    """
    if n <= 1:
        return n
    
    # Three variables fit in CPU registers
    # No memory accesses in loop
    prev, curr = 0, 1
    
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr  # Branchless swap
    
    return curr
```

### Hardware Analysis After Optimization

```
STACK:
  - Depth: 1 (no recursion)
  - Stack usage: ~16 bytes (2 variables)
  - Stack overflow: IMPOSSIBLE

CACHE:
  - Working set: 16 bytes (prev, curr, n)
  - All data in L1 cache (32 KB)
  - Cache misses: 0

BRANCH PREDICTOR:
  - One loop: predictable pattern
  - Branch prediction accuracy: ~99%

REGISTERS:
  - prev, curr, _ → fit in registers
  - No memory accesses

COMPLEXITY:
  - Time: O(n) instead of O(2^n)
  - Space: O(1) instead of O(n)

SPEEDUP: ~1,000,000x for n=40
```

---

## Anti-Pattern Detection Checklist

Before writing code, ask:

1. **Stack**: Will this cause deep recursion?
2. **Cache**: Is data access sequential or random?
3. **Branches**: Are there unpredictable conditions in hot paths?
4. **SIMD**: Can operations be vectorized?
5. **Memory**: Are there frequent small allocations?
6. **Alignment**: Is data aligned to cache line boundaries?
7. **Passes**: How many times do we iterate over the data?

If any answer is concerning, **redesign before coding**.
