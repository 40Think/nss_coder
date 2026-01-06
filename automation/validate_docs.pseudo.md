---
description: "Валидация целостности документации - broken links, missing specs, drift"
date: 2025-12-12
source_file: validate_docs.py
version: "2.0"
tags: automation, validation, links, specs
---

# validate_docs.py - Псевдокод

<!--TAG:pseudo_validate_docs-->

## PURPOSE

Валидирует целостность системы документации:
- Проверка битых ссылок в markdown-файлах
- Обнаружение Python-файлов без спецификаций
- Детекция drift между specs и кодом
- Проверка наличия YAML frontmatter

## СТРУКТУРЫ ДАННЫХ

### ValidationIssue (dataclass)
```pseudo
DATACLASS ValidationIssue:
    severity: STRING      # "error" | "warning" | "info"
    category: STRING      # "link" | "missing" | "drift" | "format"
    file_path: STRING     # Путь к файлу с проблемой
    line_number: INT      # Номер строки (если применимо)
    message: STRING       # Описание проблемы
    suggestion: STRING    # Предложение по исправлению (опционально, default="")
```

## КЛАСС: DocumentationValidator

### Инициализация
```pseudo
CLASS DocumentationValidator:
    FUNCTION __init__(project_root: Path):
        self.project_root = project_root
        self.issues: LIST[ValidationIssue] = []
```

### validate_all - Запуск всех проверок
```pseudo
FUNCTION validate_all() -> LIST[ValidationIssue]:
    LOG "🔍 Running documentation validation..."
    
    CALL check_broken_links()
    CALL check_missing_specs()
    CALL check_spec_code_drift()
    CALL check_frontmatter()
    
    RETURN self.issues
```

### check_broken_links - Проверка битых ссылок
```pseudo
FUNCTION check_broken_links():
    LOG "📎 Checking for broken links..."
    
    docs_dir = self.project_root / 'docs'
    all_files = SET()
    
    # Собрать все существующие файлы
    FOR EACH md_file IN RECURSIVE_GLOB(docs_dir, "*.md"):
        ADD md_file.relative_to(self.project_root) TO all_files
    
    # Обойти все markdown файлы
    FOR EACH md_file IN RECURSIVE_GLOB(docs_dir, "*.md"):
        content = READ md_file WITH encoding='utf-8'
        
        # Regex для markdown ссылок: [text](path)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        links = REGEX FINDALL link_pattern IN content
        
        FOR EACH (link_text, link_url) IN links:
            # Пропустить URL (http/https)
            IF link_url STARTS WITH "http://" OR link_url STARTS WITH "https://":
                CONTINUE
            
            # Пропустить anchors-only (#section)
            IF link_url STARTS WITH "#":
                CONTINUE
            
            # Разделить путь и anchor
            url_parts = SPLIT link_url BY "#"
            file_path = url_parts[0]
            
            # Преобразовать относительный путь
            link_path = (md_file.parent / file_path).resolve()
            
            # Проверить существование
            IF NOT link_path.exists():
                TRY:
                    relative_link = link_path.relative_to(self.project_root)
                EXCEPT ValueError:
                    CONTINUE  # Link outside project root - skip
                
                line_number = CALL _find_line_number(content, link_url)
                issue = NEW ValidationIssue(
                    severity = "error",
                    category = "link",
                    file_path = str(md_file RELATIVE TO self.project_root),
                    line_number = line_number,
                    message = "Broken link: {link_url}",
                    suggestion = "Check if file exists: {relative_link}"
                )
                APPEND issue TO self.issues
    
    broken_count = COUNT issues WHERE category == "link"
    LOG "  Found {broken_count} broken links"
```

