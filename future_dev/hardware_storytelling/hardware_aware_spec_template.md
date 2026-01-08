# Hardware-Aware Specification Template

## Overview

New type of specification that includes **hardware requirements** alongside functional requirements.

---

## Template

```markdown
# HARDWARE-AWARE SPECIFICATION: [Component Name]

## FUNCTIONAL REQUIREMENTS

FR1: [Functional requirement 1]
FR2: [Functional requirement 2]
...

## HARDWARE REQUIREMENTS (NEW!)

HR1: Sequential Memory Access
  - Данные должны быть в contiguous memory (numpy array, не list)
  - WHY: CPU prefetcher loads next cache lines in advance
  - IMPACT: Avoid cache misses (100+ cycles saved per element)

HR2: SIMD Vectorization
  - Operation must be vectorizable
  - Data aligned to 16/32 byte boundary
  - WHY: One SIMD instruction = 4-16 scalar operations
  - IMPACT: 4-16x speedup (theoretically)

HR3: Branch Prediction Friendly
  - Avoid conditional operators inside hot loops
  - If condition necessary: use branchless programming
  - WHY: Branch misprediction = 15-20 cycle penalty
  - IMPACT: For 1M iterations with 50% mispredictions = 10M cycles lost

HR4: Cache Line Alignment
  - Data structures aligned to cache line (64 bytes)
  - Avoid false sharing in multithreaded code
  - WHY: Unaligned access = two cache line loads instead of one
  - IMPACT: 2x more cache misses

HR5: Register Pressure
  - Minimize number of live variables in loop
  - Goal: all variables fit in registers (16 registers x86-64)
  - WHY: Spill to memory = additional stack accesses
  - IMPACT: Each spill = 3-5 cycles

## IMPLEMENTATION GUIDANCE

GOOD PATTERN (Hardware-Aware):
```python
# Contiguous memory, vectorized, no branches
data = np.array([...])  # Aligned, contiguous
result = np.sqrt(data)  # SIMD-vectorized
```

BAD PATTERN (Hardware-Unaware):
```python
# Random access, scalar, branches in loop
data = [...]  # List: scattered in memory
result = []
for x in data:  # Scalar operations
    if x > 0:  # Branch in hot loop
        result.append(math.sqrt(x))
```

## TESTING STRATEGY

PERFORMANCE TESTS:
  - Benchmark on real hardware (not VM)
  - Profiling: perf stat (cache misses, branch mispredictions)
  - Compare with theoretical peak (FLOPS, bandwidth)

HARDWARE METRICS:
  - Cache miss rate: < 1%
  - Branch misprediction rate: < 2%
  - SIMD utilization: > 80%
  - Memory bandwidth utilization: > 60%
```

---

## Hardware Requirement Categories

### Memory Access (HR-MEM)
- Sequential vs random access
- Contiguous memory layout
- Cache line utilization
- Prefetcher friendliness

### Computation (HR-COMP)
- SIMD vectorization
- Data alignment
- Loop unrolling potential
- Instruction-level parallelism

### Control Flow (HR-CTRL)
- Branch predictability
- Loop patterns
- Branchless alternatives
- Lookup tables vs conditions

### Resource Usage (HR-RES)
- Register pressure
- Stack vs heap allocation
- Memory pool usage
- Working set size

### Threading (HR-THREAD)
- False sharing avoidance
- Cache coherence
- Lock contention
- Thread affinity

### Security (HR-SEC)
- Constant-time operations
- Memory zeroing
- Side channel resistance
- Timing attack prevention
