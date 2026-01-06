#!/usr/bin/env python3
"""
Tag Validator - Validate tags against formal schema

<!--TAG:tool_tag_validator-->

PURPOSE:
    Validates semantic tags in files against the formal tag schema.
    Reports errors, warnings, and suggestions for improvement.
    Supports auto-fix for simple issues.

DOCUMENTATION:
    Spec: docs/specs/tag_schema.yaml
    Wiki: docs/wiki/09_Documentation_System.md

TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:validation--> <!--TAG:feature:tagging-->

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger (DocsLogger for isolated logging)
    Config:
        - docs/specs/tag_schema.yaml (tag validation schema)
    Data:
        - Input: Any .py or .md files
        - Output: Validation reports (console or JSON)
    External:
        - None (pure Python)

RECENT CHANGES:
    2025-12-12: Added DEPENDENCIES and RECENT CHANGES sections to header
    2025-12-12: Pseudocode rewritten to v2.0 matching class structure

USAGE:
    python3 tag_validator.py --file path/to/file.py
    python3 tag_validator.py --directory docs/automation/
    python3 tag_validator.py --all --fix

<!--/TAG:tool_tag_validator-->
"""

import os
import re
import sys
import yaml
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

# Add project root to path
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from utils.docs_logger import DocsLogger
    logger = DocsLogger("tag_validator")
except ImportError:
    import logging
    logger = logging.getLogger("tag_validator")
    logging.basicConfig(level=logging.INFO)


class Severity(Enum):
    """Issue severity levels."""
    ERROR = "ERROR"      # Must fix - breaks functionality
    WARNING = "WARNING"  # Should fix - best practice violation
    INFO = "INFO"        # Suggestion - could improve


@dataclass
class ValidationIssue:
    """A validation issue found in a file."""
    severity: Severity
    rule_name: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class ValidationReport:
    """Complete validation report for a file."""
    file_path: str
    issues: List[ValidationIssue] = field(default_factory=list)
    tags_found: List[str] = field(default_factory=list)
    is_valid: bool = True
    
    def add_issue(self, issue: ValidationIssue):
        """Add an issue to the report."""
        self.issues.append(issue)
        if issue.severity == Severity.ERROR:
            self.is_valid = False
    
    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)


