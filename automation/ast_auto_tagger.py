#!/usr/bin/env python3
"""
AST Auto-Tagger - Automatically generate tags from Python code structure

<!--TAG:tool_ast_auto_tagger-->

PURPOSE:
    Analyzes Python files using AST to automatically generate semantic tags.
    Detects components, types, and features from code structure.
    Supports draft mode for review before applying.

DOCUMENTATION:
    Spec: docs/specs/tag_schema.yaml
    Wiki: docs/wiki/hierarchical_tags.md
    Related: docs/automation/tag_validator.py, docs/automation/tag_normalizer.py

TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:tagging--> <!--TAG:feature:validation-->

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger.DocsLogger (isolated paranoid logging)
        - yaml (YAML parsing for tag schema)
        - ast (Python AST parsing and analysis)
    Config:
        - docs/specs/tag_schema.yaml (tag validation schema)
    Data:
        - Input: Python files to analyze
        - Output: Modified files with injected tags (--apply mode)
    External:
        - None (fully self-contained)

USAGE:
    python3 ast_auto_tagger.py --file path/to/file.py --preview
    python3 ast_auto_tagger.py --directory utils/ --apply
    python3 ast_auto_tagger.py --all --report
    python3 ast_auto_tagger.py --file script.py --json

RECENT CHANGES:
    2025-12-11: Initial implementation as part of Hierarchical Tag System (TICKET_10)
    2025-12-12: Audit compliance fixes - added DEPENDENCIES section

<!--/TAG:tool_ast_auto_tagger-->
"""

import os
import re
import sys
import ast
import yaml
import argparse
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field

# Add project root to path
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from utils.docs_logger import DocsLogger
    logger = DocsLogger("ast_auto_tagger")
except ImportError:
    import logging
    logger = logging.getLogger("ast_auto_tagger")
    logging.basicConfig(level=logging.INFO)


@dataclass
class TagSuggestion:
    """A suggested tag with confidence score."""
    tag: str
    confidence: float  # 0.0 - 1.0
    reason: str
    source: str  # path, import, name, content


@dataclass 
class FileTagAnalysis:
    """Complete tag analysis for a file."""
    file_path: str
    existing_tags: List[str] = field(default_factory=list)
    suggested_tags: List[TagSuggestion] = field(default_factory=list)
    primary_tag: Optional[str] = None
    classes_found: List[str] = field(default_factory=list)
    functions_found: List[str] = field(default_factory=list)
    imports_found: List[str] = field(default_factory=list)


