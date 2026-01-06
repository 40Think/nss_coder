---
description: "Строит векторные эмбеддинги и knowledge graph для AI memory system"
date: 2025-12-09
source_file: index_project.py
tags: automation, indexing, embeddings, knowledge-graph
---

# index_project.py - Псевдокод

<!--TAG:pseudo_index_project-->

## PURPOSE
Строит систему AI-памяти проекта, включающую:
- Векторные эмбеддинги для семантического поиска
- Knowledge graph связей между сущностями кода
- Быстрые индексы для lookup-операций

## СТРУКТУРЫ ДАННЫХ

### CodeEntity (dataclass)
```pseudo
DATACLASS CodeEntity:
    id: STRING                  # Уникальный ID
    type: STRING                # "file" | "class" | "function"
    name: STRING                # Имя сущности
    file_path: STRING           # Путь к файлу
    line_number: INT            # Номер строки
    content: STRING             # Содержимое (код/docstring)
    embedding: LIST[FLOAT]      # Векторный эмбеддинг (опционально)
    metadata: DICT              # Дополнительные метаданные
```

### Relationship (dataclass)
```pseudo
DATACLASS Relationship:
    source_id: STRING           # ID исходной сущности
    target_id: STRING           # ID целевой сущности
    type: STRING                # "imports" | "calls" | "inherits" | "uses"
    metadata: DICT              # Дополнительные данные
```

## КЛАСС: ProjectIndexer

### Инициализация
```pseudo
CLASS ProjectIndexer:
    FUNCTION __init__(project_root):
        self.project_root = project_root
        self.memory_dir = project_root / 'docs' / 'memory'
        self.embeddings_dir = self.memory_dir / 'embeddings'
        self.graph_dir = self.memory_dir / 'knowledge_graph'
        self.indexes_dir = self.memory_dir / 'indexes'  # ← ADDED (was missing)
        self.entities: DICT[STRING, CodeEntity] = {}  # ← FIXED (was LIST)
        self.relationships: LIST[Relationship] = []
        
        # Создать директории если нет
        CREATE self.embeddings_dir IF NOT EXISTS
        CREATE self.graph_dir IF NOT EXISTS
        CREATE self.indexes_dir IF NOT EXISTS  # ← ADDED
```

### build_embeddings - Построение эмбеддингов
```pseudo
FUNCTION build_embeddings():
    LOG "Building embeddings..."
    
    # Шаг 1: Собрать документы для эмбеддинга
    chunks = []
    
    # Обработать документацию
    FOR EACH md_file IN GLOB(self.project_root / 'docs', "**/*.md"):
        content = READ md_file
        chunks.APPEND({
            "id": GENERATE_ID(md_file, "doc"),
            "content": content,
            "type": "documentation",
            "file_path": str(md_file)
        })
    
    # Обработать Python-код
    FOR EACH py_file IN GLOB(self.project_root / 'processing', "*.py"):
        entities = CALL _extract_code_entities(py_file)
        FOR EACH entity IN entities:
            chunks.APPEND({
                "id": entity.id,
                "content": entity.content,
                "type": entity.type,
                "file_path": entity.file_path
            })
            self.entities.APPEND(entity)
    
    FOR EACH py_file IN GLOB(self.project_root / 'utils', "*.py"):
        entities = CALL _extract_code_entities(py_file)
        # ... аналогично
    
    # Шаг 2: Генерация эмбеддингов (placeholder)
    embeddings = CALL _generate_embeddings_placeholder(chunks)
    
    # Шаг 3: Сохранение
    embeddings_file = self.embeddings_dir / "project_embeddings.json"
    WRITE {
        "count": LENGTH(chunks),
        "chunks": chunks,
        "embeddings_generated": False,  # Placeholder flag
        "timestamp": CURRENT_TIME
    } AS JSON TO embeddings_file
    
    LOG "Prepared {LENGTH(chunks)} chunks for embedding"
```

