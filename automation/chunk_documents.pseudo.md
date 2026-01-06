---
description: "Hierarchical multi-layer document chunking for RAG systems"
date: 2025-12-11
source_file: chunk_documents.py
tags: automation, chunking, RAG, hierarchical, semantic
---

# chunk_documents.py - Pseudocode (v2.0 - Hierarchical)

<!--TAG:pseudo_chunk_documents-->

## PURPOSE
Splits markdown documentation into hierarchical semantic chunks for RAG systems.
Implements 3-layer memory architecture adapted from cheap_memory.py:
- **L0 (CLAUSES)**: Fine-grained sentence/paragraph level for precise matching
- **L1 (SECTIONS)**: Header-based sections for topic-level retrieval  
- **L2 (DOCUMENTS)**: Full document for broad context

Preserves code blocks, tables, and lists intact.
Supports adaptive chunk sizing based on content complexity.

## ARCHITECTURE (3 layers)

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

## DATA STRUCTURES

### ChunkLayer (Enum)
```pseudo
ENUM ChunkLayer:
    CLAUSES = "clauses"      # L0: Sentences/paragraphs
    SECTIONS = "sections"    # L1: Header-based sections
    DOCUMENTS = "documents"  # L2: Full document
```

### HierarchicalChunk (dataclass)
```pseudo
DATACLASS HierarchicalChunk:
    content: STRING            # Chunk content
    layer: ChunkLayer          # Layer (CLAUSES/SECTIONS/DOCUMENTS)
    chunk_id: STRING           # Unique ID
    metadata: DICT             # Metadata (file, section, etc)
    parent_id: STRING | None   # Parent chunk ID
    embedding_ready: BOOL      # Ready for embedding?
```

### PreservedBlock (dataclass)
```pseudo
DATACLASS PreservedBlock:
    block_type: STRING    # 'code_block', 'table', 'list'
    start: INT            # Start position in text
    end: INT              # End position
    content: STRING       # Full block content
    language: STRING      # For code blocks: language
```

## CLASS: HierarchicalDocumentChunker

### Initialization
```pseudo
CLASS HierarchicalDocumentChunker:
    CONSTANTS:
        DEFAULT_CLAUSE_SIZE = 200     # Max chars for clause
        DEFAULT_SECTION_SIZE = 2000   # Max chars before splitting section
        DEFAULT_OVERLAP = 50          # Overlap between clauses
    
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

### chunk_document - Main method (3 layers)
```pseudo
FUNCTION chunk_document(doc_file) -> Dict[ChunkLayer, List[HierarchicalChunk]]:
    # === Preparation ===
    content = READ doc_file AS UTF-8
    frontmatter = CALL _extract_frontmatter(content)
    content_body = CALL _remove_frontmatter(content)
    rel_path = CALCULATE relative path from project_root
    
    # Initialize containers for each layer
    chunks = {
        CLAUSES: [],
        SECTIONS: [],
        DOCUMENTS: []
    }
    
    # === Layer 2: DOCUMENTS (one chunk = full document) ===
    doc_chunk = CREATE HierarchicalChunk(
        content=content,
        layer=DOCUMENTS,
        chunk_id="doc_{file_stem}",
        metadata={file_path, file_name, frontmatter, char_count, word_count}
    )
    APPEND doc_chunk TO chunks[DOCUMENTS]
    
    # === Layer 1: SECTIONS (header-based split) ===
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
        
        # === Layer 0: CLAUSES (fine-grained chunks) ===
        clauses = CALL _chunk_into_clauses(section.content, section.header)
        
        FOR EACH clause AT INDEX j:
            clause_id = "cls_{file_stem}_{i}_{j}"
            
            clause_chunk = CREATE HierarchicalChunk(
                content=clause,
                layer=CLAUSES,
                chunk_id=clause_id,
                metadata={header, clause_index, section_index},
                parent_id=section_id  # Hierarchy: clause -> section -> doc
            )
            APPEND clause_chunk TO chunks[CLAUSES]
    
    RETURN chunks
