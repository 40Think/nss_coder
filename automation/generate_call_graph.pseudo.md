---
description: "Генерирует графы вызовов функций с LLM анализом, метриками, dual memory индексацией"
date: 2025-12-12
source_file: generate_call_graph.py
tags: automation, call-graph, visualization, AST, LLM, dual-memory, metrics
---

# generate_call_graph.py - Псевдокод

<!--TAG:pseudo_generate_call_graph-->

## PURPOSE
Анализирует Python-код для генерации статических графов вызовов функций.
Визуализирует зависимости функций через Mermaid.js, Graphviz DOT и JSON форматы.

## СТРУКТУРЫ ДАННЫХ

### FunctionNode (dataclass)
```pseudo
DATACLASS FunctionNode:
    name: STRING              # Имя функции
    file_path: STRING         # Путь к файлу
    line_number: INT          # Номер строки
    calls: LIST[STRING]       # Какие функции вызывает
    called_by: LIST[STRING]   # Кем вызывается (reverse edge)
```

## КЛАСС: CallGraphGenerator

### Инициализация
```pseudo
CLASS CallGraphGenerator:
    FUNCTION __init__(project_root):
        self.project_root = project_root
        self.functions: DICT[STRING, FunctionNode] = {}  # name -> node
```

### analyze_file - Анализ одного файла
```pseudo
FUNCTION analyze_file(file_path):
    # Шаг 1: Чтение и парсинг файла
    source = READ file_path as UTF-8
    TRY:
        tree = ast.parse(source)
    CATCH SyntaxError:
        LOG WARNING "Cannot parse {file_path}"
        RETURN
    
    # Шаг 2: Обход AST для поиска функций
    FOR EACH node IN ast.walk(tree):
        IF node IS ast.FunctionDef:
            func_name = node.name
            func_id = GENERATE unique ID: "{file_stem}.{func_name}"
            
            # Создать узел функции
            func_node = NEW FunctionNode(
                name = func_name,
                file_path = RELATIVE path to project_root,
                line_number = node.lineno,
                calls = [],
                called_by = []
            )
            
            # Шаг 3: Найти все вызовы внутри функции
            FOR EACH child IN ast.walk(node):
                IF child IS ast.Call:
                    call_name = CALL _extract_call_name(child)
                    IF call_name IS NOT None:
                        APPEND call_name TO func_node.calls
            
            # Сохранить функцию
            self.functions[func_name] = func_node
```

### analyze_directory - Анализ директории
```pseudo
FUNCTION analyze_directory(directory):
    FOR EACH py_file IN GLOB(directory, "**/*.py"):
        CALL analyze_file(py_file)
```

### analyze_project - Анализ всего проекта
```pseudo
FUNCTION analyze_project():
    # Анализировать ключевые директории
    FOR EACH dir IN ["processing", "utils", "scripts"]:
        dir_path = self.project_root / dir
        IF dir_path.exists():
            CALL analyze_directory(dir_path)
```

### build_reverse_edges - Построение обратных связей
```pseudo
FUNCTION build_reverse_edges():
    # Для каждой функции
    FOR EACH (caller_name, caller_node) IN self.functions:
        # Для каждого вызова
        FOR EACH callee_name IN caller_node.calls:
            # Найти вызываемую функцию (может быть неполное имя)
            FOR EACH (func_name, func_node) IN self.functions:
                IF func_name ENDS WITH "::{callee_name}":
                    # Добавить обратную связь
                    APPEND caller_name TO func_node.called_by
```

### generate_mermaid - Генерация Mermaid диаграммы
```pseudo
FUNCTION generate_mermaid(max_nodes=50):
    lines = []
    APPEND "```mermaid" TO lines
    APPEND "graph TD" TO lines
    
    # Ограничить количество узлов для читаемости
    func_items = TAKE FIRST max_nodes FROM self.functions.items()
    
    # Создать узлы и рёбра
    FOR EACH (func_id, func_node) IN func_items:
        # Санитизация ID для Mermaid (заменить точки и дефисы)
        node_id = REPLACE('.', '_') AND REPLACE('-', '_') IN func_id
        node_label = "{func_node.name}\\n{file_stem}"
        
        # Добавить узел
        APPEND "    {node_id}[\"{node_label}\"]" TO lines
        
        # Добавить рёбра (ограничить до 10 на узел)
        FOR EACH called_func IN FIRST 10 OF func_node.calls:
            # Найти целевой узел
            FOR EACH (target_id, target_node) IN func_items:
                IF target_node.name == called_func OR target_id ENDS WITH ".{called_func}":
                    target_node_id = REPLACE('.', '_') AND REPLACE('-', '_') IN target_id
                    APPEND "    {node_id} --> {target_node_id}" TO lines
                    BREAK
    
    APPEND "```" TO lines
    RETURN JOIN(lines, "\n")
