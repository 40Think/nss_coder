---
description: "Extracts 5 layers of dependencies from Python files via AST analysis"
date: 2025-12-12
version: "2.0"
source_file: analyze_dependencies.py
tags: automation, dependencies, AST, analysis, dynamic-imports
---

# analyze_dependencies.py v2.0 — Pseudocode

<!--TAG:pseudo_analyze_dependencies-->

## PURPOSE

Performs algorithmic analysis of Python code to extract 5 layers of dependencies:

1. **Code Layer** — imports, function calls, class hierarchy, exports
2. **Configuration Layer** — configuration files, environment variables, CLI arguments
3. **Data Layer** — file read/write operations
4. **External Layer** — API calls, external libraries
5. **Orchestration Layer** — entry points, subprocess calls

### v2.0 Enhancements
- Extraction of decorator arguments (`@lru_cache(maxsize=128)`)
- Resolution of relative imports (`from ..utils import helper`)
- Detection of dynamic imports (`importlib.import_module()`, `__import__()`)
- Discovery of metaclasses (`class Foo(metaclass=ABCMeta)`)

---

## DEPENDENCIES

```
Internal (docs/):
    - docs.utils.docs_logger.DocsLogger  # Isolated logger

Standard Library:
    - ast                # AST parsing of Python code
    - json               # Result serialization
    - re                 # Regular expressions for dynamic imports
    - dataclasses        # Data structures
    - pathlib.Path       # Path manipulation

Data:
    - Input:  *.py files
    - Output: docs/memory/dependencies/*_dependencies.json
```

---

## DATA STRUCTURES

### DependencyInfo (dataclass)

```pseudo
DATACLASS DependencyInfo:
    file_path: STRING                   # Path to analyzed file
    
    # === CODE LAYER ===
    imports: LIST[{
        module: STRING,                 # Module name
        name: STRING?,                  # Imported name (for from...import)
        alias: STRING?,                 # Alias (as ...)
        line: INT,                      # Line number
        is_relative: BOOL,              # Relative import?
        level: INT,                     # Level (. = 1, .. = 2)
        resolved_module: STRING         # v2.0: Absolute module path
    }]
    
    function_calls: LIST[{
        function: STRING,               # Function name
        line: INT,                      # Line number
        context: STRING?                # Context (function/class name)
    }]
    
    class_hierarchy: LIST[{
        class: STRING,                  # Class name
        bases: LIST[STRING],            # Base classes
        metaclass: STRING?,             # v2.0: Metaclass (if any)
        has_dynamic_behavior: BOOL,     # v2.0: __new__, __init_subclass__, etc.
        decorators: LIST[DecoratorInfo],# v2.0: Class decorators
        line: INT                       # Line number
    }]
    
    exports: LIST[STRING]               # Public functions/classes
    
    # v2.0: Extended function definitions
    function_definitions: LIST[{
        name: STRING,                   # Function name
        args: LIST[ArgInfo],            # Arguments with annotations
        decorators: LIST[DecoratorInfo],# v2.0: Full decorator info
        line: INT,                      # Line number
        is_async: BOOL,                 # Async function?
        class: STRING?                  # Parent class (if method)
    }]
    
    # v2.0: Dynamic imports
    dynamic_imports: LIST[{
        type: "dynamic_import",         # Record type
        pattern: STRING,                # Pattern type (importlib, __import__, etc.)
        module: STRING,                 # Module name (or variable)
        line: INT,                      # Line number
        confidence: "high"|"medium"|"low",  # Detection confidence
        warning: STRING,                # Warning for developer
        is_variable: BOOL               # Module passed via variable?
    }]
    
    # === CONFIGURATION LAYER ===
    config_files: LIST[{file, type, operation, line}]
    env_vars: LIST[{var, default, line}]
    cli_args: LIST[{arg, line}]
    
    # === DATA LAYER ===
    file_reads: LIST[{path, operation, line}]
    file_writes: LIST[{path, operation, line}]
    data_transforms: LIST[{input_type, output_type, function}]
    
    # === EXTERNAL LAYER ===
    api_calls: LIST[{service, endpoint, function, line}]
    system_commands: LIST[{command, function, line}]
    external_libs: LIST[STRING]
    
    # === ORCHESTRATION LAYER ===
    entry_points: LIST[{type, name, line}]
    subprocess_calls: LIST[{command, function, line}]
    
    # === v2.0: METADATA ===
    metadata: DICT = {
        total_functions: INT,
        total_classes: INT,
        total_imports: INT,
        has_dynamic_imports: BOOL,
        has_dynamic_behavior: BOOL,
        lines_of_code: INT,
        file_size_bytes: INT
    }
    analysis_version: STRING = "2.0"
    timestamp: ISO8601_STRING
```

