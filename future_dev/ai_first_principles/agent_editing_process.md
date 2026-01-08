# Agent Editing Process

## Internal Confirmation Process

**Before dangerous action:**

```
1. PAUSE
   - Don't act impulsively
   - Even if "you know what's needed"

2. ANALYZE
   - What exactly will happen?
   - What data may be lost?
   - Is there backup?
   - Can it be rolled back?

3. ASK (yourself)
   - Is there a way back?
   - Am I 100% sure?
   - What's the worst case?

4. DECIDE
   IF 100% sure AND way back exists:
     → Continue
   ELSE:
     → Ask user
```

### Example: Git Reset

```
Task: Roll back last 5 commits

PAUSE: Stop, destructive git command

ANALYZE:
- What will we lose? → 5 commits with changes
- Backup exists? → Only if pushed
- git log → Commits NOT pushed

ASK:
- Way back? → NO (commits will be lost)
- 100% sure? → NO (don't know context)

DECIDE: DANGEROUS

ACTION: Ask user:
"I see need to roll back 5 commits. They're not pushed,
so will be lost forever. Are you sure?
Maybe create backup branch first?"
```

---

## 23.2 Problem of Agent Editing

**Risks when agents edit code:**
- Loss of semantic glue
- Drift from specification
- Accumulation of inconsistencies
- Degradation of comment quality

---

## 23.2 Formalized Editing Rules

### Rule 1: Preserve Semantic Glue

```python
# ❌ WRONG: Agent removes comments
def search(query):
    return vector_index.search(query)

# ✅ RIGHT: Agent preserves semantic glue
def search(query):
    # STEP 1: Validate input
    # WHY: Prevent errors downstream
    if not query:
        return []
    
    # STEP 2: Perform vector search
    # WHY: Semantic understanding of query
    return vector_index.search(query)
```

**Requirement:** When editing, agent MUST preserve or improve comments, not delete them.

---

### Rule 2: Update Related Artifacts

When changing code, agent must update:

1. **Ticket at file start**
   - Add change description
   - Update modification date
   - Specify change reason

2. **Module specification**
   - Update requirements if changed
   - Add new edge cases
   - Update usage examples

3. **Related files**
   - Update imports if interfaces changed
   - Update calls if signatures changed
   - Update tests if behavior changed

---

### Rule 3: Validate Before Saving

```python
class AgentEditValidator:
    def validate_edit(self, original_file, modified_file):
        checks = [
            self.check_semantic_glue_preserved(),
            self.check_ticket_updated(),
            self.check_specification_sync(),
            self.check_tests_updated(),
            self.check_token_connectivity(),
            self.check_no_contradictions(),
        ]
        
        for check in checks:
            if not check.passed:
                raise ValidationError(check.message)
        
        return True
    
    def check_semantic_glue_preserved(self):
        """Check that semantic glue not removed"""
        original_comments = count_comments(self.original_file)
        modified_comments = count_comments(self.modified_file)
        
        if modified_comments < original_comments * 0.8:
            return CheckResult(
                passed=False,
                message="Too many comments removed. Preserve."
            )
        return CheckResult(passed=True)
```

---

### Rule 4: Minimal Changes

```python
# ❌ WRONG: Rewriting entire file
def search(q, k):  # Changed variable names
    r = idx.search(q, k)  # Shortened names
    return r

# ✅ RIGHT: Point change
def semantic_search(query: str, top_k: int = 10, timeout: int = 30):  # Added timeout
    # STEP 1: Validate input
    if not query:
        return []
    
    # STEP 2: Perform search with timeout  # Updated comment
    results = vector_index.search(query, top_k, timeout=timeout)  # Added parameter
    
    return results
```

---

### Rule 5: Document Changes

```markdown
## MODIFICATION LOG

### Change #1: Added timeout parameter
**Date:** 2025-11-29
**Agent:** Agent-007
**Type:** Enhancement
**Reason:** Prevent hanging on slow queries
**Impact:** 
- Changed function signature
- Updated 3 call sites
- Added 2 new tests
**Related:** Issue #123
**Reviewed:** Yes
```

---

## 23.3 Editing Process

### 7-Step Standard Process

**Step 1: Task Analysis**
- Which file to change?
- Which lines affected?
- Which artifacts to update?
- Which tests to add?

**Step 2: Context Loading**
```python
context = memory_system.get_context(
    file="search_engine.py",
    task=task,
    include_related=True
)
```

**Step 3: Plan Changes**
```python
plan = {
    "files_to_modify": ["search_engine.py"],
    "files_to_update": ["search_spec.md", "test_search.py"],
    "changes": [
        {"file": "...", "line": 42, "action": "add_parameter"}
    ],
    "validation_checks": ["semantic_glue", "ticket", "tests"]
}
```

**Step 4: Execute Changes**
```python
for change in plan.changes:
    apply_change(change)
    validate_change(change)
```

**Step 5: Validate**
```python
validator = AgentEditValidator()
validator.validate_edit(original_file, modified_file)
```

**Step 6: Document**
```python
add_modification_log(file, change, agent_id, date)
```

**Step 7: Save**
```python
save_file(modified_file)
commit_changes(message="Add timeout parameter")
```

---

## 23.4 Special Rules for Micro-Files

**For micro-operations (20-50 lines):**

**Rule: Prefer Regeneration**

If change affects >30% of file:
- Don't edit
- Regenerate file from scratch using updated specification