```

### generate_graphviz - Генерация Graphviz DOT
```pseudo
FUNCTION generate_graphviz():
    output = [
        "digraph CallGraph {",
        "    rankdir=LR;",
        "    node [shape=box];"
    ]
    
    # Добавить узлы
    FOR EACH (func_name, node) IN self.functions:
        short_name = EXTRACT function name FROM func_name
        label = "{short_name}\\n{node.file_path}:{node.line_number}"
        APPEND '    "{func_name}" [label="{label}"];' TO output
    
    # Добавить рёбра
    FOR EACH (func_name, node) IN self.functions:
        FOR EACH callee IN node.calls:
            FOR EACH other_name IN self.functions:
                IF other_name ENDS WITH "::{callee}":
                    APPEND '    "{func_name}" -> "{other_name}";' TO output
    
    APPEND "}" TO output
    RETURN JOIN(output, "\n")
```

### generate_json - Генерация JSON представления
```pseudo
FUNCTION generate_json(include_metrics=False):
    data = {
        "functions": {},
        "edges": [],
        "generated_at": NOW()
    }
    
    # Добавить функции как словарь
    FOR EACH (func_id, func_node) IN self.functions:
        data.functions[func_id] = {
            "name": func_node.name,
            "file": func_node.file_path,
            "line": func_node.line_number,
            "calls": func_node.calls,
            "called_by": func_node.called_by
        }
        
        # Добавить рёбра
        FOR EACH called_func IN func_node.calls:
            APPEND {
                "from": func_id,
                "to": called_func,
                "type": "calls"
            } TO data.edges
    
    # Добавить метрики если запрошено
    IF include_metrics:
        data.metrics = CALL calculate_metrics()
    
    RETURN data
```

### _extract_call_name - Извлечение имени вызова
```pseudo
FUNCTION _extract_call_name(call_node):
    IF call_node.func IS ast.Name:
        # Простой вызов: func()
        RETURN call_node.func.id
    ELIF call_node.func IS ast.Attribute:
        # Метод: obj.method()
        RETURN call_node.func.attr
    ELSE:
        RETURN None
```

### _find_cycles - Поиск циклических зависимостей
```pseudo
FUNCTION _find_cycles():
    cycles = []
    visited = SET()
    rec_stack = SET()  # Recursion stack для детекции циклов
    
    # Вложенная DFS функция
    FUNCTION dfs(node_id, path):
        IF node_id IN rec_stack:
            # Найден цикл, извлечь его
            cycle_start = INDEX OF node_id IN path
            cycle = path[cycle_start:] + [node_id]
            APPEND cycle TO cycles
            RETURN
        
        IF node_id IN visited:
            RETURN
        
        ADD node_id TO visited
        ADD node_id TO rec_stack
        APPEND node_id TO path
        
        # Обход вызовов
        IF node_id IN self.functions:
            FOR EACH called_name IN self.functions[node_id].calls:
                # Найти полный ID для вызова
                FOR EACH target_id IN self.functions:
                    IF target_id ENDS WITH ".{called_name}":
                        CALL dfs(target_id, COPY OF path)
                        BREAK
        
        REMOVE node_id FROM rec_stack
    
    # Запустить DFS от каждого узла (ограничить до 50 для производительности)
    FOR EACH func_id IN FIRST 50 OF self.functions:
        CALL dfs(func_id, [])
    
    RETURN FIRST 10 cycles  # Ограничить результат
```


## CLI INTERFACE
```pseudo
ARGUMENTS:
    --directory PATH    # Директория для анализа
    --output PATH       # Выходной файл
    --format STRING     # Формат: mermaid|graphviz|json (default: mermaid)
    --max-nodes INT     # Максимум узлов для mermaid (default: 50)

ENTRY POINT main():
    PARSE arguments
    project_root = DETECT from script location
    
    generator = NEW CallGraphGenerator(project_root)
    
    IF args.directory:
        generator.analyze_directory(args.directory)
    ELSE:
        generator.analyze_project()
    
    generator.build_reverse_edges()
    
    # Генерация вывода
    IF args.format == "mermaid":
        result = generator.generate_mermaid(args.max_nodes)
    ELIF args.format == "graphviz":
        result = generator.generate_graphviz()
    ELIF args.format == "json":
        result = generator.generate_json()
    
    # Сохранение или вывод
    IF args.output:
        WRITE result TO args.output
        LOG "Saved to {args.output}"
    ELSE:
        PRINT result
```

## НОВЫЕ МЕТОДЫ (TICKET #04, 2025-12-11)

### calculate_metrics - Расчет метрик графа
```pseudo
FUNCTION calculate_metrics():
    metrics = {
        node_count: LEN(self.functions),
        edge_count: SUM(LEN(f.calls) FOR f IN self.functions),
        calculated_at: NOW()
    }
    
    # Плотность графа
    n = metrics.node_count
    IF n > 1:
        max_edges = n * (n - 1)
        metrics.density = metrics.edge_count / max_edges
    
    # Центральность (degree centrality)
    centrality = []
    FOR EACH (id, node) IN self.functions:
        degree = LEN(node.calls) + LEN(node.called_by)
        APPEND (id, degree) TO centrality
    SORT centrality BY degree DESC
    metrics.most_central_functions = centrality[:5]
    
    # Детекция циклов
    cycles = CALL _find_cycles()
    metrics.circular_dependencies = LEN(cycles)
    
    # Orphan-функции
    orphans = [id FOR id, node IN self.functions 
               IF LEN(node.called_by) == 0 AND node.name NOT IN ["main", "__init__"]]
    metrics.orphan_count = LEN(orphans)
    
    RETURN metrics
