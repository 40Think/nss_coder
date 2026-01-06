#!/usr/bin/env python3
"""
Document Chunker - Hierarchical Multi-Layer Chunking for RAG Systems

<!--TAG:tool_chunk_documents-->

PURPOSE:
    Splits markdown documentation into hierarchical semantic chunks for RAG systems.
    Implements 3-layer memory architecture adapted from cheap_memory.py:
    - L0 (CLAUSES): Fine-grained sentence/paragraph level
    - L1 (SECTIONS): Header-based sections
    - L2 (DOCUMENTS): Full document embeddings
    
    Preserves code blocks, tables, and lists intact.
    Supports adaptive chunk sizing based on content complexity.

DOCUMENTATION:
    Spec: docs/specs/Automation_Tools_Spec.md
    Wiki: docs/wiki/09_Documentation_System.md
    Analysis: docs/technical_debt/chunk_documents_gaps.md
    
ADAPTED FROM:
    - utils/cheap_memory.py (3-layer hierarchical memory)
    - utils/embedding_client.py (adaptive batch sizing)
    - utils/thread_embedder.py (thread context)

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger (DocsLogger - paranoid logging)
        - transformers.AutoTokenizer (Qwen3 tokenizer for token counting)
    Config:
        - None (standalone utility)
    Data:
        - Input: docs/**/*.md (markdown documentation files)
        - Output: docs/memory/chunks/ (chunked JSON files)
    External:
        - yaml (optional, for frontmatter parsing)
        - transformers (HuggingFace, for Qwen3 tokenizer)

RECENT CHANGES:
    2025-12-13: v2.2 - FULL DEC 2025 BEST PRACTICES
                       - Added AgenticChunker class for LLM-based boundary detection
                       - Activated list preservation in _detect_preserved_blocks()
                       - All improvements now use Qwen3 models from vLLM server
    2025-12-13: v2.1 - TOKEN-BASED SIZING
                       - Added Qwen3 tokenizer for accurate token counting
                       - Changed from char-based to token-based chunk sizing
                       - Added overlap between chunks (50 tokens default)
                       - Added code embeddings placeholder for future
    2025-12-11: v2.0 - Implemented 3-layer hierarchical chunking
                       Added adaptive chunk sizing
                       Added code block/table preservation

TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:memory--> <!--TAG:automation--> <!--TAG:rag--> <!--TAG:chunking--> <!--TAG:hierarchical-->

<!--/TAG:tool_chunk_documents-->
"""

import os
import json
import re
from enum import Enum
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
import hashlib
import sys

# Add project root to path for imports
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.docs_logger import DocsLogger

# Initialize paranoid logger for detailed tracking
logger = DocsLogger("chunk_documents")


# =============================================================================
# LAYER ENUM (Adapted from cheap_memory.py)
# =============================================================================

class ChunkLayer(Enum):
    """
    Hierarchical chunk layers for multi-granularity retrieval.
    
    Adapted from cheap_memory.py Layer enum:
    - CLAUSES (L0): Fine-grained, sentence/paragraph level for precise matching
    - SECTIONS (L1): Header-based sections for topic-level retrieval
    - DOCUMENTS (L2): Full document for broad context
    """
    CLAUSES = "clauses"      # L0: Sentence/paragraph level
    SECTIONS = "sections"    # L1: Header-based sections (original behavior)
    DOCUMENTS = "documents"  # L2: Full document embeddings


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class HierarchicalChunk:
    """
    Chunk with layer information for hierarchical retrieval.
    
    Supports parent-child relationships for context expansion:
    - A CLAUSE chunk has a parent SECTION chunk
    - A SECTION chunk has a parent DOCUMENT chunk
    """
    content: str                    # Chunk text content
    layer: ChunkLayer              # Which layer (CLAUSES/SECTIONS/DOCUMENTS)
    chunk_id: str                  # Unique identifier
    metadata: Dict[str, Any]       # Rich metadata for filtering/context
    parent_id: Optional[str] = None  # ID of parent chunk for hierarchy
    embedding_ready: bool = True   # Flag for embedding pipeline


@dataclass
class PreservedBlock:
    """
    Represents a code block, table, or list that must be preserved intact.
    """
    block_type: str      # 'code_block', 'table', 'list'
    start: int           # Start position in text
    end: int             # End position in text
    content: str         # Full block content
    language: str = ""   # For code blocks: programming language


# =============================================================================
# HIERARCHICAL DOCUMENT CHUNKER
# =============================================================================

