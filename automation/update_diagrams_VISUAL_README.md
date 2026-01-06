# update_diagrams.py - Visual Documentation

This directory contains visual documentation for the `update_diagrams.py` automation script.

## Files

### 1. `update_diagrams_flow.mmd`
**Type**: Mermaid Flowchart  
**Purpose**: Comprehensive technical flowchart showing the complete logic flow of the diagram updater system.

**Contents**:
- **5 Dependency Layers** (color-coded):
  - 🟣 **Layer 1 - Code**: `DocsLogger`, `watchdog` library
  - 🟠 **Layer 2 - Config**: `diagram_specs.json` (read/write)
  - 🟢 **Layer 3 - Data**: Source files (`*.py`, `*.md`), output diagrams (`.mmd`, `.json`)
  - 🔴 **Layer 4 - External**: `mermaid-cli`, `subprocess` commands
  - 🟡 **Layer 5 - Orchestration**: Parallel processing, observer pattern

- **Execution Modes**:
  - `--check`: Check which diagrams need updating (mtime comparison)
  - `--watch`: File watching with debouncing (2.0s)
  - `--update-all`: Sequential diagram updates
  - `--update-all --parallel`: Parallel updates with ProcessPoolExecutor
  - `--generate-index`: Create INDEX.md catalog

- **Core Mechanisms**:
  - Initialization & spec loading
  - Source change detection (mtime comparison)
  - Diagram generation (subprocess execution)
  - Mermaid validation (optional, via mmdc CLI)
  - Timestamp tracking
  - Statistics logging

**Usage**:
```bash
# View in Mermaid Live Editor
cat update_diagrams_flow.mmd | pbcopy
# Paste at https://mermaid.live

# Or render locally with mermaid-cli
mmdc -i update_diagrams_flow.mmd -o update_diagrams_flow.png
```

---

### 2. `update_diagrams_visual.png`
**Type**: Visual Metaphor (AI-generated)  
**Purpose**: Conceptual illustration showing the system as a "Diagram Automation Observatory"

**Metaphor Elements**:

**🎯 Center - Holographic Projection Sphere**:
- Represents the core diagram processing engine
- Shows interconnected diagrams auto-updating in real-time
- Visualizes the transformation from source code → validated diagrams

**📥 Left Side - Input Layer (5 Dependencies)**:
- **Purple Neural Pathways**: Code dependencies (DocsLogger, watchdog)
- **Golden Scroll**: Config layer (diagram_specs.json)
- **Green Data Streams**: Data sources (processing/*.py, utils/*.py)
- **Pink Terminals**: External tools (mermaid-cli, subprocess)
- **Yellow Control Panel**: Orchestration (parallel workers, observer)

**⚙️ Center Mechanisms**:
- **Mode Selector Dial**: 4-position switch (CHECK/WATCH/UPDATE/PARALLEL)
- **Watch Mode Sensors**: Debouncing timer (2.0s countdown)
- **Validation Chamber**: Mermaid syntax validator beam
- **Parallel Array**: 4 worker units operating simultaneously

**📤 Right Side - Output Layer**:
- **Crystallized Outputs**: Organized shelves of .mmd and .json files
- **INDEX.md Catalog**: Master reference glowing with links
- **Timestamp Markers**: last_updated tracking
- **Status Indicators**: Green checkmarks (success), red X's (failures)

**🌐 Background**:
- Grid pattern = project file structure
- Flowing arrows = data transformation pipeline
- Clock elements = mtime comparisons
- Watchdog mascot = file change monitoring

**🎨 Style**: Cyberpunk-meets-technical-manual aesthetic with blueprint grid, neon accents, isometric perspective

---

## Relationship Between Files

```
update_diagrams.py          (Python implementation)
        ↓
update_diagrams.pseudo.md   (Pseudocode specification)
        ↓
update_diagrams_flow.mmd    (Technical flowchart - THIS FILE)
        ↓
update_diagrams_visual.png  (Visual metaphor - THIS FILE)
```

**Purpose of Each Layer**:
1. **Python code**: Executable implementation
2. **Pseudocode**: Human-readable algorithm description
3. **Mermaid flowchart**: Precise technical visualization with all dependency layers
4. **Visual metaphor**: Conceptual understanding through imagery

---

## Key Insights from Visualization

### 1. **Multi-Mode Architecture**
The system operates in 4 distinct modes, each with different execution paths:
- Check mode: Read-only analysis
- Watch mode: Event-driven updates
- Sequential update: One-by-one processing
- Parallel update: Concurrent processing

### 2. **5-Layer Dependency Model**
Every operation touches multiple dependency layers:
- Code imports and function calls
- Configuration file reads/writes
- Data file I/O operations
- External tool executions
- Orchestration patterns (parallel, observer)

### 3. **Validation Pipeline**
Diagrams go through a multi-stage validation:
1. Source change detection (mtime)
2. Command execution (subprocess)
3. Syntax validation (mermaid-cli, optional)
4. Timestamp update
5. Statistics logging

### 4. **Debouncing Strategy**
Watch mode implements 2.0s debouncing to prevent:
- Multiple updates from rapid file saves
- Resource exhaustion from event storms
- Redundant diagram regeneration

### 5. **Graceful Degradation**
System continues operating even when optional dependencies are missing:
- watchdog not installed → watch mode disabled
- mermaid-cli not installed → validation skipped
- Generator command fails → error logged, continues

---

## Usage in Documentation

### For AI Agents
- Use `update_diagrams_flow.mmd` for precise understanding of control flow
- Reference dependency layers when assembling context
- Follow execution paths for debugging

### For Human Developers
- Use `update_diagrams_visual.png` for quick conceptual overview
- Use `update_diagrams_flow.mmd` for detailed implementation understanding
- Combine both for comprehensive system knowledge

### For Documentation
- Embed visual metaphor in wiki pages for conceptual explanations
- Embed Mermaid flowchart in specs for technical details
- Reference both in developer diary entries

---

## Maintenance

When updating `update_diagrams.py`:

1. ✅ Update `update_diagrams.pseudo.md` (pseudocode)
2. ✅ Update `update_diagrams_flow.mmd` (flowchart) if logic changes
3. ⚠️ Consider regenerating `update_diagrams_visual.png` if major features added
4. ✅ Update this README if new files added

---

**Created**: 2025-12-13  
**Last Updated**: 2025-12-13  
**Maintainer**: NSS-DOCS Automation System
