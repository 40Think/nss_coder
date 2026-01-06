#!/usr/bin/env python3
"""
Context Assembler - Enhanced version with dual_memory integration

<!--TAG:tool_assemble_context-->

PURPOSE:
    Assembles relevant context from project files for AI agent prompts.
    Supports semantic search via dual_memory, adaptive tag extraction,
    file ranking, and rich metadata for each included file.
    
    Usage:
        python3 assemble_context.py --task "implement analytics pipeline" --output context.md
        python3 assemble_context.py --file processing/07_analytics.py --output context.md
        python3 assemble_context.py --component analytics --output context.md

DOCUMENTATION:
    Spec: docs/technical_debt/tickets_2025_12_11/TICKET_02_assemble_context.md
    Gap Analysis: docs/technical_debt/assemble_context_gaps.md

TAGS:
    <!--TAG:component:automation-->
    <!--TAG:type:script-->
    <!--TAG:feature:context-->
    <!--TAG:context_assembly-->
    <!--TAG:automation-->
    <!--TAG:ai_agent_tools-->

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger (DocsLogger for isolated logging)
        - docs.utils.docs_dual_memory (DocsDualMemory for semantic search)
    Config:
        - (none - uses defaults embedded in code)
    Data:
        - Input: docs/specs/, docs/wiki/, processing/, utils/, scripts/
        - Output: docs/temp/context.md (default)
    External:
        - sentence-transformers (optional, for semantic search)

RECENT CHANGES:
    2025-12-11: Enhanced v2 with dual_memory integration, metadata/provenance
    2025-12-12: Added DEPENDENCIES and RECENT CHANGES sections per GEMINI.MD

<!--/TAG:tool_assemble_context-->
"""

import os
import sys
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Add project root to path
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.docs_logger import DocsLogger

logger = DocsLogger("assemble_context")

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class FileMetadata:
    """Metadata for an included file."""
    path: str
    reason: str
    relevance_score: float
    matched_keywords: List[str]
    content_type: str  # 'spec', 'wiki', 'code', 'readme', 'dependency'
    file_size_kb: float
    last_modified: str
    tags: List[str] = field(default_factory=list)
    line_range: Optional[Tuple[int, int]] = None


@dataclass
class ContextPackage:
    """Assembled context for a task with rich metadata."""
    task_description: str
    readme_files: List[str] = field(default_factory=list)
    spec_files: List[str] = field(default_factory=list)
    wiki_files: List[str] = field(default_factory=list)
    code_files: List[str] = field(default_factory=list)
    dependency_maps: List[str] = field(default_factory=list)
    related_tags: List[str] = field(default_factory=list)
    
    # NEW: Enhanced metadata
    file_metadata: Dict[str, FileMetadata] = field(default_factory=dict)
    assembly_stats: Dict[str, Any] = field(default_factory=dict)
    search_strategy: str = "keyword"  # 'keyword' or 'semantic'
    project_tree: str = ""


# ============================================================================
# CONTEXT ASSEMBLER
# ============================================================================