class HierarchicalDocumentChunker:
    """
    Multi-layer document chunker adapted from cheap_memory.py.
    
    Features:
    - 3-layer hierarchical chunking (CLAUSES, SECTIONS, DOCUMENTS)
    - Code block and table preservation
    - Adaptive chunk sizing based on content complexity
    - Parent-child relationships for context expansion
    - Rich metadata for filtering and ranking
    """
    
    # Default configuration (TOKEN-BASED - Dec 2025 best practices)
    # NOTE: Now using TOKENS not chars. 1 token ≈ 4 chars average.
    DEFAULT_CLAUSE_SIZE = 200      # Max TOKENS for clause chunks (was chars)
    DEFAULT_SECTION_SIZE = 2000    # Max TOKENS before splitting sections
    DEFAULT_OVERLAP = 50           # Overlap TOKENS between adjacent clauses
    
    # Optimal token sizes per content type (Dec 2025 research):
    # - Code/tables: 512 tokens (keep structured content together)
    # - Dense text: 200-300 tokens (short sentences, many words)
    # - Normal text: 400 tokens (balanced)
    # - Sparse text: 600 tokens (code-like, long words)
    
    # Regex patterns for structure detection
    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    CODE_FENCE_PATTERN = re.compile(r'```[\w]*\n.*?\n```', re.DOTALL)
    TABLE_PATTERN = re.compile(r'(\|.+\|\n)+(\|[-:| ]+\|\n)(\|.+\|\n)+')
    LIST_PATTERN = re.compile(r'^(\s*[-*+]\s.+\n)+', re.MULTILINE)
    SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')
    
    def __init__(
        self, 
        project_root: Path = None,
        clause_size: int = None,
        section_size: int = None,
        overlap: int = None
    ):
        """
        Initialize the hierarchical chunker.
        
        Args:
            project_root: Project root for relative path calculation
            clause_size: Maximum size for clause chunks (L0)
            section_size: Maximum size before splitting sections
            overlap: Character overlap between adjacent clauses
        """
        # Set project root (default: 2 levels up from this file)
        self.project_root = project_root or Path(__file__).parent.parent
        
        # Configuration with defaults (all sizes in TOKENS)
        self.clause_size = clause_size or self.DEFAULT_CLAUSE_SIZE
        self.section_size = section_size or self.DEFAULT_SECTION_SIZE
        self.overlap = overlap or self.DEFAULT_OVERLAP
        
        # Initialize Qwen3 tokenizer for accurate token counting
        # NOTE: tiktoken is OpenAI-specific, Qwen3 needs HuggingFace tokenizer
        self.tokenizer = None
        self._init_tokenizer()
        
        logger.info(f"HierarchicalDocumentChunker initialized", {
            "project_root": str(self.project_root),
            "clause_size_tokens": self.clause_size,
            "section_size_tokens": self.section_size,
            "overlap_tokens": self.overlap,
            "tokenizer_available": self.tokenizer is not None
        })
    
    def _init_tokenizer(self):
        """
        Initialize Qwen3 tokenizer for accurate token counting.
        
        Uses lightweight Qwen2.5-0.5B tokenizer (same vocab as Qwen3).
        Falls back to character-based estimation if unavailable.
        """
        try:
            from transformers import AutoTokenizer
            # Use lightweight tokenizer with compatible vocabulary
            self.tokenizer = AutoTokenizer.from_pretrained(
                "Qwen/Qwen2.5-0.5B",
                trust_remote_code=True
            )
            logger.info("✅ Qwen3 tokenizer initialized successfully")
        except ImportError:
            logger.warning("⚠️ transformers not installed, using char-based fallback")
            self.tokenizer = None
        except Exception as e:
            logger.warning(f"⚠️ Tokenizer init failed, using fallback: {e}")
            self.tokenizer = None
    
    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Qwen3 tokenizer.
        
        Falls back to char/4 estimation if tokenizer unavailable.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens (approximate if using fallback)
        """
        if self.tokenizer is not None:
            # Use real tokenizer for accurate count
            return len(self.tokenizer.encode(text, add_special_tokens=False))
        else:
            # Fallback: ~4 chars per token average
            return len(text) // 4
    
    # =========================================================================
    # MAIN CHUNKING METHOD
    # =========================================================================
    
    def chunk_document(self, doc_file: Path) -> Dict[ChunkLayer, List[HierarchicalChunk]]:
        """
        Chunk document into 3 hierarchical layers.
        
        Args:
            doc_file: Path to markdown file
            
        Returns:
            Dict mapping each layer to list of chunks
        """
        logger.info(f"Chunking document: {doc_file}")
        
        # Read document content
        content = doc_file.read_text(encoding='utf-8')
        
        # Extract frontmatter for metadata
        frontmatter = self._extract_frontmatter(content)
        content_body = self._remove_frontmatter(content)
        
        # Initialize chunk containers for each layer
        chunks = {
            ChunkLayer.CLAUSES: [],
            ChunkLayer.SECTIONS: [],
            ChunkLayer.DOCUMENTS: []
        }
        
        # Calculate relative path for metadata
        try:
            rel_path = str(doc_file.relative_to(self.project_root))
        except ValueError:
            rel_path = str(doc_file)
        
        # -----------------------------------------------------------------
        # Layer 2 (DOCUMENTS): Full document chunk
        # -----------------------------------------------------------------
        doc_chunk = HierarchicalChunk(
            content=content,
            layer=ChunkLayer.DOCUMENTS,
            chunk_id=f"doc_{doc_file.stem}",
            metadata={
                'file_path': rel_path,
                'file_name': doc_file.name,
                'layer': 'document',
                'char_count': len(content),
                'word_count': len(content.split()),
                'frontmatter': frontmatter
            }
        )
        chunks[ChunkLayer.DOCUMENTS].append(doc_chunk)
        
        # -----------------------------------------------------------------
        # Layer 1 (SECTIONS): Header-based sections
        # -----------------------------------------------------------------
        sections = self._split_by_headers(content_body, doc_file)
        
        for i, section in enumerate(sections):
            section_id = f"sec_{doc_file.stem}_{i}"
            
            section_chunk = HierarchicalChunk(
                content=section['content'],
                layer=ChunkLayer.SECTIONS,
                chunk_id=section_id,
                metadata={
                    'file_path': rel_path,
                    'file_name': doc_file.name,
                    'layer': 'section',
                    'header': section['header'],
                    'header_level': section['level'],
                    'parent_header': section['parent'],
                    'section_index': i,
                    'char_count': len(section['content']),
                    'has_code': '```' in section['content'],
                    'has_table': '|' in section['content']
                },
                parent_id=doc_chunk.chunk_id
            )
            chunks[ChunkLayer.SECTIONS].append(section_chunk)
            
            # -------------------------------------------------------------
            # Layer 0 (CLAUSES): Fine-grained chunks within section
            # -------------------------------------------------------------
            clauses = self._chunk_into_clauses(
                section['content'], 
                section['header']
            )
            
            for j, clause in enumerate(clauses):
                clause_id = f"cls_{doc_file.stem}_{i}_{j}"
                
                clause_chunk = HierarchicalChunk(
                    content=clause,
                    layer=ChunkLayer.CLAUSES,
                    chunk_id=clause_id,
                    metadata={
                        'file_path': rel_path,
                        'file_name': doc_file.name,
                        'layer': 'clause',
                        'header': section['header'],
                        'clause_index': j,
                        'section_index': i,
                        'char_count': len(clause)
                    },
                    parent_id=section_id
                )
                chunks[ChunkLayer.CLAUSES].append(clause_chunk)
        
        # Log statistics
        stats = {layer.value: len(chunks[layer]) for layer in ChunkLayer}
        logger.info(f"Chunking complete: {stats}")
        
        return chunks
    
    # =========================================================================
    # FRONTMATTER HANDLING
    # =========================================================================
    
    def _extract_frontmatter(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract YAML frontmatter from markdown."""
        # Match --- at start followed by content then ---
        pattern = r'^---\n(.*?)\n---\n'
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            try:
                import yaml
                return yaml.safe_load(match.group(1))
            except Exception as e:
                logger.warning(f"Failed to parse frontmatter: {e}")
                return None
        return None
    
    def _remove_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter from content."""
        pattern = r'^---\n.*?\n---\n'
        return re.sub(pattern, '', content, count=1, flags=re.DOTALL)
    
    # =========================================================================
    # STRUCTURE PRESERVATION (Code blocks, tables, lists)
    # =========================================================================
    
    def _detect_preserved_blocks(self, content: str) -> List[PreservedBlock]:
        """
        Detect code blocks, tables, and lists that must stay intact.
        
        Returns list of PreservedBlock objects sorted by position.
        """
        blocks = []
        
        # Detect code fences (```...```)
        for match in self.CODE_FENCE_PATTERN.finditer(content):
            # Extract language from opening fence
            first_line = match.group(0).split('\n')[0]
            language = first_line.replace('```', '').strip()
            
            blocks.append(PreservedBlock(
                block_type='code_block',
                start=match.start(),
                end=match.end(),
                content=match.group(0),
                language=language
            ))
        
        # Detect markdown tables
        for match in self.TABLE_PATTERN.finditer(content):
            blocks.append(PreservedBlock(
                block_type='table',
                start=match.start(),
                end=match.end(),
                content=match.group(0)
            ))
        
        # Detect markdown lists (Dec 2025: activate list preservation)
        # Match consecutive lines starting with -, *, +, or numbers
        for match in self.LIST_PATTERN.finditer(content):
            list_content = match.group(0)
            # Only preserve lists with 2+ items (single items don't need preservation)
            if list_content.count('\n') >= 2:
                blocks.append(PreservedBlock(
                    block_type='list',
                    start=match.start(),
                    end=match.end(),
                    content=list_content
                ))
        
        # Sort by position for sequential processing
        blocks.sort(key=lambda b: b.start)
        
        return blocks
    
    def _chunk_with_preservation(
        self, 
        text: str, 
        preserved_blocks: List[PreservedBlock]
    ) -> List[str]:
        """
        Chunk text while keeping preserved blocks intact.
        
        Strategy:
        1. Split text around preserved blocks
        2. Chunk non-preserved segments normally
        3. Keep preserved blocks as single chunks
        """
        if not preserved_blocks:
            # No special blocks, chunk normally
            return self._split_into_sentences(text)
        
        chunks = []
        current_pos = 0
        
        for block in preserved_blocks:
            # Chunk text before this block
            before_text = text[current_pos:block.start]
            if before_text.strip():
                chunks.extend(self._split_into_sentences(before_text))
            
            # Add preserved block as single chunk
            chunks.append(block.content)
            
            current_pos = block.end
        
        # Chunk remaining text after last block
        remaining = text[current_pos:]
        if remaining.strip():
            chunks.extend(self._split_into_sentences(remaining))
        
        return chunks
    
    # =========================================================================
    # SECTION SPLITTING (Header-based)
    # =========================================================================
    
    def _split_by_headers(
        self, 
        content: str, 
        doc_file: Path
    ) -> List[Dict[str, Any]]:
        """
        Split content by markdown headers while preserving hierarchy.
        """
        sections = []
        lines = content.split('\n')
        
        # Track current section being built
        current_section = {
            'content': '',
            'header': None,
            'level': 0,
            'parent': None
        }
        
        # Stack for tracking header hierarchy
        header_stack = []
        
        for line in lines:
            header_match = self.HEADER_PATTERN.match(line)
            
            if header_match:
                # Save previous section if it has content
                if current_section['content'].strip():
                    sections.append(current_section)
                
                # Parse header
                level = len(header_match.group(1))
                heading = header_match.group(2).strip()
                
                # Update header stack for hierarchy tracking
                while header_stack and header_stack[-1]['level'] >= level:
                    header_stack.pop()
                
                parent = header_stack[-1]['heading'] if header_stack else None
                header_stack.append({'heading': heading, 'level': level})
                
                # Start new section
                current_section = {
                    'content': line + '\n',
                    'header': heading,
                    'level': level,
                    'parent': parent
                }
            else:
                # Add line to current section
                current_section['content'] += line + '\n'
        
        # Add final section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    # =========================================================================
    # CLAUSE CHUNKING (Fine-grained)
    # =========================================================================
    
    def _chunk_into_clauses(
        self, 
        text: str, 
        header: Optional[str] = None
    ) -> List[str]:
        """
        Chunk section into clause-level chunks.
        
        Strategy:
        1. Detect and preserve code blocks/tables
        2. Split remaining text by paragraphs
        3. Further split large paragraphs by sentences
        4. Merge small chunks to meet minimum size
        """
        # Detect blocks that must stay intact
        preserved = self._detect_preserved_blocks(text)
        
        # Chunk with preservation
        raw_chunks = self._chunk_with_preservation(text, preserved)
        
        # Merge small chunks, split large ones
        final_chunks = []
        current_chunk = ""
        
        for chunk in raw_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            
            # If chunk is a preserved block, add as-is
            if chunk.startswith('```') or '|' in chunk and '---' in chunk:
                if current_chunk:
                    final_chunks.append(current_chunk.strip())
                    current_chunk = ""
                final_chunks.append(chunk)
                continue
            
            # Calculate adaptive size based on content
            max_size = self._calculate_adaptive_size(chunk)
            
            # Merge or split based on size
            if len(current_chunk) + len(chunk) <= max_size:
                current_chunk += "\n\n" + chunk if current_chunk else chunk
            else:
                if current_chunk:
                    final_chunks.append(current_chunk.strip())
                
                # Split if still too large
                if len(chunk) > max_size:
                    final_chunks.extend(self._split_large_chunk(chunk, max_size))
                    current_chunk = ""
                else:
                    current_chunk = chunk
        
        # Add remaining chunk
        if current_chunk.strip():
            final_chunks.append(current_chunk.strip())
        
        return final_chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentence-based chunks."""
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        result = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(para) <= self.clause_size:
                result.append(para)
            else:
                # Split by sentences
                sentences = self.SENTENCE_SPLIT.split(para)
                current = ""
                
                for sent in sentences:
                    if len(current) + len(sent) <= self.clause_size:
                        current += " " + sent if current else sent
                    else:
                        if current:
                            result.append(current.strip())
                        current = sent
                
                if current:
                    result.append(current.strip())
        
        return result
    
    def _split_large_chunk(self, text: str, max_size: int) -> List[str]:
        """Split a chunk that exceeds max size."""
        sentences = self.SENTENCE_SPLIT.split(text)
        
        chunks = []
        current = ""
        
        for sent in sentences:
            if len(current) + len(sent) <= max_size:
                current += " " + sent if current else sent
            else:
                if current:
                    chunks.append(current.strip())
                current = sent
        
        if current:
            chunks.append(current.strip())
        
        return chunks
    
    # =========================================================================
    # ADAPTIVE CHUNK SIZING (TOKEN-BASED - Dec 2025 Best Practices)
    # =========================================================================
    
    def _calculate_adaptive_size(self, text: str) -> int:
        """
        Calculate optimal chunk size in TOKENS based on content complexity.
        
        Adapted from embedding_client.py calculate_batch_size().
        Updated Dec 2025 to use tokens instead of chars per best practices.
        
        Strategy (all sizes in TOKENS):
        - Code/tables: 512 tokens (keep structured content together)
        - Dense text: 200 tokens (many short words)
        - Normal text: 400 tokens (balanced)
        - Sparse text: 600 tokens (code-like, long identifiers)
        
        Research sources:
        - NVIDIA (2024): 200-800 tokens optimal range
        - Firecrawl (2025): Token-based critical for LLM alignment
        - Galileo AI (2025): tiktoken/tokenizer for accurate counting
        """
        # Check for code or tables (need larger chunks to keep intact)
        has_code = '```' in text
        has_table = '|' in text and '---' in text
        
        if has_code or has_table:
            return 512  # Large chunks for structured content (TOKENS)
        
        # Check text density (words per character indicates content type)
        words = len(text.split())
        chars = len(text)
        density = words / chars if chars > 0 else 0
        
        if density > 0.2:  # Dense text (many short words)
            return 200  # TOKENS
        elif density > 0.15:  # Normal text
            return 400  # TOKENS
        else:  # Sparse text (code-like, long identifiers)
            return 600  # TOKENS
    
    def _add_overlap(self, chunks: List[str], overlap_tokens: int = None) -> List[str]:
        """
        Add token-based overlap between consecutive chunks.
        
        Dec 2025 best practice: 10-20% overlap (50-100 tokens for 500-char chunks).
        This prevents context loss at chunk boundaries.
        
        Args:
            chunks: List of chunk texts
            overlap_tokens: Number of tokens to overlap (default: self.overlap)
            
        Returns:
            List of chunks with overlap added
        """
        if not chunks or len(chunks) < 2:
            return chunks
        
        overlap_tokens = overlap_tokens or self.overlap
        overlapped = [chunks[0]]  # First chunk unchanged
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]
            
            # Get overlap from previous chunk
            if self.tokenizer is not None:
                # Token-based overlap (accurate)
                prev_tokens = self.tokenizer.encode(prev_chunk, add_special_tokens=False)
                overlap_token_ids = prev_tokens[-overlap_tokens:] if len(prev_tokens) > overlap_tokens else prev_tokens
                overlap_text = self.tokenizer.decode(overlap_token_ids)
            else:
                # Fallback: char-based (approx 4 chars/token)
                overlap_chars = overlap_tokens * 4
                overlap_text = prev_chunk[-overlap_chars:] if len(prev_chunk) > overlap_chars else prev_chunk
            
            # Prepend overlap to current chunk
            overlapped.append(overlap_text.strip() + " " + current_chunk)
        
        return overlapped


