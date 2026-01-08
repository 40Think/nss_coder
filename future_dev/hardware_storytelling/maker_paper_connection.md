# MAKER Paper Connection

## Reference

**MAKER Paper**: arXiv:2511.09030

**Key Finding**: Extreme decomposition works for LLMs.
- **1,048,575 steps** (20-disk Towers of Hanoi) with **0 errors**
- **Microagents** for each subtask
- **Multi-agent voting** for error correction
- **Massively Decomposed Agentic Processes (MDAP)** = future of AI

---

## NSS Coder Application of MAKER Philosophy

| MAKER Concept | NSS Coder Application |
|---------------|----------------------|
| **Extreme Decomposition** | Decomposition not only by tasks, but also **by abstraction levels** (human → transistors) |
| **Microagents** | Imaginary listeners (CPU, Cache, SIMD, etc.) = microagents for each level |
| **Multi-agent Voting** | Different levels (assembler, microcode, cache) "vote" for best solution |
| **Error Correction** | Bottom-up correction = error correction at each abstraction level |
| **Zero Errors** | Hardware-aware code = fewer performance bugs, memory leaks, crashes |

---

## Theoretical Foundation

### MAKER Proved
- Extreme decomposition enables LLMs to solve million-step problems
- Each step must be self-contained (~700 tokens)
- Multi-agent voting catches errors

### NSS Coder Extends
- Apply decomposition not just to logic, but to **hardware constraints**
- Create "agents" at each hardware level
- Use their "votes" to optimize code

---

## Decomposition Comparison

### MAKER: Horizontal Decomposition
```
Problem
  ↓
[Subtask 1] [Subtask 2] [Subtask 3] ... [Subtask N]
  ↓            ↓            ↓              ↓
[Result 1]  [Result 2]  [Result 3]  ... [Result N]
  ↓
Combined Result
```

### NSS Coder: Vertical Decomposition
```
Human Cognition
  ↓
Programmer Thinking
  ↓
High-Level Spec
  ↓
Pseudocode
  ↓
Code
  ↓
Assembler Analysis
  ↓
Microcode Analysis
  ↓
Cache Analysis
  ↓
Transistor Analysis
  ↑
[Bottom-Up Correction]
```

### Combined: 3D Decomposition
```
NSS Coder combines both:
- Horizontal: Split tasks into ~700-token units
- Vertical: Each unit analyzed through all hardware levels
- Result: Optimal code at both logical AND hardware levels
```

---

## Key Insight

> MAKER confirms: Extreme decomposition + multi-agent analysis = path to reliable systems.
>
> NSS Coder extends: Apply this not only to logic, but also to **hardware constraints**.
