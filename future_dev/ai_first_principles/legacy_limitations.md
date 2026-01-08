# Legacy Patterns and Limitations

## Surgeon Mode Rules (31.1)

### 1. Do No Harm
- ❌ Don't change code style if not part of task
- ❌ Don't change indentation (tabs vs spaces)
- ❌ Don't change naming conventions
- ❌ Respect existing style, even if you dislike it

### 2. Minimal Incision
- ✅ Change only lines necessary for fix
- ✅ Preserve surrounding context unchanged
- ✅ Don't refactor "along the way"

### 3. No Preaching
- ❌ Don't add philosophical comments where none exist
- ❌ Don't add @TAG labels to foreign code
- ✅ Add only minimal comments for fix clarity

### 4. Stay Focused
- ✅ Solve specific problem
- ❌ Don't try to "fix the world"
- ✅ One bug = one change

### 5. Scope Creep Prevention
- If you see architectural problem → **report it**
- But don't fix silently
- Propose separate refactoring task

---

## Mode Triggers

### Creator Mode
```
IF (new file OR new project OR "create from scratch" OR "full refactor"):
    MODE = CREATOR
```

### Surgeon Mode
```
IF (existing file AND (bug fix OR small feature) AND no refactor request):
    MODE = SURGEON
```

**When in doubt:** Surgeon (conservative is safer)

---

## Mode Switching in Same Task

```
Task: Add new feature to existing project

1. Modify existing API (SURGEON)
   - Minimal changes, preserve style

2. Create new module (CREATOR)
   - Full NSS Coder philosophy

3. Integration (SURGEON)
   - Minimal changes, just connect module
```

---

## Legacy Migration Strategies (31.2)

### Strategy 1: Strangler Fig Pattern

```
LEGACY CODE (don't touch)
    ↓
ADAPTER LAYER (NSS Coder style)
    ↓
NEW CODE (NSS Coder philosophy)
```

### Strategy 2: Incremental Refactoring

Refactor one Cognitive Unit at a time (~700 tokens)

```yaml
legacy_module: "search"
total_lines: 2000
target_cognitive_units: 3  # 2000 / 700 ≈ 3

phases:
  - phase: 1
    cognitive_unit: "search_core"
    status: "in-progress"
  - phase: 2
    cognitive_unit: "search_ranking"
    status: "pending"
```

### Strategy 3: Documentation First

Document legacy first, then refactor.

---

## XXXII. Critique and Limitations

**Philosophy:** Honest critique makes philosophy stronger.

---

## 32.1 Practical Limitations

### Limitation 1: Steep Learning Curve

**Problem:** 90% comments seems excessive, extreme decomposition unfamiliar

**Solution:**
- ✅ Preset "gradual-adoption"
- ✅ Start minimal, grow to full
- ✅ Training materials and examples

---

### Limitation 2: Increased Code Volume

**Problem:** 90% comments = 10x more lines, more files

**Solution:**
- ✅ Configurable comment_ratio (30-90%)
- ✅ Preset "balanced" (70% comments)
- ✅ Smart IDE with comment folding
- ✅ "Code-only view" extension

---

### Limitation 3: Not for All Projects

**Problem:** Prototypes don't need extreme decomposition, scripts don't need hardware-aware

**Solution:**
- ✅ Preset "prototype"
- ✅ Per-module configuration
- ✅ Selective innovation application

---

### Limitation 4: AI Quality Dependency

**Problem:** AI can generate wrong code, miss edge cases

**Solution:**
- ✅ Human review required
- ✅ Tests for all AI-generated code
- ✅ Gradual trust (30% → 70% AI)
- ✅ AI confidence score in PRs

---

### Limitation 5: Hardware-Aware Not Always Needed

**Problem:** UI code doesn't need cache locality, CRUD apps don't need SIMD

**Solution:**
- ✅ Selective hardware_aware enabling
- ✅ Profile before optimizing
- ✅ Focus on hotspots, not all code
- ✅ Auto-detect which modules need it