class ASTAutoTagger:
    """
    Automatically generate semantic tags from Python file structure.
    
    <!--TAG:ASTAutoTagger:class-->
    
    Uses AST parsing to detect:
    - Component from file path
    - Type from content (script, class, function)
    - Features from imports and names
    """
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize tagger with schema.
        
        Args:
            schema_path: Path to tag_schema.yaml for validation.
        """
        # Find schema
        if schema_path is None:
            self.schema_path = Path(__file__).parent.parent / "specs" / "tag_schema.yaml"
        else:
            self.schema_path = Path(schema_path)
        
        # Load schema if available
        self.schema = self._load_schema()
        
        # Tag patterns for existing tag detection
        self.tag_pattern = re.compile(r'<!--TAG:([a-zA-Z0-9_:]+)-->')
        self.close_pattern = re.compile(r'<!--/TAG:([a-zA-Z0-9_:]+)-->')
        
        logger.info("ASTAutoTagger initialized")
    
    def _load_schema(self) -> Dict:
        """Load tag schema for validation."""
        if self.schema_path.exists():
            try:
                return yaml.safe_load(self.schema_path.read_text())
            except Exception as e:
                logger.warning(f"Could not load schema: {e}")
        return {}
    
    def analyze_file(self, file_path: Path) -> FileTagAnalysis:
        """
        Analyze a Python file and suggest tags.
        
        <!--TAG:analyze_file:method-->
        
        Args:
            file_path: Path to the Python file.
            
        Returns:
            FileTagAnalysis with existing and suggested tags.
        """
        # Initialize empty analysis result object with file path
        analysis = FileTagAnalysis(file_path=str(file_path))
        
        # Step 1: Read file content with UTF-8 encoding
        logger.info(f"Analyzing file", {"path": str(file_path)})
        try:
            # Read entire file content for parsing
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            # Log error and return empty analysis on read failure
            logger.error(f"Cannot read {file_path}: {e}")
            return analysis
        
        # Step 2: Extract existing tags using regex pattern
        # This finds all <!--TAG:xyz--> patterns already in the file
        analysis.existing_tags = self.tag_pattern.findall(content)
        logger.info(f"Found existing tags", {"count": len(analysis.existing_tags)})
        
        # Step 3: Parse file content into AST (Abstract Syntax Tree)
        try:
            # ast.parse() returns Module node as tree root
            tree = ast.parse(content)
        except SyntaxError as e:
            # Files with syntax errors can't be analyzed further
            logger.warning(f"Syntax error in {file_path}: {e}")
            return analysis
        
        # Step 4: Extract structural information from AST
        # Each extraction walks the tree looking for specific node types
        analysis.classes_found = self._extract_classes(tree)
        analysis.functions_found = self._extract_functions(tree)
        analysis.imports_found = self._extract_imports(tree)
        
        # Step 5: Generate tag suggestions from multiple sources
        # Sources: path, structure, imports, names, content (different confidence)
        analysis.suggested_tags = self._generate_suggestions(
            file_path, content, tree, analysis
        )
        
        # Step 6: Determine the primary identifier tag for this file
        # Used as the wrapper tag: <!--TAG:primary--> ... <!--/TAG:primary-->
        analysis.primary_tag = self._generate_primary_tag(file_path, analysis)
        
        # Log completion statistics
        logger.info(f"Analysis complete", {
            "classes": len(analysis.classes_found),
            "functions": len(analysis.functions_found),
            "suggestions": len(analysis.suggested_tags)
        })
        
        return analysis
    # <!--/TAG:analyze_file:method-->
    
    def _extract_classes(self, tree: ast.AST) -> List[str]:
        """Extract all class names from AST."""
        # Walk entire AST tree recursively to find all ClassDef nodes
        # Returns list of class names (e.g., ['MyClass', 'BaseHandler'])
        return [node.name for node in ast.walk(tree) 
                if isinstance(node, ast.ClassDef)]
    
    def _extract_functions(self, tree: ast.AST) -> List[str]:
        """Extract top-level function names from AST."""
        # Only get direct children of module (not nested/method functions)
        # iter_child_nodes only yields immediate children, not recursive
        return [node.name for node in ast.iter_child_nodes(tree)
                if isinstance(node, ast.FunctionDef)]
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all import names from AST."""
        imports = []  # Accumulator for discovered import module names
        
        # Walk entire AST tree to find all import-related nodes
        for node in ast.walk(tree):
            # Handle 'import foo, bar' style imports
            if isinstance(node, ast.Import):
                # Import can have multiple names: 'import a, b, c'
                for alias in node.names:
                    # Add the module name (not the alias if 'import x as y')
                    imports.append(alias.name)
            # Handle 'from foo import bar' style imports
            elif isinstance(node, ast.ImportFrom):
                # node.module is None for relative imports like 'from . import x'
                if node.module:
                    # Add the source module, not the imported names
                    imports.append(node.module)
        
        return imports  # Return list of all discovered import sources
    
    def _generate_suggestions(self, file_path: Path, content: str,
                               tree: ast.AST, analysis: FileTagAnalysis) -> List[TagSuggestion]:
        """Generate tag suggestions based on analysis."""
        suggestions = []
        
        # 1. Component tag from path
        component = self._detect_component(file_path)
        if component:
            suggestions.append(TagSuggestion(
                tag=f"component:{component}",
                confidence=1.0,
                reason=f"File is in {component}/ directory",
                source="path"
            ))
        
        # 2. Type tag from content
        type_tag = self._detect_type(analysis)
        suggestions.append(TagSuggestion(
            tag=f"type:{type_tag}",
            confidence=0.9,
            reason=f"Detected {type_tag} from file structure",
            source="structure"
        ))
        
        # 3. Feature tags from imports
        feature_tags = self._detect_features_from_imports(analysis.imports_found)
        for tag, reason in feature_tags:
            suggestions.append(TagSuggestion(
                tag=f"feature:{tag}",
                confidence=0.8,
                reason=reason,
                source="import"
            ))
        
        # 4. Feature tags from class/function names
        name_features = self._detect_features_from_names(
            analysis.classes_found + analysis.functions_found
        )
        for tag, reason in name_features:
            suggestions.append(TagSuggestion(
                tag=f"feature:{tag}",
                confidence=0.7,
                reason=reason,
                source="name"
            ))
        
        # 5. Feature tags from docstring content
        docstring_features = self._detect_features_from_content(content)
        for tag, reason in docstring_features:
            suggestions.append(TagSuggestion(
                tag=f"feature:{tag}",
                confidence=0.6,
                reason=reason,
                source="content"
            ))
        
        # Remove duplicates, keeping highest confidence
        seen_tags = {}
        for s in suggestions:
            if s.tag not in seen_tags or s.confidence > seen_tags[s.tag].confidence:
                seen_tags[s.tag] = s
        
        return list(seen_tags.values())
    
    def _detect_component(self, file_path: Path) -> Optional[str]:
        """Detect component from file path."""
        path_str = str(file_path)
        
        if '/automation/' in path_str or '\\automation\\' in path_str:
            return 'automation'
        elif '/utils/' in path_str or '\\utils\\' in path_str:
            return 'utils'
        elif '/processing/' in path_str or '\\processing\\' in path_str:
            return 'processing'
        elif '/tests/' in path_str or '\\tests\\' in path_str:
            return 'tests'
        elif '/docs/' in path_str or '\\docs\\' in path_str:
            return 'docs'
        
        return None
    
    def _detect_type(self, analysis: FileTagAnalysis) -> str:
        """Detect primary type from file structure."""
        if analysis.classes_found and len(analysis.classes_found) >= len(analysis.functions_found):
            return 'class'
        elif analysis.functions_found:
            return 'script'
        else:
            return 'script'
    
    def _detect_features_from_imports(self, imports: List[str]) -> List[Tuple[str, str]]:
        """Detect features from import statements."""
        features = []
        
        # Map import patterns to features
        import_map = {
            'embed': ('embeddings', 'imports embedding-related module'),
            'search': ('search', 'imports search-related module'),
            'valid': ('validation', 'imports validation-related module'),
            'logging': ('logging', 'imports logging module'),
            'log': ('logging', 'imports logging-related module'),
            'memory': ('memory', 'imports memory-related module'),
            'llm': ('llm', 'imports LLM-related module'),
            'openai': ('llm', 'imports OpenAI'),
            'anthropic': ('llm', 'imports Anthropic'),
            'vllm': ('llm', 'imports vLLM'),
            'ast': ('validation', 'uses AST parsing'),
            'yaml': ('config', 'uses YAML configuration'),
            'json': ('config', 'uses JSON configuration'),
        }
        
        for imp in imports:
            imp_lower = imp.lower()
            for pattern, (feature, reason) in import_map.items():
                if pattern in imp_lower:
                    features.append((feature, reason))
                    break
        
        return list(set(features))
    
    def _detect_features_from_names(self, names: List[str]) -> List[Tuple[str, str]]:
        """Detect features from class/function names."""
        features = []
        
        name_map = {
            'validator': ('validation', 'Validator class/function found'),
            'validate': ('validation', 'validate function found'),
            'search': ('search', 'Search class/function found'),
            'embed': ('embeddings', 'Embed class/function found'),
            'tagger': ('tagging', 'Tagger class/function found'),
            'tag': ('tagging', 'tag-related function found'),
            'logger': ('logging', 'Logger class found'),
            'memory': ('memory', 'Memory class found'),
            'index': ('indexing', 'Index class/function found'),
            'context': ('context', 'Context class/function found'),
            'assembl': ('context', 'Assembler class/function found'),
        }
        
        for name in names:
            name_lower = name.lower()
            for pattern, (feature, reason) in name_map.items():
                if pattern in name_lower:
                    features.append((feature, reason))
                    break
        
        return list(set(features))
    
    def _detect_features_from_content(self, content: str) -> List[Tuple[str, str]]:
        """Detect features from docstring content."""
        features = []
        content_lower = content.lower()
        
        # Only check docstring area (first 2000 chars)
        docstring_area = content_lower[:2000]
        
        content_map = {
            'embedding': ('embeddings', 'mentions embedding in documentation'),
            'semantic search': ('search', 'mentions semantic search'),
            'validation': ('validation', 'mentions validation'),
            'pipeline': ('pipeline', 'mentions pipeline processing'),
            'analytics': ('analytics', 'mentions analytics'),
            'llm': ('llm', 'mentions LLM integration'),
        }
        
        for pattern, (feature, reason) in content_map.items():
            if pattern in docstring_area:
                features.append((feature, reason))
        
        return list(set(features))
    
    def _generate_primary_tag(self, file_path: Path, 
                               analysis: FileTagAnalysis) -> str:
        """Generate primary tag (file identifier)."""
        stem = file_path.stem
        
        # Check for existing primary tag
        for tag in analysis.existing_tags:
            if ':' not in tag or tag.count(':') == 1:
                base = tag.split(':')[0]
                if base.startswith('tool_') or base.startswith('spec_'):
                    return tag
        
        # Generate based on path
        path_str = str(file_path)
        
        if '/automation/' in path_str:
            return f"tool_{stem}"
        elif '/specs/' in path_str:
            return f"spec_{stem}"
        elif '/utils/' in path_str:
            return f"util_{stem}"
        else:
            return stem
    
    def generate_tag_block(self, analysis: FileTagAnalysis, 
                           min_confidence: float = 0.7) -> str:
        """
        Generate a tag block to insert into file.
        
        <!--TAG:generate_tag_block:method-->
        
        Args:
            analysis: FileTagAnalysis from analyze_file().
            min_confidence: Minimum confidence for including suggestion.
            
        Returns:
            Formatted tag block string.
        """
        # Filter by confidence
        tags = [s for s in analysis.suggested_tags if s.confidence >= min_confidence]
        
        if not tags:
            return ""
        
        # Format inline tags
        inline_tags = ' '.join(f'<!--TAG:{s.tag}-->' for s in tags)
        
        # Create block
        block = f"""
<!--TAG:{analysis.primary_tag}-->

TAGS: {inline_tags}

<!--/TAG:{analysis.primary_tag}-->
"""
        return block.strip()
    # <!--/TAG:generate_tag_block:method-->
    
    def apply_tags(self, file_path: Path, analysis: FileTagAnalysis,
                   min_confidence: float = 0.7) -> bool:
        """
        Apply suggested tags to a file.
        
        <!--TAG:apply_tags:method-->
        
        Args:
            file_path: Path to the file.
            analysis: FileTagAnalysis with suggestions.
            min_confidence: Minimum confidence threshold.
            
        Returns:
            True if tags were applied successfully.
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Cannot read {file_path}: {e}")
            return False
        
        # Check if tags already exist
        if analysis.existing_tags:
            logger.info(f"{file_path} already has tags, skipping")
            return False
        
        # Generate tag block
        tag_block = self.generate_tag_block(analysis, min_confidence)
        if not tag_block:
            return False
        
        # Find insertion point (after shebang/encoding)
        lines = content.split('\n')
        insert_line = 0
        
        for i, line in enumerate(lines):
            if line.startswith('#!') or 'coding' in line or line.strip() == '':
                insert_line = i + 1
            elif line.startswith('"""') or line.startswith("'''"):
                # Insert before docstring
                insert_line = i
                break
            else:
                break
        
        # Insert tag block
        lines.insert(insert_line, tag_block)
        new_content = '\n'.join(lines)
        
        # Write back
        try:
            file_path.write_text(new_content, encoding='utf-8')
            logger.info(f"Applied tags to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Cannot write {file_path}: {e}")
            return False
    # <!--/TAG:apply_tags:method-->
    
    def format_analysis(self, analysis: FileTagAnalysis) -> str:
        """Format analysis for display."""
        lines = [
            f"\n{'='*60}",
            f"File: {analysis.file_path}",
            f"{'='*60}",
        ]
        
        # Existing tags
        if analysis.existing_tags:
            lines.append(f"\nExisting tags ({len(analysis.existing_tags)}):")
            for tag in analysis.existing_tags:
                lines.append(f"  ✓ {tag}")
        else:
            lines.append("\nNo existing tags found")
        
        # Structure info
        if analysis.classes_found:
            lines.append(f"\nClasses: {', '.join(analysis.classes_found)}")
        if analysis.functions_found:
            lines.append(f"Functions: {', '.join(analysis.functions_found[:5])}")
            if len(analysis.functions_found) > 5:
                lines.append(f"  ... and {len(analysis.functions_found) - 5} more")
        
        # Suggestions
        if analysis.suggested_tags:
            lines.append(f"\nSuggested tags ({len(analysis.suggested_tags)}):")
            for s in sorted(analysis.suggested_tags, key=lambda x: -x.confidence):
                icon = "✅" if s.confidence >= 0.8 else "⚠️" if s.confidence >= 0.6 else "❓"
                lines.append(f"  {icon} {s.tag} ({s.confidence:.0%}) - {s.reason}")
        
        # Primary tag
        if analysis.primary_tag:
            lines.append(f"\nPrimary tag: <!--TAG:{analysis.primary_tag}-->")
        
        return '\n'.join(lines)

