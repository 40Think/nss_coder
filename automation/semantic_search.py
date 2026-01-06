#!/usr/bin/env python3
"""
Unified Semantic Search - Integration with dual_memory.py

<!--TAG:tool_semantic_search-->

PURPOSE:
    Unified search interface that:
    1. Uses dual_memory.py for semantic search (embeddings-based)
    2. Falls back to keyword search when semantic unavailable
    3. Supports hybrid mode combining both methods

DOCUMENTATION:
    Spec: docs/specs/Automation_Tools_Spec.md
    Wiki: docs/wiki/09_Documentation_System.md
    Technical Debt: docs/technical_debt/semantic_search_gaps.md
    Dependencies: docs/memory/dependencies/semantic_search_dependencies.json

SEARCH MODES:
    - auto: Use semantic if available, else keyword
    - semantic: Force semantic search (dual_memory)
    - keyword: Force keyword-based search
    - hybrid: Combine both using Reciprocal Rank Fusion

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger.DocsLogger (paranoid logging)
        - docs.utils.docs_dual_memory.DocsDualMemory (optional, semantic search)
    Config:
        - docs/config/docs_config.yaml (via DocsLogger)
    Data:
        - Input: docs/*.md, project/**/*.py (read-only search)
        - Output: stdout or --output file
    External:
        - OpenAI API (for embeddings, via DocsDualMemory)

RECENT CHANGES:
    2025-12-13: Added parent-child context expansion (--expand-context)
                Loads hierarchical chunk index for context retrieval
    2025-12-11: Migrated to isolated docs utilities (docs.utils.*)
    2025-12-11: Added hybrid search with RRF fusion
    2025-12-12: Documentation audit and compliance updates

TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:search--> <!--TAG:automation--> <!--TAG:search--> <!--TAG:semantic-->

<!--/TAG:tool_semantic_search-->
"""

import os  # Operating system interface
import re  # Regular expressions
import json  # JSON serialization
import argparse  # Command line argument parsing
from pathlib import Path  # Object-oriented filesystem paths
from typing import List, Dict, Any, Optional, Tuple  # Type hints
from dataclasses import dataclass, field  # Structured data classes
import sys  # System-specific parameters

# Add project root to path for imports
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.docs_logger import DocsLogger  # Paranoid logging

# Initialize logger
logger = DocsLogger("semantic_search")

# Project root detection
PROJECT_ROOT = Path(__file__).parent.parent


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class SearchResult:
    """
    A search result with enhanced metadata.
    
    Fields:
        file_path: Relative path to the file
        score: Relevance score (0.0 - 1.0)
        excerpt: Matching content excerpt
        line_number: Line number of the match
        context: Surrounding context lines
        content_type: Type of content ('code', 'description', 'text')
        line_range: Start and end line numbers
        metadata: Additional metadata dict
        search_method: Method used ('semantic', 'keyword', 'hybrid')
    """
    file_path: str  # Relative path to file
    score: float  # Relevance score (0.0 - 1.0)
    excerpt: str  # Matching content
    line_number: int = 0  # Line number
    context: str = ""  # Surrounding context
    content_type: str = "unknown"  # 'code', 'description', 'text'
    line_range: Tuple[int, int] = (0, 0)  # (start_line, end_line)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata
    search_method: str = "keyword"  # 'semantic', 'keyword', 'hybrid'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "score": round(self.score, 4),
            "excerpt": self.excerpt[:200] + "..." if len(self.excerpt) > 200 else self.excerpt,
            "line_number": self.line_number,
            "content_type": self.content_type,
            "line_range": list(self.line_range),
            "search_method": self.search_method,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dual_memory_result(cls, result: Any) -> 'SearchResult':
        """Create SearchResult from dual_memory result."""
        # Handle both dict and object formats
        if hasattr(result, 'source_file'):
            # Object format from DualMemory
            return cls(
                file_path=getattr(result, 'source_file', ''),
                score=getattr(result, 'score', 0.0),
                excerpt=getattr(result, 'content', '')[:200],
                line_number=getattr(result, 'line_range', (0, 0))[0],
                content_type=getattr(result, 'content_type', 'unknown'),
                line_range=getattr(result, 'line_range', (0, 0)),
                metadata={'chunk_id': getattr(result, 'chunk_id', '')},
                search_method='semantic'
            )
        else:
            # Dict format
            return cls(
                file_path=result.get('source_file', ''),
                score=result.get('score', 0.0),
                excerpt=result.get('content', '')[:200],
                line_number=result.get('line_range', (0, 0))[0] if result.get('line_range') else 0,
                content_type=result.get('content_type', 'unknown'),
                line_range=tuple(result.get('line_range', (0, 0))),
                metadata=result.get('metadata', {}),
                search_method='semantic'
            )


