#!/usr/bin/env python3
"""
Adaptive Validation System - Multi-Tier Orchestrator

<!--TAG:validate_system-->

PURPOSE:
    Orchestrates a three-tier validation system with adaptive paranoia levels.
    Coordinates algorithmic validation, external tools, and AI verification
    based on project size and configured paranoia level.

DOCUMENTATION:
    Specification: docs/specs/adaptive_validation_system_spec.md
    Wiki: docs/wiki/validation_guide.md (planned)
    Dependencies: docs/memory/dependencies/validate_system_dependencies.json

TAGS FOR SEARCH:
    <!--TAG:component:automation-->
    <!--TAG:type:script-->
    <!--TAG:feature:validation-->
    <!--TAG:automation-->
    <!--TAG:validation-->
    <!--TAG:orchestrator-->

DEPENDENCIES:
    Code:
        - docs.automation.validate_docs (Tier 1 validation)
        - docs.automation.external_validators (Tier 2 validation)
        - utils.local_ai_verifier (Tier 3 validation)
        - utils.paranoid_logger (logging)
    External:
        - ruff (optional, Tier 2)
        - mypy (optional, Tier 2)
        - markdownlint (optional, Tier 2)

RECENT CHANGES:
    2025-12-11: Initial implementation (TICKET #11)

<!--/TAG:validate_system-->
"""

import os  # Operating system interface for file operations
import sys  # System-specific parameters and functions
import time  # Time tracking for performance measurement
import json  # JSON serialization for reports
import hashlib  # Hashing for ticket deduplication
import argparse  # Command-line argument parsing
import subprocess  # Running external tools
from pathlib import Path  # Object-oriented filesystem paths
from datetime import datetime  # Date and time handling
from typing import List, Dict, Any, Optional, Tuple  # Type hints
from dataclasses import dataclass, field, asdict  # Structured data classes
from collections import defaultdict  # Default dictionaries for grouping

# Add project root to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent  # Navigate to project root
sys.path.insert(0, str(BASE_DIR))  # Add to Python path

# Import project utilities
from utils.docs_logger import DocsLogger  # Paranoid logging


# ============================================================================
# CONFIGURATION
# ============================================================================

# Initialize paranoid logger for this module
logger = DocsLogger("validate_system")  # Module-specific logger

# Output directory for validation reports
OUTPUT_DIR = BASE_DIR / "output" / "validation"  # Validation reports go here

# Ticket directory for generated tickets
TICKETS_DIR = BASE_DIR / "docs" / "technical_debt" / "tickets"  # AI-generated tickets


# ============================================================================
# PARANOIA LEVELS CONFIGURATION
# ============================================================================

# Level 0 = auto-detect, Levels 1-5 = manual selection
# Default is 5 (maximum) - we don't save resources, always thorough validation

PARANOIA_LEVELS = {
    0: {
        "name": "Auto",  # Auto-detect based on project size
        "description": "Automatic level selection based on project size",
        "tiers": [],  # Will be determined at runtime
        "scope": "auto",
        "use_case": "Let system decide based on project complexity"
    },
    1: {
        "name": "Minimal",  # Human-readable name
        "description": "Basic algorithmic checks only",  # Description
        "tiers": [1],  # Which tiers to run
        "scope": "all",  # Scope for AI validation
        "use_case": "Small projects (<50 files), quick checks"  # When to use
    },
    2: {
        "name": "Standard",
        "description": "Algorithmic + external tools",
        "tiers": [1, 2],
        "scope": "all",
        "use_case": "Medium projects (50-200 files)"
    },
    3: {
        "name": "Thorough",
        "description": "Algorithmic + external + AI (changed files only)",
        "tiers": [1, 2, 3],
        "scope": "changed",  # Only validate changed files with AI
        "use_case": "Large projects (200-500 files)"
    },
    4: {
        "name": "Paranoid",
        "description": "Full validation + deep supervisor",
        "tiers": [1, 2, 3],
        "scope": "all",  # Validate all files with AI
        "extras": ["deep_supervisor"],  # Additional components
        "use_case": "Very large projects (>500 files)"
    },
    5: {
        "name": "Maximum",
        "description": "Everything + global supervisor",
        "tiers": [1, 2, 3],
        "scope": "all",
        "extras": ["deep_supervisor", "global_supervisor"],
        "use_case": "Production deployments, critical changes (DEFAULT)"
    }
}