```

## STRUCTURE PRESERVATION (Code blocks, Tables)

### _detect_preserved_blocks - Block discovery
```pseudo
FUNCTION _detect_preserved_blocks(content) -> List[PreservedBlock]:
    blocks = []
    
    # Find all code fences (```...```)
    FOR EACH match OF CODE_FENCE_PATTERN IN content:
        language = EXTRACT language FROM first line
        APPEND PreservedBlock(
            type='code_block',
            start=match.start,
            end=match.end,
            content=match.text,
            language=language
        ) TO blocks
    
    # Find all markdown tables
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

### _chunk_with_preservation - Splitting with preservation
```pseudo
FUNCTION _chunk_with_preservation(text, preserved_blocks) -> List[STRING]:
    IF preserved_blocks IS EMPTY:
        RETURN CALL _split_into_sentences(text)
    
    chunks = []
    current_pos = 0
    
    FOR EACH block IN preserved_blocks:
        # Split text BEFORE this block using regular method
        before_text = text[current_pos : block.start]
        IF before_text HAS CONTENT:
            EXTEND chunks WITH CALL _split_into_sentences(before_text)
        
        # Add preserved block AS IS (do not split!)
        APPEND block.content TO chunks
        
        current_pos = block.end
    
    # Split the remaining text
    remaining = text[current_pos:]
    IF remaining HAS CONTENT:
        EXTEND chunks WITH CALL _split_into_sentences(remaining)
    
    RETURN chunks
```

## ADAPTIVE CHUNK SIZING

### _calculate_adaptive_size
```pseudo
FUNCTION _calculate_adaptive_size(text) -> INT:
    # Code/tables = large chunks (800)
    IF '```' IN text OR ('|' IN text AND '---' IN text):
        RETURN 800
    
    # Check text density
    density = words_count / char_count
    
    IF density > 0.2:     # Dense text
        RETURN 300
    ELSE IF density > 0.15:  # Normal
        RETURN 400
    ELSE:                    # Sparse (code-like)
        RETURN 500
```

## SPLITTING INTO CLAUSES

### _chunk_into_clauses
```pseudo
FUNCTION _chunk_into_clauses(text, header) -> List[STRING]:
    # 1. Detect preserved blocks
    preserved = CALL _detect_preserved_blocks(text)
    
    # 2. Split preserving blocks
    raw_chunks = CALL _chunk_with_preservation(text, preserved)
    
    # 3. Merge small ones, split large ones
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

### SemanticChunker (wrapper)
```pseudo
CLASS SemanticChunker:
    """Backward compatible wrapper for old API."""
    
    FUNCTION __init__(max_chunk_size=1000, overlap=200):
        self._hierarchical = HierarchicalDocumentChunker(
            clause_size = max_chunk_size / 5,
            section_size = max_chunk_size,
            overlap = overlap
        )
    
    FUNCTION chunk_markdown(file_path) -> List[HierarchicalChunk]:
        chunks = self._hierarchical.chunk_document(file_path)
        # Return SECTIONS for compatibility
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

## OUTPUT FILES

```
docs/memory/chunks/
├── {file}_chunks.json           # All 3 layers for the file
├── chunks_index_clauses.json    # L0 index
├── chunks_index_sections.json   # L1 index
└── chunks_index_documents.json  # L2 index
```

## DEPENDENCIES

- **pathlib**: Path operations
- **dataclasses**: Data structures
- **enum**: ChunkLayer enum
- **hashlib**: Chunk ID generation
- **yaml**: Frontmatter parsing
- **re**: Regex for structure detection
- **docs.utils.docs_logger**: Isolated DocsLogger for paranoid logging

## RELATION TO OTHER MODULES

- **cheap_memory.py**: Layer architecture adapted from there
- **embedding_client.py**: Adaptive sizing pattern adapted from there
- **index_project.py**: Uses our chunks for indexing
- **dual_memory.py**: Stores chunk embeddings

<!--/TAG:pseudo_chunk_documents-->
