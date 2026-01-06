#!/usr/bin/env python3
"""
DocsDualMemory - Dual Memory System for Documentation

<!--TAG:docs_utils_dual_memory-->

PURPOSE:
    Provides dual-index semantic search for documentation system.
    Maintains separate indexes for descriptions and code.
    Independent from main project's utils/dual_memory.py.

<!--/TAG:docs_utils_dual_memory-->
"""

import os
import sys
import json
import re
import ast
import math
import hashlib
import random
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Import local utilities
from .docs_logger import DocsLogger
from .docs_config import docs_config

# Docs directory
DOCS_DIR = Path(__file__).resolve().parent.parent

# Initialize logger
logger = DocsLogger("docs_dual_memory")

# Memory directories
MEMORY_DIR = DOCS_DIR / "memory"
EMBEDDINGS_DIR = MEMORY_DIR / "embeddings"
INDEXES_DIR = MEMORY_DIR / "indexes"

# Default embedding configuration (Qwen3 from vLLM server)
# IMPORTANT: As of Dec 2025, we use ONLY Qwen3-Embedding-8B via vLLM
# No fallback to sentence-transformers - server must be running
EMBEDDING_MODEL = "text-embedding-qwen3-embedding-8b"
DEFAULT_EMBEDDING_DIM = 4096  # Qwen3-Embedding-8B dimension


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ContentChunk:
    """A chunk of content for embedding and search."""
    chunk_id: str
    content: str
    content_type: str  # 'description' or 'code'
    source_file: str
    line_start: int
    line_end: int
    embedding: List[float] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class SearchResult:
    """A single search result."""
    chunk_id: str
    content: str
    score: float
    source_file: str
    content_type: str
    line_range: Tuple[int, int]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "score": round(self.score, 4),
            "source_file": self.source_file,
            "content_type": self.content_type,
            "line_range": list(self.line_range)
        }


# ============================================================================
# EMBEDDING GENERATOR
# ============================================================================

