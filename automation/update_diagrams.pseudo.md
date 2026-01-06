---
description: "Автоматическое обновление диаграмм при изменении кода"
date: 2025-12-12
source_file: update_diagrams.py
version: "2.0"
tags: automation, diagrams, mermaid, visualization, watch-mode, parallel
---

# update_diagrams.py - Псевдокод

<!--TAG:pseudo_update_diagrams-->

## PURPOSE

Автоматически регенерирует диаграммы при изменении кода.
Интегрируется с Git hooks и CI/CD pipelines.
Поддерживает architecture, dependency, и call graph диаграммы.

## FEATURES (v2.0)

- **Mermaid Validation**: Валидация синтаксиса через mermaid-cli перед сохранением
- **Watch Mode**: Автообновление при изменении файлов (требует watchdog)
- **Parallel Processing**: Параллельное обновление диаграмм для ускорения
- **Force Update**: Принудительное обновление всех диаграмм
- **Debouncing**: Защита от множественных обновлений при быстрых изменениях

## СТРУКТУРЫ ДАННЫХ

### DiagramSpec (dataclass)
```pseudo
DATACLASS DiagramSpec:
    name: STRING                  # Имя диаграммы (e.g. "Documentation System Architecture")
    type: STRING                  # Тип: "architecture" | "dependencies" | "call_graph" | "data_flow"
    source_files: LIST[STRING]    # Паттерны исходных файлов (glob patterns)
    output_path: STRING           # Путь к выходному файлу
    generator_command: STRING     # Команда генерации (или "manual")
    last_updated: STRING = None   # ISO timestamp последнего обновления
```

## КЛАСС: DiagramFileHandler (FileSystemEventHandler)

### Назначение
Обрабатывает события изменения файлов для автоматического обновления диаграмм.

### Инициализация
```pseudo
CLASS DiagramFileHandler EXTENDS FileSystemEventHandler:
    FUNCTION __init__(updater: DiagramUpdater):
        self.updater = updater
        self.last_update: DICT[STRING, FLOAT] = {}  # Дебаунсинг
        self.debounce_seconds = 2.0  # Минимальный интервал между обновлениями
```

### on_modified - Обработка изменений файлов
```pseudo
FUNCTION on_modified(event):
    # Пропустить директории
    IF event.is_directory:
        RETURN
    
    # Обрабатывать только Python файлы
    IF NOT event.src_path ENDS WITH ".py":
        RETURN
    
    # Дебаунсинг - избежать множественных обновлений
    now = CURRENT_TIME()
    IF event.src_path IN self.last_update:
        IF now - self.last_update[event.src_path] < self.debounce_seconds:
            RETURN  # Слишком рано, пропустить
    
    self.last_update[event.src_path] = now
    
    LOG "📁 File changed: {event.src_path}"
    
    # Найти затронутые диаграммы
    changed_file = Path(event.src_path)
    affected = self.updater.find_affected_diagrams(changed_file)
    
    IF affected:
        LOG "  → {LENGTH(affected)} diagram(s) affected"
        FOR EACH spec IN affected:
            LOG "  → Updating {spec.name}..."
            self.updater.update_diagram(spec)
        self.updater._save_specs()
    ELSE:
        LOG "  → No diagrams affected"
```

## КЛАСС: DiagramUpdater

### Инициализация
```pseudo
CLASS DiagramUpdater:
    FUNCTION __init__(project_root: Path):
        self.project_root = project_root
        self.diagrams_dir = project_root / 'docs' / 'diagrams'
        self.specs_file = self.diagrams_dir / 'diagram_specs.json'
        self.specs: LIST[DiagramSpec] = []
        
        # Загрузить или создать спецификации
        CALL _load_specs()
```

### _load_specs - Загрузка спецификаций
```pseudo
FUNCTION _load_specs():
    IF self.specs_file.exists():
        data = READ self.specs_file AS JSON
        self.specs = [DiagramSpec(**spec) FOR spec IN data.get('diagrams', [])]
    ELSE:
        CALL _create_default_specs()
```

