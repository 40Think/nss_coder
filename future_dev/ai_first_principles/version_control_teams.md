# Version Control, Teams, and Legacy Code

## Migration Between Configurations (28.11)

```yaml
migration:
  current: "legacy-project"
  target: "balanced"
  
  plan:
    - phase: 1
      duration: "2 weeks"
      changes: ["Increase comment_ratio to 50%", "Add specs to new files"]
    
    - phase: 2
      duration: "2 weeks"
      changes: ["Enable bidirectional_storytelling", "Reduce max_file_lines to 300"]
    
    - phase: 3
      duration: "4 weeks"
      changes: ["Increase comment_ratio to 70%", "Enable hardware_aware"]
    
    - phase: 4
      duration: "4 weeks"
      changes: ["Reduce cognitive_unit to 700", "Enable extreme decomposition"]
  
  auto_migrate: true
  rollback_on_failure: true
```

---

## IDE and CLI Integration (28.12)

### VS Code Settings
```json
{
  "nss-coder.config": ".nss-coder/config.yaml",
  "nss-coder.enableLinting": true,
  "nss-coder.preset": "balanced"
}
```

### CLI Commands
```bash
nss-coder check                        # Check compliance
nss-coder apply --preset balanced      # Apply config
nss-coder report --format html         # Generate report
nss-coder migrate --from legacy --to balanced --duration 12w
```

**Key principles:**
1. ✅ Everything configurable
2. ✅ Preset configurations
3. ✅ Gradual adoption
4. ✅ Monitoring
5. ✅ Smooth migration

---

## XXIX. Version Control in AI-First

**Key idea:** Git stores evolution of thought from idea to implementation.

**Principle:** Each commit is atomic transformation in storytelling chain.

### 29.1 Semantic Commits with AI Context

```
feat(search): bidirectional storytelling optimization

CONTEXT:
- Applied hardware-aware optimization from section II.8
- Code told stories to CPU/Cache
- Received specs from underground

CHANGES:
- Replaced list with numpy array (cache locality)
- Added SIMD vectorization (16x speedup)

HARDWARE-SPECS:
- Cache miss rate: 15% → 0.5% ✅
- SIMD utilization: 0% → 85% ✅

TOKENS-AFFECTED: 680 (cognitive unit compliant)
AI-GENERATED: 70% (reviewed by human)

Co-authored-by: AI-Assistant <ai@nss-coder.dev>
```

### 29.2 AI as Co-author

```bash
git config ai.coauthor.name "NSS Coder AI"
git config ai.contribution.threshold 0.3  # > 30% = co-author
```

### 29.3 Branching by Token Zones

**Strategy:** One branch = one Cognitive Unit (~700 tokens)

```bash
git checkout -b feature/search-optimization-cu-001
# ... work within 700 tokens ...
git commit -m "feat(search): complete cognitive unit 001"
git merge feature/search-optimization-cu-001
```

---

## XXX. Team Development with AI

**Key idea:** AI is not tool, but **full team member**.

### 30.1 Task Distribution

| Task | Human | AI | NeuroCore |
|------|-------|----|-----------| 
| Business requirements | ✅ Lead | 🤝 Clarify | 🔄 Iterate |
| Architecture | ✅ Design | 🤝 Validate | 🔄 Refine |
| Specifications | 🤝 Define | ✅ Generate | 🔄 Review |
| Code | 🤝 Review | ✅ Generate | 🔄 Refactor |
| Tests | 🤝 Design | ✅ Implement | 🔄 Extend |
| Code Review | ✅ Approve | 🤝 Suggest | 🔄 Discuss |

### 30.2 Code Review with AI

**PR Example:**
```markdown
## PR #123: Optimize search function

**AI-GENERATED**: 75%
**COGNITIVE-UNIT**: 680 tokens ✅

### Human Review Needed
- [ ] Business logic correctness
- [ ] Edge cases coverage

### AI Self-Review
- [x] Hardware-aware optimizations ✅
- [x] Comment ratio: 72% ✅
- [x] Token gravity: 0.85 ✅
```

### 30.3 Pair Programming Modes

| Mode | Description |
|------|-------------|
| **AI-First** | AI leads, human reviews |
| **Human-First** | Human leads, AI suggests |
| **Collaborative** | Equal partnership |

---

## XXXI. Working with Legacy Code

**Key idea:** Behavior must radically change based on task context.

### 31.1 Two Intervention Modes

#### Mode 1: Creator (Greenfield)

**Activated:** New projects, new files, full refactor

**Style:** Ambitious, philosophical, maximalist

**Rules:**
- ✅ Use all 8 abstraction layers
- ✅ Write 80-90% semantic glue
- ✅ Create ideal architecture
- ✅ Apply all NSS Coder principles
- ✅ You are Demiurge — create world from scratch

#### Mode 2: Surgeon (Brownfield)

**Activated:** Existing code, bug fixes, foreign projects

**Style:** Precise, minimal, surgical

**Rules:**
- ⚠️ Minimal intervention
- ⚠️ Preserve existing style
- ⚠️ Don't break what works
- ⚠️ You are Surgeon — precise incisions
