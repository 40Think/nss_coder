---
description: "Test runner с двухслойным логированием для валидации системы документации"
date: 2025-12-12
source_file: test_system.py
version: "2.0"
tags: automation, testing, validation, two-layer-logging, paranoia-levels
---

# test_system.py - Псевдокод

<!--TAG:pseudo_test_system-->

## PURPOSE

Тестирует все automation-скрипты и валидирует целостность системы документации.
Реализует двухслойную архитектуру логирования:
- **Layer 1**: Paranoid logging для forensic traceability
- **Layer 2**: AI-powered analysis (Vertical + Horizontal)

Поддерживает 5 уровней паранойи для адаптивной глубины тестирования.

## PARANOIA LEVELS

| Level | Name | Description |
|-------|------|-------------|
| 1 | Basic | Базовые тесты выполнения скриптов |
| 2 | Structural | + Валидация структуры директорий |
| 3 | Deep (DEFAULT) | + Deep Supervisor (Vertical Analysis) |
| 4 | Full | + Global Supervisor (Horizontal Analysis) |
| 5 | Maximum | + Полный AI анализ с детальными отчётами |

## КЛАСС: DocumentationSystemTester

### Инициализация
```pseudo
CLASS DocumentationSystemTester:
    FUNCTION __init__(project_root: Path, paranoia_level: INT = 5):
        self.project_root = project_root
        self.automation_dir = project_root / 'docs' / 'automation'
        self.paranoia_level = CLAMP(paranoia_level, 1, 5)  # Ограничить 1-5
        self.results: LIST[TUPLE[STRING, BOOL, STRING]] = []  # (name, success, message)
        self.start_time = CURRENT_TIME()
        
        # Log initialization
        LOG_STEP "TestSystem Init" WITH {
            project_root: str(project_root),
            paranoia_level: self.paranoia_level
        }
```

### run_all_tests - Запуск всех тестов по уровням
```pseudo
FUNCTION run_all_tests() -> INT:
    PRINT banner "Documentation System Test Suite"
    PRINT "Paranoia Level: {self.paranoia_level}/5"
    PRINT "Started: {CURRENT_DATETIME}"
    
    # ========================================
    # PHASE 1: Basic Execution Tests (Level 1+)
    # ========================================
    PRINT "📋 PHASE 1: Basic Execution Tests"
    CALL _run_basic_tests()
    
    # ========================================
    # PHASE 2: Structural Validation (Level 2+)
    # ========================================
    IF self.paranoia_level >= 2:
        PRINT "📁 PHASE 2: Structural Validation"
        CALL _run_structural_tests()
    
    # ========================================
    # PHASE 3: AI-Powered Analysis (Level 3+)
    # ========================================
    IF self.paranoia_level >= 3:
        PRINT "🔬 PHASE 3: AI-Powered Analysis"
        CALL _run_ai_analysis()
    
    # Generate intellectual log
    CALL _generate_intellectual_log()
    
    # Print results and return exit code
    RETURN CALL _print_results()
```

### _run_basic_tests - Базовые тесты выполнения
```pseudo
FUNCTION _run_basic_tests():
    LOG_STEP "Basic Tests" STATUS "STARTED"
    
    # Test 1: Dependency Analysis
    CALL _test_script_execution(
        name = "Dependency Analysis",
        script = self.automation_dir / 'analyze_dependencies.py',
        args = ['--target', str(self.project_root / 'utils' / 'paranoid_logger.py')]
    )
    
    # Test 2: Document Chunking
    CALL _test_script_execution(
        name = "Document Chunking",
        script = self.automation_dir / 'chunk_documents.py',
        args = ['--input-dir', 'docs/wiki', '--output-dir', '/tmp/test_chunks']
    )
    
    # Test 3: Documentation Validation
    CALL _test_script_execution(
        name = "Documentation Validation",
        script = self.automation_dir / 'validate_docs.py',
        args = ['--report', '/tmp/test_validation_report.md']
    )
    
    LOG_STEP "Basic Tests" STATUS "COMPLETED"
```

### _run_structural_tests - Структурные тесты
```pseudo
FUNCTION _run_structural_tests():
    LOG_STEP "Structural Tests" STATUS "STARTED"
    
    CALL _test_directory_structure()
    CALL _test_readme_files()
    CALL _test_log_directories()
    
    LOG_STEP "Structural Tests" STATUS "COMPLETED"
```

