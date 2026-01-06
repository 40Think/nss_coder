---
description: "Assembles context from project files for AI agents (Enhanced v2)"
date: 2025-12-12
source_file: assemble_context.py
tags: automation, context, AI, prompt, semantic_search, dual_memory
---

# assemble_context.py - Pseudocode (Enhanced v2)

<!--TAG:pseudo_assemble_context-->

## PURPOSE
Assembles relevant context from project files for AI agents.
Supports semantic search via dual_memory with fallback to keyword search.
Adds metadata and provenance for each file.

## KEY ENHANCEMENTS v2
1. **Semantic search** via dual_memory.py
2. **Metadata/Provenance** - explanation of why each file is included
3. **Adaptive tag extraction** - handling 0-6+ tags
4. **File ranking** - prioritizing by relevance
5. **RU/EN synonyms** - support for Russian keywords

## DATA STRUCTURES

### FileMetadata (dataclass) [NEW]
```pseudo
DATACLASS FileMetadata:
    path: STRING                  # Path to file
    reason: STRING                # Why included
    relevance_score: FLOAT        # 0.0-1.0
    matched_keywords: LIST[STRING]
    content_type: STRING          # 'spec', 'wiki', 'code', 'readme', 'dependency'
    file_size_kb: FLOAT
    last_modified: STRING         # ISO timestamp
    tags: LIST[STRING]            # Semantic tags
    line_range: TUPLE[INT, INT]   # Optional: lines
```

### ContextPackage (dataclass) [ENHANCED]
```pseudo
DATACLASS ContextPackage:
    task_description: STRING
    readme_files: LIST[STRING]
    spec_files: LIST[STRING]
    wiki_files: LIST[STRING]
    code_files: LIST[STRING]
    dependency_maps: LIST[STRING]
    related_tags: LIST[STRING]
    
    # NEW FIELDS
    file_metadata: DICT[STRING, FileMetadata]  # Metadata for each file
    assembly_stats: DICT[STRING, ANY]          # Assembly statistics
    search_strategy: STRING                     # 'semantic' or 'keyword'
    project_tree: STRING                        # Project structure
```

## CLASS: ContextAssembler

### Initialization [ENHANCED]
```pseudo
CLASS ContextAssembler:
    # Synonym mapping for search terms
    KEYWORD_SYNONYMS = {
        'analytics': ['analytics', 'analysis', 'stats', 'data'],
        'memory': ['memory', 'storage', 'embedding', 'embeddings'],
        'search': ['search', 'retrieval', 'find', 'query'],
        'pipeline': ['pipeline', 'processing', 'flow', 'workflow'],
        # ... and others
    }
    
    FUNCTION __init__(project_root):
        self.project_root = project_root
        self.docs_dir = project_root / 'docs'
        self.current_keywords = []
        
        # Attempt to initialize dual_memory
        TRY:
            # Import from isolated docs namespace (not main project)
            FROM docs.utils.docs_dual_memory IMPORT DocsDualMemory
            self.dual_memory = DocsDualMemory()
            self.use_semantic = TRUE
            LOG "✅ Using dual_memory for semantic search"
        CATCH (ImportError, ModuleNotFoundError):
            self.use_semantic = FALSE
            LOG "⚠️ Dual memory unavailable, using keyword fallback"
        CATCH Exception:
            self.use_semantic = FALSE
            LOG "⚠️ Dual memory init error, using keyword fallback"
```

### assemble_for_task [ENHANCED]
```pseudo
FUNCTION assemble_for_task(task_description):
    start_time = GET current time
    
    # Step 1: Create package with metadata
    package = NEW ContextPackage()
    package.search_strategy = "semantic" IF use_semantic ELSE "keyword"
    
    # Step 2: Always add README with metadata
    CALL _add_file_with_metadata(
        package,
        "docs/README.MD",
        reason="Main documentation navigation hub",
        score=1.0,
        content_type='readme'
    )
    
    # Step 3: Extract keywords with synonyms
    self.current_keywords = CALL _extract_keywords_advanced(task_description)
    
    # Step 4: Choose search strategy
    IF use_semantic:
        CALL _assemble_semantic(package, task_description)
    ELSE:
        CALL _assemble_keyword(package)
    
    # Step 5: Add dependency maps
    FOR EACH code_file IN package.code_files:
        dep_map = CALL _find_dependency_map(code_file)
        IF dep_map EXISTS:
            CALL _add_file_with_metadata(package, dep_map, ...)
    
    # Step 6: Add project structure
    package.project_tree = CALL _generate_project_tree()
    
    # Step 7: Collect statistics
    elapsed = GET current time - start_time
    package.assembly_stats = {
        'time_seconds': elapsed,
        'total_files': LENGTH(package.file_metadata),
        'search_strategy': package.search_strategy,
        'keywords_used': self.current_keywords[:5],
        'timestamp': CURRENT ISO timestamp
    }
    
    RETURN package
```