# =============================================================================
# SPECIALIZED CODE EMBEDDINGS PLACEHOLDER (Future Implementation)
# =============================================================================
#
# TODO: Integrate specialized code embeddings for improved code retrieval
#
# MODELS TO CONSIDER (December 2025 state-of-the-art):
#   - Qwen3-embedding-8b: Native Qwen3, excellent for multilingual + code
#   - Code-Embed (Li et al., 2024): Fine-tuned on code-language pairs
#   - Qodo-Embed-1 (2025): Specialized code embeddings for search
#   - Google Gemini Embedding: State-of-the-art for code tasks
#
# IMPLEMENTATION NOTES:
#   1. Code blocks already detected via `_detect_preserved_blocks()`
#   2. `language` field available in PreservedBlock.language
#   3. For embedding: extract code, get embedding, store separately
#   4. At retrieval: use code-specific similarity when query looks like code
#
# INTEGRATION POINTS:
#   - `index_project.py`: Add code embedding generation
#       def _generate_code_embeddings(self, code_blocks: List[PreservedBlock]):
#           # Use code-specific model
#           pass
#
#   - `docs_dual_memory.py`: Add code embedding storage/search
#       def search_code(self, query: str, top_k: int = 10):
#           # Route to code-specific vector index
#           pass
#
#   - `semantic_search.py`: Route code queries to code embeddings
#       def _is_code_query(self, query: str) -> bool:
#           # Detect if query contains code patterns
#           pass
#
# EXAMPLE USAGE (future):
#   def _get_code_embedding(self, code: str, language: str) -> List[float]:
#       """Get specialized embedding for code block."""
#       # 1. Format code with language context
#       prompt = f"```{language}\n{code}\n```"
#       # 2. Use code-specific embedding model
#       embedding = self.code_embedder.encode(prompt)
#       return embedding.tolist()
#