### check_missing_specs - Проверка отсутствующих спецификаций
```pseudo
FUNCTION check_missing_specs():
    LOG "📋 Checking for missing specifications..."
    
    specs_dir = self.project_root / 'docs' / 'specs'
    processing_dir = self.project_root / 'processing'
    utils_dir = self.project_root / 'utils'
    
    # Получить список имён spec файлов (без _spec суффикса)
    spec_files = SET()
    FOR EACH spec_file IN RECURSIVE_GLOB(specs_dir, "*.md"):
        ADD spec_file.stem.replace('_spec', '') TO spec_files
    
    # Проверить processing файлы
    FOR EACH py_file IN RECURSIVE_GLOB(processing_dir, "*.py"):
        IF py_file.name == '__init__.py':
            CONTINUE
        
        file_stem = py_file.stem
        IF file_stem NOT IN spec_files:
            issue = NEW ValidationIssue(
                severity = "warning",
                category = "missing",
                file_path = str(py_file RELATIVE TO self.project_root),
                line_number = 0,
                message = "Missing specification for {py_file.name}",
                suggestion = "Create docs/specs/{file_stem}_spec.md"
            )
            APPEND issue TO self.issues
    
    # Проверить utils файлы
    FOR EACH py_file IN RECURSIVE_GLOB(utils_dir, "*.py"):
        IF py_file.name == '__init__.py':
            CONTINUE
        
        file_stem = "utils_{py_file.stem}"
        IF file_stem NOT IN spec_files:
            issue = NEW ValidationIssue(
                severity = "info",
                category = "missing",
                file_path = str(py_file RELATIVE TO self.project_root),
                line_number = 0,
                message = "Missing specification for {py_file.name}",
                suggestion = "Create docs/specs/{file_stem}_spec.md"
            )
            APPEND issue TO self.issues
    
    missing_count = COUNT issues WHERE category == "missing"
    LOG "  Found {missing_count} files without specs"
```

