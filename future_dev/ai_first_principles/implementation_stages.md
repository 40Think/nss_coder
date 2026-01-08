# Implementation Stages: Documentation and Tickets

## DDD Diagrams (3 Levels)

| Level | Scope |
|-------|-------|
| **Level 1** | Inside algorithm and specific task |
| **Level 2** | Algorithm's place in user's entire work |
| **Level 3** | User's place in entire company/project |

## Deep Research Before Code

**Key idea:** Between specification and code generation, generate Deep Research to find functions, examples, analogies.

**Process:**
1. **Internet search** (like developers search): Stack Overflow, GitHub, docs, articles
2. **Load actual examples**: Working code, patterns, best practices, anti-patterns
3. **Specifics for token gravity**: Function names, data structures, algorithms, libraries

**Result:** Code chunks attract more correct tokens.

---

## Stage 3: Textbook-Documentation

**Goal:** Convert architectural design into precise, language-independent logical steps.

### Step 3.1: CLI Micro-Documentation

Every library must expose functionality through CLI:
- Accept text input (stdin, args, files)
- Produce text output (stdout)
- Support JSON for structured data
- Enforces observability and testability

### Step 3.2: Glossary

Create glossary with all main function names for code connectivity.

### Step 3.3: Formal Languages (Critical Systems)

Write specification in formal languages: **Alloy**, **Z**, **TLA+**, **Coq**

For absolute unambiguity and automated verification. Only for critical systems.

### Step 3.4: Living Documentation

Hybrid of textbook and documentation:
- Russian pseudocode with implementation variants
- Explanation and code co-evolve
- Domain concepts → data models
- User stories → API endpoints
- Acceptance scenarios → tests

### Step 3.5: Algorithm Diagrams

Diagrams as **process representations**, not pictures:
- **Sequence Diagram** — who calls whom
- **State Diagram** — state changes
- **Data Flow Diagram** — information flow
- **Causal Loop Diagram** — feedback (important for AI)

### Step 3.6: Test Batteries

Develop test batteries after understanding algorithm logic.

### Step 3.7: Chinese Philosophy (Token Magnet)

Philosophy in Chinese with English translation as **token magnet**.
AI associations extend beyond IT domains.

---

## Stage 4: AI Programmer Tickets

**Goal:** Map formalized logic to concrete, executable code.

### Step 4.1: Ticket Generation

Generate tickets for AI to create specific functions.
Tickets + specification = context for agent.

**Result:** Agent sees spec, docs, and one ticket → creates one file.

### Step 4.2: Childish Code (Proportional to Complexity)

- Planning: Complex abstractions, mental models
- Implementation: Minimal programming means, closer to machine code

**AI writes code as it sees fit.**

### Step 4.3: 5 Code Complexity Levels

| Level | Allowed Constructs |
|-------|-------------------|
| **1 (Childish)** | IF/ELSE, loops only |
| **2 (Simple)** | Basic functions, simple data structures |
| **3 (Moderate)** | Classes, objects, moderate patterns |
| **4 (Advanced)** | Complex abstractions, advanced patterns |
| **5 (Unrestricted)** | Anything, maximum expressiveness |

**Selection principle:** Not by human complexity, but by AI token binding ease.

### Step 4.4: Comments and Semantic Connectivity

Comments per line if needed. Priority: AI expressing its Vision.

**Semantic connectivity through:**
- Logs
- Console outputs
- Long function/variable names (containing essence)
- Code comments

### Step 4.5: Bioorganic Fusion

> Code where spec + docs + ticket + comments + rich function names = looks like English text from distance.

**Related tokens swarm** like tree growing through fence — monolith expressing understanding clouds baked into unified meaning.

> Creating hologram or baking pie with all ingredients mixed explicitly.

### Step 4.6: Async (Where Needed)

No dead-ends, always paths forward.

Non-linear execution models:
- Statecharts (Harel)
- Petri Nets
- Actor Models
- Event-Driven Architectures

> Structure of execution matters more than content of code.

### Step 4.7: Feedback Analysis

Linters, tests on created code. Fix on the fly or regenerate from scratch.

---

## Code Evolution: Bloating to Compactness

**Phases:**
1. **Bloating**: Many autonomous functions, duplication
2. **Analysis**: Find patterns, common parts
3. **Compactness**: Create reusable LEGO blocks

**Ideal blocks:**
- Archetypal patterns
- Logical operations
- Universal components
- Easy to combine

---

## Native Code Language Principles

| Principle | Description |
|-----------|-------------|
| **Minimal Syntax** | Only IF, FOR, SET, CALL |
| **Sequential Flow** | Matches narrative: do A, then B, unless C |
| **No Hidden State** | All variables explicit |
| **LLM-Centric** | Designed for generation |
| **Linkable Units** | Each block is cognitive node |
| **Context-Aware** | Inline comments as meaning |

> **Structure code like mind map, not filesystem.**
> **Code must be graph-native, not tree-constrained.**
