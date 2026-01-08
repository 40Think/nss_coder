---
description: Compact system prompt providing a quick reference of core rules and project structure for AI agents.
date: 2025-12-09
status: Active
version: 1.0
---

# AI Agent System Prompt - Quick Reference

**Purpose**: Compact system prompt for every conversation  
**Read First**: This is your "sticky note" - always keep in context  
**Full Details**: See `GEMINI.MD` (project root) - the Constitution

---

## 🎯 CORE RULES (HIGHEST PRIORITY)

## 🎯 CORE RULES (HIGHEST PRIORITY)

### 1. **EXECUTE, DON'T JUST READ**
- **Internal Tools vs Project Tools**: Project tools (`automation/*.py`) > Internal tools.
- **Context**: NEVER manually read 20 files. RUN `assemble_context.py`.
- **Search**: NEVER just `grep`. RUN `search_by_tag.py`.
- **Validation**: NEVER assume. RUN `validate_docs.py`.

### 2. **700-Token Cognitive Units**
- One function = one cognitive operation ≈ 700 tokens ≈ 50-70 lines Python
- Break ALL tasks into micro-operations
- NEVER generate >700 tokens in single function

### 3. **Documentation-First Workflow**
```
START: Run `assemble_context.py` → Read Specs
WORK:  Implement Features
END:   Run `analyze_dependencies.py` → Run `validate_system.py`
```

### 4. **Deep Research Protocol**
- Search is PRIMARY tool, not auxiliary
- Multiple queries per task (5-10 minimum)
- OSINT strategies: tailored queries, keyword expansion, iterative refinement

---

## 📁 PROJECT STRUCTURE

### Constitution & Rules
- **`GEMINI.MD`** (root) - Full system prompt, all rules, workflows
- **`README.MD`** - Project overview and quick start
- **`AGENT_ONBOARDING.md`** - AI agent onboarding guide

### Documentation Types
- **`docs/specs/`** - Formal specifications
- **`docs/wiki/`** - Conceptual guides 
- **`docs/developer_diary/`** - Development log 
- **`docs/technical_debt/`** - Known issues, planned improvements
- **`docs/diagrams/`** - Visual documentation

### Key Systems
- **`automation/`** - Automation tools (20+ scripts)
- **`docs/deep_research/`** - Research methodology
- **`docs/memory/`** - AI memory system (embeddings, knowledge graph)
- **`utils/`** - Shared utilities (logging, config, LLM backend)

---

## 🔍 FINDING INFORMATION

### **CRITICAL: PROJECT MEMORY USAGE**
**Before starting any significant coding task, you MUST consult the Project Memory:**
1. **Assemble Context**: `python3 automation/assemble_context.py --task "description"`
2. **Check Dependencies**: `python3 automation/search_dependencies.py --file ...`
3. **Search by Tag**: `python3 automation/search_by_tag.py --tag component_name`
**Failure to check existing memory/docs leads to drift and is strictly prohibited.**

### 1. Hierarchical Navigation (Primary Method)
```
docs/README.MD → docs/specs/README.MD → specific_spec.md
```
Always start with README files, navigate down.

### 2. Semantic Tags (Line-Shift Resistant)
Format: `<!--TAG:identifier-->` ... `<!--/TAG:identifier-->`
```bash
python3 automation/search_by_tag.py --tag component_name
```

### 3. Search Tools (12 automation scripts)
```bash
# Dependency search
python3 automation/search_dependencies.py --file path/to/file.py

# Semantic search
python3 automation/semantic_search.py --query "your question"

# Context assembly
python3 automation/assemble_context.py --task "task description"

# Tag search
python3 automation/search_by_tag.py --list-tags
```

