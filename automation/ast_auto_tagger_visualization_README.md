# AST Auto-Tagger Visualization

This directory contains visual documentation for the `ast_auto_tagger.py` script.

## Files

- **`ast_auto_tagger.mmd`** - Mermaid flowchart diagram showing:
  - Complete workflow from CLI entry to output
  - All 5 tag detection sources with confidence levels
  - Data dependencies (inputs/outputs)
  - Config dependencies (tag_schema.yaml)
  - Code dependencies (DocsLogger, AST, YAML)
  - Decision points and error handling

- **`ast_auto_tagger_workflow.png`** - Metaphorical visualization:
  - "Tag Forge" / "Semantic Workshop" concept
  - 5 detection chambers with confidence-based glow
  - Input conveyor (Python files as scrolls)
  - Output streams (modified files, JSON, reports, preview)
  - AST tree visualization in background
  - Dependency orbs (DocsLogger, YAML, AST)

## How to Use

### View Mermaid Diagram
```bash
# In VS Code with Mermaid extension
code ast_auto_tagger.mmd

# Or render online
cat ast_auto_tagger.mmd | pbcopy
# Paste at https://mermaid.live
```

### View Workflow Visualization
```bash
# Open image
xdg-open ast_auto_tagger_workflow.png
```

## Diagram Legend

### Confidence Levels (Detection Sources)
1. **Path Detection** (1.0 / 100%) - File location in directory structure
2. **Structure Analysis** (0.9 / 90%) - Classes/functions from AST
3. **Import Scanning** (0.8 / 80%) - Import statements
4. **Name Matching** (0.7 / 70%) - Class/function names
5. **Content Reading** (0.6 / 60%) - Docstring keywords

### Dependency Types
- **Data Dependencies**: Input/output files
- **Config Dependencies**: tag_schema.yaml
- **Code Dependencies**: DocsLogger, AST module, YAML parser
- **External Dependencies**: None (fully self-contained)

## Related Documentation

- **Script**: `ast_auto_tagger.py`
- **Pseudocode**: `ast_auto_tagger.pseudo.md`
- **Tag Schema**: `../specs/tag_schema.yaml`
- **Audit Report**: `../developer_diary/20251212_ast_auto_tagger_audit.md`
