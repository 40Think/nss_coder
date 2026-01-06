---
description: "Валидация семантических тегов по формальной схеме"
date: 2025-12-12
source_file: tag_validator.py
version: "2.0"
tags: automation, validation, tags, schema, semantic-tags
---

# tag_validator.py - Псевдокод

<!--TAG:pseudo_tag_validator-->

## PURPOSE

Валидирует семантические теги в Python и Markdown файлах:
- Проверка соответствия формальной схеме `tag_schema.yaml`
- Проверка закрывающих тегов для primary tags
- Проверка валидности идентификаторов
- Рекомендации по использованию dimension tags

## СТРУКТУРЫ ДАННЫХ

### Severity (Enum)
```pseudo
ENUM Severity:
    ERROR = "ERROR"        # Обязательно исправить - ломает функциональность
    WARNING = "WARNING"    # Рекомендуется исправить - нарушение best practices
    INFO = "INFO"          # Информация - можно улучшить
```

### ValidationIssue (dataclass)
```pseudo
DATACLASS ValidationIssue:
    severity: Severity           # Уровень серьёзности
    rule_name: STRING            # Имя правила валидации
    message: STRING              # Описание проблемы
    file_path: STRING            # Путь к файлу
    line_number: Optional[INT]   # Номер строки (если применимо)
    suggestion: Optional[STRING] # Предложение по исправлению
    auto_fixable: BOOL = False   # Можно ли исправить автоматически
```

### ValidationReport (dataclass)
```pseudo
DATACLASS ValidationReport:
    file_path: STRING                      # Путь к валидируемому файлу
    issues: LIST[ValidationIssue] = []     # Найденные проблемы
    tags_found: LIST[STRING] = []          # Найденные теги
    is_valid: BOOL = True                  # Результат валидации
    
    FUNCTION add_issue(issue: ValidationIssue):
        APPEND issue TO self.issues
        IF issue.severity == Severity.ERROR:
            self.is_valid = False
    
    PROPERTY error_count -> INT:
        RETURN COUNT issues WHERE severity == ERROR
    
    PROPERTY warning_count -> INT:
        RETURN COUNT issues WHERE severity == WARNING
```

## КЛАСС: TagValidator

### Инициализация
```pseudo
CLASS TagValidator:
    FUNCTION __init__(schema_path: Optional[Path] = None):
        # Установить путь к схеме
        IF schema_path IS None:
            self.schema_path = Path(__file__).parent.parent / "specs" / "tag_schema.yaml"
        ELSE:
            self.schema_path = Path(schema_path)
        
        # Загрузить схему
        self.schema = CALL _load_schema()
        
        # Скомпилировать regex паттерны для поиска тегов
        self.tag_pattern = COMPILE r'<!--TAG:([a-zA-Z0-9_:]+)-->'
        self.close_pattern = COMPILE r'<!--/TAG:([a-zA-Z0-9_:]+)-->'
        
        LOG "TagValidator initialized with schema: {self.schema_path}"
```

### _load_schema - Загрузка схемы
```pseudo
FUNCTION _load_schema() -> Dict:
    IF NOT self.schema_path.exists():
        LOG WARNING "Schema file not found: {self.schema_path}"
        RETURN CALL _get_default_schema()
    
    TRY:
        content = READ self.schema_path AS YAML
        LOG "Loaded schema version: {content.version}"
        RETURN content
    CATCH Exception as e:
        LOG ERROR "Failed to load schema: {e}"
        RETURN CALL _get_default_schema()
```

### _get_default_schema - Дефолтная схема
```pseudo
FUNCTION _get_default_schema() -> Dict:
    RETURN {
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
```