# File count thresholds for auto-detection
SIZE_THRESHOLDS = {
    "minimal": 50,    # < 50 files = Level 1
    "standard": 200,  # 50-200 files = Level 2
    "thorough": 500,  # 200-500 files = Level 3
    "paranoid": 1000  # 500-1000 files = Level 4, >1000 = Level 5
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ValidationIssue:
    """Represents a single validation issue found."""
    
    severity: str  # 'ERROR', 'WARNING', 'INFO'
    category: str  # 'code_quality', 'docs_sync', 'link', 'format', 'type', 'lint'
    file_path: str  # Path to file with issue
    line: int = 0  # Line number (0 if not applicable)
    column: int = 0  # Column number (0 if not applicable)
    code: str = ""  # Error code (e.g., 'E501', 'MD001')
    message: str = ""  # Description of the issue
    suggestion: str = ""  # Suggested fix
    tool: str = ""  # Tool that found the issue
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)  # Use dataclass built-in conversion


@dataclass
class ValidationResult:
    """Result from running a single validation tool."""
    
    tier: int  # Which tier (1, 2, or 3)
    tool: str  # Tool name (e.g., 'validate_docs', 'ruff', 'ai_verifier')
    status: str  # 'PASS', 'WARN', 'FAIL', 'SKIP', 'ERROR'
    issues: List[ValidationIssue] = field(default_factory=list)  # Found issues
    duration: float = 0.0  # How long the validation took (seconds)
    error_message: str = ""  # Error message if status is ERROR
    
    def error_count(self) -> int:
        """Count ERROR severity issues."""
        return sum(1 for i in self.issues if i.severity == "ERROR")
    
    def warning_count(self) -> int:
        """Count WARNING severity issues."""
        return sum(1 for i in self.issues if i.severity == "WARNING")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "tier": self.tier,
            "tool": self.tool,
            "status": self.status,
            "issues": [i.to_dict() for i in self.issues],
            "duration": self.duration,
            "error_count": self.error_count(),
            "warning_count": self.warning_count(),
            "error_message": self.error_message
        }


@dataclass
class ValidationReport:
    """Complete validation report from all tiers."""
    
    timestamp: datetime  # When validation was run
    paranoia_level: int  # Which paranoia level was used
    project_size: int  # Number of files in project
    results: List[ValidationResult] = field(default_factory=list)  # Results from each tool
    tickets_generated: int = 0  # How many tickets were created
    
    def total_errors(self) -> int:
        """Total ERROR count across all tools."""
        return sum(r.error_count() for r in self.results)
    
    def total_warnings(self) -> int:
        """Total WARNING count across all tools."""
        return sum(r.warning_count() for r in self.results)
    
    def overall_status(self) -> str:
        """Determine overall validation status."""
        if any(r.status == "ERROR" for r in self.results):
            return "ERROR"  # System error during validation
        if self.total_errors() > 0:
            return "FAIL"  # Validation found errors
        if self.total_warnings() > 0:
            return "WARN"  # Validation found warnings
        return "PASS"  # All clear
    
    def to_markdown(self) -> str:
        """Convert report to markdown format."""
        
        lines = []  # Accumulator for report lines
        
        # Header
        lines.append("# Validation Report")
        lines.append("")
        lines.append(f"**Date**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Paranoia Level**: {self.paranoia_level} ({PARANOIA_LEVELS[self.paranoia_level]['name']})")
        lines.append(f"**Project Size**: {self.project_size} files")
        lines.append("")
        
        # Overall status with emoji
        status = self.overall_status()
        status_emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "ERROR": "🔥"}.get(status, "❓")
        lines.append(f"## Overall Status: {status_emoji} {status}")
        lines.append("")
        
        # Summary statistics
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Errors**: {self.total_errors()}")
        lines.append(f"- **Total Warnings**: {self.total_warnings()}")
        lines.append(f"- **Tickets Generated**: {self.tickets_generated}")
        lines.append("")
        
        # Results by tier
        for tier_num in [1, 2, 3]:
            tier_results = [r for r in self.results if r.tier == tier_num]
            if not tier_results:
                continue
            
            tier_name = {1: "Algorithmic", 2: "External Tools", 3: "AI Verification"}[tier_num]
            lines.append(f"## Tier {tier_num}: {tier_name}")
            lines.append("")
            
            for result in tier_results:
                # Tool status with emoji
                tool_emoji = {
                    "PASS": "✅", "WARN": "⚠️", "FAIL": "❌", 
                    "SKIP": "⏭️", "ERROR": "🔥"
                }.get(result.status, "❓")
                
                lines.append(f"### {tool_emoji} {result.tool}")
                lines.append("")
                lines.append(f"- **Status**: {result.status}")
                lines.append(f"- **Duration**: {result.duration:.2f}s")
                lines.append(f"- **Issues**: {result.error_count()} errors, {result.warning_count()} warnings")
                lines.append("")
                
                # Show top issues (limit to 10)
                if result.issues:
                    lines.append("**Top Issues:**")
                    lines.append("")
                    for issue in result.issues[:10]:
                        severity_icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}.get(issue.severity, "•")
                        lines.append(f"- {severity_icon} `{issue.file_path}:{issue.line}` - {issue.message}")
                    
                    if len(result.issues) > 10:
                        lines.append(f"- ... and {len(result.issues) - 10} more")
                    lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Generated by Adaptive Validation System*")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "paranoia_level": self.paranoia_level,
            "project_size": self.project_size,
            "overall_status": self.overall_status(),
            "total_errors": self.total_errors(),
            "total_warnings": self.total_warnings(),
            "tickets_generated": self.tickets_generated,
            "results": [r.to_dict() for r in self.results]
        }