### DecoratorInfo (helper structure)

```pseudo
STRUCTURE DecoratorInfo:
    name: STRING        # Decorator name (e.g., "lru_cache")
    args: LIST[ANY]     # Positional arguments
    kwargs: DICT        # Keyword arguments
```

### ArgInfo (helper structure)

```pseudo
STRUCTURE ArgInfo:
    name: STRING        # Argument name
    type: "arg"|"vararg"|"kwarg"  # Type (*args, **kwargs)
    annotation: STRING? # Type annotation
```

---

## CLASS: DynamicImportDetector (v2.0)

Detects dynamic imports that AST cannot fully resolve.

```pseudo
CLASS DynamicImportDetector:
    
    # Regex patterns for detection
    PATTERNS = {
        "importlib":        r'importlib\.import_module\s*\(\s*["\']([^"\']+)["\']\s*\)',
        "importlib_var":    r'importlib\.import_module\s*\(\s*(\w+)\s*\)',
        "__import__":       r'__import__\s*\(\s*["\']([^"\']+)["\']\s*\)',
        "__import___var":   r'__import__\s*\(\s*(\w+)\s*\)',
        "exec_import":      r'exec\s*\(\s*["\']import\s+(\w+)["\']\s*\)',
        "conditional_import": r'if\s+[^:]+:\s*\n\s*import\s+(\w+)',
        "try_import":       r'try:\s*\n\s*import\s+(\w+)'
    }
    
    FUNCTION detect_dynamic_imports(source_code: STRING, file_path: STRING) -> LIST:
        """
        Detects dynamic imports via regex + heuristics.
        """
        results = []
        
        FOR EACH pattern_name, regex IN PATTERNS:
            TRY:
                matches = regex.findall(source_code)
                
                FOR EACH match IN matches:
                    # Extract module name
                    module_name = match.group(1) OR "unknown"
                    
                    # Calculate line number
                    line_num = COUNT newlines before match + 1
                    
                    # Determine confidence
                    IF "_var" IN pattern_name:
                        confidence = "low"
                        warning = "Dynamic import with variable - cannot resolve statically"
                    ELIF "conditional" OR "try" IN pattern_name:
                        confidence = "medium"
                        warning = "Conditional import - may not always be executed"
                    ELSE:
                        confidence = "high"
                        warning = "Dynamic import detected - verify manually"
                    
                    APPEND TO results: {
                        type: "dynamic_import",
                        pattern: pattern_name (without _var),
                        module: module_name,
                        line: line_num,
                        confidence: confidence,
                        warning: warning,
                        is_variable: "_var" IN pattern_name
                    }
                    
            CATCH regex.error:
                LOG warning
                CONTINUE
        
        RETURN results
```

---

## CLASS: DependencyAnalyzer (AST Visitor)

### Initialization

```pseudo
CLASS DependencyAnalyzer EXTENDS ast.NodeVisitor:
    
    FUNCTION __init__(file_path: STRING, project_root: PATH = None):
        self.file_path = file_path
        self.project_root = project_root OR parent(parent(file_path))
        self.deps = NEW DependencyInfo(file_path)
        
        # Context for tracking current position in AST
        self.current_class = None
        self.current_function = None
```

