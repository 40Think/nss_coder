# Generate Call Graph - Workflow Documentation

This directory contains workflow documentation for `generate_call_graph.py`.

## Files

### 1. `generate_call_graph_workflow.mmd`
Comprehensive Mermaid diagram showing:
- **4 Dependency Types**: Code, Config, Data, External
- **Core Processing**: AST parsing, metrics calculation, LLM analysis, dual memory indexing
- **Outputs**: Mermaid/Graphviz/JSON formats, memory indexes, logs

### 2. `generate_call_graph_visualization.png`
Metaphorical visualization of the call graph generation process:
- **Left (Inputs)**: Python files, isolated utilities, vLLM API
- **Center (Processing)**: AST parser, function graph, metrics, AI analyzer
- **Right (Outputs)**: Diagrams, JSON data, memory vault, logs

## Viewing the Diagram

### Mermaid (Text)
```bash
cat docs/automation/generate_call_graph_workflow.mmd
```

### Visual Metaphor
```bash
xdg-open docs/automation/generate_call_graph_visualization.png
```

## Diagram Legend

**Colors**:
- 🔵 Blue: Input dependencies
- 🟠 Orange: Core processing
- 🟢 Green: Outputs
- 🟣 Purple: Optional AI features (dashed lines)
- 🟡 Yellow: Data structures

**Dependency Types**:
1. **Code**: `docs.utils.*` isolated modules
2. **Config**: None (hardcoded paths)
3. **Data**: Python source files, project structure
4. **External**: vLLM API (optional)

## Key Workflows

### Basic Call Graph Generation
```
Python Files → AST Parser → Function Registry → Output Generator → Mermaid/Graphviz/JSON
```

### Enhanced with AI Analysis
```
Function Registry → LLM Analyzer → Insights → Embedded in Output
```

### Dual Memory Integration
```
JSON Output → Dual Memory Indexer → Semantic Search Index
```

### Metrics Calculation
```
Function Registry → Metrics Calculator → Density/Cycles/Centrality → JSON Output
```

## Related Documentation

- **Script**: `generate_call_graph.py`
- **Pseudocode**: `generate_call_graph.pseudo.md`
- **Audit Report**: `docs/developer_diary/20251213_generate_call_graph_audit_fixes.md`
- **Ticket**: `docs/technical_debt/tickets_2025_12_11/TICKET_04_generate_call_graph.md`
