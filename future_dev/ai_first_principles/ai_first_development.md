# AI-First Development

## Core Principle

**We program in a way that's convenient for AI to plan, develop, and write code, not just for humans.**

---

## Key Aspects

### Human Role
- Set high-level logic and architectures
- Guide overall direction
- Validate and approve

### AI Role
- Gradually transform ideas into concrete solutions through dialogue
- Handle implementation details
- Optimize for both readability and performance

### Code Nature
- Code is the **materialization of dialogue** between human and AI
- Project structure optimized for AI understanding, not just compilation
- Documentation serves as AI context, not just human reference

---

## Implications

### Project Structure
```
Traditional:
  - Organized for human navigation
  - Minimal comments (humans remember context)
  - Implicit patterns

AI-First:
  - Organized for AI context retrieval
  - Rich comments (every decision explained)
  - Explicit patterns with tags
```

### Documentation
```
Traditional:
  - Written after code
  - External to code files
  - Often outdated

AI-First:
  - Written before and with code
  - Embedded in code files
  - Always current (part of development)
```

### Communication
```
Traditional:
  - Imperative: "Create function X"
  - Focus on implementation
  - Short, assuming context

AI-First:
  - Declarative: "We need capability Y because..."
  - Focus on intention
  - Rich context, explicit assumptions
```

---

## Practical Guidelines

1. **Always explain WHY**, not just what
2. **Include context** in every file header
3. **Use semantic tags** for cross-references
4. **Write for future AI sessions** (no implicit context)
5. **Structure for retrieval**, not just navigation
