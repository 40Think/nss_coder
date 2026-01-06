# Automation Scripts — Documentation System

This directory contains Python scripts that automatically maintain project documentation.

## Philosophy

**Algorithmic First, AI Second**: We extract dependencies and structure algorithmically, then use AI to refine and explain.

## Overview of Scripts

### Core Analysis Tools

#### 1. `analyze_dependencies.py` ✅ COMPLETE
**Purpose**: Extract five layers of dependencies from Python files using AST analysis.

**Five Layers**:
1. **Code Layer**: imports, function calls, class hierarchy
2. **Configuration Layer**: YAML/JSON files, environment variables, CLI arguments
3. **Data Layer**: file reads/writes, data transformations
4. **External Layer**: API calls, subprocess commands
5. **Orchestration Layer**: execution order, conditional logic

**Usage**:
```bash
# Single file
python3 analyze_dependencies.py --target processing/01_splitter.py

# Directory
python3 analyze_dependencies.py --target-dir processing/

# Entire project
python3 analyze_dependencies.py --all

# Output to file
python3 analyze_dependencies.py --target file.py --output deps.json
```

**Output**: JSON file in `docs/memory/dependencies/`

---

#### 2. `chunk_documents.py` ✅ COMPLETE (v2.0)
**Purpose**: Hierarchical multi-layer chunking of documentation for RAG systems.

**3-Layer Architecture** (adapted from cheap_memory.py):
- **L0 (CLAUSES)**: Fine-grained sentence/paragraph level
- **L1 (SECTIONS)**: Header-based sections
- **L2 (DOCUMENTS)**: Full document embeddings