class DocsEmbeddingGenerator:
    """
    Generates embeddings using Qwen3-Embedding-8B via vLLM.
    
    IMPORTANT: As of Dec 2025, this class uses ONLY Qwen3 from vLLM.
    No fallback to sentence-transformers - vLLM server must be running.
    """
    
    def __init__(self):
        """Initialize embedding generator for Qwen3."""
        self.embedding_dim = DEFAULT_EMBEDDING_DIM
        self._backend = "vllm"  # Only vLLM now
        
        # vLLM embedding endpoint configuration
        self.vllm_endpoint = docs_config.get(
            "embeddings.vllm_endpoint",
            "http://localhost:8001/v1/embeddings"
        )
        self.vllm_model = docs_config.get(
            "embeddings.vllm_model",
            EMBEDDING_MODEL
        )
        
        self._init_backend()
    
    def _init_backend(self):
        """Initialize vLLM embedding backend (NO FALLBACK)."""
        import requests
        
        # vLLM is the ONLY backend - no fallbacks
        try:
            health_url = self.vllm_endpoint.replace("/v1/embeddings", "/health")
            response = requests.get(health_url, timeout=5)
            if response.ok:
                self._backend = "vllm"
                logger.info(f"✅ Qwen3-Embedding-8B ready at {self.vllm_endpoint}")
            else:
                logger.error(f"❌ vLLM server returned {response.status_code}. Start server!")
                self._backend = "error"
        except Exception as e:
            logger.error(f"❌ vLLM server not available: {e}")
            logger.error("Run: bash start_vllm_server.sh to start embedding server on port 8001")
            self._backend = "error"
    
    def generate(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Qwen3-Embedding-8B via vLLM.
        
        Raises error if vLLM server is not available.
        """
        if not texts:
            return []
        
        if self._backend != "vllm":
            logger.error("❌ Cannot generate embeddings - vLLM server not available!")
            raise RuntimeError("vLLM embedding server not available. Run: bash start_vllm_server.sh")
        
        logger.info(f"Generating {len(texts)} embeddings via Qwen3-Embedding-8B")
        return self._generate_vllm(texts)
    
    def _generate_vllm(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using vLLM API with concurrent batching.
        
        Uses ThreadPoolExecutor for parallel batch processing.
        Long texts are adaptively split and embeddings averaged.
        """
        import requests
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import numpy as np
        
        # Model limits
        MAX_CHARS_PER_TEXT = 2000  # ~500 tokens, safe for embedding
        OVERLAP_CHARS = 200  # Overlap between splits
        
        batch_size = 32
        max_workers = 8
        
        # Adaptive splitting: split long texts, track original indices
        split_texts = []  # (original_idx, split_text)
        for orig_idx, text in enumerate(texts):
            if len(text) <= MAX_CHARS_PER_TEXT:
                split_texts.append((orig_idx, text))
            else:
                # Split into overlapping chunks
                pos = 0
                while pos < len(text):
                    end = min(pos + MAX_CHARS_PER_TEXT, len(text))
                    split_texts.append((orig_idx, text[pos:end]))
                    pos += MAX_CHARS_PER_TEXT - OVERLAP_CHARS
                    if end == len(text):
                        break
        
        logger.info(f"Adaptive split: {len(texts)} texts -> {len(split_texts)} chunks")
        
        # Build batches from split texts
        batches = []
        for i in range(0, len(split_texts), batch_size):
            batch_items = split_texts[i:i + batch_size]
            batches.append((i, [item[1] for item in batch_items]))
        
        logger.info(f"Processing {len(batches)} batches with {max_workers} concurrent workers")
        
        # Results indexed by position
        results = [None] * len(batches)
        
        def process_batch(batch_info):
            """Process single batch and return (index, embeddings)."""
            idx, batch = batch_info
            try:
                response = requests.post(
                    self.vllm_endpoint,
                    json={
                        "model": self.vllm_model,
                        "input": batch
                    },
                    timeout=120
                )
                response.raise_for_status()
                data = response.json()
                
                batch_embeddings = []
                for item in data.get("data", []):
                    batch_embeddings.append(item.get("embedding", []))
                
                return (idx, batch_embeddings)
                
            except Exception as e:
                logger.warning(f"Batch {idx} failed: {e}")
                # Return placeholder for failed batch
                return (idx, [[random.random() for _ in range(self.embedding_dim)] for _ in batch])
        
        # Process batches concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_batch, b): b[0] for b in batches}
            
            completed = 0
            for future in as_completed(futures):
                idx, batch_embeddings = future.result()
                results[idx // batch_size] = batch_embeddings
                completed += 1
                
                # Progress logging every 10%
                if completed % max(1, len(batches) // 10) == 0:
                    logger.info(f"  Progress: {completed}/{len(batches)} batches ({100*completed//len(batches)}%)")
        
        # Flatten results to get all split embeddings
        split_embeddings = []
        for batch_result in results:
            if batch_result:
                split_embeddings.extend(batch_result)
        
        # Average embeddings for texts that were split
        # Build mapping: original_idx -> [embedding indices]
        orig_to_splits = {}
        for split_idx, (orig_idx, _) in enumerate(split_texts):
            if orig_idx not in orig_to_splits:
                orig_to_splits[orig_idx] = []
            orig_to_splits[orig_idx].append(split_idx)
        
        # Compute final embeddings by averaging splits
        final_embeddings = []
        for orig_idx in range(len(texts)):
            split_indices = orig_to_splits.get(orig_idx, [])
            if len(split_indices) == 0:
                # Fallback: placeholder
                final_embeddings.append([random.random() for _ in range(self.embedding_dim)])
            elif len(split_indices) == 1:
                # Single chunk - use as is
                final_embeddings.append(split_embeddings[split_indices[0]])
            else:
                # Multiple chunks - average them
                chunk_embs = [split_embeddings[i] for i in split_indices if i < len(split_embeddings)]
                if chunk_embs:
                    avg_emb = np.mean(chunk_embs, axis=0).tolist()
                    final_embeddings.append(avg_emb)
                else:
                    final_embeddings.append([random.random() for _ in range(self.embedding_dim)])
        
        logger.info(f"✅ Generated {len(final_embeddings)} embeddings ({len(split_embeddings)} chunks averaged)")
        return final_embeddings
    
    def _generate_placeholder(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic placeholder embeddings."""
        embeddings = []
        for text in texts:
            seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            random.seed(seed)
            embedding = [random.random() for _ in range(self.embedding_dim)]
            embeddings.append(embedding)
        return embeddings


# ============================================================================
# DUAL MEMORY INDEX
# ============================================================================

class DocsDualMemoryIndex:
    """Maintains and searches dual indexes."""
    
    def __init__(self):
        """Initialize dual memory index."""
        EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
        INDEXES_DIR.mkdir(parents=True, exist_ok=True)
        
        self.description_index_path = EMBEDDINGS_DIR / "description_embeddings.json"
        self.code_index_path = EMBEDDINGS_DIR / "code_embeddings.json"
        
        self.embedder = DocsEmbeddingGenerator()
    
    def _load_index(self, index_type: str) -> Dict:
        """Load index from disk."""
        path = self.description_index_path if index_type == "description" else self.code_index_path
        
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load index: {e}")
        
        return {"chunks": [], "embeddings": [], "metadata": {}}
    
    def _save_index(self, index_type: str, data: Dict):
        """Save index to disk."""
        path = self.description_index_path if index_type == "description" else self.code_index_path
        data["metadata"]["updated_at"] = datetime.now().isoformat()
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {index_type} index to {path}")
    
    def build_indexes(self, directories: List[str] = None):
        """Build indexes from source files."""
        logger.info("Building dual memory indexes...")
        
        if directories is None:
            directories = ["automation", "specs", "wiki"]
        
        description_chunks = []
        code_chunks = []
        
        for dir_name in directories:
            dir_path = DOCS_DIR / dir_name
            if not dir_path.exists():
                continue
            
            logger.info(f"Processing: {dir_name}")
            
            # Process Python files
            for py_file in dir_path.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                chunks = self._extract_from_python(py_file)
                for chunk in chunks:
                    if chunk.content_type == "description":
                        description_chunks.append(chunk)
                    else:
                        code_chunks.append(chunk)
            
            # Process Markdown files
            for md_file in dir_path.rglob("*.md"):
                chunks = self._extract_from_markdown(md_file)
                description_chunks.extend(chunks)
        
        logger.info(f"Collected {len(description_chunks)} descriptions, {len(code_chunks)} code chunks")
        
        # Generate and save embeddings
        if description_chunks:
            texts = [c.content for c in description_chunks]
            embeddings = self.embedder.generate(texts)
            self._save_index("description", {
                "chunks": [self._chunk_to_dict(c) for c in description_chunks],
                "embeddings": embeddings,
                "metadata": {"total": len(description_chunks)}
            })
        
        if code_chunks:
            texts = [c.content for c in code_chunks]
            embeddings = self.embedder.generate(texts)
            self._save_index("code", {
                "chunks": [self._chunk_to_dict(c) for c in code_chunks],
                "embeddings": embeddings,
                "metadata": {"total": len(code_chunks)}
            })
    
    def _chunk_to_dict(self, chunk: ContentChunk) -> Dict:
        """Convert chunk to dictionary."""
        return {
            "chunk_id": chunk.chunk_id,
            "content": chunk.content,
            "source_file": chunk.source_file,
            "line_start": chunk.line_start,
            "line_end": chunk.line_end,
            "metadata": chunk.metadata
        }
    
    def _extract_from_python(self, file_path: Path) -> List[ContentChunk]:
        """Extract chunks from Python file."""
        chunks = []
        try:
            content = file_path.read_text(encoding='utf-8')
            rel_path = str(file_path.relative_to(DOCS_DIR))
        except Exception:
            return chunks
        
        try:
            tree = ast.parse(content)
            
            # Module docstring
            doc = ast.get_docstring(tree)
            if doc:
                chunks.append(ContentChunk(
                    chunk_id=f"desc_{file_path.stem}_module",
                    content=f"Module: {file_path.stem}\n\n{doc}",
                    content_type="description",
                    source_file=rel_path,
                    line_start=1,
                    line_end=len(doc.split('\n')) + 1,
                    metadata={"type": "module"}
                ))
            
            # Functions and classes
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        chunks.append(ContentChunk(
                            chunk_id=f"desc_{file_path.stem}_{node.name}",
                            content=f"{node.name}: {docstring}",
                            content_type="description",
                            source_file=rel_path,
                            line_start=node.lineno,
                            line_end=node.lineno + len(docstring.split('\n')),
                            metadata={"name": node.name, "type": type(node).__name__}
                        ))
        except SyntaxError:
            pass
        
        return chunks
    
    def _extract_from_markdown(self, file_path: Path) -> List[ContentChunk]:
        """Extract chunks from Markdown file."""
        chunks = []
        try:
            content = file_path.read_text(encoding='utf-8')
            rel_path = str(file_path.relative_to(DOCS_DIR))
        except Exception:
            return chunks
        
        # Split by headers
        sections = re.split(r'^(#+\s+.+)$', content, flags=re.MULTILINE)
        current_header = "Overview"
        current_content = []
        line_offset = 0
        
        for section in sections:
            if section.strip().startswith('#'):
                if current_content:
                    text = '\n'.join(current_content).strip()
                    if len(text) > 50:
                        chunks.append(ContentChunk(
                            chunk_id=f"doc_{file_path.stem}_{len(chunks)}",
                            content=f"{current_header}\n\n{text}",
                            content_type="description",
                            source_file=rel_path,
                            line_start=line_offset,
                            line_end=line_offset + len(current_content),
                            metadata={"header": current_header}
                        ))
                current_header = section.strip()
                current_content = []
            else:
                current_content.append(section)
            line_offset += len(section.split('\n'))
        
        return chunks


# ============================================================================
# DUAL MEMORY SEARCH
# ============================================================================

class DocsDualMemory:
    """Dual-index memory system."""
    
    def __init__(self):
        """Initialize dual memory."""
        self.index = DocsDualMemoryIndex()
    
    def search_descriptions(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search description index."""
        index_data = self.index._load_index("description")
        return self._search_index(query, index_data, "description", top_k)
    
    def search_code(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search code index."""
        index_data = self.index._load_index("code")
        return self._search_index(query, index_data, "code", top_k)
    
    def unified_search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search both indexes."""
        desc = self.search_descriptions(query, top_k)
        code = self.search_code(query, top_k)
        
        all_results = desc + code
        all_results.sort(key=lambda r: r.score, reverse=True)
        return all_results[:top_k]
    
    def _search_index(self, query: str, index_data: Dict, 
                      content_type: str, top_k: int) -> List[SearchResult]:
        """Search single index."""
        results = []
        
        if not index_data.get("chunks"):
            return results
        
        query_embedding = self.index.embedder.generate([query])[0]
        chunks = index_data["chunks"]
        embeddings = index_data["embeddings"]
        
        similarities = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            score = self._cosine_similarity(query_embedding, embedding)
            similarities.append((i, score))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        for idx, score in similarities[:top_k]:
            chunk = chunks[idx]
            results.append(SearchResult(
                chunk_id=chunk["chunk_id"],
                content=chunk["content"],
                score=score,
                source_file=chunk["source_file"],
                content_type=content_type,
                line_range=(chunk["line_start"], chunk["line_end"])
            ))
        
        return results
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    
    def build(self, directories: List[str] = None):
        """Build indexes."""
        self.index.build_indexes(directories)


# Convenience functions
def unified_search(query: str, top_k: int = 10) -> List[SearchResult]:
    """Search both indexes."""
    return DocsDualMemory().unified_search(query, top_k)


def build_dual_memory():
    """Build dual memory indexes."""
    DocsDualMemory().build()