### v2.0: Decorator Analysis

```pseudo
FUNCTION _analyze_decorator(decorator_node) -> DecoratorInfo:
    """
    Extracts decorator name and its arguments.
    
    Examples:
        @property              -> {name: "property", args: [], kwargs: {}}
        @lru_cache(maxsize=128) -> {name: "lru_cache", args: [], kwargs: {maxsize: 128}}
        @app.route("/api")     -> {name: "app.route", args: ["/api"], kwargs: {}}
    """
    IF decorator IS ast.Name:
        # Simple decorator: @property
        RETURN {name: decorator.id, args: [], kwargs: {}}
    
    ELIF decorator IS ast.Attribute:
        # Decorator with attribute: @module.decorator
        RETURN {name: GET_FULL_NAME(decorator), args: [], kwargs: {}}
    
    ELIF decorator IS ast.Call:
        # Decorator with arguments: @decorator(arg1, key=val)
        name = GET_NAME(decorator.func)
        
        # Positional arguments
        args = [GET_VALUE(arg) FOR arg IN decorator.args]
        
        # Keyword arguments
        kwargs = {kw.arg: GET_VALUE(kw.value) FOR kw IN decorator.keywords IF kw.arg}
        
        RETURN {name: name, args: args, kwargs: kwargs}
    
    RETURN {name: "unknown", args: [], kwargs: {}}
```

### v2.0: Relative Import Resolution

```pseudo
FUNCTION _resolve_relative_import(relative_module: STRING, level: INT) -> STRING:
    """
    Transforms a relative import into an absolute module path.
    
    Examples:
        from . import utils       (level=1) -> current_package.utils
        from ..core import base   (level=2) -> parent_package.core.base
    """
    TRY:
        file_path = Path(self.file_path)
        
        # Get package structure from file path
        IF self.project_root AND file_path.is_absolute():
            relative_path = file_path.relative_to(self.project_root)
            package_parts = relative_path.parts[:-1]  # Remove file name
        ELSE:
            package_parts = file_path.parts[:-1]
        
        # Go up level directories
        IF level > LENGTH(package_parts):
            LOG warning "Can't resolve import level {level}"
            RETURN relative_module OR ""
        
        # Calculate base package
        base_parts = package_parts[:-level] IF level > 0 ELSE package_parts
        base_package = JOIN(base_parts, ".")
        
        # Merge with relative module
        IF relative_module:
            RETURN "{base_package}.{relative_module}" IF base_package ELSE relative_module
        RETURN base_package
        
    CATCH Exception:
        LOG warning
        RETURN relative_module OR ""
```

### visit_Import — Process import statements

```pseudo
FUNCTION visit_Import(node):
    # Example: import os, sys as system
    FOR EACH alias IN node.names:
        APPEND TO self.deps.imports: {
            module: alias.name,
            alias: alias.asname,
            line: node.lineno,
            is_relative: False,
            resolved_module: alias.name
        }
    
    CONTINUE visiting children
```

### visit_ImportFrom — Process from...import statements

```pseudo
FUNCTION visit_ImportFrom(node):
    """
    Example: from utils.helpers import foo
    Example v2.0: from ..core import base (relative import)
    """
    module = node.module OR ""
    is_relative = node.level > 0
    
    # v2.0: Relative import resolution
    IF is_relative:
        resolved_module = CALL _resolve_relative_import(module, node.level)
    ELSE:
        resolved_module = module
    
    FOR EACH alias IN node.names:
        APPEND TO self.deps.imports: {
            module: module,
            name: alias.name,
            alias: alias.asname,
            line: node.lineno,
            is_relative: is_relative,
            level: node.level IF is_relative ELSE 0,
            resolved_module: resolved_module
        }
    
    CONTINUE visiting children
```

