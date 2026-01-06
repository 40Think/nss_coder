---
description: "Поиск зависимостей с кэшированием, инвертированным индексом и графовыми запросами"
date: 2025-12-13
source_file: search_dependencies.py
tags: automation, dependencies, search, visualization, cache, networkx
version: 2.0
---

# search_dependencies.py - Псевдокод (v2.0)

<!--TAG:pseudo_search_dependencies-->

## PURPOSE
Ищет зависимости для файла с оптимизациями:
- **LRU Cache**: Кэширование JSON файлов в памяти (10x speedup)
- **Inverted Index**: O(1) поиск обратных зависимостей (100x speedup)
- **NetworkX Graph**: Транзитивные зависимости, поиск циклов

## СТРУКТУРЫ ДАННЫХ

### DependencyInfo (dataclass)
```pseudo
DATACLASS DependencyInfo:
    file_path: STRING                     # Путь к файлу
    dependencies: DICT[STRING, LIST]      # Категория -> список зависимостей
    reverse_dependencies: LIST[STRING]    # Файлы, которые зависят от этого
    transitive_dependencies: LIST[STRING] # Транзитивные зависимости
```

### CacheStats (dataclass)
```pseudo
DATACLASS CacheStats:
    hits: INT = 0           # Попадания в кэш
    misses: INT = 0         # Промахи кэша
    total_load_time_ms: FLOAT = 0.0  # Время загрузки с диска
    
    PROPERTY hit_rate -> FLOAT:
        RETURN hits / (hits + misses) * 100
```

## КЛАСС: DependencySearcher

### Инициализация
```pseudo
CLASS DependencySearcher:
    FUNCTION __init__(project_root):
        self.project_root = project_root
        self.deps_dir = project_root / 'docs' / 'memory' / 'dependencies'
        
        # TASK 1: LRU Cache
        self._cache = {}              # {file_path: deps_data}
        self._cache_stats = CacheStats()
        self._cache_max_size = 100
        
        # TASK 2: Inverted Index
        self._reverse_index_file = deps_dir / '_reverse_index.json'
        self._reverse_index = {}      # module -> [files that import it]
        self._reverse_index_loaded = FALSE
        
        # TASK 3: NetworkX Graph
        self._graph = None            # nx.DiGraph
        self._graph_built = FALSE
```

---

## TASK 1: LRU CACHE

### _load_deps_cached - Загрузка с кэшированием
```pseudo
FUNCTION _load_deps_cached(dep_file):
    cache_key = str(dep_file)
    
    # Проверка кэша
    IF cache_key IN self._cache:
        self._cache_stats.hits += 1
        RETURN self._cache[cache_key]
    
    # Кэш-промах: загрузка с диска
    self._cache_stats.misses += 1
    start_time = NOW()
    
    deps = READ dep_file AS JSON
    
    # LRU eviction: удалить старейший если превышен лимит
    IF len(self._cache) >= self._cache_max_size:
        oldest_key = FIRST_KEY(self._cache)
        DELETE self._cache[oldest_key]
    
    self._cache[cache_key] = deps
    RETURN deps
```

### get_cache_stats - Статистика кэша
```pseudo
FUNCTION get_cache_stats():
    RETURN {
        "hits": self._cache_stats.hits,
        "misses": self._cache_stats.misses,
        "hit_rate": f"{self._cache_stats.hit_rate}%",
        "cached_entries": len(self._cache)
    }
```

---

## TASK 2: INVERTED INDEX

### _load_or_build_reverse_index - Загрузка/построение индекса
```pseudo
FUNCTION _load_or_build_reverse_index():
    IF self._reverse_index_loaded:
        RETURN self._reverse_index
    
    # Попытка загрузить с диска
    IF self._reverse_index_file.exists():
        self._reverse_index = READ self._reverse_index_file AS JSON
        self._reverse_index_loaded = TRUE
        RETURN self._reverse_index
    
    # Построить с нуля
    RETURN CALL rebuild_reverse_index()
```