**Features**:
- Hierarchical chunking with parent-child relationships
- Code block preservation (keeps ``` blocks intact)
- Table preservation (markdown tables not split)
- Adaptive chunk sizing based on content complexity
- YAML frontmatter extraction
- Backward compatible via SemanticChunker wrapper

**Usage**:
```bash
# Hierarchical 3-layer mode (default)
python3 chunk_documents.py --input-dir docs/wiki --output-dir docs/memory/chunks

# Single file analysis
python3 chunk_documents.py --file docs/specs/MySpec.md

# Legacy single-layer mode
python3 chunk_documents.py --input-dir docs/ --legacy
```

**Output**: JSON files with hierarchical chunks in `docs/memory/chunks/`

---

#### 3. `validate_system.py` ✅ COMPLETE (NEW - TICKET #11)
**Purpose**: Adaptive multi-tier validation orchestrator.

**Three Tiers**:
- **Tier 1**: Algorithmic validation (validate_docs.py)
- **Tier 2**: External tools (ruff, mypy, markdownlint)
- **Tier 3**: AI validation (local_ai_verifier.py)

**Paranoia Levels** (1-5):
| Level | Name | Tiers | Use Case |
|-------|------|-------|----------|
| 1 | Minimal | [1] | < 50 files |
| 2 | Standard | [1,2] | 50-200 files |
| 3 | Thorough | [1,2,3] | 200-500 files |
| 4 | Paranoid | [1,2,3] | 500-1000 files |
| 5 | Maximum | [1,2,3] | > 1000 files |

**Usage**:
```bash
# Auto-detect level based on project size
python3 validate_system.py --auto

# Specific paranoia level
python3 validate_system.py --paranoia 2

# Maximum validation
python3 validate_system.py --paranoia 5
```

**Output**: 
- Reports in `output/validation/` (Markdown + JSON)
- Tickets in `docs/technical_debt/tickets/` (auto-deduplicated)

---

#### 4. `validate_docs.py` ✅ COMPLETE
**Purpose**: Detect documentation drift, broken links, and inconsistencies.

**Checks**:
- Broken links in markdown files
- Missing specifications for Python files
- Spec-code drift (functions in spec but not in code, and vice versa)
- YAML frontmatter presence

**Usage**:
```bash
# Run validation
python3 validate_docs.py --report docs/validation_report.md

# CI mode (exit with error if issues found)
python3 validate_docs.py --ci-mode
```

**Output**: Markdown report with categorized issues (errors, warnings, info)

---

### Search and Discovery Tools

#### 4. `search_by_tag.py` ✅ COMPLETE
**Purpose**: Search documentation using semantic tags (line-shift resistant).

**Tag Format**: `<!--TAG:identifier-->` ... `<!--/TAG:identifier-->`

**Usage**:
```bash
# List all available tags
python3 search_by_tag.py --list-tags

# Search for specific tag
python3 search_by_tag.py --tag component_splitter

# With context
python3 search_by_tag.py --tag feature_entropy --show-context

# Save to file
python3 search_by_tag.py --tag algo_calculation --output results.md
```

**Benefits**: Tags don't break when line numbers change, providing stable references.

---

#### 4a. `tag_validator.py` ✅ COMPLETE (NEW)
**Purpose**: Validate semantic tags against formal schema.

**Schema**: `docs/specs/tag_schema.yaml` defines:
- 3 dimensions: `component`, `type`, `feature`
- 6 validation rules
- Auto-tagging rules

**Validation Rules**:
1. max_tags_per_file (6)
2. primary_tag_must_close
3. valid_identifier
4. script_must_have_component
5. no_duplicate_tags
6. known_dimension_value

**Usage**:
```bash
# Validate single file
python3 tag_validator.py --file utils/dual_memory.py

# Validate directory
python3 tag_validator.py --directory docs/automation/

# Validate entire project
python3 tag_validator.py --all

# JSON output for integration
python3 tag_validator.py --directory utils/ --json
```

**Output**: Validation report with ERROR/WARNING/INFO severity levels.

---

#### 4b. `ast_auto_tagger.py` ✅ COMPLETE (NEW)
**Purpose**: Automatically generate semantic tags from Python code using AST analysis.

**Detection Methods**:
- **Path-based**: `docs/automation/` → `component:automation`
- **Import-based**: `import embed...` → `feature:embeddings`
- **Name-based**: `class TagValidator` → `feature:validation`
- **Content-based**: docstring analysis

**Usage**:
```bash
# Analyze single file (preview)
python3 ast_auto_tagger.py --file utils/dual_memory.py

# Analyze directory with report
python3 ast_auto_tagger.py --directory utils/ --report

# Apply suggested tags
python3 ast_auto_tagger.py --file new_script.py --apply

# Minimum confidence threshold
python3 ast_auto_tagger.py --file script.py --min-confidence 0.8

# JSON output
python3 ast_auto_tagger.py --directory docs/automation/ --json
```

**Output**: Suggested tags with confidence scores (0.0-1.0) and reasons.

---

#### 5. `search_dependencies.py` ✅ COMPLETE
**Purpose**: Search and visualize dependencies for Python files with caching and graph analysis.

**Features**:
- Shows all 5 dependency layers
- **LRU Cache** for JSON files (10x+ speedup)
- **Inverted Index** for O(1) reverse dependency lookup
- **NetworkX Graph** for transitive dependencies and cycle detection
- Text, Mermaid diagram, and JSON output formats

**Usage**:
```bash
# Search dependencies
python3 search_dependencies.py --file processing/01_splitter.py

# Include reverse dependencies (O(1) with inverted index)
python3 search_dependencies.py --file utils/llm_client.py --reverse

# Show cache statistics
python3 search_dependencies.py --file file.py --stats

# Rebuild inverted index
python3 search_dependencies.py --rebuild-index

# Find transitive dependencies (NetworkX BFS)
python3 search_dependencies.py --file orchestrator.py --transitive --depth 3

# Detect circular dependencies
python3 search_dependencies.py --cycles

# Show graph statistics (nodes, edges, density)
python3 search_dependencies.py --graph-stats

# Find shortest path between modules
python3 search_dependencies.py --path source.py target_module

# Output formats
python3 search_dependencies.py --file file.py --format mermaid
python3 search_dependencies.py --file file.py --format json
```

**Generated Files**:
- `docs/memory/dependencies/_reverse_index.json` - Inverted index for O(1) reverse lookups



#### 6. `semantic_search.py` ✅ COMPLETE
**Purpose**: Keyword-based semantic search across documentation.

**Note**: This is a simplified implementation. For production, integrate with vector databases (ChromaDB, FAISS) as described in `docs/RESEARCH_FINDINGS.md`.

**Usage**:
```bash
# Search documentation
python3 semantic_search.py --query "how does entropy linking work"

# Limit results
python3 semantic_search.py --query "LLM client" --top-k 5

# Show context
python3 semantic_search.py --query "pipeline stages" --show-context
```

---

### Context Engineering Tools

#### 7. `assemble_context.py` ✅ COMPLETE
**Purpose**: Automatically assemble focused context for AI agents.

**Strategies**:
- Task-based assembly (from description)
- File-based assembly (for specific file)
- Component-based assembly (for entire component)

**Usage**:
```bash
# Assemble context for a task
python3 assemble_context.py --task "modify entropy linker" --output docs/temp/context.md

# Assemble context for a file
python3 assemble_context.py --file processing/05_entropy_linker.py

# Assemble context for a component
python3 assemble_context.py --component analytics
```

**Output**: Single markdown file with:
- README files (navigation)
- Relevant specs
- Relevant wiki pages
- Code files
- Dependency maps
- Related tags

---

#### 8. `summarize_docs.py` ✅ COMPLETE
**Purpose**: Summarize long documentation files for context compression.

**Features**:
- Hierarchical structure extraction
- Section summarization
- Key points extraction
- Configurable max length

**Usage**:
```bash
# Summarize a file
python3 summarize_docs.py --input docs/wiki/02_Pipeline_Stages.md

# With max length
python3 summarize_docs.py --input docs/specs/01_Core_Pipeline_Spec.md --max-length 500

# Save to file
python3 summarize_docs.py --input file.md --output summary.md
```

---

### Testing and Validation

#### 9. `test_system.py` ✅ COMPLETE
**Purpose**: Test the entire documentation system.

**Tests**:
1. Dependency analysis functionality
2. Document chunking functionality
3. Documentation validation
4. Directory structure completeness
5. README file presence

**Usage**:
```bash
python3 test_system.py
```

**Output**: Test results with pass/fail for each component.

---

### Advanced Tools

#### 10. `generate_call_graph.py` ✅ COMPLETE
**Purpose**: Generate function call graphs and visualizations.

#### 11. `update_diagrams.py` ✅ COMPLETE
**Purpose**: Automatically update diagrams when code changes.

#### 12. `index_project.py` ✅ COMPLETE
**Purpose**: Build vector embeddings and knowledge graph for AI memory system.

### `generate_call_graph.py`
**Purpose**: Create visual function call graphs

**Features**:
- Module-level dependency graphs
- Function-level call graphs
- Interactive HTML visualizations
- Mermaid diagram generation

**Output**: `docs/diagrams/dependencies/`

**Usage**:
```bash
python docs/automation/generate_call_graph.py --module processing.01_splitter
python docs/automation/generate_call_graph.py --all-modules
```

### `update_diagrams.py`
**Purpose**: Regenerate all visual documentation

**Diagram Types**:
- Architecture (C4 model)
- Data flow (Mermaid)
- Dependencies (Graphviz)
- Algorithms (PlantUML)

**Output**: `docs/diagrams/`

**Usage**:
```bash
python docs/automation/update_diagrams.py --type architecture
python docs/automation/update_diagrams.py --all
```

### `validate_docs.py`
**Purpose**: Detect documentation drift

**Checks**:
- Spec vs code consistency
- Broken documentation links
- Diagram accuracy
- Missing documentation

**Output**: Drift report with actionable fixes

**Usage**:
```bash
python docs/automation/validate_docs.py --report docs/validation_report.md
python docs/automation/validate_docs.py --fix-links  # Auto-fix broken links
```

### `index_project.py`
**Purpose**: Build AI-queryable project index

**Features**:
- Generate code embeddings
- Build knowledge graph
- Create search indexes
- Extract semantic relationships

**Output**: `docs/memory/`

**Usage**:
```bash
python docs/automation/index_project.py --rebuild  # Full rebuild
python docs/automation/index_project.py --incremental  # Update only changed files
```

## Integration

### Git Hooks
Add to `.git/hooks/post-commit`:
```bash
#!/bin/bash
python docs/automation/analyze_dependencies.py --incremental
python docs/automation/update_diagrams.py --changed-only
```

### CI/CD
Add to `.github/workflows/documentation.yml`:
```yaml
name: Documentation
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate Documentation
        run: python docs/automation/validate_docs.py --ci-mode
      - name: Update Diagrams
        run: python docs/automation/update_diagrams.py --all
```

### Pre-commit Hook
Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: validate-docs
      name: Validate Documentation
      entry: python docs/automation/validate_docs.py
      language: system
      pass_filenames: false
```

## Development

### Adding New Automation
1. Create script in this directory
2. Follow naming convention: `verb_noun.py`
3. Add CLI interface with `argparse`
4. Update this README
5. Add to CI/CD if needed

### Dependencies
```bash
pip install ast pydeps snakefood networkx graphviz mermaid-py
```

## Maintenance Schedule

- **On every commit**: Incremental dependency analysis
- **Daily**: Full dependency analysis
- **Weekly**: Full diagram regeneration
- **Monthly**: Complete validation and drift report
