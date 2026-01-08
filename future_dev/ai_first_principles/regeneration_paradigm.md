# Regeneration vs Editing Paradigm

## Key Idea

> Code is not edited — code is regenerated.

---

## Traditional Approach (Patching)

```
Code v1.0
  ↓ [Manual editing]
Code v1.1 (patch)
  ↓ [Manual editing]
Code v1.2 (patch)
  ↓ [Technical debt accumulation]
Code v2.0 (refactoring)
```

**Problems:**
- Technical debt accumulation
- Documentation drift
- "Hacks" and "workarounds" pile up
- Code-spec divergence

---

## AI-First Approach (Regeneration)

```
Specification v1.0
  ↓ [AI generation]
Code v1.0
  
Specification v1.1 (updated)
  ↓ [AI regeneration from scratch]
Code v1.1 (completely new)
  
Specification v1.2 (updated)
  ↓ [AI regeneration from scratch]
Code v1.2 (completely new)
```

---

## Principles

### 1. Immutable Code Generation
- Code is immutable artifact
- Changes only in specifications
- Code fully recreated on each change

### 2. Human Doesn't Touch Code
- Works only with high-level specifications
- Doesn't edit generated code manually
- Doesn't make "quick fixes" in code

### 3. Full Regeneration
- On any requirement change
- Code generated anew from scratch
- No technical debt accumulation
- No drift between code and documentation

### 4. Code as Ephemeral Artifact
- Code can be deleted at any moment
- Code can be recreated from specifications
- Code doesn't store critical information
- All critical information in specifications

---

## Advantages

### ✅ No Documentation Drift
- Code always matches specification
- Impossible: "code does X, docs say Y"
- Synchronization guaranteed architecturally

### ✅ No Technical Debt
- Each regeneration is clean slate
- No accumulation of "crutches" and "hacks"
- Code always optimal for current requirements

### ✅ Simple Updates
- Changed specification → regenerated code
- No need to think "how to edit this"
- No fear of breaking existing code

### ✅ Evolution with Models
- New AI version → regenerate all code
- Code automatically improves
- New model capabilities utilized

---

## Exceptions

### ⚠️ When Manual Code Editing is Allowed

1. **Emergency hotfix in production**
   - Critical bug, no time for regeneration
   - Must be followed by spec update + regeneration

2. **Performance tuning**
   - Micro-optimizations based on profiling
   - Should be documented as hardware requirements

3. **Integration testing**
   - Temporary debug code
   - Must be removed before merge

---

## Workflow

```
1. Identify needed change
   ↓
2. Update specification (NOT code)
   ↓
3. Review updated specification
   ↓
4. Regenerate code from specification
   ↓
5. Verify regenerated code works
   ↓
6. Deploy
```

---

## Key Mindset Shift

> Stop thinking "how do I edit this code?"
> Start thinking "how do I update this specification?"
