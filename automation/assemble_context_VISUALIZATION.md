# assemble_context.py - Workflow Visualization

**Script**: `docs/automation/assemble_context.py`  
**Purpose**: Assembles relevant context from project files for AI agent prompts  
**Date**: 2025-12-12

---

## 📊 Mermaid Diagram

**File**: [`assemble_context_workflow.mmd`](./assemble_context_workflow.mmd)

The Mermaid flowchart visualizes the complete workflow of the context assembler, including:

### 5 Dependency Layers (INPUTS)

1. **Code Dependencies** 🔵
   - `docs.utils.docs_logger` (DocsLogger)
   - `docs.utils.docs_dual_memory` (DocsDualMemory)
   - `sentence_transformers` (optional)

2. **Configuration** ⚙️
   - CLI arguments: `--task`, `--file`, `--component`
   - Project root path

3. **Data Sources** 📚
   - `docs/specs/*.md` - Specifications
   - `docs/wiki/*.md` - Wiki guides
   - `processing/*.py`, `utils/*.py` - Code files
   - `docs/README.MD` - Navigation hub
   - `docs/memory/dependencies/*_dependencies.json` - Dependency maps

4. **External Services** 🌐
   - Embedding model: `all-MiniLM-L6-v2`

5. **Orchestration** 🎯
   - `__main__` entry point

### Core Logic Flow

```
CLI Input → Router → [Task/File/Component Assembly]
                           ↓
                    Semantic Search ⚡ OR Keyword Search 🔍
                           ↓
                    Add Files with Metadata
                           ↓
                    Find Dependency Maps
                           ↓
                    Generate Project Tree
                           ↓
                    Collect Assembly Stats
                           ↓
                    Generate Output File
```

### Three Assembly Modes

1. **Task-Based** (`--task "description"`)
   - Extracts keywords with RU/EN synonyms
   - Semantic search via dual_memory (if available)
   - Keyword-based ranking (fallback)
   - Ranks specs, wiki, code by relevance

2. **File-Based** (`--file path/to/file.py`)
   - Adds target file + directory README
   - Finds matching spec
   - Extracts semantic tags
   - Adds dependency map

3. **Component-Based** (`--component name`)
   - Searches code directories for matching files
   - Ranks specs/wiki mentioning component
   - Sets keywords to component name

### Metadata Tracking

**FileMetadata** (per file):
- `path`, `reason`, `relevance_score`
- `matched_keywords`, `content_type`
- `file_size_kb`, `last_modified`
- `tags`, `line_range`

**ContextPackage** (assembly result):
- File lists by type (readme, spec, wiki, code, dependency)
- `file_metadata` dict
- `assembly_stats` (time, strategy, keywords)
- `project_tree` structure

### OUTPUTS

- **`docs/temp/context.md`** - Assembled context with metadata
- **`docs/logs/assemble_context/`** - Execution logs
- **Console** - Summary statistics

---

## 🎨 Metaphorical Visualization

![Context Assembly Factory](./assemble_context_metaphor.png)

### Visual Metaphor: "Context Assembly Factory"

The visualization represents the context assembly process as a **futuristic factory** with three main zones:

#### LEFT - INPUT ZONE (5 Layers)
- **Code Dependencies**: Glowing blue power cores (DocsLogger, DocsDualMemory)
- **Configuration**: Control panel with mode switches
- **Data Sources**: Organized stacks of glowing documents (specs, wiki, code)
- **External Services**: Neural network representing embedding model
- **Orchestration**: Main control tower (`__main__`)

#### CENTER - ASSEMBLY PROCESS
- **Semantic Search Engine** ⚡: Glowing sphere with vector arrows connecting concepts
- **Keyword Matcher** 🔍: Traditional filing cabinet for fallback mode
- **Metadata Enrichment Station**: Files being tagged with scores and keywords
- **Ranking Sorter**: Mechanical sorter organizing by relevance
- **Tag Extractor**: Robotic arms extracting semantic tags

#### RIGHT - OUTPUT ZONE
- **Golden context.md**: Assembled knowledge file emerging from assembly line
- **Mechanical Scribe**: Writing logs (DocsLogger)
- **Console Display**: Showing statistics

### Key Visual Elements

| Element | Metaphor | Represents |
|---------|----------|------------|
| Glowing data cards | Files with metadata labels | FileMetadata objects |
| Vector arrows | Semantic connections | Embedding similarity |
| Index cards | Traditional matching | Keyword search |
| Connection diagrams | Dependency maps | File relationships |
| Holographic tree | Project structure | Directory hierarchy |

---

## 🔄 Workflow Summary

```
1. Initialize ContextAssembler
   ↓
2. Try to load dual_memory (semantic search)
   ↓
3. Route by input type (task/file/component)
   ↓
4. Search strategy selection:
   - Semantic: Use embeddings + cosine similarity
   - Keyword: Rank files by keyword matches
   ↓
5. Add files with rich metadata:
   - Why included (reason)
   - Relevance score (0.0-1.0)
   - Matched keywords
   - Content type
   - File stats (size, modified date)
   - Semantic tags
   ↓
6. Find dependency maps for code files
   ↓
7. Generate project tree structure
   ↓
8. Collect assembly statistics
   ↓
9. Generate context.md with:
   - Header (task, strategy, stats)
   - Project tree
   - Files sorted by score
   - File contents with metadata
   - Tags summary
   ↓
10. Write to docs/temp/context.md
```

---

## 📈 Performance Characteristics

- **Semantic Search**: ~15 results, embedding-based ranking
- **Keyword Search**: ~5 specs + 3 wiki + 5 code files
- **Assembly Time**: Typically 0.5-2 seconds
- **Output Size**: 8000 chars per file (truncated if larger)
- **Metadata Overhead**: ~200 bytes per file

---

## 🔗 Related Documentation

- **Spec**: `docs/technical_debt/tickets_2025_12_11/TICKET_02_assemble_context.md`
- **Pseudocode**: [`assemble_context.pseudo.md`](./assemble_context.pseudo.md)
- **Audit Report**: `docs/developer_diary/20251212_assemble_context_audit_fixes.md`
- **Source Code**: [`assemble_context.py`](./assemble_context.py)

---

**Visualization Style**: Cyberpunk technical blueprint with neon blues, purples, and golds. Isometric perspective mixing futuristic holographic elements with traditional mechanical assembly metaphors.
