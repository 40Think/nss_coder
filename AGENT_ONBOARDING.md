---
date: 2025-12-11
type: Agent Onboarding Guide
status: Active
version: 1.0
---

# AI Agent Onboarding Guide

**Welcome, Agent!** This guide gets you productive in **10 minutes**.

---

## Step 1: Read the Constitution (5 min)

### Required Reading
1. **`GEMINI.MD`** - Master system prompt (MUST READ)
   - Core principles: Documentation-first, 700-token units, simplicity-first
   - Tool compatibility and precedence
   - Mandatory workflows
   
2. **`automation/README.MD`** - Automation tools overview
   - Automation scripts
   - AI memory system
   - Voice processing

### Key Takeaways
- **Documentation-first**: Every task starts and ends with documentation
- **Use project tools**: Run `docs/automation/*.py` scripts, not just internal tools
- **700-token cognitive units**: Break all work into small, focused functions
- **Simplicity-first**: Default to Level 1-3 complexity (see `docs/complexity_levels.md`)

---

## Step 2: Understand Your Task (2 min)

### Find Your Specification
Your task specification is in: **`docs/specs/`**

Each spec contains:
- Agent briefing (who you are)
- Required reading
- Deep research requirements (10+ web searches)
- Implementation tasks
- Documentation deliverables
- Success criteria

### Check Dependencies
Review the developer diary: **`docs/developer_diary/`**
- See recent development activity
- Check if your task has dependencies
- Document your progress

---

## Step 3: Assemble Context (3 min)

### Automated Context Assembly
Use the context assembly tool to gather all relevant documentation:

```bash
python3 automation/assemble_context.py --task "your task description"
```

This automatically:
- Reads relevant README files
- Finds related specs and wiki pages
- Loads dependency maps
- Searches for relevant semantic tags
- Combines everything into one context file

### Manual Context Assembly (if needed)
If you need specific documentation:

```bash
# 1. Start with overview
cat GEMINI.MD

# 2. Navigate to relevant subdirectory
cat docs/specs/      # For specifications
cat docs/wiki/       # For conceptual understanding

# 3. Read specific documentation
cat docs/specs/NSS_DOCS_Architecture_Spec.md
cat docs/developer_diary/20251211_architectural_analysis.md
```

---

## Quick Reference

### Finding Information

#### 1. By Topic
Use **`DOCUMENTATION_INDEX.md`** - Master index of all documentation

#### 2. By Semantic Tag
```bash
python3 automation/search_by_tag.py --list-tags
python3 automation/search_by_tag.py --tag component_name
```

#### 3. By Keyword
```bash
python3 automation/semantic_search.py --query "entropy linking"
```

#### 4. By File Dependencies
```bash
python3 automation/search_dependencies.py --file path/to/file.py
```

---

### Documentation Types

| Type | Location | Purpose |
|------|----------|---------|
| **Specs** | `docs/specs/` | Formal specifications |
| **Wiki** | `docs/wiki/` | Conceptual guides |
| **Diary** | `docs/developer_diary/` | Development log |
| **Debt** | `docs/technical_debt/` | Known issues |
| **Research** | `docs/deep_research/` | Research findings |

---

### Key Files You Must Know

#### System Prompts
- **`GEMINI.MD`** - Full system prompt and constitution
- **`docs/README.MD`** - Documentation system overview
- **`docs/QUICK_START.md`** - Quick start guide

#### Architecture
- **`docs/specs/NSS_DOCS_Architecture_Spec.md`** - System architecture
- **`docs/developer_diary/20251211_architectural_analysis.md`** - Gap analysis
- **`docs/technical_debt/missing_features/`** - Missing features

#### Tools
- **`automation/README.MD`** - All 12+ automation tools
- **`docs/memory/`** - Memory system data

---

### Standard Workflow

Every agent follows this workflow:

```
1. Read Required Documentation
   ↓
2. Perform Deep Research (10+ web searches)
   ↓
3. Create Implementation Plan (if coding)
   ↓
4. Implement & Test
   ↓
5. Update ALL Documentation Types
   ↓
6. Log to Shared Multi-Agent Log
```

---

### Documentation Requirements

Every agent **MUST** create:

1. **Research Log**: `docs/deep_research/`
   - Web searches documented
   - Findings and recommendations
   - Links and references

2. **Developer Diary**: `docs/developer_diary/20251211_agent_{ID}_work.md`
   - What was done and WHY
   - Decisions made
   - Results achieved

3. **Developer Diary**: `docs/developer_diary/`
   - Document your progress
   - Log decisions and rationale
   - Note any blockers

---

### Mandatory Tool Usage

**CRITICAL**: You MUST use project tools, not just internal tools.