### assemble_for_file [NEW - added 2025-12-12]
```pseudo
FUNCTION assemble_for_file(file_path):
    """Assemble context for modifying a specific file."""
    start_time = GET current time
    
    # Create package for file-specific context
    package = NEW ContextPackage()
    package.search_strategy = "file_based"
    
    # Always add main README
    CALL _add_file_with_metadata(package, "docs/README.MD", 
         reason="Main documentation navigation", score=1.0)
    
    # Add directory README if exists
    file_dir = PARENT of file_path
    IF directory_readme EXISTS:
        CALL _add_file_with_metadata(package, dir_readme, 
             reason="Directory documentation", score=0.9)
    
    # Add target file
    IF file EXISTS:
        CALL _add_file_with_metadata(package, file_path,
             reason="Target file for modification", score=1.0)
    
    # Find spec for file
    file_stem = BASENAME of file_path WITHOUT extension
    spec_patterns = [
        "docs/specs/{file_stem}_spec.md",
        "docs/specs/{file_stem}.md"
    ]
    FOR spec IN spec_patterns:
        IF spec EXISTS:
            CALL _add_file_with_metadata(package, spec,
                 reason="Specification for file", score=0.95)
            BREAK
    
    # Find dependency map
    dep_map = CALL _find_dependency_map(file_path)
    IF dep_map EXISTS:
        CALL _add_file_with_metadata(package, dep_map, ...)
    
    # Extract tags from target file
    package.related_tags = CALL _extract_tags_from_file(file_path)
    
    # Add project structure
    package.project_tree = CALL _generate_project_tree()
    
    RETURN package
```

### assemble_for_component [NEW - added 2025-12-12]
```pseudo
FUNCTION assemble_for_component(component_name):
    """Assemble context for working on a component."""
    start_time = GET current time
    
    # Create package for component-based context
    package = NEW ContextPackage()
    package.search_strategy = "component_based"
    
    # Always add main README
    CALL _add_file_with_metadata(package, "docs/README.MD", ...)
    
    # Set keywords for component search
    self.current_keywords = [LOWERCASE(component_name)]
    
    # Find matching files in code directories
    FOR dir IN ['processing', 'utils', 'scripts', 'docs/automation']:
        IF dir EXISTS:
            FOR py_file IN GLOB(dir, "*.py"):
                IF component_name IN LOWERCASE(py_file.name):
                    CALL _add_file_with_metadata(package, py_file,
                         reason="Component file matching name", score=0.9)
    
    # Find specs mentioning component
    specs = CALL _find_relevant_specs_ranked(current_keywords, max=3)
    FOR spec IN specs:
        CALL _add_file_with_metadata(package, spec.path, ...)
    
    # Find wiki pages
    wikis = CALL _find_relevant_wiki_ranked(current_keywords, max=2)
    FOR wiki IN wikis:
        CALL _add_file_with_metadata(package, wiki.path, ...)
    
    # Add project structure
    package.project_tree = CALL _generate_project_tree()
    
    RETURN package
```

### _find_relevant_specs_ranked [NEW - added 2025-12-12]
```pseudo
FUNCTION _find_relevant_specs_ranked(keywords, max_results=5):
    """Find and rank spec files by keyword relevance."""
    RETURN CALL _rank_files_in_directory(
        directory=docs/specs,
        pattern="*.md",
        keywords=keywords,
        max_results=max_results
    )
```

### _find_relevant_wiki_ranked [NEW - added 2025-12-12]
```pseudo
FUNCTION _find_relevant_wiki_ranked(keywords, max_results=3):
    """Find and rank wiki files by keyword relevance."""
    RETURN CALL _rank_files_in_directory(
        directory=docs/wiki,
        pattern="*.md",
        keywords=keywords,
        max_results=max_results
    )
```

