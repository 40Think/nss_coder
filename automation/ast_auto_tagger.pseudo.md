# AST Auto Tagger Pseudocode

<!--TAG:pseudocode_ast_auto_tagger-->

---
source_file: docs/automation/ast_auto_tagger.py
date: 2025-12-12
version: 2.0
---

## Purpose

Automatically generates semantic tags for Python files using AST analysis.
Detects components from file paths, types from code structure, and features from imports/names.

## Data Structures

```
DATACLASS TagSuggestion:
    tag: str           # Full tag string (e.g., "component:automation")
    confidence: float  # 0.0 to 1.0 confidence score
    reason: str        # Human-readable explanation
    source: str        # Detection source: path, import, name, content

DATACLASS FileTagAnalysis:
    file_path: str                    # Path to analyzed file
    existing_tags: List[str]          # Tags already present in file
    suggested_tags: List[TagSuggestion]  # New tag suggestions
    primary_tag: Optional[str]        # Main file identifier tag
    classes_found: List[str]          # Class names from AST
    functions_found: List[str]        # Top-level function names
    imports_found: List[str]          # Import module names
```

## Class: ASTAutoTagger

```
CLASS ASTAutoTagger:
    ATTRIBUTES:
        schema_path: Path           # Path to tag_schema.yaml
        schema: Dict                # Loaded schema data
        tag_pattern: Regex          # Pattern for <!--TAG:...-->
        close_pattern: Regex        # Pattern for <!--/TAG:...-->
    
    METHOD __init__(schema_path: Optional[Path]):
        IF schema_path is None:
            schema_path = docs/specs/tag_schema.yaml
        schema = _load_schema()
        tag_pattern = compile(r'<!--TAG:([a-zA-Z0-9_:]+)-->')
        close_pattern = compile(r'<!--/TAG:([a-zA-Z0-9_:]+)-->')
        LOG "ASTAutoTagger initialized"
    
    METHOD _load_schema() -> Dict:
        IF schema_path.exists():
            TRY:
                RETURN yaml.safe_load(schema_path.read_text())
            CATCH Exception:
                LOG WARNING "Could not load schema"
        RETURN empty dict
```

## Main Algorithm

```
METHOD analyze_file(file_path: Path) -> FileTagAnalysis:
    # Initialize analysis result
    analysis = FileTagAnalysis(file_path=str(file_path))
    
    # Step 1: Read file content
    TRY:
        content = file_path.read_text(encoding='utf-8')
    CATCH Exception:
        LOG ERROR "Cannot read file"
        RETURN analysis
    
    # Step 2: Extract existing tags
    analysis.existing_tags = tag_pattern.findall(content)
    
    # Step 3: Parse AST
    TRY:
        tree = ast.parse(content)
    CATCH SyntaxError:
        LOG WARNING "Syntax error in file"
        RETURN analysis
    
    # Step 4: Extract AST information
    analysis.classes_found = _extract_classes(tree)
    analysis.functions_found = _extract_functions(tree)
    analysis.imports_found = _extract_imports(tree)
    
    # Step 5: Generate suggestions from multiple sources
    analysis.suggested_tags = _generate_suggestions(
        file_path, content, tree, analysis
    )
    
    # Step 6: Determine primary tag
    analysis.primary_tag = _generate_primary_tag(file_path, analysis)
    
    RETURN analysis
```

## AST Extraction Methods

```
METHOD _extract_classes(tree: AST) -> List[str]:
    # Walk entire tree, collect ClassDef node names
    RETURN [node.name FOR node IN ast.walk(tree) 
            IF isinstance(node, ClassDef)]

METHOD _extract_functions(tree: AST) -> List[str]:
    # Only top-level functions (direct children of module)
    RETURN [node.name FOR node IN ast.iter_child_nodes(tree)
            IF isinstance(node, FunctionDef)]

METHOD _extract_imports(tree: AST) -> List[str]:
    imports = []
    FOR node IN ast.walk(tree):
        IF isinstance(node, Import):
            FOR alias IN node.names:
                imports.ADD(alias.name)
        ELIF isinstance(node, ImportFrom):
            IF node.module:
                imports.ADD(node.module)
    RETURN imports
```

## Tag Suggestion Generation