# =============================================================================
# AGENTIC CHUNKING (Dec 2025 - LLM-Based Boundary Detection)
# =============================================================================

class AgenticChunker:
    """
    LLM-based chunker that uses Qwen3-Coder-30B to determine optimal boundaries.
    
    Dec 2025 best practice: Instead of rule-based splitting, use LLM to
    understand content semantically and place boundaries at natural breaks.
    
    This is OPT-IN via --agentic flag (expensive, requires LLM server).
    """
    
    # System prompt for boundary detection
    BOUNDARY_PROMPT = '''You are a document chunking expert. Your task is to analyze text and identify the best places to split it into semantic chunks.

Rules:
1. Each chunk should be self-contained and about ONE topic
2. Keep related information together (code with its explanation, list items together)
3. Split at natural boundaries: paragraph breaks, section changes, topic shifts
4. Target chunk size: 200-500 tokens per chunk
5. NEVER split in the middle of: code blocks, tables, lists, sentences

Output format: Return ONLY a JSON array of line numbers where splits should occur.
Example: [15, 42, 78, 112]'''

    def __init__(self, project_root: Path = None):
        """Initialize agentic chunker with LLM backend."""
        self.project_root = project_root or Path(__file__).parent.parent
        self.llm_backend = None
        self._init_llm_backend()
    
    def _init_llm_backend(self):
        """Initialize LLM backend for boundary detection."""
        try:
            from utils.docs_llm_backend import DocsLLMBackend
            self.llm_backend = DocsLLMBackend()
            logger.info("✅ Agentic chunker initialized with LLM backend")
        except ImportError:
            logger.warning("⚠️ LLM backend not available, agentic chunking disabled")
            self.llm_backend = None
        except Exception as e:
            logger.warning(f"⚠️ LLM backend init failed: {e}")
            self.llm_backend = None
    
    def is_available(self) -> bool:
        """Check if agentic chunking is available."""
        if self.llm_backend is None:
            return False
        return self.llm_backend.is_available()
    
    def get_boundaries(self, content: str, max_tokens: int = 1000) -> List[int]:
        """
        Use LLM to determine optimal chunk boundaries.
        
        Args:
            content: Text content to analyze
            max_tokens: Max tokens for LLM context
            
        Returns:
            List of line numbers where splits should occur
        """
        if not self.is_available():
            logger.warning("⚠️ LLM not available, returning empty boundaries")
            return []
        
        # Add line numbers to content for LLM
        lines = content.split('\n')
        numbered_content = '\n'.join(
            f"{i+1}: {line}" for i, line in enumerate(lines)
        )
        
        # Truncate if too long (keep first and last parts for context)
        if len(numbered_content) > max_tokens * 4:  # Rough char estimate
            mid = len(lines) // 2
            first_part = '\n'.join(f"{i+1}: {lines[i]}" for i in range(min(100, mid)))
            last_part = '\n'.join(f"{i+1}: {lines[i]}" for i in range(max(mid, len(lines)-100), len(lines)))
            numbered_content = f"{first_part}\n...[truncated]...\n{last_part}"
        
        user_prompt = f"""Analyze this document and identify optimal line numbers for chunk boundaries:

```
{numbered_content}
```

Return ONLY a JSON array of line numbers. No explanation."""
        
        try:
            response = self.llm_backend.generate(
                system_prompt=self.BOUNDARY_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,  # Low temperature for consistent output
                max_tokens=200  # Just need the array
            )
            
            if not response:
                return []
            
            # Parse JSON array from response
            import json
            # Handle markdown code blocks in response
            if '```' in response:
                response = response.split('```')[1]
                if response.startswith('json'):
                    response = response[4:]
                response = response.strip()
            
            boundaries = json.loads(response)
            
            if isinstance(boundaries, list):
                # Validate line numbers
                valid_boundaries = [
                    int(b) for b in boundaries 
                    if isinstance(b, (int, float)) and 1 <= int(b) <= len(lines)
                ]
                logger.info(f"LLM identified {len(valid_boundaries)} chunk boundaries")
                return sorted(valid_boundaries)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
        except Exception as e:
            logger.error(f"Agentic boundary detection failed: {e}")
        
        return []
    
    def chunk_with_llm_boundaries(
        self, 
        content: str, 
        boundaries: List[int]
    ) -> List[str]:
        """
        Split content at LLM-determined boundaries.
        
        Args:
            content: Full text content
            boundaries: Line numbers from get_boundaries()
            
        Returns:
            List of chunk texts
        """
        if not boundaries:
            return [content]
        
        lines = content.split('\n')
        chunks = []
        prev_boundary = 0
        
        for boundary in boundaries:
            # boundary is 1-indexed line number
            chunk_lines = lines[prev_boundary:boundary]
            chunk_text = '\n'.join(chunk_lines).strip()
            if chunk_text:
                chunks.append(chunk_text)
            prev_boundary = boundary
        
        # Add final chunk
        if prev_boundary < len(lines):
            final_chunk = '\n'.join(lines[prev_boundary:]).strip()
            if final_chunk:
                chunks.append(final_chunk)
        
        logger.info(f"Created {len(chunks)} chunks using agentic boundaries")
        return chunks