# ============================================================================
# SIMPLE KEYWORD SEARCHER (Fallback)
# ============================================================================

class SimpleKeywordSearcher:
    """
    Simple keyword-based search (fallback when semantic unavailable).
    
    Uses basic keyword matching with stop word filtering.
    """
    
    def __init__(self, project_root: Path):
        """Initialize keyword searcher."""
        self.project_root = project_root
        self.docs_dir = project_root / 'docs'
        
        # Stop words to filter out
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are',
            'was', 'were', 'how', 'what', 'where', 'when', 'why', 'does',
            'can', 'could', 'would', 'should', 'not', 'no', 'yes'
        }
    
    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Search documentation using keyword matching.
        
        Args:
            query: Search query string
            top_k: Maximum number of results
            
        Returns:
            List of SearchResult objects
        """
        keywords = self._extract_keywords(query)
        
        if not keywords:
            logger.warning(f"No keywords extracted from query: {query}")
            return []
        
        results = []
        
        # Search in docs directory
        for doc_file in self.docs_dir.rglob('*.md'):
            if '__pycache__' in str(doc_file):
                continue
            file_results = self._search_file(doc_file, keywords)
            results.extend(file_results)
        
        # Also search Python files
        for py_file in self.project_root.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            if 'venv' in str(py_file) or 'site-packages' in str(py_file):
                continue
            file_results = self._search_file(py_file, keywords)
            results.extend(file_results)
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        # Mark as keyword search
        for result in results:
            result.search_method = 'keyword'
        
        logger.info(f"Keyword search for '{query}' found {len(results)} total matches")
        return results[:top_k]
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query, removing stop words."""
        words = query.lower().split()
        keywords = [
            w for w in words 
            if w not in self.stop_words and len(w) > 2
        ]
        return keywords
    
    def _search_file(self, file_path: Path, keywords: List[str]) -> List[SearchResult]:
        """Search a single file for keywords."""
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()
                matches = sum(1 for kw in keywords if kw in line_lower)
                
                if matches > 0:
                    score = matches / len(keywords)
                    
                    # Extract context (3 lines before and after)
                    context_start = max(0, line_num - 3)
                    context_end = min(len(lines), line_num + 2)
                    context = ''.join(lines[context_start:context_end])
                    
                    # Determine content type
                    content_type = 'description' if file_path.suffix == '.md' else 'code'
                    
                    results.append(SearchResult(
                        file_path=str(file_path.relative_to(self.project_root)),
                        score=score,
                        excerpt=line.strip(),
                        line_number=line_num,
                        context=context,
                        content_type=content_type,
                        line_range=(line_num, line_num),
                        metadata={'keyword_matches': matches, 'total_keywords': len(keywords)}
                    ))
        
        except Exception as e:
            logger.debug(f"Error searching {file_path}: {e}")
        
        return results


# ============================================================================
# UNIFIED SEARCHER
# ============================================================================