# ============================================================================
# TIER 1: ALGORITHMIC VALIDATION
# ============================================================================

class Tier1Validator:
    """Tier 1: Algorithmic validation using validate_docs.py."""
    
    def __init__(self, project_root: Path):
        """Initialize Tier 1 validator."""
        self.project_root = project_root  # Project root path
        self.logger = DocsLogger("tier1_validator")  # Component logger
    
    def validate(self) -> ValidationResult:
        """Run Tier 1 validation."""
        
        self.logger.info("Running Tier 1: Algorithmic validation...")
        start_time = time.time()  # Start timing
        
        try:
            # Run validate_docs.py
            validate_script = self.project_root / "docs" / "automation" / "validate_docs.py"
            
            if not validate_script.exists():
                self.logger.error(f"validate_docs.py not found: {validate_script}")
                return ValidationResult(
                    tier=1,
                    tool="validate_docs",
                    status="ERROR",
                    duration=time.time() - start_time,
                    error_message="validate_docs.py not found"
                )
            
            # Run the validation script
            result = subprocess.run(
                [sys.executable, str(validate_script), "--report", "/dev/stdout"],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=60  # 60 second timeout
            )
            
            # Parse output for issues
            issues = self._parse_output(result.stdout)
            
            # Determine status
            error_count = sum(1 for i in issues if i.severity == "ERROR")
            status = "FAIL" if error_count > 0 else ("WARN" if issues else "PASS")
            
            duration = time.time() - start_time
            self.logger.info(f"Tier 1 complete: {status} ({len(issues)} issues in {duration:.2f}s)")
            
            return ValidationResult(
                tier=1,
                tool="validate_docs",
                status=status,
                issues=issues,
                duration=duration
            )
            
        except subprocess.TimeoutExpired:
            self.logger.error("Tier 1 validation timed out")
            return ValidationResult(
                tier=1,
                tool="validate_docs",
                status="ERROR",
                duration=60.0,
                error_message="Validation timed out after 60 seconds"
            )
        except Exception as e:
            self.logger.error(f"Tier 1 validation failed: {e}")
            return ValidationResult(
                tier=1,
                tool="validate_docs",
                status="ERROR",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def _parse_output(self, output: str) -> List[ValidationIssue]:
        """Parse validate_docs.py output for issues."""
        
        issues = []  # Accumulator for found issues
        
        # Look for issue patterns in markdown output
        # Format: ### path/to/file.md followed by - **Line**: N, - **Category**: X, - **Message**: Y
        
        current_file = None
        current_issue = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            # New file section
            if line.startswith("### "):
                # Save previous issue if exists
                if current_file and current_issue.get('message'):
                    issues.append(ValidationIssue(
                        severity=self._map_severity(current_issue.get('category', '')),
                        category=current_issue.get('category', 'unknown'),
                        file_path=current_file,
                        line=current_issue.get('line', 0),
                        message=current_issue.get('message', ''),
                        suggestion=current_issue.get('suggestion', ''),
                        tool="validate_docs"
                    ))
                
                current_file = line[4:].strip()
                current_issue = {}
            
            # Parse issue details
            elif line.startswith("- **Line**:"):
                try:
                    current_issue['line'] = int(line.split(":", 1)[1].strip())
                except ValueError:
                    current_issue['line'] = 0
            elif line.startswith("- **Category**:"):
                current_issue['category'] = line.split(":", 1)[1].strip()
            elif line.startswith("- **Message**:"):
                current_issue['message'] = line.split(":", 1)[1].strip()
            elif line.startswith("- **Suggestion**:"):
                current_issue['suggestion'] = line.split(":", 1)[1].strip()
        
        # Don't forget last issue
        if current_file and current_issue.get('message'):
            issues.append(ValidationIssue(
                severity=self._map_severity(current_issue.get('category', '')),
                category=current_issue.get('category', 'unknown'),
                file_path=current_file,
                line=current_issue.get('line', 0),
                message=current_issue.get('message', ''),
                suggestion=current_issue.get('suggestion', ''),
                tool="validate_docs"
            ))
        
        return issues
    
    def _map_severity(self, category: str) -> str:
        """Map category to severity level."""
        # Error categories
        if category in ['link', 'error']:
            return "ERROR"
        # Warning categories
        elif category in ['drift', 'missing']:
            return "WARNING"
        # Info categories
        else:
            return "INFO"


# ============================================================================
# TIER 2: EXTERNAL TOOLS
# ============================================================================

class Tier2Validator:
    """Tier 2: External tool validation (ruff, mypy, markdownlint)."""
    
    def __init__(self, project_root: Path):
        """Initialize Tier 2 validator."""
        self.project_root = project_root  # Project root path
        self.logger = DocsLogger("tier2_validator")  # Component logger
    
    def validate(self) -> List[ValidationResult]:
        """Run all Tier 2 validations."""
        
        self.logger.info("Running Tier 2: External tools validation...")
        results = []  # Accumulator for results
        
        # Run each external tool
        results.append(self._run_ruff())
        results.append(self._run_mypy())
        results.append(self._run_markdownlint())
        
        return results
    
    def _run_ruff(self) -> ValidationResult:
        """Run ruff linter."""
        
        self.logger.info("Running ruff...")
        start_time = time.time()
        
        try:
            # Check if ruff is installed
            result = subprocess.run(
                ["ruff", "check", str(self.project_root), "--output-format", "json"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse JSON output
            issues = self._parse_ruff_output(result.stdout)
            
            # Determine status
            error_count = sum(1 for i in issues if i.severity == "ERROR")
            status = "FAIL" if error_count > 0 else ("WARN" if issues else "PASS")
            
            duration = time.time() - start_time
            self.logger.info(f"ruff complete: {status} ({len(issues)} issues in {duration:.2f}s)")
            
            return ValidationResult(
                tier=2,
                tool="ruff",
                status=status,
                issues=issues,
                duration=duration
            )
            
        except FileNotFoundError:
            self.logger.warning("ruff not installed, skipping")
            return ValidationResult(
                tier=2,
                tool="ruff",
                status="SKIP",
                duration=time.time() - start_time,
                error_message="ruff not installed (pip install ruff)"
            )
        except subprocess.TimeoutExpired:
            self.logger.error("ruff timed out")
            return ValidationResult(
                tier=2,
                tool="ruff",
                status="ERROR",
                duration=120.0,
                error_message="ruff timed out after 120 seconds"
            )
        except Exception as e:
            self.logger.error(f"ruff failed: {e}")
            return ValidationResult(
                tier=2,
                tool="ruff",
                status="ERROR",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def _parse_ruff_output(self, output: str) -> List[ValidationIssue]:
        """Parse ruff JSON output."""
        
        issues = []
        
        if not output.strip():
            return issues
        
        try:
            data = json.loads(output)
            
            for item in data:
                # Map ruff codes to severity (with null check)
                code = item.get("code") or ""  # Handle None
                severity = "ERROR" if code.startswith("E") else "WARNING"
                
                issues.append(ValidationIssue(
                    severity=severity,
                    category="lint",
                    file_path=item.get("filename", ""),
                    line=item.get("location", {}).get("row", 0),
                    column=item.get("location", {}).get("column", 0),
                    code=code,
                    message=item.get("message", ""),
                    tool="ruff"
                ))
                
        except json.JSONDecodeError:
            # Fallback to line-by-line parsing
            for line in output.split('\n'):
                if not line.strip():
                    continue
                
                # Try to parse: file:line:col: code message
                import re
                match = re.match(r'(.+):(\d+):(\d+): (\w+) (.+)', line)
                if match:
                    file, line_num, col, code, message = match.groups()
                    severity = "ERROR" if code.startswith("E") else "WARNING"
                    
                    issues.append(ValidationIssue(
                        severity=severity,
                        category="lint",
                        file_path=file,
                        line=int(line_num),
                        column=int(col),
                        code=code,
                        message=message,
                        tool="ruff"
                    ))
        
        return issues
    
    def _run_mypy(self) -> ValidationResult:
        """Run mypy type checker."""
        
        self.logger.info("Running mypy...")
        start_time = time.time()
        
        try:
            # Run mypy with JSON output
            result = subprocess.run(
                [
                    "mypy", 
                    str(self.project_root),
                    "--ignore-missing-imports",
                    "--no-error-summary"
                ],
                capture_output=True,
                text=True,
                timeout=180  # mypy can be slow
            )
            
            # Parse output
            issues = self._parse_mypy_output(result.stdout)
            
            # Determine status
            error_count = sum(1 for i in issues if i.severity == "ERROR")
            status = "FAIL" if error_count > 0 else ("WARN" if issues else "PASS")
            
            duration = time.time() - start_time
            self.logger.info(f"mypy complete: {status} ({len(issues)} issues in {duration:.2f}s)")
            
            return ValidationResult(
                tier=2,
                tool="mypy",
                status=status,
                issues=issues,
                duration=duration
            )
            
        except FileNotFoundError:
            self.logger.warning("mypy not installed, skipping")
            return ValidationResult(
                tier=2,
                tool="mypy",
                status="SKIP",
                duration=time.time() - start_time,
                error_message="mypy not installed (pip install mypy)"
            )
        except subprocess.TimeoutExpired:
            self.logger.error("mypy timed out")
            return ValidationResult(
                tier=2,
                tool="mypy",
                status="ERROR",
                duration=180.0,
                error_message="mypy timed out after 180 seconds"
            )
        except Exception as e:
            self.logger.error(f"mypy failed: {e}")
            return ValidationResult(
                tier=2,
                tool="mypy",
                status="ERROR",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def _parse_mypy_output(self, output: str) -> List[ValidationIssue]:
        """Parse mypy output."""
        
        issues = []
        import re
        
        for line in output.split('\n'):
            if not line.strip():
                continue
            
            # mypy format: file:line: severity: message
            match = re.match(r'(.+):(\d+): (error|warning|note): (.+)', line)
            if match:
                file, line_num, severity_str, message = match.groups()
                
                # Map mypy severity
                severity = {
                    "error": "ERROR",
                    "warning": "WARNING",
                    "note": "INFO"
                }.get(severity_str, "INFO")
                
                issues.append(ValidationIssue(
                    severity=severity,
                    category="type",
                    file_path=file,
                    line=int(line_num),
                    message=message,
                    tool="mypy"
                ))
        
        return issues
    
    def _run_markdownlint(self) -> ValidationResult:
        """Run markdownlint for documentation."""
        
        self.logger.info("Running markdownlint...")
        start_time = time.time()
        
        docs_dir = self.project_root / "docs"
        
        if not docs_dir.exists():
            self.logger.warning("docs/ directory not found, skipping markdownlint")
            return ValidationResult(
                tier=2,
                tool="markdownlint",
                status="SKIP",
                duration=time.time() - start_time,
                error_message="docs/ directory not found"
            )
        
        try:
            # Try markdownlint-cli2 first, then markdownlint
            for cmd in ["markdownlint-cli2", "markdownlint"]:
                try:
                    result = subprocess.run(
                        [cmd, str(docs_dir)],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    break
                except FileNotFoundError:
                    continue
            else:
                # Neither command found
                raise FileNotFoundError("markdownlint not installed")
            
            # Parse output
            issues = self._parse_markdownlint_output(result.stdout + result.stderr)
            
            # Determine status
            status = "WARN" if issues else "PASS"
            
            duration = time.time() - start_time
            self.logger.info(f"markdownlint complete: {status} ({len(issues)} issues in {duration:.2f}s)")
            
            return ValidationResult(
                tier=2,
                tool="markdownlint",
                status=status,
                issues=issues,
                duration=duration
            )
            
        except FileNotFoundError:
            self.logger.warning("markdownlint not installed, skipping")
            return ValidationResult(
                tier=2,
                tool="markdownlint",
                status="SKIP",
                duration=time.time() - start_time,
                error_message="markdownlint not installed (npm install -g markdownlint-cli)"
            )
        except subprocess.TimeoutExpired:
            self.logger.error("markdownlint timed out")
            return ValidationResult(
                tier=2,
                tool="markdownlint",
                status="ERROR",
                duration=60.0,
                error_message="markdownlint timed out after 60 seconds"
            )
        except Exception as e:
            self.logger.error(f"markdownlint failed: {e}")
            return ValidationResult(
                tier=2,
                tool="markdownlint",
                status="ERROR",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def _parse_markdownlint_output(self, output: str) -> List[ValidationIssue]:
        """Parse markdownlint output."""
        
        issues = []
        import re
        
        for line in output.split('\n'):
            if not line.strip():
                continue
            
            # markdownlint format: file:line code/code-name message
            match = re.match(r'(.+):(\d+):?(\d+)? (MD\d+)/([^\s]+) (.+)', line)
            if match:
                file, line_num, col, code, code_name, message = match.groups()
                
                issues.append(ValidationIssue(
                    severity="WARNING",  # Markdown issues are usually warnings
                    category="format",
                    file_path=file,
                    line=int(line_num),
                    column=int(col) if col else 0,
                    code=f"{code}/{code_name}",
                    message=message,
                    tool="markdownlint"
                ))
            else:
                # Try simpler format: file:line message
                match = re.match(r'(.+):(\d+):? (.+)', line)
                if match:
                    file, line_num, message = match.groups()
                    issues.append(ValidationIssue(
                        severity="WARNING",
                        category="format",
                        file_path=file,
                        line=int(line_num),
                        message=message,
                        tool="markdownlint"
                    ))
        
        return issues


# ============================================================================
# TIER 3: AI VALIDATION
# ============================================================================

class Tier3Validator:
    """Tier 3: AI validation using local_ai_verifier.py."""
    
    def __init__(self, project_root: Path, scope: str = "changed"):
        """Initialize Tier 3 validator."""
        self.project_root = project_root  # Project root path
        self.scope = scope  # 'changed' or 'all'
        self.logger = DocsLogger("tier3_validator")  # Component logger
    
    def validate(self) -> ValidationResult:
        """Run Tier 3 AI validation."""
        
        self.logger.info(f"Running Tier 3: AI validation (scope: {self.scope})...")
        start_time = time.time()
        
        try:
            # Check if AI verifier exists
            verifier_script = self.project_root / "utils" / "local_ai_verifier.py"
            
            if not verifier_script.exists():
                self.logger.warning("local_ai_verifier.py not found, skipping")
                return ValidationResult(
                    tier=3,
                    tool="ai_verifier",
                    status="SKIP",
                    duration=time.time() - start_time,
                    error_message="local_ai_verifier.py not found"
                )
            
            # Build command based on scope
            if self.scope == "changed":
                cmd = [sys.executable, str(verifier_script)]
            else:
                cmd = [sys.executable, str(verifier_script), "--commits", "1"]
            
            # Run AI verifier (this can take a while)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=300  # 5 minute timeout for AI
            )
            
            # Parse output for issues
            issues = self._parse_output(result.stdout)
            
            # Determine status
            error_count = sum(1 for i in issues if i.severity == "ERROR")
            status = "FAIL" if error_count > 0 else ("WARN" if issues else "PASS")
            
            duration = time.time() - start_time
            self.logger.info(f"Tier 3 complete: {status} ({len(issues)} issues in {duration:.2f}s)")
            
            return ValidationResult(
                tier=3,
                tool="ai_verifier",
                status=status,
                issues=issues,
                duration=duration
            )
            
        except subprocess.TimeoutExpired:
            self.logger.error("AI verification timed out")
            return ValidationResult(
                tier=3,
                tool="ai_verifier",
                status="ERROR",
                duration=300.0,
                error_message="AI verification timed out after 300 seconds"
            )
        except Exception as e:
            self.logger.error(f"AI verification failed: {e}")
            return ValidationResult(
                tier=3,
                tool="ai_verifier",
                status="ERROR",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    def _parse_output(self, output: str) -> List[ValidationIssue]:
        """Parse AI verifier output for issues."""
        
        issues = []
        
        # AI verifier outputs markdown report
        # Look for ## Issues Found section
        
        in_issues = False
        current_category = ""
        
        for line in output.split('\n'):
            line = line.strip()
            
            if line == "## Issues Found":
                in_issues = True
                continue
            
            if in_issues:
                # Stop at next major section
                if line.startswith("## ") and "Issues" not in line:
                    break
                
                # Category header
                if line.startswith("### "):
                    current_category = line[4:].strip().lower()
                    continue
                
                # Issue line
                if line.startswith("**") and "**:" in line:
                    # Format: **category**: message
                    parts = line.split("**:", 1)
                    if len(parts) == 2:
                        message = parts[1].strip()
                        
                        # Try to extract file from next line
                        # (simplified parsing - AI output format may vary)
                        issues.append(ValidationIssue(
                            severity="WARNING",  # AI issues are usually warnings until confirmed
                            category=current_category or "ai_check",
                            file_path="",  # May be extracted from message
                            message=message,
                            tool="ai_verifier"
                        ))
        
        return issues


# ============================================================================
# TICKET GENERATOR
# ============================================================================

class TicketGenerator:
    """Generates structured tickets from validation issues."""
    
    def __init__(self, tickets_dir: Path):
        """Initialize ticket generator."""
        self.tickets_dir = tickets_dir  # Where to save tickets
        self.tickets_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        self.logger = DocsLogger("ticket_generator")  # Component logger
        self.seen_hashes = set()  # Track seen tickets for deduplication
    
    def generate_tickets(self, results: List[ValidationResult]) -> int:
        """Generate tickets from validation results."""
        
        self.logger.info("Generating tickets from validation results...")
        tickets_created = 0
        
        # Load existing ticket hashes for deduplication
        self._load_existing_hashes()
        
        # Collect all issues that warrant tickets (ERROR and WARNING only)
        for result in results:
            for issue in result.issues:
                if issue.severity not in ["ERROR", "WARNING"]:
                    continue
                
                # Generate ticket hash for deduplication
                ticket_hash = self._hash_issue(issue)
                
                if ticket_hash in self.seen_hashes:
                    self.logger.debug(f"Skipping duplicate ticket: {issue.message[:50]}...")
                    continue
                
                # Create ticket
                ticket_path = self._create_ticket(issue, ticket_hash)
                if ticket_path:
                    tickets_created += 1
                    self.seen_hashes.add(ticket_hash)
        
        self.logger.info(f"Created {tickets_created} new tickets")
        return tickets_created
    
    def _hash_issue(self, issue: ValidationIssue) -> str:
        """Generate hash for deduplication."""
        # Hash based on file + line + message (approximate match)
        content = f"{issue.file_path}:{issue.line}:{issue.message}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _load_existing_hashes(self):
        """Load hashes from existing tickets."""
        
        for ticket_file in self.tickets_dir.glob("*.md"):
            try:
                content = ticket_file.read_text(encoding='utf-8')
                
                # Extract ticket_id from frontmatter
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        frontmatter = content[3:end]
                        for line in frontmatter.split('\n'):
                            if line.startswith("ticket_hash:"):
                                hash_value = line.split(":", 1)[1].strip()
                                self.seen_hashes.add(hash_value)
                                break
            except Exception as e:
                self.logger.debug(f"Could not read ticket {ticket_file}: {e}")
    
    def _create_ticket(self, issue: ValidationIssue, ticket_hash: str) -> Optional[Path]:
        """Create a ticket file for an issue."""
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_file = issue.file_path.replace("/", "_").replace("\\", "_")[:50] or "unknown"
        filename = f"TICKET_{timestamp}_{safe_file}_{issue.category}.md"
        
        ticket_path = self.tickets_dir / filename
        
        # Build ticket content
        content = self._build_ticket_content(issue, ticket_hash)
        
        try:
            ticket_path.write_text(content, encoding='utf-8')
            self.logger.info(f"Created ticket: {filename}")
            return ticket_path
        except Exception as e:
            self.logger.error(f"Failed to create ticket: {e}")
            return None
    
    def _build_ticket_content(self, issue: ValidationIssue, ticket_hash: str) -> str:
        """Build markdown content for a ticket."""
        
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        content = f"""---
ticket_hash: {ticket_hash}
severity: {issue.severity}
category: {issue.category}
file: {issue.file_path}
line: {issue.line}
status: open
created: {timestamp}
tool: {issue.tool}
---

# Issue: {issue.message[:80]}

## Description

{issue.message}

## Location

- **File**: `{issue.file_path}`
- **Line**: {issue.line}
- **Column**: {issue.column}
- **Code**: {issue.code or 'N/A'}

## Tool Information

- **Detected by**: {issue.tool}
- **Severity**: {issue.severity}
- **Category**: {issue.category}

## Suggested Fix

{issue.suggestion or 'No specific suggestion provided. Please review the issue and fix accordingly.'}

---

*Auto-generated by Adaptive Validation System*
"""
        
        return content


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

class AdaptiveValidationSystem:
    """Main orchestrator for multi-tier adaptive validation."""
    
    def __init__(self, project_root: Path):
        """Initialize adaptive validation system."""
        self.project_root = project_root  # Project root path
        self.logger = DocsLogger("adaptive_validation")  # Main logger
        
        # Detect project size and paranoia level
        self.project_size = self._count_project_files()
        self.auto_paranoia_level = self._detect_paranoia_level()
        
        # Ensure output directories exist
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"AdaptiveValidationSystem initialized: {self.project_size} files, auto-level: {self.auto_paranoia_level}")
    
    def _count_project_files(self) -> int:
        """Count relevant project files."""
        
        py_files = len(list(self.project_root.rglob("*.py")))
        md_files = len(list(self.project_root.rglob("*.md")))
        
        return py_files + md_files
    
    def _detect_paranoia_level(self) -> int:
        """Auto-detect appropriate paranoia level based on project size."""
        
        if self.project_size < SIZE_THRESHOLDS["minimal"]:
            return 1  # Minimal
        elif self.project_size < SIZE_THRESHOLDS["standard"]:
            return 2  # Standard
        elif self.project_size < SIZE_THRESHOLDS["thorough"]:
            return 3  # Thorough
        elif self.project_size < SIZE_THRESHOLDS["paranoid"]:
            return 4  # Paranoid
        else:
            return 5  # Maximum
    
    def validate(self, paranoia_level: int = 5) -> ValidationReport:
        """Run validation based on paranoia level.
        
        Args:
            paranoia_level: 0=auto, 1-5=manual. Default is 5 (maximum).
        """
        
        # Level 0 means auto-detect based on project size
        if paranoia_level == 0:
            level = self.auto_paranoia_level
            self.logger.info(f"Auto-detected paranoia level: {level}")
        else:
            level = paranoia_level
        
        level_config = PARANOIA_LEVELS.get(level, PARANOIA_LEVELS[5])  # Fallback to max
        
        self.logger.info(f"Starting validation at paranoia level {level} ({level_config['name']})")
        print(f"\n{'='*60}")
        print(f"🔍 Adaptive Validation System")
        print(f"{'='*60}")
        print(f"Paranoia Level: {level} ({level_config['name']})")
        if paranoia_level == 0:
            print(f"(Auto-detected from project size: {self.project_size} files)")
        print(f"Description: {level_config['description']}")
        print(f"Project Size: {self.project_size} files")
        print(f"{'='*60}\n")
        
        results = []  # Accumulator for all results
        
        # Tier 1: Always run (algorithmic)
        if 1 in level_config.get("tiers", [1]):
            print("📋 Tier 1: Algorithmic Validation...")
            tier1 = Tier1Validator(self.project_root)
            results.append(tier1.validate())
        
        # Tier 2: External tools (level >= 2)
        if 2 in level_config.get("tiers", []):
            print("🔧 Tier 2: External Tools...")
            tier2 = Tier2Validator(self.project_root)
            results.extend(tier2.validate())
        
        # Tier 3: AI validation (level >= 3)
        if 3 in level_config.get("tiers", []):
            scope = level_config.get("scope", "changed")
            print(f"🤖 Tier 3: AI Validation (scope: {scope})...")
            tier3 = Tier3Validator(self.project_root, scope=scope)
            results.append(tier3.validate())
        
        # Generate tickets from issues
        print("\n📝 Generating tickets...")
        ticket_gen = TicketGenerator(TICKETS_DIR)
        tickets_created = ticket_gen.generate_tickets(results)
        
        # Build report
        report = ValidationReport(
            timestamp=datetime.now(),
            paranoia_level=level,
            project_size=self.project_size,
            results=results,
            tickets_generated=tickets_created
        )
        
        # Save report
        self._save_report(report)
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _save_report(self, report: ValidationReport):
        """Save validation report to files."""
        
        timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Save markdown report
        md_path = OUTPUT_DIR / f"validation_report_{timestamp}.md"
        md_path.write_text(report.to_markdown(), encoding='utf-8')
        self.logger.info(f"Markdown report saved: {md_path}")
        
        # Save JSON report
        json_path = OUTPUT_DIR / f"validation_report_{timestamp}.json"
        json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding='utf-8')
        self.logger.info(f"JSON report saved: {json_path}")
        
        print(f"\n📊 Reports saved to: {OUTPUT_DIR}")
    
    def _print_summary(self, report: ValidationReport):
        """Print validation summary to console."""
        
        status = report.overall_status()
        status_emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "ERROR": "🔥"}.get(status, "❓")
        
        print(f"\n{'='*60}")
        print(f"📊 Validation Summary")
        print(f"{'='*60}")
        print(f"Status: {status_emoji} {status}")
        print(f"Errors: {report.total_errors()}")
        print(f"Warnings: {report.total_warnings()}")
        print(f"Tickets: {report.tickets_generated}")
        print(f"{'='*60}")
        
        # Print per-tool summary
        print("\nPer-Tool Results:")
        for result in report.results:
            tool_emoji = {
                "PASS": "✅", "WARN": "⚠️", "FAIL": "❌",
                "SKIP": "⏭️", "ERROR": "🔥"
            }.get(result.status, "❓")
            print(f"  {tool_emoji} {result.tool}: {result.status} ({result.error_count()} errors, {result.warning_count()} warnings)")
        
        print()


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="Adaptive Validation System - Multi-Tier Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Paranoia Levels:
  0 - Auto:     Auto-detect based on project size
  1 - Minimal:  Algorithmic checks only (fast)
  2 - Standard: Algorithmic + external tools
  3 - Thorough: All tiers, AI on changed files only
  4 - Paranoid: All tiers + deep supervisor
  5 - Maximum:  Everything + global supervisor (DEFAULT)

Examples:
  python validate_system.py              # Uses level 5 (maximum) by default
  python validate_system.py -p 0         # Auto-detect level
  python validate_system.py --paranoia 2 # Use Standard level
"""
    )
    
    parser.add_argument(
        '--paranoia', '-p',
        type=int,
        choices=[0, 1, 2, 3, 4, 5],
        default=5,  # Maximum by default - we don't save resources
        help='Paranoia level: 0=auto-detect, 1=minimal, 5=maximum (default: 5)'
    )
    
    parser.add_argument(
        '--project-root',
        type=Path,
        default=BASE_DIR,
        help='Project root directory (default: auto-detect)'
    )
    
    args = parser.parse_args()
    
    # Initialize system
    validator = AdaptiveValidationSystem(args.project_root)
    
    # Run validation with specified paranoia level (default=5, 0=auto)
    report = validator.validate(paranoia_level=args.paranoia)
    
    # Exit with appropriate code
    status = report.overall_status()
    if status == "FAIL" or status == "ERROR":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