```
METHOD _generate_suggestions(file_path, content, tree, analysis) -> List[TagSuggestion]:
    suggestions = []
    
    # Source 1: Component from file path (confidence: 1.0)
    component = _detect_component(file_path)
    IF component:
        suggestions.ADD(TagSuggestion(
            tag=f"component:{component}",
            confidence=1.0,
            reason=f"File is in {component}/ directory",
            source="path"
        ))
    
    # Source 2: Type from file structure (confidence: 0.9)
    type_tag = _detect_type(analysis)
    suggestions.ADD(TagSuggestion(
        tag=f"type:{type_tag}",
        confidence=0.9,
        reason=f"Detected {type_tag} from file structure",
        source="structure"
    ))
    
    # Source 3: Features from imports (confidence: 0.8)
    FOR tag, reason IN _detect_features_from_imports(analysis.imports_found):
        suggestions.ADD(TagSuggestion(
            tag=f"feature:{tag}",
            confidence=0.8,
            reason=reason,
            source="import"
        ))
    
    # Source 4: Features from class/function names (confidence: 0.7)
    FOR tag, reason IN _detect_features_from_names(analysis.classes_found + analysis.functions_found):
        suggestions.ADD(TagSuggestion(
            tag=f"feature:{tag}",
            confidence=0.7,
            reason=reason,
            source="name"
        ))
    
    # Source 5: Features from docstring content (confidence: 0.6)
    FOR tag, reason IN _detect_features_from_content(content):
        suggestions.ADD(TagSuggestion(
            tag=f"feature:{tag}",
            confidence=0.6,
            reason=reason,
            source="content"
        ))
    
    # Deduplicate, keeping highest confidence
    RETURN deduplicate_by_tag(suggestions)
```

## Feature Detection Rules

```
METHOD _detect_component(file_path: Path) -> Optional[str]:
    path_str = str(file_path)
    IF '/automation/' IN path_str: RETURN 'automation'
    IF '/utils/' IN path_str: RETURN 'utils'
    IF '/processing/' IN path_str: RETURN 'processing'
    IF '/tests/' IN path_str: RETURN 'tests'
    IF '/docs/' IN path_str: RETURN 'docs'
    RETURN None

METHOD _detect_type(analysis: FileTagAnalysis) -> str:
    IF analysis.classes_found AND len(classes) >= len(functions):
        RETURN 'class'
    ELIF analysis.functions_found:
        RETURN 'script'
    ELSE:
        RETURN 'script'

METHOD _detect_features_from_imports(imports: List[str]) -> List[Tuple[str, str]]:
    # Import pattern -> (feature, reason)
    MAPPING:
        'embed' -> ('embeddings', 'imports embedding-related module')
        'search' -> ('search', 'imports search-related module')
        'valid' -> ('validation', 'imports validation-related module')
        'log' -> ('logging', 'imports logging-related module')
        'memory' -> ('memory', 'imports memory-related module')
        'llm|openai|anthropic|vllm' -> ('llm', 'imports LLM-related module')
        'yaml' -> ('config', 'uses YAML configuration')
        'json' -> ('config', 'uses JSON configuration')

METHOD _detect_features_from_names(names: List[str]) -> List[Tuple[str, str]]:
    # Name pattern -> (feature, reason)
    MAPPING:
        'validator|validate' -> ('validation', 'Validator found')
        'search' -> ('search', 'Search class/function found')
        'embed' -> ('embeddings', 'Embed class/function found')
        'tagger|tag' -> ('tagging', 'Tagger class/function found')
        'logger' -> ('logging', 'Logger class found')
        'memory' -> ('memory', 'Memory class found')
        'index' -> ('indexing', 'Index class/function found')
        'context|assembl' -> ('context', 'Context assembler found')

METHOD _detect_features_from_content(content: str) -> List[Tuple[str, str]]:
    # Check only first 2000 chars (docstring area)
    MAPPING:
        'embedding' -> ('embeddings', 'mentions embedding')
        'semantic search' -> ('search', 'mentions semantic search')
        'validation' -> ('validation', 'mentions validation')
        'pipeline' -> ('pipeline', 'mentions pipeline')
        'llm' -> ('llm', 'mentions LLM integration')
```

## Tag Generation Output

```
METHOD _generate_primary_tag(file_path: Path, analysis: FileTagAnalysis) -> str:
    stem = file_path.stem
    
    # Check for existing primary tag
    FOR tag IN analysis.existing_tags:
        IF tag starts with 'tool_' OR 'spec_':
            RETURN tag
    
    # Generate based on path
    IF '/automation/' IN path: RETURN f"tool_{stem}"
    IF '/specs/' IN path: RETURN f"spec_{stem}"
    IF '/utils/' IN path: RETURN f"util_{stem}"
    RETURN stem

METHOD generate_tag_block(analysis: FileTagAnalysis, min_confidence: float = 0.7) -> str:
    # Filter by confidence threshold
    tags = [s FOR s IN analysis.suggested_tags IF s.confidence >= min_confidence]
    
    IF NOT tags:
        RETURN ""
    
    # Format inline tags
    inline_tags = ' '.join(f'<!--TAG:{s.tag}-->' FOR s IN tags)
    
    # Create block with primary tag wrapper
    RETURN f"""
<!--TAG:{analysis.primary_tag}-->

TAGS: {inline_tags}

<!--/TAG:{analysis.primary_tag}-->
"""
```

