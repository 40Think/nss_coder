#!/usr/bin/env python3
"""
Documentation Summarizer - Summarize long documentation files

<!--TAG:tool_summarize_docs-->

PURPOSE:
    Summarize long documentation files for context compression.
    Uses hierarchical summarization strategy.
    Supports recursive summarization.

DOCUMENTATION:
    Spec: docs/specs/Automation_Tools_Spec.md
    Wiki: docs/wiki/09_Documentation_System.md

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger.DocsLogger (isolated logging for NSS-DOCS)
        - docs.utils.docs_llm_backend.DocsLLMBackend (optional, for --use-llm mode)
        - docs.automation.chunk_documents.HierarchicalDocumentChunker (3-layer hierarchical chunking)
    Config:
        - None (standalone script)
    Data:
        - Input: User-provided --input path (any markdown/text file)
        - Output: User-provided --output path or stdout
    External:
        - vLLM server (optional, for --use-llm mode, port 8000)

RECENT CHANGES:
    2025-12-13: v2.0 - Multi-level summarization implementation
                       - Added HierarchicalDocumentChunker integration (3-layer: CLAUSES/SECTIONS/DOCUMENTS)
                       - Added 4 detail levels (TLDR/Brief/Detailed/Full)
                       - Added LLM backend support (optional --use-llm flag)
                       - Added async processing support
                       - Added hierarchical UID storage (--save-hierarchy flag)
                       - Backward compatible: old --max-length mode still works
    2025-12-10: Migrated from utils.paranoid_logger to docs.utils.docs_logger for NSS-DOCS isolation
    2025-12-12: Fixed duplicate file write bug, added DEPENDENCIES/RECENT CHANGES sections

TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:documentation--> <!--TAG:automation--> <!--TAG:summarization--> <!--TAG:context-->

<!--/TAG:tool_summarize_docs-->
"""

import os
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import sys
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.docs_logger import DocsLogger
from utils.docs_llm_backend import DocsLLMBackend
# Import hierarchical chunker
from docs.automation.chunk_documents import (
    HierarchicalDocumentChunker,
    ChunkLayer,
    HierarchicalChunk
)

logger = DocsLogger("summarize_docs")

@dataclass
class Summary:
    """Document summary (backward compatible)"""
    original_file: str
    original_length: int
    summary_length: int
    compression_ratio: float
    summary: str

@dataclass
class MultiLevelSummary:
    """Multi-level document summary with hierarchical structure."""
    tldr: str                           # 1-2 sentences, <100 words
    brief: str                          # 2-3 paragraphs, <300 words
    detailed: str                       # Full summary, <1000 words
    full: str                           # Complete hierarchical summary
    hierarchy_uids: List[str] = field(default_factory=list)  # UIDs of intermediate summaries
    compression_ratios: Dict[str, float] = field(default_factory=dict)  # Ratio for each level
    original_file: str = ""
    original_length: int = 0