```

### analyze_with_llm - LLM анализ графа
```pseudo
FUNCTION analyze_with_llm(mermaid_content):
    TRY:
        backend = NEW VLLMBackend()
        status, _ = backend.check_health()
        
        IF status != "OK":
            LOG WARNING "vLLM not available"
            RETURN {}
        
        prompt = BUILD analysis prompt with:
            - function count
            - edge count
            - mermaid diagram (first 1500 chars)
        
        response = backend.generate(prompt, max_tokens=300)
        
        RETURN {
            llm_analysis: response,
            analyzed_at: NOW(),
            model: "vllm"
        }
    
    CATCH Exception:
        LOG WARNING "LLM analysis failed"
        RETURN {}
```

### index_in_dual_memory - Индексация в dual memory
```pseudo
FUNCTION index_in_dual_memory(graph_data, source_file):
    TRY:
        index = NEW DualMemoryIndex()
        
        # Создать текстовое описание
        description = BUILD description with:
            - function names
            - node count, edge count, density
            - LLM analysis text
        
        # Создать chunk
        chunk = NEW ContentChunk(
            chunk_id = "call_graph_{source_file}",
            content = description,
            metadata = {type: "call_graph", ...}
        )
        
        # Сгенерировать embedding
        embedding = index.embedder.generate([description])[0]
        
        # Добавить в индекс
        index_data = index._load_index("description")
        REMOVE old entry IF EXISTS
        APPEND chunk TO index_data.chunks
        APPEND embedding TO index_data.embeddings
        index._save_index("description", index_data)
        
        RETURN True
    
    CATCH Exception:
        LOG WARNING "Dual memory indexing failed"
        RETURN False
```

### should_regenerate - Проверка необходимости регенерации
```pseudo
FUNCTION should_regenerate(source_path, output_path):
    IF NOT output_path.exists():
        RETURN True
    
    source_mtime = source_path.stat().st_mtime
    output_mtime = output_path.stat().st_mtime
    
    IF source_mtime > output_mtime:
        LOG INFO "Source file modified, will regenerate"
        RETURN True
    
    RETURN False
```

## CLI INTERFACE (обновлен)
```pseudo
ARGUMENTS:
    --file PATH         # Один файл для анализа
    --directory PATH    # Директория для анализа
    --all               # Весь проект
    --output PATH       # Выходной файл
    --format STRING     # Формат: mermaid|graphviz|json (default: mermaid)
    --max-nodes INT     # Максимум узлов для mermaid (default: 50)
    
    # Новые флаги (TICKET #04)
    --with-metrics      # Расчет метрик
    --llm-analyze       # LLM анализ (требует vLLM)
    --index-memory      # Индексация в dual memory
    --force             # Принудительная регенерация

ENTRY POINT main():
    PARSE arguments
    project_root = DETECT from script location
    
    generator = NEW CallGraphGenerator(project_root)
    
    # Проверка необходимости регенерации
    IF args.output AND NOT args.force:
        IF NOT generator.should_regenerate(source, output):
            PRINT "Call graph is up-to-date"
            RETURN
    
    # Анализ
    IF args.file:
        generator.analyze_file(args.file)
    ELIF args.directory:
        generator.analyze_directory(args.directory)
    ELSE:
        generator.analyze_project()
    
    generator.build_reverse_edges()
    
    # Генерация с опциональными улучшениями
    IF args.format == "json":
        data = generator.generate_json(include_metrics=args.with_metrics)
        
        IF args.llm_analyze:
            mermaid = generator.generate_mermaid(30)
            data.llm_analysis = generator.analyze_with_llm(mermaid)
        
        IF args.index_memory:
            generator.index_in_dual_memory(data, args.file)
        
        result = JSON.dumps(data)
    ELSE:
        result = generator.generate_mermaid() OR generate_graphviz()
    
    # Сохранение
    IF args.output:
        WRITE result TO args.output
    ELSE:
        PRINT result
```

## ЗАВИСИМОСТИ
- ast (стандартная библиотека)
- pathlib.Path
- dataclasses
- datetime.datetime
- json (для JSON вывода)
- argparse (для CLI)
- docs.utils.docs_logger.DocsLogger (изолированное логирование)
- docs.utils.docs_llm_backend.DocsLLMBackend (опционально, для LLM анализа)
- docs.utils.docs_dual_memory.DocsDualMemoryIndex (опционально, для индексации)

<!--/TAG:pseudo_generate_call_graph-->
