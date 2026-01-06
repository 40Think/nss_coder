#!/usr/bin/env python3
"""
Call Graph Generator - Visualize function dependencies with LLM analysis

<!--TAG:tool_call_graph-->

PURPOSE:
    Analyzes Python code to generate static call graphs.
    Visualizes function calls and dependencies using Mermaid.js.
    Supports Graphviz and JSON formats.
    NEW: LLM analysis, dual memory integration, metrics calculation.

DOCUMENTATION:
    Spec: docs/specs/Automation_Tools_Spec.md
    Wiki: docs/wiki/09_Documentation_System.md
    Ticket: docs/technical_debt/tickets_2025_12_11/TICKET_04_generate_call_graph.md

TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:analysis--> <!--TAG:automation--> <!--TAG:visualization--> <!--TAG:analysis-->

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger.DocsLogger (paranoid logging)
        - docs.utils.docs_llm_backend.DocsLLMBackend (optional, LLM analysis)
        - docs.utils.docs_dual_memory.DocsDualMemoryIndex (optional, indexing)
    Config:
        - None (uses hardcoded project structure)
    Data:
        - Input: Any Python source files (*.py)
        - Output: Mermaid/Graphviz/JSON to specified path
    External:
        - vLLM API (optional, for LLM analysis)

RECENT CHANGES:
    2025-12-12: Fixed header DEPENDENCIES section (audit compliance)
    2025-12-11: Added LLM analysis, dual memory, metrics, auto-regeneration

<!--/TAG:tool_call_graph-->
"""

import ast  # Abstract Syntax Tree for parsing Python code
import json  # JSON serialization for output
import sys  # System-specific parameters
from pathlib import Path  # Object-oriented filesystem paths
from typing import Dict, List, Optional, Any  # Type hints
from dataclasses import dataclass, field  # Structured data classes
from datetime import datetime  # Date and time handling

# Add project root to path for imports
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.docs_logger import DocsLogger  # Paranoid logging system

# Initialize logger
logger = DocsLogger("generate_call_graph")

# Project root constant
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class FunctionNode:
    """A function in the call graph."""
    name: str  # Function name
    file_path: str  # Path to source file
    line_number: int  # Line number in file
    calls: List[str] = field(default_factory=list)  # Functions this calls
    called_by: List[str] = field(default_factory=list)  # Functions that call this


