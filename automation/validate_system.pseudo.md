# Validate System Pseudocode

<!--TAG:pseudocode_validate_system-->

---
script: validate_system.py
source_file: docs/automation/validate_system.py
version: "2.0"
date: 2025-12-12
status: synced
complexity: high
---

## Purpose

Multi-tier adaptive validation system that orchestrates algorithmic validation, 
external tools (ruff, mypy, markdownlint), and AI-based verification. Supports 
configurable paranoia levels (0-5) with default maximum validation.

## Data Structures

```
DATACLASS ValidationIssue:
    """Single validation issue found by any tool."""
    severity: STRING     # 'ERROR', 'WARNING', 'INFO'
    category: STRING     # 'code_quality', 'docs_sync', 'link', 'format', 'type', 'lint'
    file_path: STRING    # Path to file with issue
    line: INTEGER = 0    # Line number (0 if not applicable)
    column: INTEGER = 0  # Column number (0 if not applicable)
    code: STRING = ""    # Error code (e.g., 'E501', 'MD001')
    message: STRING = "" # Description of the issue
    suggestion: STRING = ""  # Suggested fix
    tool: STRING = ""    # Tool that found the issue

DATACLASS ValidationResult:
    """Result from running a single validation tool."""
    tier: INTEGER        # Which tier (1, 2, or 3)
    tool: STRING         # Tool name ('validate_docs', 'ruff', 'mypy', etc.)
    status: STRING       # 'PASS', 'WARN', 'FAIL', 'SKIP', 'ERROR'
    issues: LIST[ValidationIssue]  # Found issues
    duration: FLOAT = 0.0          # Seconds
    error_message: STRING = ""     # Error if status is ERROR

DATACLASS ValidationReport:
    """Complete validation report from all tiers."""
    timestamp: DATETIME
    paranoia_level: INTEGER    # 0-5
    project_size: INTEGER      # Number of files
    results: LIST[ValidationResult]
    tickets_generated: INTEGER = 0
```

## Paranoia Levels

| Level | Name     | Tiers   | AI Scope | Description |
|-------|----------|---------|----------|-------------|
| 0     | Auto     | varies  | varies   | Auto-detect based on project size |
| 1     | Minimal  | [1]     | none     | Algorithmic only |
| 2     | Standard | [1,2]   | none     | + external tools (ruff, mypy, markdownlint) |
| 3     | Thorough | [1,2,3] | changed  | + AI on changed files only |
| 4     | Paranoid | [1,2,3] | all      | + deep supervisor |
| 5     | Maximum  | [1,2,3] | all      | + global supervisor **(DEFAULT)** |

## Class: Tier1Validator

```
CLASS Tier1Validator:
    """Tier 1: Algorithmic validation using validate_docs.py"""
    
    INIT(project_root: PATH):
        self.project_root = project_root
        self.logger = DocsLogger("tier1_validator")
    
    METHOD validate() -> ValidationResult:
        """Run algorithmic validation via validate_docs.py"""
        
        start_time = time.now()
        script = project_root / "docs/automation/validate_docs.py"
        
        IF script NOT EXISTS:
            RETURN ValidationResult(tier=1, tool="validate_docs", status="ERROR")
        
        TRY:
            result = subprocess.run([python, script, "--report", "/dev/stdout"])
            issues = _parse_output(result.stdout)
            status = "FAIL" IF errors > 0 ELSE ("WARN" IF issues ELSE "PASS")
            RETURN ValidationResult(tier=1, tool="validate_docs", status, issues)
        EXCEPT TimeoutExpired:
            RETURN ValidationResult(status="ERROR", error_message="Timeout 60s")
    
    METHOD _parse_output(output: STRING) -> LIST[ValidationIssue]:
        """Parse markdown output from validate_docs.py"""
        # Parses: ### path/to/file followed by - **Line**: N, etc.
```

## Class: Tier2Validator

