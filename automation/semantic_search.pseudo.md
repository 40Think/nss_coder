---
description: "Unified semantic search with dual_memory integration and keyword fallback"
date: 2025-12-11
source_file: semantic_search.py
tags: automation, search, semantic, keywords, hybrid, dual_memory
---

# semantic_search.py - Псевдокод

<!--TAG:pseudo_semantic_search-->

## PURPOSE
Унифицированный интерфейс поиска с:
1. Semantic search через dual_memory.py (embeddings-based)
2. Keyword search как fallback
3. Hybrid mode с Reciprocal Rank Fusion (RRF)

## РЕЖИМЫ ПОИСКА

| Mode | Описание | Когда использовать |
|------|----------|-------------------|
| `auto` | Semantic если доступен, иначе keyword | По умолчанию |
| `semantic` | Только semantic search (dual_memory) | Когда нужно понимание смысла |
| `keyword` | Только keyword matching | Для точных терминов |
| `hybrid` | RRF fusion обоих методов | Максимальная полнота |

## СТРУКТУРЫ ДАННЫХ

### SearchResult (dataclass)
```pseudo
DATACLASS SearchResult:
    file_path: STRING          # Относительный путь к файлу
    score: FLOAT               # Оценка релевантности (0.0 - 1.0)
    excerpt: STRING            # Найденный контент
    line_number: INT           # Номер строки
    context: STRING = ""       # Контекст (окружающие строки)
    content_type: STRING = "unknown"  # 'code', 'description', 'text'
    line_range: TUPLE = (0, 0)        # (start_line, end_line)
    metadata: DICT = {}               # Дополнительные метаданные
    search_method: STRING = "keyword" # 'semantic', 'keyword', 'hybrid'
    
    FUNCTION to_dict():
        # Конвертация в словарь для JSON
        RETURN {
            "file_path": self.file_path,
            "score": ROUND(self.score, 4),
            "excerpt": TRUNCATE(self.excerpt, 200),
            "line_number": self.line_number,
            "content_type": self.content_type,
            "line_range": LIST(self.line_range),
            "search_method": self.search_method,
            "metadata": self.metadata
        }
    
    CLASSMETHOD from_dual_memory_result(result):
        # Конвертация результата dual_memory в SearchResult
        RETURN SearchResult(
            file_path = result.source_file,
            score = result.score,
            excerpt = result.content[:200],
            content_type = result.content_type,
            search_method = 'semantic'
        )
```

## КЛАСС: SimpleKeywordSearcher

### Назначение
Fallback поиск по ключевым словам когда semantic недоступен.

### Инициализация
```pseudo
CLASS SimpleKeywordSearcher:
    FUNCTION __init__(project_root):
        self.project_root = project_root
        self.docs_dir = project_root / 'docs'
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', ...
        }
```

### search - Keyword поиск
```pseudo
FUNCTION search(query, top_k=10):
    # Шаг 1: Извлечь ключевые слова
    keywords = CALL _extract_keywords(query)
    
    IF keywords IS EMPTY:
        LOG WARNING "No keywords extracted"
        RETURN []
    
    results = []
    
    # Шаг 2: Поиск в документации (.md)
    FOR EACH doc_file IN RECURSIVE_GLOB(self.docs_dir, "*.md"):
        IF "__pycache__" IN str(doc_file):
            CONTINUE
        file_results = CALL _search_file(doc_file, keywords)
        EXTEND results WITH file_results
    
    # Шаг 3: Поиск в Python файлах
    FOR EACH py_file IN RECURSIVE_GLOB(self.project_root, "*.py"):
        IF "__pycache__" OR "venv" IN str(py_file):
            CONTINUE
        file_results = CALL _search_file(py_file, keywords)
        EXTEND results WITH file_results
    
    # Шаг 4: Сортировка и возврат top_k
    SORT results BY score DESCENDING
    FOR result IN results:
        result.search_method = 'keyword'
    
    RETURN results[:top_k]
```

### _extract_keywords - Извлечение ключевых слов
```pseudo
FUNCTION _extract_keywords(query):
    words = SPLIT query.lower() BY whitespace
    keywords = []
    
    FOR word IN words:
        IF word NOT IN stop_words AND LENGTH(word) > 2:
            APPEND word TO keywords
    
    RETURN keywords
```