### _create_default_specs - Создание дефолтных спецификаций
```pseudo
FUNCTION _create_default_specs():
    self.specs = [
        # Architecture diagram
        DiagramSpec(
            name = "Documentation System Architecture",
            type = "architecture",
            source_files = ["docs/README.MD", "docs/automation/*.py"],
            output_path = "docs/diagrams/architecture/documentation_system.mmd",
            generator_command = "manual"
        ),
        
        # Processing dependencies
        DiagramSpec(
            name = "Processing Dependencies",
            type = "dependencies",
            source_files = ["processing/*.py"],
            output_path = "docs/diagrams/dependencies/processing_deps.mmd",
            generator_command = "python3 docs/automation/generate_call_graph.py --directory processing/ --format mermaid --output {output}"
        ),
        
        # Utils dependencies
        DiagramSpec(
            name = "Utils Dependencies",
            type = "dependencies",
            source_files = ["utils/*.py"],
            output_path = "docs/diagrams/dependencies/utils_deps.mmd",
            generator_command = "python3 docs/automation/generate_call_graph.py --directory utils/ --format mermaid --output {output}"
        ),
        
        # Full call graph
        DiagramSpec(
            name = "Full Project Call Graph",
            type = "call_graph",
            source_files = ["processing/*.py", "utils/*.py"],
            output_path = "docs/diagrams/dependencies/full_call_graph.json",
            generator_command = "python3 docs/automation/generate_call_graph.py --all --format json --output {output}"
        )
    ]
    
    CALL _save_specs()
```

### _save_specs - Сохранение спецификаций
```pseudo
FUNCTION _save_specs():
    CREATE self.specs_file.parent IF NOT EXISTS
    
    data = {
        'diagrams': [
            {
                'name': spec.name,
                'type': spec.type,
                'source_files': spec.source_files,
                'output_path': spec.output_path,
                'generator_command': spec.generator_command,
                'last_updated': spec.last_updated
            }
            FOR spec IN self.specs
        ]
    }
    
    WRITE data AS JSON TO self.specs_file
```

### _validate_mermaid - Валидация Mermaid синтаксиса
```pseudo
FUNCTION _validate_mermaid(content: STRING) -> BOOL:
    """Валидирует Mermaid синтаксис через mermaid-cli."""
    TRY:
        result = subprocess.run(
            ['mmdc', '--validate', '-i', '-'],
            input = content,
            capture_output = True,
            text = True,
            timeout = 10
        )
        
        IF result.returncode == 0:
            RETURN True
        ELSE:
            LOG WARNING "Mermaid validation failed: {result.stderr}"
            RETURN False
    
    CATCH FileNotFoundError:
        # mermaid-cli не установлен - пропустить валидацию
        LOG WARNING "mermaid-cli not installed, skipping validation"
        LOG INFO "  Install with: npm install -g @mermaid-js/mermaid-cli"
        RETURN True  # Не блокировать при отсутствии зависимости
    
    CATCH subprocess.TimeoutExpired:
        LOG ERROR "Mermaid validation timed out"
        RETURN False
    
    CATCH Exception as e:
        LOG WARNING "Mermaid validation error: {e}"
        RETURN True  # Не блокировать при ошибках валидации
```

### check_updates_needed - Проверка необходимости обновления
```pseudo
FUNCTION check_updates_needed() -> LIST[DiagramSpec]:
    needs_update = []
    
    FOR EACH spec IN self.specs:
        IF spec.generator_command == "manual":
            CONTINUE
        
        IF CALL _sources_changed(spec):
            APPEND spec TO needs_update
    
    RETURN needs_update
```

### _sources_changed - Проверка изменений исходных файлов
```pseudo
FUNCTION _sources_changed(spec: DiagramSpec) -> BOOL:
    output_path = self.project_root / spec.output_path
    
    # Если выходной файл не существует - нужно обновить
    IF NOT output_path.exists():
        RETURN True
    
    output_mtime = GET modification time OF output_path
    
    # Проверить каждый паттерн исходных файлов
    FOR EACH pattern IN spec.source_files:
        FOR EACH source_file IN GLOB(self.project_root, pattern):
            IF source_file.is_file():
                source_mtime = GET modification time OF source_file
                IF source_mtime > output_mtime:
                    RETURN True
    
    RETURN False
```

### find_affected_diagrams - Поиск затронутых диаграмм
```pseudo
FUNCTION find_affected_diagrams(changed_file: Path) -> LIST[DiagramSpec]:
    affected = []
    
    # Нормализовать путь
    TRY:
        changed_file = changed_file.resolve()
    EXCEPT Exception:
        PASS
    
    FOR EACH spec IN self.specs:
        IF spec.generator_command == "manual":
            CONTINUE
        
        FOR EACH source_pattern IN spec.source_files:
            # Обработка glob паттернов
            IF '*' IN source_pattern:
                matching_files = LIST(GLOB(self.project_root, source_pattern))
                matching_resolved = [m.resolve() FOR m IN matching_files]
                
                IF changed_file IN matching_resolved:
                    APPEND spec TO affected
                    BREAK
            ELSE:
                # Прямой путь к файлу
                source_path = (self.project_root / source_pattern).resolve()
                IF changed_file == source_path:
                    APPEND spec TO affected
                    BREAK
    
    RETURN affected
```

