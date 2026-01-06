#!/usr/bin/env python3
"""
Dependency Analyzer v2.0 - Enhanced dependency extraction from Python files

<!--TAG:tool_analyze_dependencies-->

PURPOSE:
    Performs algorithmic analysis of Python code to extract dependency layers:
    Code, Configuration, Data, External, and Orchestration.
    
    v2.0 Enhancements (TICKET #01):
    - Decorator argument extraction
    - Relative import resolution
    - Dynamic import detection
    - Metaclass detection
    - Enhanced metadata output

DOCUMENTATION:
    Spec: docs/specs/Automation_Tools_Spec.md
    Wiki: docs/wiki/09_Documentation_System.md
    Ticket: docs/technical_debt/tickets_2025_12_11/TICKET_01_analyze_dependencies.md
    Pseudocode: docs/automation/analyze_dependencies.pseudo.md

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger (isolated paranoid logging)
    Standard Library:
        - ast (AST parsing)
        - json (output serialization)
        - re (dynamic import detection via regex)
        - dataclasses (data structures)
        - pathlib.Path (file path handling)
    Data:
        - Input: *.py files
        - Output: docs/memory/dependencies/*_dependencies.json

RECENT CHANGES:
    2025-12-11: v2.0 - Added decorator args, dynamic imports, metaclass detection
                (see docs/technical_debt/tickets_2025_12_11/TICKET_01_analyze_dependencies.md)
    2025-12-12: Updated pseudocode to v2.0, added DEPENDENCIES section

TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:analysis--> <!--TAG:automation--> <!--TAG:analysis--> <!--TAG:dependencies-->

<!--/TAG:tool_analyze_dependencies-->
"""

import ast
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from datetime import datetime

# Add project root to path
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.docs_logger import DocsLogger

# Initialize logger
logger = DocsLogger("analyze_dependencies")

# Analysis version
ANALYSIS_VERSION = "2.0"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class DependencyInfo:
    """
    Complete dependency information for a Python file.
    
    v2.0: Added function_definitions, dynamic_imports, resolved_imports, metadata
    """
    file_path: str
    
    # Code Layer
    imports: List[Dict[str, Any]] = field(default_factory=list)  # [{module, name, alias, line, is_relative, resolved_module}]
    function_calls: List[Dict[str, Any]] = field(default_factory=list)  # [{function, module, line}]
    class_hierarchy: List[Dict[str, Any]] = field(default_factory=list)  # [{class, bases, metaclass, has_dynamic_behavior}]
    exports: List[str] = field(default_factory=list)  # Public functions/classes
    
    # v2.0: Enhanced function definitions with decorators
    function_definitions: List[Dict[str, Any]] = field(default_factory=list)  # [{name, args, decorators, line}]
    
    # v2.0: Dynamic imports detected via regex
    dynamic_imports: List[Dict[str, Any]] = field(default_factory=list)  # [{type, pattern, module, line, confidence}]
    
    # Configuration Layer
    config_files: List[Dict[str, Any]] = field(default_factory=list)  # [{file, type, line}]
    env_vars: List[Dict[str, Any]] = field(default_factory=list)  # [{var, default, line}]
    cli_args: List[Dict[str, Any]] = field(default_factory=list)  # [{arg, type, help}]
    
    # Data Layer
    file_reads: List[Dict[str, Any]] = field(default_factory=list)  # [{path, line, operation}]
    file_writes: List[Dict[str, Any]] = field(default_factory=list)  # [{path, line, operation}]
    data_transforms: List[Dict[str, str]] = field(default_factory=list)  # [{input_type, output_type, function}]
    
    # External Layer
    api_calls: List[Dict[str, Any]] = field(default_factory=list)  # [{service, endpoint, line}]
    system_commands: List[Dict[str, Any]] = field(default_factory=list)  # [{command, line}]
    external_libs: List[str] = field(default_factory=list)  # Third-party libraries
    
    # Orchestration Layer
    entry_points: List[Dict[str, str]] = field(default_factory=list)  # [{type, name, line}]
    subprocess_calls: List[Dict[str, Any]] = field(default_factory=list)  # [{script, args, line}]
    
    # v2.0: Metadata for indexing
    metadata: Dict[str, Any] = field(default_factory=dict)
    analysis_version: str = ANALYSIS_VERSION
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# TASK 2.1: Dynamic Import Detector
# ============================================================================