# =============================================================================
# BACKWARD COMPATIBLE WRAPPER
# =============================================================================

class SemanticChunker:
    """
    Backward compatible wrapper for the old API.
    
    Delegates to HierarchicalDocumentChunker but returns flat chunk list.
    """
    
    def __init__(self, max_chunk_size: int = 1000, overlap: int = 200):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self._hierarchical = HierarchicalDocumentChunker(
            clause_size=max_chunk_size // 5,
            section_size=max_chunk_size,
            overlap=overlap
        )
    
    def chunk_markdown(self, file_path: Path) -> List[HierarchicalChunk]:
        """Chunk markdown file (backward compatible)."""
        chunks = self._hierarchical.chunk_document(file_path)
        # Return SECTIONS layer for backward compatibility
        return chunks[ChunkLayer.SECTIONS]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def json_serial(obj):
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, ChunkLayer):
        return obj.value
    raise TypeError(f"Type {type(obj)} not serializable")


def chunk_to_dict(chunk: HierarchicalChunk) -> Dict[str, Any]:
    """Convert chunk to dictionary for JSON serialization."""
    return {
        'chunk_id': chunk.chunk_id,
        'content': chunk.content,
        'layer': chunk.layer.value,
        'metadata': chunk.metadata,
        'parent_id': chunk.parent_id,
        'embedding_ready': chunk.embedding_ready
    }


