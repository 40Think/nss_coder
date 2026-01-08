# 7 Complexity Levels for AI Code

## Overview

AI, based on ticket, context, and overall task, understands which code is **simplest** for the case.

If implementation isn't possible through simpler level, use more complex one. **As needed.**

No rigid rules. AI based on its semantic space, which tokens attract, chooses how to assemble working algorithm.

---

## Level 1: Linear Code (Simplest)

```python
# Sequence of operations without branching
result = input_data
result = result + 10
result = result * 2
result = result - 5
return result
```

**When to Use:**
- Simple sequence of operations
- No conditions, no loops
- Direct data transformation

**Complexity for AI:** Minimal  
**Complexity for CPU:** Minimal (linear execution, excellent branch prediction)

---

## Level 2: Conditions and Branching (IF/ELSE)

```python
# Simple conditions
if value > 0:
    result = value * 2
else:
    result = 0

# Multiple conditions
if condition_a:
    do_a()
elif condition_b:
    do_b()
else:
    do_c()
```

**When to Use:**
- Need to make decision based on condition
- Different execution paths
- Guard clauses for validation

**Complexity for AI:** Low (natural logic branching)  
**Complexity for CPU:** Low (branch prediction works well for predictable patterns)

---

## Level 3: Loops (FOR/WHILE)

```python
# Simple loop
for item in items:
    process(item)

# Loop with condition
while not done:
    step()
    if check():
        done = True

# Nested loops
for i in range(n):
    for j in range(m):
        matrix[i][j] = compute(i, j)
```

**When to Use:**
- Need to process collection of elements
- Repeating operations
- Iterative algorithms

**Complexity for AI:** Medium (requires understanding iteration)  
**Complexity for CPU:** Medium (loop unrolling, vectorization possible)

---

## Level 4: Functions and Procedural Decomposition

```python
def validate_input(data):
    if data is None:
        return False
    if len(data) == 0:
        return False
    return True

def transform_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result

def main(input_data):
    if not validate_input(input_data):
        return None
    return transform_data(input_data)
```

**When to Use:**
- Logic becomes complex for one function
- Need reusability
- Improved readability through decomposition

**Complexity for AI:** Medium (requires decomposition planning)  
**Complexity for CPU:** Medium (function call overhead, but inlining helps)

---

## Level 5: Data Structures (Classes, Dicts, Lists)

```python
class DataProcessor:
    def __init__(self):
        self.cache = {}
        self.results = []
    
    def process(self, item):
        if item in self.cache:
            return self.cache[item]
        result = expensive_compute(item)
        self.cache[item] = result
        self.results.append(result)
        return result
```

**When to Use:**
- Need to organize related data
- State management required
- Complex data relationships

**Complexity for AI:** Medium-High  
**Complexity for CPU:** Medium (memory access patterns matter)

---

## Level 6: Design Patterns

```python
# Strategy pattern
class SearchStrategy:
    def search(self, query): pass

class SemanticSearch(SearchStrategy):
    def search(self, query):
        return self.model.embed(query)

class KeywordSearch(SearchStrategy):
    def search(self, query):
        return self.index.lookup(query)

class HybridSearch:
    def __init__(self, strategies):
        self.strategies = strategies
    
    def search(self, query):
        results = []
        for strategy in self.strategies:
            results.extend(strategy.search(query))
        return self.rank(results)
```

**When to Use:**
- Need flexibility for future changes
- Multiple interchangeable implementations
- Complex behavior composition

**Complexity for AI:** High (requires pattern knowledge)  
**Complexity for CPU:** High (indirection, virtual calls)

---

## Level 7: Advanced Abstractions (Metaprogramming, Functional)

```python
# Decorators
def cache_result(func):
    cache = {}
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper

# Functional composition
from functools import reduce
pipeline = lambda fns: lambda x: reduce(lambda v, f: f(v), fns, x)
process = pipeline([validate, transform, normalize, output])

# Metaclasses
class PluginMeta(type):
    plugins = {}
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        if name != 'Plugin':
            mcs.plugins[name] = cls
        return cls
```

**When to Use:**
- Building frameworks or DSLs
- Extreme code reuse requirements
- Dynamic behavior modification

**Complexity for AI:** Very High (requires deep abstraction understanding)  
**Complexity for CPU:** Variable (depends on implementation)

---

## Selection Principle

```
SIMPLEST THAT WORKS

Start at Level 1
    ↓
Can it solve the problem?
    ↓
YES → Use this level
NO  → Try next level
    ↓
Repeat until solution found
```

---

## Key Philosophy

> Use the **simplest possible level** that solves the problem.
> 
> "Child-like" code using IF/ELSE and loops is **perfectly acceptable**.
> 
> Complex patterns are only for complex requirements.
