# Hardware-Aware Programming

## V.8 Hardware-Aware Programming: Code Optimized for Hardware

**Connection with bidirectional storytelling (II.8)**:

This section describes **practical application** of dungeon specifications.
After code "told stories" to hardware and received feedback,
we apply **hardware-aware patterns** for writing efficient code.

---

## V.8.1 Principles of Hardware-Aware Programming

**Main principle**: Modern hardware is not an abstraction, but reality with specific constraints.

### Importance Hierarchy (from most critical)

| Priority | Aspect | Impact | Penalty |
|----------|--------|--------|---------|
| 1 | **Cache Locality** | 90% of performance | Cache miss = 100+ cycles |
| 2 | **SIMD Vectorization** | 4-16x speedup | Lost parallel opportunity |
| 3 | **Branch Prediction** | Avoid 15-20 cycle penalty | Misprediction stall |
| 4 | **Memory Alignment** | Avoid double load | Unaligned access penalty |
| 5 | **Register Pressure** | Avoid spill to memory | Stack access = slow |

---

## V.8.2 Optimization Patterns

### Pattern 1: Data-Oriented Design

```python
# ❌ BAD: Object-Oriented (poor cache locality)
class Particle:
    def __init__(self, x, y, vx, vy, mass):
        self.x, self.y, self.vx, self.vy, self.mass = x, y, vx, vy, mass

particles = [Particle(...) for _ in range(100000)]
for p in particles:  # Random access to each object
    p.x += p.vx  # Cache miss on each iteration
    p.y += p.vy


# ✅ GOOD: Data-Oriented (excellent cache locality)
import numpy as np

# Structure of Arrays (SoA)
particles = {
    'x': np.zeros(100000), 'y': np.zeros(100000),
    'vx': np.zeros(100000), 'vy': np.zeros(100000),
    'mass': np.zeros(100000)
}

# Sequential access + SIMD vectorization
particles['x'] += particles['vx']  # One operation for all
particles['y'] += particles['vy']

# SPEEDUP: ~50-100x
```

### Pattern 2: Batch Processing

```python
# ❌ BAD: One-by-one processing
for doc in documents:
    embedding = model.encode(doc)  # Overhead each call

# ✅ GOOD: Batch processing
for i in range(0, len(documents), batch_size):
    batch = documents[i:i+batch_size]
    embeddings = model.encode(batch)  # GPU parallel processing

# SPEEDUP: ~10-20x
```

### Pattern 3: Branchless Programming

```python
# ❌ BAD: Branches in hot loop
for v in values:
    if v < min_val:      # Branch misprediction
        result.append(min_val)
    elif v > max_val:    # Branch misprediction
        result.append(max_val)

# ✅ GOOD: Branchless (numpy)
result = np.clip(values, min_val, max_val)  # SIMD min/max

# SPEEDUP: ~5-10x
```

### Pattern 4: Memory Pool

```python
# ❌ BAD: Frequent allocations
for item in stream:
    buffer = []  # New allocation each time
    buffer.append(process(item))

# ✅ GOOD: Memory pool (reuse)
buffer = []  # One allocation
for item in stream:
    buffer.clear()  # Reuse
    buffer.append(process(item))

# SPEEDUP: ~2-5x
```

---

## V.8.3 Hardware-Aware Specifications

```markdown
# SPECIFICATION: Vector Search Engine

## HARDWARE REQUIREMENTS

HR1: Contiguous Memory Layout
  WHY: Sequential access enables CPU prefetching
  IMPLEMENTATION: Use numpy arrays, not Python lists
  METRIC: Cache miss rate < 1%

HR2: SIMD Vectorization
  WHY: 16x speedup via AVX-512
  IMPLEMENTATION: Use np.dot() for similarity computation
  METRIC: SIMD utilization > 80%

HR3: GPU Acceleration (if available)
  WHY: 100x speedup for vector operations
  IMPLEMENTATION: FAISS GPU index
  METRIC: GPU utilization > 60%

## PERFORMANCE TARGETS

- Throughput: > 100 QPS
- Latency (p50): < 5ms
- Latency (p99): < 20ms
```

---

## V.8.4 Profiling Tools

### Linux perf (CPU profiling)

```bash
# Cache misses profiling
perf stat -e cache-misses,cache-references python script.py

# Branch mispredictions
perf stat -e branch-misses,branches python script.py

# Detailed profile (hotspots)
perf record -g python script.py && perf report
```

### Interpretation

| Metric | GOOD | BAD |
|--------|------|-----|
| Cache miss rate | < 1% | > 10% |
| Branch misprediction | < 2% | > 10% |

### GPU Profiling (NVIDIA)

```bash
nvidia-smi -l 1        # Real-time monitoring
nvprof python script.py  # CUDA kernel profiling
```

---

## V.8.5 Hardware-Aware Code Checklist

### Before Writing
- [ ] Hardware requirements defined?
- [ ] Correct data structure chosen (numpy vs list)?
- [ ] Memory layout planned (SoA vs AoS)?
- [ ] Batch size determined for GPU/SIMD?

### During Writing
- [ ] Sequential access used (not random)?
- [ ] Loops vectorizable (numpy operations)?
- [ ] Conditions avoided in hot loops?
- [ ] Data aligned?

### After Writing
- [ ] perf stat run (cache misses < 1%)?
- [ ] SIMD utilization checked (> 80%)?
- [ ] Compared with theoretical peak?
- [ ] Profiled on real hardware (not VM)?

---

## V.8.6 When NOT to Optimize

**Rule 80/20**: 80% of time spent in 20% of code.

**Profile first, optimize second:**
1. Write simple code (readability > performance)
2. Profile (find hotspots)
3. Optimize only hotspots (hardware-aware)
4. Measure speedup (should be > 2x, otherwise not worth it)

### DON'T Optimize
- ❌ Rarely executed code (< 1% of time)
- ❌ Already fast code (< 1ms)
- ❌ Hard to profile code
- ❌ Prematurely (before profiling)

### DO Optimize
- ✅ Hot loops (> 50% of time)
- ✅ Critical paths (latency-sensitive)
- ✅ Batch operations (GPU/SIMD friendly)
- ✅ After profiling (data-driven)