class UnifiedSearcher:
    """
    Unified search interface with dual_memory + keyword fallback.
    
    Provides:
    - Semantic search using dual_memory.py (embeddings-based)
    - Keyword fallback when semantic unavailable
    - Hybrid mode combining both with RRF fusion
    """
    
    def __init__(self, project_root: Path = None):
        """
        Initialize unified searcher.
        
        Args:
            project_root: Path to project root (auto-detected if None)
        """
        self.project_root = project_root or PROJECT_ROOT
        self.docs_dir = self.project_root / 'docs'
        
        # Try to initialize dual_memory for semantic search
        self.dual_memory = None
        self.has_semantic = False
        
        try:
            from utils.docs_dual_memory import DocsDualMemory
            self.dual_memory = DocsDualMemory()
            self.has_semantic = True
            logger.info("✅ Semantic search available (dual_memory)")
        except ImportError as e:
            logger.warning(f"⚠️ dual_memory not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ dual_memory initialization failed: {e}")
        
        # Keyword searcher always available as fallback
        self.keyword_searcher = SimpleKeywordSearcher(self.project_root)
        logger.info("✅ Keyword search available (fallback)")
    
    def search(
        self, 
        query: str, 
        mode: str = 'auto', 
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Unified search interface.
        
        Args:
            query: Search query string
            mode: Search mode ('auto', 'semantic', 'keyword', 'hybrid')
            top_k: Maximum number of results
            
        Returns:
            List of SearchResult objects
        """
        logger.info(f"Search: query='{query}', mode={mode}, top_k={top_k}")
        
        if mode == 'auto':
            # Auto-select: use semantic if available, else keyword
            if self.has_semantic:
                return self._semantic_search(query, top_k)
            else:
                return self._keyword_search(query, top_k)
        
        elif mode == 'semantic':
            if not self.has_semantic:
                logger.error("Semantic search not available, use 'keyword' or 'auto' mode")
                return []
            return self._semantic_search(query, top_k)
        
        elif mode == 'keyword':
            return self._keyword_search(query, top_k)
        
        elif mode == 'hybrid':
            if not self.has_semantic:
                logger.warning("Hybrid mode requires semantic search, falling back to keyword")
                return self._keyword_search(query, top_k)
            return self._hybrid_search(query, top_k)
        
        else:
            raise ValueError(f"Unknown search mode: {mode}")
    
    def _semantic_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Perform semantic search using dual_memory."""
        logger.info(f"Performing semantic search for: {query}")
        
        try:
            # Use dual_memory unified search
            results = self.dual_memory.unified_search(query, top_k=top_k)
            
            # Convert to SearchResult format
            search_results = []
            for result in results:
                search_results.append(
                    SearchResult.from_dual_memory_result(result)
                )
            
            logger.info(f"Semantic search found {len(search_results)} results")
            return search_results
        
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            logger.info("Falling back to keyword search")
            return self._keyword_search(query, top_k)
    
    def _keyword_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Perform keyword-based search."""
        logger.info(f"Performing keyword search for: {query}")
        return self.keyword_searcher.search(query, top_k)
    
    def _hybrid_search(self, query: str, top_k: int) -> List[SearchResult]:
        """
        Hybrid search: combine semantic and keyword using RRF.
        
        Reciprocal Rank Fusion (RRF) effectively merges ranked lists
        from different retrieval methods.
        """
        logger.info(f"Performing hybrid search for: {query}")
        
        # Get results from both methods (fetch more for better fusion)
        semantic_results = self._semantic_search(query, top_k * 2)
        keyword_results = self._keyword_search(query, top_k * 2)
        
        # Apply Reciprocal Rank Fusion
        combined = self._reciprocal_rank_fusion(
            [semantic_results, keyword_results],
            k=60  # RRF constant
        )
        
        # Mark as hybrid
        for result in combined:
            result.search_method = 'hybrid'
        
        logger.info(f"Hybrid search produced {len(combined[:top_k])} results")
        return combined[:top_k]
    
    def _reciprocal_rank_fusion(
        self, 
        result_lists: List[List[SearchResult]], 
        k: int = 60
    ) -> List[SearchResult]:
        """
        Combine multiple result lists using Reciprocal Rank Fusion.
        
        RRF formula: score = sum(1 / (k + rank)) for each list
        
        Args:
            result_lists: List of result lists to combine
            k: RRF constant (typically 60)
            
        Returns:
            Combined and re-ranked results
        """
        rrf_scores: Dict[str, Dict] = {}
        
        for results in result_lists:
            for rank, result in enumerate(results):
                # Use file_path + line_number as unique key
                key = f"{result.file_path}:{result.line_number}"
                
                if key not in rrf_scores:
                    rrf_scores[key] = {
                        'result': result,
                        'score': 0.0,
                        'sources': []
                    }
                
                # RRF score contribution: 1 / (k + rank + 1)
                rrf_scores[key]['score'] += 1.0 / (k + rank + 1)
                rrf_scores[key]['sources'].append(result.search_method)
        
        # Sort by RRF score
        sorted_results = sorted(
            rrf_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        # Build final results with updated scores
        final_results = []
        for item in sorted_results:
            result = item['result']
            result.score = item['score']
            result.metadata['rrf_sources'] = item['sources']
            final_results.append(result)
        
        return final_results
    
    def get_status(self) -> Dict[str, Any]:
        """Get search system status."""
        return {
            'semantic_available': self.has_semantic,
            'keyword_available': True,
            'project_root': str(self.project_root),
            'docs_dir': str(self.docs_dir)
        }
    
    # ========================================================================
    # PARENT-CHILD CONTEXT EXPANSION (Dec 2025 Best Practice)
    # ========================================================================
    
    def expand_context(
        self, 
        results: List[SearchResult],
        chunk_index: Dict[str, Any] = None
    ) -> List[SearchResult]:
        """
        Expand search results with parent chunk context.
        
        Dec 2025 best practice: For CLAUSE-level matches, include parent
        SECTION content to provide richer context to LLM.
        
        This is OPTIONAL and must be explicitly enabled via --expand-context.
        Does NOT affect existing workflows (assemble_context.py, etc.)
        
        Args:
            results: Search results to expand
            chunk_index: Pre-loaded chunk index (loads if None)
            
        Returns:
            Results with expanded context in metadata
        """
        if not chunk_index:
            chunk_index = self._load_chunk_index()
        
        if not chunk_index:
            logger.warning("⚠️ Chunk index not available, skipping context expansion")
            return results
        
        expanded_results = []
        
        for result in results:
            # Try to find parent context
            chunk_id = result.metadata.get('chunk_id', '')
            
            if chunk_id and chunk_id in chunk_index:
                chunk_data = chunk_index[chunk_id]
                parent_id = chunk_data.get('parent_id')
                
                if parent_id and parent_id in chunk_index:
                    parent_chunk = chunk_index[parent_id]
                    parent_content = parent_chunk.get('content', '')
                    
                    # Add parent context to metadata
                    result.metadata['parent_context'] = parent_content[:500]  # Limit size
                    result.metadata['parent_id'] = parent_id
                    result.metadata['parent_layer'] = parent_chunk.get('layer', 'unknown')
                    
                    logger.debug(f"Expanded context for {chunk_id} with parent {parent_id}")
            
            expanded_results.append(result)
        
        logger.info(f"Expanded context for {len(expanded_results)} results")
        return expanded_results
    
    def _load_chunk_index(self) -> Dict[str, Any]:
        """
        Load hierarchical chunk index for context expansion.
        
        Loads from chunk_documents.py output file.
        Returns empty dict if file not found.
        """
        # Try multiple possible locations for chunk index
        possible_paths = [
            self.docs_dir / 'memory' / 'chunks' / 'chunks_index_all.json',
            self.docs_dir / 'memory' / 'chunks' / 'chunks_index_sections.json',
            self.docs_dir / 'memory' / 'chunks_index.json',
        ]
        
        for index_path in possible_paths:
            if index_path.exists():
                try:
                    with open(index_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Build lookup by chunk_id
                    chunk_index = {}
                    
                    # Handle both list and dict formats
                    if isinstance(data, list):
                        for chunk in data:
                            chunk_id = chunk.get('chunk_id')
                            if chunk_id:
                                chunk_index[chunk_id] = chunk
                    elif isinstance(data, dict):
                        # Could be already indexed by chunk_id
                        if all(isinstance(v, dict) for v in data.values()):
                            chunk_index = data
                        else:
                            # Nested structure by layer
                            for layer, chunks in data.items():
                                if isinstance(chunks, list):
                                    for chunk in chunks:
                                        chunk_id = chunk.get('chunk_id')
                                        if chunk_id:
                                            chunk_index[chunk_id] = chunk
                    
                    logger.info(f"✅ Loaded chunk index: {len(chunk_index)} chunks from {index_path.name}")
                    return chunk_index
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load {index_path}: {e}")
        
        logger.warning("⚠️ No chunk index found, context expansion unavailable")
        return {}
    
    def get_neighbors(
        self, 
        chunk_id: str, 
        n: int = 2,
        chunk_index: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Get N neighboring chunks (before and after) for seamless reading.
        
        Dec 2025 best practice: When user views a matched chunk, also
        provide surrounding context for continuous comprehension.
        
        Args:
            chunk_id: ID of the center chunk
            n: Number of neighbors to get on each side (default: 2)
            chunk_index: Pre-loaded chunk index
            
        Returns:
            List of neighbor chunks: [prev_n, ..., prev_1, CENTER, next_1, ..., next_n]
        """
        if not chunk_index:
            chunk_index = self._load_chunk_index()
        
        if not chunk_index or chunk_id not in chunk_index:
            logger.warning(f"⚠️ Cannot find neighbors for {chunk_id}")
            return []
        
        center_chunk = chunk_index[chunk_id]
        source_file = center_chunk.get('metadata', {}).get('file_path', '')
        
        # Get all chunks from the same file
        same_file_chunks = []
        for cid, chunk in chunk_index.items():
            chunk_file = chunk.get('metadata', {}).get('file_path', '')
            if chunk_file == source_file:
                same_file_chunks.append((cid, chunk))
        
        # Sort by position in file (using chunk_id pattern or line_range)
        def get_position(item):
            cid, chunk = item
            # Try to parse position from chunk_id or use line_start
            metadata = chunk.get('metadata', {})
            return metadata.get('line_start', 0) or 0
        
        same_file_chunks.sort(key=get_position)
        
        # Find center chunk index
        center_idx = -1
        for i, (cid, _) in enumerate(same_file_chunks):
            if cid == chunk_id:
                center_idx = i
                break
        
        if center_idx == -1:
            return [center_chunk]
        
        # Get neighbors
        start_idx = max(0, center_idx - n)
        end_idx = min(len(same_file_chunks), center_idx + n + 1)
        
        neighbors = []
        for i in range(start_idx, end_idx):
            cid, chunk = same_file_chunks[i]
            chunk['is_center'] = (i == center_idx)
            neighbors.append(chunk)
        
        logger.info(f"Retrieved {len(neighbors)} chunks around {chunk_id}")
        return neighbors


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Unified semantic search for documentation and code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Auto mode (uses semantic if available)
    python3 semantic_search.py "embedding generation"
    
    # Force semantic search
    python3 semantic_search.py "memory system" --mode semantic
    
    # Keyword-only search
    python3 semantic_search.py "analytics pipeline" --mode keyword
    
    # Hybrid search (combines both)
    python3 semantic_search.py "dual memory" --mode hybrid
    
    # JSON output
    python3 semantic_search.py "search" --format json
        """
    )
    
    # Positional argument for query
    parser.add_argument(
        'query', 
        type=str, 
        nargs='?',
        help='Search query'
    )
    
    # Alternative: --query flag (for backward compatibility)
    parser.add_argument(
        '--query', '-q',
        type=str,
        dest='query_flag',
        help='Search query (alternative to positional argument)'
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['auto', 'semantic', 'keyword', 'hybrid'],
        default='auto',
        help='Search mode (default: auto)'
    )
    
    parser.add_argument(
        '--top-k', '-k',
        type=int,
        default=10,
        help='Number of results (default: 10)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--show-context', '-c',
        action='store_true',
        help='Show surrounding context'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Save results to file'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show search system status'
    )
    
    parser.add_argument(
        '--expand-context', '-e',
        action='store_true',
        help='Expand results with parent chunk context (Dec 2025 best practice)'
    )
    
    args = parser.parse_args()
    
    # Initialize searcher
    searcher = UnifiedSearcher()
    
    # Handle --status
    if args.status:
        status = searcher.get_status()
        print(json.dumps(status, indent=2))
        return
    
    # Get query from positional or flag
    query = args.query or args.query_flag
    
    if not query:
        parser.print_help()
        return
    
    # Perform search
    results = searcher.search(query, mode=args.mode, top_k=args.top_k)
    
    if not results:
        logger.warning(f"No results found for: {query}")
        if args.format == 'json':
            print(json.dumps({
                "query": query,
                "mode": args.mode,
                "total_results": 0,
                "results": []
            }, indent=2))
        else:
            print(f"\n❌ No results found for: '{query}'")
        return
    
    # Optionally expand context with parent chunks
    if args.expand_context:
        results = searcher.expand_context(results)
    
    # Format output
    if args.format == 'json':
        output = {
            "query": query,
            "mode": args.mode,
            "total_results": len(results),
            "semantic_available": searcher.has_semantic,
            "results": [r.to_dict() for r in results]
        }
        output_text = json.dumps(output, indent=2, ensure_ascii=False)
    else:
        # Text format
        lines = []
        lines.append(f"\n🔍 Search Results for: '{query}'")
        lines.append(f"Mode: {args.mode} | Found: {len(results)} results")
        
        if searcher.has_semantic:
            lines.append("✅ Semantic search available")
        else:
            lines.append("⚠️ Using keyword fallback (semantic unavailable)")
        
        lines.append("=" * 60)
        
        for i, result in enumerate(results, 1):
            method_icon = {
                'semantic': '🧠',
                'keyword': '🔤',
                'hybrid': '🔀'
            }.get(result.search_method, '❓')
            
            lines.append(f"\n{i}. [{method_icon}] {result.file_path}")
            lines.append(f"   Line {result.line_number} | Score: {result.score:.4f} | Type: {result.content_type}")
            lines.append("-" * 60)
            lines.append(f"   {result.excerpt[:100]}...")
            
            if args.show_context and result.context:
                lines.append("\n   [Context]")
                for ctx_line in result.context.split('\n')[:5]:
                    lines.append(f"   {ctx_line}")
            
            lines.append("")
        
        output_text = '\n'.join(lines)
    
    # Output
    if args.output:
        output_path = PROJECT_ROOT / args.output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_text)
        logger.info(f"Results saved to: {output_path}")
        print(f"✅ Results saved to: {output_path}")
    else:
        print(output_text)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def search(query: str, mode: str = 'auto', top_k: int = 10) -> List[SearchResult]:
    """
    Convenience function for programmatic use.
    
    Args:
        query: Search query string
        mode: Search mode ('auto', 'semantic', 'keyword', 'hybrid')
        top_k: Maximum number of results
        
    Returns:
        List of SearchResult objects
    """
    searcher = UnifiedSearcher()
    return searcher.search(query, mode=mode, top_k=top_k)


def search_semantic(query: str, top_k: int = 10) -> List[SearchResult]:
    """Convenience function for semantic search only."""
    return search(query, mode='semantic', top_k=top_k)


def search_keyword(query: str, top_k: int = 10) -> List[SearchResult]:
    """Convenience function for keyword search only."""
    return search(query, mode='keyword', top_k=top_k)


def search_hybrid(query: str, top_k: int = 10) -> List[SearchResult]:
    """Convenience function for hybrid search."""
    return search(query, mode='hybrid', top_k=top_k)


if __name__ == '__main__':
    main()