### visit_ClassDef — Process classes (v2.0: metaclasses)

```pseudo
FUNCTION visit_ClassDef(node):
    """
    Processes class definition with metaclass detection.
    """
    # Extract base classes
    bases = [GET_NAME(base) FOR base IN node.bases]
    
    # v2.0: Metaclass detection
    metaclass = None
    FOR EACH keyword IN node.keywords:
        IF keyword.arg == "metaclass":
            metaclass = GET_NAME(keyword.value)
    
    # v2.0: Dynamic behavior detection
    has_dynamic_behavior = metaclass IS NOT None
    FOR EACH item IN node.body:
        IF item IS FunctionDef AND item.name IN ["__new__", "__init_subclass__", "__class_getitem__"]:
            has_dynamic_behavior = True
            BREAK
    
    # v2.0: Extract class decorators
    class_decorators = [_analyze_decorator(d) FOR d IN node.decorator_list]
    
    APPEND TO self.deps.class_hierarchy: {
        class: node.name,
        bases: bases,
        metaclass: metaclass,
        has_dynamic_behavior: has_dynamic_behavior,
        decorators: class_decorators,
        line: node.lineno
    }
    
    # Add to exports if public
    IF NOT node.name.startswith("_"):
        APPEND node.name TO self.deps.exports
    
    # Continue traversal with updated context
    old_class = self.current_class
    self.current_class = node.name
    CONTINUE visiting children
    self.current_class = old_class
```

### visit_FunctionDef — Process functions (v2.0: decorators with arguments)

```pseudo
FUNCTION visit_FunctionDef(node):
    """
    Processes function definition with full decorator analysis.
    """
    # v2.0: Analysis of decorators with arguments
    decorators_info = [_analyze_decorator(d) FOR d IN node.decorator_list]
    
    # Extract function arguments
    args_info = _extract_function_args(node.args)
    
    APPEND TO self.deps.function_definitions: {
        name: node.name,
        args: args_info,
        decorators: decorators_info,
        line: node.lineno,
        is_async: False,
        class: self.current_class
    }
    
    # Add to exports if public
    IF NOT node.name.startswith("_"):
        APPEND node.name TO self.deps.exports
    
    # Entry point check
    IF node.name == "main":
        APPEND TO self.deps.entry_points: {
            type: "main_function",
            name: node.name,
            line: node.lineno
        }
    
    # Check for CLI arguments inside function
    FOR EACH child IN ast.walk(node):
        IF child IS Call AND "argparse" IN GET_CALL_NAME(child):
            CALL _analyze_cli_args(node)
            BREAK
    
    # Continue traversal with updated context
    old_function = self.current_function
    self.current_function = node.name
    CONTINUE visiting children
    self.current_function = old_function
```

### visit_AsyncFunctionDef — Process async functions (v2.0)

```pseudo
FUNCTION visit_AsyncFunctionDef(node):
    """
    Similar to visit_FunctionDef, but for async def.
    """
    decorators_info = [_analyze_decorator(d) FOR d IN node.decorator_list]
    args_info = _extract_function_args(node.args)
    
    APPEND TO self.deps.function_definitions: {
        name: node.name,
        args: args_info,
        decorators: decorators_info,
        line: node.lineno,
        is_async: True,  # Difference from sync functions
        class: self.current_class
    }
    
    IF NOT node.name.startswith("_"):
        APPEND node.name TO self.deps.exports
    
    CONTINUE visiting children
```

### visit_Call — Process function calls

