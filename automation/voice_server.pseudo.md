# voice_server.py - Pseudocode

<!--TAG:voicepal_server_pseudocode-->

## PURPOSE
Flask server for VoicePal v3 with multi-channel search, Total Recall, and hypothesis generation.

> ⚡ **MIGRATED (2025-12-16)**: Whisper backend upgraded from whisper.cpp to **faster-whisper**
> - Performance: **82.7x real-time** on RTX PRO 6000 Blackwell
> - See: `voice_whisper_fast.py` (FasterWhisperService)

## DEPENDENCIES
- Flask, aiohttp, asyncio
- docs.automation.voice_whisper_fast (FasterWhisperService) — MIGRATED 2025-12-16
- docs.utils.docs_dual_memory (DocsDualMemory)
- docs.automation.search_dependencies (DependencySearcher)
- docs.automation.summarize_docs (DocumentSummarizer)
- docs.automation.search_by_tag (TagSearcher)
- docs.utils.docs_llm_backend (DocsLLMBackend)
- voice_processor (VoiceProcessor)

---

## MAIN ENDPOINTS

### /api/project_tree
```
GET /api/project_tree
    project_root = get_project_root()
    tree = build_tree_recursive(project_root, max_depth=5)
    RETURN {success: true, tree: tree}
```

### /api/external_files
```
POST /api/external_files
    INPUT: {paths: [file_paths]}
    
    FOR each path IN paths:
        IF file_extension NOT IN [.md, .txt, .py, .json]:
            SKIP
        IF file_size > 500KB:
            SKIP
        
        content = read_file(path)
        escaped_content = html.escape(content)
        files.append({path, name, content: escaped_content, size_kb, extension})
    
    RETURN {success: true, files: files, errors: errors}
```

### /api/smart_preselect
```
POST /api/smart_preselect
    INPUT: {query: user_query}
    
    tree_simplified = simplify_tree_for_llm(project_tree, max_depth=3)
    
    prompt = f"""Given query: {query}
    Project structure: {tree_simplified}
    
    Suggest relevant directories and files.
    Output JSON: {{"suggested_dirs": [...], "suggested_files": [...]}}"""
    
    llm_response = call_vllm(prompt, temperature=0.3)
    suggestions = parse_json(llm_response)
    
    RETURN {success: true, suggestions: suggestions}
```

### /api/reindex
```
POST /api/reindex
    INPUT: {incremental: bool}
    
    memory = DocsDualMemory()
    memory.build()  # Rebuild embeddings index
    
    RETURN {success: true, message: "Indexes rebuilt"}
```

### /api/get_summaries
```
POST /api/get_summaries
    INPUT: {file_paths: [paths]}
    
    summarizer = DocumentSummarizer()
    summaries = {}
    
    FOR each path IN file_paths[:20]:  # Limit 20
        summary = summarizer.summarize(path, max_length=200)
        summaries[path] = {summary: summary.summary, compression_ratio: summary.compression_ratio}
    
    RETURN {success: true, summaries: summaries}
```

### /api/suggest_tags
```
POST /api/suggest_tags
    INPUT: {query: user_query}
    
    # Get available tags
    searcher = TagSearcher(config)
    available_tags = list(searcher.tag_index.keys())[:100]
    
    # Ask LLM which tags are relevant
    prompt = f"""Available tags: {available_tags[:50]}
    User query: {query}
    
    Respond with JSON array of 3-5 most relevant tags: ["tag1", "tag2"]"""
    
    llm_response = DocsLLMBackend().generate(prompt, max_tokens=100)
    suggested_tags = extract_json_array(llm_response)
    
    RETURN {success: true, suggested_tags: suggested_tags}
```