### _run_ai_analysis - AI анализ (Layer 2)
```pseudo
FUNCTION _run_ai_analysis():
    LOG_STEP "AI Analysis" STATUS "STARTED"
    
    # Deep Supervisor (Vertical Analysis) - Level 3+
    IF self.paranoia_level >= 3 AND DEEP_SUPERVISOR_AVAILABLE:
        PRINT "  🔍 Running Deep Supervisor (Vertical Analysis)..."
        
        TRY:
            # Sample size зависит от уровня паранойи
            sample_size = 5 IF level == 3 ELSE 10 IF level == 4 ELSE 20
            supervisor = NEW DocsDeepSupervisor()
            success = supervisor.run(sample_size)
            
            IF success:
                APPEND ("Deep Supervisor", True, "Analyzed {sample_size} files") TO results
                PRINT "  ✅ Deep Supervisor: Analyzed {sample_size} files"
            ELSE:
                APPEND ("Deep Supervisor", False, "No files to analyze") TO results
        
        CATCH Exception as e:
            APPEND ("Deep Supervisor", False, str(e)[:100]) TO results
            PRINT "  ❌ Deep Supervisor failed"
    
    # Global Supervisor (Horizontal Analysis) - Level 4+
    IF self.paranoia_level >= 4 AND GLOBAL_SUPERVISOR_AVAILABLE:
        PRINT "  🌍 Running Global Supervisor (Horizontal Analysis)..."
        
        TRY:
            supervisor = NEW DocsGlobalSupervisor()
            success = supervisor.supervise()
            
            IF success:
                APPEND ("Global Supervisor", True, "Executive summary generated") TO results
            ELSE:
                APPEND ("Global Supervisor", False, "Failed to generate summary") TO results
        
        CATCH Exception as e:
            APPEND ("Global Supervisor", False, str(e)[:100]) TO results
    
    LOG_STEP "AI Analysis" STATUS "COMPLETED"
```

### _test_script_execution - Тест выполнения скрипта
```pseudo
FUNCTION _test_script_execution(name: STRING, script_path: Path, args: LIST[STRING]):
    test_start = CURRENT_TIME()
    LOG "Testing: {name}"
    
    # Проверить существование скрипта
    IF NOT script_path.exists():
        APPEND (name, False, "Script not found") TO results
        PRINT "  ❌ {name}: Script not found"
        RETURN
    
    TRY:
        # Запустить скрипт как subprocess
        result = subprocess.run(
            [sys.executable, str(script_path)] + args,
            capture_output = True,
            text = True,
            timeout = 60,
            cwd = str(self.project_root)
        )
        
        duration = CURRENT_TIME() - test_start
        
        IF result.returncode == 0:
            APPEND (name, True, "Duration: {duration:.2f}s") TO results
            PRINT "  ✅ {name}: PASS ({duration:.2f}s)"
        ELSE:
            error_msg = result.stderr[:200] OR "Unknown error"
            APPEND (name, False, error_msg) TO results
            PRINT "  ❌ {name}: FAIL"
    
    CATCH subprocess.TimeoutExpired:
        APPEND (name, False, "Timeout (60s)") TO results
        PRINT "  ❌ {name}: Timeout"
    
    CATCH Exception as e:
        APPEND (name, False, str(e)) TO results
        PRINT "  ❌ {name}: Error"
```

### _test_directory_structure - Тест структуры директорий
```pseudo
FUNCTION _test_directory_structure():
    LOG "Testing: Directory Structure"
    
    required_dirs = [
        'docs', 'docs/automation', 'docs/diagrams', 'docs/memory',
        'docs/technical_debt', 'docs/specs', 'docs/wiki', 'docs/developer_diary',
        'logs/paranoid', 'logs/intellectual'
    ]
    
    missing = []
    FOR EACH dir_path IN required_dirs:
        full_path = self.project_root / dir_path
        IF NOT full_path.exists():
            APPEND dir_path TO missing
    
    IF missing IS EMPTY:
        APPEND ("Directory Structure", True, "{LENGTH(required_dirs)} directories verified") TO results
        PRINT "  ✅ Directory Structure: All {LENGTH(required_dirs)} directories exist"
    ELSE:
        APPEND ("Directory Structure", False, "Missing: {JOIN(missing[:3], ', ')}") TO results
        PRINT "  ❌ Directory Structure: Missing {LENGTH(missing)} directories"
```

### _test_readme_files - Тест README файлов
```pseudo
FUNCTION _test_readme_files():
    LOG "Testing: README Files"
    
    required_readmes = [
        'docs/README.MD', 'docs/automation/README.MD',
        'docs/specs/README.MD', 'docs/wiki/README.MD'
    ]
    
    missing = []
    FOR EACH readme_path IN required_readmes:
        full_path = self.project_root / readme_path
        # Проверить .MD и .md варианты
        IF NOT full_path.exists() AND NOT (full_path WITH '.md').exists():
            APPEND readme_path TO missing
    
    IF missing IS EMPTY:
        APPEND ("README Files", True, "{LENGTH(required_readmes)} READMEs verified") TO results
    ELSE:
        APPEND ("README Files", False, "Missing: {JOIN(missing[:2], ', ')}") TO results
```