```pseudo
FUNCTION visit_Call(node):
    func_name = GET_CALL_NAME(node)
    
    IF func_name:
        # File operations detection
        IF func_name IN ["open", "Path", "read", "write", "load", "dump"]:
            CALL _analyze_file_operation(node, func_name)
        
        # Config loading detection
        ELIF "config" OR "yaml" OR "json" IN func_name.lower():
            CALL _analyze_config_operation(node, func_name)
        
        # Environment variables detection
        ELIF "getenv" OR "environ" IN func_name:
            CALL _analyze_env_var(node, func_name)
        
        # API calls detection
        ELIF "request" OR "post" OR "api" OR "client" IN func_name.lower():
            CALL _analyze_api_call(node, func_name)
        
        # Subprocess detection
        ELIF "subprocess" OR "Popen" OR "run" OR "call" OR "system" IN func_name:
            CALL _analyze_subprocess(node, func_name)
        
        # Record function call
        APPEND TO self.deps.function_calls: {
            function: func_name,
            line: node.lineno,
            context: self.current_function OR self.current_class
        }
    
    CONTINUE visiting children
```

### Helper methods

```pseudo
FUNCTION _extract_function_args(args: ast.arguments) -> LIST[ArgInfo]:
    """Extracts information about function arguments."""
    result = []
    
    # Regular arguments
    FOR EACH arg IN args.args:
        arg_info = {name: arg.arg, type: "arg"}
        IF arg.annotation:
            arg_info.annotation = GET_NAME(arg.annotation)
        APPEND arg_info TO result
    
    # *args
    IF args.vararg:
        APPEND {name: args.vararg.arg, type: "vararg"} TO result
    
    # **kwargs
    IF args.kwarg:
        APPEND {name: args.kwarg.arg, type: "kwarg"} TO result
    
    RETURN result

FUNCTION _get_value(node: ast.expr) -> ANY:
    """
    Extracts Python value from AST node.
    Supports: constants, names, lists, dicts, calls.
    """
    MATCH node:
        ast.Constant -> RETURN node.value
        ast.Num      -> RETURN node.n      # Python 3.7 compatibility
        ast.Str      -> RETURN node.s      # Python 3.7 compatibility
        ast.Name     -> RETURN node.id
        ast.List     -> RETURN [_get_value(elt) FOR elt IN node.elts]
        ast.Tuple    -> RETURN tuple(_get_value(elt) FOR elt IN node.elts)
        ast.Dict     -> RETURN {_get_value(k): _get_value(v) FOR k, v IN zip(node.keys, node.values) IF k}
        ast.Attribute -> RETURN GET_NAME(node)
        ast.Call     -> RETURN "{GET_NAME(node.func)}(...)"
        _            -> RETURN str(ast.dump(node))

FUNCTION _analyze_file_operation(node, func_name):
    IF node.args:
        path = GET_NAME(node.args[0])
        operation = "read" IF "read" OR "load" IN func_name ELSE "write"
        
        target = self.deps.file_reads IF operation == "read" ELSE self.deps.file_writes
        APPEND TO target: {path: path, operation: func_name, line: node.lineno}

FUNCTION _analyze_config_operation(node, func_name):
    IF node.args:
        config_file = GET_NAME(node.args[0])
        file_type = DETECT from func_name (yaml/json/unknown)
        APPEND TO self.deps.config_files: {file: config_file, type: file_type, operation: func_name, line: node.lineno}

FUNCTION _analyze_env_var(node, func_name):
    IF node.args:
        var_name = GET_NAME(node.args[0])
        default = GET_NAME(node.args[1]) IF LENGTH(node.args) > 1 ELSE None
        APPEND TO self.deps.env_vars: {var: var_name, default: default, line: node.lineno}

FUNCTION _analyze_api_call(node, func_name):
    service = DETECT from func_name (OpenAI/Anthropic/Google/unknown)
    endpoint = GET_NAME(node.args[0]) IF node.args ELSE None
    APPEND TO self.deps.api_calls: {service: service, endpoint: endpoint, function: func_name, line: node.lineno}

FUNCTION _analyze_subprocess(node, func_name):
    IF node.args:
        command = GET_NAME(node.args[0])
        APPEND TO self.deps.subprocess_calls: {command: command, function: func_name, line: node.lineno}

FUNCTION _analyze_cli_args(node):
    FOR EACH child IN ast.walk(node):
        IF child IS Call AND "add_argument" IN GET_CALL_NAME(child):
            IF child.args:
                arg_name = GET_NAME(child.args[0])
                APPEND TO self.deps.cli_args: {arg: arg_name, line: child.lineno}
```

