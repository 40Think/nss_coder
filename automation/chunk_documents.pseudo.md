---
description: "Hierarchical multi-layer document chunking for RAG systems"
date: 2025-12-11
source_file: chunk_documents.py
tags: automation, chunking, RAG, hierarchical, semantic
version: 2.0
---

# chunk_documents.py - Псевдокод (v2.0 - Hierarchical)

<!--TAG:pseudo_chunk_documents-->

## PURPOSE
Splits markdown documentation into hierarchical semantic chunks for RAG systems.
Implements 3-layer memory architecture adapted from cheap_memory.py:
- **L0 (CLAUSES)**: Fine-grained sentence/paragraph level for precise matching
- **L1 (SECTIONS)**: Header-based sections for topic-level retrieval  
- **L2 (DOCUMENTS)**: Full document for broad context

Preserves code blocks, tables, and lists intact.
Supports adaptive chunk sizing based on content complexity.

## АРХИТЕКТУРА (3 слоя)

```
┌─────────────────────────────────────────────┐
│              DOCUMENT (L2)                   │
│    Full document with frontmatter            │
├─────────────────────────────────────────────┤
│  SECTION (L1)  │  SECTION (L1)  │ SECTION...│
│  Header-based  │  Header-based  │           │
├────────────────┼────────────────┼───────────┤
│ CLS │ CLS│ CLS │ CLS │ CLS│ CLS │ CLS...    │
│ Fine-grained   │ Fine-grained   │           │
└────────────────┴────────────────┴───────────┘
     L0 CLAUSES       L0 CLAUSES
```

## СТРУКТУРЫ ДАННЫХ

### ChunkLayer (Enum)
```pseudo
ENUM ChunkLayer:
    CLAUSES = "clauses"      # L0: Предложения/абзацы
    SECTIONS = "sections"    # L1: Секции по заголовкам
    DOCUMENTS = "documents"  # L2: Полный документ
```

### HierarchicalChunk (dataclass)
```pseudo
DATACLASS HierarchicalChunk:
    content: STRING            # Содержимое чанка
    layer: ChunkLayer          # Уровень (CLAUSES/SECTIONS/DOCUMENTS)
    chunk_id: STRING           # Уникальный ID
    metadata: DICT             # Метаданные (file, section, etc)
    parent_id: STRING | None   # ID родительского чанка
    embedding_ready: BOOL      # Готов ли для эмбеддинга
```

### PreservedBlock (dataclass)
```pseudo
DATACLASS PreservedBlock:
    block_type: STRING    # 'code_block', 'table', 'list'
    start: INT            # Позиция начала в тексте
    end: INT              # Позиция конца
    content: STRING       # Полное содержимое блока
    language: STRING      # Для код-блоков: язык
```

## КЛАСС: HierarchicalDocumentChunker

### Инициализация
```pseudo
CLASS HierarchicalDocumentChunker:
    CONSTANTS:
        DEFAULT_CLAUSE_SIZE = 200     # Макс. символов для clause
        DEFAULT_SECTION_SIZE = 2000   # Макс. символов перед разбиением секции
        DEFAULT_OVERLAP = 50          # Перекрытие между clauses
    
    REGEX PATTERNS:
        HEADER_PATTERN = /^(#{1,6})\s+(.+)$/m
        CODE_FENCE_PATTERN = /```[\w]*\n.*?\n```/s
        TABLE_PATTERN = /(\|.+\|\n)+(\|[-:| ]+\|\n)(\|.+\|\n)+/
        SENTENCE_SPLIT = /(?<=[.!?])\s+/
    
    FUNCTION __init__(project_root, clause_size, section_size, overlap):
        self.project_root = project_root OR detect_project_root()
        self.clause_size = clause_size OR DEFAULT_CLAUSE_SIZE
        self.section_size = section_size OR DEFAULT_SECTION_SIZE
        self.overlap = overlap OR DEFAULT_OVERLAP
```