### _find_relevant_code_ranked [NEW - added 2025-12-12]
```pseudo
FUNCTION _find_relevant_code_ranked(keywords, max_results=5):
    """Find and rank code files across directories."""
    all_results = []
    
    FOR code_dir IN ['processing', 'utils', 'scripts']:
        IF code_dir EXISTS:
            results = CALL _rank_files_in_directory(
                directory=code_dir,
                pattern="*.py",
                keywords=keywords,
                max_results=max_results
            )
            EXTEND all_results WITH results
    
    SORT all_results BY score DESC
    RETURN all_results[:max_results]
```

### _extract_keywords_advanced [NEW]
```pseudo
FUNCTION _extract_keywords_advanced(text):
    keywords = SET()
    text_lower = LOWERCASE(text)
    
    # Check all synonyms
    FOR EACH (canonical, variants) IN KEYWORD_SYNONYMS:
        FOR EACH variant IN variants:
            IF variant IN text_lower:
                ADD canonical TO keywords
                BREAK
    
    RETURN LIST(keywords)
```

### _assemble_semantic [NEW]
```pseudo
FUNCTION _assemble_semantic(package, query):
    TRY:
        results = dual_memory.unified_search(query, top_k=15)
        
        FOR EACH result IN results:
            # Determine content type
            content_type = DETECT from result.source_file
            
            CALL _add_file_with_metadata(
                package,
                result.source_file,
                reason="Semantic match (type: {result.content_type})",
                score=result.score,
                content_type=content_type,
                line_range=result.line_range
            )
    CATCH Exception:
        LOG "Semantic search failed, using fallback"
        CALL _assemble_keyword(package)
```

### _add_file_with_metadata [NEW]
```pseudo
FUNCTION _add_file_with_metadata(package, file_path, reason, score, content_type, keywords=None, line_range=None):
    # Skip if already added with higher score
    IF file_path IN package.file_metadata:
        IF package.file_metadata[file_path].relevance_score >= score:
            RETURN
    
    # Get file statistics
    stat = GET file statistics(file_path)
    size_kb = stat.size / 1024
    modified = FORMAT stat.mtime AS ISO
    
    # Extract tags
    tags = CALL _extract_tags_from_file(file_path)
    
    # Create metadata
    metadata = NEW FileMetadata(
        path=file_path,
        reason=reason,
        relevance_score=ROUND(score, 3),
        matched_keywords=keywords OR current_keywords[:3],
        content_type=content_type,
        file_size_kb=size_kb,
        last_modified=modified,
        tags=tags,
        line_range=line_range
    )
    
    package.file_metadata[file_path] = metadata
    
    # Add to appropriate list based on content_type
    APPEND file_path TO appropriate list based on content_type
```

### _extract_tagged_content_adaptive [NEW]
```pseudo
FUNCTION _extract_tagged_content_adaptive(file_path):
    content = READ file_path
    
    # Find all tags
    tags = REGEX findall '<!--TAG:(.+?)-->(.+?)<!--/TAG:\1-->' IN content
    
    IF LENGTH(tags) == 0:
        # No tags - return full file
        RETURN {
            'strategy': 'full_file',
            'content': content,
            'note': 'No semantic tags found'
        }
    
    ELSE IF LENGTH(tags) == 1:
        tag_content = tags[0].content
        
        IF LENGTH(tag_content) < 500:
            # Only docstring - include full file
            RETURN {
                'strategy': 'docstring_only',
                'docstring': tag_content,
                'full_content': content,
                'note': 'Tag contains only docstring'
            }
        ELSE:
            RETURN {
                'strategy': 'single_tag',
                'content': tag_content
            }
    
    ELSE IF LENGTH(tags) > 5:
        # Too many tags - prioritize
        scored_tags = []
        FOR EACH tag IN tags:
            score = COUNT keyword matches in tag.content
            APPEND (tag, score) TO scored_tags
        
        SORT scored_tags BY score DESC
        
        RETURN {
            'strategy': 'prioritized_tags',
            'tags': TOP 3 scored_tags,
            'note': 'Selected top 3 of N tags by relevance'
        }
    
    ELSE:
        # Normal case - 2-5 tags
        RETURN {
            'strategy': 'multiple_tags',
            'tags': ALL tags
        }
```