```
CLASS Tier2Validator:
    """Tier 2: External tool validation (ruff, mypy, markdownlint)"""
    
    INIT(project_root: PATH):
        self.project_root = project_root
        self.logger = DocsLogger("tier2_validator")
    
    METHOD validate() -> LIST[ValidationResult]:
        """Run all Tier 2 validations"""
        results = []
        results.append(_run_ruff())
        results.append(_run_mypy())
        results.append(_run_markdownlint())
        RETURN results
    
    METHOD _run_ruff() -> ValidationResult:
        """Run ruff linter with JSON output"""
        TRY:
            result = subprocess.run(["ruff", "check", project_root, "--output-format", "json"])
            issues = _parse_ruff_output(result.stdout)
            RETURN ValidationResult(tier=2, tool="ruff", status, issues)
        EXCEPT FileNotFoundError:
            RETURN ValidationResult(tier=2, tool="ruff", status="SKIP", 
                                    error_message="ruff not installed")
    
    METHOD _run_mypy() -> ValidationResult:
        """Run mypy type checker"""
        # Similar pattern: subprocess, parse output, handle FileNotFoundError
    
    METHOD _run_markdownlint() -> ValidationResult:
        """Run markdownlint for documentation"""
        # Tries markdownlint-cli2 first, then markdownlint
        # Parses: file:line code/code-name message
```

## Class: Tier3Validator

```
CLASS Tier3Validator:
    """Tier 3: AI validation using local_ai_verifier.py"""
    
    INIT(project_root: PATH, scope: STRING = "changed"):
        self.project_root = project_root
        self.scope = scope  # 'changed' or 'all'
        self.logger = DocsLogger("tier3_validator")
    
    METHOD validate() -> ValidationResult:
        """Run AI-based validation"""
        
        verifier = project_root / "utils/local_ai_verifier.py"
        
        IF verifier NOT EXISTS:
            RETURN ValidationResult(status="SKIP")
        
        TRY:
            IF scope == "changed":
                cmd = [python, verifier]
            ELSE:
                cmd = [python, verifier, "--commits", "1"]
            
            result = subprocess.run(cmd, timeout=300)
            issues = _parse_output(result.stdout)
            RETURN ValidationResult(tier=3, tool="ai_verifier", status, issues)
        EXCEPT TimeoutExpired:
            RETURN ValidationResult(status="ERROR", error_message="Timeout 300s")
```

## Class: TicketGenerator

```
CLASS TicketGenerator:
    """Generates structured tickets from validation issues"""
    
    INIT(tickets_dir: PATH):
        self.tickets_dir = tickets_dir
        tickets_dir.mkdir(parents=True, exist_ok=True)
        self.seen_hashes = SET()
    
    METHOD generate_tickets(results: LIST[ValidationResult]) -> INTEGER:
        """Generate tickets from validation results"""
        
        _load_existing_hashes()  # Deduplication
        tickets_created = 0
        
        FOR result IN results:
            FOR issue IN result.issues:
                IF issue.severity NOT IN ["ERROR", "WARNING"]:
                    CONTINUE
                
                ticket_hash = _hash_issue(issue)
                IF ticket_hash IN seen_hashes:
                    CONTINUE  # Skip duplicate
                
                ticket_path = _create_ticket(issue, ticket_hash)
                IF ticket_path:
                    tickets_created += 1
                    seen_hashes.add(ticket_hash)
        
        RETURN tickets_created
    
    METHOD _hash_issue(issue: ValidationIssue) -> STRING:
        """Generate MD5 hash for deduplication"""
        content = f"{issue.file_path}:{issue.line}:{issue.message}"
        RETURN md5(content)[:12]
    
    METHOD _create_ticket(issue, ticket_hash) -> PATH:
        """Create markdown ticket file with YAML frontmatter"""
        # Filename: TICKET_{timestamp}_{file}_{category}.md
```

## Class: AdaptiveValidationSystem