class CallGraphGenerator:
    """Generate function call graphs from Python code with LLM analysis."""
    
    def __init__(self, project_root: Path):
        """Initialize call graph generator."""
        self.project_root = project_root  # Project root path
        self.functions: Dict[str, FunctionNode] = {}  # Function registry
        
    def analyze_file(self, file_path: Path):
        """Analyze a single Python file and extract function calls."""
        try:
            # Read and parse the file
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return
        
        # Extract functions and their calls
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name  # Get function name
                func_id = f"{file_path.stem}.{func_name}"  # Create unique ID
                
                # Create function node
                self.functions[func_id] = FunctionNode(
                    name=func_name,
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=node.lineno
                )
                
                # Find function calls within this function
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        called_func = self._extract_call_name(child)
                        if called_func:
                            self.functions[func_id].calls.append(called_func)
    
    def analyze_directory(self, directory: Path):
        """Analyze all Python files in a directory."""
        for py_file in directory.rglob('*.py'):
            # Skip cache and vllm directories
            if '__pycache__' in str(py_file) or 'vllm-latest' in str(py_file):
                continue
            self.analyze_file(py_file)
    
    def analyze_project(self):
        """Analyze entire project code directories."""
        for code_dir in ['processing', 'utils', 'scripts']:
            dir_path = self.project_root / code_dir
            if dir_path.exists():
                self.analyze_directory(dir_path)
    
    def build_reverse_edges(self):
        """Build reverse edges (called_by relationships)."""
        for func_id, func_node in self.functions.items():
            for called_func in func_node.calls:
                # Try to find the called function in our registry
                for target_id, target_node in self.functions.items():
                    if target_node.name == called_func or target_id.endswith(f".{called_func}"):
                        target_node.called_by.append(func_id)
    
    # =========================================================================
    # NEW: Metrics Calculation (TICKET #04 Phase 3)
    # =========================================================================
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate graph metrics using NetworkX-like algorithms."""
        metrics = {
            'node_count': len(self.functions),  # Total functions
            'edge_count': sum(len(f.calls) for f in self.functions.values()),  # Total calls
            'calculated_at': datetime.now().isoformat()
        }
        
        # Calculate density: edges / (nodes * (nodes - 1))
        n = metrics['node_count']
        if n > 1:
            max_edges = n * (n - 1)  # Directed graph
            metrics['density'] = round(metrics['edge_count'] / max_edges, 4)
        else:
            metrics['density'] = 0.0
        
        # Find most central functions (highest in+out degree)
        centrality = []
        for func_id, func_node in self.functions.items():
            degree = len(func_node.calls) + len(func_node.called_by)
            centrality.append((func_id, degree))
        
        # Sort by degree descending, take top 5
        centrality.sort(key=lambda x: x[1], reverse=True)
        metrics['most_central_functions'] = centrality[:5]
        
        # Detect circular dependencies using simple DFS
        cycles = self._find_cycles()
        metrics['circular_dependencies'] = len(cycles)
        if cycles:
            metrics['cycle_examples'] = [' -> '.join(cycle) for cycle in cycles[:3]]
        
        # Find orphan functions (no callers, not main/entry points)
        orphans = [
            func_id for func_id, func_node in self.functions.items()
            if not func_node.called_by and func_node.name not in ['main', '__init__', 'setup']
        ]
        metrics['orphan_count'] = len(orphans)
        if orphans:
            metrics['orphan_examples'] = orphans[:5]
        
        logger.info(f"✅ Metrics: {metrics['node_count']} nodes, {metrics['edge_count']} edges, density={metrics['density']}")
        
        return metrics
    
    def _find_cycles(self) -> List[List[str]]:
        """Find circular dependencies using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str, path: List[str]):
            if node_id in rec_stack:
                # Found a cycle, extract it
                cycle_start = path.index(node_id)
                cycle = path[cycle_start:] + [node_id]
                cycles.append(cycle)
                return
            
            if node_id in visited:
                return
            
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            # Get function node, traverse calls
            if node_id in self.functions:
                for called_name in self.functions[node_id].calls:
                    # Find the full ID for this call
                    for target_id in self.functions:
                        if target_id.endswith(f".{called_name}"):
                            dfs(target_id, path.copy())
                            break
            
            rec_stack.remove(node_id)
        
        # Run DFS from each node
        for func_id in list(self.functions.keys())[:50]:  # Limit to avoid long runs
            dfs(func_id, [])
        
        return cycles[:10]  # Limit to 10 cycles
    
    # =========================================================================
    # NEW: LLM Analysis (TICKET #04 Phase 1)
    # =========================================================================
    
    def analyze_with_llm(self, mermaid_content: str) -> Dict[str, Any]:
        """Analyze call graph using LLM for insights."""
        try:
            from utils.docs_llm_backend import DocsLLMBackend
            
            backend = DocsLLMBackend()
            
            # Check if vLLM is available
            status, _ = backend.check_health()
            if status != "OK":
                logger.warning("vLLM not available, skipping LLM analysis")
                return {}
            
            # Build prompt for analysis
            system_prompt = """You are a code architecture analyst. Analyze call graphs and provide concise insights.
Keep responses under 200 words. Use bullet points."""
            
            user_prompt = f"""Analyze this call graph:

## Statistics
- Total functions: {len(self.functions)}
- Total edges: {sum(len(f.calls) for f in self.functions.values())}

## Graph (first 1500 chars)
{mermaid_content[:1500]}

## Provide:
1. **Complexity Assessment** (1-10): How complex?
2. **Key Functions**: 2-3 most important functions
3. **Potential Issues**: Circular deps, bottlenecks
4. **Recommendations**: 1-2 quick improvements

Be concise."""
            
            # Generate analysis
            response = backend.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=300,
                temperature=0.3
            )
            
            if response:
                logger.info("✅ LLM analysis completed")
                return {
                    'llm_analysis': response,
                    'analyzed_at': datetime.now().isoformat(),
                    'model': 'vllm'
                }
            else:
                logger.warning("LLM returned empty response")
                return {}
                
        except ImportError:
            logger.warning("vLLM backend not available")
            return {}
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")
            return {}
    
    # =========================================================================
    # NEW: Dual Memory Integration (TICKET #04 Phase 2)
    # =========================================================================
    
    def index_in_dual_memory(self, graph_data: Dict, source_file: str) -> bool:
        """Index call graph in dual memory system for semantic search."""
        try:
            from utils.docs_dual_memory import DocsDualMemoryIndex, ContentChunk
            
            index = DocsDualMemoryIndex()
            
            # Create description text for embedding
            function_names = [f['name'] for f in list(graph_data.get('functions', {}).values())[:10]]
            llm_text = graph_data.get('llm_analysis', {}).get('llm_analysis', '')
            
            description = f"""Call Graph Analysis for {source_file}

Functions: {', '.join(function_names)}
Total nodes: {graph_data.get('metrics', {}).get('node_count', len(graph_data.get('functions', {})))}
Total edges: {graph_data.get('metrics', {}).get('edge_count', 0)}
Density: {graph_data.get('metrics', {}).get('density', 0)}

{llm_text}
"""
            
            # Create content chunk
            chunk = ContentChunk(
                chunk_id=f"call_graph_{Path(source_file).stem}",
                content=description,
                content_type="description",
                source_file=source_file,
                line_start=0,
                line_end=0,
                metadata={
                    'type': 'call_graph',
                    'node_count': graph_data.get('metrics', {}).get('node_count', 0),
                    'edge_count': graph_data.get('metrics', {}).get('edge_count', 0),
                    'generated_at': datetime.now().isoformat()
                }
            )
            
            # Generate embedding and add to index
            embedding = index.embedder.generate([description])[0]
            chunk.embedding = embedding
            
            # Load existing index, append, save
            index_data = index._load_index("description")
            
            # Remove old entry for same source if exists
            index_data['chunks'] = [
                c for c in index_data.get('chunks', [])
                if c.get('chunk_id') != chunk.chunk_id
            ]
            index_data['embeddings'] = [
                e for i, e in enumerate(index_data.get('embeddings', []))
                if i < len(index_data['chunks'])
            ]
            
            # Add new chunk
            index_data['chunks'].append({
                'chunk_id': chunk.chunk_id,
                'content': chunk.content,
                'source_file': chunk.source_file,
                'line_start': chunk.line_start,
                'line_end': chunk.line_end,
                'metadata': chunk.metadata
            })
            index_data['embeddings'].append(embedding)
            
            # Update metadata
            if 'metadata' not in index_data:
                index_data['metadata'] = {}
            index_data['metadata']['total_chunks'] = len(index_data['chunks'])
            
            # Save
            index._save_index("description", index_data)
            
            logger.info(f"✅ Indexed call graph in dual memory: {chunk.chunk_id}")
            return True
            
        except ImportError:
            logger.warning("dual_memory not available, skipping indexing")
            return False
        except Exception as e:
            logger.warning(f"Dual memory indexing failed: {e}")
            return False
    
    # =========================================================================
    # NEW: Auto-Regeneration Check (TICKET #04 Phase 4)
    # =========================================================================
    
    def should_regenerate(self, source_path: Path, output_path: Path) -> bool:
        """Check if call graph needs regeneration based on file modification times."""
        if not output_path.exists():
            logger.info(f"Output file does not exist, will generate")
            return True
        
        # Get modification times
        source_mtime = source_path.stat().st_mtime
        output_mtime = output_path.stat().st_mtime
        
        if source_mtime > output_mtime:
            logger.info(f"Source file modified, will regenerate")
            return True
        
        logger.info(f"Call graph is up-to-date")
        return False
    
    # =========================================================================
    # Output Generation Methods
    # =========================================================================
    
    def generate_mermaid(self, max_nodes: int = 50) -> str:
        """Generate Mermaid diagram for embedding in Markdown documentation.
        
        Creates a Mermaid.js flowchart showing function call relationships.
        Limits nodes to prevent overwhelming diagrams.
        """
        lines = []  # Accumulator for Mermaid diagram lines
        lines.append("```mermaid")  # Opening fence for Markdown code block
        lines.append("graph TD")  # Top-down directed graph
        
        # Limit nodes to prevent overwhelming diagrams
        func_items = list(self.functions.items())[:max_nodes]
        
        for func_id, func_node in func_items:
            # Sanitize ID for Mermaid (no dots, dashes)
            node_id = func_id.replace('.', '_').replace('-', '_')
            node_label = f"{func_node.name}\\n{Path(func_node.file_path).stem}"
            
            lines.append(f'    {node_id}["{node_label}"]')
            
            # Add edges (limit per node)
            for called_func in func_node.calls[:10]:
                # Find target node
                for target_id, target_node in func_items:
                    if target_node.name == called_func or target_id.endswith(f".{called_func}"):
                        target_node_id = target_id.replace('.', '_').replace('-', '_')
                        lines.append(f"    {node_id} --> {target_node_id}")
                        break
        
        lines.append("```")
        return '\n'.join(lines)
    
    def generate_graphviz(self) -> str:
        """Generate Graphviz DOT format for professional graph visualization.
        
        Creates a directed graph in DOT language compatible with Graphviz
        tools (dot, neato, circo, etc.) for high-quality graph layouts.
        """
        lines = []  # Accumulator for DOT language lines
        lines.append("digraph CallGraph {")  # Define directed graph
        lines.append("    rankdir=LR;")  # Left-to-right layout for better readability
        lines.append("    node [shape=box, style=rounded];")  # Rounded boxes for all nodes
        
        for func_id, func_node in self.functions.items():
            # Sanitize ID
            node_id = func_id.replace('.', '_').replace('-', '_')
            label = f"{func_node.name}\\n{Path(func_node.file_path).stem}"
            
            lines.append(f'    {node_id} [label="{label}"];')
            
            # Add edges
            for called_func in func_node.calls:
                for target_id, target_node in self.functions.items():
                    if target_node.name == called_func or target_id.endswith(f".{called_func}"):
                        target_node_id = target_id.replace('.', '_').replace('-', '_')
                        lines.append(f"    {node_id} -> {target_node_id};")
                        break
        
        lines.append("}")
        return '\n'.join(lines)
    
    def generate_json(self, include_metrics: bool = False, include_llm: bool = False) -> Dict:
        """Generate JSON representation as dict."""
        data = {
            'functions': {},
            'edges': [],
            'generated_at': datetime.now().isoformat()
        }
        
        for func_id, func_node in self.functions.items():
            data['functions'][func_id] = {
                'name': func_node.name,
                'file': func_node.file_path,
                'line': func_node.line_number,
                'calls': func_node.calls,
                'called_by': func_node.called_by
            }
            
            # Add edges
            for called_func in func_node.calls:
                data['edges'].append({
                    'from': func_id,
                    'to': called_func,
                    'type': 'calls'
                })
        
        # Add metrics if requested
        if include_metrics:
            data['metrics'] = self.calculate_metrics()
        
        return data
    
    def _extract_call_name(self, call_node: ast.Call) -> Optional[str]:
        """Extract function name from AST Call node."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return None


def main():
    """Main entry point with enhanced CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate function call graphs with LLM analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --file processing/02_grouper.py --format json
  %(prog)s --all --format mermaid --output docs/diagrams/call_graph.mmd
  %(prog)s --file utils/llm_client.py --with-metrics --llm-analyze --format json
        """
    )
    
    # Input options
    parser.add_argument('--file', type=str, help='Single file to analyze')
    parser.add_argument('--directory', type=str, help='Directory to analyze')
    parser.add_argument('--all', action='store_true', help='Analyze entire project')
    
    # Output options
    parser.add_argument('--format', choices=['mermaid', 'graphviz', 'json'], 
                       default='mermaid', help='Output format (default: mermaid)')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--max-nodes', type=int, default=50, 
                       help='Maximum nodes in diagram (default: 50)')
    
    # NEW: Enhancement options (TICKET #04)
    parser.add_argument('--with-metrics', action='store_true',
                       help='Calculate and include graph metrics')
    parser.add_argument('--llm-analyze', action='store_true',
                       help='Analyze graph using LLM (requires vLLM)')
    parser.add_argument('--index-memory', action='store_true',
                       help='Index result in dual memory system')
    parser.add_argument('--force', action='store_true',
                       help='Force regeneration even if up-to-date')
    
    args = parser.parse_args()
    
    # Validate input
    if not any([args.file, args.directory, args.all]):
        parser.print_help()
        return
    
    project_root = PROJECT_ROOT
    generator = CallGraphGenerator(project_root)
    
    # Determine source path for regeneration check
    source_path = None
    if args.file:
        source_path = project_root / args.file
    
    # Check if regeneration needed (TICKET #04 Phase 4)
    if args.output and source_path and not args.force:
        output_path = project_root / args.output
        if not generator.should_regenerate(source_path, output_path):
            print("Call graph is up-to-date, skipping (use --force to override)")
            return
    
    # Analyze
    if args.file:
        file_path = project_root / args.file
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return
        generator.analyze_file(file_path)
    elif args.directory:
        dir_path = project_root / args.directory
        if not dir_path.exists():
            logger.error(f"Directory not found: {dir_path}")
            return
        generator.analyze_directory(dir_path)
    elif args.all:
        generator.analyze_project()
    
    # Build reverse edges
    generator.build_reverse_edges()
    
    logger.info(f"Analyzed {len(generator.functions)} functions")
    
    # Generate output
    if args.format == 'mermaid':
        output = generator.generate_mermaid(args.max_nodes)
        
        # Add LLM analysis as comments if requested
        if args.llm_analyze:
            llm_result = generator.analyze_with_llm(output)
            if llm_result.get('llm_analysis'):
                analysis_comment = llm_result['llm_analysis'].replace('\n', '\n%% ')
                output = f"{output}\n\n%% === LLM Analysis ===\n%% {analysis_comment}"
        
    elif args.format == 'graphviz':
        output = generator.generate_graphviz()
        
    elif args.format == 'json':
        # Generate JSON data with optional enhancements
        data = generator.generate_json(include_metrics=args.with_metrics)
        
        # Add LLM analysis if requested (TICKET #04 Phase 1)
        if args.llm_analyze:
            mermaid_for_llm = generator.generate_mermaid(30)  # Smaller for LLM
            llm_result = generator.analyze_with_llm(mermaid_for_llm)
            if llm_result:
                data['llm_analysis'] = llm_result
        
        # Index in dual memory if requested (TICKET #04 Phase 2)
        if args.index_memory:
            source_name = args.file or args.directory or "project"
            generator.index_in_dual_memory(data, source_name)
        
        output = json.dumps(data, indent=2, ensure_ascii=False)
    
    # Save or print
    if args.output:
        output_path = project_root / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info(f"✅ Call graph saved to: {output_path} | {len(generator.functions)} functions")
    else:
        print(output)


if __name__ == '__main__':
    main()