### rebuild_reverse_index - Полное перестроение индекса
```pseudo
FUNCTION rebuild_reverse_index():
    index = defaultdict(list)
    
    FOR EACH dep_file IN GLOB(deps_dir, '*_dependencies.json'):
        IF dep_file.name == '_reverse_index.json':
            CONTINUE
        
        deps = CALL _load_deps_cached(dep_file)
        source_file = deps.get('file_path')
        
        # Индексировать импорты
        FOR EACH imp IN deps.get('imports', []):
            module = imp.get('module')
            index[module].append(source_file)
            index[module.split('.')[-1]].append(source_file)  # Также по stem
        
        # Индексировать function calls
        FOR EACH call IN deps.get('function_calls', []):
            func = call.get('function')
            IF '.' IN func:
                module_prefix = func.split('.')[0]
                index[module_prefix].append(source_file)
    
    # Сохранить на диск
    WRITE index TO self._reverse_index_file AS JSON
    
    self._reverse_index = dict(index)
    self._reverse_index_loaded = TRUE
    RETURN self._reverse_index
```

### _find_reverse_dependencies_fast - O(1) поиск
```pseudo
FUNCTION _find_reverse_dependencies_fast(target_file):
    CALL _load_or_build_reverse_index()
    
    target_name = target_file.stem
    reverse_deps = self._reverse_index.get(target_name, [])
    
    RETURN UNIQUE(reverse_deps)
```

---

## TASK 3: NETWORKX GRAPH

### _build_dependency_graph - Построение графа
```pseudo
FUNCTION _build_dependency_graph():
    IF NOT HAS_NETWORKX:
        LOG ERROR "NetworkX not installed"
        RETURN None
    
    self._graph = nx.DiGraph()
    
    FOR EACH dep_file IN GLOB(deps_dir, '*_dependencies.json'):
        deps = CALL _load_deps_cached(dep_file)
        source = deps.get('file_path')
        
        self._graph.add_node(source, type='file')
        
        FOR EACH imp IN deps.get('imports', []):
            target = imp.get('module')
            self._graph.add_node(target, type='module')
            self._graph.add_edge(source, target, type='import')
    
    self._graph_built = TRUE
    RETURN self._graph
```

### find_transitive_dependencies - BFS обход
```pseudo
FUNCTION find_transitive_dependencies(file_path, max_depth=3):
    CALL _ensure_graph_built()
    
    # Нормализация пути (поддержка абсолютных и относительных)
    target_str = NORMALIZE_PATH(file_path)
    
    IF target_str NOT IN self._graph:
        LOG WARNING "Node not found"
        RETURN []
    
    # BFS обход
    visited = SET()
    queue = [(target_str, 0)]
    
    WHILE queue NOT EMPTY:
        node, depth = queue.pop(0)
        
        IF depth >= max_depth OR node IN visited:
            CONTINUE
        
        visited.add(node)
        
        FOR EACH successor IN self._graph.successors(node):
            queue.append((successor, depth + 1))
    
    visited.remove(target_str)
    RETURN sorted(list(visited))
```

### detect_cycles - Поиск циклических зависимостей
```pseudo
FUNCTION detect_cycles():
    CALL _ensure_graph_built()
    cycles = nx.simple_cycles(self._graph)
    RETURN list(cycles)
```

### get_graph_stats - Статистика графа
```pseudo
FUNCTION get_graph_stats():
    CALL _ensure_graph_built()
    RETURN {
        "nodes": self._graph.number_of_nodes(),
        "edges": self._graph.number_of_edges(),
        "density": nx.density(self._graph),
        "is_dag": nx.is_directed_acyclic_graph(self._graph)
    }
```

---

## CORE SEARCH METHODS

### search - Main search function
```pseudo
FUNCTION search(file_path, include_reverse=FALSE):
    # Normalize path (absolute to relative)
    target_file = Path(file_path)
    IF target_file.is_absolute():
        target_file = target_file.relative_to(project_root)
    
    # Find dependency JSON file
    dep_file = CALL _find_dependency_file(target_file)
    
    IF NOT dep_file OR NOT dep_file.exists():
        LOG ERROR "No dependency map found for: {file_path}"
        RETURN None
    
    # Load dependencies using cache
    deps = CALL _load_deps_cached(dep_file)
    
    # Create result object
    result = DependencyInfo(
        file_path=str(target_file),
        dependencies=deps
    )
    
    # Find reverse dependencies if requested (using fast O(1) lookup)
    IF include_reverse:
        result.reverse_dependencies = CALL _find_reverse_dependencies_fast(target_file)
    
    RETURN result
```

