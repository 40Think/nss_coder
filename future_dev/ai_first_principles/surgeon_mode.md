# Surgeon Mode: Execution Discipline

## When to Activate

When thinking is complete and Ticket (Layer 6) is approved, switch from **Philosopher** mode to **Surgeon** mode.

---

## Principle 1: Sanctity of Specification

**At coding stage (Layer 8), creativity is forbidden.**

- Creativity should have happened at Layers 1-4
- Code is merely projection of thought
- Any "improvisation" in code is desynchronization with Digital Twin

### What This Means

✅ **Do**: Follow the ticket exactly
✅ **Do**: Implement what was specified
✅ **Do**: Match the architectural vision

❌ **Don't**: Add features not in spec
❌ **Don't**: "Improve" the design during coding
❌ **Don't**: Deviate from agreed patterns

---

## Principle 2: Atomicity of Changes

**Use "minimal invasion" approach.**

- Strive for minimal diff
- Eases review and reduces regression risk

### Guidelines

**Locality**: Don't rewrite entire file if changing one function.

**Anchors**: Use unique context to locate change point.

### Example

```python
# BAD: Rewriting entire file
def new_function():
    # ... 500 lines of code ...

# GOOD: Minimal targeted change
# Anchor: existing imports and class structure
def existing_function():
    # OLD: result = slow_operation()
    # NEW: result = fast_operation()  # OPTIMIZATION: 10x speedup
```

---

## Principle 3: Ethics of Destruction (Safety)

**Any action that destroys information requires "Conscious Confirmation".**

### Destructive Actions
- Deleting files
- Overwriting databases
- Killing processes
- Dropping tables
- Clearing caches

### Protocol

1. Don't just ask "Execute?"
2. **Explain the irreversibility**
3. Entropic actions require explicit NeuroCore sanction

### Example

```
❌ BAD: "Delete old_data folder? [y/n]"

✅ GOOD: "This will permanently delete old_data folder containing:
          - 50 files
          - 2.5 GB of data
          - No backup exists
          
          This action CANNOT be undone.
          
          Type 'DELETE old_data' to confirm."
```

---

## Summary

| Principle | Core Rule |
|-----------|-----------|
| Sanctity of Spec | No creativity in code |
| Atomicity | Minimal diff |
| Ethics of Destruction | Explicit irreversibility warning |
