# Development Phases: Top-Down and Bottom-Up

## Phase 1: Descent (Top-Down Decomposition)

1. **Global vision** → name, annotation, abstract
2. **Table of contents** → high-level sections
3. **Sections** → subsections
4. **Subsections** → specific algorithms
5. **At each level, generated:**
   - Prompts for next level
   - Specifications
   - Standard function names
   - Selected patterns and principles

---

## Phase 2: Ascent (Bottom-Up Integration)

1. **Microfunction implementation** (1-10 lines of code)
2. **Microfunction verification**
3. **Component assembly from microfunctions**
4. **Connectivity testing**
5. **Integration at upper levels**
6. **Connection point adjusted if needed**

---

## Microagent Work Packages

Each microagent creating their work section receives documentation package:

| Level | Contents |
|-------|----------|
| **Strategic** | Global project vision, development philosophy |
| **Tactical** | Component architecture, specifications |
| **Operational** | Specific algorithm, patterns, work principles |
| **Contextual** | Connections with other components, dependencies |

**Like a programmer in large corporation:**
- Doesn't need to know entire project
- Receives narrow work section
- Has all necessary documentation for their section
- Works within established standards and patterns

---

## Approach Benefits

✅ **Context poisoning exclusion**: each agent works with narrow area
✅ **Degeneration prevention**: focus on specific task, attention not lost
✅ **Parallelization**: different microagents work on different tree branches
✅ **Traceability**: each decision documented at its level
✅ **Scalability**: can add new branches without rewriting everything
✅ **Understandability**: any level can be understood in isolation