### update_diagram - Обновление одной диаграммы
```pseudo
FUNCTION update_diagram(spec: DiagramSpec) -> BOOL:
    LOG "Updating diagram: {spec.name}"
    
    IF spec.generator_command == "manual":
        LOG "  → Manual diagram, skipping"
        RETURN False
    
    # Подготовить команду
    output_path = self.project_root / spec.output_path
    command = spec.generator_command.replace('{output}', str(spec.output_path))
    
    # Создать директорию если не существует
    CREATE output_path.parent IF NOT EXISTS
    
    TRY:
        result = subprocess.run(
            command,
            shell = True,
            cwd = str(self.project_root),
            capture_output = True,
            text = True,
            timeout = 120
        )
        
        IF result.returncode == 0:
            # Валидировать Mermaid диаграммы
            IF spec.output_path ENDS WITH '.mmd' AND output_path.exists():
                content = READ output_path
                IF NOT CALL _validate_mermaid(content):
                    LOG ERROR "  ✗ Invalid Mermaid syntax in {spec.name}"
                    RETURN False
            
            spec.last_updated = CURRENT_TIME AS ISO STRING
            LOG "  ✓ Updated: {spec.output_path}"
            RETURN True
        ELSE:
            LOG ERROR "  ✗ Error: {result.stderr}"
            RETURN False
    
    CATCH subprocess.TimeoutExpired:
        LOG ERROR "  ✗ Timeout generating {spec.name}"
        RETURN False
    
    CATCH Exception as e:
        LOG ERROR "  ✗ Exception: {e}"
        RETURN False
```

### update_all - Обновление всех диаграмм (последовательно)
```pseudo
FUNCTION update_all(diagram_type: STRING = None, force: BOOL = False) -> TUPLE[INT, INT]:
    updated = 0
    failed = 0
    skipped = 0
    
    FOR EACH spec IN self.specs:
        # Фильтр по типу если указан
        IF diagram_type AND spec.type != diagram_type:
            CONTINUE
        
        # Пропустить если не изменился (если не force)
        IF NOT force AND NOT CALL _sources_changed(spec):
            skipped += 1
            LOG "⊡ Up-to-date: {spec.name}"
            CONTINUE
        
        IF CALL update_diagram(spec):
            updated += 1
        ELSE:
            failed += 1
    
    # Сохранить обновлённые спецификации
    CALL _save_specs()
    
    LOG "Summary: {updated} updated, {failed} failed, {skipped} skipped"
    RETURN (updated, failed)
```

### update_all_parallel - Параллельное обновление диаграмм
```pseudo
FUNCTION update_all_parallel(diagram_type: STRING = None, 
                             max_workers: INT = 4, 
                             force: BOOL = False) -> TUPLE[INT, INT]:
    # Отфильтровать спецификации для обновления
    specs_to_update = []
    FOR EACH spec IN self.specs:
        IF diagram_type AND spec.type != diagram_type:
            CONTINUE
        IF spec.generator_command == "manual":
            CONTINUE
        IF NOT force AND NOT CALL _sources_changed(spec):
            LOG "⊡ Up-to-date: {spec.name}"
            CONTINUE
        APPEND spec TO specs_to_update
    
    IF NOT specs_to_update:
        LOG "No diagrams need updating"
        RETURN (0, 0)
    
    LOG "Updating {LENGTH(specs_to_update)} diagram(s) in parallel (workers={max_workers})..."
    
    updated = 0
    failed = 0
    
    # Параллельное выполнение
    WITH ProcessPoolExecutor(max_workers=max_workers) AS executor:
        # Отправить все задачи
        future_to_spec = {
            executor.submit(_update_diagram_worker, spec): spec
            FOR spec IN specs_to_update
        }
        
        # Собрать результаты
        FOR future IN as_completed(future_to_spec):
            spec = future_to_spec[future]
            TRY:
                success, last_updated = future.result()
                IF success:
                    updated += 1
                    spec.last_updated = last_updated
                    LOG "  ✓ {spec.name}"
                ELSE:
                    failed += 1
                    LOG ERROR "  ✗ {spec.name}"
            EXCEPT Exception as e:
                failed += 1
                LOG ERROR "  ✗ {spec.name}: {e}"
    
    CALL _save_specs()
    
    LOG "Summary: {updated} updated, {failed} failed"
    RETURN (updated, failed)
```

### _update_diagram_worker - Воркер для параллельного обновления
```pseudo
FUNCTION _update_diagram_worker(spec: DiagramSpec) -> TUPLE[BOOL, STRING]:
    """Worker function for parallel updates."""
    output_path = self.project_root / spec.output_path
    command = spec.generator_command.replace('{output}', str(spec.output_path))
    
    CREATE output_path.parent IF NOT EXISTS
    
    TRY:
        result = subprocess.run(
            command,
            shell = True,
            cwd = str(self.project_root),
            capture_output = True,
            text = True,
            timeout = 120
        )
        
        IF result.returncode == 0:
            RETURN (True, CURRENT_TIME AS ISO STRING)
        ELSE:
            RETURN (False, None)
    
    EXCEPT Exception:
        RETURN (False, None)
```