### /api/search_integrated
```
POST /api/search_integrated
    INPUT: {query, top_k, selected_files, active_context}
    
    # SECURITY: Validate query
    IF query CONTAINS dangerous_patterns [;|&`$()rm sudo wget curl]:
        RETURN 400 "Query contains disallowed characters"
    
    all_results = []
    
    # Channel 1: Embeddings (dual_memory)
    TRY:
        memory = DocsDualMemory()
        desc_results = memory.search_descriptions(query, top_k=top_k/2)
        code_results = memory.search_code(query, top_k=top_k/2)
        
        FOR result IN desc_results + code_results:
            all_results.append({
                file_path, score, excerpt, content_type,
                source: "embeddings",
                source_label: "🔍 Embeddings (70-80%)"
            })
    
    # Channel 2: Semantic (processor fallback)
    TRY:
        processor_results = processor.search_context(query, top_k)
        FOR result IN processor_results:
            IF result NOT IN all_results:
                all_results.append({...source: "processor"})
    
    # Channel 3: Dependencies (for .py files)
    py_files = [f FOR f IN selected_files IF f.endswith('.py')]
    IF py_files:
        searcher = DependencySearcher(project_root)
        FOR py_file IN py_files[:5]:
            dep_info = searcher.search(py_file, include_reverse=True)
            
            # Add imported modules
            FOR import_type, imports IN dep_info.dependencies:
                all_results.append({
                    file_path: import,
                    source: "dependencies",
                    source_label: "📦 Dependencies (85%)"
                })
            
            # Add reverse dependencies
            FOR rev_dep IN dep_info.reverse_dependencies[:3]:
                all_results.append({
                    file_path: rev_dep,
                    source: "dependencies",
                    source_label: "📦 Imported By (80%)"
                })
    
    # Channel 4: Human-selected (highest priority)
    FOR file IN selected_files:
        all_results.insert(0, {
            file_path: file,
            score: 1.0,
            source: "human",
            source_label: "🧑 Human-in-the-Loop (100%)"
        })
    
    # Deduplicate and sort
    unique_results = deduplicate_by_path(all_results)
    unique_results = sort_by_score(unique_results, descending=True)
    
    # Read full content for top results
    FOR result IN unique_results[:top_k]:
        result['full_content'] = read_file(result['file_path'])[:200KB]
    
    RETURN {
        success: true,
        results: unique_results[:top_k],
        channels_used: ["embeddings", "semantic", "dependencies", "human_selected"]
    }
```

### /total_recall
```
POST /total_recall
    INPUT: {query, excluded_dirs, central_files, external_files}
    
    # Collect all .py and .md files
    all_files = glob(project_root, ['*.py', '*.md'])
    
    # Filter by excluded_dirs
    filtered_files = [f FOR f IN all_files 
                      IF NOT any(skip_dir IN f FOR skip_dir IN excluded_dirs)]
    
    # Read file contents
    file_data = []
    FOR file IN filtered_files:
        content = read_file(file)
        file_data.append({
            path: relative_path(file),
            content_for_prompt: content[:1000],
            full_content: content,
            is_central: path IN central_files
        })
    
    # Add external files
    FOR ext_file IN external_files:
        file_data.append({path: ext_file, content: escaped_content})
    
    # STRICT relevance check via vLLM
    DEFINE relevance_prompt_template = """
    You are a STRICT code relevance classifier.
    
    TASK CONTEXT: {query}
    FILE: {file_path}
    CONTENT: {content}
    
    STRICT CRITERIA - answer YES only if ALL conditions met:
    1. File DIRECTLY implements functionality mentioned in task
    2. File would be REQUIRED reading to complete task
    3. File is NOT just tangentially related or dependency
    
    When in doubt, answer NO.
    
    VERDICT: YES or VERDICT: NO (exact format)
    """
    
    ASYNC FUNCTION check_relevance(item):
        prompt = format(relevance_prompt_template, query, item.path, item.content)
        
        payload = {
            model: "qwen3-coder-30b",
            messages: [
                {role: "system", content: "Be conservative - only mark ESSENTIAL files. When in doubt, NO."},
                {role: "user", content: prompt}
            ],
            temperature: 0.0,  # Deterministic
            max_tokens: 150
        }
        
        response = await vllm_api.post(payload)
        answer = response.choices[0].message.content
        
        # STRICT check - only exact "VERDICT: YES"
        is_relevant = "VERDICT: YES" IN answer.upper()
        
        RETURN {relevant: is_relevant, item: item, answer: answer}
    
    # Parallel batch processing
    semaphore = Semaphore(64)  # Max 64 concurrent
    tasks = [check_relevance(item) FOR item IN file_data]
    results = await gather(tasks)
    
    # Filter relevant files
    relevant_files = [r.item FOR r IN results IF r.relevant]
    
    # Add central files with score 1.0
    FOR central IN central_files:
        IF central NOT IN relevant_files:
            relevant_files.insert(0, {path: central, score: 1.0})
    
    # Sort by score
    relevant_files = sort_by_score(relevant_files, descending=True)
    
    RETURN {
        success: true,
        results: relevant_files,
        total_scanned: len(file_data),
        total_relevant: len(relevant_files)
    }
