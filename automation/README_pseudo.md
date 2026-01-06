---
description: "Псевдокод-описания для всех automation-скриптов"
date: 2025-12-09
status: Complete
version: 1.0
---

# Pseudocode Documentation

<!--TAG:pseudocode_docs-->

Эта директория содержит псевдокод-описания для каждого Python-скрипта 
в `docs/automation/`. Отношение 1:1 между исходным файлом и его описанием.

## Формат файлов

Каждый файл `*.pseudo.md` содержит:

1. **YAML frontmatter** - метаданные (description, date, source_file, tags)
2. **PURPOSE** - высокоуровневое описание назначения
3. **Структуры данных** - dataclasses и их поля
4. **Алгоритмы** - псевдокод функций и методов
5. **CLI Interface** - описание аргументов командной строки
6. **Зависимости** - список используемых модулей

## Список файлов

| Исходный файл | Псевдокод | Описание |
|---------------|-----------|----------|

| `analyze_dependencies.py` | [analyze_dependencies.pseudo.md](analyze_dependencies.pseudo.md) | AST-анализ зависимостей Python |
| `assemble_context.py` | [assemble_context.pseudo.md](assemble_context.pseudo.md) | Сборка контекста для AI-агентов |
| `chunk_documents.py` | [chunk_documents.pseudo.md](chunk_documents.pseudo.md) | Семантическое разбиение документов |
| `generate_call_graph.py` | [generate_call_graph.pseudo.md](generate_call_graph.pseudo.md) | Генерация графов вызовов |
| `index_project.py` | [index_project.pseudo.md](index_project.pseudo.md) | Индексация проекта (embeddings, graph) |
| `search_by_tag.py` | [search_by_tag.pseudo.md](search_by_tag.pseudo.md) | Поиск по семантическим тегам |
| `search_dependencies.py` | [search_dependencies.pseudo.md](search_dependencies.pseudo.md) | Поиск зависимостей файла |
| `semantic_search.py` | [semantic_search.pseudo.md](semantic_search.pseudo.md) | Keyword-based поиск в документации |
| `summarize_docs.py` | [summarize_docs.pseudo.md](summarize_docs.pseudo.md) | Суммаризация документов |
| `test_system.py` | [test_system.pseudo.md](test_system.pseudo.md) | Тестирование системы документации |
| `update_diagrams.py` | [update_diagrams.pseudo.md](update_diagrams.pseudo.md) | Автообновление диаграмм |
| `validate_docs.py` | [validate_docs.pseudo.md](validate_docs.pseudo.md) | Валидация документации |

## Использование

Псевдокод-описания полезны для:

- **Понимания логики** без чтения реального кода
- **Онбординга** новых разработчиков
- **AI-агентов** для понимания структуры скриптов
- **Документации** алгоритмов и data flow
- **Code review** для сравнения с реализацией

## Примечания

- Все файлы содержат семантические теги `<!--TAG:pseudo_*-->`
- Псевдокод использует упрощённый синтаксис близкий к Python
- Алгоритмы разбиты на логические шаги с комментариями
- CLI interface описывает все доступные аргументы

<!--/TAG:pseudocode_docs-->
