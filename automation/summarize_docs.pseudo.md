# Pseudocode: summarize_docs.py v2.0

**Version**: 2.0  
**Last Updated**: 2025-12-13  
**Python Implementation**: [summarize_docs.py](file:///home/user/Telegram_Parser/docs/automation/summarize_docs.py)

---

## Overview

Multi-level documentation summarizer with hierarchical chunking integration and optional LLM backend support.

**Key Features**:
- 4 detail levels (TLDR/Brief/Detailed/Full)
- Hierarchical chunking via `HierarchicalDocumentChunker`
- Optional vLLM integration for high-quality summaries
- Async processing support
- Backward compatible with v1.0 simple mode

---

## Dependencies

```
IMPORTS:
    - os, re, asyncio
    - pathlib.Path
    - typing: List, Dict, Optional, Tuple
    - dataclasses: dataclass, field
    - collections.defaultdict
    - docs.utils.docs_logger.DocsLogger
    - docs.utils.docs_llm_backend.DocsLLMBackend
    - docs.automation.chunk_documents: HierarchicalDocumentChunker, ChunkLayer, HierarchicalChunk

LOGGER = DocsLogger("summarize_docs")
```

---

## Data Structures

### Summary (Backward Compatible)
```
DATACLASS Summary:
    original_file: STRING
    original_length: INTEGER
    summary_length: INTEGER
    compression_ratio: FLOAT
    summary: STRING
```

### MultiLevelSummary (New in v2.0)
```
DATACLASS MultiLevelSummary:
    tldr: STRING                           # 1-2 sentences, <100 words
    brief: STRING                          # 2-3 paragraphs, <300 words
    detailed: STRING                       # Full summary, <1000 words
    full: STRING                           # Complete hierarchical summary
    hierarchy_uids: LIST[STRING]           # UIDs of intermediate summaries
    compression_ratios: DICT[STRING, FLOAT] # Ratio for each level
    original_file: STRING
    original_length: INTEGER
```

---

## Class: DocumentSummarizer

### Constructor
```
FUNCTION __init__(project_root: Path = None):
    SET self.project_root = project_root OR Path(__file__).parent.parent.parent
    SET self.llm_backend = null
    CALL self._init_llm_backend()
```

### LLM Backend Initialization
```
FUNCTION _init_llm_backend():
    """Initialize LLM backend (optional, for --use-llm mode)."""
    
    TRY:
        SET self.llm_backend = DocsLLMBackend()
        
        IF self.llm_backend.is_available():
            LOG INFO "✅ LLM backend available for high-quality summaries"
        ELSE:
            LOG WARNING "⚠️ LLM backend not available, will use extractive mode"
            SET self.llm_backend = null
    
    CATCH Exception as e:
        LOG WARNING "⚠️ LLM backend init failed: {e}"
        SET self.llm_backend = null
```

---

### Simple Summarization (v1.0 Backward Compatible)
```
FUNCTION summarize(file_path: Path, max_length: INTEGER = 1000) -> Summary:
    """Summarize a documentation file (simple mode)."""
    
    # Read file
    READ content FROM file_path
    SET original_length = LENGTH(content)
    
    # Extract structure
    SET structure = CALL self._extract_structure(content)
    
    # Generate summary
    CREATE summary_parts = []
    
    # Add title
    IF structure['title']:
        APPEND "# {structure['title']}\n" TO summary_parts
    
    # Add overview
    IF structure['overview']:
        APPEND "## Overview\n" TO summary_parts
        APPEND "{structure['overview'][:200]}...\n" TO summary_parts
    
    # Add section summaries
    IF structure['sections']:
        APPEND "## Sections\n" TO summary_parts
        FOR EACH section IN structure['sections'][:10]:  # Limit to 10
            APPEND "### {section['heading']}" TO summary_parts
            SET first_sentence = section['content'].split('.')[0][:100]
            APPEND "{first_sentence}...\n" TO summary_parts
    
    # Add key points
    IF structure['key_points']:
        APPEND "## Key Points\n" TO summary_parts
        FOR EACH point IN structure['key_points'][:5]:
            APPEND "- {point}" TO summary_parts
    
    # Combine summary
    SET summary_text = JOIN summary_parts WITH '\n'
    
    # Trim to max length if needed
    IF LENGTH(summary_text) > max_length:
        SET summary_text = summary_text[:max_length] + "\n\n... (truncated)"
    
    RETURN Summary(
        original_file=STRING(file_path),
        original_length=original_length,
        summary_length=LENGTH(summary_text),
        compression_ratio=LENGTH(summary_text) / original_length,
        summary=summary_text
    )
```

---

### Structure Extraction
```
FUNCTION _extract_structure(content: STRING) -> DICT:
    """Extract document structure (title, sections, key points)."""
    
    CREATE structure = {
        'title': null,
        'overview': null,
        'sections': [],
        'key_points': []
    }
    
    SET lines = SPLIT content BY '\n'
    
    # Extract title (first # heading)
    FOR EACH line IN lines:
        IF line STARTS WITH '# ':
            SET structure['title'] = line[2:].strip()
            BREAK
    
    # Extract sections
    SET current_section = null
    FOR EACH line IN lines:
        # Heading
        IF line STARTS WITH '##':
            IF current_section:
                APPEND current_section TO structure['sections']
            
            SET heading_level = LENGTH(REGEX_MATCH(r'^#+', line))
            SET heading_text = line[heading_level:].strip()
            
            SET current_section = {
                'level': heading_level,
                'heading': heading_text,
                'content': ''
            }
        
        # Content
        ELSE IF current_section:
            APPEND line + '\n' TO current_section['content']
    
    # Add last section
    IF current_section:
        APPEND current_section TO structure['sections']
    
    # Extract overview (first section or first paragraph)
    IF structure['sections']:
        SET first_section = structure['sections'][0]
        IF first_section['heading'].lower() IN ['overview', 'introduction', 'purpose']:
            SET structure['overview'] = first_section['content']
        ELSE:
            SET structure['overview'] = first_section['content'][:500]
    
    # Extract key points (bullet points)
    FOR EACH line IN lines:
        IF line STARTS WITH '- ' OR line STARTS WITH '* ':
            SET point = line[2:].strip()
            IF LENGTH(point) > 10:  # Skip very short points
                APPEND point TO structure['key_points']
    
    RETURN structure
```

---

### Multi-Level Summarization (v2.0 New)
```
ASYNC FUNCTION summarize_multi_level_async(
    file_path: Path,
    use_llm: BOOLEAN = false,
    save_hierarchy: BOOLEAN = false
) -> MultiLevelSummary:
    """Generate multi-level summary using hierarchical chunking."""
    
    LOG INFO "Generating multi-level summary for: {file_path}"
    
    # 1. Chunk document using existing infrastructure
    CREATE chunker = HierarchicalDocumentChunker(
        project_root=self.project_root,
        clause_size=200,      # Tokens
        section_size=2000,
        overlap=50
    )
    SET chunks = chunker.chunk_document(file_path)
    
    # 2. Get document chunk for metadata
    SET doc_chunk = chunks[ChunkLayer.DOCUMENTS][0]
    SET original_length = LENGTH(doc_chunk.content)
    
    # 3. Generate TLDR (from DOCUMENTS layer)
    LOG INFO "Generating TLDR..."
    SET tldr = CALL self._generate_tldr(doc_chunk.content, use_llm)
    
    # 4. Generate Brief (from SECTIONS layer)
    LOG INFO "Generating Brief..."
    SET section_chunks = chunks[ChunkLayer.SECTIONS]
    SET brief = AWAIT self._generate_brief_async(section_chunks, use_llm)
    
    # 5. Generate Detailed (from CLAUSES layer)
    LOG INFO "Generating Detailed..."
    SET clause_chunks = chunks[ChunkLayer.CLAUSES]
    SET detailed = AWAIT self._generate_detailed_async(clause_chunks, use_llm)
    
    # 6. Generate Full (hierarchical with UIDs)
    LOG INFO "Generating Full..."
    SET (full, hierarchy_uids) = AWAIT self._generate_full_async(
        chunks, use_llm, save_hierarchy, file_path
    )
    
    # 7. Calculate compression ratios
    CREATE ratios = {
        'tldr': LENGTH(tldr) / original_length IF original_length > 0 ELSE 0,
        'brief': LENGTH(brief) / original_length IF original_length > 0 ELSE 0,
        'detailed': LENGTH(detailed) / original_length IF original_length > 0 ELSE 0,
        'full': LENGTH(full) / original_length IF original_length > 0 ELSE 0
    }
    
    LOG INFO "Multi-level summary complete. Compression ratios: {ratios}"
    
    RETURN MultiLevelSummary(
        tldr=tldr,
        brief=brief,
        detailed=detailed,
        full=full,
        hierarchy_uids=hierarchy_uids,
        compression_ratios=ratios,
        original_file=STRING(file_path),
        original_length=original_length
    )
```

---

### TLDR Generation
```
FUNCTION _generate_tldr(content: STRING, use_llm: BOOLEAN) -> STRING:
    """Generate TLDR (1-2 sentences)."""
    
    IF use_llm AND self.llm_backend:
        # Use LLM for high-quality TLDR
        SET system_prompt = "You are a concise summarizer. Generate a 1-2 sentence summary."
        SET user_prompt = "Summarize in 1-2 sentences:\n\n{content[:2000]}"
        SET result = self.llm_backend.generate(system_prompt, user_prompt, max_tokens=100)
        
        IF result:
            RETURN result
    
    # Extractive fallback: first 2 sentences
    SET sentences = REGEX_SPLIT(r'[.!?]+\s+', content)
    SET tldr_sentences = [s.strip() FOR s IN sentences[:2] IF s.strip()]
    
    IF tldr_sentences:
        RETURN JOIN tldr_sentences WITH '. ' + '.'
    ELSE:
        RETURN "No content available."
```

---

### Brief Generation
```
ASYNC FUNCTION _generate_brief_async(
    section_chunks: LIST[HierarchicalChunk],
    use_llm: BOOLEAN
) -> STRING:
    """Generate Brief (2-3 paragraphs from sections)."""
    
    IF use_llm AND self.llm_backend:
        # Summarize top sections
        CREATE summaries = []
        
        FOR EACH chunk IN section_chunks[:10]:  # Limit to 10 sections
            SET header = chunk.metadata.get('header', 'Section')
            SET content_preview = chunk.content[:500]
            
            SET system_prompt = "You are a concise summarizer."
            SET user_prompt = "Summarize this section in 2-3 sentences:\n\n## {header}\n\n{content_preview}"
            SET result = self.llm_backend.generate(system_prompt, user_prompt, max_tokens=150)
            
            IF result:
                APPEND "**{header}**: {result}" TO summaries
        
        IF summaries:
            RETURN JOIN summaries WITH '\n\n'
        ELSE:
            RETURN "No sections available."
    
    ELSE:
        # Extractive: first sentence of each section
        CREATE summaries = []
        
        FOR EACH chunk IN section_chunks[:10]:
            SET header = chunk.metadata.get('header', 'Section')
            SET first_sentence = chunk.content.split('. ')[0] + '.'
            APPEND "**{header}**: {first_sentence}" TO summaries
        
        IF summaries:
            RETURN JOIN summaries WITH '\n\n'
        ELSE:
            RETURN "No sections available."
```

---

### Detailed Generation
```
ASYNC FUNCTION _generate_detailed_async(
    clause_chunks: LIST[HierarchicalChunk],
    use_llm: BOOLEAN
) -> STRING:
    """Generate Detailed summary (<1000 words)."""
    
    # Group clauses by section
    CREATE sections = defaultdict(list)
    FOR EACH chunk IN clause_chunks:
        SET header = chunk.metadata.get('header', 'Introduction')
        APPEND chunk.content TO sections[header]
    
    IF use_llm AND self.llm_backend:
        # Summarize each section comprehensively
        CREATE summaries = []
        
        FOR EACH (header, clauses) IN LIST(sections.items())[:15]:  # Limit to 15 sections
            SET combined = JOIN clauses[:5] WITH '\n\n'  # Limit to 5 clauses per section
            
            SET system_prompt = "You are a detailed summarizer."
            SET user_prompt = "Summarize this section comprehensively:\n\n## {header}\n\n{combined[:2000]}"
            SET result = self.llm_backend.generate(system_prompt, user_prompt, max_tokens=300)
            
            IF result:
                APPEND "## {header}\n\n{result}" TO summaries
        
        IF summaries:
            RETURN JOIN summaries WITH '\n\n'
        ELSE:
            RETURN "No content available."
    
    ELSE:
        # Extractive: combine clauses with headers
        CREATE summaries = []
        
        FOR EACH (header, clauses) IN LIST(sections.items())[:15]:
            SET combined = JOIN clauses[:5] WITH ' '
            SET combined = combined[:500]  # Limit length
            APPEND "## {header}\n\n{combined}..." TO summaries
        
        IF summaries:
            RETURN JOIN summaries WITH '\n\n'
        ELSE:
            RETURN "No content available."
```

---

### Full Generation
```
ASYNC FUNCTION _generate_full_async(
    chunks: DICT[ChunkLayer, LIST[HierarchicalChunk]],
    use_llm: BOOLEAN,
    save_hierarchy: BOOLEAN,
    file_path: Path
) -> TUPLE[STRING, LIST[STRING]]:
    """Generate Full hierarchical summary with UIDs."""
    
    SET doc_chunk = chunks[ChunkLayer.DOCUMENTS][0]
    SET section_chunks = chunks[ChunkLayer.SECTIONS]
    SET clause_chunks = chunks[ChunkLayer.CLAUSES]
    
    CREATE hierarchy_uids = []
    
    # Save intermediate summaries if requested
    IF save_hierarchy:
        FOR i, chunk IN ENUMERATE(clause_chunks):
            SET uid = CALL self._save_chunk_summary(chunk, file_path, 'clause', i)
            APPEND uid TO hierarchy_uids
        
        FOR i, chunk IN ENUMERATE(section_chunks):
            SET uid = CALL self._save_chunk_summary(chunk, file_path, 'section', i)
            APPEND uid TO hierarchy_uids
    
    # Build full summary
    CREATE full_parts = []
    APPEND "# {doc_chunk.metadata.get('file_name', 'Document')}\n" TO full_parts
    
    # Add TLDR
    SET tldr = CALL self._generate_tldr(doc_chunk.content, use_llm)
    APPEND "**TL;DR**: {tldr}\n" TO full_parts
    
    # Add section summaries
    FOR EACH section IN section_chunks:
        SET header = section.metadata['header']
        # Get clauses for this section
        SET section_clauses = [c FOR c IN clause_chunks IF c.parent_id == section.chunk_id]
        
        APPEND "## {header}\n" TO full_parts
        
        IF section_clauses:
            # Show first 3 clauses
            FOR EACH clause IN section_clauses[:3]:
                APPEND clause.content TO full_parts
            
            IF LENGTH(section_clauses) > 3:
                APPEND "\n... and {LENGTH(section_clauses) - 3} more clauses" TO full_parts
        ELSE:
            # Fallback to section content preview
            APPEND section.content[:500] + "..." TO full_parts
    
    # Add hierarchy section if saved
    IF save_hierarchy AND hierarchy_uids:
        APPEND "\n\n## Summary Hierarchy\n" TO full_parts
        APPEND "This summary was built from the following intermediate summaries:\n" TO full_parts
        APPEND JOIN ["- [[{uid}]]" FOR uid IN hierarchy_uids] WITH '\n' TO full_parts
    
    RETURN (JOIN full_parts WITH '\n\n', hierarchy_uids)
```

---

### Chunk Summary Saving
```
FUNCTION _save_chunk_summary(
    chunk: HierarchicalChunk,
    file_path: Path,
    layer: STRING,
    index: INTEGER
) -> STRING:
    """Save chunk summary and return UID."""
    
    SET uid = "chunk-{file_path.stem}-{layer}-{index:03d}"
    
    # Save to docs/automation/summaries/chunks/
    SET output_dir = Path(__file__).parent / "summaries" / "chunks" / file_path.stem
    CREATE DIRECTORY output_dir (parents=true, exist_ok=true)
    
    SET output_file = output_dir / "{layer}_{index:03d}.md"
    
    SET content = """---
uid: {uid}
type: chunk_summary
layer: {layer}
parent: {chunk.parent_id}
---

# Chunk Summary: {layer.capitalize()} {index + 1}

{chunk.content}

---
*Generated by summarize_docs.py*
"""
    
    # Atomic write
    SET temp_file = output_file.with_suffix('.tmp')
    
    TRY:
        OPEN temp_file FOR WRITE AS f:
            WRITE content TO f
            FLUSH f
            FSYNC f
        
        REPLACE temp_file WITH output_file  # Atomic operation
        LOG DEBUG "Saved chunk summary: {uid}"
    
    CATCH Exception as e:
        IF temp_file EXISTS:
            DELETE temp_file
        LOG ERROR "Failed to save chunk summary: {e}"
        RAISE e
    
    RETURN uid
```

---

## Main Function

```
FUNCTION main():
    """CLI entry point."""
    
    # Parse arguments
    CREATE parser = ArgumentParser(
        description='Summarize documentation files with multi-level detail',
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple mode (backward compatible)
  python3 summarize_docs.py --input GEMINI.MD --max-length 1000

  # Multi-level mode with all detail levels
  python3 summarize_docs.py --input GEMINI.MD --detail-level all

  # Use LLM for high-quality summaries
  python3 summarize_docs.py --input GEMINI.MD --detail-level all --use-llm

  # Save hierarchical structure
  python3 summarize_docs.py --input GEMINI.MD --detail-level full --save-hierarchy

  # Async mode for large documents
  python3 summarize_docs.py --input GEMINI.MD --detail-level all --async
        """
    )
    
    ADD ARGUMENT '--input' (type=STRING, required=true, help='Input file to summarize')
    ADD ARGUMENT '--output' (type=STRING, help='Output file for summary')
    ADD ARGUMENT '--max-length' (type=INTEGER, default=1000, help='Maximum summary length (simple mode only)')
    ADD ARGUMENT '--detail-level' (type=STRING, choices=['tldr', 'brief', 'detailed', 'full', 'all'], help='Level of detail for summary (enables multi-level mode)')
    ADD ARGUMENT '--use-llm' (action='store_true', help='Use LLM for high-quality summaries (requires vLLM server)')
    ADD ARGUMENT '--save-hierarchy' (action='store_true', help='Save intermediate summaries with UIDs')
    ADD ARGUMENT '--async' (dest='use_async', action='store_true', help='Use async processing (faster for large docs)')
    
    SET args = PARSE ARGUMENTS
    
    SET input_path = Path(args.input)
    
    IF NOT input_path EXISTS:
        LOG ERROR "Error: File not found: {input_path}"
        RETURN
    
    # Initialize summarizer
    CREATE summarizer = DocumentSummarizer()
    
    # Determine mode: multi-level or simple
    IF args.detail_level:
        # Multi-level mode
        LOG INFO "Multi-level summarization mode: {args.detail_level}"
        
        # Run async (both --async and non-async use asyncio.run)
        SET summary = ASYNCIO.RUN(summarizer.summarize_multi_level_async(
            input_path,
            use_llm=args.use_llm,
            save_hierarchy=args.save_hierarchy
        ))
        
        # Format output based on detail level
        IF args.detail_level == 'tldr':
            SET result_text = "# TL;DR\n\n{summary.tldr}"
        
        ELSE IF args.detail_level == 'brief':
            SET result_text = "# Brief Summary\n\n{summary.brief}"
        
        ELSE IF args.detail_level == 'detailed':
            SET result_text = "# Detailed Summary\n\n{summary.detailed}"
        
        ELSE IF args.detail_level == 'full':
            SET result_text = summary.full
        
        ELSE IF args.detail_level == 'all':
            SET result_text = """# Multi-Level Summary: {input_path.name}

## TL;DR
{summary.tldr}

---

## Brief
{summary.brief}

---

## Detailed
{summary.detailed}

---

## Full
{summary.full}

---

## Compression Ratios
- TL;DR: {summary.compression_ratios['tldr']:.1%}
- Brief: {summary.compression_ratios['brief']:.1%}
- Detailed: {summary.compression_ratios['detailed']:.1%}
- Full: {summary.compression_ratios['full']:.1%}

**Original length**: {summary.original_length} chars
"""
    
    ELSE:
        # Simple mode (backward compatible)
        LOG INFO "Simple summarization mode"
        SET summary = summarizer.summarize(input_path, args.max_length)
        
        # Format output
        CREATE output = []
        APPEND "Summary of: {summary.original_file}" TO output
        APPEND "Original length: {summary.original_length} chars" TO output
        APPEND "Summary length: {summary.summary_length} chars" TO output
        APPEND "Compression ratio: {summary.compression_ratio:.1%}" TO output
        APPEND "\n" + "=" * 60 + "\n" TO output
        APPEND summary.summary TO output
        
        SET result_text = JOIN output WITH '\n'
    
    # Save to file or print to stdout
    IF args.output:
        SET output_path = Path(args.output)
        WRITE result_text TO output_path
        LOG INFO "Summary saved to: {output_path}"
    ELSE:
        PRINT result_text


IF __name__ == '__main__':
    CALL main()
```

---

## Algorithm Summary

### Simple Mode (v1.0 Backward Compatible)
1. Read file content
2. Extract structure (title, sections, key points)
3. Generate summary by concatenating:
   - Title
   - Overview (first section or paragraph)
   - Section summaries (first sentence of each)
   - Key points (bullet list)
4. Truncate to max_length if needed
5. Return Summary dataclass

### Multi-Level Mode (v2.0)
1. **Chunk document** using HierarchicalDocumentChunker (3 layers: CLAUSES/SECTIONS/DOCUMENTS)
2. **Generate TLDR** from DOCUMENTS layer (1-2 sentences)
   - LLM mode: Use vLLM with max_tokens=100
   - Extractive mode: First 2 sentences
3. **Generate Brief** from SECTIONS layer (2-3 paragraphs)
   - LLM mode: Summarize top 10 sections (2-3 sentences each)
   - Extractive mode: First sentence of each section
4. **Generate Detailed** from CLAUSES layer (<1000 words)
   - Group clauses by section
   - LLM mode: Summarize each section comprehensively (max_tokens=300)
   - Extractive mode: Combine first 5 clauses per section
5. **Generate Full** hierarchical summary
   - Include TLDR, section summaries with clauses, hierarchy UIDs
   - Optionally save intermediate summaries (--save-hierarchy)
6. **Calculate compression ratios** for all 4 levels
7. Return MultiLevelSummary dataclass

---

## Key Differences from v1.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Detail Levels | 1 (simple) | 4 (TLDR/Brief/Detailed/Full) |
| Chunking | Character-based truncation | Token-based hierarchical (3 layers) |
| LLM Integration | None | Optional vLLM backend |
| Async Support | No | Yes (async methods) |
| Hierarchical Storage | No | Yes (--save-hierarchy flag) |
| Compression Ratios | Single | Per-level (4 ratios) |
| CLI Arguments | 3 | 7 |
| Lines of Code | 220 | 520 |

---

## Version History

- **v2.0** (2025-12-13): Multi-level summarization with hierarchical chunking and LLM integration
- **v1.0** (2025-12-10): Simple structural extractor with character-based truncation

---

**Synchronized with**: [summarize_docs.py](file:///home/user/Telegram_Parser/docs/automation/summarize_docs.py) v2.0  
**Last Verified**: 2025-12-13