### validate_file - Валидация одного файла
```pseudo
FUNCTION validate_file(file_path: Path) -> ValidationReport:
    report = NEW ValidationReport(file_path=str(file_path))
    
    # Проверка существования файла
    IF NOT file_path.exists():
        report.add_issue(ValidationIssue(
            severity = ERROR,
            rule_name = "file_exists",
            message = "File not found: {file_path}",
            file_path = str(file_path)
        ))
        RETURN report
    
    # Чтение содержимого
    TRY:
        content = READ file_path WITH encoding='utf-8'
    CATCH Exception as e:
        report.add_issue(ValidationIssue(
            severity = ERROR,
            rule_name = "file_readable",
            message = "Cannot read file: {e}",
            file_path = str(file_path)
        ))
        RETURN report
    
    # Извлечение всех тегов
    opening_tags = FINDALL self.tag_pattern IN content
    closing_tags = FINDALL self.close_pattern IN content
    report.tags_found = opening_tags
    
    # Запуск всех правил валидации
    CALL _check_tag_count(report, opening_tags)
    CALL _check_matching_close_tags(report, opening_tags, closing_tags, content)
    CALL _check_valid_identifiers(report, opening_tags)
    CALL _check_component_tag(report, file_path, opening_tags)
    CALL _check_duplicate_tags(report, opening_tags)
    CALL _check_known_dimensions(report, opening_tags)
    
    RETURN report
```

### Правила валидации

#### _check_tag_count - Проверка количества тегов
```pseudo
FUNCTION _check_tag_count(report: ValidationReport, tags: List[str]):
    max_tags = 6  # default
    
    # Получить max из схемы если есть
    FOR rule IN self.schema.tag_rules:
        IF rule.name == "max_tags_per_file":
            max_tags = rule.max_value
    
    # Считать уникальные теги
    unique_tags = SET(t.split(':')[0] IF ':' NOT IN t ELSE t FOR t IN tags)
    
    IF LENGTH(unique_tags) > max_tags:
        report.add_issue(ValidationIssue(
            severity = WARNING,
            rule_name = "max_tags_per_file",
            message = "Too many tags: {LENGTH(unique_tags)} (max {max_tags})",
            file_path = report.file_path,
            suggestion = "Consider consolidating tags or removing less important ones"
        ))
```

#### _check_matching_close_tags - Проверка закрывающих тегов
```pseudo
FUNCTION _check_matching_close_tags(report, opening, closing, content):
    # Получить primary tags (не inline dimension tags)
    primary_tags = [t FOR t IN opening IF ':' NOT IN t OR t.count(':') == 1]
    
    FOR tag IN primary_tags:
        base_tag = tag.split(':')[0]
        
        # Пропустить если есть закрывающий тег
        IF base_tag IN closing:
            CONTINUE
        
        # Пропустить inline dimension tags
        IF ':' IN tag AND tag.split(':')[0] IN ['component', 'type', 'feature']:
            CONTINUE
        
        # Проверить есть ли контент после открывающего тега
        opening_pos = FIND "<!--TAG:{tag}-->" IN content
        IF opening_pos != -1:
            closing_pos = FIND "<!--/TAG:{tag}-->" IN content AFTER opening_pos
            
            # Найти следующий тег для определения границ контента
            next_tag_pos = FIND "<!--" IN content AFTER opening_pos
            IF next_tag_pos == -1:
                next_tag_pos = LENGTH(content)
            
            content_between = content[opening_pos + tag_length : next_tag_pos].strip()
            
            # Если есть значительный контент, должен быть closing tag
            IF LENGTH(content_between) > 50 AND closing_pos == -1:
                line_num = COUNT newlines BEFORE opening_pos + 1
                report.add_issue(ValidationIssue(
                    severity = ERROR,
                    rule_name = "primary_tag_must_close",
                    message = "Tag '{tag}' has content but no closing tag",
                    file_path = report.file_path,
                    line_number = line_num,
                    suggestion = "Add <!--/TAG:{tag}--> after the content",
                    auto_fixable = True
                ))
```

#### _check_valid_identifiers - Проверка идентификаторов
```pseudo
FUNCTION _check_valid_identifiers(report, tags):
    valid_pattern = COMPILE r'^[a-zA-Z][a-zA-Z0-9_:]*$'
    
    FOR tag IN tags:
        IF NOT MATCH valid_pattern TO tag:
            report.add_issue(ValidationIssue(
                severity = ERROR,
                rule_name = "valid_identifier",
                message = "Invalid tag identifier: '{tag}'",
                file_path = report.file_path,
                suggestion = "Tag identifiers must start with a letter and contain only alphanumeric, underscore, colon"
            ))
```