### build_knowledge_graph - Построение knowledge graph
```pseudo
FUNCTION build_knowledge_graph():
    LOG "Building knowledge graph..."
    
    # Шаг 1: Загрузить dependency files
    deps_dir = self.memory_dir / 'dependencies'
    
    IF deps_dir.exists():
        FOR EACH dep_file IN GLOB(deps_dir, "*_dependencies.json"):
            CALL _process_dependency_file(dep_file)
    
    # Шаг 2: Построить граф из entities и relationships
    graph = {
        "nodes": [],
        "edges": []
    }
    
    # Добавить узлы
    FOR EACH entity IN self.entities:
        graph.nodes.APPEND({
            "id": entity.id,
            "type": entity.type,
            "name": entity.name,
            "file": entity.file_path,
            "line": entity.line_number
        })
    
    # Добавить рёбра
    FOR EACH rel IN self.relationships:
        graph.edges.APPEND({
            "source": rel.source_id,
            "target": rel.target_id,
            "type": rel.type
        })
    
    # Шаг 3: Сохранение
    graph_file = self.graph_dir / "code_graph.json"  # ← FIXED (was knowledge_graph.json)
    WRITE graph AS JSON TO graph_file
    
    LOG "Knowledge graph: {LENGTH(graph.nodes)} nodes, {LENGTH(graph.edges)} edges"
```

### build_indexes - Построение lookup-индексов
```pseudo
FUNCTION build_indexes():
    LOG "Building indexes..."
    
    indexes = {
        "by_type": {},      # type -> [entity_ids]
        "by_file": {},      # file_path -> [entity_ids]
        "by_name": {},      # name -> entity_id
        "relationships_from": {},  # entity_id -> [relationships]
        "relationships_to": {}     # entity_id -> [relationships]
    }
    
    # Индекс по типу
    FOR EACH entity IN self.entities:
        IF entity.type NOT IN indexes.by_type:
            indexes.by_type[entity.type] = []
        indexes.by_type[entity.type].APPEND(entity.id)
    
    # Индекс по файлу
    FOR EACH entity IN self.entities:
        IF entity.file_path NOT IN indexes.by_file:
            indexes.by_file[entity.file_path] = []
        indexes.by_file[entity.file_path].APPEND(entity.id)
    
    # Индекс по имени
    FOR EACH entity IN self.entities:
        indexes.by_name[entity.name] = entity.id
    
    # Индексы связей
    FOR EACH rel IN self.relationships:
        IF rel.source_id NOT IN indexes.relationships_from:
            indexes.relationships_from[rel.source_id] = []
        indexes.relationships_from[rel.source_id].APPEND(rel)
        
        IF rel.target_id NOT IN indexes.relationships_to:
            indexes.relationships_to[rel.target_id] = []
        indexes.relationships_to[rel.target_id].APPEND(rel)
    
    # Сохранение
    index_file = self.memory_dir / "indexes" / "lookup_indexes.json"  # ← FIXED (was indexes.json)
    WRITE indexes AS JSON TO index_file
    
    LOG "Indexes built successfully"
```

### _extract_code_entities - Извлечение сущностей из кода
```pseudo
FUNCTION _extract_code_entities(file_path):
    entities = []
    
    source = READ file_path
    TRY:
        tree = ast.parse(source)
    CATCH:
        RETURN entities
    
    # Сущность файла
    file_entity = NEW CodeEntity(
        id = CALL _generate_id(file_path, file_path.name, "file"),
        type = "file",
        name = file_path.name,
        file_path = str(file_path),
        line_number = 1,
        content = EXTRACT docstring FROM tree
    )
    entities.APPEND(file_entity)
    
    # Классы и функции
    FOR EACH node IN ast.walk(tree):
        IF node IS ast.ClassDef:
            class_entity = NEW CodeEntity(
                id = CALL _generate_id(file_path, node.name, "class"),
                type = "class",
                name = node.name,
                file_path = str(file_path),
                line_number = node.lineno,
                content = ast.get_docstring(node) OR ""
            )
            entities.APPEND(class_entity)
        
        IF node IS ast.FunctionDef:
            func_entity = NEW CodeEntity(
                id = CALL _generate_id(file_path, node.name, "function"),
                type = "function",
                name = node.name,
                file_path = str(file_path),
                line_number = node.lineno,
                content = ast.get_docstring(node) OR ""
            )
            entities.APPEND(func_entity)
    
    RETURN entities
```