class ContextAssembler:
    """
    Enhanced context assembler with dual_memory integration.
    
    Features:
    - Semantic search via dual_memory (with keyword fallback)
    - Rich metadata for each file (why included, score, keywords)
    - Adaptive tag extraction (handles 0-6 tags per file)
    - File ranking by relevance
    - Project structure tree
    """
    
    # Synonym mapping for keyword extraction (RU/EN)
    KEYWORD_SYNONYMS = {
        'analytics': ['analytics', 'аналитика', 'analysis', 'анализ', 'stats'],
        'memory': ['memory', 'память', 'embedding', 'embeddings', 'vector'],
        'search': ['search', 'поиск', 'retrieval', 'find', 'query'],
        'pipeline': ['pipeline', 'конвейер', 'processing', 'обработка', 'flow'],
        'splitter': ['splitter', 'split', 'разделение', 'chunk'],
        'grouper': ['grouper', 'group', 'группировка', 'cluster'],
        'linker': ['linker', 'link', 'связь', 'relation'],
        'tagger': ['tagger', 'tag', 'теги', 'label'],
        'ontology': ['ontology', 'онтология', 'taxonomy', 'classification'],
        'transcriber': ['transcriber', 'transcription', 'транскрипция', 'speech'],
        'vision': ['vision', 'image', 'изображение', 'visual', 'ocr'],
        'context': ['context', 'контекст', 'prompt', 'assembly'],
        'dependency': ['dependency', 'зависимость', 'import', 'require'],
        'test': ['test', 'тест', 'testing', 'validation'],
    }
    
    def __init__(self, project_root: Path):
        """
        Initialize context assembler with optional dual_memory.
        
        Args:
            project_root: Path to project root directory
        """
        # Store project root for resolving relative paths
        self.project_root = project_root
        
        # Docs directory contains specs, wiki, automation scripts
        self.docs_dir = project_root / 'docs'
        
        # Current keywords extracted from task - used for ranking
        self.current_keywords: List[str] = []
        
        # Dual memory for semantic search (optional, may fail)
        self.dual_memory = None
        
        # Flag: True if semantic search available, False for keyword fallback
        self.use_semantic = False
        
        # Try to initialize dual_memory for semantic search
        self._init_dual_memory()
    
    def _init_dual_memory(self):
        """
        Initialize dual_memory for semantic search if available.
        Falls back to keyword search if dual_memory cannot be loaded.
        """
        try:
            # Import isolated dual memory from docs namespace (not main project)
            from utils.docs_dual_memory import DocsDualMemory
            
            # Create new dual memory instance for semantic search
            self.dual_memory = DocsDualMemory()
            
            # Enable semantic search mode
            self.use_semantic = True
            
            # Log successful initialization
            logger.info("✅ Using dual_memory for semantic search")
            
        except (ImportError, ModuleNotFoundError) as e:
            # sentence-transformers not installed or module missing
            logger.warning(f"⚠️ Dual memory unavailable, using keyword fallback: {e}")
            self.use_semantic = False
            
        except Exception as e:
            # Other errors (e.g., embedding model download failed)
            logger.warning(f"⚠️ Dual memory init error, using keyword fallback: {e}")
            self.use_semantic = False
    
    # ========================================================================
    # MAIN ASSEMBLY METHODS
    # ========================================================================
    
    def assemble_for_task(self, task_description: str) -> ContextPackage:
        """Assemble context based on task description."""
        start_time = time.time()
        
        package = ContextPackage(
            task_description=task_description,
            search_strategy="semantic" if self.use_semantic else "keyword"
        )
        
        # Always include main README
        self._add_file_with_metadata(
            package, 
            str(self.docs_dir / 'README.MD'),
            reason="Main documentation navigation hub",
            score=1.0,
            content_type='readme'
        )
        
        # Extract keywords for fallback/ranking
        self.current_keywords = self._extract_keywords_advanced(task_description)
        
        if self.use_semantic:
            # Semantic search via dual_memory
            self._assemble_semantic(package, task_description)
        else:
            # Keyword-based fallback
            self._assemble_keyword(package)
        
        # Find dependency maps for code files
        for code_file in package.code_files:
            dep_map = self._find_dependency_map(code_file)
            if dep_map:
                self._add_file_with_metadata(
                    package, dep_map,
                    reason=f"Dependency map for {Path(code_file).name}",
                    score=0.5,
                    content_type='dependency'
                )
        
        # Add project structure tree
        package.project_tree = self._generate_project_tree()
        
        # Assembly stats
        elapsed = time.time() - start_time
        package.assembly_stats = {
            'time_seconds': round(elapsed, 3),
            'total_files': len(package.file_metadata),
            'search_strategy': package.search_strategy,
            'keywords_used': self.current_keywords[:5],
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Assembled context: {len(package.file_metadata)} files in {elapsed:.2f}s")
        return package
    
    def assemble_for_file(self, file_path: str) -> ContextPackage:
        """Assemble context for modifying a specific file."""
        start_time = time.time()
        
        package = ContextPackage(
            task_description=f"Modify {file_path}",
            search_strategy="file_based"
        )
        
        # Add main README
        self._add_file_with_metadata(
            package,
            str(self.docs_dir / 'README.MD'),
            reason="Main documentation navigation",
            score=1.0,
            content_type='readme'
        )
        
        # Add directory README if exists
        file_dir = Path(file_path).parent
        dir_readme = self.project_root / file_dir / 'README.MD'
        if dir_readme.exists():
            self._add_file_with_metadata(
                package,
                str(dir_readme),
                reason=f"Directory documentation for {file_dir}",
                score=0.9,
                content_type='readme'
            )
        
        # Add the target file
        full_path = self.project_root / file_path
        if full_path.exists():
            self._add_file_with_metadata(
                package,
                file_path,
                reason="Target file for modification",
                score=1.0,
                content_type='code'
            )
        
        # Find spec for this file
        file_stem = Path(file_path).stem
        spec_patterns = [
            self.docs_dir / 'specs' / f'{file_stem}_spec.md',
            self.docs_dir / 'specs' / f'{file_stem}.md',
        ]
        for spec_file in spec_patterns:
            if spec_file.exists():
                self._add_file_with_metadata(
                    package,
                    str(spec_file.relative_to(self.project_root)),
                    reason=f"Specification for {file_stem}",
                    score=0.95,
                    content_type='spec'
                )
                break
        
        # Find dependency map
        dep_map = self._find_dependency_map(file_path)
        if dep_map:
            self._add_file_with_metadata(
                package, dep_map,
                reason=f"Dependency map for {Path(file_path).name}",
                score=0.8,
                content_type='dependency'
            )
        
        # Extract tags from file
        package.related_tags = self._extract_tags_from_file(file_path)
        
        # Add project structure
        package.project_tree = self._generate_project_tree()
        
        # Stats
        elapsed = time.time() - start_time
        package.assembly_stats = {
            'time_seconds': round(elapsed, 3),
            'total_files': len(package.file_metadata),
            'search_strategy': 'file_based',
            'target_file': file_path,
            'timestamp': datetime.now().isoformat()
        }
        
        return package
    
    def assemble_for_component(self, component_name: str) -> ContextPackage:
        """Assemble context for a component."""
        start_time = time.time()
        
        package = ContextPackage(
            task_description=f"Work on {component_name} component",
            search_strategy="component_based"
        )
        
        # Add main README
        self._add_file_with_metadata(
            package,
            str(self.docs_dir / 'README.MD'),
            reason="Main documentation navigation",
            score=1.0,
            content_type='readme'
        )
        
        # Set keywords for component
        self.current_keywords = [component_name.lower()]
        
        # Find component directories
        for code_dir in ['processing', 'utils', 'scripts', 'docs/automation']:
            comp_dir = self.project_root / code_dir
            if not comp_dir.exists():
                continue
            
            # Find files matching component name
            for py_file in comp_dir.glob('*.py'):
                if component_name.lower() in py_file.name.lower():
                    self._add_file_with_metadata(
                        package,
                        str(py_file.relative_to(self.project_root)),
                        reason=f"Component file matching '{component_name}'",
                        score=0.9,
                        content_type='code'
                    )
        
        # Find specs mentioning component
        specs = self._find_relevant_specs_ranked(self.current_keywords, max_results=3)
        for spec in specs:
            self._add_file_with_metadata(
                package,
                spec['path'],
                reason=spec['reason'],
                score=spec['score'] / 100,  # Normalize
                content_type='spec',
                keywords=spec.get('keywords', [])
            )
        
        # Find wiki pages
        wikis = self._find_relevant_wiki_ranked(self.current_keywords, max_results=2)
        for wiki in wikis:
            self._add_file_with_metadata(
                package,
                wiki['path'],
                reason=wiki['reason'],
                score=wiki['score'] / 100,
                content_type='wiki',
                keywords=wiki.get('keywords', [])
            )
        
        # Add project structure
        package.project_tree = self._generate_project_tree()
        
        # Stats
        elapsed = time.time() - start_time
        package.assembly_stats = {
            'time_seconds': round(elapsed, 3),
            'total_files': len(package.file_metadata),
            'search_strategy': 'component_based',
            'component': component_name,
            'timestamp': datetime.now().isoformat()
        }
        
        return package
    
    # ========================================================================
    # SEMANTIC SEARCH
    # ========================================================================
    
    def _assemble_semantic(self, package: ContextPackage, query: str):
        """Use dual_memory for semantic search."""
        try:
            results = self.dual_memory.unified_search(query, top_k=15)
            
            for result in results:
                # Determine content type from path
                source_file = result.source_file
                if 'spec' in source_file:
                    content_type = 'spec'
                elif 'wiki' in source_file:
                    content_type = 'wiki'
                elif source_file.endswith('.py'):
                    content_type = 'code'
                elif source_file.endswith('.md'):
                    content_type = 'readme'
                else:
                    content_type = 'other'
                
                self._add_file_with_metadata(
                    package,
                    source_file,
                    reason=f"Semantic match (type: {result.content_type})",
                    score=result.score,
                    content_type=content_type,
                    line_range=result.line_range
                )
            
            logger.info(f"Semantic search returned {len(results)} results")
            
        except Exception as e:
            logger.warning(f"Semantic search failed, using keyword fallback: {e}")
            self._assemble_keyword(package)
    
    def _assemble_keyword(self, package: ContextPackage):
        """Keyword-based assembly (fallback)."""
        # Find specs
        specs = self._find_relevant_specs_ranked(self.current_keywords, max_results=5)
        for spec in specs:
            self._add_file_with_metadata(
                package,
                spec['path'],
                reason=spec['reason'],
                score=spec['score'] / 100,
                content_type='spec',
                keywords=spec.get('keywords', [])
            )
        
        # Find wiki
        wikis = self._find_relevant_wiki_ranked(self.current_keywords, max_results=3)
        for wiki in wikis:
            self._add_file_with_metadata(
                package,
                wiki['path'],
                reason=wiki['reason'],
                score=wiki['score'] / 100,
                content_type='wiki',
                keywords=wiki.get('keywords', [])
            )
        
        # Find code
        codes = self._find_relevant_code_ranked(self.current_keywords, max_results=5)
        for code in codes:
            self._add_file_with_metadata(
                package,
                code['path'],
                reason=code['reason'],
                score=code['score'] / 100,
                content_type='code',
                keywords=code.get('keywords', [])
            )
    
    # ========================================================================
    # KEYWORD EXTRACTION
    # ========================================================================
    
    def _extract_keywords_advanced(self, text: str) -> List[str]:
        """Extract keywords with synonym support (RU/EN)."""
        keywords = set()
        text_lower = text.lower()
        
        # Check all synonyms
        for canonical, variants in self.KEYWORD_SYNONYMS.items():
            for variant in variants:
                if variant in text_lower:
                    keywords.add(canonical)
                    break
        
        return list(keywords)
    
    # ========================================================================
    # RANKED FILE FINDING
    # ========================================================================
    
    def _find_relevant_specs_ranked(self, keywords: List[str], max_results: int = 5) -> List[Dict]:
        """Find and rank specs by relevance."""
        return self._rank_files_in_directory(
            self.docs_dir / 'specs',
            '*.md',
            keywords,
            max_results
        )
    
    def _find_relevant_wiki_ranked(self, keywords: List[str], max_results: int = 3) -> List[Dict]:
        """Find and rank wiki files."""
        return self._rank_files_in_directory(
            self.docs_dir / 'wiki',
            '*.md',
            keywords,
            max_results
        )
    
    def _find_relevant_code_ranked(self, keywords: List[str], max_results: int = 5) -> List[Dict]:
        """Find and rank code files."""
        all_results = []
        for code_dir in ['processing', 'utils', 'scripts']:
            code_path = self.project_root / code_dir
            if code_path.exists():
                results = self._rank_files_in_directory(
                    code_path,
                    '*.py',
                    keywords,
                    max_results
                )
                all_results.extend(results)
        
        # Sort all and return top N
        all_results.sort(key=lambda x: x['score'], reverse=True)
        return all_results[:max_results]
    
    def _rank_files_in_directory(
        self, 
        directory: Path, 
        pattern: str,
        keywords: List[str],
        max_results: int
    ) -> List[Dict]:
        """Rank files in a directory by keyword relevance."""
        results = []
        
        if not directory.exists():
            return results
        
        for file_path in directory.glob(pattern):
            try:
                # Read file content for keyword matching
                content = file_path.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                # File unreadable or binary - skip to next file
                continue
            
            # Calculate score
            score = 0
            matched_keywords = []
            filename_lower = file_path.name.lower()
            content_lower = content.lower()
            
            for keyword in keywords:
                # Filename match (higher weight)
                if keyword in filename_lower:
                    score += 10
                    matched_keywords.append(keyword)
                
                # Content matches
                content_matches = content_lower.count(keyword)
                if content_matches > 0:
                    score += min(content_matches, 10)  # Cap at 10
                    if keyword not in matched_keywords:
                        matched_keywords.append(keyword)
            
            if score > 0:
                rel_path = str(file_path.relative_to(self.project_root))
                results.append({
                    'path': rel_path,
                    'score': score,
                    'keywords': matched_keywords,
                    'reason': f"Matched {len(matched_keywords)} keywords: {', '.join(matched_keywords)}"
                })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]
    
    # ========================================================================
    # ADAPTIVE TAG EXTRACTION
    # ========================================================================
    
    def _extract_tagged_content_adaptive(self, file_path: str) -> Dict[str, Any]:
        """Adaptively extract content based on tag structure."""
        try:
            # Resolve full path from project root
            full_path = self.project_root / file_path
            
            # Read entire file content for tag extraction
            content = full_path.read_text(encoding='utf-8')
            
        except (OSError, UnicodeDecodeError) as e:
            # File unreadable or has encoding issues
            return {'strategy': 'error', 'content': f'(Could not read file: {e})'}
        
        # Extract all tags
        tag_pattern = r'<!--TAG:([a-zA-Z0-9_]+)-->(.*?)<!--/TAG:\1-->'
        tags = list(re.finditer(tag_pattern, content, re.DOTALL))
        
        if not tags:
            # No tags - return full file with warning
            return {
                'strategy': 'full_file',
                'content': content,
                'note': 'No semantic tags found'
            }
        
        elif len(tags) == 1:
            tag_content = tags[0].group(2).strip()
            
            # Check if it's only docstring (< 500 chars)
            if len(tag_content) < 500:
                return {
                    'strategy': 'docstring_only',
                    'docstring': tag_content,
                    'full_content': content,
                    'note': 'Tag contains only docstring, including full file'
                }
            else:
                return {
                    'strategy': 'single_tag',
                    'content': tag_content
                }
        
        elif len(tags) > 5:
            # Too many tags - prioritize by relevance
            scored_tags = []
            for tag in tags:
                tag_name = tag.group(1)
                tag_content = tag.group(2).strip()
                
                # Score by keyword match
                score = 0
                for keyword in self.current_keywords:
                    if keyword.lower() in tag_content.lower():
                        score += 1
                
                scored_tags.append({
                    'name': tag_name,
                    'content': tag_content,
                    'score': score
                })
            
            # Sort and take top 3
            scored_tags.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'strategy': 'prioritized_tags',
                'tags': scored_tags[:3],
                'note': f'Selected top 3 of {len(tags)} tags by relevance'
            }
        
        else:
            # Normal case - 2-5 tags
            return {
                'strategy': 'multiple_tags',
                'tags': [
                    {'name': tag.group(1), 'content': tag.group(2).strip()}
                    for tag in tags
                ]
            }
    
    def _extract_tags_from_file(self, file_path: str) -> List[str]:
        """Extract tag names from a file."""
        tags = []
        try:
            # Resolve full path from project root
            full_path = self.project_root / file_path
            
            # Read file content for tag extraction
            content = full_path.read_text(encoding='utf-8')
            
            # Regex pattern to find opening semantic tags
            tag_pattern = r'<!--TAG:([a-zA-Z0-9_]+)-->'
            
            # Extract all tag identifiers from file
            tags = re.findall(tag_pattern, content)
            
        except (OSError, UnicodeDecodeError):
            # File unreadable - return empty tags list
            pass
        return tags
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _add_file_with_metadata(
        self,
        package: ContextPackage,
        file_path: str,
        reason: str,
        score: float,
        content_type: str,
        keywords: List[str] = None,
        line_range: Tuple[int, int] = None
    ):
        """Add file to package with metadata."""
        if not file_path:
            return
        
        # Skip if already added (keep highest score)
        if file_path in package.file_metadata:
            if package.file_metadata[file_path].relevance_score >= score:
                return
        
        # Get file stats
        full_path = self.project_root / file_path
        try:
            stat = full_path.stat()
            size_kb = round(stat.st_size / 1024, 2)
            modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except:
            size_kb = 0
            modified = "unknown"
        
        # Extract tags
        tags = self._extract_tags_from_file(file_path)
        
        # Create metadata
        metadata = FileMetadata(
            path=file_path,
            reason=reason,
            relevance_score=round(score, 3),
            matched_keywords=keywords or self.current_keywords[:3],
            content_type=content_type,
            file_size_kb=size_kb,
            last_modified=modified,
            tags=tags,
            line_range=line_range
        )
        package.file_metadata[file_path] = metadata
        
        # Add to appropriate list
        if content_type == 'readme':
            if file_path not in package.readme_files:
                package.readme_files.append(file_path)
        elif content_type == 'spec':
            if file_path not in package.spec_files:
                package.spec_files.append(file_path)
        elif content_type == 'wiki':
            if file_path not in package.wiki_files:
                package.wiki_files.append(file_path)
        elif content_type == 'code':
            if file_path not in package.code_files:
                package.code_files.append(file_path)
        elif content_type == 'dependency':
            if file_path not in package.dependency_maps:
                package.dependency_maps.append(file_path)
    
    def _find_dependency_map(self, file_path: str) -> Optional[str]:
        """Find dependency map for a file."""
        file_stem = Path(file_path).stem
        dep_file = self.docs_dir / 'memory' / 'dependencies' / f'{file_stem}_dependencies.json'
        
        if dep_file.exists():
            return str(dep_file.relative_to(self.project_root))
        return None
    
    def _generate_project_tree(self) -> str:
        """Generate project structure summary."""
        try:
            spec_count = len(list((self.docs_dir / 'specs').glob('*.md'))) if (self.docs_dir / 'specs').exists() else 0
            wiki_count = len(list((self.docs_dir / 'wiki').glob('*.md'))) if (self.docs_dir / 'wiki').exists() else 0
            automation_count = len(list((self.docs_dir / 'automation').glob('*.py'))) if (self.docs_dir / 'automation').exists() else 0
        except:
            spec_count = wiki_count = automation_count = 0
        
        return f"""## Project Structure

```
{self.project_root.name}/
├── docs/
│   ├── README.MD (Main navigation - START HERE)
│   ├── specs/ ({spec_count} specifications)
│   ├── wiki/ ({wiki_count} guides)
│   ├── automation/ ({automation_count} automation scripts)
│   └── memory/ (Embeddings and dependency graphs)
├── processing/ (Pipeline stages 01-09)
├── utils/ (Shared utilities)
├── scripts/ (Standalone scripts)
└── tests/ (Test suites)
```

## How to Navigate
1. **Start with docs/README.MD** for system overview
2. **Check docs/specs/** for formal specifications
3. **Check docs/wiki/** for conceptual guides
4. **Code is in processing/ and utils/**
"""
    
    # ========================================================================
    # OUTPUT GENERATION
    # ========================================================================
    
    def generate_context_file(self, package: ContextPackage, output_path: Path):
        """Generate context file with rich metadata."""
        lines = []
        
        # Header with stats
        lines.append("# Context Assembly Report\n")
        lines.append(f"**Task**: {package.task_description}")
        lines.append(f"**Strategy**: {package.search_strategy}")
        lines.append(f"**Total files**: {len(package.file_metadata)}")
        lines.append(f"**Assembly time**: {package.assembly_stats.get('time_seconds', 0):.3f}s")
        lines.append(f"**Timestamp**: {package.assembly_stats.get('timestamp', 'N/A')}")
        if package.assembly_stats.get('keywords_used'):
            lines.append(f"**Keywords**: {', '.join(package.assembly_stats['keywords_used'])}")
        lines.append("\n" + "=" * 60 + "\n")
        
        # Project structure
        if package.project_tree:
            lines.append(package.project_tree)
            lines.append("\n" + "=" * 60 + "\n")
        
        # Files sorted by score
        sorted_files = sorted(
            package.file_metadata.items(),
            key=lambda x: x[1].relevance_score,
            reverse=True
        )
        
        for i, (file_path, metadata) in enumerate(sorted_files, 1):
            lines.append(f"## {i}. {Path(file_path).name} (Score: {metadata.relevance_score})")
            lines.append("")
            lines.append(f"**Path**: `{file_path}`")
            lines.append(f"**Type**: {metadata.content_type}")
            lines.append(f"**Why included**: {metadata.reason}")
            
            if metadata.matched_keywords:
                lines.append(f"**Matched keywords**: {', '.join(metadata.matched_keywords)}")
            
            lines.append(f"**File size**: {metadata.file_size_kb} KB")
            lines.append(f"**Last modified**: {metadata.last_modified}")
            
            if metadata.tags:
                lines.append(f"**Tags**: {', '.join(f'`{t}`' for t in metadata.tags[:5])}")
            
            if metadata.line_range:
                lines.append(f"**Lines**: {metadata.line_range[0]}-{metadata.line_range[1]}")
            
            lines.append("\n**Content**:\n")
            
            # Include file content with adaptive tag handling
            try:
                full_path = self.project_root / file_path
                if file_path.endswith('.json'):
                    lines.append("```json")
                elif file_path.endswith('.py'):
                    lines.append("```python")
                else:
                    lines.append("```markdown")
                
                content = full_path.read_text(encoding='utf-8')
                
                # Truncate very long files
                max_chars = 8000
                if len(content) > max_chars:
                    content = content[:max_chars] + f"\n\n... (truncated, {len(content)} total chars)"
                
                lines.append(content)
                lines.append("```")
            except Exception as e:
                lines.append(f"(Could not read file: {e})")
            
            lines.append("\n" + "-" * 60 + "\n")
        
        # Tags summary
        all_tags = set()
        for metadata in package.file_metadata.values():
            all_tags.update(metadata.tags)
        
        if all_tags:
            lines.append("## Related Tags\n")
            for tag in sorted(all_tags)[:20]:
                lines.append(f"- `<!--TAG:{tag}-->`")
        
        # Write file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Context saved to: {output_path}")


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Assemble context for AI agents (Enhanced)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 assemble_context.py --task "implement analytics pipeline" --output context.md
  python3 assemble_context.py --file processing/07_analytics.py --output context.md
  python3 assemble_context.py --component analytics --output context.md
        """
    )
    parser.add_argument('--task', type=str, help='Task description')
    parser.add_argument('--file', type=str, help='Specific file to work on')
    parser.add_argument('--component', type=str, help='Component name')
    parser.add_argument('--output', type=str, default='docs/temp/context.md',
                        help='Output file path (default: docs/temp/context.md)')
    
    args = parser.parse_args()
    
    if not any([args.task, args.file, args.component]):
        parser.print_help()
        return
    
    project_root = Path(__file__).parent.parent
    assembler = ContextAssembler(project_root)
    
    # Assemble context
    if args.task:
        package = assembler.assemble_for_task(args.task)
    elif args.file:
        package = assembler.assemble_for_file(args.file)
    elif args.component:
        package = assembler.assemble_for_component(args.component)
    
    # Generate output
    output_path = project_root / args.output
    assembler.generate_context_file(package, output_path)
    
    # Print summary
    print(f"\n✅ Context assembled successfully!")
    print(f"   Strategy: {package.search_strategy}")
    print(f"   Files: {len(package.file_metadata)}")
    print(f"   Time: {package.assembly_stats.get('time_seconds', 0):.3f}s")
    print(f"   Output: {output_path}")


if __name__ == '__main__':
    main()
