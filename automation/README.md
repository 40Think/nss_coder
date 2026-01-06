# Automation Scripts

<!--TAG:docs_automation_readme-->

This directory contains 15 automation scripts for the NSS-DOCS documentation system.

## Quick Reference

| Script | Purpose | CLI Example |
|--------|---------|-------------|
| `analyze_dependencies.py` | Extract 5-layer dependencies | `--target file.py` |
| `assemble_context.py` | Gather AI agent context | `--task "description"` |
| `ast_auto_tagger.py` | Generate semantic tags | `--file file.py --preview` |
| `chunk_documents.py` | 3-layer document chunking | `--file doc.md` |
| `generate_call_graph.py` | Mermaid call graphs | `--file file.py` |
| `index_project.py` | Build embeddings & indexes | `--build-human-index` |
| `search_by_tag.py` | Search by semantic tags | `--tag embeddings` |
| `search_dependencies.py` | Find who uses what | `--file file.py` |
| `semantic_search.py` | Semantic search | `--query "search term"` |
| `summarize_docs.py` | Summarize markdown | `--input doc.md` |
| `tag_validator.py` | Validate semantic tags | `--file file.py` |
| `test_system.py` | Run tests with paranoia | `-p 1` to `-p 5` |
| `update_diagrams.py` | Update mermaid diagrams | `--check` or `--update-all` |
| `validate_docs.py` | Validate documentation | (no args) |
| `validate_system.py` | Multi-tier validation | `-p 1` to `-p 5` |

## Directory Structure

```
docs/automation/
├── *.py                    # 15 automation scripts
├── pseudocode/             # Human-readable specifications
│   ├── README.md           # Pseudocode guide
│   └── *.pseudo.md         # Per-script pseudocode
└── README.md               # This file
```

## Usage Patterns

### For AI Agents

```bash
# Gather context for a task
python3 docs/automation/assemble_context.py --task "implement feature X"

# Find related files
python3 docs/automation/semantic_search.py --query "feature X"

# Understand dependencies
python3 docs/automation/analyze_dependencies.py --target path/to/file.py
```

### For Validation

```bash
# Quick check (algorithmic only)
python3 docs/automation/validate_system.py -p 1

# Full check (with external tools)
python3 docs/automation/validate_system.py -p 2

# Deep analysis (with supervisors)
python3 docs/automation/test_system.py -p 4
```

## Configuration

Scripts use `utils/config_loader.py` for configuration:
- Embedding model: `all-MiniLM-L6-v2` (384 dimensions)
- Memory directory: `docs/memory/`

## Related Documentation

- Specifications: `docs/specs/Automation_Tools_Spec.md`
- Wiki: `docs/wiki/09_Documentation_System.md`
- Pseudocode: `docs/automation/pseudocode/`

<!--/TAG:docs_automation_readme-->