## Tag Application

```
METHOD apply_tags(file_path: Path, analysis: FileTagAnalysis, min_confidence: float = 0.7) -> bool:
    TRY:
        content = file_path.read_text(encoding='utf-8')
    CATCH Exception:
        LOG ERROR "Cannot read file"
        RETURN False
    
    # Skip if already has tags
    IF analysis.existing_tags:
        LOG INFO "File already has tags, skipping"
        RETURN False
    
    # Generate tag block
    tag_block = generate_tag_block(analysis, min_confidence)
    IF NOT tag_block:
        RETURN False
    
    # Find insertion point (after shebang/encoding, before docstring)
    lines = content.split('\n')
    insert_line = 0
    FOR i, line IN enumerate(lines):
        IF line starts with '#!' OR 'coding' IN line OR line is empty:
            insert_line = i + 1
        ELIF line starts with '"""' OR "'''":
            insert_line = i
            BREAK
        ELSE:
            BREAK
    
    # Insert and write back
    lines.insert(insert_line, tag_block)
    file_path.write_text('\n'.join(lines))
    LOG INFO "Applied tags to file"
    RETURN True
```

## CLI Interface

```
ARGUMENTS:
    --file FILE           Analyze single Python file
    --directory DIR       Analyze all .py files in directory (recursive)
    --all                 Analyze project dirs: docs/automation, utils, processing
    --preview             Show suggestions without applying (default behavior)
    --apply               Actually modify files with new tags
    --min-confidence N    Minimum confidence threshold (default: 0.7)
    --report              Generate summary statistics report
    --json                Output results as JSON format

MAIN FLOW:
    1. Parse arguments
    2. Initialize ASTAutoTagger
    3. Collect files based on --file/--directory/--all
    4. Analyze each file
    5. Output based on mode:
       - --json: JSON array of results
       - --apply: Apply tags, report count
       - --report: Summary statistics
       - default: Formatted preview
```

## Output Formats

### Preview Format (default)
```
============================================================
File: /path/to/script.py
============================================================

Existing tags (2):
  ✓ tool_script
  ✓ component:automation

Classes: MyClass, OtherClass
Functions: main, helper, process

Suggested tags (4):
  ✅ component:automation (100%) - File is in automation/ directory
  ✅ type:script (90%) - Detected script from file structure
  ⚠️ feature:logging (70%) - imports logging-related module
  ❓ feature:config (60%) - mentions configuration in docstring

Primary tag: <!--TAG:tool_script-->
```

### JSON Format (--json)
```json
[
  {
    "file": "/path/to/script.py",
    "existing_tags": ["tool_script"],
    "suggested_tags": [
      {"tag": "component:automation", "confidence": 1.0, "reason": "..."}
    ],
    "primary_tag": "tool_script",
    "classes": ["MyClass"],
    "functions": ["main"]
  }
]
```

### Report Format (--report)
```
============================================================
AST AUTO-TAGGER REPORT
============================================================
Files analyzed: 25
With existing tags: 18
Without tags: 7

Files needing tags:
  - utils/helper.py (3 suggestions)
  - processing/parser.py (4 suggestions)
```

## Feature Detection Confidence Levels

| Source | Confidence | Rationale |
|--------|------------|-----------|
| File path | 1.0 | Path location is definitive |
| Code structure | 0.9 | AST structure is reliable |
| Import patterns | 0.8 | Imports strongly indicate features |
| Name patterns | 0.7 | Names are suggestive but not definitive |
| Content patterns | 0.6 | Docstring mentions are weakest signal |

## Dependencies

- **docs.utils.docs_logger**: Isolated logging for docs/automation
- **yaml**: YAML parsing for tag_schema.yaml
- **ast**: Python AST parsing
- **argparse**: CLI argument handling
- **pathlib**: Path manipulation
- **dataclasses**: Data structure definitions
- **typing**: Type hints
- **re**: Regular expression patterns

<!--/TAG:pseudocode_ast_auto_tagger-->