### _process_dependency_file - Обработка dependency JSON
```pseudo
FUNCTION _process_dependency_file(dep_file):
    deps = READ dep_file AS JSON
    
    source_file = deps.file_path
    source_id = CALL _generate_id(source_file, Path(source_file).name, "file")
    
    # Создать relationships из imports
    FOR EACH imp IN deps.imports:
        target_module = imp.module
        rel = NEW Relationship(
            source_id = source_id,
            target_id = "module::" + target_module,
            type = "imports"
        )
        self.relationships.APPEND(rel)
    
    # Создать relationships из function_calls
    FOR EACH call IN deps.function_calls:
        rel = NEW Relationship(
            source_id = source_id,
            target_id = "func::" + call.name,
            type = "calls"
        )
        self.relationships.APPEND(rel)
    
    # Создать relationships из class_hierarchy
    FOR EACH cls IN deps.class_hierarchy:
        FOR EACH base IN cls.bases:
            rel = NEW Relationship(
                source_id = "class::" + cls.name,
                target_id = "class::" + base,
                type = "inherits"
            )
            self.relationships.APPEND(rel)
```

### _generate_id - Генерация уникального ID
```pseudo
FUNCTION _generate_id(file_path, name, entity_type):
    unique_str = "{file_path}::{entity_type}::{name}"
    hash_val = MD5_HASH(unique_str)[:16]  # ← FIXED (was [:12])
    RETURN "{entity_type}_{hash_val}"
```

### _generate_embeddings_real - Реальная генерация эмбеддингов (NEW v2025-12-11)
```pseudo
FUNCTION _generate_embeddings_real(chunks) -> LIST[LIST[FLOAT]]:
    """Генерирует реальные эмбеддинги используя sentence-transformers или fallback."""
    
    # Проверка на пустой список
    IF chunks IS EMPTY:
        RETURN []
    
    # Извлечь текстовое содержимое из каждого chunk
    texts = [c.get('content', '') FOR c IN chunks]
    
    # Попытка 1: sentence-transformers (предпочтительный метод)
    TRY:
        model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim embeddings
        embeddings = model.encode(texts, show_progress_bar=True)
        LOG "✓ Generated {LENGTH(embeddings)} embeddings (dim={embeddings[0].length})"
        RETURN embeddings.tolist()  # Convert numpy to list
    CATCH ImportError:
        LOG WARNING "sentence-transformers not installed, trying vLLM"
    CATCH Exception AS e:
        LOG WARNING "sentence-transformers failed: {e}"
    
    # Попытка 2: vLLM embedding endpoint (если сконфигурирован)
    TRY:
        embed_model = docs_config.get("VLLM_MODEL_PATH_EMBEDDING", "")
        IF embed_model AND "path/to/models" NOT IN embed_model:
            LOG "vLLM embedding model configured: {embed_model}"
            # vLLM integration placeholder - будет реализовано позже
            LOG WARNING "vLLM embedding not yet implemented, using fallback"
    CATCH Exception AS e:
        LOG WARNING "vLLM check failed: {e}"
    
    # Fallback: детерминированные placeholder эмбеддинги
    LOG WARNING "Using placeholder embeddings (install sentence-transformers for real embeddings)"
    RETURN _generate_embeddings_placeholder(chunks)
```

### _generate_embeddings_placeholder - Placeholder для эмбеддингов
```pseudo
FUNCTION _generate_embeddings_placeholder(chunks) -> LIST[LIST[FLOAT]]:
    """Fallback: детерминированные placeholder эмбеддинги на основе хэша контента."""
    
    embeddings = []
    
    FOR EACH chunk IN chunks:
        # Использовать MD5 хэш для детерминированности (одинаковый текст = одинаковый эмбеддинг)
        content = chunk.get('content', '')
        seed = INT(MD5_HASH(content)[:8], base=16)  # Первые 8 символов хэша как seed
        
        # Генерировать псевдослучайный вектор с фиксированным seed
        RANDOM.seed(seed)
        embedding = [RANDOM.random() FOR _ IN RANGE(384)]  # 384-dim для совместимости с MiniLM
        
        embeddings.APPEND(embedding)
    
    RETURN embeddings
```