class TagValidator:
    """
    Validates semantic tags against the formal schema.
    
    <!--TAG:TagValidator:class-->
    """
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize validator with schema.
        
        Args:
            schema_path: Path to tag_schema.yaml. If None, uses default location.
        """
        # Find schema file
        if schema_path is None:
            self.schema_path = Path(__file__).parent.parent / "specs" / "tag_schema.yaml"
        else:
            self.schema_path = Path(schema_path)
        
        # Load schema from YAML file (contains allowed dimensions and rules)
        self.schema = self._load_schema()
        
        # Regex pattern to match opening semantic tags: <!--TAG:identifier-->
        # Captures the identifier which can contain letters, numbers, underscores, colons
        # Example matches: <!--TAG:component:automation-->, <!--TAG:validate_file:method-->
        self.tag_pattern = re.compile(r'<!--TAG:([a-zA-Z0-9_:]+)-->')
        
        # Regex pattern to match closing semantic tags: <!--/TAG:identifier-->
        # Note the forward slash before TAG indicating this is a closing tag
        # Must match the identifier from the corresponding opening tag
        self.close_pattern = re.compile(r'<!--/TAG:([a-zA-Z0-9_:]+)-->')
        
        # Log successful initialization with schema path for debugging
        logger.info(f"TagValidator initialized with schema: {self.schema_path}")
    
    def _load_schema(self) -> Dict:
        """Load and parse the tag schema."""
        if not self.schema_path.exists():
            logger.warning(f"Schema file not found: {self.schema_path}")
            return self._get_default_schema()
        
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = yaml.safe_load(f)
            logger.info(f"Loaded schema version: {schema.get('version', 'unknown')}")
            return schema
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            return self._get_default_schema()
    
    def _get_default_schema(self) -> Dict:
        """Return minimal default schema if file not found."""
        return {
            "version": "1.0",
            "tag_hierarchy": {
                "component": ["automation", "utils", "processing", "docs"],
                "type": ["script", "class", "function", "documentation"],
                "feature": ["embeddings", "search", "validation", "logging"]
            },
            "tag_rules": [
                {"name": "max_tags_per_file", "max_value": 6},
                {"name": "valid_identifier", "pattern": "^[a-zA-Z][a-zA-Z0-9_:]*$"}
            ]
        }
    
    def validate_file(self, file_path: Path) -> ValidationReport:
        """
        Validate all tags in a single file.
        
        <!--TAG:validate_file:method-->
        
        Args:
            file_path: Path to the file to validate.
            
        Returns:
            ValidationReport with all issues found.
        """
        report = ValidationReport(file_path=str(file_path))
        
        # Check file exists
        if not file_path.exists():
            report.add_issue(ValidationIssue(
                severity=Severity.ERROR,
                rule_name="file_exists",
                message=f"File not found: {file_path}",
                file_path=str(file_path)
            ))
            return report
        
        # Read file content
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            report.add_issue(ValidationIssue(
                severity=Severity.ERROR,
                rule_name="file_readable",
                message=f"Cannot read file: {e}",
                file_path=str(file_path)
            ))
            return report
        
        # Extract all tags
        opening_tags = self.tag_pattern.findall(content)
        closing_tags = self.close_pattern.findall(content)
        report.tags_found = opening_tags
        
        # Run all validation rules
        self._check_tag_count(report, opening_tags)
        self._check_matching_close_tags(report, opening_tags, closing_tags, content)
        self._check_valid_identifiers(report, opening_tags)
        self._check_component_tag(report, file_path, opening_tags)
        self._check_duplicate_tags(report, opening_tags)
        self._check_known_dimensions(report, opening_tags)
        
        return report
    # <!--/TAG:validate_file:method-->
    
    def _check_tag_count(self, report: ValidationReport, tags: List[str]):
        """Check if tag count exceeds maximum."""
        max_tags = 6
        for rule in self.schema.get("tag_rules", []):
            if rule.get("name") == "max_tags_per_file":
                max_tags = rule.get("max_value", 6)
        
        # Count unique tags (excluding dimension variants)
        unique_tags = set(t.split(':')[0] if ':' not in t else t for t in tags)
        
        if len(unique_tags) > max_tags:
            report.add_issue(ValidationIssue(
                severity=Severity.WARNING,
                rule_name="max_tags_per_file",
                message=f"Too many tags: {len(unique_tags)} (max {max_tags})",
                file_path=report.file_path,
                suggestion=f"Consider consolidating tags or removing less important ones"
            ))
    
    def _check_matching_close_tags(self, report: ValidationReport, 
                                   opening: List[str], closing: List[str],
                                   content: str):
        """Check that primary tags have matching closing tags."""
        # Get primary tags (non-inline, non-dimension tags)
        primary_tags = [t for t in opening if ':' not in t or t.count(':') == 1]
        
        for tag in primary_tags:
            # Check if tag appears in docstring header (inline feature tags don't need closing)
            base_tag = tag.split(':')[0]
            if base_tag in closing:
                continue
            
            # Check if it's an inline dimension tag
            if ':' in tag and tag.split(':')[0] in ['component', 'type', 'feature']:
                continue  # Inline dimension tags don't need closing
            
            # Check if the tag has content that needs closing
            opening_pos = content.find(f"<!--TAG:{tag}-->")
            if opening_pos != -1:
                # Look for closing tag
                closing_pos = content.find(f"<!--/TAG:{tag}-->", opening_pos)
                
                # Check if there's significant content after the opening tag
                next_tag_pos = content.find("<!--", opening_pos + len(f"<!--TAG:{tag}-->"))
                if next_tag_pos == -1:
                    next_tag_pos = len(content)
                
                content_between = content[opening_pos + len(f"<!--TAG:{tag}-->"):next_tag_pos].strip()
                
                # If there's content, it should have a closing tag
                if len(content_between) > 50 and closing_pos == -1:
                    line_num = content[:opening_pos].count('\n') + 1
                    report.add_issue(ValidationIssue(
                        severity=Severity.ERROR,
                        rule_name="primary_tag_must_close",
                        message=f"Tag '{tag}' has content but no closing tag",
                        file_path=report.file_path,
                        line_number=line_num,
                        suggestion=f"Add <!--/TAG:{tag}--> after the content",
                        auto_fixable=True
                    ))
    
    def _check_valid_identifiers(self, report: ValidationReport, tags: List[str]):
        """Check that tag identifiers follow naming conventions."""
        # Pattern: alphanumeric with underscores and colons
        valid_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_:]*$')
        
        for tag in tags:
            if not valid_pattern.match(tag):
                report.add_issue(ValidationIssue(
                    severity=Severity.ERROR,
                    rule_name="valid_identifier",
                    message=f"Invalid tag identifier: '{tag}'",
                    file_path=report.file_path,
                    suggestion="Tag identifiers must start with a letter and contain only alphanumeric, underscore, colon"
                ))
    
    def _check_component_tag(self, report: ValidationReport, 
                             file_path: Path, tags: List[str]):
        """Check that Python files have component tags."""
        if file_path.suffix != '.py':
            return
        
        # Check for component dimension tag
        component_tags = ['component:' + c for c in self.schema.get('tag_hierarchy', {}).get('component', [])]
        has_component = any(t in component_tags or t.startswith('component:') for t in tags)
        
        if not has_component:
            # Infer from path
            suggested_component = self._infer_component_from_path(file_path)
            report.add_issue(ValidationIssue(
                severity=Severity.WARNING,
                rule_name="script_must_have_component",
                message="Python file missing component tag",
                file_path=str(file_path),
                suggestion=f"Add <!--TAG:component:{suggested_component}--> to the docstring",
                auto_fixable=True
            ))
    
    def _infer_component_from_path(self, file_path: Path) -> str:
        """Infer component from file path."""
        path_str = str(file_path)
        
        if 'automation' in path_str:
            return 'automation'
        elif 'utils' in path_str:
            return 'utils'
        elif 'processing' in path_str:
            return 'processing'
        elif 'docs' in path_str:
            return 'docs'
        elif 'tests' in path_str:
            return 'tests'
        else:
            return 'utils'  # Default
    
    def _check_duplicate_tags(self, report: ValidationReport, tags: List[str]):
        """Check for duplicate tags."""
        seen = set()
        duplicates = set()
        
        for tag in tags:
            if tag in seen:
                duplicates.add(tag)
            seen.add(tag)
        
        for dup in duplicates:
            report.add_issue(ValidationIssue(
                severity=Severity.WARNING,
                rule_name="no_duplicate_tags",
                message=f"Duplicate tag: '{dup}'",
                file_path=report.file_path,
                suggestion="Remove duplicate tag occurrences"
            ))
    
    def _check_known_dimensions(self, report: ValidationReport, tags: List[str]):
        """Check that dimension tags use known values."""
        hierarchy = self.schema.get('tag_hierarchy', {})
        
        for tag in tags:
            if ':' in tag:
                parts = tag.split(':')
                if len(parts) >= 2:
                    dimension, value = parts[0], parts[1]
                    
                    # Skip non-dimension tags (like method:name)
                    if dimension not in ['component', 'type', 'feature']:
                        continue
                    
                    known_values = hierarchy.get(dimension, [])
                    if known_values and value not in known_values:
                        report.add_issue(ValidationIssue(
                            severity=Severity.INFO,
                            rule_name="known_dimension_value",
                            message=f"Unknown {dimension} value: '{value}'",
                            file_path=report.file_path,
                            suggestion=f"Known values: {', '.join(known_values)}"
                        ))
    
    def validate_directory(self, directory: Path, 
                          extensions: List[str] = None) -> List[ValidationReport]:
        """
        Validate all files in a directory.
        
        <!--TAG:validate_directory:method-->
        
        Args:
            directory: Directory to scan.
            extensions: File extensions to validate (default: .py, .md).
            
        Returns:
            List of ValidationReports for each file.
        """
        if extensions is None:
            extensions = ['.py', '.md']
        
        reports = []
        
        for ext in extensions:
            for file_path in directory.rglob(f'*{ext}'):
                # Skip generated/cache files
                if '__pycache__' in str(file_path):
                    continue
                if '.git' in str(file_path):
                    continue
                
                report = self.validate_file(file_path)
                reports.append(report)
        
        return reports
    # <!--/TAG:validate_directory:method-->
    
    def format_report(self, report: ValidationReport) -> str:
        """Format a validation report for display."""
        lines = []
        
        # Header
        status = "✅ VALID" if report.is_valid else "❌ INVALID"
        lines.append(f"\n{status}: {report.file_path}")
        lines.append(f"  Tags found: {len(report.tags_found)}")
        
        if report.tags_found:
            lines.append(f"  Tags: {', '.join(report.tags_found[:5])}")
            if len(report.tags_found) > 5:
                lines.append(f"        ... and {len(report.tags_found) - 5} more")
        
        # Issues grouped by severity
        for severity in [Severity.ERROR, Severity.WARNING, Severity.INFO]:
            severity_issues = [i for i in report.issues if i.severity == severity]
            if severity_issues:
                icon = "🚨" if severity == Severity.ERROR else "⚠️" if severity == Severity.WARNING else "ℹ️"
                for issue in severity_issues:
                    line_info = f" (line {issue.line_number})" if issue.line_number else ""
                    lines.append(f"  {icon} [{severity.value}] {issue.message}{line_info}")
                    if issue.suggestion:
                        lines.append(f"      → {issue.suggestion}")
        
        return '\n'.join(lines)
    
    def format_summary(self, reports: List[ValidationReport]) -> str:
        """Format summary of all reports."""
        total_files = len(reports)
        valid_files = sum(1 for r in reports if r.is_valid)
        total_errors = sum(r.error_count for r in reports)
        total_warnings = sum(r.warning_count for r in reports)
        
        lines = [
            "\n" + "=" * 60,
            "TAG VALIDATION SUMMARY",
            "=" * 60,
            f"Files validated: {total_files}",
            f"Valid files: {valid_files} ({100*valid_files//total_files if total_files else 0}%)",
            f"Total errors: {total_errors}",
            f"Total warnings: {total_warnings}",
            "=" * 60
        ]
        
        return '\n'.join(lines)

# <!--/TAG:TagValidator:class-->

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Validate semantic tags against formal schema'
    )
    parser.add_argument('--file', type=str, help='Single file to validate')
    parser.add_argument('--directory', type=str, help='Directory to validate')
    parser.add_argument('--all', action='store_true', help='Validate entire project')
    parser.add_argument('--schema', type=str, help='Path to tag schema YAML')
    parser.add_argument('--fix', action='store_true', help='Auto-fix simple issues')
    parser.add_argument('--quiet', action='store_true', help='Only show errors')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # Initialize validator
    schema_path = Path(args.schema) if args.schema else None
    validator = TagValidator(schema_path=schema_path)
    
    reports = []
    
    if args.file:
        # Validate single file
        report = validator.validate_file(Path(args.file))
        reports.append(report)
        
    elif args.directory:
        # Validate directory
        reports = validator.validate_directory(Path(args.directory))
        
    elif args.all:
        # Validate entire project
        project_root = Path(__file__).parent.parent
        
        # Validate key directories
        for dir_name in ['docs/automation', 'utils', 'processing']:
            dir_path = project_root / dir_name
            if dir_path.exists():
                reports.extend(validator.validate_directory(dir_path))
    else:
        parser.print_help()
        return
    
    # Format and print output
    if args.json:
        import json
        output = []
        for r in reports:
            output.append({
                'file': r.file_path,
                'valid': r.is_valid,
                'tags': r.tags_found,
                'errors': r.error_count,
                'warnings': r.warning_count,
                'issues': [
                    {
                        'severity': i.severity.value,
                        'rule': i.rule_name,
                        'message': i.message,
                        'line': i.line_number,
                        'suggestion': i.suggestion
                    }
                    for i in r.issues
                ]
            })
        print(json.dumps(output, indent=2))
    else:
        for report in reports:
            if not args.quiet or not report.is_valid:
                print(validator.format_report(report))
        
        print(validator.format_summary(reports))


if __name__ == '__main__':
    main()