### check_spec_code_drift - Проверка drift между spec и кодом
```pseudo
FUNCTION check_spec_code_drift():
    LOG "🔄 Checking for spec-code drift..."
    
    specs_dir = self.project_root / 'docs' / 'specs'
    
    FOR EACH spec_file IN RECURSIVE_GLOB(specs_dir, "*_spec.md"):
        # Найти соответствующий Python файл
        py_file = CALL _find_python_file(spec_file)
        
        IF py_file IS None OR NOT py_file.exists():
            CONTINUE
        
        # Загрузить содержимое
        spec_content = READ spec_file WITH encoding='utf-8'
        code_content = READ py_file WITH encoding='utf-8'
        
        # Извлечь функции упомянутые в spec (формат: `function_name(`)
        function_pattern = r'`([a-zA-Z_][a-zA-Z0-9_]*)\(`'
        spec_functions = SET(REGEX FINDALL function_pattern IN spec_content)
        
        # Извлечь функции из Python кода
        code_function_pattern = r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        code_functions = SET(REGEX FINDALL code_function_pattern IN code_content WITH MULTILINE)
        
        # Найти функции в spec которых нет в коде
        missing_in_code = spec_functions - code_functions
        IF missing_in_code:
            issue = NEW ValidationIssue(
                severity = "warning",
                category = "drift",
                file_path = str(spec_file RELATIVE TO self.project_root),
                line_number = 0,
                message = "Functions in spec but not in code: {JOIN(missing_in_code, ', ')}",
                suggestion = "Update spec or implement missing functions in {py_file.name}"
            )
            APPEND issue TO self.issues
        
        # Найти функции в коде которых нет в spec (исключая приватные)
        missing_in_spec = code_functions - spec_functions
        missing_in_spec = FILTER missing_in_spec WHERE NOT STARTS WITH "_"
        IF missing_in_spec:
            issue = NEW ValidationIssue(
                severity = "info",
                category = "drift",
                file_path = str(spec_file RELATIVE TO self.project_root),
                line_number = 0,
                message = "Functions in code but not in spec: {JOIN(missing_in_spec, ', ')}",
                suggestion = "Document these functions in the spec"
            )
            APPEND issue TO self.issues
    
    drift_count = COUNT issues WHERE category == "drift"
    LOG "  Found {drift_count} drift issues"
```

### check_frontmatter - Проверка YAML frontmatter
```pseudo
FUNCTION check_frontmatter():
    LOG "📝 Checking YAML frontmatter..."
    
    docs_dir = self.project_root / 'docs'
    
    FOR EACH md_file IN RECURSIVE_GLOB(docs_dir, "*.md"):
        # Пропустить README файлы
        IF md_file.name == "README.MD":
            CONTINUE
        
        content = READ md_file WITH encoding='utf-8'
        
        # Проверить regex для frontmatter: ^---\n.*?\n---\n
        frontmatter_pattern = r'^---\n.*?\n---\n'
        IF NOT REGEX MATCH frontmatter_pattern IN content WITH DOTALL:
            issue = NEW ValidationIssue(
                severity = "info",
                category = "format",
                file_path = str(md_file RELATIVE TO self.project_root),
                line_number = 1,
                message = "Missing YAML frontmatter",
                suggestion = "Add frontmatter with metadata (version, date, status)"
            )
            APPEND issue TO self.issues
    
    format_count = COUNT issues WHERE category == "format"
    LOG "  Found {format_count} formatting issues"
```

### Вспомогательные методы
```pseudo
FUNCTION _find_python_file(spec_file: Path) -> Optional[Path]:
    # Извлечь имя без _spec суффикса
    spec_name = spec_file.stem.replace('_spec', '')
    
    # Поискать в processing/ (если не начинается с utils_)
    IF NOT spec_name.startswith('utils_'):
        candidate = self.project_root / 'processing' / "{spec_name}.py"
        IF candidate.exists():
            RETURN candidate
    
    # Поискать в utils/ (если начинается с utils_)
    IF spec_name.startswith('utils_'):
        utils_name = spec_name.replace('utils_', '')
        candidate = self.project_root / 'utils' / "{utils_name}.py"
        IF candidate.exists():
            RETURN candidate
    
    RETURN None

FUNCTION _find_line_number(content: str, search_text: str) -> int:
    lines = SPLIT content BY newlines
    FOR i, line IN ENUMERATE(lines, start=1):
        IF search_text IN line:
            RETURN i
    RETURN 0
```

### generate_report - Генерация отчёта
```pseudo
FUNCTION generate_report(output_file: Path):
    # Группировка по severity
    by_severity = defaultdict(list)
    FOR EACH issue IN self.issues:
        APPEND issue TO by_severity[issue.severity]
    
    # Построить markdown отчёт
    report = "# Documentation Validation Report\n\n"
    report += "**Generated**: {script_name}\n\n"
    
    report += "## Summary\n\n"
    report += "- **Errors**: {LENGTH(by_severity['error'])}\n"
    report += "- **Warnings**: {LENGTH(by_severity['warning'])}\n"
    report += "- **Info**: {LENGTH(by_severity['info'])}\n"
    report += "- **Total**: {LENGTH(self.issues)}\n\n"
    
    # Детали по severity
    FOR EACH severity IN ['error', 'warning', 'info']:
        issues = by_severity[severity]
        IF NOT issues:
            CONTINUE
        
        report += "## {severity.UPPER()}S\n\n"
        
        FOR EACH issue IN issues:
            report += "### {issue.file_path}\n\n"
            report += "- **Line**: {issue.line_number}\n"
            report += "- **Category**: {issue.category}\n"
            report += "- **Message**: {issue.message}\n"
            IF issue.suggestion:
                report += "- **Suggestion**: {issue.suggestion}\n"
            report += "\n"
    
    # Сохранить отчёт
    WRITE report TO output_file WITH encoding='utf-8'
    LOG "📊 Report saved to: {output_file}"
```

## CLI INTERFACE
```pseudo
ARGUMENTS:
    --report PATH       # Output file for validation report (default: docs/validation_report.md)
    --ci-mode           # Exit with error code if issues found

ENTRY POINT main():
    PARSE arguments
    project_root = Path(__file__).parent.parent.parent
    
    validator = NEW DocumentationValidator(project_root)
    issues = validator.validate_all()
    
    # Generate report to specified file
    report_file = project_root / args.report
    validator.generate_report(report_file)
    
    # Print summary
    LOG "=" * 60
    LOG "✓ Validation complete: {LENGTH(issues)} issues found"
    LOG "=" * 60
    
    # Exit with error in CI mode if errors found
    IF args.ci_mode:
        error_count = COUNT issues WHERE severity == "error"
        IF error_count > 0:
            LOG ERROR "CI mode: {error_count} errors found"
            EXIT 1
```

## ЗАВИСИМОСТИ

- os
- re  
- json
- pathlib.Path
- dataclasses (dataclass, asdict)
- collections.defaultdict
- typing (List, Dict, Set, Tuple)
- docs.utils.docs_logger.DocsLogger

<!--/TAG:pseudo_validate_docs-->