### _test_log_directories - Тест log директорий
```pseudo
FUNCTION _test_log_directories():
    LOG "Testing: Log Directories"
    
    log_dirs = [
        'logs/paranoid', 'logs/intellectual',
        'llm_requests', 'output/deep_supervision', 'output/global_supervision'
    ]
    
    issues = []
    FOR EACH dir_path IN log_dirs:
        full_path = self.project_root / dir_path
        IF NOT full_path.exists():
            TRY:
                CREATE full_path WITH parents=True
                LOG "Created missing directory: {dir_path}"
            CATCH Exception as e:
                APPEND "{dir_path}: {e}" TO issues
    
    IF issues IS EMPTY:
        APPEND ("Log Directories", True, "{LENGTH(log_dirs)} directories ready") TO results
    ELSE:
        APPEND ("Log Directories", False, issues[0]) TO results
```

### _generate_intellectual_log - Генерация intellectual log
```pseudo
FUNCTION _generate_intellectual_log():
    duration = CURRENT_TIME() - self.start_time
    
    passed = COUNT results WHERE success == True
    total = LENGTH(results)
    success_rate = (passed / total * 100) IF total > 0 ELSE 0
    
    # Build markdown log content
    log_content = """
    # Intellectual Log: test_system
    
    ## Session Statistics
    - **Date**: {CURRENT_DATETIME}
    - **Duration**: {duration:.2f}s
    - **Paranoia Level**: {self.paranoia_level}/5
    
    ## Results Summary
    - Tests Run: {total}
    - Passed: {passed}
    - Failed: {total - passed}
    - Success Rate: {success_rate:.1f}%
    
    ## Individual Results
    {FOR EACH (name, success, message) IN results:
        {status emoji} {name} - {message}
    }
    
    ## Paranoia Level Details
    - Level 1: Basic execution tests {✓ if level >= 1}
    - Level 2: Structural validation {✓ if level >= 2}
    - Level 3: Deep Supervisor {✓ if level >= 3}
    - Level 4: Global Supervisor {✓ if level >= 4}
    - Level 5: Full AI analysis {✓ if level >= 5}
    """
    
    # Save to logs/intellectual/
    log_dir = self.project_root / "logs" / "intellectual"
    CREATE log_dir IF NOT EXISTS
    log_file = log_dir / "test_system_{TIMESTAMP}.md"
    WRITE log_content TO log_file
    
    LOG_FILE_INTERACTION log_file, "save_intellectual_log", "SUCCESS"
```

### _print_results - Вывод результатов
```pseudo
FUNCTION _print_results() -> INT:
    duration = CURRENT_TIME() - self.start_time
    passed = COUNT results WHERE success == True
    total = LENGTH(results)
    
    PRINT banner "TEST RESULTS SUMMARY"
    
    FOR EACH (name, success, message) IN results:
        status = "✅ PASS" IF success ELSE "❌ FAIL"
        PRINT "{status}: {name}"
        IF NOT success AND message:
            PRINT "       {message[:70]}"
    
    PRINT "TOTAL: {passed}/{total} tests passed ({passed*100//total}%)"
    PRINT "Duration: {duration:.2f}s"
    PRINT "Paranoia Level: {self.paranoia_level}/5"
    
    LOG_STEP "TestSystem" STATUS "COMPLETED" WITH {passed, total, paranoia_level}
    
    IF passed == total:
        PRINT "🎉 All tests passed! Documentation system is ready."
        RETURN 0
    ELSE:
        PRINT "⚠️  {total - passed} test(s) failed. Please review."
        RETURN 1
```

## CLI INTERFACE
```pseudo
ARGUMENTS:
    -p, --paranoia INT   # Уровень паранойи (1-5, default: 3)
    -v, --verbose        # Включить verbose output

ENTRY POINT main():
    PARSE arguments
    
    # Enable verbose if requested
    IF args.verbose:
        logger = NEW DocsLogger("test_system")
    
    # Run tests
    project_root = Path(__file__).parent.parent.parent
    tester = NEW DocumentationSystemTester(project_root, paranoia_level=args.paranoia)
    exit_code = tester.run_all_tests()
    
    # Print stats summary (if logger supports it)
    logger.print_stats_summary()
    
    EXIT exit_code
```

## ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
```bash
# Запуск с дефолтным уровнем (3)
python3 test_system.py

# Максимальная паранойя
python3 test_system.py -p 5

# Быстрые базовые тесты
python3 test_system.py --paranoia 1

# Verbose output
python3 test_system.py -v
```

## ЗАВИСИМОСТИ

- subprocess
- sys
- time
- argparse
- pathlib.Path
- datetime
- typing (List, Tuple, Dict, Any)
- docs.utils.docs_logger.DocsLogger
- docs.utils.docs_deep_supervisor.DocsDeepSupervisor (optional)
- docs.utils.docs_global_supervisor.DocsGlobalSupervisor (optional)

<!--/TAG:pseudo_test_system-->
