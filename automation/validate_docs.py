#!/usr/bin/env python3
"""
Documentation Validator - Checks for broken links and missing specs

<!--TAG:tool_validate_docs-->

PURPOSE:
    Validates the integrity of the documentation system.
    Checks for broken relative links, missing specification files,
    and strict folder structure adherence.

DOCUMENTATION:
    Spec: docs/specs/Automation_Tools_Spec.md
    Wiki: docs/wiki/09_Documentation_System.md
    Dependencies: docs/memory/dependencies/validate_docs_dependencies.json

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger (DocsLogger)
    Config:
        - None
    Data:
        - Input: docs/ (all markdown files)
        - Output: docs/validation_report.md
    External:
        - None (pure filesystem operations)

RECENT CHANGES:
    2025-12-12: Fixed duplicate statements, added DEPENDENCIES section

TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:validation-->

<!--/TAG:tool_validate_docs-->
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import sys
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.docs_logger import DocsLogger

logger = DocsLogger("validate_docs")

@dataclass
class ValidationIssue:
    """Documentation validation issue"""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'drift', 'link', 'missing', 'format'
    file_path: str
    line_number: int
    message: str
    suggestion: str = ""

class DocumentationValidator:
    """Validates documentation consistency and completeness"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[ValidationIssue] = []
        
    def validate_all(self) -> List[ValidationIssue]:
        """Run all validation checks"""
        logger.info("🔍 Running documentation validation...")
        
        self.check_broken_links()
        self.check_missing_specs()
        self.check_spec_code_drift()
        self.check_frontmatter()
        
        return self.issues
    
    def check_broken_links(self):
        """Check for broken links in markdown files"""
        logger.info("📎 Checking for broken links...")
        
        docs_dir = self.project_root / 'docs'
        all_files = set()
        
        # Collect all existing files
        for md_file in docs_dir.rglob('*.md'):
            all_files.add(md_file.relative_to(self.project_root))
        
        # Check links in each file
        for md_file in docs_dir.rglob('*.md'):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find markdown links
            link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
            links = re.findall(link_pattern, content)
            
            for link_text, link_url in links:
                # Skip external URLs
                if link_url.startswith('http://') or link_url.startswith('https://'):
                    continue
                
                # Skip anchors
                if link_url.startswith('#'):
                    continue
                
                # Resolve relative path (handle anchors)
                url_parts = link_url.split('#')
                file_path = url_parts[0]
                
                link_path = (md_file.parent / file_path).resolve()
                
                # Check if file exists
                if not link_path.exists():
                    # Try to get relative path, skip if outside project
                    try:
                        relative_link = link_path.relative_to(self.project_root)
                    except ValueError:
                        # Link points outside project root - skip validation
                        continue
                    
                    self.issues.append(ValidationIssue(
                        severity='error',
                        category='link',
                        file_path=str(md_file.relative_to(self.project_root)),
                        line_number=self._find_line_number(content, link_url),
                        message=f"Broken link: {link_url}",
                        suggestion=f"Check if file exists: {relative_link}"
                    ))
        
        broken_count = sum(1 for issue in self.issues if issue.category == 'link')
        logger.info(f"  Found {broken_count} broken links")
    
    def check_missing_specs(self):
        """Check for Python files without specifications"""
        logger.info("📋 Checking for missing specifications...")
        
        specs_dir = self.project_root / 'docs' / 'specs'
        processing_dir = self.project_root / 'processing'
        utils_dir = self.project_root / 'utils'
        
        # Get all spec files
        spec_files = set()
        for spec_file in specs_dir.rglob('*.md'):
            spec_files.add(spec_file.stem.replace('_spec', ''))
        
        # Check processing files
        for py_file in processing_dir.rglob('*.py'):
            if py_file.name == '__init__.py':
                continue
            
            file_stem = py_file.stem
            if file_stem not in spec_files:
                self.issues.append(ValidationIssue(
                    severity='warning',
                    category='missing',
                    file_path=str(py_file.relative_to(self.project_root)),
                    line_number=0,
                    message=f"Missing specification for {py_file.name}",
                    suggestion=f"Create docs/specs/{file_stem}_spec.md"
                ))
        
        # Check utils files
        for py_file in utils_dir.rglob('*.py'):
            if py_file.name == '__init__.py':
                continue
            
            file_stem = f"utils_{py_file.stem}"
            if file_stem not in spec_files:
                self.issues.append(ValidationIssue(
                    severity='info',
                    category='missing',
                    file_path=str(py_file.relative_to(self.project_root)),
                    line_number=0,
                    message=f"Missing specification for {py_file.name}",
                    suggestion=f"Create docs/specs/{file_stem}_spec.md"
                ))
        
        missing_count = sum(1 for issue in self.issues if issue.category == 'missing')
        logger.info(f"  Found {missing_count} files without specs")
    
    def check_spec_code_drift(self):
        """Check for drift between specs and actual code"""
        logger.info("🔄 Checking for spec-code drift...")
        
        specs_dir = self.project_root / 'docs' / 'specs'
        
        for spec_file in specs_dir.rglob('*_spec.md'):
            # Find corresponding Python file
            py_file = self._find_python_file(spec_file)
            
            if not py_file or not py_file.exists():
                continue
            
            # Read spec
            with open(spec_file, 'r', encoding='utf-8') as f:
                spec_content = f.read()
            
            # Read code
            with open(py_file, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            # Check for mentioned functions in spec
            function_pattern = r'`([a-zA-Z_][a-zA-Z0-9_]*)\(`'
            spec_functions = set(re.findall(function_pattern, spec_content))
            
            # Extract actual functions from code
            code_function_pattern = r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            code_functions = set(re.findall(code_function_pattern, code_content, re.MULTILINE))
            
            # Find functions in spec but not in code
            missing_in_code = spec_functions - code_functions
            if missing_in_code:
                self.issues.append(ValidationIssue(
                    severity='warning',
                    category='drift',
                    file_path=str(spec_file.relative_to(self.project_root)),
                    line_number=0,
                    message=f"Functions in spec but not in code: {', '.join(missing_in_code)}",
                    suggestion=f"Update spec or implement missing functions in {py_file.name}"
                ))
            
            # Find functions in code but not in spec
            missing_in_spec = code_functions - spec_functions
            # Filter out private functions
            missing_in_spec = {f for f in missing_in_spec if not f.startswith('_')}
            if missing_in_spec:
                self.issues.append(ValidationIssue(
                    severity='info',
                    category='drift',
                    file_path=str(spec_file.relative_to(self.project_root)),
                    line_number=0,
                    message=f"Functions in code but not in spec: {', '.join(missing_in_spec)}",
                    suggestion=f"Document these functions in the spec"
                ))
        
        drift_count = sum(1 for issue in self.issues if issue.category == 'drift')
        logger.info(f"  Found {drift_count} drift issues")
    
    def check_frontmatter(self):
        """Check for proper YAML frontmatter in markdown files"""
        logger.info("📝 Checking YAML frontmatter...")
        
        docs_dir = self.project_root / 'docs'
        
        for md_file in docs_dir.rglob('*.md'):
            # Skip README files
            if md_file.name == 'README.MD':
                continue
            
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for frontmatter
            frontmatter_pattern = r'^---\n.*?\n---\n'
            if not re.match(frontmatter_pattern, content, re.DOTALL):
                self.issues.append(ValidationIssue(
                    severity='info',
                    category='format',
                    file_path=str(md_file.relative_to(self.project_root)),
                    line_number=1,
                    message="Missing YAML frontmatter",
                    suggestion="Add frontmatter with metadata (version, date, status)"
                ))
        
        format_count = sum(1 for issue in self.issues if issue.category == 'format')
        logger.info(f"  Found {format_count} formatting issues")
    
    def _find_python_file(self, spec_file: Path) -> Path:
        """Find Python file corresponding to spec"""
        spec_name = spec_file.stem.replace('_spec', '')
        
        # Check processing directory
        if not spec_name.startswith('utils_'):
            py_file = self.project_root / 'processing' / f"{spec_name}.py"
            if py_file.exists():
                return py_file
        
        # Check utils directory
        if spec_name.startswith('utils_'):
            utils_name = spec_name.replace('utils_', '')
            py_file = self.project_root / 'utils' / f"{utils_name}.py"
            if py_file.exists():
                return py_file
        
        return None
    
    def _find_line_number(self, content: str, search_text: str) -> int:
        """Find line number of text in content"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 0
    
    def generate_report(self, output_file: Path):
        """Generate validation report"""
        # Group issues by severity
        by_severity = defaultdict(list)
        for issue in self.issues:
            by_severity[issue.severity].append(issue)
        
        # Generate markdown report
        report = "# Documentation Validation Report\n\n"
        report += f"**Generated**: {Path(__file__).name}\n\n"
        
        report += "## Summary\n\n"
        report += f"- **Errors**: {len(by_severity['error'])}\n"
        report += f"- **Warnings**: {len(by_severity['warning'])}\n"
        report += f"- **Info**: {len(by_severity['info'])}\n"
        report += f"- **Total**: {len(self.issues)}\n\n"
        
        # Details by severity
        for severity in ['error', 'warning', 'info']:
            issues = by_severity[severity]
            if not issues:
                continue
            
            report += f"## {severity.upper()}S\n\n"
            
            for issue in issues:
                report += f"### {issue.file_path}\n\n"
                report += f"- **Line**: {issue.line_number}\n"
                report += f"- **Category**: {issue.category}\n"
                report += f"- **Message**: {issue.message}\n"
                if issue.suggestion:
                    report += f"- **Suggestion**: {issue.suggestion}\n"
                report += "\n"
        
        # Write report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📊 Report saved to: {output_file}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate documentation consistency')
    parser.add_argument('--report', type=str, default='docs/validation_report.md',
                       help='Output file for validation report')
    parser.add_argument('--ci-mode', action='store_true',
                       help='Exit with error code if issues found')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    validator = DocumentationValidator(project_root)
    
    issues = validator.validate_all()
    
    # Generate report
    report_file = project_root / args.report
    validator.generate_report(report_file)
    
    # Print summary
    logger.info("="*60)
    logger.info(f"✓ Validation complete: {len(issues)} issues found")
    logger.info("="*60)
    
    # Exit with error in CI mode if errors found
    if args.ci_mode:
        error_count = sum(1 for issue in issues if issue.severity == 'error')
        if error_count > 0:
            logger.error(f"CI mode: {error_count} errors found")
            exit(1)

if __name__ == '__main__':
    main()
