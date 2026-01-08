# Modular Structure Pattern

## Core Concept

Instead of one 100-700 line file with dozens of operations, use modular folder structure.

---

## Standard Module Structure

```
module/
├── README.md                    # Module description
├── architecture.mermaid         # Module architecture diagrams
├── specification.md             # Specification for this module
├── orchestrator.py              # Central orchestration file
├── operation_1.py               # Inside: 10-20% code, 80-90% semantic glue
├── operation_2.py               # All context INSIDE the file
└── operation_3.py
```

---

## Principles

### 1. Each Module is a Folder with its Own README
- Self-contained documentation
- Module purpose and scope
- Dependencies and interfaces

### 2. Mermaid Diagram Files for Architecture Visualization
- Visual representation of module structure
- Component relationships
- Data flow

### 3. Specification at Module Level
- Requirements for the module
- Constraints and contracts
- Integration points

### 4. Each .py File Contains EVERYTHING Inside Itself
- **10-20% executable code**
- **80-90% semantic glue and vector sugar:**
  - Comments
  - Pseudocode
  - Tickets
  - Specifications
  - ASCII diagrams
  - Examples

### 5. Files Call Each Other
- Directly or through orchestrator
- Depending on situation
- Clear dependency direction

---

## File Content Ratio

```
┌─────────────────────────────────────────┐
│ TYPICAL FILE IN NSS CODER               │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ Ticket Header (150-200 lines)       │ │
│ │ - Context                           │ │
│ │ - Requirements                      │ │
│ │ - Design decisions                  │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Semantic Glue (~50-100 lines)       │ │
│ │ - Comments on every line            │ │
│ │ - WHY explanations                  │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Executable Code (~30-50 lines)      │ │
│ │ - Actual implementation             │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ RATIO: ~20% code / ~80% context         │
└─────────────────────────────────────────┘
```

---

## Why This Works

1. **Self-Contained**: Each file understandable without external context
2. **AI-Friendly**: All context available for AI processing
3. **Maintainable**: Changes localized to specific modules
4. **Discoverable**: Easy to navigate and find relevant code
5. **Regenerable**: Each module can be regenerated independently
