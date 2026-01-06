# NSS Coder — AI-First Documentation & Automation System

> **Philosophy**: In the AI programming era, documentation is more important than code. This system serves as both AI memory and human reference.

## Purpose

NSS Coder is a comprehensive **documentation-first development toolkit** designed for **dual consumption**:

### For AI Agents
- **Active Execution**: Run the automation scripts, not just read about them
- **Perfect Memory**: Complete understanding of project architecture and dependencies
- **Context Retrieval**: Run `assemble_context.py` to get task-specific context
- **Refactoring Safety**: Run `analyze_dependencies.py` to check impacts
- **Validation**: Run `validate_docs.py` to verify your work

### For Humans
- **Navigation**: Clear roadmap through complex codebase
- **Onboarding**: New developers can understand the system quickly
- **Maintenance**: Easy to find and fix issues
- **Knowledge Transfer**: Institutional knowledge preserved

---

## 🚀 Quick Start

**New to this project?** Start here:

1. **Constitution**: [GEMINI.MD](GEMINI.MD) (required reading)
2. **Automation**: [automation/README.MD](automation/README.MD) (core tools)
3. **Run Tests**: `python3 automation/test_system.py -p 1`

### Essential Commands

```bash
# Analyze dependencies for a file
python3 automation/analyze_dependencies.py --target path/to/file.py

# Assemble AI context for a task
python3 automation/assemble_context.py --task "implement feature X"

# Search documentation
python3 automation/semantic_search.py --query "your search term"

# Validate documentation
python3 automation/validate_docs.py
```

---

## Project Structure

```
nss_coder/
├── GEMINI.MD                    # Project constitution & AI rules
├── README.MD                    # This file
├── requirements.txt             # Python dependencies
│
├── automation/                  # Core automation toolkit (20+ scripts)
│   ├── README.MD               # Detailed automation guide
│   ├── *.py                    # Python automation scripts
│   ├── *.pseudo.md             # Pseudocode specifications
│   ├── *.mmd                   # Mermaid diagrams
│   └── voice_*.py              # Voicepal voice interface
│
├── docs/                        # Documentation system
│   ├── specs/                  # Formal specifications
│   ├── wiki/                   # Human-readable guides
│   ├── diagrams/               # Visual documentation
│   ├── developer_diary/        # Development logs
│   ├── technical_debt/         # Known issues & planned fixes
│   ├── logging_system/         # Two-layer logging docs
│   └── memory/                 # AI memory system
│       ├── embeddings/         # Vector embeddings
│       ├── knowledge_graph/    # Project knowledge graph
│       └── indexes/            # Fast lookup indexes
│
├── utils/                       # Shared utilities
│   ├── config_loader.py        # Configuration management
│   ├── docs_logger.py          # Paranoid logging
│   └── ...                     # Other utilities
│
└── output/                      # Generated outputs
    ├── validation/             # Validation reports
    └── verification/           # AI verification results
```

---

## Documentation Layers

We document **five interconnected layers**:

| Layer | Description |
|-------|-------------|
| **Code** | Imports, function calls, class inheritance, exports |
| **Configuration** | YAML/JSON files, environment variables, CLI args |
| **Data** | Input/output files, intermediate data, transformations |
| **External** | API calls, external services, system commands |
| **Orchestration** | Execution order, conditional logic, entry points |

---

## Methodology

### Algorithmic First, AI Second

**Priority**: Automated extraction using AST parsing, dependency analysis, and static analysis.

**AI Enhancement**: LLMs refine and explain algorithmic findings, not replace them.

### Living Documentation

Documentation updates **automatically** with code changes:
- Git hooks trigger validation
- CI/CD runs dependency analysis
- Diagrams regenerate on structure changes
- Drift detection alerts on mismatches

### Documentation-Driven Development

1. **Specification First**: Write spec before code
2. **Diary Entry**: Log intent in developer diary
3. **Implementation**: Write code
4. **Validation**: Run automation scripts
5. **Completion**: Update diary with results

---

## Core Automation Tools

| Script | Purpose |
|--------|---------|
| `analyze_dependencies.py` | 5-layer dependency extraction via AST |
| `assemble_context.py` | AI context assembly for tasks |
| `chunk_documents.py` | Hierarchical document chunking for RAG |
| `search_dependencies.py` | Dependency search & visualization |
| `semantic_search.py` | Keyword/semantic documentation search |
| `search_by_tag.py` | Semantic tag-based search |
| `validate_docs.py` | Documentation drift detection |
| `validate_system.py` | Multi-tier validation orchestrator |
| `test_system.py` | Paranoia-level test runner |

See [automation/README.MD](automation/README.MD) for detailed documentation.

---

## Voice Interface (Voicepal)

The primary interaction mode for development is through the **Voicepal** voice ecosystem:

- `voice_server.py` — Main Flask server
- `voice_processor.py` — vLLM intent processing
- `voice_whisper_fast.py` — 82.7x real-time ASR

---

## Configuration

Scripts use shared configuration:
- **Embedding model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Memory directory**: `docs/memory/`
- **LLM backend**: vLLM (configurable endpoint)

---

## What Makes This Unique

1. **Dual-Purpose Design**: Optimized for both AI and humans
2. **Five-Layer Dependency Mapping**: Beyond simple code dependencies
3. **Algorithmic First**: Automated extraction before AI enhancement
4. **Living Documentation**: Auto-updates with code changes
5. **Documentation-Driven Development**: Specs before code
6. **Military-Grade Observability**: Forensic-level logging

---

**Version**: 3.0  
**Last Updated**: 2026-01-06  
**Status**: Active Development
