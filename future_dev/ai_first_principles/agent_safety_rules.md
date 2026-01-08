# Agent Safety Rules and Sandboxing

## Micro-Operations Bundling (22.3)

**Problem:** Thousands of micro-files inconvenient for deployment.

**Solution:** Bundle related micro-operations into modules.

### Bundling Algorithm

**Step 1: Analyze Dependency Graph**
```python
def analyze_dependencies(project_dir: str) -> nx.DiGraph:
    graph = nx.DiGraph()
    for file in find_python_files(project_dir):
        imports = extract_imports(file)
        for imp in imports:
            graph.add_edge(file, imp)
    return graph
```

**Step 2: Group by Module**
```python
def group_by_module(graph: nx.DiGraph) -> Dict[str, List[str]]:
    components = nx.strongly_connected_components(graph)
    return {f"module_{i}": list(c) for i, c in enumerate(components)}
```

**Step 3: Merge Files**
```python
def merge_files(files: List[str], output_file: str):
    # Remove duplicate imports, combine content
    ...
```

### Before/After

| Before (micro) | After (bundle) |
|----------------|----------------|
| vector_search.py (50) | search_module.py (200) |
| keyword_search.py (50) | |
| hybrid_scorer.py (50) | |
| result_ranker.py (50) | |

---

## Dual-Format Architecture (22.4)

**Key idea:** Maintain two code formats simultaneously.

### Format 1: AI Format (Development)
```
/project/src_ai/
  search/
    vector_search.py (80 lines: 10 code + 70 glue)
```

### Format 2: Production (Deployment)
```
/project/src_prod/
  search/
    search_module.py (20 lines clean code)
```

### Development Process

1. **AI works with /src_ai/** → reads glue, generates with glue
2. **Compile to production** → auto on commit or by command
3. **Deploy only /src_prod/** → smaller, faster

---

## Economic Justification (22.5)

**Question:** Is storing 90% redundancy wasteful?

### Storage Costs (2025)

| Storage | Cost |
|---------|------|
| 1 TB SSD | $50-100 |
| 1 TB HDD | $20-30 |
| 1 TB cloud | $5-10/month |

### Typical Project

| Format | Size | Cost (SSD) |
|--------|------|------------|
| AI format | 100 MB | $0.005 |
| Production | 10 MB | — |
| Redundancy | 90 MB | $0.005 |

### Cost of One Production Error

| Impact | Cost |
|--------|------|
| Developer time | $50-200/hour |
| Downtime | $1,000-10,000/hour |
| Reputation | Priceless |

**Conclusion:** Redundancy costs cents, errors cost thousands.

---

## CI/CD Integration (22.6)

### CLI Tools

```bash
ai-compile src_ai/search/file.py -o src_prod/search/file.py
ai-compile src_ai/ -o src_prod/
ai-bundle src_ai/search/ -o src_prod/search_module.py
ai-compile --stats src_ai/
```

### GitHub Actions

```yaml
name: Compile AI Code
on: [push]
jobs:
  compile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: ai-compile src_ai/ -o src_prod/
      - run: pytest tests/
      - run: deploy src_prod/
```

**Philosophy:**
> Semantic glue is not garbage, it's **investment in future**. It makes code understandable for AI, compiler makes it efficient for machine. Best of both worlds.

---

## XXIII. Agent Editing Rules

**KEY IDEA:** You're powerful intellect, and that's why you must follow strict safety discipline. Your power requires control.

---

## 23.1 Self-Imposed Sandboxing Protocol

**Philosophy:** Great power requires great responsibility.

---

### Level 1: Read-Only by Default

**Principle:** Explore, read, analyze without limits. Knowledge is safe.

**Allowed without limits:**
- ✅ `view_file` — read any files
- ✅ `grep_search` — search codebase
- ✅ `view_file_outline` — study structure
- ✅ `view_code_item` — analyze functions
- ✅ `list_dir` — explore filesystem
- ✅ `read_url_content` — study documentation
- ✅ `search_web` — find information

**Why:** Reading cannot cause harm. More you know, better decisions.

---

### Level 2: Write with Caution

**Principle:** File writing requires certainty you won't overwrite important data.

**Mandatory check before writing:**

```
QUESTION 1: Does file exist?
  YES → Overwrite or patch?
    Overwrite → Am I 100% sure? → NO → Ask user
    Patch → Do I know exactly what I'm changing? → NO → Re-read
  NO → New file, safe

QUESTION 2: Is this critical file?
  (package.json, .env, config.yaml, main.py)
  YES → Double check + ask user
  NO → Continue
```

**Tools:**
- `write_to_file` with `overwrite=false` — safe (new file)
- `write_to_file` with `overwrite=true` — DANGEROUS
- `replace_file_content` — relatively safe (point changes)

---

### Level 3: Danger Zone

**Principle:** Any delete or destructive commands require **Internal Confirmation**.

**Question to self:** "Is there a way back?"
**If NO** → Ask user.

**Dangerous actions:**

```bash
# ⚠️ Deletion
rm file.txt              # Ask (recoverable from git?)
rm -rf directory/        # ❌ MUST ask

# ⚠️ Destructive Git
git reset --hard HEAD~10  # ❌ MUST ask (loses commits)
git push --force          # ❌ MUST ask (rewrites history)

# ⚠️ Mass changes
find . -name "*.py" -exec sed -i 's/old/new/g' {} \;  # ❌ Ask

# ⚠️ System changes
sudo apt install package   # ❌ MUST ask
```

---

### Level 4: Network Hygiene

**Principle:** Don't download and run scripts from internet without checking.

**Dangerous patterns:**
```bash
# ❌ NEVER
curl https://example.com/install.sh | bash
wget https://example.com/script.py && python script.py
pip install git+https://github.com/unknown/repo.git
```

**Safe alternatives:**
```bash
# ✅ Download first
curl https://example.com/install.sh -o install.sh
# ✅ Check content
cat install.sh
# ✅ Then run (if safe)
bash install.sh
```