### chunk_document - Главный метод (3 слоя)
```pseudo
FUNCTION chunk_document(doc_file) -> Dict[ChunkLayer, List[HierarchicalChunk]]:
    # === Подготовка ===
    content = READ doc_file AS UTF-8
    frontmatter = CALL _extract_frontmatter(content)
    content_body = CALL _remove_frontmatter(content)
    rel_path = CALCULATE relative path from project_root
    
    # Инициализация контейнеров для каждого слоя
    chunks = {
        CLAUSES: [],
        SECTIONS: [],
        DOCUMENTS: []
    }
    
    # === Layer 2: DOCUMENTS (один чанк = весь документ) ===
    doc_chunk = CREATE HierarchicalChunk(
        content=content,
        layer=DOCUMENTS,
        chunk_id="doc_{file_stem}",
        metadata={file_path, file_name, frontmatter, char_count, word_count}
    )
    APPEND doc_chunk TO chunks[DOCUMENTS]
    
    # === Layer 1: SECTIONS (разбиение по заголовкам) ===
    sections = CALL _split_by_headers(content_body)
    
    FOR EACH section AT INDEX i:
        section_id = "sec_{file_stem}_{i}"
        
        section_chunk = CREATE HierarchicalChunk(
            content=section.content,
            layer=SECTIONS,
            chunk_id=section_id,
            metadata={header, header_level, parent_header, has_code, has_table},
            parent_id=doc_chunk.chunk_id
        )
        APPEND section_chunk TO chunks[SECTIONS]
        
        # === Layer 0: CLAUSES (мелкозернистые чанки) ===
        clauses = CALL _chunk_into_clauses(section.content, section.header)
        
        FOR EACH clause AT INDEX j:
            clause_id = "cls_{file_stem}_{i}_{j}"
            
            clause_chunk = CREATE HierarchicalChunk(
                content=clause,
                layer=CLAUSES,
                chunk_id=clause_id,
                metadata={header, clause_index, section_index},
                parent_id=section_id  # Иерархия: clause -> section -> doc
            )
            APPEND clause_chunk TO chunks[CLAUSES]
    
    RETURN chunks
```

## СОХРАНЕНИЕ СТРУКТУРЫ (Code blocks, Tables)

### _detect_preserved_blocks - Обнаружение блоков
```pseudo
FUNCTION _detect_preserved_blocks(content) -> List[PreservedBlock]:
    blocks = []
    
    # Найти все code fences (```...```)
    FOR EACH match OF CODE_FENCE_PATTERN IN content:
        language = EXTRACT language FROM first line
        APPEND PreservedBlock(
            type='code_block',
            start=match.start,
            end=match.end,
            content=match.text,
            language=language
        ) TO blocks
    
    # Найти все markdown таблицы
    FOR EACH match OF TABLE_PATTERN IN content:
        APPEND PreservedBlock(
            type='table',
            start=match.start,
            end=match.end,
            content=match.text
        ) TO blocks
    
    SORT blocks BY start position
    RETURN blocks
```

### _chunk_with_preservation - Разбиение с сохранением
```pseudo
FUNCTION _chunk_with_preservation(text, preserved_blocks) -> List[STRING]:
    IF preserved_blocks IS EMPTY:
        RETURN CALL _split_into_sentences(text)
    
    chunks = []
    current_pos = 0
    
    FOR EACH block IN preserved_blocks:
        # Разбить текст ДО этого блока обычным способом
        before_text = text[current_pos : block.start]
        IF before_text HAS CONTENT:
            EXTEND chunks WITH CALL _split_into_sentences(before_text)
        
        # Добавить preserved block КАК ЕСТЬ (не разбивать!)
        APPEND block.content TO chunks
        
        current_pos = block.end
    
    # Разбить остаток текста
    remaining = text[current_pos:]
    IF remaining HAS CONTENT:
        EXTEND chunks WITH CALL _split_into_sentences(remaining)
    
    RETURN chunks
```

## АДАПТИВНЫЙ РАЗМЕР ЧАНКОВ

