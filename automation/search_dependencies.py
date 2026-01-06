#!/usr/bin/env python3
"""
Dependency Search - Find code dependencies with caching and graph queries

<!--TAG:tool_search_dependencies-->

PURPOSE:
    Search and visualize code dependencies using pre-generated dependency maps.
    Supports LRU caching, inverted index for reverse dependencies, and NetworkX
    graph for transitive dependency analysis and cycle detection.

DOCUMENTATION:
    Specification: docs/specs/Automation_Tools_Spec.md
    Wiki Guide: docs/wiki/03_Automation_Tools.md#dependency-search
    Dependencies: docs/memory/dependencies/search_dependencies_dependencies.json

FEATURES:
    - LRU cache for JSON files (10-100x speedup on repeated queries)
    - Inverted index for O(1) reverse dependency lookup
    - NetworkX graph for transitive dependencies and cycle detection
    - Multiple output formats: text, mermaid, json

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger (DocsLogger for isolated logging)
        - networkx (optional, for graph queries - graceful fallback if missing)
    Data:
        - Input: docs/memory/dependencies/*_dependencies.json
        - Output: docs/memory/dependencies/_reverse_index.json

RECENT CHANGES:
    2025-12-11: v2.0 - Added LRU cache, inverted index, NetworkX graph queries
    2025-12-12: Migrated to isolated docs.utils.docs_logger for NSS-DOCS autonomy

TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:search-->

<!--/TAG:tool_search_dependencies-->
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict

# Add project root to path for imports
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.docs_logger import DocsLogger

# Try importing NetworkX - graceful fallback if not available
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None

# Initialize logger
logger = DocsLogger("search_dependencies")


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class DependencyInfo:
    """Dependency information for a file."""
    file_path: str  # Path to the analyzed file
    dependencies: Dict[str, List]  # Category -> list of dependencies
    reverse_dependencies: List[str] = None  # Files that depend on this file
    transitive_dependencies: List[str] = None  # All transitive dependencies


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""
    hits: int = 0  # Number of cache hits
    misses: int = 0  # Number of cache misses
    total_load_time_ms: float = 0.0  # Total time spent loading from disk
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


# ============================================================================
# MAIN CLASS: DependencySearcher
# ============================================================================

class DependencySearcher:
    """
    Search dependencies using pre-generated dependency maps.
    
    Features:
        - LRU cache for JSON files (avoids repeated disk I/O)
        - Inverted index for O(1) reverse dependency lookup
        - NetworkX graph for complex queries (transitive deps, cycles)
    
    <!--TAG:class_dependency_searcher-->
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize DependencySearcher with project root.
        
        Args:
            project_root: Path to the project root directory
        """
        # Store project root and deps directory path
        self.project_root = project_root
        self.deps_dir = project_root / 'docs' / 'memory' / 'dependencies'
        
        # =====================================================================
        # TASK 1: LRU Cache for JSON files
        # =====================================================================
        self._cache: Dict[str, Dict] = {}  # {file_path: deps_data}
        self._cache_stats = CacheStats()  # Track hits/misses
        self._cache_max_size = 100  # Maximum number of cached entries
        
        # =====================================================================
        # TASK 2: Inverted Index for reverse dependencies
        # =====================================================================
        self._reverse_index_file = self.deps_dir / '_reverse_index.json'
        self._reverse_index: Dict[str, List[str]] = {}  # module -> [files that import it]
        self._reverse_index_loaded = False  # Lazy loading flag
        
        # =====================================================================
        # TASK 3: NetworkX Graph for complex queries
        # =====================================================================
        self._graph: Optional['nx.DiGraph'] = None  # Lazy-loaded graph
        self._graph_built = False  # Flag to track if graph is built
        
        # Log initialization
        logger.info("DependencySearcher initialized", {
            "project_root": str(project_root),
            "deps_dir": str(self.deps_dir),
            "has_networkx": HAS_NETWORKX
        })
    
    # =========================================================================
    # TASK 1: LRU Cache Methods
    # =========================================================================
    
    def _load_deps_cached(self, dep_file: Path) -> Dict:
        """
        Load dependencies from JSON file with LRU caching.
        
        Args:
            dep_file: Path to the dependency JSON file
            
        Returns:
            Parsed JSON data as dictionary
        """
        cache_key = str(dep_file)  # Use absolute path as cache key
        
        # Check if already in cache
        if cache_key in self._cache:
            self._cache_stats.hits += 1
            logger.debug(f"Cache HIT: {dep_file.name}")
            return self._cache[cache_key]
        
        # Cache miss - load from disk
        self._cache_stats.misses += 1
        start_time = time.time()
        
        try:
            with open(dep_file, 'r', encoding='utf-8') as f:
                deps = json.load(f)
            
            # Track load time
            load_time_ms = (time.time() - start_time) * 1000
            self._cache_stats.total_load_time_ms += load_time_ms
            
            # Evict oldest entry if cache is full (simple LRU)
            if len(self._cache) >= self._cache_max_size:
                # Remove first (oldest) entry
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"Cache eviction: {oldest_key}")
            
            # Store in cache
            self._cache[cache_key] = deps
            logger.debug(f"Cache MISS: {dep_file.name} (loaded in {load_time_ms:.2f}ms)")
            
            return deps
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {dep_file}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading {dep_file}: {e}")
            return {}
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache stats
        """
        return {
            "hits": self._cache_stats.hits,
            "misses": self._cache_stats.misses,
            "hit_rate": f"{self._cache_stats.hit_rate:.1f}%",
            "total_load_time_ms": f"{self._cache_stats.total_load_time_ms:.2f}",
            "cached_entries": len(self._cache),
            "max_size": self._cache_max_size
        }
    
    def clear_cache(self):
        """Clear the LRU cache."""
        self._cache.clear()
        self._cache_stats = CacheStats()
        logger.info("Cache cleared")
    
    # =========================================================================
    # TASK 2: Inverted Index Methods
    # =========================================================================
    
    def _load_or_build_reverse_index(self) -> Dict[str, List[str]]:
        """
        Load inverted index from disk or build if not exists.
        
        Returns:
            Inverted index mapping module names to files that import them
        """
        if self._reverse_index_loaded:
            return self._reverse_index
        
        # Try loading from disk first
        if self._reverse_index_file.exists():
            try:
                with open(self._reverse_index_file, 'r', encoding='utf-8') as f:
                    self._reverse_index = json.load(f)
                self._reverse_index_loaded = True
                logger.info(f"Loaded reverse index: {len(self._reverse_index)} entries")
                return self._reverse_index
            except Exception as e:
                logger.warning(f"Failed to load reverse index: {e}")
        
        # Build index from scratch
        return self.rebuild_reverse_index()
    
    def rebuild_reverse_index(self) -> Dict[str, List[str]]:
        """
        (Re)build the inverted index for reverse dependency lookup.
        
        Returns:
            Newly built inverted index
        """
        logger.info("Building reverse index...")
        start_time = time.time()
        
        index = defaultdict(list)  # module -> [files that import it]
        files_processed = 0
        
        # Iterate through all dependency files
        for dep_file in self.deps_dir.rglob('*_dependencies.json'):
            # Skip the index file itself
            if dep_file.name == '_reverse_index.json':
                continue
            
            try:
                # Use cached loader for efficiency
                deps = self._load_deps_cached(dep_file)
                source_file = deps.get('file_path', str(dep_file.stem))
                
                # Index imports
                for imp in deps.get('imports', []):
                    module = imp.get('module', '')
                    if module:
                        # Add to index - module -> source file
                        if source_file not in index[module]:
                            index[module].append(source_file)
                        
                        # Also index by module stem (last part)
                        module_stem = module.split('.')[-1]
                        if module_stem and source_file not in index[module_stem]:
                            index[module_stem].append(source_file)
                
                # Index function calls (for cross-module references)
                for call in deps.get('function_calls', []):
                    func = call.get('function', '')
                    if '.' in func:
                        # Extract module prefix
                        module_prefix = func.split('.')[0]
                        if module_prefix and source_file not in index[module_prefix]:
                            index[module_prefix].append(source_file)
                
                files_processed += 1
                
            except Exception as e:
                logger.warning(f"Error processing {dep_file}: {e}")
                continue
        
        # Convert defaultdict to regular dict
        self._reverse_index = dict(index)
        self._reverse_index_loaded = True
        
        # Save to disk for persistence
        try:
            with open(self._reverse_index_file, 'w', encoding='utf-8') as f:
                json.dump(self._reverse_index, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved reverse index to {self._reverse_index_file}")
        except Exception as e:
            logger.error(f"Failed to save reverse index: {e}")
        
        duration = time.time() - start_time
        logger.info(f"Reverse index built: {len(self._reverse_index)} modules, "
                   f"{files_processed} files processed in {duration:.2f}s")
        
        return self._reverse_index
    
    def _find_reverse_dependencies_fast(self, target_file: Path) -> List[str]:
        """
        Find files that depend on target file using inverted index (O(1)).
        
        Args:
            target_file: Path to the target file
            
        Returns:
            List of files that import/depend on the target
        """
        # Ensure index is loaded
        self._load_or_build_reverse_index()
        
        # Look up by stem (filename without extension)
        target_name = target_file.stem
        
        # Get all files that import this module
        reverse_deps = self._reverse_index.get(target_name, [])
        
        # Also check full relative path
        target_str = str(target_file)
        if target_str in self._reverse_index:
            reverse_deps.extend(self._reverse_index[target_str])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_deps = []
        for dep in reverse_deps:
            if dep not in seen:
                seen.add(dep)
                unique_deps.append(dep)
        
        return unique_deps
    
    # =========================================================================
    # TASK 3: NetworkX Graph Methods
    # =========================================================================
    
    def _ensure_graph_built(self):
        """Ensure the NetworkX graph is built (lazy initialization)."""
        if not HAS_NETWORKX:
            logger.warning("NetworkX not available. Install with: pip install networkx")
            return False
        
        if self._graph_built:
            return True
        
        self._build_dependency_graph()
        return True
    
    def _build_dependency_graph(self) -> Optional['nx.DiGraph']:
        """
        Build NetworkX directed graph from dependency files.
        
        Returns:
            NetworkX DiGraph with nodes as files and edges as dependencies
        """
        if not HAS_NETWORKX:
            logger.error("NetworkX not installed")
            return None
        
        logger.info("Building dependency graph...")
        start_time = time.time()
        
        self._graph = nx.DiGraph()
        files_processed = 0
        edges_added = 0
        
        # Iterate through all dependency files
        for dep_file in self.deps_dir.rglob('*_dependencies.json'):
            if dep_file.name == '_reverse_index.json':
                continue
            
            try:
                deps = self._load_deps_cached(dep_file)
                source = deps.get('file_path', str(dep_file.stem))
                
                # Add source node with metadata
                self._graph.add_node(source, type='file')
                
                # Add edges for imports
                for imp in deps.get('imports', []):
                    target = imp.get('module', '')
                    if target:
                        self._graph.add_node(target, type='module')
                        self._graph.add_edge(source, target, type='import')
                        edges_added += 1
                
                # Add edges for function calls (optional, for detailed graph)
                for call in deps.get('function_calls', []):
                    func = call.get('function', '')
                    if '.' in func:
                        module = func.split('.')[0]
                        if module and not self._graph.has_edge(source, module):
                            self._graph.add_edge(source, module, type='call')
                            edges_added += 1
                
                files_processed += 1
                
            except Exception as e:
                logger.warning(f"Error processing {dep_file} for graph: {e}")
                continue
        
        self._graph_built = True
        duration = time.time() - start_time
        
        logger.info(f"Dependency graph built: {self._graph.number_of_nodes()} nodes, "
                   f"{self._graph.number_of_edges()} edges in {duration:.2f}s")
        
        return self._graph
    
    def find_transitive_dependencies(self, file_path: str, max_depth: int = 3) -> List[str]:
        """
        Find all transitive dependencies up to max_depth using BFS.
        
        Args:
            file_path: Starting file path
            max_depth: Maximum depth to traverse (default: 3)
            
        Returns:
            List of all transitive dependencies
        """
        if not self._ensure_graph_built():
            return []
        
        # Normalize file path - try both absolute and relative
        target = Path(file_path)
        target_str = str(target)
        
        # Try the path as given first
        if target_str not in self._graph:
            # Try with project root prefix (absolute)
            abs_path = str(self.project_root / target)
            if abs_path in self._graph:
                target_str = abs_path
            else:
                # Try relative version
                if target.is_absolute():
                    try:
                        rel_path = str(target.relative_to(self.project_root))
                        if rel_path in self._graph:
                            target_str = rel_path
                    except ValueError:
                        pass
        
        # Check if node exists after all attempts
        if target_str not in self._graph:
            logger.warning(f"Node not found in graph: {file_path}")
            return []
        
        # BFS traversal
        visited: Set[str] = set()

        queue: List[Tuple[str, int]] = [(target_str, 0)]  # (node, depth)
        
        while queue:
            node, depth = queue.pop(0)
            
            # Skip if already visited or max depth reached
            if node in visited or depth >= max_depth:
                continue
            
            visited.add(node)
            
            # Add all successors (outgoing edges = dependencies)
            for successor in self._graph.successors(node):
                if successor not in visited:
                    queue.append((successor, depth + 1))
        
        # Remove the starting node from results
        visited.discard(target_str)
        
        return sorted(list(visited))
    
    def find_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        Find shortest dependency path between two files.
        
        Args:
            source: Source file path
            target: Target file/module
            
        Returns:
            List of nodes in the path, or None if no path exists
        """
        if not self._ensure_graph_built():
            return None
        
        try:
            path = nx.shortest_path(self._graph, source, target)
            return path
        except nx.NetworkXNoPath:
            logger.info(f"No path found from {source} to {target}")
            return None
        except nx.NodeNotFound as e:
            logger.warning(f"Node not found: {e}")
            return None
    
    def detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies in the graph.
        
        Returns:
            List of cycles (each cycle is a list of nodes)
        """
        if not self._ensure_graph_built():
            return []
        
        try:
            cycles = list(nx.simple_cycles(self._graph))
            if cycles:
                logger.warning(f"Found {len(cycles)} circular dependencies")
            else:
                logger.info("No circular dependencies found")
            return cycles
        except Exception as e:
            logger.error(f"Error detecting cycles: {e}")
            return []
    
    def get_graph_stats(self) -> Dict:
        """
        Get NetworkX graph statistics.
        
        Returns:
            Dictionary with graph statistics
        """
        if not self._ensure_graph_built():
            return {"error": "NetworkX not available"}
        
        return {
            "nodes": self._graph.number_of_nodes(),
            "edges": self._graph.number_of_edges(),
            "density": f"{nx.density(self._graph):.4f}",
            "is_dag": nx.is_directed_acyclic_graph(self._graph),
            "weakly_connected_components": nx.number_weakly_connected_components(self._graph)
        }
    
    # =========================================================================
    # Core Search Methods
    # =========================================================================
    
    def search(self, file_path: str, include_reverse: bool = False) -> Optional[DependencyInfo]:
        """
        Search dependencies for a file.
        
        Args:
            file_path: Path to the file to analyze
            include_reverse: Whether to include reverse dependencies
            
        Returns:
            DependencyInfo object or None if not found
        """
        # Convert to Path and normalize
        target_file = Path(file_path)
        if target_file.is_absolute():
            try:
                target_file = target_file.relative_to(self.project_root)
            except ValueError:
                pass
        
        # Find dependency JSON file
        dep_file = self._find_dependency_file(target_file)
        
        if not dep_file or not dep_file.exists():
            logger.error(f"No dependency map found for: {file_path}")
            logger.info(f"Run: python3 docs/automation/analyze_dependencies.py --target {file_path}")
            return None
        
        # Load dependencies using cache
        deps = self._load_deps_cached(dep_file)
        
        result = DependencyInfo(
            file_path=str(target_file),
            dependencies=deps
        )
        
        # Find reverse dependencies if requested (using fast O(1) lookup)
        if include_reverse:
            result.reverse_dependencies = self._find_reverse_dependencies_fast(target_file)
        
        return result
    
    def _find_dependency_file(self, target_file: Path) -> Optional[Path]:
        """
        Find the dependency JSON file for a target file.
        
        Args:
            target_file: Path to the target file
            
        Returns:
            Path to dependency JSON file or None if not found
        """
        # Try exact match by stem
        dep_file = self.deps_dir / f"{target_file.stem}_dependencies.json"
        if dep_file.exists():
            return dep_file
        
        # Try in subdirectory matching file structure
        if target_file.parent != Path('.'):
            dep_file = self.deps_dir / target_file.parent / f"{target_file.stem}_dependencies.json"
            if dep_file.exists():
                return dep_file
        
        return None
    
    def _find_reverse_dependencies(self, target_file: Path) -> List[str]:
        """
        Find files that depend on the target file (legacy fallback).
        
        This method is kept for backward compatibility.
        Use _find_reverse_dependencies_fast() for better performance.
        """
        # Use fast inverted index lookup instead
        return self._find_reverse_dependencies_fast(target_file)
    
    # =========================================================================
    # Visualization Methods
    # =========================================================================
    
    def visualize_dependencies(self, file_path: str, output_format: str = 'text') -> str:
        """
        Create a visual representation of dependencies.
        
        Args:
            file_path: Path to the file to visualize
            output_format: Output format ('text', 'mermaid', 'json')
            
        Returns:
            Formatted string representation
        """
        info = self.search(file_path, include_reverse=True)
        
        if not info:
            return "No dependency information available"
        
        if output_format == 'mermaid':
            return self._generate_mermaid(info)
        else:
            return self._generate_text(info)
    
    def _generate_text(self, info: DependencyInfo) -> str:
        """Generate text representation of dependencies."""
        lines = []
        lines.append(f"Dependencies for: {info.file_path}")
        lines.append("=" * 60)
        
        # Code dependencies
        if info.dependencies.get('imports'):
            lines.append("\n📦 CODE DEPENDENCIES (Imports)")
            lines.append("-" * 60)
            for imp in info.dependencies['imports']:
                module = imp.get('module', '')
                name = imp.get('name', '')
                if name:
                    lines.append(f"  • from {module} import {name}")
                else:
                    lines.append(f"  • import {module}")
        
        # Configuration dependencies
        if info.dependencies.get('config_files'):
            lines.append("\n⚙️  CONFIG DEPENDENCIES")
            lines.append("-" * 60)
            for cfg in info.dependencies['config_files']:
                lines.append(f"  • {cfg.get('file')} ({cfg.get('type')})")
        
        if info.dependencies.get('env_vars'):
            lines.append("\n🔐 ENVIRONMENT VARIABLES")
            lines.append("-" * 60)
            for env in info.dependencies['env_vars']:
                default = f" (default: {env.get('default')})" if env.get('default') else ""
                lines.append(f"  • {env.get('var')}{default}")
        
        # Data dependencies
        if info.dependencies.get('file_reads'):
            lines.append("\n📥 DATA INPUTS (File Reads)")
            lines.append("-" * 60)
            for read in info.dependencies['file_reads']:
                lines.append(f"  • {read.get('path')} ({read.get('operation')})")
        
        if info.dependencies.get('file_writes'):
            lines.append("\n📤 DATA OUTPUTS (File Writes)")
            lines.append("-" * 60)
            for write in info.dependencies['file_writes']:
                lines.append(f"  • {write.get('path')} ({write.get('operation')})")
        
        # External dependencies
        if info.dependencies.get('api_calls'):
            lines.append("\n🌐 EXTERNAL APIS")
            lines.append("-" * 60)
            for api in info.dependencies['api_calls']:
                service = api.get('service', 'Unknown')
                endpoint = api.get('endpoint', '')
                lines.append(f"  • {service}: {endpoint}")
        
        if info.dependencies.get('subprocess_calls'):
            lines.append("\n🔧 SYSTEM COMMANDS")
            lines.append("-" * 60)
            for cmd in info.dependencies['subprocess_calls']:
                lines.append(f"  • {cmd.get('command')}")
        
        # Reverse dependencies
        if info.reverse_dependencies:
            lines.append("\n⬅️  REVERSE DEPENDENCIES (Files that depend on this)")
            lines.append("-" * 60)
            for dep in info.reverse_dependencies:
                lines.append(f"  • {dep}")
        
        # Transitive dependencies if available
        if info.transitive_dependencies:
            lines.append("\n🔄 TRANSITIVE DEPENDENCIES")
            lines.append("-" * 60)
            for dep in info.transitive_dependencies:
                lines.append(f"  • {dep}")
        
        return '\n'.join(lines)
    
    def _generate_mermaid(self, info: DependencyInfo) -> str:
        """Generate Mermaid diagram of dependencies."""
        lines = []
        lines.append("```mermaid")
        lines.append("graph TD")
        
        # Main file node
        main_id = "MAIN[" + info.file_path + "]"
        lines.append(f"    {main_id}")
        lines.append(f"    style MAIN fill:#f9f,stroke:#333,stroke-width:2px")
        
        # Import nodes
        for i, imp in enumerate(info.dependencies.get('imports', [])[:10]):  # Limit to 10
            module = imp.get('module', '').replace('.', '_').replace('-', '_')
            safe_id = f"IMP{i}"
            lines.append(f"    {safe_id}[{imp.get('module')}]")
            lines.append(f"    MAIN --> {safe_id}")
        
        # Config file nodes
        for i, cfg in enumerate(info.dependencies.get('config_files', [])):
            safe_id = f"CFG{i}"
            lines.append(f"    {safe_id}[{cfg.get('file')}]")
            lines.append(f"    MAIN -.-> {safe_id}")
        
        # Reverse dependency nodes
        if info.reverse_dependencies:
            for i, rev in enumerate(info.reverse_dependencies[:5]):  # Limit to 5
                safe_id = f"REV{i}"
                lines.append(f"    {safe_id}[{Path(rev).name}]")
                lines.append(f"    {safe_id} --> MAIN")
        
        lines.append("```")
        return '\n'.join(lines)

# <!--/TAG:class_dependency_searcher-->

# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main entry point for CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Search file dependencies with caching and graph analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search
  python3 search_dependencies.py --file utils/paranoid_logger.py
  
  # Include reverse dependencies
  python3 search_dependencies.py --file utils/paranoid_logger.py --reverse
  
  # Show cache statistics
  python3 search_dependencies.py --file utils/paranoid_logger.py --stats
  
  # Rebuild reverse index
  python3 search_dependencies.py --rebuild-index
  
  # Find transitive dependencies
  python3 search_dependencies.py --file orchestrator.py --transitive --depth 2
  
  # Detect circular dependencies
  python3 search_dependencies.py --cycles
  
  # Show graph statistics
  python3 search_dependencies.py --graph-stats
"""
    )
    
    # Basic arguments
    parser.add_argument('--file', type=str, help='File to analyze')
    parser.add_argument('--reverse', action='store_true', help='Include reverse dependencies')
    parser.add_argument('--format', choices=['text', 'mermaid', 'json'], default='text',
                       help='Output format')
    parser.add_argument('--output', type=str, help='Save to file')
    
    # Cache arguments
    parser.add_argument('--stats', action='store_true', help='Show cache statistics')
    
    # Index arguments
    parser.add_argument('--rebuild-index', action='store_true', 
                       help='Rebuild reverse dependency index')
    
    # Graph arguments
    parser.add_argument('--transitive', action='store_true',
                       help='Find transitive dependencies')
    parser.add_argument('--depth', type=int, default=3,
                       help='Max depth for transitive search (default: 3)')
    parser.add_argument('--cycles', action='store_true',
                       help='Detect circular dependencies')
    parser.add_argument('--path', type=str, nargs=2, metavar=('SOURCE', 'TARGET'),
                       help='Find shortest path between two files')
    parser.add_argument('--graph-stats', action='store_true',
                       help='Show graph statistics')
    
    args = parser.parse_args()
    
    # Initialize searcher
    project_root = Path(__file__).parent.parent
    searcher = DependencySearcher(project_root)
    
    # Handle rebuild-index command
    if args.rebuild_index:
        searcher.rebuild_reverse_index()
        print("✅ Reverse index rebuilt successfully")
        print(f"📁 Saved to: {searcher._reverse_index_file}")
        return
    
    # Handle cycles command
    if args.cycles:
        cycles = searcher.detect_cycles()
        if cycles:
            print(f"⚠️  Found {len(cycles)} circular dependencies:\n")
            for i, cycle in enumerate(cycles[:10], 1):  # Show max 10
                print(f"  {i}. {' → '.join(cycle)} → {cycle[0]}")
            if len(cycles) > 10:
                print(f"\n  ... and {len(cycles) - 10} more")
        else:
            print("✅ No circular dependencies found")
        return
    
    # Handle graph-stats command
    if args.graph_stats:
        stats = searcher.get_graph_stats()
        print("📊 Dependency Graph Statistics:")
        print(f"  Nodes: {stats.get('nodes', 'N/A')}")
        print(f"  Edges: {stats.get('edges', 'N/A')}")
        print(f"  Density: {stats.get('density', 'N/A')}")
        print(f"  Is DAG: {stats.get('is_dag', 'N/A')}")
        print(f"  Connected Components: {stats.get('weakly_connected_components', 'N/A')}")
        return
    
    # Handle path command
    if args.path:
        source, target = args.path
        path = searcher.find_shortest_path(source, target)
        if path:
            print(f"📍 Shortest path ({len(path)} steps):")
            print(f"   {' → '.join(path)}")
        else:
            print(f"❌ No path found from {source} to {target}")
        return
    
    # Require --file for other operations
    if not args.file:
        parser.print_help()
        return
    
    # Handle transitive dependencies
    if args.transitive:
        trans_deps = searcher.find_transitive_dependencies(args.file, args.depth)
        print(f"🔄 Transitive dependencies for {args.file} (depth={args.depth}):")
        if trans_deps:
            for dep in trans_deps:
                print(f"  • {dep}")
        else:
            print("  (none found)")
        
        # Show cache stats if requested
        if args.stats:
            print(f"\n📊 Cache: {json.dumps(searcher.get_cache_stats(), indent=2)}")
        return
    
    # Standard search
    if args.format == 'json':
        info = searcher.search(args.file, args.reverse)
        if info:
            result = json.dumps(asdict(info), indent=2, ensure_ascii=False)
        else:
            result = "{}"
    else:
        result = searcher.visualize_dependencies(args.file, args.format)
    
    # Show stats if requested
    if args.stats:
        cache_stats = searcher.get_cache_stats()
        result += f"\n\n📊 Cache Statistics:\n{json.dumps(cache_stats, indent=2)}"
    
    # Output result
    if args.output:
        output_path = project_root / args.output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        logger.info(f"Results saved to: {output_path}")
        print(f"✅ Saved to: {output_path}")
    else:
        print(result)


if __name__ == '__main__':
    main()