# <!--/TAG:ASTAutoTagger:class-->

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Automatically generate semantic tags from Python code'
    )
    parser.add_argument('--file', type=str, help='Single file to analyze')
    parser.add_argument('--directory', type=str, help='Directory to analyze')
    parser.add_argument('--all', action='store_true', help='Analyze entire project')
    parser.add_argument('--preview', action='store_true', help='Preview without applying')
    parser.add_argument('--apply', action='store_true', help='Apply suggested tags')
    parser.add_argument('--min-confidence', type=float, default=0.7,
                       help='Minimum confidence for applying tags (default: 0.7)')
    parser.add_argument('--report', action='store_true', help='Generate summary report')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    tagger = ASTAutoTagger()
    analyses = []
    
    if args.file:
        # Single file
        analysis = tagger.analyze_file(Path(args.file))
        analyses.append(analysis)
        
    elif args.directory:
        # Directory
        for py_file in Path(args.directory).rglob('*.py'):
            if '__pycache__' not in str(py_file):
                analyses.append(tagger.analyze_file(py_file))
                
    elif args.all:
        # Entire project
        project_root = Path(__file__).parent.parent
        for dir_name in ['docs/automation', 'utils', 'processing']:
            dir_path = project_root / dir_name
            if dir_path.exists():
                for py_file in dir_path.rglob('*.py'):
                    if '__pycache__' not in str(py_file):
                        analyses.append(tagger.analyze_file(py_file))
    else:
        parser.print_help()
        return
    
    # Output
    if args.json:
        import json
        output = []
        for a in analyses:
            output.append({
                'file': a.file_path,
                'existing_tags': a.existing_tags,
                'suggested_tags': [
                    {'tag': s.tag, 'confidence': s.confidence, 'reason': s.reason}
                    for s in a.suggested_tags
                ],
                'primary_tag': a.primary_tag,
                'classes': a.classes_found,
                'functions': a.functions_found
            })
        print(json.dumps(output, indent=2))
        
    elif args.apply:
        applied_count = 0
        for analysis in analyses:
            if tagger.apply_tags(Path(analysis.file_path), analysis, args.min_confidence):
                applied_count += 1
        print(f"\nApplied tags to {applied_count}/{len(analyses)} files")
        
    elif args.report:
        # Summary report
        total = len(analyses)
        with_tags = sum(1 for a in analyses if a.existing_tags)
        without_tags = total - with_tags
        
        print("\n" + "="*60)
        print("AST AUTO-TAGGER REPORT")
        print("="*60)
        print(f"Files analyzed: {total}")
        print(f"With existing tags: {with_tags}")
        print(f"Without tags: {without_tags}")
        
        if without_tags:
            print(f"\nFiles needing tags:")
            for a in analyses:
                if not a.existing_tags:
                    suggestions = len([s for s in a.suggested_tags if s.confidence >= args.min_confidence])
                    print(f"  - {a.file_path} ({suggestions} suggestions)")
    else:
        # Preview
        for analysis in analyses:
            print(tagger.format_analysis(analysis))


if __name__ == '__main__':
    main()