```

---

## FRONTEND LOGIC

### searchScope State
```javascript
let searchScope = {
    includedDirs: [],
    excludedDirs: ['.'],  // Default: ALL unchecked
    centralFiles: [],     // User-marked important
    externalFiles: []     // Loaded from OS
};
```

### handleExternalFiles (Folder + File Support)
```javascript
ASYNC FUNCTION handleExternalFiles(event):
    files = Array.from(event.target.files)
    maxSize = 500 * 1024  // 500KB
    allowedExt = ['.md', '.txt', '.py', '.json']
    
    FOR each file IN files:
        ext = get_extension(file.name)
        IF ext NOT IN allowedExt:
            SKIP  // Silent skip for bulk operations
        
        IF file.size > maxSize:
            SKIP
        
        content = await readFileAsText(file)
        displayPath = file.webkitRelativePath OR file.name
        
        IF displayPath NOT IN searchScope.externalFiles:
            searchScope.externalFiles.push({
                path: displayPath,
                name: displayPath,
                content: content,
                size_kb: file.size / 1024,
                extension: ext
            })
    
    refreshExternalFilesList()
```

### isExcluded (Path Hierarchy Check)
```javascript
FUNCTION isExcluded(path):
    // Special case: '.' means all excluded
    IF searchScope.excludedDirs.includes('.'):
        RETURN true
    
    // Check if path or any parent is excluded
    FOR each excluded IN searchScope.excludedDirs:
        IF path === excluded OR path.startsWith(excluded + '/'):
            RETURN true
    
    RETURN false
```

### treeTotalRecall (Tree Viewer TR Button)
```javascript
ASYNC FUNCTION treeTotalRecall():
    query = editableText.value OR rawTranscription
    IF NOT query:
        alert('Enter query first')
        RETURN
    
    // Collect only non-excluded files
    includedPaths = []
    FUNCTION collectIncluded(node):
        IF NOT isExcluded(node.path):
            IF node.type === 'file':
                includedPaths.push(node.path)
            IF node.children:
                FOR child IN node.children:
                    collectIncluded(child)
    
    collectIncluded(projectTree)
    
    IF includedPaths.length === 0:
        alert('No files selected')
        RETURN
    
    // Call Total Recall with scope
    response = await fetch('/total_recall', {
        query: query,
        excluded_dirs: searchScope.excludedDirs,
        central_files: searchScope.centralFiles,
        external_files: searchScope.externalFiles,
        mode: 'tree_only'
    })
    
    // Mark found files as central
    FOR result IN response.results:
        IF result.file_path NOT IN searchScope.centralFiles:
            searchScope.centralFiles.push(result.file_path)
    
    refreshTreeUI()
    displayContext(response.results, 'total_recall')
```

### generateHypotheses (Works Without Total Recall)
```javascript
ASYNC FUNCTION generateHypotheses():
    query = currentSearchText OR editableText.value OR rawTranscription
    IF NOT query:
        alert('Enter text first')
        RETURN
    
    // Build context from available sources
    files = []
    
    // Priority 1: Total Recall results
    IF contextData AND contextData.length > 0:
        files = contextData.map(f => ({file_path: f.file_path, excerpt: f.excerpt}))
    
    // Priority 2: Tree centralFiles
    ELSE IF searchScope.centralFiles.length > 0:
        files = searchScope.centralFiles.map(f => ({file_path: f, excerpt: '[User selected]'}))
    
    // Priority 3: External files
    ELSE IF searchScope.externalFiles.length > 0:
        files = searchScope.externalFiles.map(f => ({file_path: f.name, excerpt: f.content[:200]}))
    
    // Priority 4: Can work with empty context
    
    response = await fetch('/hypotheses', {
        query: query,
        files: files
    })
    
    IF response.success:
        displayHypotheses(response.hypotheses)
