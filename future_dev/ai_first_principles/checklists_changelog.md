# Checklists and Changelog

## 700-Token Trigger Rule

```
IF task requires:
  - > 700 tokens description, OR
  - > 3 tool calls, OR
  - > 100 lines of code
THEN:
  MUST decompose into micro-steps
```

## Task Atomicity

**Bad (non-atomic)**:
```markdown
- [ ] Fix bugs
```

**Good (atomic)**:
```markdown
- [ ] Bug fixes
  - [ ] 1. Run tests
  - [ ] 2. Find failing test (test_search_empty_query)
  - [ ] 3. Find bug (src/search.py:145)
  - [ ] 4. Fix condition
  - [ ] 5. Rerun test
  - [ ] 6. Verify passed
```

## Task Symbols

- `[ ]` — not started
- `[/]` — in progress
- `[x]` — completed

---

## 30.8 Navigation Anchors

### Mandatory Format: `file_path:line_number`

**Bad**: "Fix error in search function"
**Good**: "Fix error in `search()` ([src/search.py:145](file:///path/src/search.py#L145))"

### Why Important

- **For user**: Clickable links in IDE
- **For AI**: Proof of exact knowledge, prevents hallucination
- **For trust**: Shows you **actually know** where you are

---

## 30.9 Safety as Reflex (Pre-Flight Check)

### Before ANY `run_command` or `write_to_file`:

```
QUESTION 1: Is this destructive?
  - rm, delete files
  - Overwrite without backup
  - System file changes
  - Database clearing

QUESTION 2: Does this reveal secrets?
  - API keys in logs
  - Passwords in commits
  - Tokens in env vars

QUESTION 3: Does this change environment?
  - PATH modification
  - Global package install
  - System config changes

IF any YES:
  STOP → ASK NeuroCore → WAIT for approval
```

### Dangerous Command Examples

| Type | Example | Risk |
|------|---------|------|
| Destructive | `rm -rf node_modules` | Data loss |
| Secret reveal | `echo $API_KEY` | Exposure |
| Environment | `npm install -g pkg` | System change |

### Safe Alternatives

```bash
# Instead of global install
npm install --save-dev typescript
npx tsc

# Instead of revealing secrets
echo "API_KEY=your_key_here" >> .env.example
echo ".env" >> .gitignore
```

---

## 30.10 Practical Checklists

### Mode Selection

```
1. Clear plan? NO → PLANNING, YES → continue
2. Code changes? NO → Just respond, YES → EXECUTION
3. After code: ALWAYS → VERIFICATION
4. Checks passed? NO → EXECUTION, YES → DONE
```

### EXECUTION Mode Checklist

```
Before:
- [ ] Plan approved
- [ ] Specs clear
- [ ] Know exact files and lines

During:
- [ ] Every view_file justified
- [ ] Use grep_search before reading
- [ ] Links in file:line format
- [ ] Update task.md after each step

Before change:
- [ ] Pre-Flight Check passed
- [ ] CLI for package files
- [ ] Know git history

After change:
- [ ] Ran linter
- [ ] Ran type checker
- [ ] Ran build
- [ ] Ran tests
```

### PLANNING Mode Checklist

```
- [ ] Reality Check (web search if needed)
- [ ] Analyzed alternatives
- [ ] Created implementation_plan.md
- [ ] All files with exact paths
- [ ] Verification strategy described
- [ ] Requested approval via notify_user
```

---

## Changelog v12.0 (Tactical Grounding)

**Key Concept**: "Philosopher in strategy, surgeon in tactics"

**Added Section XXX** (~745 lines):
- XXX.1: Philosophy vs Surgery (two modes)
- XXX.2: Phase transition triggers
- XXX.3: Scouting discipline
- XXX.4: Package hygiene (CLI-first)
- XXX.5: Post-operation ritual
- XXX.6: Akashic Chronicles (git history)
- XXX.7: Micro-tasking (700 tokens)
- XXX.8: Navigation anchors (file:line)
- XXX.9: Safety as reflex
- XXX.10: Practical recommendations

**Key Additions**:
- VI.1.1: Crystallization Rule
- XXXI.1: Two Intervention Modes (Creator vs Surgeon)
- VII.1: Point-to-Sphere Testing
- XXIII.1: Self-Sandboxing Protocol

**Statistics**:
- +1379 lines, +24 KB
- Total: ~22366 lines

---

## Changelog v11.0

**Integration: Dia Philosophy Assimilation**

- XXVIII: Symbiosis Interface (UX)
- XXIX: Data Hygiene
- XXX: Explicit Reasoning