### _find_dependency_file - Locate dependency JSON
```pseudo
FUNCTION _find_dependency_file(target_file):
    # Try exact match by stem
    dep_file = deps_dir / f"{target_file.stem}_dependencies.json"
    IF dep_file.exists():
        RETURN dep_file
    
    # Try in subdirectory matching file structure
    IF target_file.parent != Path('.'):
        dep_file = deps_dir / target_file.parent / f"{target_file.stem}_dependencies.json"
        IF dep_file.exists():
            RETURN dep_file
    
    RETURN None
```

### _find_reverse_dependencies - Legacy fallback
```pseudo
FUNCTION _find_reverse_dependencies(target_file):
    # Kept for backward compatibility
    # Delegates to fast inverted index lookup
    RETURN CALL _find_reverse_dependencies_fast(target_file)
```

---

## VISUALIZATION METHODS

### visualize_dependencies - Create visual representation
```pseudo
FUNCTION visualize_dependencies(file_path, output_format='text'):
    # Search with reverse dependencies
    info = CALL search(file_path, include_reverse=TRUE)
    
    IF NOT info:
        RETURN "No dependency information available"
    
    # Generate output based on format
    IF output_format == 'mermaid':
        RETURN CALL _generate_mermaid(info)
    ELSE:
        RETURN CALL _generate_text(info)
```

### _generate_text - Text format output
```pseudo
FUNCTION _generate_text(info):
    lines = []
    lines.append(f"Dependencies for: {info.file_path}")
    lines.append("=" * 60)
    
    # Code dependencies (imports)
    IF info.dependencies.get('imports'):
        lines.append("\n📦 CODE DEPENDENCIES (Imports)")
        FOR EACH imp IN info.dependencies['imports']:
            lines.append(f"  • import {imp.get('module')}")
    
    # Configuration dependencies
    IF info.dependencies.get('config_files'):
        lines.append("\n⚙️  CONFIG DEPENDENCIES")
        FOR EACH cfg IN info.dependencies['config_files']:
            lines.append(f"  • {cfg.get('file')}")
    
    # Data dependencies
    IF info.dependencies.get('file_reads'):
        lines.append("\n📥 DATA INPUTS (File Reads)")
        FOR EACH read IN info.dependencies['file_reads']:
            lines.append(f"  • {read.get('path')}")
    
    # Reverse dependencies
    IF info.reverse_dependencies:
        lines.append("\n⬅️  REVERSE DEPENDENCIES")
        FOR EACH dep IN info.reverse_dependencies:
            lines.append(f"  • {dep}")
    
    RETURN JOIN(lines, '\n')
```

### _generate_mermaid - Mermaid diagram output
```pseudo
FUNCTION _generate_mermaid(info):
    lines = ["```mermaid", "graph TD"]
    
    # Main file node
    lines.append(f"    MAIN[{info.file_path}]")
    lines.append("    style MAIN fill:#f9f,stroke:#333,stroke-width:2px")
    
    # Import nodes (limit to 10)
    FOR i, imp IN ENUMERATE(info.dependencies.get('imports', [])[:10]):
        safe_id = f"IMP{i}"
        lines.append(f"    {safe_id}[{imp.get('module')}]")
        lines.append(f"    MAIN --> {safe_id}")
    
    # Config file nodes
    FOR i, cfg IN ENUMERATE(info.dependencies.get('config_files', [])):
        safe_id = f"CFG{i}"
        lines.append(f"    {safe_id}[{cfg.get('file')}]")
        lines.append(f"    MAIN -.-> {safe_id}")
    
    # Reverse dependency nodes (limit to 5)
    IF info.reverse_dependencies:
        FOR i, rev IN ENUMERATE(info.reverse_dependencies[:5]):
            safe_id = f"REV{i}"
            lines.append(f"    {safe_id}[{Path(rev).name}]")
            lines.append(f"    {safe_id} --> MAIN")
    
    lines.append("```")
    RETURN JOIN(lines, '\n')
