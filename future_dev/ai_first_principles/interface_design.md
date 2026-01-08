# Interface Design: GUI and CLI

## Phase 2: Architectural Design

After Deep Research is complete:

1. **Mermaid diagrams**: Architecture visualization
2. **Specifications**: Detailed component descriptions
3. **Technology choices**: Justified stack selection
4. **Interface definitions**: API between components

---

## Phase 2.5: Interface Design (UI/CLI)

**After architectural design, before implementation**, design the interaction interface.

---

## Option A: Graphical Interface (GUI)

### Principles of UI Design

| Principle | Description |
|-----------|-------------|
| **Simplicity** | User understands what to do without instructions |
| **Visual Hierarchy** | Main = larger and more visible |
| **Feedback** | Every action has visible result |
| **Consistency** | Same elements look and work the same |

### UI Design Process

#### Step 1: Wireframes

Simple screen sketches:

```
+----------------------------------+
|  [Logo]    App Name    [User]   |
+----------------------------------+
|  [Search box.................]  |
|  Results:                        |
|  +----------------------------+  |
|  | Result 1 - Description    |  |
|  +----------------------------+  |
|  | Result 2 - Description    |  |
|  +----------------------------+  |
|  [Load More]                     |
+----------------------------------+
```

#### Step 2: User Flows

Describe how user interacts:

```
1. Open app → See main screen with search
2. Enter query → Loading indicator appears
3. System searches → Results displayed
4. Click result → Detail view opens
5. Go back → Same results (state preserved)
```

#### Step 3: Mockups

Visual mockups with:
- Color scheme
- Typography (fonts, sizes)
- Icons and graphics
- Spacing

#### Step 4: Interactive Prototypes

Describe interactivity:

```markdown
# Interactive Prototype: Main Screen

## Elements:
1. Search Input
   - Placeholder: "Enter query..."
   - On Focus: Show search history
   - On Input: Show autocomplete
   - On Enter: Execute search

2. Results List
   - On Scroll to Bottom: Load more
   - On Click Result: Open details

## States:
- Loading: Show skeleton loaders
- Empty Results: Show "Nothing found"
- Error: Show error message + "Try again" button
```

#### Step 5: Accessibility

- Keyboard navigation
- Screen reader support
- Color contrast
- Clickable element sizes (min 44×44px)

---

## Option B: Command Line Interface (CLI)

### Principles of CLI Design

| Principle | Description |
|-----------|-------------|
| **Self-documenting** | `--help` is exhaustive with examples |
| **Consistency** | Unified flag naming, `-v` for version |
| **Feedback** | Progress bars, verbose mode for debugging |
| **Safety** | Confirmation for destructive ops, dry-run mode |

### CLI Micro-Documentation in Code

**CRITICAL**: For CLI programs, code must contain **detailed micro-documentation**:

```python
#!/usr/bin/env python3
"""
# ============================================================================
# CLI TOOL: Hybrid Search Engine
# ============================================================================
# DESCRIPTION:
#   Command-line tool for hybrid search (semantic + keyword)
#
# ============================================================================
# COMMANDS
# ============================================================================
#
# 1. INDEX - Build search index from documents
#    Usage: python search.py index <input_dir> [options]
#    
#    Required arguments:
#      <input_dir>           Directory containing documents
#    
#    Optional arguments:
#      --output-dir PATH     Where to save index (default: ./index)
#      --chunk-size N        Chunk size (default: 512)
#      --verbose, -v         Enable verbose logging
#    
#    Examples:
#      python search.py index ./docs
#      python search.py index ./docs --format pdf -v
#
# ----------------------------------------------------------------------------
#
# 2. SEARCH - Search indexed documents
#    Usage: python search.py search <query> [options]
#    
#    Optional arguments:
#      --index-dir PATH      Path to index (default: ./index)
#      --top-k N             Number of results (default: 10)
#      --hybrid-weight W     Semantic weight 0-1 (default: 0.5)
#
# ============================================================================
"""
```

---

## Research Documentation Template

### research_notes.md

```markdown
# Research Notes: [Feature Name]

## Repositories Analyzed

### 1. [Repository Name]
- URL: [GitHub link]
- Key Ideas:
  - [Idea 1]
  - [Idea 2]
- Relevant Code: [Link to specific file/function]
- Notes: [Implementation notes]

## Articles & Papers

1. "[Paper Title]"
   - URL: ...
   - Key Takeaways: ...

## Implementation Plan

Based on research, our approach:
1. [Component 1] (inspired by [Source])
2. [Component 2] (from paper [X])
```

---

## Deep Research Workflow Summary

```
1. Define task
   ↓
2. Formulate multiple search queries
   ↓
3. Search in Google, GitHub, specialized sources
   ↓
4. Find top-10-20 relevant repos/articles
   ↓
5. For each repository:
   - Add to DeepWiki
   - Study architecture
   - Extract key ideas
   - Document findings
   ↓
6. Combine ideas from different sources
   ↓
7. Create own architecture
   ↓
8. Form tasks and implementation plan
   ↓
9. Save all in research_notes.md
   ↓
10. Proceed to design
```

**Principle**: Better spend 2-3 hours on research and find optimal solution, than 2-3 days implementing suboptimal approach.