### _search_file - Поиск в файле
```pseudo
FUNCTION _search_file(file_path, keywords):
    results = []
    
    TRY:
        lines = READ file_path AS lines
        
        FOR line_num FROM 1 TO LENGTH(lines):
            line = lines[line_num - 1]
            line_lower = line.lower()
            
            # Подсчёт совпадений
            matches = COUNT(kw FOR kw IN keywords IF kw IN line_lower)
            
            IF matches > 0:
                score = matches / LENGTH(keywords)
                
                # Извлечь контекст (3 строки до и после)
                context_start = MAX(0, line_num - 3)
                context_end = MIN(LENGTH(lines), line_num + 2)
                context = JOIN lines[context_start:context_end]
                
                # Определить тип контента
                content_type = 'description' IF file_path.suffix == '.md' ELSE 'code'
                
                result = NEW SearchResult(
                    file_path = RELATIVE(file_path, self.project_root),
                    score = score,
                    excerpt = TRIM(line),
                    line_number = line_num,
                    context = context,
                    content_type = content_type,
                    metadata = {'keyword_matches': matches}
                )
                APPEND result TO results
    CATCH:
        LOG DEBUG "Error searching file"
    
    RETURN results
```

## КЛАСС: UnifiedSearcher

### Назначение
Главный интерфейс поиска, объединяющий semantic и keyword search.

### Инициализация
```pseudo
CLASS UnifiedSearcher:
    FUNCTION __init__(project_root=None):
        self.project_root = project_root OR PROJECT_ROOT
        self.docs_dir = self.project_root / 'docs'
        
        # Попытка инициализации dual_memory для semantic search
        self.dual_memory = None
        self.has_semantic = False
        
        TRY:
            FROM docs.utils.docs_dual_memory IMPORT DocsDualMemory
            self.dual_memory = NEW DocsDualMemory()
            self.has_semantic = True
            LOG INFO "✅ Semantic search available (dual_memory)"
        CATCH ImportError:
            LOG WARNING "⚠️ dual_memory not available"
        CATCH Exception:
            LOG WARNING "⚠️ dual_memory initialization failed"
        
        # Keyword searcher всегда доступен
        self.keyword_searcher = NEW SimpleKeywordSearcher(self.project_root)
        LOG INFO "✅ Keyword search available (fallback)"
```

### search - Унифицированный поиск
```pseudo
FUNCTION search(query, mode='auto', top_k=10):
    LOG INFO "Search: query='{query}', mode={mode}, top_k={top_k}"
    
    IF mode == 'auto':
        # Автовыбор: semantic если доступен, иначе keyword
        IF self.has_semantic:
            RETURN CALL _semantic_search(query, top_k)
        ELSE:
            RETURN CALL _keyword_search(query, top_k)
    
    ELIF mode == 'semantic':
        IF NOT self.has_semantic:
            LOG ERROR "Semantic search not available"
            RETURN []
        RETURN CALL _semantic_search(query, top_k)
    
    ELIF mode == 'keyword':
        RETURN CALL _keyword_search(query, top_k)
    
    ELIF mode == 'hybrid':
        IF NOT self.has_semantic:
            LOG WARNING "Hybrid requires semantic, falling back to keyword"
            RETURN CALL _keyword_search(query, top_k)
        RETURN CALL _hybrid_search(query, top_k)
    
    ELSE:
        RAISE ValueError("Unknown search mode")
```

### _semantic_search - Semantic поиск через dual_memory
```pseudo
FUNCTION _semantic_search(query, top_k):
    LOG INFO "Performing semantic search"
    
    TRY:
        # Использовать unified search из dual_memory
        results = self.dual_memory.unified_search(query, top_k=top_k)
        
        # Конвертировать в SearchResult формат
        search_results = []
        FOR result IN results:
            sr = SearchResult.from_dual_memory_result(result)
            APPEND sr TO search_results
        
        LOG INFO "Semantic search found {LENGTH(search_results)} results"
        RETURN search_results
    
    CATCH Exception AS e:
        LOG ERROR "Semantic search failed: {e}"
        LOG INFO "Falling back to keyword search"
        RETURN CALL _keyword_search(query, top_k)
```

### _keyword_search - Keyword поиск
```pseudo
FUNCTION _keyword_search(query, top_k):
    LOG INFO "Performing keyword search"
    RETURN self.keyword_searcher.search(query, top_k)
```

### _hybrid_search - Гибридный поиск с RRF
```pseudo
FUNCTION _hybrid_search(query, top_k):
    LOG INFO "Performing hybrid search"
    
    # Получить результаты из обоих методов (больше для лучшего fusion)
    semantic_results = CALL _semantic_search(query, top_k * 2)
    keyword_results = CALL _keyword_search(query, top_k * 2)
    
    # Применить Reciprocal Rank Fusion
    combined = CALL _reciprocal_rank_fusion(
        [semantic_results, keyword_results],
        k=60  # RRF константа
    )
    
    # Пометить как hybrid
    FOR result IN combined:
        result.search_method = 'hybrid'
    
    RETURN combined[:top_k]
```

