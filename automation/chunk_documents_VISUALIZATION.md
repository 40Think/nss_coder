# chunk_documents.py - Visualization

This directory contains visual documentation for the hierarchical document chunking system.

## Files

### 1. `chunk_documents.mmd` - Mermaid Flowchart
Technical flowchart showing:
- **Input Layer**: Markdown files, YAML frontmatter, configuration
- **Processing Pipeline**: Frontmatter extraction, structure detection, preservation logic
- **3-Layer Architecture**:
  - L2 (DOCUMENTS): Full document chunks
  - L1 (SECTIONS): Header-based section chunks
  - L0 (CLAUSES): Fine-grained sentence/paragraph chunks
- **Output Layer**: JSON files for each layer + combined index
- **Dependencies**: ParanoidLogger, YAML library, regex patterns
- **Downstream Consumers**: index_project.py, semantic_search.py, dual_memory.py

### 2. `chunk_documents_visualization.png` - Metaphorical Diagram
Visual metaphor using a tree to represent the hierarchical chunking process:

**Tree Metaphor**:
- **Canopy (L2)**: Full documents as golden-leafed tree crowns
- **Branches (L1)**: Sections as major branches with leaf clusters
- **Twigs (L0)**: Clauses as fine twigs and individual leaves

**Data Flow**:
- **Inputs** (left): Blue streams (markdown), orange particles (YAML), purple sparks (config)
- **Processing** (trunk): Extraction, detection, preservation, adaptive sizing
- **Outputs** (right): Three colored streams merging into golden "Combined Index" river
- **Consumers** (bottom): Search tower, memory vault, index library

## Architecture Overview

```
Markdown Files → Hierarchical Chunker → 3 Layers → JSON Outputs → RAG Systems
                        ↓
                 Code/Table Preservation
                 Adaptive Sizing
                 Parent-Child Links
```

## Statistics (145 files processed)

| Layer | Chunks | Purpose |
|-------|--------|---------|
| L0 (CLAUSES) | 3,527 | Fine-grained retrieval |
| L1 (SECTIONS) | 2,635 | Topic-level retrieval |
| L2 (DOCUMENTS) | 145 | Broad context |
| **Total** | **6,307** | Multi-granularity search |

## Key Features Visualized

1. **Hierarchical Structure**: Parent-child relationships between layers
2. **Code Preservation**: Shield protecting code blocks from splitting
3. **Adaptive Sizing**: Dynamic chunk sizing (300-800 chars)
4. **Metadata Flow**: YAML frontmatter enriching all layers
5. **Multi-Output**: Separate JSON files per layer + combined index

## Usage

View the Mermaid diagram:
```bash
# In VS Code with Mermaid extension
code chunk_documents.mmd

# Or render online
https://mermaid.live/
```

View the metaphorical visualization:
```bash
# Open the PNG file
xdg-open chunk_documents_visualization.png
```

## Related Documentation

- **Implementation**: `chunk_documents.py`
- **Pseudocode**: `pseudocode/chunk_documents.pseudo.md`
- **Specification**: `../../specs/Automation_Tools_Spec.md`
- **Tests**: `../../tests/test_chunk_documents.py`
- **Analysis**: `../../technical_debt/chunk_documents_gaps.md`