### _rank_files_in_directory [NEW]
```pseudo
FUNCTION _rank_files_in_directory(directory, pattern, keywords, max_results):
    results = []
    
    FOR EACH file IN GLOB(directory, pattern):
        content = READ file
        score = 0
        matched_keywords = []
        
        FOR EACH keyword IN keywords:
            # Filename match (higher weight)
            IF keyword IN LOWERCASE(file.name):
                score += 10
                APPEND keyword TO matched_keywords
            
            # Content matches
            content_matches = COUNT keyword IN LOWERCASE(content)
            IF content_matches > 0:
                score += MIN(content_matches, 10)
                IF keyword NOT IN matched_keywords:
                    APPEND keyword TO matched_keywords
        
        IF score > 0:
            APPEND {
                'path': relative path,
                'score': score,
                'keywords': matched_keywords,
                'reason': "Matched N keywords: ..."
            } TO results
    
    SORT results BY score DESC
    RETURN results[:max_results]
```

### _generate_project_tree [NEW]
```pseudo
FUNCTION _generate_project_tree():
    spec_count = COUNT files IN docs/specs/*.md
    wiki_count = COUNT files IN docs/wiki/*.md
    automation_count = COUNT files IN docs/automation/*.py
    
    RETURN """
## Project Structure

```
{project_name}/
├── docs/
│   ├── README.MD (Main navigation - START HERE)
│   ├── specs/ ({spec_count} specifications)
│   ├── wiki/ ({wiki_count} guides)
│   ├── automation/ ({automation_count} scripts)
│   └── memory/ (Embeddings and graphs)
├── processing/ (Pipeline stages 01-09)
├── utils/ (Shared utilities)
└── tests/ (Test suites)
```

## How to Navigate
1. Start with docs/README.MD
2. Check docs/specs/ for specifications
3. Check docs/wiki/ for guides
4. Code is in processing/ and utils/
"""
```

### generate_context_file [ENHANCED]
```pseudo
FUNCTION generate_context_file(package, output_path):
    lines = []
    
    # Header with stats
    APPEND "# Context Assembly Report"
    APPEND "**Task**: {package.task_description}"
    APPEND "**Strategy**: {package.search_strategy}"
    APPEND "**Total files**: {LENGTH(package.file_metadata)}"
    APPEND "**Assembly time**: {package.assembly_stats.time_seconds}s"
    APPEND "**Keywords**: {package.assembly_stats.keywords_used}"
    
    # Project structure
    APPEND package.project_tree
    
    # Files sorted by score
    sorted_files = SORT package.file_metadata BY relevance_score DESC
    
    FOR EACH (file_path, metadata) IN sorted_files:
        APPEND "## {index}. {filename} (Score: {metadata.relevance_score})"
        APPEND "**Path**: {file_path}"
        APPEND "**Type**: {metadata.content_type}"
        APPEND "**Why included**: {metadata.reason}"
        APPEND "**Matched keywords**: {metadata.matched_keywords}"
        APPEND "**File size**: {metadata.file_size_kb} KB"
        APPEND "**Tags**: {metadata.tags}"
        
        APPEND "**Content**:"
        content = READ file_path
        IF LENGTH(content) > 8000:
            content = TRUNCATE content + "... (truncated)"
        APPEND code block with content
    
    WRITE lines TO output_path
```

## CLI

```pseudo
FUNCTION main():
    parser = NEW ArgumentParser("Assemble context for AI agents")
    parser.add_argument('--task', help="Task description")
    parser.add_argument('--file', help="Specific file to work on")
    parser.add_argument('--component', help="Component name")
    parser.add_argument('--output', default="docs/temp/context.md")
    
    args = PARSE arguments
    
    assembler = NEW ContextAssembler(project_root)
    
    IF args.task:
        package = assembler.assemble_for_task(args.task)
    ELSE IF args.file:
        package = assembler.assemble_for_file(args.file)
    ELSE IF args.component:
        package = assembler.assemble_for_component(args.component)
    
    assembler.generate_context_file(package, args.output)
    
    PRINT "✅ Context assembled successfully!"
    PRINT "   Strategy: {package.search_strategy}"
    PRINT "   Files: {LENGTH(package.file_metadata)}"
    PRINT "   Time: {package.assembly_stats.time_seconds}s"
```

<!--/TAG:pseudo_assemble_context-->
