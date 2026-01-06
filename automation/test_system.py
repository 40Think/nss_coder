#!/usr/bin/env python3
"""
Documentation System Test Runner - Two-Layer Logging and AI Analysis

<!--TAG:tool_test_system-->

PURPOSE:
    Comprehensive test runner for the NSS-DOCS documentation system.
    Implements two-layer logging architecture:
    - Layer 1: Paranoid logging for forensic traceability
    - Layer 2: AI-powered analysis (Vertical + Horizontal)
    
    Supports multiple paranoia levels for adaptive testing depth.

DOCUMENTATION:
    Spec: docs/specs/Automation_Tools_Spec.md
    Wiki: docs/wiki/09_Documentation_System.md
    Logging: docs/logging_system/README.MD

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger (DocsLogger for paranoid logging)
        - docs.utils.docs_deep_supervisor (optional, for vertical AI analysis)
        - docs.utils.docs_global_supervisor (optional, for horizontal AI analysis)
    Config:
        - None (uses project_root auto-detection)
    Data:
        - Input: docs/automation/*.py (scripts to test)
        - Output: docs/logs/intellectual/{timestamp}.md
    External:
        - None

RECENT CHANGES:
    2025-12-12: Fixed import (ParanoidLogger → DocsLogger) for NSS-DOCS isolation

TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:logging--> <!--TAG:automation--> <!--TAG:testing--> <!--TAG:validation--> <!--TAG:two_layer_logging-->

<!--/TAG:tool_test_system-->
"""

import subprocess
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import paranoid logger for Layer 1
from utils.docs_logger import DocsLogger

# Try to import supervisors for Layer 2
try:
    # DocsDeepSupervisor - temporarily disabled for standalone mode
# from utils.docs_deep_supervisor import DocsDeepSupervisor
    DEEP_SUPERVISOR_AVAILABLE = True
except ImportError:
    DEEP_SUPERVISOR_AVAILABLE = False

try:
    # DocsGlobalSupervisor - temporarily disabled for standalone mode
# from utils.docs_global_supervisor import DocsGlobalSupervisor
    GLOBAL_SUPERVISOR_AVAILABLE = True
except ImportError:
    GLOBAL_SUPERVISOR_AVAILABLE = False

# Initialize logger with DocsLogger for NSS-DOCS isolation
logger = DocsLogger("test_system")