```
CLASS AdaptiveValidationSystem:
    """Main orchestrator for multi-tier adaptive validation"""
    
    INIT(project_root: PATH):
        self.project_root = project_root
        self.logger = DocsLogger("adaptive_validation")
        self.project_size = _count_project_files()
        self.auto_paranoia_level = _detect_paranoia_level()
    
    METHOD validate(paranoia_level: INTEGER = 5) -> ValidationReport:
        """Run validation based on paranoia level.
        
        Args:
            paranoia_level: 0=auto, 1-5=manual. Default is 5 (maximum).
        """
        
        # Level 0 means auto-detect based on project size
        IF paranoia_level == 0:
            level = self.auto_paranoia_level
        ELSE:
            level = paranoia_level
        
        level_config = PARANOIA_LEVELS[level]
        results = []
        
        # Tier 1: Always run (algorithmic)
        IF 1 IN level_config.tiers:
            tier1 = Tier1Validator(project_root)
            results.append(tier1.validate())
        
        # Tier 2: External tools (level >= 2)
        IF 2 IN level_config.tiers:
            tier2 = Tier2Validator(project_root)
            results.extend(tier2.validate())
        
        # Tier 3: AI validation (level >= 3)
        IF 3 IN level_config.tiers:
            scope = level_config.scope  # 'changed' or 'all'
            tier3 = Tier3Validator(project_root, scope)
            results.append(tier3.validate())
        
        # Generate tickets from issues
        ticket_gen = TicketGenerator(TICKETS_DIR)
        tickets_created = ticket_gen.generate_tickets(results)
        
        # Build and save report
        report = ValidationReport(datetime.now(), level, project_size, results, tickets_created)
        _save_report(report)
        _print_summary(report)
        
        RETURN report
    
    METHOD _detect_paranoia_level() -> INTEGER:
        """Auto-detect level based on file count"""
        IF file_count < 50:   RETURN 1   # Minimal
        IF file_count < 200:  RETURN 2   # Standard
        IF file_count < 500:  RETURN 3   # Thorough
        IF file_count < 1000: RETURN 4   # Paranoid
        ELSE:                 RETURN 5   # Maximum
```

## CLI Interface

```
ARGUMENTS:
    --paranoia, -p    INTEGER    Paranoia level (0-5, default: 5)
                                 0 = auto-detect from project size
                                 1-5 = manual selection
    --project-root    PATH       Project root directory (default: auto-detect)

EXAMPLES:
    python validate_system.py              # Uses level 5 (maximum) by default
    python validate_system.py -p 0         # Auto-detect level
    python validate_system.py --paranoia 2 # Use Standard level
```

## Output Format

```
============================================================
🔍 Adaptive Validation System
============================================================
Paranoia Level: 5 (Maximum)
Description: Everything + global supervisor
Project Size: 234 files
============================================================

📋 Tier 1: Algorithmic Validation...
🔧 Tier 2: External Tools...
🤖 Tier 3: AI Validation (scope: all)...

📝 Generating tickets...

============================================================
📊 Validation Summary
============================================================
Status: ❌ FAIL
Errors: 463
Warnings: 638
Tickets: 930
============================================================

Per-Tool Results:
  ✅ validate_docs: PASS (0 errors, 0 warnings)
  ❌ ruff: FAIL (462 errors, 638 warnings)
  ❌ mypy: FAIL (1 errors, 0 warnings)
  ⏭️ markdownlint: SKIP (not installed)
```

## File Dependencies

| Type | Path | Purpose |
|------|------|---------|
| Internal | docs/automation/validate_docs.py | Tier 1 validation |
| Internal | utils/local_ai_verifier.py | Tier 3 AI validation |
| External | ruff | Python linter (Tier 2) |
| External | mypy | Type checker (Tier 2) |
| External | markdownlint-cli | Markdown linter (Tier 2) |
| Output | output/validation/ | Reports (JSON, Markdown) |
| Output | docs/technical_debt/tickets/ | Auto-generated tickets |

<!--/TAG:pseudocode_validate_system-->
