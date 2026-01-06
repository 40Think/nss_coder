---
description: "Поиск файлов по семантическим тегам <!--TAG:name-->"
date: 2025-12-12
source_file: search_by_tag.py
tags: automation, search, tags, semantic
---

# search_by_tag.py - Псевдокод

<!--TAG:pseudo_search_by_tag-->

## PURPOSE
Ищет файлы, содержащие специфические семантические теги.
Устойчив к сдвигам строк и изменениям кода.
Поддерживает листинг всех доступных тегов.

## ФОРМАТ ТЕГОВ
```
Открывающий тег: <!--TAG:tag_name-->
Закрывающий тег: <!--/TAG:tag_name-->
```

## СТРУКТУРЫ ДАННЫХ

### TagMatch (dataclass)
```pseudo
DATACLASS TagMatch:
    tag: STRING              # Имя тега
    file_path: STRING        # Относительный путь к файлу
    start_line: INT          # Начальная строка
    end_line: INT            # Конечная строка
    content: STRING          # Содержимое между тегами
    context_before: STRING   # Контекст до (опционально)
    context_after: STRING    # Контекст после (опционально)
```

## КЛАСС: TagSearcher

### Инициализация
```pseudo
CLASS TagSearcher:
    FUNCTION __init__(project_root):
        self.project_root = project_root
```

### search - Поиск тега во всех файлах
```pseudo
FUNCTION search(tag, include_context=False):
    matches = []
    
    # Поиск в docs/
    docs_dir = self.project_root / 'docs'
    FOR EACH file_path IN RECURSIVE_GLOB(docs_dir, "*"):
        IF file_path IS FILE AND file_path.suffix IN [".md", ".py", ".yaml", ".yml"]:
            file_matches = CALL _search_file(file_path, tag, include_context)
            EXTEND matches WITH file_matches
    
    # Поиск в code directories
    FOR EACH code_dir IN ["processing", "utils", "scripts"]:
        code_path = self.project_root / code_dir
        IF code_path.exists():
            FOR EACH file_path IN RECURSIVE_GLOB(code_path, "*.py"):
                file_matches = CALL _search_file(file_path, tag, include_context)
                EXTEND matches WITH file_matches
    
    RETURN matches
```

### _search_file - Поиск тега в одном файле
```pseudo
FUNCTION _search_file(file_path, tag, include_context):
    matches = []
    
    TRY:
        content = READ file_path as UTF-8
    CATCH:
        RETURN matches
    
    # Построить паттерны тегов
    opening_tag = "<!--TAG:{tag}-->"
    closing_tag = "<!--/TAG:{tag}-->"
    
    # Итеративный поиск всех вхождений
    start_pos = 0
    WHILE True:
        # Найти открывающий тег
        start_idx = FIND opening_tag IN content STARTING FROM start_pos
        IF start_idx == -1:
            BREAK
        
        # Найти закрывающий тег
        end_idx = FIND closing_tag IN content STARTING FROM start_idx
        IF end_idx == -1:
            LOG WARNING "Unclosed tag {tag} in {file_path}"
            BREAK
        
        # Извлечь содержимое между тегами
        tag_content = content[start_idx + LENGTH(opening_tag) : end_idx]
        tag_content = TRIM tag_content
        
        # Вычислить номера строк
        start_line = COUNT newlines IN content[0:start_idx] + 1
        end_line = COUNT newlines IN content[0:end_idx] + 1
        
        # Извлечь контекст если запрошено
        context_before = ""
        context_after = ""
        IF include_context:
            lines = SPLIT content BY newlines
            context_before = JOIN lines[max(0, start_line-4) : start_line-1]
            context_after = JOIN lines[end_line : min(LENGTH(lines), end_line+3)]
        
        # Создать match
        match = NEW TagMatch(
            tag = tag,
            file_path = str(file_path RELATIVE TO self.project_root),
            start_line = start_line,
            end_line = end_line,
            content = tag_content,
            context_before = context_before,
            context_after = context_after
        )
        APPEND match TO matches
        
        # Продолжить поиск после текущего тега
        start_pos = end_idx + LENGTH(closing_tag)
    
    RETURN matches
```

### find_all_tags - Найти все уникальные теги в проекте
```pseudo
FUNCTION find_all_tags():
    tags = SET()
    
    # Обойти все директории
    FOR EACH root_dir IN [
        self.project_root / 'docs',
        self.project_root / 'processing',
        self.project_root / 'utils'
    ]:
        IF NOT root_dir.exists():
            CONTINUE
        
        FOR EACH file_path IN RECURSIVE_GLOB(root_dir, "*"):
            IF file_path IS NOT FILE:
                CONTINUE
            
            TRY:
                content = READ file_path as UTF-8
                
                # Найти все открывающие теги через regex
                tag_pattern = r"<!--TAG:([a-zA-Z0-9_]+)-->"
                found_tags = REGEX FINDALL tag_pattern IN content
                
                # Добавить в множество
                FOR EACH tag IN found_tags:
                    ADD tag TO tags
            CATCH:
                CONTINUE
    
    RETURN SORTED LIST FROM tags
```

## CLI INTERFACE
```pseudo
ARGUMENTS:
    --tag STRING        # Тег для поиска
    --list-tags         # Показать все доступные теги
    --show-context      # Показать контекст вокруг совпадений
    --output PATH       # Сохранить результаты в файл

ENTRY POINT main():
    PARSE arguments
    project_root = DETECT from script location
    searcher = NEW TagSearcher(project_root)
    
    # Режим списка тегов
    IF args.list_tags:
        PRINT "Available tags:"
        tags = searcher.find_all_tags()
        FOR EACH tag IN tags:
            PRINT "  - {tag}"
        RETURN
    
    # Проверка наличия тега
    IF NOT args.tag:
        PRINT help
        RETURN
    
    # Поиск тега
    matches = searcher.search(args.tag, args.show_context)
    
    IF NOT matches:
        PRINT "No matches found for tag: {args.tag}"
        RETURN
    
    # Форматирование вывода
    output = []
    APPEND "Found {LENGTH(matches)} match(es) for tag: {args.tag}" TO output
    APPEND "=" * 60 TO output
    
    FOR i, match IN ENUMERATE(matches, 1):
        APPEND "[{i}] {match.file_path} (lines {match.start_line}-{match.end_line})" TO output
        APPEND "-" * 60 TO output
        
        IF match.context_before AND args.show_context:
            APPEND "... context before ..." TO output
            APPEND match.context_before TO output
        
        APPEND match.content TO output
        
        IF match.context_after AND args.show_context:
            APPEND "... context after ..." TO output
            APPEND match.context_after TO output
    
    result = JOIN(output, "\n")
    
    # Вывод или сохранение
    IF args.output:
        WRITE result TO args.output
        LOG "Results saved to: {args.output}"
    ELSE:
        PRINT result
```

## ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
```bash
# Найти все файлы с тегом "analytics"
python3 search_by_tag.py --tag analytics

# Показать все теги в проекте
python3 search_by_tag.py --list-tags

# Поиск с контекстом
python3 search_by_tag.py --tag feature_entropy --show-context
```

## ЗАВИСИМОСТИ
- os
- re (regex)
- pathlib.Path
- dataclasses
- docs.utils.docs_logger.DocsLogger

<!--/TAG:pseudo_search_by_tag-->
