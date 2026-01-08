# Orchestration Advanced Features

## Missing Stages Tree (17.8)

**Function:** If NeuroCore forgot important method/stage, output **tree of everything** to do before creating code.

**When:** Automatically during critic stage.

**Process:**
1. AI-critic analyzes specification
2. Checks documentation completeness
3. If something missing → outputs missing stages tree
4. Shows what to do before code

### Example Tree

```
Missing stages:
├── Stage 1: Understanding needs
│   ├── ✅ User Story
│   ├── ✅ Domain analysis
│   ├── ❌ Pre-Mortem Analysis (MISSING)
│   └── ❌ Intent-graph (MISSING)
├── Stage 2: Specification
│   ├── ✅ Alternatives analysis
│   ├── ❌ Deep Research (MISSING)
│   └── ✅ DDD diagrams
└── Stage 3: Documentation
    ├── ✅ Glossary
    ├── ❌ DSL (MISSING)
    └── ✅ Diagrams
```

---

## Orchestration Advantages (17.9)

### 1. More Stable and Reliable

**Why:** Each link is very simple.

**Principle:**
- Fragment into simple parts
- Each part solves one task
- Easy to test and replace
- If one link breaks — others work

### 2. More Advanced

> Much more advanced than currently accepted.

**Why:**
- Dynamic prompt constructor
- Isolated contexts
- Rotator agents
- Hidden orchestration

### 3. Flexibility

**Not obligated to go through all sections:**
- Rotators decide what's relevant now
- What can be skipped
- Where to switch

**Adaptiveness:**
- Simple tasks → fewer stages
- Complex tasks → more stages
- Dynamic decision

---

## Code Evolution (17.10)

### Evolution Phases

| Phase | Description |
|-------|-------------|
| **1. Bloating** | Many autonomous functions, duplication |
| **2. Analysis** | Find patterns, common parts |
| **3. Compactness** | Create reusable LEGO blocks |

### Ideal Blocks

- Archetypal patterns
- Logical operations
- Universal components
- Easy to combine

---

## Orchestration Results (17.11)

**What human sees:** Sequential dialogue.

**Behind the curtain:** Model rotation, system prompts, contexts.

### How it works

- **Parallel**: Different agents work simultaneously
- **Horizontal**: Same abstraction level
- **Vertical**: Different abstraction levels

> Like in software development corporation with huge team.

### What we get

| Benefit | Description |
|---------|-------------|
| **Stability** | Each link simple |
| **Advanced** | Much more advanced architecture |
| **Flexibility** | Not obligated to go through all |
| **Scalability** | Easy to add new agents |
| **Efficiency** | 700 tokens = 1M steps without errors |
| **Evolution** | From bloating to compactness |

---

## Dynamic System Prompt Assembly (17.9)

**Key idea:** Split generator into what's in system prompt and specific prompts in RAG memory, pulled as needed into context.

### Problem with Static System Prompt

- Information overload
- Much unused context
- Quality degradation
- Exceeds average human level

### Solution: Agentic Context-Engineering

**Principle:** Pass system prompt and prompt segments, from which context dynamically assembled.

### Structure

**1. Base System Prompt (always active):**
- Role and mission
- Key principles
- Communication style
- Base constraints

**2. Numbered Blocks in RAG:**
- Block 1: AI-First development principles
- Block 2: Coding standards
- Block 3: Specification creation process
- Block 4: DDD and architecture
- Block 5: Testing and verification
- ... (up to 50-100 blocks)

**3. Dynamic Block Selection:**
- In response to task
- By rotator agents
- Based on current context