#### _check_component_tag - Проверка component тега
```pseudo
FUNCTION _check_component_tag(report, file_path, tags):
    # Только для Python файлов
    IF file_path.suffix != '.py':
        RETURN
    
    # Проверить наличие component dimension tag
    component_values = self.schema.tag_hierarchy.get('component', [])
    component_tags = ['component:' + c FOR c IN component_values]
    has_component = ANY(t IN component_tags OR t.startswith('component:') FOR t IN tags)
    
    IF NOT has_component:
        suggested_component = CALL _infer_component_from_path(file_path)
        report.add_issue(ValidationIssue(
            severity = WARNING,
            rule_name = "script_must_have_component",
            message = "Python file missing component tag",
            file_path = str(file_path),
            suggestion = "Add <!--TAG:component:{suggested_component}--> to the docstring",
            auto_fixable = True
        ))
```

#### _infer_component_from_path - Определение component из пути
```pseudo
FUNCTION _infer_component_from_path(file_path: Path) -> STRING:
    path_str = str(file_path)
    
    IF 'automation' IN path_str: RETURN 'automation'
    IF 'utils' IN path_str: RETURN 'utils'
    IF 'processing' IN path_str: RETURN 'processing'
    IF 'docs' IN path_str: RETURN 'docs'
    IF 'tests' IN path_str: RETURN 'tests'
    
    RETURN 'utils'  # Default
```

#### _check_duplicate_tags - Проверка дубликатов
```pseudo
FUNCTION _check_duplicate_tags(report, tags):
    seen = SET()
    duplicates = SET()
    
    FOR tag IN tags:
        IF tag IN seen:
            ADD tag TO duplicates
        ADD tag TO seen
    
    FOR dup IN duplicates:
        report.add_issue(ValidationIssue(
            severity = WARNING,
            rule_name = "no_duplicate_tags",
            message = "Duplicate tag: '{dup}'",
            file_path = report.file_path,
            suggestion = "Remove duplicate tag occurrences"
        ))
```

#### _check_known_dimensions - Проверка известных dimension values
```pseudo
FUNCTION _check_known_dimensions(report, tags):
    hierarchy = self.schema.tag_hierarchy
    
    FOR tag IN tags:
        IF ':' IN tag:
            parts = SPLIT tag BY ':'
            IF LENGTH(parts) >= 2:
                dimension, value = parts[0], parts[1]
                
                # Пропустить не-dimension теги (типа method:name)
                IF dimension NOT IN ['component', 'type', 'feature']:
                    CONTINUE
                
                known_values = hierarchy.get(dimension, [])
                IF known_values AND value NOT IN known_values:
                    report.add_issue(ValidationIssue(
                        severity = INFO,
                        rule_name = "known_dimension_value",
                        message = "Unknown {dimension} value: '{value}'",
                        file_path = report.file_path,
                        suggestion = "Known values: {JOIN(known_values, ', ')}"
                    ))
```

### validate_directory - Валидация директории
```pseudo
FUNCTION validate_directory(directory: Path, extensions: List[str] = None) -> List[ValidationReport]:
    IF extensions IS None:
        extensions = ['.py', '.md']
    
    reports = []
    
    FOR ext IN extensions:
        FOR file_path IN RECURSIVE_GLOB(directory, "*{ext}"):
            # Пропустить __pycache__ и .git
            IF '__pycache__' IN str(file_path): CONTINUE
            IF '.git' IN str(file_path): CONTINUE
            
            report = CALL validate_file(file_path)
            APPEND report TO reports
    
    RETURN reports
```

### format_report - Форматирование отчёта
```pseudo
FUNCTION format_report(report: ValidationReport) -> STRING:
    lines = []
    
    # Заголовок
    status = "✅ VALID" IF report.is_valid ELSE "❌ INVALID"
    APPEND "\n{status}: {report.file_path}" TO lines
    APPEND "  Tags found: {LENGTH(report.tags_found)}" TO lines
    
    IF report.tags_found:
        APPEND "  Tags: {JOIN(first 5 tags, ', ')}" TO lines
        IF LENGTH(report.tags_found) > 5:
            APPEND "        ... and {LENGTH - 5} more" TO lines
    
    # Группировка проблем по severity
    FOR severity IN [ERROR, WARNING, INFO]:
        severity_issues = FILTER report.issues WHERE severity == current_severity
        IF severity_issues:
            icon = "🚨" IF ERROR ELSE "⚠️" IF WARNING ELSE "ℹ️"
            FOR issue IN severity_issues:
                line_info = " (line {issue.line_number})" IF issue.line_number ELSE ""
                APPEND "  {icon} [{severity}] {issue.message}{line_info}" TO lines
                IF issue.suggestion:
                    APPEND "      → {issue.suggestion}" TO lines
    
    RETURN JOIN(lines, '\n')
```