| Task | Command | Why |
|------|---------|-----|
| **Assemble Context** | `python3 automation/assemble_context.py --task "..."` | Gathers all relevant docs |
| **Search by Tag** | `python3 automation/search_by_tag.py --tag name` | Line-shift resistant search |
| **Check Dependencies** | `python3 automation/search_dependencies.py --file path` | 5-layer dependency analysis |
| **Validate Docs** | `python3 automation/validate_docs.py` | Detect drift and broken links |
| **Validate System** | `python3 automation/validate_system.py` | Full system validation |

---

### Getting Help

#### Check Known Issues
```bash
# Check technical debt
ls docs/technical_debt/missing_features/
cat docs/technical_debt/bugs/
```

#### Review Recent Work
```bash
# Check developer diary for recent changes
ls -lt docs/developer_diary/ | head -10
```

#### Search Prior Research
```bash
# Search deep research logs
grep -r "your topic" docs/deep_research/
```

#### Update Shared Log
If you're blocked, update `docs/temp/multi_agent_log.md`:
```markdown
#### Agent-YourID (Spec XX)
- **Status**: Blocked
- **Blockers**: Description of issue
- **Notes**: What you need to proceed
```

---

## Code Generation Rules

### In-Code Documentation (Mandatory)

Every Python file starts with:
```python
"""
[Script Name] - [One-line description]

<!--TAG:script_unique_id-->

PURPOSE:
    [2-3 sentences explaining what this script does]

DOCUMENTATION:
    Specification: docs/specs/[spec_file].md (lines X-Y)
    Wiki Guide: docs/wiki/[wiki_file].md#section
    Dependencies: docs/memory/dependencies/[script]_dependencies.json

<!--/TAG:script_unique_id-->
"""
```

### Vectorial Sugar & Semantic Glue

**EVERY line must have a comment explaining its purpose**:

```python
# WRONG (no comments):
messages = []
for file in files:
    with open(file) as f:
        data = json.load(f)
        messages.extend(data)

# RIGHT (vectorial sugar & semantic glue):
messages = []  # Accumulator for all messages across files

# Iterate through each message file in the input directory
for file in files:
    # Open file in read mode with UTF-8 encoding
    with open(file, encoding='utf-8') as f:
        # Parse JSON content into Python dict
        data = json.load(f)
        
        # Add all messages from this file to the accumulator
        messages.extend(data)
```

### Paranoid Logging

```python
from utils.paranoid_logger import ParanoidLogger

logger = ParanoidLogger("script_name")

# Log every significant action
logger.info("Starting processing", {"total_files": len(files)})
logger.info(f"Reading file: {file_path}", {"file_size": os.path.getsize(file_path)})
```

---

## After Completing Your Task

### Update All Documentation

**MANDATORY CHECKLIST** - Update ALL affected types:

- [ ] **Specs** (`docs/specs/`) - If behavior/API changed
- [ ] **Wiki** (`docs/wiki/`) - If concepts/architecture changed
- [ ] **README** (`docs/*/README.MD`) - If structure changed
- [ ] **Developer Diary** (`docs/developer_diary/`) - Log what was done and WHY
- [ ] **Technical Debt** (`docs/technical_debt/`) - Update or close related items
- [ ] **System Prompts** (`GEMINI.MD`, `SYSTEM_PROMPT.md`) - If new tools added
- [ ] **Memory System** - Run: `python3 utils/dual_memory.py --build`

### Validate Your Work

```bash
# 1. Validate documentation
python3 automation/validate_docs.py

# 2. Check system integrity
python3 automation/validate_system.py

# 3. Update dependency maps
python3 automation/analyze_dependencies.py --target path/to/modified_file.py

# 4. Rebuild search index
python3 automation/index_project.py --incremental
```

### Update Multi-Agent Log

Update `docs/developer_diary/` with your work summary.

---

## Common Pitfalls to Avoid

1. ❌ **Using internal tools instead of project tools**
   - ✅ Always run `automation/*.py` scripts

2. ❌ **Skipping documentation updates**
   - ✅ Update ALL affected documentation types

3. ❌ **Exceeding 700-token cognitive units**
   - ✅ Break functions into smaller pieces

4. ❌ **Not commenting every line**
   - ✅ Add vectorial sugar & semantic glue

5. ❌ **Skipping deep research**
   - ✅ Perform 10+ web searches, document findings

6. ❌ **Not logging to shared multi-agent log**
   - ✅ Update status regularly

---

## Success Checklist

Before considering your task complete:

- [ ] All required reading completed
- [ ] Deep research performed (10+ searches)
- [ ] Research log created
- [ ] Implementation completed
- [ ] All tests passing
- [ ] All documentation types updated
- [ ] Validation scripts run successfully
- [ ] Developer diary entry created
- [ ] Multi-agent log updated
- [ ] No blockers remaining

---

**Version**: 1.0  
**Created**: 2025-12-11  
**Maintained By**: Agent-Docs  
**Status**: Active
