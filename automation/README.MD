# Automation Scripts — NSS Coder Toolkit

<!--TAG:docs_automation_master_readme-->

This directory contains the core automation engine for the NSS Coder project — **103 files** across documentation, analysis, voice processing, and visualization. These scripts handle everything from 5-layer dependency extraction and AI context assembly to voice-controlled development workflows.

**Last Updated**: 2026-01-06

---

## 🧠 Philosophy: Algorithmic-First, AI-Second

We prioritize rigorous **algorithmic analysis** (AST parsing, dependency graphs, semantic tagging) to provide high-fidelity context, which then empowers AI agents to perform complex tasks with maximum reliability. Every Python script has a corresponding `.pseudo.md` file documenting its logic in human-readable pseudocode.

---

## � Directory Structure

```
automation/
├── *.py                     # 20+ Python automation scripts
├── *.pseudo.md              # Pseudocode specifications (1:1 with .py)
├── *.mmd                    # Mermaid workflow diagrams
├── *_VISUALIZATION.md       # Visualization documentation
├── *.png                    # Generated architecture diagrams
├── backup/                  # Backup files
├── neuro_semantics/         # Advanced NLP/semantics modules (178 files)
├── recordings/              # Voice session recordings
├── sessions/                # Voice session data
├── static/                  # Web assets (CSS/JS)
└── templates/               # Jinja2 HTML templates
```

---

## 🛠️ Core Analysis Tools

### 1. `analyze_dependencies.py` — 5-Layer Dependency Extraction
**Purpose**: Extracts comprehensive dependencies from Python files using AST analysis.

**Five Dependency Layers**:
| Layer | Description |
|-------|-------------|
| **Code** | imports, function calls, class inheritance |
| **Configuration** | YAML/JSON files, environment variables, CLI args |
| **Data** | file I/O operations, data transformations |
| **External** | API calls, subprocess commands |
| **Orchestration** | execution order, conditional logic, entry points |

**Usage**:
```bash
python3 automation/analyze_dependencies.py --target file.py
python3 automation/analyze_dependencies.py --target-dir processing/
python3 automation/analyze_dependencies.py --all --output deps.json
```

**Related Files**:
- [`analyze_dependencies.pseudo.md`](analyze_dependencies.pseudo.md) — Algorithm specification
- [`analyze_dependencies_workflow.mmd`](analyze_dependencies_workflow.mmd) — Mermaid diagram
- [`analyze_dependencies_visual.png`](analyze_dependencies_visual.png) — Visual architecture

---

### 2. `chunk_documents.py` — Hierarchical Document Chunking
**Purpose**: 3-layer hierarchical chunking for RAG (Retrieval-Augmented Generation) systems.

**Three-Layer Architecture**:
| Layer | Name | Description |
|-------|------|-------------|
| L0 | CLAUSES | Fine-grained sentence/paragraph chunks |
| L1 | SECTIONS | Header-based logical sections |
| L2 | DOCUMENTS | Full document with metadata |

