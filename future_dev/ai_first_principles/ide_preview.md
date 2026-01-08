# IDE Preview Advanced Features

## Usage Scenarios

### Scenario 1: Code Review
**Situation:** Senior wants to understand algorithm logic quickly.

**Action:**
1. Opens file with microfunctions
2. Presses `Ctrl+Shift+P` → "Show Clean Code Preview"
3. Sees compact code without comments
4. Quick assessment (30 seconds instead of 5 minutes)

**Result:** 10x faster code review for understanding structure.

---

### Scenario 2: Debugging
**Situation:** Bug in assembled pipeline, need to understand call sequence.

**Action:**
1. Opens Preview in "Structural" mode
2. Sees `@order:1`, `@order:2`, `@order:3` tags
3. Understands `@parallel` functions execute simultaneously
4. Finds race condition

**Result:** Explicit execution flow visualization eases debugging.

---

### Scenario 3: Onboarding
**Situation:** New developer sees AI-First code with 90% comments for first time.

**Action:**
1. First looks at Clean Code Preview
2. Understands general structure
3. Then switches to full code with comments
4. Dives into details

**Result:** Gradual immersion instead of overwhelming effect.

---

### Scenario 4: Code Export
**Situation:** Need to share code with external team not using NSS Coder.

**Action:**
1. Generates Clean Code Preview
2. Exports to separate file
3. Sends to partners

**Result:** External team gets normal code without comment "clutter."

---

## Configuration: .nss-coder.yaml

```yaml
preview:
  enabled: true
  default_mode: "documented"  # clean | structural | documented
  
  auto_update: true
  update_delay_ms: 300  # debouncing
  
  hotkeys:
    toggle_preview: "Ctrl+Shift+P"
    cycle_modes: "Ctrl+Shift+M"
    export_clean: "Ctrl+Shift+E"
  
  optimization_level: 1  # 0 | 1 | 2
  
  comment_filters:
    keep_docstrings: true
    keep_assembly_tags: true
    keep_todos: false
    keep_explanations: false
  
  cache:
    enabled: true
    max_size_mb: 100
    ttl_seconds: 3600
```

---

## Benefits

### For Developers
✅ Fast code reading (30 sec vs 5 min)
✅ Flexible viewing (3 modes)
✅ No mental overload (one-click switch)
✅ Gradual onboarding

### For AI
✅ Source code remains AI-friendly
✅ Semantic glue preserved
✅ Token connectivity unbroken

### For Team
✅ Faster code review
✅ Export compatibility
✅ Personal viewing preferences

---

## IDE Integration

### VS Code Extension: `NSS Coder Preview`
- Sidebar with preview panel
- Command palette commands
- Status bar icon (mode + build status)
- Context menu: "Generate Clean Code"

### IntelliJ IDEA Plugin: `NSS Coder Assistant`
- Tool window with preview
- Intention actions: "Show without comments"
- Build error notifications
- Project structure integration

### Web IDE (GitHub Codespaces, Replit)
- Language Server Protocol (LSP)
- Server-side preview generation
- WebSocket for live updates

---

## Comparison: Comment Folding vs NSS Coder Preview

| Aspect | Comment Folding | NSS Coder Preview |
|--------|-----------------|-------------------|
| **Approach** | Hides comments | Generates new code |
| **Optimization** | No | Yes (inline, dead code elimination) |
| **Assembly** | No | Yes (microfunctions → pipeline) |
| **Dependency graph** | No | Yes (@assembly tags) |
| **Modes** | 1 (hidden/shown) | 3 (clean/structural/documented) |
| **Export** | Copy + manual removal | Auto-export ready code |
| **AI context** | Lost | Preserved in sources |

---

## Full Workflow Example

### Before (Source Microfunction) — 22 lines
```python
# @assembly:search_pipeline @order:1
def fetch_bm25_results(query, top_k):
    """
    Gets results from BM25 index
    
    Why BM25: Finds by exact words
    Problem: No synonyms
    """
    # STEP 1: Validate
    # WHY: Prevent errors
    if not query:
        return []
    
    # STEP 2: Search
    # WHY: Find matches
    results = bm25_index.search(query, top_k * 2)
    
    # STEP 3: Log
    print(f"[LOG] Found {len(results)} docs")
    
    return results
```

### After (Clean Preview) — 6 lines
```python
def fetch_bm25_results(query, top_k):
    if not query:
        return []
    results = bm25_index.search(query, top_k * 2)
    print(f"[LOG] Found {len(results)} docs")
    return results
```

**Results:**
- Lines: 22 → 6 (73% reduction)
- Reading time: 45s → 10s

---

## Philosophy Connection

This concept reinforces:
1. **Dual Causality**: Optimal for both Human→AI and AI→Human
2. **Holography**: Microfunctions self-contained, Preview shows whole
3. **Extreme Decomposition**: Simplifies assembly via independent microfunctions
4. **Auto-assembly**: Preview is IDE implementation of auto-assembly

> We don't force humans to read AI-code. We **translate** AI-code to human-readable format.