### _reciprocal_rank_fusion - RRF алгоритм
```pseudo
FUNCTION _reciprocal_rank_fusion(result_lists, k=60):
    """
    Объединение нескольких списков результатов с помощью RRF.
    
    Формула RRF: score = sum(1 / (k + rank)) для каждого списка
    
    Это стандартный алгоритм для fusion результатов из разных методов.
    """
    rrf_scores = {}
    
    FOR results IN result_lists:
        FOR rank, result IN ENUMERATE(results):
            # Уникальный ключ: file_path + line_number
            key = "{result.file_path}:{result.line_number}"
            
            IF key NOT IN rrf_scores:
                rrf_scores[key] = {
                    'result': result,
                    'score': 0.0,
                    'sources': []
                }
            
            # RRF вклад: 1 / (k + rank + 1)
            rrf_scores[key]['score'] += 1.0 / (k + rank + 1)
            APPEND result.search_method TO rrf_scores[key]['sources']
    
    # Сортировка по RRF score
    sorted_results = SORT rrf_scores.values() BY score DESCENDING
    
    # Построить финальные результаты
    final_results = []
    FOR item IN sorted_results:
        result = item['result']
        result.score = item['score']
        result.metadata['rrf_sources'] = item['sources']
        APPEND result TO final_results
    
    RETURN final_results
```

### get_status - Статус системы поиска
```pseudo
FUNCTION get_status():
    """
    Возвращает статус системы поиска.
    
    RETURN:
        Dictionary с информацией о доступности методов поиска
    """
    RETURN {
        'semantic_available': self.has_semantic,
        'keyword_available': True,
        'project_root': STRING(self.project_root),
        'docs_dir': STRING(self.docs_dir)
    }
```

## CLI INTERFACE

```pseudo
ARGUMENTS:
    query STRING              # Поисковый запрос (позиционный или --query)
    --mode CHOICE             # auto|semantic|keyword|hybrid (default: auto)
    --top-k INT               # Количество результатов (default: 10)
    --format CHOICE           # text|json (default: text)
    --show-context            # Показать контекст
    --output PATH             # Сохранить результаты в файл
    --status                  # Показать статус системы

ENTRY POINT main():
    PARSE arguments
    
    searcher = NEW UnifiedSearcher()
    
    IF args.status:
        status = searcher.get_status()
        PRINT json.dumps(status)
        RETURN
    
    query = args.query OR args.query_flag
    IF NOT query:
        PRINT help
        RETURN
    
    # Выполнить поиск
    results = searcher.search(query, mode=args.mode, top_k=args.top_k)
    
    IF args.format == 'json':
        output = {
            "query": query,
            "mode": args.mode,
            "total_results": LENGTH(results),
            "semantic_available": searcher.has_semantic,
            "results": [r.to_dict() FOR r IN results]
        }
        PRINT json.dumps(output)
    ELSE:
        # Text output с эмодзи для метода
        FOR i, result IN ENUMERATE(results, 1):
            icon = {'semantic': '🧠', 'keyword': '🔤', 'hybrid': '🔀'}[result.search_method]
            PRINT "[{icon}] {result.file_path}"
            PRINT "   Line {result.line_number} | Score: {result.score}"
            PRINT "   {result.excerpt[:100]}..."
    
    IF args.output:
        WRITE output TO args.output
```

## ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

```bash
# Auto mode (semantic если доступен)
python3 semantic_search.py "embedding generation"

# Force semantic search
python3 semantic_search.py "memory system" --mode semantic

# Keyword-only search
python3 semantic_search.py "analytics pipeline" --mode keyword

# Hybrid search (RRF fusion)
python3 semantic_search.py "dual memory" --mode hybrid

# JSON output
python3 semantic_search.py "search" --format json --top-k 5

# Show context
python3 semantic_search.py "processing" --show-context

# Check status
python3 semantic_search.py --status
```

## CONVENIENCE FUNCTIONS

```pseudo
# Для программного использования
FUNCTION search(query, mode='auto', top_k=10):
    searcher = NEW UnifiedSearcher()
    RETURN searcher.search(query, mode=mode, top_k=top_k)

FUNCTION search_semantic(query, top_k=10):
    RETURN search(query, mode='semantic', top_k=top_k)

FUNCTION search_keyword(query, top_k=10):
    RETURN search(query, mode='keyword', top_k=top_k)

FUNCTION search_hybrid(query, top_k=10):
    RETURN search(query, mode='hybrid', top_k=top_k)
```

## ЗАВИСИМОСТИ
- os
- re
- json
- argparse
- pathlib.Path
- dataclasses
- typing
- docs.utils.docs_logger.DocsLogger (isolated logging)
- docs.utils.docs_dual_memory.DocsDualMemory (optional, semantic search)

## ТЕСТЫ
- tests/test_semantic_search_unified.py (9 тестов)

<!--/TAG:pseudo_semantic_search-->