### _calculate_adaptive_size
```pseudo
FUNCTION _calculate_adaptive_size(text) -> INT:
    # Код/таблицы = большие чанки (800)
    IF '```' IN text OR ('|' IN text AND '---' IN text):
        RETURN 800
    
    # Проверить плотность текста
    density = words_count / char_count
    
    IF density > 0.2:     # Плотный текст
        RETURN 300
    ELSE IF density > 0.15:  # Нормальный
        RETURN 400
    ELSE:                    # Разреженный (код-подобный)
        RETURN 500
```

## РАЗБИЕНИЕ НА CLAUSES

### _chunk_into_clauses
```pseudo
FUNCTION _chunk_into_clauses(text, header) -> List[STRING]:
    # 1. Обнаружить preserved blocks
    preserved = CALL _detect_preserved_blocks(text)
    
    # 2. Разбить с сохранением блоков
    raw_chunks = CALL _chunk_with_preservation(text, preserved)
    
    # 3. Объединить мелкие, разбить крупные
    final_chunks = []
    current = ""
    
    FOR EACH chunk IN raw_chunks:
        IF chunk IS preserved_block:
            IF current NOT EMPTY:
                APPEND current TO final_chunks
                current = ""
            APPEND chunk TO final_chunks
            CONTINUE
        
        max_size = CALL _calculate_adaptive_size(chunk)
        
        IF LENGTH(current + chunk) <= max_size:
            current = current + "\n\n" + chunk
        ELSE:
            IF current NOT EMPTY:
                APPEND current TO final_chunks
            
            IF LENGTH(chunk) > max_size:
                EXTEND final_chunks WITH CALL _split_large_chunk(chunk, max_size)
                current = ""
            ELSE:
                current = chunk
    
    IF current NOT EMPTY:
        APPEND current TO final_chunks
    
    RETURN final_chunks
```

## BACKWARD COMPATIBILITY

### SemanticChunker (обёртка)
```pseudo
CLASS SemanticChunker:
    """Backward compatible wrapper для старого API."""
    
    FUNCTION __init__(max_chunk_size=1000, overlap=200):
        self._hierarchical = HierarchicalDocumentChunker(
            clause_size = max_chunk_size / 5,
            section_size = max_chunk_size,
            overlap = overlap
        )
    
    FUNCTION chunk_markdown(file_path) -> List[HierarchicalChunk]:
        chunks = self._hierarchical.chunk_document(file_path)
        # Возвращаем SECTIONS для совместимости
        RETURN chunks[SECTIONS]
```

## CLI INTERFACE

```pseudo
FUNCTION main():
    PARSE arguments:
        --input-dir (default: 'docs')
        --output-dir (default: 'docs/memory/chunks')
        --file (single file mode)
        --legacy (use old single-layer mode)
        --clause-size (default: 200)
        --section-size (default: 2000)
    
    IF --file SPECIFIED:
        # Single file mode
        chunks = chunker.chunk_document(file_path)
        PRINT chunks by layer
    ELSE:
        # Directory mode
        chunk_directory(input_dir, output_dir, hierarchical=NOT legacy)
```

## ВЫХОДНЫЕ ФАЙЛЫ

```
docs/memory/chunks/
├── {file}_chunks.json           # Все 3 слоя для файла
├── chunks_index_clauses.json    # Индекс L0
├── chunks_index_sections.json   # Индекс L1
└── chunks_index_documents.json  # Индекс L2
```

## ЗАВИСИМОСТИ

- **pathlib**: Path operations
- **dataclasses**: Data structures
- **enum**: ChunkLayer enum
- **hashlib**: Chunk ID generation
- **yaml**: Frontmatter parsing
- **re**: Regex for structure detection
- **docs.utils.docs_logger**: Isolated DocsLogger for paranoid logging

## СВЯЗЬ С ДРУГИМИ МОДУЛЯМИ

- **cheap_memory.py**: Layer architecture adapted from there
- **embedding_client.py**: Adaptive sizing pattern adapted from there
- **index_project.py**: Uses our chunks for indexing
- **dual_memory.py**: Stores chunk embeddings

<!--/TAG:pseudo_chunk_documents-->