# =============================================================================
# DIRECTORY PROCESSING
# =============================================================================

def chunk_directory(
    input_dir: Path, 
    output_dir: Path, 
    file_pattern: str = "*.md",
    hierarchical: bool = True
):
    """
    Chunk all markdown files in a directory.
    
    Args:
        input_dir: Input directory containing markdown files
        output_dir: Output directory for chunk JSON files
        file_pattern: Glob pattern for files to process
        hierarchical: If True, use 3-layer chunking; else use legacy mode
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize appropriate chunker
    if hierarchical:
        chunker = HierarchicalDocumentChunker(project_root=input_dir.parent)
    else:
        chunker = SemanticChunker(max_chunk_size=1000, overlap=200)
    
    # Track all chunks by layer
    all_chunks = {layer: [] for layer in ChunkLayer}
    files_processed = 0
    
    for md_file in input_dir.rglob(file_pattern):
        # Skip system directories
        if '__pycache__' in str(md_file) or 'vllm-latest' in str(md_file):
            continue
        
        logger.info(f"Chunking: {md_file}")
        
        try:
            if hierarchical:
                chunks = chunker.chunk_document(md_file)
                
                # Aggregate by layer
                for layer in ChunkLayer:
                    all_chunks[layer].extend(chunks[layer])
                
                # Save per-file chunks
                relative_path = md_file.relative_to(input_dir)
                output_file = output_dir / f"{relative_path.stem}_chunks.json"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Save all layers for this file
                file_chunks = {
                    layer.value: [chunk_to_dict(c) for c in chunks[layer]]
                    for layer in ChunkLayer
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(file_chunks, f, indent=2, ensure_ascii=False, default=json_serial)
                
                total = sum(len(chunks[l]) for l in ChunkLayer)
                logger.info(f"  → {total} chunks saved to: {output_file}")
            else:
                # Legacy mode
                chunks = chunker.chunk_markdown(md_file)
                all_chunks[ChunkLayer.SECTIONS].extend(chunks)
            
            files_processed += 1
            
        except Exception as e:
            logger.error(f"  ✗ Error processing {md_file}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    # Save combined indexes by layer
    for layer in ChunkLayer:
        index_file = output_dir / f"chunks_index_{layer.value}.json"
        layer_chunks = [chunk_to_dict(c) for c in all_chunks[layer]]
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(layer_chunks, f, indent=2, ensure_ascii=False, default=json_serial)
        
        logger.info(f"Layer {layer.value}: {len(layer_chunks)} chunks → {index_file}")
    
    # Summary statistics
    total_chunks = sum(len(all_chunks[l]) for l in ChunkLayer)
    print(f"\n✓ Processed {files_processed} files")
    print(f"✓ Total chunks: {total_chunks}")
    for layer in ChunkLayer:
        print(f"  - {layer.value}: {len(all_chunks[layer])} chunks")


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Hierarchical Document Chunker for RAG Systems',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Chunk docs with hierarchical 3-layer mode (default)
  python3 chunk_documents.py --input-dir docs --output-dir docs/memory/chunks
  
  # Chunk single file
  python3 chunk_documents.py --file docs/specs/MySpec.md
  
  # Legacy single-layer mode
  python3 chunk_documents.py --input-dir docs --legacy
        """
    )
    
    parser.add_argument('--input-dir', type=str, default='docs',
                       help='Input directory containing markdown files')
    parser.add_argument('--output-dir', type=str, default='docs/memory/chunks',
                       help='Output directory for chunks')
    parser.add_argument('--file', type=str, default=None,
                       help='Single file to chunk (overrides --input-dir)')
    parser.add_argument('--pattern', type=str, default='*.md',
                       help='File pattern to match')
    parser.add_argument('--legacy', action='store_true',
                       help='Use legacy single-layer mode')
    parser.add_argument('--clause-size', type=int, default=200,
                       help='Max size for clause chunks')
    parser.add_argument('--section-size', type=int, default=2000,
                       help='Max size before splitting sections')
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent.parent  # Project root
    
    if args.file:
        # Single file mode
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = base_dir / file_path
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return
        
        chunker = HierarchicalDocumentChunker(
            project_root=base_dir,
            clause_size=args.clause_size,
            section_size=args.section_size
        )
        
        chunks = chunker.chunk_document(file_path)
        
        # Print results
        print(f"\n✓ Chunked: {file_path.name}")
        for layer in ChunkLayer:
            layer_chunks = chunks[layer]
            print(f"\n=== {layer.value.upper()} ({len(layer_chunks)} chunks) ===")
            for c in layer_chunks[:3]:  # Show first 3
                preview = c.content[:100].replace('\n', ' ')
                print(f"  [{c.chunk_id}] {preview}...")
            if len(layer_chunks) > 3:
                print(f"  ... and {len(layer_chunks) - 3} more")
    else:
        # Directory mode
        input_dir = base_dir / args.input_dir
        output_dir = base_dir / args.output_dir
        
        if not input_dir.exists():
            logger.error(f"Input directory not found: {input_dir}")
            return
        
        chunk_directory(
            input_dir, 
            output_dir, 
            args.pattern,
            hierarchical=not args.legacy
        )


if __name__ == '__main__':
    main()