### watch_mode - Режим наблюдения за файлами
```pseudo
FUNCTION watch_mode():
    """Watch for file changes and auto-update diagrams."""
    IF NOT WATCHDOG_AVAILABLE:
        LOG ERROR "Watch mode requires watchdog library"
        LOG INFO "Install with: pip install watchdog"
        RETURN
    
    LOG "👀 Starting watch mode..."
    LOG "   Monitoring: {self.project_root}"
    LOG "   Press Ctrl+C to stop"
    
    # Показать отслеживаемые паттерны
    patterns = SET()
    FOR EACH spec IN self.specs:
        IF spec.generator_command != "manual":
            FOR pattern IN spec.source_files:
                ADD pattern TO patterns
    LOG "   Patterns: {JOIN(SORTED(patterns), ', ')}"
    
    # Создать event handler и observer
    event_handler = DiagramFileHandler(self)
    observer = Observer()
    observer.schedule(event_handler, str(self.project_root), recursive=True)
    observer.start()
    
    TRY:
        WHILE True:
            SLEEP(1)
    EXCEPT KeyboardInterrupt:
        observer.stop()
        LOG "👋 Stopped watching"
    
    observer.join()
```

### generate_index - Генерация индекса диаграмм
```pseudo
FUNCTION generate_index():
    index_path = self.diagrams_dir / 'INDEX.md'
    
    lines = []
    APPEND "# Diagram Index\n" TO lines
    APPEND "**Last Updated**: {CURRENT_DATETIME}\n" TO lines
    
    # Группировка по типу
    by_type: DICT[STRING, LIST[DiagramSpec]] = {}
    FOR EACH spec IN self.specs:
        IF spec.type NOT IN by_type:
            by_type[spec.type] = []
        APPEND spec TO by_type[spec.type]
    
    # Генерация секций
    FOR EACH (diagram_type, specs) IN SORTED(by_type.items()):
        APPEND "## {diagram_type.title()}\n" TO lines
        
        FOR EACH spec IN specs:
            output_path = Path(spec.output_path)
            relative_path = output_path RELATIVE TO self.diagrams_dir
            
            APPEND "### {spec.name}\n" TO lines
            APPEND "- **File**: [{output_path.name}]({relative_path})" TO lines
            APPEND "- **Type**: {spec.type}" TO lines
            IF spec.last_updated:
                APPEND "- **Last Updated**: {spec.last_updated}" TO lines
            APPEND "- **Sources**: {JOIN(spec.source_files, ', ')}" TO lines
            APPEND "" TO lines
    
    WRITE JOIN(lines, '\n') TO index_path
    LOG "Index generated: {index_path}"
```

## CLI INTERFACE
```pseudo
ARGUMENTS:
    --check              # Проверить какие диаграммы нужно обновить
    --update-all         # Обновить все диаграммы
    --type STRING        # Фильтр по типу диаграммы
    --force              # Принудительно обновить даже если не изменились
    --generate-index     # Сгенерировать индекс диаграмм
    --watch              # Наблюдать за изменениями и автообновлять
    --parallel           # Обновлять диаграммы параллельно
    --workers INT        # Количество параллельных воркеров (default: 4)

ENTRY POINT main():
    PARSE arguments
    project_root = Path(__file__).parent.parent.parent
    updater = NEW DiagramUpdater(project_root)
    
    IF args.check:
        needs_update = updater.check_updates_needed()
        IF needs_update:
            LOG "Diagrams needing update:"
            FOR EACH spec IN needs_update:
                LOG "  - {spec.name} ({spec.output_path})"
        ELSE:
            LOG "All diagrams are up to date"
    
    ELIF args.watch:
        updater.watch_mode()
    
    ELIF args.update_all:
        IF args.parallel:
            updater.update_all_parallel(args.type, args.workers, args.force)
        ELSE:
            updater.update_all(args.type, args.force)
    
    ELIF args.generate_index:
        updater.generate_index()
    
    ELSE:
        parser.print_help()
```

## ЗАВИСИМОСТИ

- os
- sys
- json
- subprocess
- time
- pathlib.Path
- datetime
- dataclasses (dataclass)
- concurrent.futures (ProcessPoolExecutor, as_completed)
- typing (List, Dict, Set, Optional)
- docs.utils.docs_logger.DocsLogger
- watchdog (optional, for watch mode)

<!--/TAG:pseudo_update_diagrams-->