class DynamicImportDetector:
    """
    Detects dynamic import patterns that AST can't fully resolve.
    
    Uses regex to find:
    - importlib.import_module()
    - __import__()
    - Conditional imports (if ... import)
    """
    
    # Regex patterns for dynamic imports
    PATTERNS = {
        'importlib': r'importlib\.import_module\s*\(\s*["\']([^"\']+)["\']\s*\)',
        'importlib_var': r'importlib\.import_module\s*\(\s*(\w+)\s*\)',
        '__import__': r'__import__\s*\(\s*["\']([^"\']+)["\']\s*\)',
        '__import___var': r'__import__\s*\(\s*(\w+)\s*\)',
        'exec_import': r'exec\s*\(\s*["\']import\s+(\w+)["\']\s*\)',
        'conditional_import': r'if\s+[^:]+:\s*\n\s*import\s+(\w+)',
        'try_import': r'try:\s*\n\s*import\s+(\w+)',
    }
    
    def detect_dynamic_imports(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Detect dynamic imports via regex + heuristics.
        
        Args:
            source_code: Python source code as string
            file_path: Path to the file being analyzed
            
        Returns:
            List of detected dynamic import patterns
        """
        dynamic_imports = []
        
        for pattern_name, regex in self.PATTERNS.items():
            try:
                matches = re.finditer(regex, source_code, re.MULTILINE)
                for match in matches:
                    # Get module name from capture group
                    module_name = match.group(1) if match.groups() else 'unknown'
                    
                    # Calculate line number
                    line_num = source_code[:match.start()].count('\n') + 1
                    
                    # Determine confidence based on pattern type
                    if '_var' in pattern_name:
                        confidence = 'low'  # Variable - can't know the value
                        warning = 'Dynamic import with variable - cannot resolve statically'
                    elif 'conditional' in pattern_name or 'try' in pattern_name:
                        confidence = 'medium'  # Conditional - may or may not execute
                        warning = 'Conditional import - may not always be executed'
                    else:
                        confidence = 'high'  # Literal string - we know the module
                        warning = 'Dynamic import detected - verify manually'
                    
                    dynamic_imports.append({
                        'type': 'dynamic_import',
                        'pattern': pattern_name.replace('_var', ''),
                        'module': module_name,
                        'line': line_num,
                        'confidence': confidence,
                        'warning': warning,
                        'is_variable': '_var' in pattern_name
                    })
            except re.error as e:
                logger.warning(f"Regex error for pattern {pattern_name}: {e}")
                continue
        
        return dynamic_imports


# ============================================================================
# MAIN ANALYZER CLASS
# ============================================================================

class DependencyAnalyzer(ast.NodeVisitor):
    """
    AST visitor to extract dependencies from Python source code.
    
    v2.0 Enhancements:
    - Decorator argument extraction
    - Relative import resolution
    - Metaclass detection
    """
    
    def __init__(self, file_path: str, project_root: Path = None):
        """
        Initialize the analyzer.
        
        Args:
            file_path: Path to the file being analyzed
            project_root: Project root for relative import resolution
        """
        self.file_path = file_path
        self.project_root = project_root or Path(file_path).parent.parent
        
        # Initialize dependency info
        self.deps = DependencyInfo(file_path=file_path)
        
        # Context tracking
        self.current_class = None
        self.current_function = None
        
    # =========================================================================
    # TASK 1.1: Enhanced Decorator Analysis
    # =========================================================================
    
    def _analyze_decorator(self, decorator_node: ast.expr) -> Dict[str, Any]:
        """
        Extract decorator name and arguments.
        
        Args:
            decorator_node: AST node for the decorator
            
        Returns:
            Dict with decorator name, args, and kwargs
        """
        if isinstance(decorator_node, ast.Name):
            # Simple decorator: @property
            return {
                'name': decorator_node.id,
                'args': [],
                'kwargs': {}
            }
        elif isinstance(decorator_node, ast.Attribute):
            # Attribute decorator: @module.decorator
            return {
                'name': self._get_name(decorator_node),
                'args': [],
                'kwargs': {}
            }
        elif isinstance(decorator_node, ast.Call):
            # Decorator with arguments: @lru_cache(maxsize=128)
            dec_name = self._get_name(decorator_node.func)
            
            # Extract positional arguments
            dec_args = []
            for arg in decorator_node.args:
                arg_value = self._get_value(arg)
                dec_args.append(arg_value)
            
            # Extract keyword arguments
            dec_kwargs = {}
            for keyword in decorator_node.keywords:
                if keyword.arg:  # Ignore **kwargs
                    dec_kwargs[keyword.arg] = self._get_value(keyword.value)
            
            return {
                'name': dec_name,
                'args': dec_args,
                'kwargs': dec_kwargs
            }
        
        return {'name': 'unknown', 'args': [], 'kwargs': {}}
    
    def _get_value(self, node: ast.expr) -> Any:
        """
        Extract value from AST node.
        
        Args:
            node: AST expression node
            
        Returns:
            Python value or string representation
        """
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # Python 3.7 compatibility
            return node.n
        elif isinstance(node, ast.Str):  # Python 3.7 compatibility
            return node.s
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            return [self._get_value(elt) for elt in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self._get_value(elt) for elt in node.elts)
        elif isinstance(node, ast.Dict):
            return {self._get_value(k): self._get_value(v) 
                    for k, v in zip(node.keys, node.values) if k}
        elif isinstance(node, ast.Attribute):
            return self._get_name(node)
        elif isinstance(node, ast.Call):
            return f"{self._get_name(node.func)}(...)"
        return str(ast.dump(node))
    
    # =========================================================================
    # TASK 1.2: Relative Import Resolution
    # =========================================================================
    
    def _resolve_relative_import(self, relative_module: str, level: int) -> str:
        """
        Resolve relative import to absolute module path.
        
        Args:
            relative_module: The relative module name (may be empty)
            level: Number of dots (1 = ., 2 = .., etc.)
            
        Returns:
            Absolute module path or original if can't resolve
        """
        try:
            file_path = Path(self.file_path)
            
            # Get package structure from file path
            if self.project_root and file_path.is_absolute():
                try:
                    relative_path = file_path.relative_to(self.project_root)
                    package_parts = list(relative_path.parts[:-1])  # Remove filename
                except ValueError:
                    package_parts = list(file_path.parts[:-1])
            else:
                package_parts = list(file_path.parts[:-1])
            
            # Go up 'level' directories
            if level > len(package_parts):
                logger.warning(f"Can't resolve import level {level} from {file_path}")
                return relative_module or ''
            
            # Calculate base package
            if level > 0:
                base_parts = package_parts[:-level] if level <= len(package_parts) else []
            else:
                base_parts = package_parts
            
            base_package = '.'.join(base_parts)
            
            # Combine with relative module
            if relative_module:
                if base_package:
                    return f"{base_package}.{relative_module}"
                return relative_module
            return base_package
            
        except Exception as e:
            logger.warning(f"Error resolving relative import: {e}")
            return relative_module or ''
    
    # =========================================================================
    # AST Visitors
    # =========================================================================
    
    def visit_Import(self, node: ast.Import):
        """Extract import statements."""
        for alias in node.names:
            self.deps.imports.append({
                'module': alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'is_relative': False,
                'resolved_module': alias.name
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """
        Extract from ... import statements with relative import resolution.
        """
        module = node.module or ''
        is_relative = node.level > 0
        
        # Resolve relative imports
        if is_relative:
            resolved_module = self._resolve_relative_import(module, node.level)
        else:
            resolved_module = module
        
        for alias in node.names:
            self.deps.imports.append({
                'module': module,
                'name': alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'is_relative': is_relative,
                'level': node.level if is_relative else 0,
                'resolved_module': resolved_module
            })
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Extract class definitions with metaclass detection (Task 2.2).
        """
        bases = [self._get_name(base) for base in node.bases]
        
        # TASK 2.2: Detect metaclass
        metaclass = None
        for keyword in node.keywords:
            if keyword.arg == 'metaclass':
                metaclass = self._get_name(keyword.value)
        
        # Detect dynamic behavior indicators
        has_dynamic_behavior = metaclass is not None
        
        # Check for __new__, __init_subclass__, etc.
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name in ('__new__', '__init_subclass__', '__class_getitem__'):
                    has_dynamic_behavior = True
                    break
        
        # Extract decorators for class
        class_decorators = [self._analyze_decorator(d) for d in node.decorator_list]
        
        self.deps.class_hierarchy.append({
            'class': node.name,
            'bases': bases,
            'metaclass': metaclass,
            'has_dynamic_behavior': has_dynamic_behavior,
            'decorators': class_decorators,
            'line': node.lineno
        })
        
        # Check if exported (not starting with _)
        if not node.name.startswith('_'):
            self.deps.exports.append(node.name)
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Extract function definitions with decorator analysis (Task 1.1).
        """
        # TASK 1.1: Enhanced decorator analysis
        decorators_info = [self._analyze_decorator(d) for d in node.decorator_list]
        
        # Extract function arguments
        args_info = self._extract_function_args(node.args)
        
        # Store function definition with enhanced info
        self.deps.function_definitions.append({
            'name': node.name,
            'args': args_info,
            'decorators': decorators_info,
            'line': node.lineno,
            'is_async': False,
            'class': self.current_class
        })
        
        # Check if exported
        if not node.name.startswith('_'):
            self.deps.exports.append(node.name)
        
        # Check for entry points
        if node.name == 'main':
            self.deps.entry_points.append({
                'type': 'main_function',
                'name': node.name,
                'line': node.lineno
            })
        
        # Check for CLI argument parsing
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func_name = self._get_call_name(child)
                if func_name and ('argparse' in func_name or 'ArgumentParser' in func_name):
                    self._analyze_cli_args(node)
                    break
        
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Extract async function definitions."""
        decorators_info = [self._analyze_decorator(d) for d in node.decorator_list]
        args_info = self._extract_function_args(node.args)
        
        self.deps.function_definitions.append({
            'name': node.name,
            'args': args_info,
            'decorators': decorators_info,
            'line': node.lineno,
            'is_async': True,
            'class': self.current_class
        })
        
        if not node.name.startswith('_'):
            self.deps.exports.append(node.name)
        
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def _extract_function_args(self, args: ast.arguments) -> List[Dict[str, Any]]:
        """Extract function argument information."""
        result = []
        
        # Regular arguments
        for arg in args.args:
            arg_info = {'name': arg.arg, 'type': 'arg'}
            if arg.annotation:
                arg_info['annotation'] = self._get_name(arg.annotation)
            result.append(arg_info)
        
        # *args
        if args.vararg:
            result.append({'name': args.vararg.arg, 'type': 'vararg'})
        
        # **kwargs
        if args.kwarg:
            result.append({'name': args.kwarg.arg, 'type': 'kwarg'})
        
        return result
    
    def visit_Call(self, node: ast.Call):
        """Extract function calls and detect special patterns."""
        func_name = self._get_call_name(node)
        
        if func_name:
            # Detect file operations
            if func_name in ['open', 'Path', 'read', 'write', 'load', 'dump']:
                self._analyze_file_operation(node, func_name)
            
            # Detect config loading
            elif 'config' in func_name.lower() or 'yaml' in func_name.lower() or 'json' in func_name.lower():
                self._analyze_config_operation(node, func_name)
            
            # Detect environment variables
            elif 'getenv' in func_name or 'environ' in func_name:
                self._analyze_env_var(node, func_name)
            
            # Detect API calls
            elif any(x in func_name.lower() for x in ['request', 'post', 'api', 'client']):
                self._analyze_api_call(node, func_name)
            
            # Detect subprocess calls
            elif any(x in func_name for x in ['subprocess', 'Popen', 'run', 'call', 'system']):
                self._analyze_subprocess(node, func_name)
            
            # Record function call
            self.deps.function_calls.append({
                'function': func_name,
                'line': node.lineno,
                'context': self.current_function or self.current_class
            })
        
        self.generic_visit(node)
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Extract function name from Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return f"{self._get_name(node.func.value)}.{node.func.attr}"
        return None
    
    def _get_name(self, node: ast.expr) -> Optional[str]:
        """Extract name from various node types."""
        if node is None:
            return None
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._get_name(node.value)
            if value_name:
                return f"{value_name}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Subscript):
            value_name = self._get_name(node.value)
            return f"{value_name}[...]" if value_name else None
        return None
    
    def _analyze_file_operation(self, node: ast.Call, func_name: str):
        """Analyze file I/O operations."""
        if node.args:
            path = self._get_name(node.args[0])
            operation = 'read' if 'read' in func_name or 'load' in func_name else 'write'
            
            target = self.deps.file_reads if operation == 'read' else self.deps.file_writes
            target.append({
                'path': path,
                'operation': func_name,
                'line': node.lineno
            })
    
    def _analyze_config_operation(self, node: ast.Call, func_name: str):
        """Analyze configuration file loading."""
        if node.args:
            config_file = self._get_name(node.args[0])
            file_type = 'yaml' if 'yaml' in func_name.lower() else 'json' if 'json' in func_name.lower() else 'unknown'
            
            self.deps.config_files.append({
                'file': config_file,
                'type': file_type,
                'operation': func_name,
                'line': node.lineno
            })
    
    def _analyze_env_var(self, node: ast.Call, func_name: str):
        """Analyze environment variable access."""
        if node.args:
            var_name = self._get_name(node.args[0])
            default = self._get_name(node.args[1]) if len(node.args) > 1 else None
            
            self.deps.env_vars.append({
                'var': var_name,
                'default': default,
                'line': node.lineno
            })
    
    def _analyze_api_call(self, node: ast.Call, func_name: str):
        """Analyze API calls."""
        service = 'unknown'
        endpoint = None
        
        # Detect service from context
        if 'openai' in func_name.lower():
            service = 'OpenAI'
        elif 'anthropic' in func_name.lower() or 'claude' in func_name.lower():
            service = 'Anthropic'
        elif 'google' in func_name.lower() or 'gemini' in func_name.lower():
            service = 'Google'
        
        if node.args:
            endpoint = self._get_name(node.args[0])
        
        self.deps.api_calls.append({
            'service': service,
            'endpoint': endpoint,
            'function': func_name,
            'line': node.lineno
        })
    
    def _analyze_subprocess(self, node: ast.Call, func_name: str):
        """Analyze subprocess calls."""
        if node.args:
            command = self._get_name(node.args[0])
            
            self.deps.subprocess_calls.append({
                'command': command,
                'function': func_name,
                'line': node.lineno
            })
    
    def _analyze_cli_args(self, node: ast.FunctionDef):
        """Analyze CLI argument definitions."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func_name = self._get_call_name(child)
                if func_name and 'add_argument' in func_name:
                    if child.args:
                        arg_name = self._get_name(child.args[0])
                        self.deps.cli_args.append({
                            'arg': arg_name,
                            'line': child.lineno
                        })


# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def analyze_file(file_path: Path, project_root: Path = None) -> Optional[DependencyInfo]:
    """
    Analyze a single Python file.
    
    Args:
        file_path: Path to the Python file
        project_root: Project root for relative import resolution
        
    Returns:
        DependencyInfo object or None on error
    """
    try:
        # Read source code
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse AST
        tree = ast.parse(source, filename=str(file_path))
        
        # Run AST analyzer
        analyzer = DependencyAnalyzer(str(file_path), project_root)
        analyzer.visit(tree)
        
        # TASK 2.1: Detect dynamic imports
        detector = DynamicImportDetector()
        dynamic_imports = detector.detect_dynamic_imports(source, str(file_path))
        analyzer.deps.dynamic_imports = dynamic_imports
        
        # Check for __main__ entry point
        if '__name__' in source and '__main__' in source:
            main_pos = source.find('__main__')
            analyzer.deps.entry_points.append({
                'type': 'main_guard',
                'name': '__main__',
                'line': source[:main_pos].count('\n') + 1
            })
        
        # Generate metadata
        analyzer.deps.metadata = {
            'total_functions': len(analyzer.deps.function_definitions),
            'total_classes': len(analyzer.deps.class_hierarchy),
            'total_imports': len(analyzer.deps.imports),
            'has_dynamic_imports': len(dynamic_imports) > 0,
            'has_dynamic_behavior': any(
                c.get('has_dynamic_behavior') for c in analyzer.deps.class_hierarchy
            ),
            'lines_of_code': source.count('\n') + 1,
            'file_size_bytes': len(source.encode('utf-8'))
        }
        
        return analyzer.deps
        
    except SyntaxError as e:
        logger.error(f"Syntax error in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
        return None


def analyze_directory(dir_path: Path, output_dir: Path, project_root: Path = None):
    """
    Analyze all Python files in a directory.
    
    Args:
        dir_path: Directory to analyze
        output_dir: Output directory for JSON files
        project_root: Project root for relative import resolution
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    files_processed = 0
    files_failed = 0
    
    for py_file in dir_path.rglob('*.py'):
        # Skip unwanted directories
        if '__pycache__' in str(py_file) or 'vllm-latest' in str(py_file):
            continue
        
        logger.info(f"Analyzing: {py_file}")
        deps = analyze_file(py_file, project_root)
        
        if deps:
            # Save to JSON
            relative_path = py_file.relative_to(dir_path.parent)
            output_file = output_dir / f"{relative_path.stem}_dependencies.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(deps), f, indent=2, ensure_ascii=False)
            
            logger.info(f"  → Saved to: {output_file}")
            files_processed += 1
        else:
            files_failed += 1
    
    logger.info(f"Analysis complete: {files_processed} files processed, {files_failed} failed")


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main entry point for CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze Python file dependencies (v2.0)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file
  python3 analyze_dependencies.py --target utils/dual_memory.py
  
  # Directory
  python3 analyze_dependencies.py --target-dir processing/
  
  # Entire project
  python3 analyze_dependencies.py --all
  
  # With custom output
  python3 analyze_dependencies.py --target file.py --output-dir custom/path

v2.0 Features:
  - Decorator argument extraction
  - Relative import resolution
  - Dynamic import detection
  - Metaclass detection
"""
    )
    
    parser.add_argument('--target', type=str, help='Single file to analyze')
    parser.add_argument('--target-dir', type=str, help='Directory to analyze')
    parser.add_argument('--all', action='store_true', help='Analyze entire project')
    parser.add_argument('--output-dir', type=str, default='docs/memory/dependencies',
                       help='Output directory for dependency JSON files')
    parser.add_argument('--version', action='store_true', help='Show version')
    
    args = parser.parse_args()
    
    if args.version:
        print(f"analyze_dependencies.py v{ANALYSIS_VERSION}")
        return
    
    base_dir = Path(__file__).parent.parent  # Project root
    output_dir = base_dir / args.output_dir
    
    if args.target:
        target_file = base_dir / args.target
        if not target_file.exists():
            print(f"Error: File not found: {target_file}")
            return
        
        deps = analyze_file(target_file, base_dir)
        if deps:
            output_file = output_dir / f"{target_file.stem}_dependencies.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(deps), f, indent=2, ensure_ascii=False)
            print(f"✅ Analysis saved to: {output_file}")
            print(f"   Functions: {deps.metadata.get('total_functions', 0)}")
            print(f"   Classes: {deps.metadata.get('total_classes', 0)}")
            print(f"   Imports: {deps.metadata.get('total_imports', 0)}")
            if deps.dynamic_imports:
                print(f"   ⚠️  Dynamic imports: {len(deps.dynamic_imports)}")
    
    elif args.target_dir:
        target_dir = base_dir / args.target_dir
        if not target_dir.exists():
            print(f"Error: Directory not found: {target_dir}")
            return
        analyze_directory(target_dir, output_dir, base_dir)
    
    elif args.all:
        for subdir in ['processing', 'utils', 'scripts', 'docs/automation']:
            target_dir = base_dir / subdir
            if target_dir.exists():
                print(f"\n=== Analyzing {subdir}/ ===")
                analyze_directory(target_dir, output_dir / subdir.replace('/', '_'), base_dir)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