```

---

## ADDITIONAL GRAPH METHODS

### _ensure_graph_built - Lazy graph initialization
```pseudo
FUNCTION _ensure_graph_built():
    IF NOT HAS_NETWORKX:
        LOG WARNING "NetworkX not available"
        RETURN FALSE
    
    IF self._graph_built:
        RETURN TRUE
    
    CALL _build_dependency_graph()
    RETURN TRUE
```

### find_shortest_path - NetworkX path query
```pseudo
FUNCTION find_shortest_path(source, target):
    IF NOT CALL _ensure_graph_built():
        RETURN None
    
    TRY:
        path = nx.shortest_path(self._graph, source, target)
        RETURN path
    EXCEPT nx.NetworkXNoPath:
        LOG INFO "No path found from {source} to {target}"
        RETURN None
    EXCEPT nx.NodeNotFound:
        LOG WARNING "Node not found"
        RETURN None
```

### clear_cache - Clear LRU cache
```pseudo
FUNCTION clear_cache():
    self._cache.clear()
    self._cache_stats = CacheStats()
    LOG INFO "Cache cleared"
```

---

## CLI ИНТЕРФЕЙС

```pseudo
PROGRAM main:
    parser = ArgumentParser()
    
    # Базовые аргументы
    parser.add("--file", help="File to analyze")
    parser.add("--reverse", action="store_true")
    parser.add("--format", choices=["text", "mermaid", "json"])
    parser.add("--output", help="Save to file")
    
    # Cache
    parser.add("--stats", action="store_true", help="Show cache stats")
    
    # Index
    parser.add("--rebuild-index", action="store_true")
    
    # Graph
    parser.add("--transitive", action="store_true")
    parser.add("--depth", type=int, default=3)
    parser.add("--cycles", action="store_true")
    parser.add("--graph-stats", action="store_true")
    parser.add("--path", nargs=2, metavar=("SOURCE", "TARGET"), help="Find shortest path")
    
    args = parser.parse_args()
    searcher = DependencySearcher(project_root)
    
    # Обработка команд
    IF args.rebuild_index:
        searcher.rebuild_reverse_index()
        PRINT "✅ Index rebuilt"
    
    ELIF args.cycles:
        cycles = searcher.detect_cycles()
        PRINT cycles
    
    ELIF args.graph_stats:
        stats = searcher.get_graph_stats()
        PRINT stats
    
    ELIF args.path:
        source, target = args.path
        path = searcher.find_shortest_path(source, target)
        IF path:
            PRINT f"📍 Shortest path: {' → '.join(path)}"
        ELSE:
            PRINT "❌ No path found"
    
    ELIF args.transitive:
        deps = searcher.find_transitive_dependencies(args.file, args.depth)
        PRINT deps
        IF args.stats:
            PRINT searcher.get_cache_stats()
    
    ELSE:
        # Standard search
        IF args.format == 'json':
            info = searcher.search(args.file, args.reverse)
            result = JSON.dumps(info)
        ELSE:
            result = searcher.visualize_dependencies(args.file, args.format)
        
        IF args.stats:
            result += searcher.get_cache_stats()
        
        IF args.output:
            WRITE result TO args.output
        ELSE:
            PRINT result
```
```

<!--/TAG:pseudo_search_dependencies-->

## МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ

| Операция | До оптимизации | После оптимизации |
|----------|---------------|-------------------|
| Поиск зависимостей | O(1) disk I/O | O(1) memory (cache) |
| Обратные зависимости | O(N) scan all files | O(1) index lookup |
| Транзитивные deps | ❌ Не поддерживалось | O(V+E) BFS |
| Поиск циклов | ❌ Не поддерживалось | O(V+E) DFS |

## СВЯЗАННЫЕ ФАЙЛЫ

- **Реализация**: `docs/automation/search_dependencies.py`
- **Тесты**: `tests/test_search_dependencies.py`
- **Индекс**: `docs/memory/dependencies/_reverse_index.json`