class DocumentSummarizer:
    """Summarize documentation files"""
    
    def __init__(self, project_root: Path = None):
        """Initialize summarizer with optional project root."""
        self.project_root = project_root or Path(__file__).parent.parent
        self.llm_backend = None
        self._init_llm_backend()
    
    def _init_llm_backend(self):
        """Initialize LLM backend (optional, for --use-llm mode)."""
        try:
            self.llm_backend = DocsLLMBackend()
            if self.llm_backend.is_available():
                logger.info("✅ LLM backend available for high-quality summaries")
            else:
                logger.warning("⚠️ LLM backend not available, will use extractive mode")
                self.llm_backend = None
        except Exception as e:
            logger.warning(f"⚠️ LLM backend init failed: {e}")
            self.llm_backend = None
    
    def summarize(self, file_path: Path, max_length: int = 1000) -> Summary:
        """Summarize a documentation file"""
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_length = len(content)
        
        # Extract structure
        structure = self._extract_structure(content)
        
        # Generate summary
        summary_parts = []
        
        # Add title
        if structure['title']:
            summary_parts.append(f"# {structure['title']}\n")
        
        # Add overview
        if structure['overview']:
            summary_parts.append("## Overview\n")
            summary_parts.append(structure['overview'][:200] + "...\n")
        
        # Add section summaries
        if structure['sections']:
            summary_parts.append("## Sections\n")
            for section in structure['sections'][:10]:  # Limit to 10 sections
                summary_parts.append(f"### {section['heading']}")
                # Take first sentence or 100 chars
                first_sentence = section['content'].split('.')[0][:100]
                summary_parts.append(f"{first_sentence}...\n")
        
        # Add key points
        if structure['key_points']:
            summary_parts.append("## Key Points\n")
            for point in structure['key_points'][:5]:
                summary_parts.append(f"- {point}")
            summary_parts.append("")
        
        # Combine summary
        summary_text = '\n'.join(summary_parts)
        
        # Trim to max length if needed
        if len(summary_text) > max_length:
            summary_text = summary_text[:max_length] + "\n\n... (truncated)"
        
        return Summary(
            original_file=str(file_path),
            original_length=original_length,
            summary_length=len(summary_text),
            compression_ratio=len(summary_text) / original_length,
            summary=summary_text
        )
    
    def _extract_structure(self, content: str) -> Dict:
        """Extract document structure"""
        structure = {
            'title': None,
            'overview': None,
            'sections': [],
            'key_points': []
        }
        
        lines = content.split('\n')
        
        # Extract title (first # heading)
        for line in lines:
            if line.startswith('# '):
                structure['title'] = line[2:].strip()
                break
        
        # Extract sections
        current_section = None
        for line in lines:
            # Heading
            if line.startswith('##'):
                if current_section:
                    structure['sections'].append(current_section)
                
                heading_level = len(re.match(r'^#+', line).group())
                heading_text = line[heading_level:].strip()
                
                current_section = {
                    'level': heading_level,
                    'heading': heading_text,
                    'content': ''
                }
            
            # Content
            elif current_section:
                current_section['content'] += line + '\n'
        
        # Add last section
        if current_section:
            structure['sections'].append(current_section)
        
        # Extract overview (first section or first paragraph)
        if structure['sections']:
            first_section = structure['sections'][0]
            if first_section['heading'].lower() in ['overview', 'introduction', 'purpose']:
                structure['overview'] = first_section['content']
        
        # Extract key points (bullet lists)
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('*'):
                point = line.strip()[1:].strip()
                if len(point) > 10:  # Meaningful points
                    structure['key_points'].append(point)
        
        return structure
    
    async def summarize_multi_level_async(
        self,
        file_path: Path,
        use_llm: bool = False,
        save_hierarchy: bool = False
    ) -> MultiLevelSummary:
        """
        Generate multi-level summary using hierarchical chunking.
        
        Args:
            file_path: Path to markdown file
            use_llm: Use LLM for high-quality summaries (requires vLLM server)
            save_hierarchy: Save intermediate summaries with UIDs
            
        Returns:
            MultiLevelSummary with all 4 detail levels
        """
        logger.info(f"Generating multi-level summary for: {file_path}")
        
        # 1. Chunk document using existing infrastructure
        chunker = HierarchicalDocumentChunker(
            project_root=self.project_root,
            clause_size=200,  # Tokens
            section_size=2000,
            overlap=50
        )
        chunks = chunker.chunk_document(file_path)
        
        # 2. Get document chunk for metadata
        doc_chunk = chunks[ChunkLayer.DOCUMENTS][0]
        original_length = len(doc_chunk.content)
        
        # 3. Generate TLDR (from DOCUMENTS layer)
        logger.info("Generating TLDR...")
        tldr = self._generate_tldr(doc_chunk.content, use_llm)
        
        # 4. Generate Brief (from SECTIONS layer)
        logger.info("Generating Brief...")
        section_chunks = chunks[ChunkLayer.SECTIONS]
        brief = await self._generate_brief_async(section_chunks, use_llm)
        
        # 5. Generate Detailed (from CLAUSES layer with batching)
        logger.info("Generating Detailed...")
        clause_chunks = chunks[ChunkLayer.CLAUSES]
        detailed = await self._generate_detailed_async(clause_chunks, use_llm)
        
        # 6. Generate Full (hierarchical with UIDs)
        logger.info("Generating Full...")
        full, hierarchy_uids = await self._generate_full_async(
            chunks, use_llm, save_hierarchy, file_path
        )
        
        # 7. Calculate compression ratios
        ratios = {
            'tldr': len(tldr) / original_length if original_length > 0 else 0,
            'brief': len(brief) / original_length if original_length > 0 else 0,
            'detailed': len(detailed) / original_length if original_length > 0 else 0,
            'full': len(full) / original_length if original_length > 0 else 0
        }
        
        logger.info(f"Multi-level summary complete. Compression ratios: {ratios}")
        
        return MultiLevelSummary(
            tldr=tldr,
            brief=brief,
            detailed=detailed,
            full=full,
            hierarchy_uids=hierarchy_uids,
            compression_ratios=ratios,
            original_file=str(file_path),
            original_length=original_length
        )
    
    def _generate_tldr(self, content: str, use_llm: bool) -> str:
        """Generate TLDR (1-2 sentences)."""
        if use_llm and self.llm_backend:
            # Use LLM for high-quality TLDR
            system_prompt = "You are a concise summarizer. Generate a 1-2 sentence summary."
            user_prompt = f"Summarize in 1-2 sentences:\n\n{content[:2000]}"
            result = self.llm_backend.generate(system_prompt, user_prompt, max_tokens=100)
            if result:
                return result
        
        # Extractive fallback: first 2 sentences
        sentences = re.split(r'[.!?]+\s+', content)
        tldr_sentences = [s.strip() for s in sentences[:2] if s.strip()]
        return '. '.join(tldr_sentences) + '.' if tldr_sentences else "No content available."
    
    async def _generate_brief_async(self, section_chunks: List[HierarchicalChunk], use_llm: bool) -> str:
        """Generate Brief (2-3 paragraphs from sections)."""
        if use_llm and self.llm_backend:
            # Summarize top sections
            summaries = []
            for chunk in section_chunks[:10]:  # Limit to 10 sections
                header = chunk.metadata.get('header', 'Section')
                content_preview = chunk.content[:500]
                
                system_prompt = "You are a concise summarizer."
                user_prompt = f"Summarize this section in 2-3 sentences:\n\n## {header}\n\n{content_preview}"
                result = self.llm_backend.generate(system_prompt, user_prompt, max_tokens=150)
                
                if result:
                    summaries.append(f"**{header}**: {result}")
            
            return '\n\n'.join(summaries) if summaries else "No sections available."
        else:
            # Extractive: first sentence of each section
            summaries = []
            for chunk in section_chunks[:10]:
                header = chunk.metadata.get('header', 'Section')
                first_sentence = chunk.content.split('. ')[0] + '.'
                summaries.append(f"**{header}**: {first_sentence}")
            return '\n\n'.join(summaries) if summaries else "No sections available."
    
    async def _generate_detailed_async(self, clause_chunks: List[HierarchicalChunk], use_llm: bool) -> str:
        """Generate Detailed summary (<1000 words)."""
        # Group clauses by section
        sections = defaultdict(list)
        for chunk in clause_chunks:
            header = chunk.metadata.get('header', 'Introduction')
            sections[header].append(chunk.content)
        
        if use_llm and self.llm_backend:
            # Summarize each section comprehensively
            summaries = []
            for header, clauses in list(sections.items())[:15]:  # Limit to 15 sections
                combined = '\n\n'.join(clauses[:5])  # Limit to 5 clauses per section
                
                system_prompt = "You are a detailed summarizer."
                user_prompt = f"Summarize this section comprehensively:\n\n## {header}\n\n{combined[:2000]}"
                result = self.llm_backend.generate(system_prompt, user_prompt, max_tokens=300)
                
                if result:
                    summaries.append(f"## {header}\n\n{result}")
            
            return '\n\n'.join(summaries) if summaries else "No content available."
        else:
            # Extractive: combine clauses with headers
            summaries = []
            for header, clauses in list(sections.items())[:15]:
                combined = ' '.join(clauses[:5])[:500]  # Limit length
                summaries.append(f"## {header}\n\n{combined}...")
            return '\n\n'.join(summaries) if summaries else "No content available."
    
    async def _generate_full_async(
        self,
        chunks: Dict[ChunkLayer, List[HierarchicalChunk]],
        use_llm: bool,
        save_hierarchy: bool,
        file_path: Path
    ) -> Tuple[str, List[str]]:
        """Generate Full hierarchical summary with UIDs."""
        doc_chunk = chunks[ChunkLayer.DOCUMENTS][0]
        section_chunks = chunks[ChunkLayer.SECTIONS]
        clause_chunks = chunks[ChunkLayer.CLAUSES]
        
        hierarchy_uids = []
        
        # Save intermediate summaries if requested
        if save_hierarchy:
            for i, chunk in enumerate(clause_chunks):
                uid = self._save_chunk_summary(chunk, file_path, 'clause', i)
                hierarchy_uids.append(uid)
            
            for i, chunk in enumerate(section_chunks):
                uid = self._save_chunk_summary(chunk, file_path, 'section', i)
                hierarchy_uids.append(uid)
        
        # Build full summary
        full_parts = []
        full_parts.append(f"# {doc_chunk.metadata.get('file_name', 'Document')}\n")
        
        # Add TLDR
        tldr = self._generate_tldr(doc_chunk.content, use_llm)
        full_parts.append(f"**TL;DR**: {tldr}\n")
        
        # Add section summaries
        for section in section_chunks:
            header = section.metadata['header']
            # Get clauses for this section
            section_clauses = [c for c in clause_chunks if c.parent_id == section.chunk_id]
            
            full_parts.append(f"## {header}\n")
            
            if section_clauses:
                # Show first 3 clauses
                for clause in section_clauses[:3]:
                    full_parts.append(clause.content)
                
                if len(section_clauses) > 3:
                    full_parts.append(f"\n... and {len(section_clauses) - 3} more clauses")
            else:
                # Fallback to section content preview
                full_parts.append(section.content[:500] + "...")
        
        # Add hierarchy section if saved
        if save_hierarchy and hierarchy_uids:
            full_parts.append("\n\n## Summary Hierarchy\n")
            full_parts.append("This summary was built from the following intermediate summaries:\n")
            full_parts.append('\n'.join([f"- [[{uid}]]" for uid in hierarchy_uids]))
        
        return '\n\n'.join(full_parts), hierarchy_uids
    
    def _save_chunk_summary(self, chunk: HierarchicalChunk, file_path: Path, layer: str, index: int) -> str:
        """Save chunk summary and return UID."""
        uid = f"chunk-{file_path.stem}-{layer}-{index:03d}"
        
        # Save to docs/automation/summaries/chunks/
        output_dir = Path(__file__).parent / "summaries" / "chunks" / file_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{layer}_{index:03d}.md"
        
        content = f"""---
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
        temp_file = output_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_file, output_file)
            logger.debug(f"Saved chunk summary: {uid}")
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            logger.error(f"Failed to save chunk summary: {e}")
            raise e
        
        return uid

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Summarize documentation files with multi-level detail',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple mode (backward compatible)
  python3 summarize_docs.py --input GEMINI.MD --max-length 1000

  # Multi-level mode with all detail levels
  python3 summarize_docs.py --input GEMINI.MD --detail-level all

  # Use LLM for high-quality summaries (requires vLLM server)
  python3 summarize_docs.py --input GEMINI.MD --detail-level all --use-llm

  # Save hierarchical structure
  python3 summarize_docs.py --input GEMINI.MD --detail-level full --save-hierarchy

  # Async mode for large documents
  python3 summarize_docs.py --input GEMINI.MD --detail-level all --async
        """
    )
    
    parser.add_argument('--input', type=str, required=True, help='Input file to summarize')
    parser.add_argument('--output', type=str, help='Output file for summary')
    parser.add_argument('--max-length', type=int, default=1000, 
                       help='Maximum summary length (simple mode only)')
    parser.add_argument('--detail-level', type=str,
                       choices=['tldr', 'brief', 'detailed', 'full', 'all'],
                       help='Level of detail for summary (enables multi-level mode)')
    parser.add_argument('--use-llm', action='store_true',
                       help='Use LLM for high-quality summaries (requires vLLM server)')
    parser.add_argument('--save-hierarchy', action='store_true',
                       help='Save intermediate summaries with UIDs')
    parser.add_argument('--async', dest='use_async', action='store_true',
                       help='Use async processing (faster for large docs)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        logger.error(f"Error: File not found: {input_path}")
        return
    
    # Initialize summarizer
    summarizer = DocumentSummarizer()
    
    # Determine mode: multi-level or simple
    if args.detail_level:
        # Multi-level mode
        logger.info(f"Multi-level summarization mode: {args.detail_level}")
        
        if args.use_async:
            # Async mode
            summary = asyncio.run(summarizer.summarize_multi_level_async(
                input_path,
                use_llm=args.use_llm,
                save_hierarchy=args.save_hierarchy
            ))
        else:
            # Sync mode (run async in sync context)
            summary = asyncio.run(summarizer.summarize_multi_level_async(
                input_path,
                use_llm=args.use_llm,
                save_hierarchy=args.save_hierarchy
            ))
        
        # Format output based on detail level
        if args.detail_level == 'tldr':
            result_text = f"# TL;DR\n\n{summary.tldr}"
        elif args.detail_level == 'brief':
            result_text = f"# Brief Summary\n\n{summary.brief}"
        elif args.detail_level == 'detailed':
            result_text = f"# Detailed Summary\n\n{summary.detailed}"
        elif args.detail_level == 'full':
            result_text = summary.full
        elif args.detail_level == 'all':
            result_text = f"""# Multi-Level Summary: {input_path.name}

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
    else:
        # Simple mode (backward compatible)
        logger.info("Simple summarization mode")
        summary = summarizer.summarize(input_path, args.max_length)
        
        # Format output
        output = []
        output.append(f"Summary of: {summary.original_file}")
        output.append(f"Original length: {summary.original_length} chars")
        output.append(f"Summary length: {summary.summary_length} chars")
        output.append(f"Compression ratio: {summary.compression_ratio:.1%}")
        output.append("\n" + "=" * 60 + "\n")
        output.append(summary.summary)
        
        result_text = '\n'.join(output)
    
    # Save to file or print to stdout
    if args.output:
        output_path = Path(args.output)
        # Write summary to specified output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_text)
        logger.info(f"Summary saved to: {output_path}")
    else:
        print(result_text)

if __name__ == '__main__':
    main()