---

## ALGORITHM: analyze_file(file_path, project_root)

```pseudo
FUNCTION analyze_file(file_path: PATH, project_root: PATH = None) -> DependencyInfo?:
    TRY:
        # Step 1: Read source code
        source_code = READ file_path AS UTF-8
        
        # Step 2: Parse into AST
        tree = ast.parse(source_code, filename=str(file_path))
        
        # Step 3: AST analysis
        analyzer = NEW DependencyAnalyzer(file_path, project_root)
        analyzer.visit(tree)
        
        # Step 4 (v2.0): Dynamic import detection
        detector = NEW DynamicImportDetector()
        dynamic_imports = detector.detect_dynamic_imports(source_code, file_path)
        analyzer.deps.dynamic_imports = dynamic_imports
        
        # Step 5: Check for __main__ entry point
        IF "__name__" IN source_code AND "__main__" IN source_code:
            main_pos = FIND "__main__" IN source_code
            line_num = COUNT newlines before main_pos + 1
            APPEND TO analyzer.deps.entry_points: {
                type: "main_guard",
                name: "__main__",
                line: line_num
            }
        
        # Step 6 (v2.0): Metadata generation
        analyzer.deps.metadata = {
            total_functions: LENGTH(analyzer.deps.function_definitions),
            total_classes: LENGTH(analyzer.deps.class_hierarchy),
            total_imports: LENGTH(analyzer.deps.imports),
            has_dynamic_imports: LENGTH(dynamic_imports) > 0,
            has_dynamic_behavior: ANY(c.has_dynamic_behavior FOR c IN analyzer.deps.class_hierarchy),
            lines_of_code: COUNT newlines IN source_code + 1,
            file_size_bytes: LENGTH(source_code AS bytes)
        }
        
        RETURN analyzer.deps
        
    CATCH SyntaxError AS e:
        LOG ERROR "Syntax error in {file_path}: {e}"
        RETURN None
    CATCH Exception AS e:
        LOG ERROR "Error analyzing {file_path}: {e}"
        RETURN None
```

---

## ALGORITHM: analyze_directory(dir_path, output_dir, project_root)

```pseudo
FUNCTION analyze_directory(dir_path: PATH, output_dir: PATH, project_root: PATH = None):
    # Create output directory
    CREATE output_dir IF NOT EXISTS
    
    files_processed = 0
    files_failed = 0
    
    # Recursive traversal of Python files
    FOR EACH py_file IN GLOB(dir_path, "**/*.py"):
        # Skip unwanted directories
        IF "__pycache__" OR "vllm-latest" IN py_file:
            CONTINUE
        
        LOG INFO "Analyzing: {py_file}"
        deps = CALL analyze_file(py_file, project_root)
        
        IF deps:
            # Save to JSON
            relative_path = py_file.relative_to(dir_path.parent)
            output_file = output_dir / "{relative_path.stem}_dependencies.json"
            CREATE output_file.parent IF NOT EXISTS
            
            WRITE deps AS JSON TO output_file (indent=2, ensure_ascii=False)
            LOG INFO "  → Saved to: {output_file}"
            files_processed += 1
        ELSE:
            files_failed += 1
    
    LOG INFO "Analysis complete: {files_processed} processed, {files_failed} failed"
```

---

## CLI INTERFACE