**Features**:
- Code block preservation (keeps ``` intact)
- Table preservation (markdown tables not split)
- Adaptive chunk sizing based on content complexity
- YAML frontmatter extraction
- Token-based sizing with Qwen3 tokenizer

**Usage**:
```bash
python3 automation/chunk_documents.py --input-dir docs/wiki --output-dir docs/memory/chunks
python3 automation/chunk_documents.py --file docs/specs/MySpec.md
python3 automation/chunk_documents.py --input-dir docs/ --legacy  # Single-layer mode
```

**Related Files**:
- [`chunk_documents.pseudo.md`](chunk_documents.pseudo.md)
- [`chunk_documents.mmd`](chunk_documents.mmd)
- [`chunk_documents_visualization.png`](chunk_documents_visualization.png)

---

### 3. `assemble_context.py` — AI Context Assembly
**Purpose**: Automatically assembles focused context packages for AI agents.

**Assembly Strategies**:
- **Task-based**: From natural language description
- **File-based**: For specific file modification
- **Component-based**: For entire component/module

**Output Includes**:
- README files for navigation
- Relevant specifications
- Related wiki pages
- Code files with dependencies
- Semantic tag matches

**Usage**:
```bash
python3 automation/assemble_context.py --task "modify entropy linker"
python3 automation/assemble_context.py --file processing/05_linker.py
python3 automation/assemble_context.py --component analytics
```

**Related Files**:
- [`assemble_context.pseudo.md`](assemble_context.pseudo.md)
- [`assemble_context_workflow.mmd`](assemble_context_workflow.mmd)
- [`assemble_context_metaphor.png`](assemble_context_metaphor.png)

---

### 4. `search_dependencies.py` — Dependency Search & Visualization
**Purpose**: Search and visualize dependencies with caching, inverted index, and graph analysis.

**Features**:
- LRU cache for 10x+ speedup
- Inverted index for O(1) reverse lookup
- NetworkX graph for transitive deps & cycle detection
- Text, Mermaid, and JSON output formats

**Usage**:
```bash
python3 automation/search_dependencies.py --file utils/llm_client.py
python3 automation/search_dependencies.py --file file.py --reverse
python3 automation/search_dependencies.py --cycles
python3 automation/search_dependencies.py --path source.py target_module
```

**Related Files**:
- [`search_dependencies.pseudo.md`](search_dependencies.pseudo.md)
- [`search_dependencies.mmd`](search_dependencies.mmd)
- [`search_dependencies_visualization.png`](search_dependencies_visualization.png)

---

### 5. `semantic_search.py` — Documentation Search
**Purpose**: Keyword and semantic search across all documentation.

**Features**:
- BM25-style ranking
- Synonym expansion (EN/RU)
- Context snippet extraction
- Configurable result limits

**Usage**:
```bash
python3 automation/semantic_search.py --query "how does entropy linking work"
python3 automation/semantic_search.py --query "LLM client" --top-k 5
python3 automation/semantic_search.py --query "pipeline stages" --show-context
```

**Related Files**:
- [`semantic_search.pseudo.md`](semantic_search.pseudo.md)
- [`semantic_search.mmd`](semantic_search.mmd)
- [`semantic_search_architecture.png`](semantic_search_architecture.png)

---

### 6. `search_by_tag.py` — Semantic Tag Search
**Purpose**: Search documentation using stable semantic tags (line-shift resistant).

**Tag Format**: `<!--TAG:identifier-->` ... `<!--/TAG:identifier-->`

**Usage**:
```bash
python3 automation/search_by_tag.py --list-tags
python3 automation/search_by_tag.py --tag component_splitter
python3 automation/search_by_tag.py --tag feature_entropy --show-context
```

**Related Files**:
- [`search_by_tag.pseudo.md`](search_by_tag.pseudo.md)
- [`search_by_tag_flow.mmd`](search_by_tag_flow.mmd)
- [`search_by_tag_visualization.png`](search_by_tag_visualization.png)

---

### 7. `tag_validator.py` — Semantic Tag Validation
**Purpose**: Validate semantic tags against formal schema (`docs/specs/tag_schema.yaml`).

**Validation Rules**:
1. `max_tags_per_file` (6)
2. `primary_tag_must_close`
3. `valid_identifier`
4. `script_must_have_component`
5. `no_duplicate_tags`
6. `known_dimension_value`

**Usage**:
```bash
python3 automation/tag_validator.py --file utils/dual_memory.py
python3 automation/tag_validator.py --directory docs/automation/
python3 automation/tag_validator.py --all --json
```

**Related Files**:
- [`tag_validator.pseudo.md`](tag_validator.pseudo.md)
- [`tag_validator.mmd`](tag_validator.mmd)
- [`tag_validator_visualization.png`](tag_validator_visualization.png)

---

### 8. `ast_auto_tagger.py` — Automatic Tag Generation
**Purpose**: Generate semantic tags from Python code using AST analysis.

**Detection Methods**:
- **Path-based**: `docs/automation/` → `component:automation`
- **Import-based**: `import embed...` → `feature:embeddings`
- **Name-based**: `class TagValidator` → `feature:validation`
- **Content-based**: Docstring analysis

**Usage**:
```bash
python3 automation/ast_auto_tagger.py --file utils/dual_memory.py
python3 automation/ast_auto_tagger.py --directory utils/ --report
python3 automation/ast_auto_tagger.py --file new_script.py --apply
```

**Related Files**:
- [`ast_auto_tagger.pseudo.md`](ast_auto_tagger.pseudo.md)
- [`ast_auto_tagger.mmd`](ast_auto_tagger.mmd)
- [`ast_auto_tagger_architecture.md`](ast_auto_tagger_architecture.md)
- [`ast_auto_tagger_workflow.png`](ast_auto_tagger_workflow.png)

---

### 9. `summarize_docs.py` — Document Summarization
**Purpose**: Multi-level summarization with hierarchical chunking integration.

**Detail Levels**:
| Level | Output |
|-------|--------|
| `tldr` | 1-2 sentences |
| `brief` | 2-3 paragraphs |
| `detailed` | < 1000 words |
| `full` | Complete hierarchical |
| `all` | All levels combined |

**Usage**:
```bash
python3 automation/summarize_docs.py --input docs/wiki/Pipeline.md --detail-level tldr
python3 automation/summarize_docs.py --input GEMINI.MD --detail-level all --use-llm
python3 automation/summarize_docs.py --input file.md --save-hierarchy
```

**Related Files**:
- [`summarize_docs.pseudo.md`](summarize_docs.pseudo.md)
- [`summarize_docs.mmd`](summarize_docs.mmd)
- [`summarize_docs_visualization.png`](summarize_docs_visualization.png)

---

### 10. `index_project.py` — Project Indexing
**Purpose**: Build vector embeddings and knowledge graph for AI memory system.

**Features**:
- Generate code embeddings (all-MiniLM-L6-v2, 384 dims)
- Build knowledge graph
- Create search indexes
- Extract semantic relationships

**Usage**:
```bash
python3 automation/index_project.py --rebuild
python3 automation/index_project.py --incremental
python3 automation/index_project.py --build-human-index
```

**Related Files**:
- [`index_project.pseudo.md`](index_project.pseudo.md)
- [`index_project.mmd`](index_project.mmd)
- [`index_project_visualization.png`](index_project_visualization.png)

---

### 11. `generate_call_graph.py` — Call Graph Generation
**Purpose**: Create visual function/module call graphs.

**Output Formats**:
- Mermaid diagrams
- Interactive HTML
- PNG visualizations

**Usage**:
```bash
python3 automation/generate_call_graph.py --file processing/01_splitter.py
python3 automation/generate_call_graph.py --module processing.01_splitter
python3 automation/generate_call_graph.py --all-modules
```

**Related Files**:
- [`generate_call_graph.pseudo.md`](generate_call_graph.pseudo.md)
- [`generate_call_graph_workflow.mmd`](generate_call_graph_workflow.mmd)
- [`generate_call_graph_visualization.png`](generate_call_graph_visualization.png)

---

### 12. `update_diagrams.py` — Diagram Auto-Update
**Purpose**: Automatically regenerate diagrams when code changes.

**Diagram Types**:
- Architecture (C4 model)
- Data flow (Mermaid)
- Dependencies (Graphviz)
- Algorithms (PlantUML)

**Usage**:
```bash
python3 automation/update_diagrams.py --check
python3 automation/update_diagrams.py --update-all
python3 automation/update_diagrams.py --type architecture
```

**Related Files**:
- [`update_diagrams.pseudo.md`](update_diagrams.pseudo.md)
- [`update_diagrams_flow.mmd`](update_diagrams_flow.mmd)
- [`update_diagrams_visual.png`](update_diagrams_visual.png)

---

## ✅ Validation & Testing Tools

### 13. `validate_docs.py` — Documentation Validation
**Purpose**: Detect documentation drift, broken links, and inconsistencies.

**Checks**:
- Broken markdown links
- Missing specifications for Python files
- Spec-code drift (functions mismatch)
- YAML frontmatter presence

**Usage**:
```bash
python3 automation/validate_docs.py --report docs/validation_report.md
python3 automation/validate_docs.py --ci-mode
```

**Related Files**:
- [`validate_docs.pseudo.md`](validate_docs.pseudo.md)
- [`validate_docs.mmd`](validate_docs.mmd)
- [`validate_docs_flow.png`](validate_docs_flow.png)

---

### 14. `validate_system.py` — Multi-Tier Validation Orchestrator
**Purpose**: Adaptive validation with three tiers and five paranoia levels.

**Tiers**:
| Tier | Tools |
|------|-------|
| 1 | Algorithmic (validate_docs.py) |
| 2 | External (ruff, mypy, markdownlint) |
| 3 | AI (local_ai_verifier.py) |

**Paranoia Levels (1-5)**:
| Level | Tiers Used | Use Case |
|-------|------------|----------|
| 1 | [1] | < 50 files |
| 2 | [1,2] | 50-200 files |
| 3 | [1,2,3] | 200-500 files |
| 4 | [1,2,3] deep | 500-1000 files |
| 5 | [1,2,3] max | > 1000 files |

**Usage**:
```bash
python3 automation/validate_system.py --auto
python3 automation/validate_system.py --paranoia 2
python3 automation/validate_system.py --paranoia 5
```

**Related Files**:
- [`validate_system.pseudo.md`](validate_system.pseudo.md)
- [`validate_system.mmd`](validate_system.mmd)
- [`validate_system_workflow.png`](validate_system_workflow.png)

---

### 15. `test_system.py` — Paranoia-Level Test Runner
**Purpose**: Test the entire documentation system with configurable depth.

**Tests**:
1. Dependency analysis functionality
2. Document chunking functionality
3. Documentation validation
4. Directory structure completeness
5. README file presence

**Usage**:
```bash
python3 automation/test_system.py -p 1  # Quick
python3 automation/test_system.py -p 3  # Thorough
python3 automation/test_system.py -p 5  # Maximum
```

**Related Files**:
- [`test_system.pseudo.md`](test_system.pseudo.md)
- [`test_system.mmd`](test_system.mmd)
- [`test_system_metaphor.png`](test_system_metaphor.png)

---

## 🎙️ Voice & Voicepal Ecosystem

### 16. `voice_server.py` — Voice Development Server
**Purpose**: Main Flask server for voice-controlled development workflows.

**Features**:
- Real-time audio capture
- WebSocket streaming
- Session management
- Integration with ASR and LLM backends

**Related Files**:
- [`voice_server.pseudo.md`](voice_server.pseudo.md)
- [`voice_server_architecture.mmd`](voice_server_architecture.mmd)
- [`voice_server_architecture.png`](voice_server_architecture.png)

---

### 17. `voice_processor.py` — Voice Intent Processing
**Purpose**: Process voice input through vLLM backend for intent extraction.

**Related Files**:
- [`voice_processor.pseudo.md`](voice_processor.pseudo.md)
- [`voice_processor_architecture.mmd`](voice_processor_architecture.mmd)
- [`voice_processor_architecture.png`](voice_processor_architecture.png)

---

### 18. `voice_whisper.py` & `voice_whisper_fast.py` — ASR Integration
**Purpose**: Whisper-based speech-to-text with 82.7x real-time performance.

**Related Files**:
- [`voice_whisper.pseudo.md`](voice_whisper.pseudo.md)
- [`voice_whisper_architecture.mmd`](voice_whisper_architecture.mmd)
- [`voice_whisper_architecture.png`](voice_whisper_architecture.png)

---

### 19. `voice_whisper_client.py` — Distributed Whisper Client
**Purpose**: Client for connecting to remote faster-whisper-server instances.

---

## 🔮 NSS-Spec IDE (Prototype)

### 20. `nss_spec_ide.py` — Specification Generation IDE
**Status**: ⚠️ **UI Prototype Only**

The NSS-Spec IDE displays a 10-stage pipeline with 50+ buttons for specification generation. However, the underlying logic is not yet fully functional.

**Current Workflow**: All active development is performed via:
1. **Voicepal** voice sessions
2. **Direct CLI** calls to individual scripts

**Related Documentation**:
- [`nss_spec_pipeline_analysis.md`](nss_spec_pipeline_analysis.md) — 75KB comprehensive analysis
- [`voicepal_architecture.mmd`](voicepal_architecture.mmd)
- [`voicepal_architecture.png`](voicepal_architecture.png)

---

## � Architecture Documentation

| File | Description |
|------|-------------|
| [`VOICEPAL_ARCHITECTURE.md`](VOICEPAL_ARCHITECTURE.md) | Voicepal system architecture |
| [`VOICEPAL_INNOVATION_ANALYSIS.md`](VOICEPAL_INNOVATION_ANALYSIS.md) | Innovation analysis (18KB) |
| [`Web Framework Architecture for Local AI.md`](Web%20Framework%20Architecture%20for%20Local%20AI.md) | Django/Channels architecture (41KB) |
| [`docs_dual_memory_architecture.md`](docs_dual_memory_architecture.md) | Dual-index memory system |
| [`deep_research_prompt.md`](deep_research_prompt.md) | Deep research query template |

---

## 📊 Visualization Files

Each major script has associated visualization assets:

| Pattern | Description |
|---------|-------------|
| `*_VISUALIZATION.md` | Detailed visualization documentation |
| `*.mmd` | Mermaid diagram source |
| `*.png` | Rendered architecture diagrams |

---

## �️ Subdirectories

| Directory | Description |
|-----------|-------------|
| `backup/` | Backup files (4 files) |
| `neuro_semantics/` | Advanced NLP/semantics modules (178 files) |
| `recordings/` | Voice session recordings |
| `sessions/` | Voice session state data (20 sessions) |
| `static/` | Web assets (CSS/JS) |
| `templates/` | Jinja2 HTML templates |

---

## 🚀 Quick Start

### Run Tests
```bash
python3 automation/test_system.py -p 1
```

### Analyze Dependencies
```bash
python3 automation/analyze_dependencies.py --target path/to/file.py
```

### Assemble AI Context
```bash
python3 automation/assemble_context.py --task "implement feature X"
```

### Search Documentation
```bash
python3 automation/semantic_search.py --query "your search term"
```

---

## � Configuration

Scripts use `utils/config_loader.py` for shared configuration:
- **Embedding model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Memory directory**: `docs/memory/`
- **LLM backend**: vLLM (configurable endpoint)

---

## 📝 Related Documentation

- **Specifications**: `docs/specs/Automation_Tools_Spec.md`
- **Wiki**: `docs/wiki/09_Documentation_System.md`
- **Constitution**: `GEMINI.MD` (project root)

<!--/TAG:docs_automation_master_readme-->