class DocumentationSystemTester:
    """
    Enhanced test runner for documentation system with two-layer logging.
    
    Paranoia Levels:
    - Level 1: Basic execution tests only
    - Level 2: + Structural validation  
    - Level 3: + Deep Supervisor (Vertical Analysis)
    - Level 4: + Global Supervisor (Horizontal Analysis)
    - Level 5: + Full AI analysis with detailed reports
    """
    
    def __init__(self, project_root: Path, paranoia_level: int = 3):
        """
        Initialize the test runner.
        
        Args:
            project_root: Path to project root directory
            paranoia_level: Testing depth level (1-5)
        """
        self.project_root = project_root
        self.automation_dir = project_root / 'docs' / 'automation'
        self.paranoia_level = min(max(paranoia_level, 1), 5)  # Clamp to 1-5
        self.results: List[Tuple[str, bool, str]] = []
        self.start_time = time.time()
        
        # Log initialization
        logger.log_step("TestSystem Init", "STARTED", 0, 0, {
            "project_root": str(project_root),
            "paranoia_level": self.paranoia_level
        })
        logger.info(f"Initialized with paranoia level {self.paranoia_level}")
        
    def run_all_tests(self) -> int:
        """
        Run all documentation system tests based on paranoia level.
        
        Returns:
            Exit code (0 = success, 1 = failures)
        """
        print(f"\n{'='*70}")
        print("📊 DOCUMENTATION SYSTEM TEST SUITE")
        print(f"{'='*70}")
        print(f"Paranoia Level: {self.paranoia_level}/5")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        logger.info("="*60)
        logger.info("DOCUMENTATION SYSTEM TEST SUITE - TWO-LAYER LOGGING")
        logger.info(f"Paranoia Level: {self.paranoia_level}/5")
        logger.info("="*60)
        
        # Layer 1: Basic Tests (Level 1+)
        print("📋 PHASE 1: Basic Execution Tests")
        print("-" * 40)
        self._run_basic_tests()
        
        # Structural Tests (Level 2+)
        if self.paranoia_level >= 2:
            print("\n📁 PHASE 2: Structural Validation")
            print("-" * 40)
            self._run_structural_tests()
        
        # Layer 2: AI Analysis
        if self.paranoia_level >= 3:
            print("\n🔬 PHASE 3: AI-Powered Analysis")
            print("-" * 40)
            self._run_ai_analysis()
        
        # Generate intellectual log
        self._generate_intellectual_log()
        
        # Print results
        return self._print_results()
    
    def _run_basic_tests(self):
        """Run basic execution tests for automation scripts."""
        logger.log_step("Basic Tests", "STARTED", 0, 0)
        
        # Test 1: Dependency Analysis
        self._test_script_execution(
            "Dependency Analysis",
            self.automation_dir / 'analyze_dependencies.py',
            ['--target', str(self.project_root / 'utils' / 'paranoid_logger.py')]
        )
        
        # Test 2: Document Chunking
        self._test_script_execution(
            "Document Chunking",
            self.automation_dir / 'chunk_documents.py',
            ['--input-dir', 'docs/wiki', '--output-dir', '/tmp/test_chunks']
        )
        
        # Test 3: Documentation Validation
        self._test_script_execution(
            "Documentation Validation",
            self.automation_dir / 'validate_docs.py',
            ['--report', '/tmp/test_validation_report.md']
        )
        
        logger.log_step("Basic Tests", "COMPLETED", time.time() - self.start_time, 0)
    
    def _run_structural_tests(self):
        """Run structural validation tests."""
        logger.log_step("Structural Tests", "STARTED", 0, 0)
        
        # Test 4: Directory Structure
        self._test_directory_structure()
        
        # Test 5: README Files
        self._test_readme_files()
        
        # Test 6: Log Directories
        self._test_log_directories()
        
        logger.log_step("Structural Tests", "COMPLETED", time.time() - self.start_time, 0)
    
    def _run_ai_analysis(self):
        """Run AI-powered analysis (Layer 2)."""
        logger.log_step("AI Analysis", "STARTED", 0, 0)
        
        # Deep Supervisor (Vertical Analysis) - Level 3+
        if self.paranoia_level >= 3 and DEEP_SUPERVISOR_AVAILABLE:
            print("\n  🔍 Running Deep Supervisor (Vertical Analysis)...")
            logger.info("Starting Deep Supervisor")
            
            try:
                sample_size = 5 if self.paranoia_level == 3 else 10 if self.paranoia_level == 4 else 20
                supervisor = DocsDeepSupervisor()
                success = supervisor.run(sample_size=sample_size)
                
                if success:
                    self.results.append(("Deep Supervisor", True, f"Analyzed {sample_size} files"))
                    logger.info(f"Deep Supervisor completed: {sample_size} files analyzed")
                    print(f"     ✅ Deep Supervisor: Analyzed {sample_size} files")
                else:
                    self.results.append(("Deep Supervisor", False, "No files to analyze"))
                    logger.warning("Deep Supervisor: No files to analyze")
                    print("     ⚠️  Deep Supervisor: No files to analyze")
                    
            except Exception as e:
                self.results.append(("Deep Supervisor", False, str(e)[:100]))
                logger.error(f"Deep Supervisor failed: {e}")
                print(f"     ❌ Deep Supervisor failed: {str(e)[:50]}...")
        elif self.paranoia_level >= 3:
            print("  ⚠️  Deep Supervisor not available (import failed)")
            logger.warning("Deep Supervisor not available")
        
        # Global Supervisor (Horizontal Analysis) - Level 4+
        if self.paranoia_level >= 4 and GLOBAL_SUPERVISOR_AVAILABLE:
            print("\n  🌍 Running Global Supervisor (Horizontal Analysis)...")
            logger.info("Starting Global Supervisor")
            
            try:
                supervisor = DocsGlobalSupervisor()
                success = supervisor.supervise()
                
                if success:
                    self.results.append(("Global Supervisor", True, "Executive summary generated"))
                    logger.info("Global Supervisor completed")
                    print("     ✅ Global Supervisor: Executive summary generated")
                else:
                    self.results.append(("Global Supervisor", False, "Failed to generate summary"))
                    logger.warning("Global Supervisor failed")
                    print("     ⚠️  Global Supervisor failed")
                    
            except Exception as e:
                self.results.append(("Global Supervisor", False, str(e)[:100]))
                logger.error(f"Global Supervisor failed: {e}")
                print(f"     ❌ Global Supervisor failed: {str(e)[:50]}...")
        elif self.paranoia_level >= 4:
            print("  ⚠️  Global Supervisor not available (import failed)")
            logger.warning("Global Supervisor not available")
        
        logger.log_step("AI Analysis", "COMPLETED", time.time() - self.start_time, 0)
    
    def _test_script_execution(self, name: str, script_path: Path, args: List[str]):
        """
        Test that a script executes successfully.
        
        Args:
            name: Test name for reporting
            script_path: Path to the script to test
            args: Command line arguments for the script
        """
        test_start = time.time()
        logger.info(f"Testing: {name}")
        
        if not script_path.exists():
            self.results.append((name, False, "Script not found"))
            logger.error(f"  ❌ {name}: Script not found")
            print(f"  ❌ {name}: Script not found")
            return
        
        try:
            # Run the script
            result = subprocess.run(
                [sys.executable, str(script_path)] + args,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_root)
            )
            
            duration = time.time() - test_start
            
            if result.returncode == 0:
                self.results.append((name, True, f"Duration: {duration:.2f}s"))
                logger.log_step(f"Test {name}", "COMPLETED", duration, 0)
                logger.info(f"  ✅ {name}: PASS ({duration:.2f}s)")
                print(f"  ✅ {name}: PASS ({duration:.2f}s)")
            else:
                error_msg = result.stderr[:200] if result.stderr else "Unknown error"
                self.results.append((name, False, error_msg))
                logger.log_step(f"Test {name}", "FAILED", duration, 0)
                logger.error(f"  ❌ {name}: FAIL - {error_msg[:80]}")
                print(f"  ❌ {name}: FAIL")
                
        except subprocess.TimeoutExpired:
            self.results.append((name, False, "Timeout (60s)"))
            logger.error(f"  ❌ {name}: Timeout")
            print(f"  ❌ {name}: Timeout")
        except Exception as e:
            self.results.append((name, False, str(e)))
            logger.error(f"  ❌ {name}: {e}")
            print(f"  ❌ {name}: Error - {str(e)[:50]}")
    
    def _test_directory_structure(self):
        """Test that all required directories exist."""
        logger.info("Testing: Directory Structure")
        
        required_dirs = [
            'docs',
            'docs/automation',
            'docs/diagrams',
            'docs/memory',
            'docs/technical_debt',
            'docs/specs',
            'docs/wiki',
            'docs/developer_diary',
            'logs/paranoid',
            'logs/intellectual',
        ]
        
        missing = []
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing.append(dir_path)
                logger.warning(f"Missing directory: {dir_path}")
        
        if not missing:
            self.results.append(("Directory Structure", True, f"{len(required_dirs)} directories verified"))
            logger.info(f"  ✅ Directory Structure: All {len(required_dirs)} directories exist")
            print(f"  ✅ Directory Structure: All {len(required_dirs)} directories exist")
        else:
            self.results.append(("Directory Structure", False, f"Missing: {', '.join(missing[:3])}"))
            logger.error(f"  ❌ Directory Structure: Missing {len(missing)} directories")
            print(f"  ❌ Directory Structure: Missing {len(missing)} directories")
    
    def _test_readme_files(self):
        """Test that all required README files exist."""
        logger.info("Testing: README Files")
        
        required_readmes = [
            'docs/README.MD',
            'docs/automation/README.MD',
            'docs/specs/README.MD',
            'docs/wiki/README.MD',
        ]
        
        missing = []
        for readme_path in required_readmes:
            full_path = self.project_root / readme_path
            # Check both .MD and .md variants
            if not full_path.exists() and not (self.project_root / readme_path.replace('.MD', '.md')).exists():
                missing.append(readme_path)
        
        if not missing:
            self.results.append(("README Files", True, f"{len(required_readmes)} READMEs verified"))
            logger.info(f"  ✅ README Files: All core READMEs exist")
            print(f"  ✅ README Files: All core READMEs exist")
        else:
            self.results.append(("README Files", False, f"Missing: {', '.join(missing[:2])}"))
            logger.warning(f"  ⚠️  README Files: Missing {len(missing)} files")
            print(f"  ⚠️  README Files: Missing {len(missing)} files")
    
    def _test_log_directories(self):
        """Test that logging directories exist and are writable."""
        logger.info("Testing: Log Directories")
        
        log_dirs = [
            'logs/paranoid',
            'logs/intellectual',
            'llm_requests',
            'output/deep_supervision',
            'output/global_supervision',
        ]
        
        issues = []
        for dir_path in log_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                # Try to create it
                try:
                    full_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created missing directory: {dir_path}")
                except Exception as e:
                    issues.append(f"{dir_path}: {e}")
        
        if not issues:
            self.results.append(("Log Directories", True, f"{len(log_dirs)} directories ready"))
            logger.info(f"  ✅ Log Directories: All ready")
            print(f"  ✅ Log Directories: All ready")
        else:
            self.results.append(("Log Directories", False, issues[0]))
            logger.error(f"  ❌ Log Directories: {issues[0]}")
            print(f"  ❌ Log Directories: Issues found")
    
    def _generate_intellectual_log(self):
        """Generate intellectual log summary for this test run."""
        duration = time.time() - self.start_time
        
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        log_content = f"""# Intellectual Log: test_system

## Session Statistics
- **Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Duration**: {duration:.2f}s
- **Paranoia Level**: {self.paranoia_level}/5

## Results Summary
- Tests Run: {total}
- Passed: {passed}
- Failed: {total - passed}
- Success Rate: {success_rate:.1f}%

## Individual Results
"""
        for name, success, message in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            log_content += f"- {status}: {name} - {message[:60]}\n"
        
        log_content += f"""
## Paranoia Level Details
- Level 1: Basic execution tests {'✓' if self.paranoia_level >= 1 else '○'}
- Level 2: Structural validation {'✓' if self.paranoia_level >= 2 else '○'}
- Level 3: Deep Supervisor (vertical) {'✓' if self.paranoia_level >= 3 else '○'}
- Level 4: Global Supervisor (horizontal) {'✓' if self.paranoia_level >= 4 else '○'}
- Level 5: Full AI analysis {'✓' if self.paranoia_level >= 5 else '○'}
"""
        
        # Save intellectual log
        log_dir = self.project_root / "logs" / "intellectual"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"test_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        log_file.write_text(log_content, encoding='utf-8')
        
        logger.log_file_interaction(str(log_file), "save_intellectual_log", "SUCCESS")
    
    def _print_results(self) -> int:
        """
        Print test results summary.
        
        Returns:
            Exit code (0 = all passed, 1 = some failed)
        """
        duration = time.time() - self.start_time
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        print(f"\n{'='*70}")
        print("📊 TEST RESULTS SUMMARY")
        print(f"{'='*70}")
        
        for test_name, success, message in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status}: {test_name}")
            if not success and message:
                print(f"       {message[:70]}")
        
        print(f"\n{'='*70}")
        print(f"TOTAL: {passed}/{total} tests passed ({passed*100//total if total > 0 else 0}%)")
        print(f"Duration: {duration:.2f}s")
        print(f"Paranoia Level: {self.paranoia_level}/5")
        print(f"{'='*70}")
        
        logger.log_step("TestSystem", "COMPLETED", duration, 0, {
            "passed": passed,
            "total": total,
            "paranoia_level": self.paranoia_level
        })
        
        if passed == total:
            print("\n🎉 All tests passed! Documentation system is ready.")
            logger.info("All tests passed!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
            logger.warning(f"{total - passed} tests failed")
            return 1


def main():
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Documentation System Test Runner with Two-Layer Logging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Paranoia Levels:
  1 - Basic execution tests only
  2 - + Structural validation
  3 - + Deep Supervisor (Vertical Analysis)
  4 - + Global Supervisor (Horizontal Analysis)
  5 - Full AI analysis with detailed reports [DEFAULT]

Examples:
  python3 test_system.py                    # Run with default level (3)
  python3 test_system.py -p 5              # Full paranoid mode
  python3 test_system.py --paranoia 1      # Quick basic tests
"""
    )
    parser.add_argument(
        '-p', '--paranoia',
        type=int,
        default=5,
        choices=[1, 2, 3, 4, 5],
        help='Paranoia level (1-5, default: 5)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Enable verbose output (DocsLogger handles console logging internally)
    if args.verbose:
        global logger
        logger = DocsLogger("test_system")
    
    # Run tests
    project_root = Path(__file__).parent.parent
    tester = DocumentationSystemTester(project_root, paranoia_level=args.paranoia)
    exit_code = tester.run_all_tests()
    
    # Print stats summary
    logger.print_stats_summary()
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
