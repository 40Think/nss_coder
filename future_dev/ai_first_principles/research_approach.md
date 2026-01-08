# Research Approach

## Core Philosophy

Before doing anything, always research first.

---

## 2.1 Documentation First

**Before doing anything, always search for:**

- Project documentation
- Specifications
- README.md for understanding essence and architecture
- Existing patterns in codebase

### Research Order

1. **Internal docs**: Project README, specs, architecture docs
2. **Code patterns**: How similar things are done in the project
3. **External docs**: Library documentation, API references
4. **Best practices**: Industry standards for the technology

---

## 2.2 Internet Research

**For any task, we must search the internet for optimal solutions for each implementation step:**

- Best practices for specific technology
- Existing libraries and solutions
- Architectural patterns
- Performance and optimizations

### What to Search

| Task Type | Search For |
|-----------|------------|
| New feature | Similar implementations, design patterns |
| Optimization | Benchmarks, profiling guides, hardware docs |
| Bug fix | Similar issues, known solutions |
| Integration | API docs, SDK examples, community solutions |

---

## 2.3 Questions Instead of Assumptions

**If something is not said — ask.**

### Guidelines

- Leave question lists in implementation plan
- Don't make assumptions about critical decisions
- Document uncertainties
- Request clarifications before starting implementation

### Question Template

```markdown
## ❓ Questions Requiring Clarification

### Critical (Blocking)
1. Which database should we use: PostgreSQL or SQLite?
2. What is the expected latency requirement?

### Important (Should Answer Soon)
3. Should we support concurrent users?
4. Is there a preference for testing framework?

### Nice to Know
5. Are there branding guidelines for UI?
```

---

## Research Workflow

```
1. Receive task
    ↓
2. Search internal documentation
    ↓
3. Identify knowledge gaps
    ↓
4. Search external resources
    ↓
5. Formulate questions for unclear items
    ↓
6. Get answers to critical questions
    ↓
7. Begin implementation
```