```pseudo
ARGUMENTS:
    --target PATH       # Single file analysis
    --target-dir PATH   # Directory analysis  
    --all               # Entire project analysis (processing/, utils/, scripts/, docs/automation/)
    --output-dir PATH   # Output directory (default: docs/memory/dependencies)
    --version           # Show version (v2.0)

ENTRY POINT main():
    PARSE arguments
    
    IF args.version:
        PRINT "analyze_dependencies.py v{ANALYSIS_VERSION}"
        RETURN
    
    base_dir = PROJECT_ROOT  # Parent of docs/automation/
    output_dir = base_dir / args.output_dir
    
    IF args.target:
        target_file = base_dir / args.target
        IF NOT target_file.exists():
            PRINT ERROR "File not found: {target_file}"
            RETURN
        
        deps = CALL analyze_file(target_file, base_dir)
        IF deps:
            output_file = output_dir / "{target_file.stem}_dependencies.json"
            CREATE output_file.parent IF NOT EXISTS
            WRITE deps AS JSON TO output_file
            
            PRINT "✅ Analysis saved to: {output_file}"
            PRINT "   Functions: {deps.metadata.total_functions}"
            PRINT "   Classes: {deps.metadata.total_classes}"
            PRINT "   Imports: {deps.metadata.total_imports}"
            IF deps.dynamic_imports:
                PRINT "   ⚠️  Dynamic imports: {LENGTH(deps.dynamic_imports)}"
    
    ELIF args.target_dir:
        target_dir = base_dir / args.target_dir
        IF NOT target_dir.exists():
            PRINT ERROR "Directory not found: {target_dir}"
            RETURN
        CALL analyze_directory(target_dir, output_dir, base_dir)
    
    ELIF args.all:
        FOR EACH subdir IN ["processing", "utils", "scripts", "docs/automation"]:
            target_dir = base_dir / subdir
            IF target_dir.exists():
                PRINT "\n=== Analyzing {subdir}/ ==="
                CALL analyze_directory(target_dir, output_dir / subdir.replace("/", "_"), base_dir)
    
    ELSE:
        PRINT help
```

## USAGE EXAMPLES

```bash
# Analyze single file
python3 docs/automation/analyze_dependencies.py --target utils/dual_memory.py

# Analyze directory
python3 docs/automation/analyze_dependencies.py --target-dir processing/

# Analyze entire project
python3 docs/automation/analyze_dependencies.py --all

# Custom output directory
python3 docs/automation/analyze_dependencies.py --target file.py --output-dir custom/path

# Version check
python3 docs/automation/analyze_dependencies.py --version
```

---

## OUTPUT JSON (example)

```json
{
  "file_path": "utils/dual_memory.py",
  "imports": [
    {"module": "json", "alias": null, "line": 5, "is_relative": false, "resolved_module": "json"},
    {"module": "numpy", "name": "array", "alias": "np_array", "line": 6, "is_relative": false, "resolved_module": "numpy"}
  ],
  "function_definitions": [
    {
      "name": "search",
      "args": [{"name": "self", "type": "arg"}, {"name": "query", "type": "arg", "annotation": "str"}],
      "decorators": [{"name": "lru_cache", "args": [], "kwargs": {"maxsize": 128}}],
      "line": 45,
      "is_async": false,
      "class": "DualMemoryIndex"
    }
  ],
  "class_hierarchy": [
    {
      "class": "DualMemoryIndex",
      "bases": ["BaseIndex"],
      "metaclass": null,
      "has_dynamic_behavior": false,
      "decorators": [],
      "line": 30
    }
  ],
  "dynamic_imports": [
    {
      "type": "dynamic_import",
      "pattern": "importlib",
      "module": "optional_module",
      "line": 15,
      "confidence": "high",
      "warning": "Dynamic import detected - verify manually",
      "is_variable": false
    }
  ],
  "metadata": {
    "total_functions": 12,
    "total_classes": 2,
    "total_imports": 8,
    "has_dynamic_imports": true,
    "has_dynamic_behavior": false,
    "lines_of_code": 450,
    "file_size_bytes": 15234
  },
  "analysis_version": "2.0",
  "timestamp": "2025-12-12T12:55:00+07:00"
}
```

<!--/TAG:pseudo_analyze_dependencies-->