```

### fetchSummaries (Auto-load After Search)
```javascript
ASYNC FUNCTION fetchSummaries(filePaths):
    response = await fetch('/api/get_summaries', {
        file_paths: filePaths
    })
    
    IF response.success:
        FOR each [path, info] IN response.summaries:
            item = querySelector(`[data-path="${path}"] .context-summary`)
            IF item:
                item.textContent = info.summary
                item.style.fontStyle = 'italic'
```

### Search Button (Active Tab Context)
```javascript
searchBtn.addEventListener('click', ASYNC () => {
    // Determine query from active tab
    activeContext = ''
    
    IF currentGeneratedTab AND generatedVariants[currentGeneratedTab]:
        query = generatedVariants[currentGeneratedTab]
        activeContext = currentGeneratedTab  // 'spec' | 'ticket' | 'prompt'
    ELSE:
        query = currentSearchText OR editableText.value OR rawTranscription
    
    IF NOT query:
        RETURN
    
    showLoading(`🔍 Integrated search ${activeContext ? '(around ' + activeContext + ')' : ''}`)
    
    response = await fetch('/api/search_integrated', {
        query: query,
        top_k: 100,
        selected_files: searchScope.centralFiles,
        active_context: activeContext
    })
    
    IF response.results:
        displayContext(response.results, 'integrated')
        
        // Auto-fetch summaries for top 10
        topPaths = response.results.slice(0, 10).map(r => r.file_path)
        IF topPaths.length > 0:
            fetchSummaries(topPaths)
})
```

---

## KEY ALGORITHMS

### Path Exclusion Logic
```
INPUT: node.path, excludedDirs
OUTPUT: boolean (is_excluded)

IF '.' IN excludedDirs:
    RETURN true  // All excluded

FOR each excluded IN excludedDirs:
    IF node.path === excluded:
        RETURN true
    IF node.path.startsWith(excluded + '/'):
        RETURN true  // Parent excluded

RETURN false
```

### Multi-Channel Result Merging
```
INPUT: results from [embeddings, semantic, dependencies, human]
OUTPUT: unique_results sorted by score

seen_paths = Set()
unique_results = []

FOR result IN sorted(all_results, key=score, reverse=True):
    IF result.file_path NOT IN seen_paths:
        seen_paths.add(result.file_path)
        unique_results.append(result)

RETURN unique_results
```

### STRICT Relevance Validation
```
INPUT: llm_answer
OUTPUT: boolean (is_relevant)

# OLD (too permissive):
is_relevant = "YES" IN answer.upper()[:50]

# NEW (strict):
is_relevant = "VERDICT: YES" IN answer.upper()

# Requires exact format, rejects:
# - "Yes, this file is relevant"
# - "I think YES"
# - "VERDICT: MAYBE"
```

---

## SECURITY

### Command Injection Prevention
```
dangerous_patterns = r'[;|&`$()]|rm\s|sudo|chmod|chown|wget|curl\s|eval|exec'

IF re.search(dangerous_patterns, query, re.IGNORECASE):
    RETURN 400 "Query contains disallowed characters"
```

**Philosophy:** LLM generates ONLY search queries, NEVER terminal commands

---

## PERFORMANCE

### Concurrency Limits
- **Total Recall:** 64 concurrent vLLM requests (semaphore)
- **Summaries:** 20 files max per batch
- **Dependencies:** 5 .py files max per search

### Caching
- **Summaries:** Generated on-demand, not cached (future: use summarize_docs cache)
- **Embeddings:** Cached by DocsDualMemory
- **Dependencies:** Cached by DependencySearcher (LRU cache)

---

<!--/TAG:voicepal_server_pseudocode-->