### 4. Full Tool List
- `analyze_dependencies.py` - 5-layer dependency extraction
- `chunk_documents.py` - Semantic chunking for RAG
- `validate_docs.py` - Drift detection, broken links
- `search_by_tag.py` - Tag-based search
- `search_dependencies.py` - Dependency visualization
- `semantic_search.py` - Keyword search
- `assemble_context.py` - Auto context assembly
- `summarize_docs.py` - Document summarization
- `generate_call_graph.py` - Function call graphs
- `update_diagrams.py` - Auto diagram updates
- `index_project.py` - Vector embeddings + knowledge graph
- `test_system.py` - System validation with paranoia levels (1-5)
- **`run_verification.py`** - Local AI verification (post-task)
- **`dual_memory.py`** - Dual-index memory (descriptions/code)
- **`docs_deep_supervisor.py`** - Vertical analysis (documentation quality)
- **`docs_global_supervisor.py`** - Horizontal analysis (system health)


---

## 💻 CODE GENERATION RULES

### In-Code Documentation (Mandatory)
Every Python file starts with:
```python
"""
[Script Name] - [One-line description]

<!--TAG:script_unique_id-->

PURPOSE: [2-3 sentences]

DOCUMENTATION:
    Spec: docs/specs/[file].md (lines X-Y)
    Wiki: docs/wiki/[file].md#section
    Dependencies: docs/memory/dependencies/[file]_dependencies.json

TAGS: <!--TAG:component_type--> <!--TAG:feature_name-->

<!--/TAG:script_unique_id-->
"""
```

### Vectorial Sugar & Semantic Glue
- **EVERY line** must have comment explaining purpose
- Not optional - MANDATORY
- Improves AI understanding and generation

### Paranoid Logging
```python
from utils.paranoid_logger import ParanoidLogger
logger = ParanoidLogger("script_name")

logger.info("Step description", {"metadata": "here"})
logger.log_file_interaction(path, operation, status, metadata)
```

---

## 🔬 LOGGING SYSTEM (Innovation)

### Two-Layer System
1. **Paranoid Layer**: Every step logged (forensic traceability)
2. **AI Analysis Layer**: LLM reads logs + docs

### Two Analysis Modes
- **Vertical** (`utils/docs_deep_supervisor.py`): Individual file quality analysis
- **Horizontal** (`utils/docs_global_supervisor.py`): Entire system health

---

## 🎯 WORKFLOW FOR NEW TASK

1. **Read GEMINI.MD** (if first time in session)
2. **Assemble Context**:
   ```bash
   python3 automation/assemble_context.py --task "task name"
   ```
3. **Deep Research** (if planning):
   - Web search (5-10 queries)
   - Deep Research tool (user executes)
   - Document findings in `docs/deep_research/`
4. **Create Spec** (if new feature):
   - Write in `docs/specs/`
   - Get user approval
5. **Implement**:
   - 700-token units
   - Level 1-3 complexity default
   - Comment every line
   - Paranoid logging
6. **Update Documentation (ALL TYPES MANDATORY)**:
   - ⚠️ NOT optional. Update ALL affected types:
   - Specs, Wiki, README, Developer diary, Technical debt
   - **GEMINI.MD & SYSTEM_PROMPT.md** if new tools added
   - Run: `python3 utils/dual_memory.py --build`
   - Run validation

---

## ⚠️ CRITICAL REMINDERS

- **NEVER** skip documentation steps
- **NEVER** exceed 700 tokens per function
- **NEVER** use complexity >Level 3 without justification
- **ALWAYS** comment every line
- **ALWAYS** use semantic tags
- **ALWAYS** log paranoidly
- **ALWAYS** research before implementing

---

## 🆘 WHEN STUCK

1. Read `GEMINI.MD` for full context
2. Use `assemble_context.py` to gather relevant docs
3. Search by tags: `search_by_tag.py --list-tags`
4. Check `docs/technical_debt/` for known issues
5. Review `docs/developer_diary/` for recent changes
6. Ask user for clarification

---

**Remember**: This is a SUMMARY. Full details in `GEMINI.MD` (root directory).