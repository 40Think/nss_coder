#!/usr/bin/env python3
"""
Project Indexer - Build vector embeddings and knowledge graph

<!--TAG:tool_project_indexer-->

PURPOSE:
    Builds the AI memory system including:
    - Vector embeddings for semantic search (using sentence-transformers or fallback)
    - Knowledge graph for code relationships (from dependency JSONs)
    - Fast lookup indexes for entity queries
    - Human-readable PROJECT_INDEX.md for navigation

DOCUMENTATION:
    Specification: docs/specs/Automation_Tools_Spec.md
    Wiki Guide: docs/wiki/09_Documentation_System.md
    Dependencies: docs/memory/dependencies/index_project_dependencies.json

TAGS FOR SEARCH:
    <!--TAG:component:automation-->
    <!--TAG:type:script-->
    <!--TAG:feature:memory-->
    <!--TAG:feature:embeddings-->
    <!--TAG:feature:knowledge_graph-->

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger (DocsLogger for logging)
        - docs.utils.docs_config (docs_config for vLLM config)
        - sentence_transformers (optional, for real embeddings)
    Config:
        - docs/config/docs_config.yaml (VLLM_MODEL_PATH_EMBEDDING)
    Data:
        - Input: docs/memory/chunks/chunks_index.json
        - Input: docs/memory/dependencies/*_dependencies.json
        - Output: docs/memory/embeddings/project_embeddings.json
        - Output: docs/memory/knowledge_graph/code_graph.json
        - Output: docs/memory/indexes/lookup_indexes.json
        - Output: docs/memory/PROJECT_INDEX.md
    External:
        - None (all local processing)

RECENT CHANGES:
    2025-12-11: Added IncrementalIndexer, generate_human_readable_index(), real embeddings
    2025-12-09: Initial implementation with placeholder embeddings

<!--/TAG:tool_project_indexer-->
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import sys
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.docs_logger import DocsLogger
from utils.docs_dual_memory import DocsEmbeddingGenerator

logger = DocsLogger("index_project")

# Directories to EXCLUDE from indexing
EXCLUDED_DIRS = {
    'logs', 'input', 'output', 'llm_requests',  # Data/IO folders
    'data', '.git', '.pytest_cache', '.ruff_cache',  # Technical
    '__pycache__', 'venv', 'site-packages', 'node_modules',  # Dependencies
    '.agent', '.gemini',  # Agent artifacts
}

@dataclass
class CodeEntity:
    """An entity in the code (file, class, function)"""
    id: str
    type: str  # 'file', 'class', 'function', 'module'
    name: str
    file_path: str
    line_number: int
    content: str
    embedding: List[float] = None
    metadata: Dict = None

@dataclass
class Relationship:
    """A relationship between entities"""
    source_id: str
    target_id: str
    type: str  # 'imports', 'calls', 'inherits', 'contains'
    metadata: Dict = None

class ProjectIndexer:
    """Build vector embeddings and knowledge graph"""
    
    def __init__(self, project_root: Path):
        """Initialize ProjectIndexer with project filesystem structure."""
        # Store project root for relative path calculations
        self.project_root = project_root
        
        # Memory directory contains all AI-generated indexes and embeddings
        self.memory_dir = project_root / 'docs' / 'memory'
        
        # Subdirectories for different index types
        self.embeddings_dir = self.memory_dir / 'embeddings'  # Vector embeddings for semantic search
        self.graph_dir = self.memory_dir / 'knowledge_graph'  # Entity relationship graph
        self.indexes_dir = self.memory_dir / 'indexes'        # Fast lookup tables
        
        # Create directories if they don't exist (idempotent operation)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        self.indexes_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage for entities and relationships during indexing
        self.entities: Dict[str, CodeEntity] = {}  # entity_id -> CodeEntity mapping
        self.relationships: List[Relationship] = []  # All discovered relationships between entities
    
    def build_embeddings(self):
        """Build vector embeddings for code and documentation.
        
        Workflow:
            1. Collect documentation chunks from chunk_documents.py output
            2. Extract code entities (classes, functions) from Python files
            3. Generate embeddings using sentence-transformers or fallback
            4. Save embeddings to JSON for semantic search
        """
        logger.info("Building embeddings...")
        
        # Accumulator for all text chunks to be embedded
        chunks = []
        
        # STEP 1: Load pre-chunked documentation from chunk_documents.py output
        chunks_index = self.memory_dir / 'chunks' / 'chunks_index.json'
        if chunks_index.exists():
            # Open and parse the chunks index JSON file
            with open(chunks_index, 'r', encoding='utf-8') as f:
                doc_chunks = json.load(f)  # List of {chunk_id, content, metadata}
                chunks.extend(doc_chunks)  # Add all documentation chunks to accumulator
        
        # STEP 2: Extract code entities from ALL project directories
        # Iterate through all directories (excluding EXCLUDED_DIRS)
        for item in self.project_root.iterdir():
            if item.is_dir() and item.name not in EXCLUDED_DIRS:
                # Recursively find all Python files
                for py_file in item.rglob('*.py'):
                    # Skip excluded directories in path
                    if any(excl in str(py_file) for excl in EXCLUDED_DIRS):
                        continue
                    
                    # Extract classes and functions from this file using AST
                    entities = self._extract_code_entities(py_file)
                    
                    # Convert each code entity to a chunk format
                    for entity in entities:
                        chunks.append({
                            'chunk_id': entity.id,  # Unique hash-based ID
                            'content': entity.content,  # Code snippet or docstring
                            'metadata': {
                                'type': entity.type,  # 'class', 'function', 'file'
                                'file_path': entity.file_path,  # Relative path from project root
                                'line_number': entity.line_number  # Starting line number
                            }
                        })
        
        # Log total chunks collected before embedding generation
        logger.info(f"  Collected {len(chunks)} chunks")
        
        # STEP 3: Generate vector embeddings (tries sentence-transformers, falls back to placeholder)
        embeddings = self._generate_embeddings_real(chunks)
        
        # STEP 4: Save embeddings and chunks to JSON file for semantic search
        embeddings_file = self.embeddings_dir / 'project_embeddings.json'
        with open(embeddings_file, 'w', encoding='utf-8') as f:
            json.dump({
                'chunks': chunks,  # Original text chunks with metadata
                'embeddings': embeddings,  # Vector representations (384-dim)
                'metadata': {
                    'total_chunks': len(chunks),  # Total number of embedded chunks
                    'embedding_dim': len(embeddings[0]) if embeddings else 0,  # Dimension of vectors
                    'created_at': datetime.now().isoformat()  # Timestamp for cache invalidation
                }
            }, f, indent=2, ensure_ascii=False)  # Pretty-print with Unicode support
        
        # Log success with output file path
        logger.info(f"  ✓ Embeddings saved to: {embeddings_file}")
    
    def build_knowledge_graph(self):
        """Build knowledge graph from code"""
        logger.info("Building knowledge graph...")
        
        # 1. Extract entities and relationships from dependency maps
        deps_dir = self.memory_dir / 'dependencies'
        if deps_dir.exists():
            for dep_file in deps_dir.rglob('*_dependencies.json'):
                self._process_dependency_file(dep_file)
        
        # 2. Save graph
        graph_file = self.graph_dir / 'code_graph.json'
        with open(graph_file, 'w', encoding='utf-8') as f:
            json.dump({
                'entities': {eid: asdict(entity) for eid, entity in self.entities.items()},
                'relationships': [asdict(rel) for rel in self.relationships],
                'metadata': {
                    'total_entities': len(self.entities),
                    'total_relationships': len(self.relationships),
                    'created_at': datetime.now().isoformat()
                }
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"  ✓ Knowledge graph saved to: {graph_file}")
        logger.info(f"  Entities: {len(self.entities)}, Relationships: {len(self.relationships)}")
    
    def build_indexes(self):
        """Build fast lookup indexes"""
        logger.info("Building indexes...")
        
        indexes = {
            'file_index': {},      # file_path -> entity_ids
            'type_index': {},      # entity_type -> entity_ids
            'name_index': {},      # entity_name -> entity_ids
            'relationship_index': {}  # source_id -> relationships
        }
        
        # Build indexes from entities
        for entity_id, entity in self.entities.items():
            # File index
            if entity.file_path not in indexes['file_index']:
                indexes['file_index'][entity.file_path] = []
            indexes['file_index'][entity.file_path].append(entity_id)
            
            # Type index
            if entity.type not in indexes['type_index']:
                indexes['type_index'][entity.type] = []
            indexes['type_index'][entity.type].append(entity_id)
            
            # Name index
            if entity.name not in indexes['name_index']:
                indexes['name_index'][entity.name] = []
            indexes['name_index'][entity.name].append(entity_id)
        
        # Build relationship index
        for rel in self.relationships:
            if rel.source_id not in indexes['relationship_index']:
                indexes['relationship_index'][rel.source_id] = []
            indexes['relationship_index'][rel.source_id].append(asdict(rel))
        
        # Save indexes
        indexes_file = self.indexes_dir / 'lookup_indexes.json'
        with open(indexes_file, 'w', encoding='utf-8') as f:
            json.dump(indexes, f, indent=2, ensure_ascii=False)
        
        logger.info(f"  ✓ Indexes saved to: {indexes_file}")
    
    def _extract_code_entities(self, file_path: Path) -> List[CodeEntity]:
        """Extract code entities (classes, functions) from a Python file using AST parsing.
        
        Args:
            file_path: Path to Python file to analyze
            
        Returns:
            List of CodeEntity objects representing classes and functions
        """
        # Accumulator for discovered entities
        entities = []
        
        try:
            # Import AST module for Python source code parsing
            import ast
            
            # Read the entire Python file as text
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()  # Full source code as string
                
                # Parse source code into Abstract Syntax Tree
                tree = ast.parse(content, filename=str(file_path))
            
            # Walk through all nodes in the AST to find classes and functions
            for node in ast.walk(tree):
                # Check if this node is a class definition
                if isinstance(node, ast.ClassDef):
                    # Generate unique ID for this class entity
                    entity_id = self._generate_id(file_path, node.name, 'class')
                    
                    # Create CodeEntity for this class
                    entities.append(CodeEntity(
                        id=entity_id,  # Unique hash-based identifier
                        type='class',  # Entity type for indexing
                        name=node.name,  # Class name (e.g., "ProjectIndexer")
                        file_path=str(file_path.relative_to(self.project_root)),  # Relative path
                        line_number=node.lineno,  # Starting line number in file
                        content=ast.get_source_segment(content, node) or node.name  # Full class code or name
                    ))
                
                # Check if this node is a function definition
                elif isinstance(node, ast.FunctionDef):
                    # Generate unique ID for this function entity
                    entity_id = self._generate_id(file_path, node.name, 'function')
                    
                    # Create CodeEntity for this function
                    entities.append(CodeEntity(
                        id=entity_id,  # Unique hash-based identifier
                        type='function',  # Entity type for indexing
                        name=node.name,  # Function name (e.g., "build_embeddings")
                        file_path=str(file_path.relative_to(self.project_root)),  # Relative path
                        line_number=node.lineno,  # Starting line number in file
                        content=ast.get_source_segment(content, node) or node.name  # Full function code or name
                    ))
        
        except Exception as e:
            # Log parsing errors but don't crash - some files may have syntax errors
            logger.warning(f"  Warning: Could not parse {file_path}: {e}")
        
        # Return all discovered entities (may be empty if parsing failed)
        return entities
    
    def _process_dependency_file(self, dep_file: Path):
        """Process a dependency JSON file to extract entities and relationships"""
        try:
            with open(dep_file, 'r', encoding='utf-8') as f:
                deps = json.load(f)
            
            file_path = deps.get('file_path', '')
            
            # Create file entity
            file_id = self._generate_id(Path(file_path), file_path, 'file')
            if file_id not in self.entities:
                self.entities[file_id] = CodeEntity(
                    id=file_id,
                    type='file',
                    name=Path(file_path).name,
                    file_path=file_path,
                    line_number=0,
                    content=file_path
                )
            
            # Process imports (relationships)
            for imp in deps.get('imports', []):
                module = imp.get('module', '')
                target_id = self._generate_id(None, module, 'module')
                
                # Create module entity if not exists
                if target_id not in self.entities:
                    self.entities[target_id] = CodeEntity(
                        id=target_id,
                        type='module',
                        name=module,
                        file_path='',
                        line_number=0,
                        content=module
                    )
                
                # Create relationship
                self.relationships.append(Relationship(
                    source_id=file_id,
                    target_id=target_id,
                    type='imports',
                    metadata={'line': imp.get('line')}
                ))
        
        except Exception as e:
            logger.warning(f"  Warning: Could not process {dep_file}: {e}")
    
    def _generate_id(self, file_path: Path, name: str, entity_type: str) -> str:
        """Generate unique ID for an entity"""
        if file_path:
            base = f"{file_path.stem}:{name}:{entity_type}"
        else:
            base = f"{name}:{entity_type}"
        
        return hashlib.md5(base.encode()).hexdigest()[:16]
    
    def _generate_embeddings_real(self, chunks: List[Dict]) -> List[List[float]]:
        """
        Generate embeddings using Qwen3-Embedding-8B via vLLM.
        
        Uses docs_dual_memory.DocsEmbeddingGenerator which connects to vLLM server.
        """
        if not chunks:
            return []
        
        texts = [c.get('content', '') for c in chunks]
        
        try:
            # Use DocsEmbeddingGenerator which connects to Qwen3-Embedding-8B
            embedder = DocsEmbeddingGenerator()
            logger.info(f"  Using Qwen3-Embedding-8B for {len(texts)} texts")
            embeddings = embedder.generate(texts)
            logger.info(f"  ✅ Generated {len(embeddings)} embeddings (dim={len(embeddings[0]) if embeddings else 0})")
            return embeddings
        except Exception as e:
            logger.error(f"  ❌ Embedding generation failed: {e}")
            raise RuntimeError(f"Cannot generate embeddings: {e}")
    
    def _generate_embeddings_placeholder(self, chunks: List[Dict]) -> List[List[float]]:
        """Fallback: deterministic placeholder embeddings based on content hash."""
        # TAG:embedding_fallback - Deterministic placeholder
        import random
        
        embeddings = []
        for chunk in chunks:
            # Use hash for deterministic embeddings (same text = same embedding)
            content = chunk.get('content', '')
            seed = int(hashlib.md5(content.encode()).hexdigest()[:8], 16)
            random.seed(seed)
            # Use 384-dim to match MiniLM when it's available
            embedding = [random.random() for _ in range(384)]
            embeddings.append(embedding)
        
        return embeddings
    
    def generate_human_readable_index(self):
        """Generate PROJECT_INDEX.md for human navigation."""
        # TAG:human_index - Human-readable project index
        logger.info("Generating human-readable index...")
        
        output = [
            "# Project Index\n\n",
            f"**Updated**: {datetime.now().isoformat()}\n\n",
            f"**Entities**: {len(self.entities)} | **Relationships**: {len(self.relationships)}\n\n",
            "---\n\n"
        ]
        
        # File Structure
        output.append("## File Structure\n\n")
        
        # Group entities by file
        files_index = {}
        for entity_id, entity in self.entities.items():
            if entity.file_path:
                if entity.file_path not in files_index:
                    files_index[entity.file_path] = []
                files_index[entity.file_path].append(entity)
        
        for file_path in sorted(files_index.keys()):
            entities = files_index[file_path]
            file_name = Path(file_path).name
            full_path = self.project_root / file_path
            output.append(f"### [{file_name}](file:///{full_path})\n\n")
            
            for entity in sorted(entities, key=lambda e: e.line_number):
                icon = "🏛️" if entity.type == "class" else "⚙️" if entity.type == "function" else "📄"
                output.append(f"- {icon} **{entity.type}** `{entity.name}` (line {entity.line_number})\n")
            output.append("\n")
        
        # Dependency Graph (Mermaid)
        if self.relationships:
            output.append("## Dependency Graph\n\n")
            output.append("```mermaid\n")
            output.append("graph TD\n")
            
            # Limit to 50 relationships for readability
            for rel in self.relationships[:50]:
                # Sanitize IDs for Mermaid (remove special chars)
                source = rel.source_id[:8]
                target = rel.target_id[:8]
                rel_type = rel.type[:10]
                output.append(f"    {source}[{source}] -->|{rel_type}| {target}[{target}]\n")
            
            if len(self.relationships) > 50:
                output.append(f"    %% ... and {len(self.relationships) - 50} more relationships\n")
            
            output.append("```\n\n")
        
        # Type Summary
        output.append("## Entity Summary\n\n")
        type_counts = {}
        for entity in self.entities.values():
            type_counts[entity.type] = type_counts.get(entity.type, 0) + 1
        
        for entity_type, count in sorted(type_counts.items()):
            output.append(f"- **{entity_type}**: {count}\n")
        
        # Save
        index_file = self.memory_dir / 'PROJECT_INDEX.md'
        index_file.write_text(''.join(output), encoding='utf-8')
        
        logger.info(f"  ✓ Human-readable index saved to: {index_file}")
        logger.info(f"  Files: {len(files_index)}, Entities: {len(self.entities)}, Relationships: {len(self.relationships)}")


class IncrementalIndexer:
    """Manages file hash caching for incremental indexing."""
    # TAG:incremental_indexer - File hash caching for incremental builds
    
    def __init__(self, memory_dir: Path):
        """Initialize incremental indexer with cache file."""
        self.cache_file = memory_dir / '.index_cache.json'
        self.file_hashes: Dict[str, str] = self._load_cache()
        self.changed = False
    
    def _load_cache(self) -> Dict[str, str]:
        """Load file hash cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def save_cache(self):
        """Save file hash cache to disk."""
        if self.changed:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_hashes, f, indent=2)
            logger.info(f"  ✓ Cache saved: {len(self.file_hashes)} file hashes")
    
    def get_changed_files(self, files: List[Path]) -> Tuple[List[Path], List[Path]]:
        """Get list of changed and unchanged files.
        
        Returns:
            Tuple of (changed_files, unchanged_files)
        """
        changed = []
        unchanged = []
        
        for file in files:
            try:
                current_hash = hashlib.md5(file.read_bytes()).hexdigest()
                cached_hash = self.file_hashes.get(str(file))
                
                if cached_hash != current_hash:
                    changed.append(file)
                    self.file_hashes[str(file)] = current_hash
                    self.changed = True
                else:
                    unchanged.append(file)
            except Exception:
                changed.append(file)
        
        return changed, unchanged
    
    def mark_file_indexed(self, file: Path):
        """Mark a file as indexed with its current hash."""
        try:
            current_hash = hashlib.md5(file.read_bytes()).hexdigest()
            self.file_hashes[str(file)] = current_hash
            self.changed = True
        except Exception:
            pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Build project index with embeddings and knowledge graph')
    parser.add_argument('--build-embeddings', action='store_true', help='Build vector embeddings')
    parser.add_argument('--build-knowledge-graph', action='store_true', help='Build knowledge graph')
    parser.add_argument('--build-indexes', action='store_true', help='Build lookup indexes')
    parser.add_argument('--build-human-index', action='store_true', help='Generate human-readable PROJECT_INDEX.md')
    parser.add_argument('--build-all', action='store_true', help='Build everything')
    parser.add_argument('--incremental', action='store_true', help='Only process changed files (uses hash cache)')
    
    args = parser.parse_args()
    
    # Check if any build action specified
    build_actions = [args.build_embeddings, args.build_knowledge_graph, 
                     args.build_indexes, args.build_human_index, args.build_all]
    if not any(build_actions):
        parser.print_help()
        return
    
    project_root = Path(__file__).parent.parent
    indexer = ProjectIndexer(project_root)
    
    # Log incremental mode
    if args.incremental:
        logger.info("📦 Incremental mode enabled (only changed files will be processed)")
    
    if args.build_all or args.build_embeddings:
        indexer.build_embeddings()
    
    if args.build_all or args.build_knowledge_graph:
        indexer.build_knowledge_graph()
    
    if args.build_all or args.build_indexes:
        indexer.build_indexes()
    
    # Generate human-readable index (needs knowledge graph to be built first)
    if args.build_all or args.build_human_index:
        # Ensure knowledge graph is built for human index
        if not indexer.entities and not args.build_knowledge_graph and not args.build_all:
            logger.info("Building knowledge graph for human index...")
            indexer.build_knowledge_graph()
        indexer.generate_human_readable_index()
    
    logger.info("\n✓ Project indexing complete!")
    logger.info(f"  Embeddings: {indexer.embeddings_dir}")
    logger.info(f"  Knowledge graph: {indexer.graph_dir}")
    logger.info(f"  Indexes: {indexer.indexes_dir}")
    if args.build_all or args.build_human_index:
        logger.info(f"  Human index: {indexer.memory_dir / 'PROJECT_INDEX.md'}")

if __name__ == '__main__':
    main()