### generate_human_readable_index - Генерация PROJECT_INDEX.md (NEW v2025-12-11)
```pseudo
FUNCTION generate_human_readable_index():
    LOG "Generating human-readable index..."
    
    output = []
    output.APPEND "# Project Index"
    output.APPEND "**Updated**: {CURRENT_TIME}"
    output.APPEND "**Entities**: {LENGTH(entities)} | **Relationships**: {LENGTH(relationships)}"
    
    # Шаг 1: Группировка сущностей по файлам
    files_index = GROUP entities BY file_path
    
    # Шаг 2: File Structure section
    output.APPEND "## File Structure"
    FOR EACH file_path IN SORTED(files_index.keys()):
        output.APPEND "### [{basename}](file:///{full_path})"
        FOR EACH entity IN SORTED(entities, BY line_number):
            icon = "🏛️" IF class ELSE "⚙️" IF function ELSE "📄"
            output.APPEND "- {icon} **{type}** `{name}` (line {line})"
    
    # Шаг 3: Mermaid Dependency Graph
    IF relationships NOT EMPTY:
        output.APPEND "## Dependency Graph"
        output.APPEND "```mermaid"
        output.APPEND "graph TD"
        FOR EACH rel IN relationships[:50]:  # Limit for readability
            output.APPEND "    {source[:8]} -->|{type}| {target[:8]}"
        output.APPEND "```"
    
    # Шаг 4: Entity Summary
    output.APPEND "## Entity Summary"
    type_counts = COUNT entities BY type
    FOR EACH type, count IN type_counts:
        output.APPEND "- **{type}**: {count}"
    
    # Сохранение
    WRITE output TO memory_dir / "PROJECT_INDEX.md"
    LOG "✓ Human-readable index saved"
```

## КЛАСС: IncrementalIndexer (NEW v2025-12-11)
```pseudo
CLASS IncrementalIndexer:
    """Кэширование хэшей файлов для инкрементальной индексации."""
    
    FUNCTION __init__(memory_dir):
        self.cache_file = memory_dir / ".index_cache.json"
        self.file_hashes = _load_cache()
        self.changed = False
    
    FUNCTION _load_cache() -> DICT:
        IF cache_file EXISTS:
            RETURN JSON.load(cache_file)
        RETURN {}
    
    FUNCTION save_cache():
        IF self.changed:
            WRITE file_hashes AS JSON TO cache_file
            LOG "✓ Cache saved: {LENGTH(file_hashes)} file hashes"
    
    FUNCTION get_changed_files(files: LIST[Path]) -> TUPLE[LIST, LIST]:
        """Получить списки изменённых и неизменённых файлов.
        
        Returns:
            Tuple of (changed_files, unchanged_files)
        """
        changed = []
        unchanged = []
        
        FOR EACH file IN files:
            current_hash = MD5(file.read_bytes())
            cached_hash = file_hashes.GET(str(file))
            
            IF cached_hash != current_hash:
                changed.APPEND(file)
                file_hashes[str(file)] = current_hash
                self.changed = True
            ELSE:
                unchanged.APPEND(file)
        
        RETURN (changed, unchanged)
    
    FUNCTION mark_file_indexed(file: Path):
        """Отметить файл как проиндексированный с его текущим хэшем."""
        TRY:
            current_hash = MD5(file.read_bytes())
            file_hashes[str(file)] = current_hash
            self.changed = True
        CATCH Exception:
            PASS  # Игнорировать ошибки чтения файла
```

## CLI INTERFACE (UPDATED v2025-12-11)
```pseudo
ARGUMENTS:
    --build-embeddings      # Построить эмбеддинги
    --build-knowledge-graph # Построить knowledge graph
    --build-indexes         # Построить lookup индексы
    --build-human-index     # Сгенерировать PROJECT_INDEX.md (NEW)
    --build-all             # Всё вместе
    --incremental           # Только изменённые файлы (NEW)

ENTRY POINT main():
    PARSE arguments
    project_root = DETECT from script location
    
    indexer = NEW ProjectIndexer(project_root)
    
    IF args.incremental:
        LOG "📦 Incremental mode enabled"
    
    IF args.build_all OR args.build_embeddings:
        indexer.build_embeddings()
    
    IF args.build_all OR args.build_knowledge_graph:
        indexer.build_knowledge_graph()
    
    IF args.build_all OR args.build_indexes:
        indexer.build_indexes()
    
    IF args.build_all OR args.build_human_index:
        indexer.generate_human_readable_index()
    
    LOG "✓ Indexing complete!"
```

## ЗАВИСИМОСТИ
- ast (стандартная библиотека)
- pathlib.Path
- dataclasses
- hashlib
- datetime
- sentence_transformers (опционально, для реальных эмбеддингов)
- docs.utils.docs_logger.DocsLogger  # ← FIXED (was utils.paranoid_logger)
- docs.utils.docs_config.docs_config  # ← ADDED

<!--/TAG:pseudo_index_project-->