### format_summary - Сводка по всем отчётам
```pseudo
FUNCTION format_summary(reports: List[ValidationReport]) -> STRING:
    total_files = LENGTH(reports)
    valid_files = COUNT reports WHERE is_valid == True
    total_errors = SUM(r.error_count FOR r IN reports)
    total_warnings = SUM(r.warning_count FOR r IN reports)
    
    lines = [
        "\n" + "=" * 60,
        "TAG VALIDATION SUMMARY",
        "=" * 60,
        "Files validated: {total_files}",
        "Valid files: {valid_files} ({100 * valid_files // total_files}%)",
        "Total errors: {total_errors}",
        "Total warnings: {total_warnings}",
        "=" * 60
    ]
    
    RETURN JOIN(lines, '\n')
```

## CLI INTERFACE

```pseudo
ARGUMENTS:
    --file PATH         # Валидировать один файл
    --directory PATH    # Валидировать директорию рекурсивно
    --all               # Валидировать весь проект (docs/automation, utils, processing)
    --schema PATH       # Путь к файлу схемы tag_schema.yaml
    --fix               # Автоматически исправить простые проблемы (NOT IMPLEMENTED)
    --quiet             # Показывать только ошибки
    --json              # Вывод в формате JSON

ENTRY POINT main():
    PARSE arguments
    
    # Инициализация валидатора
    schema_path = Path(args.schema) IF args.schema ELSE None
    validator = NEW TagValidator(schema_path=schema_path)
    
    reports = []
    
    IF args.file:
        report = validator.validate_file(Path(args.file))
        APPEND report TO reports
    
    ELIF args.directory:
        reports = validator.validate_directory(Path(args.directory))
    
    ELIF args.all:
        project_root = Path(__file__).parent.parent.parent
        FOR dir_name IN ['docs/automation', 'utils', 'processing']:
            dir_path = project_root / dir_name
            IF dir_path.exists():
                reports.extend(validator.validate_directory(dir_path))
    
    ELSE:
        PRINT help
        RETURN
    
    # Вывод результатов
    IF args.json:
        output = [
            {
                'file': r.file_path,
                'valid': r.is_valid,
                'tags': r.tags_found,
                'errors': r.error_count,
                'warnings': r.warning_count,
                'issues': [asdict(i) FOR i IN r.issues]
            }
            FOR r IN reports
        ]
        PRINT JSON(output, indent=2)
    ELSE:
        FOR report IN reports:
            IF NOT args.quiet OR NOT report.is_valid:
                PRINT validator.format_report(report)
        
        PRINT validator.format_summary(reports)
```

## ПРАВИЛА ВАЛИДАЦИИ (Summary)

| Правило | Severity | Описание |
|---------|----------|----------|
| `file_exists` | ERROR | Файл должен существовать |
| `file_readable` | ERROR | Файл должен быть читаемым |
| `max_tags_per_file` | WARNING | Максимум 6 уникальных тегов |
| `primary_tag_must_close` | ERROR | Primary tags с контентом нужен closing tag |
| `valid_identifier` | ERROR | Идентификатор должен быть валидным |
| `script_must_have_component` | WARNING | Python файлы должны иметь component tag |
| `no_duplicate_tags` | WARNING | Нет дублирующихся тегов |
| `known_dimension_value` | INFO | Используйте известные значения dimension |

## ЗАВИСИМОСТИ

- os, re, sys
- yaml
- argparse
- pathlib.Path
- typing (List, Dict, Optional, Tuple, Set)
- dataclasses (dataclass, field)
- enum.Enum
- docs.utils.docs_logger.DocsLogger

<!--/TAG:pseudo_tag_validator-->
