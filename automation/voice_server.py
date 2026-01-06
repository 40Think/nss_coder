#!/usr/bin/env python3
"""
Voice Server - Flask Backend for Voice Recording Interface

<!--TAG:tool_voice_server-->

PURPOSE:
    Flask web server providing:
    1. Voice recording interface (HTML/JS)
    2. Audio transcription via faster-whisper (GPU) — MIGRATED 2025-12-16
       - Previously: whisper.cpp, now: faster-whisper (CTranslate2)
       - Performance: 82.7x real-time on RTX PRO 6000 Blackwell
    3. Text enhancement via local vLLM
    4. Context search from NSS-DOCS
    5. Formatting options (prompt/ticket/spec)
    
DOCUMENTATION:
    Spec: docs/specs/voice_interface_spec.md (TBD)
    Wiki: docs/wiki/09_Documentation_System.md
    
TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:voice-->

DEPENDENCIES (Quick Reference):
    Code:
        - docs.automation.voice_whisper_fast (FasterWhisperService) — MIGRATED 2025-12-16
        - docs.automation.voice_processor (VoiceProcessor)
        - docs.utils.docs_logger (DocsLogger)
    External:
        - Flask (pip install flask)
        - faster-whisper (pip install faster-whisper) — replaces whisper.cpp
        - vLLM server (localhost:8000)

RECENT CHANGES:
    2025-12-16: MIGRATED from whisper.cpp to faster-whisper (82.7x real-time)
    2025-12-12: Created voice server with premium UI

<!--/TAG:tool_voice_server-->
"""

import os  # Operating system interface
import json  # JSON serialization
import time  # Timing
import tempfile  # Temporary file handling
from pathlib import Path  # Filesystem paths
from datetime import datetime  # Timestamps
import sys  # System path manipulation

# Add docs to Python path for isolated utilities
DOCS_DIR = Path(__file__).resolve().parent.parent  # docs/ directory (actually nss_coder root)
AUTOMATION_DIR = DOCS_DIR / "automation"  # This directory
sys.path.insert(0, str(DOCS_DIR))  # Project root (nss_coder)

# Flask import with error handling
try:
    from flask import render_template, Flask, request, jsonify, send_from_directory, Response
except ImportError:
    print("Flask not installed. Install with: pip install flask")
    sys.exit(1)

# Import our voice modules
# Import our voice modules
try:
    from utils.docs_logger import DocsLogger  # Logging
except ImportError:
    # If running as script, try to adjust path or fallback
    # sys.path.insert(0, str(PROJECT_ROOT)) # Already done above but maybe not correctly?
    # Let's try direct import if we are in nss_coder
    from utils.docs_logger import DocsLogger

# ============================================================================
# MIGRATION NOTE (2025-12-16): 
# Migrated from whisper.cpp (VoiceWhisper) to faster-whisper (FasterWhisperService)
# Performance improvement: 12-28x -> 82.7x real-time on RTX PRO 6000 Blackwell
# Old import: from automation.voice_whisper import VoiceWhisper, TranscriptionResult
# ============================================================================
# ============================================================================
from automation.voice_whisper_client import (
    get_faster_whisper_service
)
from automation.voice_processor import VoiceProcessor, ProcessingResult  # Processing

# Initialize logger
logger = DocsLogger("voice_server")


# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__, static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload

# Initialize services
# MIGRATION: Using FasterWhisperService instead of VoiceWhisper for 82.7x speedup
whisper = get_faster_whisper_service()  # Singleton instance with GPU acceleration
processor = VoiceProcessor()

# Recordings directory for temporary audio files
RECORDINGS_DIR = AUTOMATION_DIR / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True)


# ============================================================================
# STATIC FILES (Embedded HTML/CSS/JS)
# ============================================================================

# Premium dark theme HTML with voice recording - V2

# INDEX_HTML moved to templates/index.html



# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check for whisper and LLM services."""
    # Check whisper
    whisper_status, whisper_info = whisper.check_health()
    
    # Check LLM
    llm_status = "OK" if processor.llm.is_available() else "ERROR"
    
    return jsonify({
        "whisper": whisper_status,
        "whisper_info": whisper_info,
        "llm": llm_status
    })


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe uploaded audio file.
    
    Expects: multipart form with 'audio' file
    Returns: JSON with transcription result
    """
    logger.info("Received transcription request")
    
    # Check if audio file is present
    if 'audio' not in request.files:
        return jsonify({"success": False, "error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    
    if audio_file.filename == '':
        return jsonify({"success": False, "error": "Empty filename"}), 400
    
    # Save to temporary file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_path = RECORDINGS_DIR / f"recording_{timestamp}.webm"
    
    try:
        audio_file.save(str(temp_path))
        logger.info(f"Saved audio to {temp_path}", {
            "size_kb": temp_path.stat().st_size / 1024
        })
        
        # Transcribe
        result = whisper.transcribe(temp_path)
        
        if result.success:
            return jsonify({
                "success": True,
                "text": result.text,
                "language": result.language,
                "duration_audio_sec": result.duration_audio_sec,
                "duration_process_sec": result.duration_process_sec
            })
        else:
            return jsonify({
                "success": False,
                "error": result.error
            }), 500
            
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        # Clean up temp file after a delay (in case needed for debugging)
        # In production, clean immediately
        pass


@app.route('/process', methods=['POST'])
def process():
    """
    Process text with enhancement, translation, and formatting.
    
    Expects: JSON with 'text', 'format', 'search_context', 'scope'
    Returns: JSON with processed variants
    """
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({"success": False, "error": "No text provided"}), 400
    
    text = data['text']
    format_type = data.get('format', 'enhanced')
    search_context = data.get('search_context', True)
    context_files = data.get('context_files', [])  # Selected files from Related Content
    scope = data.get('scope', {})  # Tree Viewer scope with source attribution
    
    # Extract scope data
    central_files = scope.get('centralFiles', [])  # Human-in-the-Loop: highest priority
    external_files = scope.get('externalFiles', [])  # External files with content
    excluded_dirs = scope.get('excludedDirs', [])
    
    logger.info(f"Processing text", {
        "length": len(text),
        "format": format_type,
        "search_context": search_context,
        "context_files_count": len(context_files),
        "central_files_count": len(central_files),
        "external_files_count": len(external_files)
    })
    
    # Build annotated context with source attribution
    annotated_context = []
    
    # 1. Central files (Human-in-the-Loop - highest priority)
    for cf in central_files:
        annotated_context.append({
            "path": cf,
            "source": "human_selected",
            "priority": "highest",
            "description": "User explicitly marked as important (Human-in-the-Loop)"
        })
    
    # 2. External files with content
    for ef in external_files:
        annotated_context.append({
            "path": ef.get('name', 'unknown'),
            "content": ef.get('content', ''),
            "source": "external",
            "priority": "high",
            "description": "External file loaded from outside project"
        })
    
    # 3. Context files from Related Content panel
    for cf in context_files:
        annotated_context.append({
            "path": cf,
            "source": "related_content",
            "priority": "medium",
            "description": "Selected from search results"
        })
    
    try:
        # Process with annotated context
        if annotated_context or context_files:
            logger.info(f"Using {len(annotated_context)} annotated context items")
            all_context_paths = [c['path'] for c in annotated_context if 'path' in c]
            result = processor.process(text, format_type=format_type, search_context=False, 
                                       pre_selected_context=all_context_paths)
            # Add external file contents to the result for prompt building
            result.annotated_context = annotated_context
        else:
            result = processor.process(text, format_type=format_type, search_context=search_context)
        
        # Convert context results to dicts
        context_list = [
            {
                "file_path": r.file_path,
                "score": r.score,
                "excerpt": r.excerpt,
                "content_type": r.content_type
            }
            for r in result.context_results
        ]
        
        return jsonify({
            "success": result.success,
            "original_ru": result.original_ru,
            "original_en": result.original_en,
            "enhanced": result.enhanced,
            "formatted": result.formatted,
            "formatted_type": result.formatted_type,
            "context": context_list,
            "processing_time_sec": result.processing_time_sec,
            "llm_calls": result.llm_calls,
            "error": result.error
        })
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# NSS-DOCS INTEGRATED SEARCH
# ============================================================================

@app.route('/api/reindex', methods=['POST'])
def reindex():
    """
    Trigger re-indexing of project documentation.
    
    Uses docs_dual_memory for embedding generation.
    Supports incremental updates (only changed files).
    """
    print("[PARANOID] /api/reindex called")
    
    try:
        from utils.docs_dual_memory import DocsDualMemory
        
        data = request.get_json() or {}
        incremental = data.get('incremental', True)
        
        logger.info(f"Re-indexing started (incremental={incremental})")
        print(f"[PARANOID] Starting re-index, incremental={incremental}")
        
        memory = DocsDualMemory()
        memory.build()  # Rebuild indexes
        
        logger.info("Re-indexing complete")
        print("[PARANOID] Re-index complete")
        
        return jsonify({
            "success": True,
            "message": "Indexes rebuilt successfully"
        })
        
    except Exception as e:
        logger.error(f"Re-index error: {e}")
        print(f"[PARANOID] Re-index error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/get_summaries', methods=['POST'])
def get_summaries():
    """
    Get cached summaries for a list of files.
    
    Uses summarize_docs.py to generate/retrieve summaries.
    Returns brief summaries for context display.
    """
    print("[PARANOID] /api/get_summaries called")
    
    data = request.get_json()
    file_paths = data.get('file_paths', [])
    
    if not file_paths:
        return jsonify({"success": False, "error": "No file paths provided"}), 400
    
    try:
        from automation.summarize_docs import DocumentSummarizer
        summarizer = DocumentSummarizer()
        
        project_root = Path(__file__).resolve().parent.parent.parent
        summaries = {}
        
        for fp in file_paths[:20]:  # Limit to 20 files
            try:
                file_path = project_root / fp
                if file_path.exists():
                    summary = summarizer.summarize(file_path, max_length=200)
                    summaries[fp] = {
                        "summary": summary.summary,
                        "compression_ratio": summary.compression_ratio
                    }
            except Exception as e:
                summaries[fp] = {"summary": f"[Error: {e}]", "compression_ratio": 0}
        
        print(f"[PARANOID] Generated {len(summaries)} summaries")
        
        return jsonify({
            "success": True,
            "summaries": summaries
        })
        
    except Exception as e:
        logger.error(f"Summary error: {e}")
        print(f"[PARANOID] Summary error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/suggest_tags', methods=['POST'])
def suggest_tags():
    """
    LLM-based tag suggestions for search.
    
    Gets available tags from project, asks LLM which are relevant for the query.
    """
    print("[PARANOID] /api/suggest_tags called")
    
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({"success": False, "error": "No query provided"}), 400
    
    try:
        # Get available tags using search_by_tag
        from automation.search_by_tag import TagSearcher, TagConfig
        project_root = Path(__file__).resolve().parent.parent.parent
        config = TagConfig(docs_root=project_root / 'docs')
        searcher = TagSearcher(config)
        
        # Get all unique tags
        available_tags = list(searcher.tag_index.keys())[:100]  # Limit to 100
        
        if not available_tags:
            return jsonify({"success": True, "suggested_tags": [], "message": "No tags indexed"})
        
        # Ask LLM which tags are relevant
        from utils.docs_llm_backend import DocsLLMBackend
        llm = DocsLLMBackend()
        
        prompt = f"""Given the user's query, suggest which semantic tags would be most relevant.

Available tags: {', '.join(available_tags[:50])}

User query: {query}

Respond with ONLY a JSON array of 3-5 most relevant tag names, e.g.: ["tag1", "tag2", "tag3"]
"""
        
        response = llm.generate(prompt, max_tokens=100)
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON array from response
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            suggested = json.loads(match.group())
        else:
            suggested = []
        
        print(f"[PARANOID] LLM suggested tags: {suggested}")
        
        return jsonify({
            "success": True,
            "suggested_tags": suggested,
            "available_tags_count": len(available_tags)
        })
        
    except Exception as e:
        logger.error(f"Tag suggestion error: {e}")
        print(f"[PARANOID] Tag error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/search_integrated', methods=['POST'])
def search_integrated():
    """
    Multi-channel search using NSS-DOCS system.
    
    Combines results from:
    1. Embeddings (dual_memory) - semantic similarity
    2. Keyword search - exact matches
    3. Dependency analysis - for .py files
    
    Returns results with source attribution.
    """
    print("[PARANOID] /api/search_integrated called")
    
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"success": False, "error": "No query provided"}), 400
    
    query = data['query']
    top_k = data.get('top_k', 50)
    selected_files = data.get('selected_files', [])  # Pre-selected files from Tree Viewer
    
    # SECURITY: Reject queries with dangerous shell patterns
    import re
    dangerous_patterns = r'[;|&`$()]|rm\s|sudo|chmod|chown|wget|curl\s|eval|exec'
    if re.search(dangerous_patterns, query, re.IGNORECASE):
        print(f"[PARANOID] SECURITY: Dangerous pattern detected in query!")
        logger.warning(f"Security: Blocked query with dangerous pattern")
        return jsonify({"success": False, "error": "Query contains disallowed characters"}), 400
    
    print(f"[PARANOID] Query: {query[:50]}..., top_k={top_k}")
    logger.info(f"Integrated search: {query[:50]}...")
    
    all_results = []
    
    try:
        # Channel 1: Embeddings search via dual_memory
        try:
            from utils.docs_dual_memory import DocsDualMemory
            memory = DocsDualMemory()
            
            # Search descriptions (documentation)
            desc_results = memory.search_descriptions(query, top_k=top_k // 2)
            for r in desc_results:
                all_results.append({
                    "file_path": r.source_file,
                    "score": r.score,
                    "excerpt": r.content[:500],
                    "content_type": r.content_type,
                    "source": "embeddings",
                    "source_label": "🔍 Embeddings (70-80%)"
                })
            print(f"[PARANOID] Embeddings: {len(desc_results)} results")
            
            # Search code
            code_results = memory.search_code(query, top_k=top_k // 2)
            for r in code_results:
                all_results.append({
                    "file_path": r.source_file,
                    "score": r.score,
                    "excerpt": r.content[:500],
                    "content_type": "code",
                    "source": "embeddings",
                    "source_label": "🔍 Embeddings (70-80%)"
                })
            print(f"[PARANOID] Code search: {len(code_results)} results")
            
        except Exception as e:
            logger.warning(f"Dual memory search failed: {e}")
            print(f"[PARANOID] Dual memory error: {e}")
        
        # Channel 2: Fallback to processor search
        try:
            processor_results = processor.search_context(query, top_k=top_k)
            for r in processor_results:
                # Avoid duplicates
                if not any(ar['file_path'] == r.file_path for ar in all_results):
                    all_results.append({
                        "file_path": r.file_path,
                        "score": r.score,
                        "excerpt": r.excerpt,
                        "content_type": r.content_type,
                        "source": "processor",
                        "source_label": "🔍 Semantic Search"
                    })
            print(f"[PARANOID] Processor search added unique results")
        except Exception as e:
            logger.warning(f"Processor search failed: {e}")
        
        # Channel 3: Dependencies analysis for .py files
        py_files = [f for f in selected_files if f.endswith('.py')]
        if py_files:
            try:
                from automation.search_dependencies import DependencySearcher
                project_root = Path(__file__).resolve().parent.parent.parent
                searcher = DependencySearcher(project_root)
                
                for py_file in py_files[:5]:  # Limit to 5 files
                    dep_info = searcher.search(py_file, include_reverse=True)
                    if dep_info:
                        # Add imported modules
                        for import_type, imports in dep_info.dependencies.items():
                            for imp in imports[:3]:  # Top 3 per type
                                if isinstance(imp, dict):
                                    imp_path = imp.get('module', str(imp))
                                else:
                                    imp_path = str(imp)
                                all_results.append({
                                    "file_path": imp_path,
                                    "score": 0.85,
                                    "excerpt": f"[Dependency of {py_file}] {import_type}",
                                    "content_type": "dependency",
                                    "source": "dependencies",
                                    "source_label": "📦 Dependencies (85%)"
                                })
                        
                        # Add reverse dependencies (who imports this)
                        if dep_info.reverse_dependencies:
                            for rev_dep in dep_info.reverse_dependencies[:3]:
                                all_results.append({
                                    "file_path": rev_dep,
                                    "score": 0.80,
                                    "excerpt": f"[Imports {py_file}]",
                                    "content_type": "reverse_dependency",
                                    "source": "dependencies",
                                    "source_label": "📦 Imported By (80%)"
                                })
                
                print(f"[PARANOID] Dependencies: processed {len(py_files)} .py files")
            except Exception as e:
                logger.warning(f"Dependency search failed: {e}")
                print(f"[PARANOID] Dependency error: {e}")
        
        # Add pre-selected files with highest priority
        for sf in selected_files:
            all_results.insert(0, {
                "file_path": sf,
                "score": 1.0,
                "excerpt": "[User selected]",
                "content_type": "user_selected",
                "source": "human",
                "source_label": "🧑 Human-in-the-Loop (100%)"
            })
        
        # Sort by score and dedupe
        seen = set()
        unique_results = []
        for r in sorted(all_results, key=lambda x: x['score'], reverse=True):
            if r['file_path'] not in seen:
                seen.add(r['file_path'])
                unique_results.append(r)
        
        # Read full content for top results
        project_root = Path(__file__).resolve().parent.parent.parent
        for r in unique_results[:top_k]:
            try:
                file_path = project_root / r['file_path']
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    r['full_content'] = content[:200000]  # 200KB limit
            except:
                pass
        
        print(f"[PARANOID] Final results: {len(unique_results)}")
        
        return jsonify({
            "success": True,
            "results": unique_results[:top_k],
            "channels_used": ["embeddings", "semantic", "dependencies", "human_selected"]
        })
        
    except Exception as e:
        logger.error(f"Integrated search error: {e}")
        print(f"[PARANOID] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/search', methods=['POST'])
def search():
    """
    Search NSS-DOCS for context.
    
    Expects: JSON with 'query'
    Returns: JSON with search results including full file content
    """
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"success": False, "error": "No query provided"}), 400
    
    query = data['query']
    top_k = data.get('top_k', 20)  # Default to 20 docs
    
    logger.info(f"Search request: {query[:50]}...")
    
    try:
        results = processor.search_context(query, top_k=top_k)
        
        # Read full file content for expand feature
        project_root = Path(__file__).resolve().parent.parent.parent
        enhanced_results = []
        
        for r in results:
            # Try to read full file content (limited to 10KB)
            full_content = ""
            try:
                file_path = project_root / r.file_path
                if file_path.exists():
                    raw_content = file_path.read_text(encoding='utf-8', errors='ignore')
                    max_content_size = 200000  # 200KB limit
                    if len(raw_content) > max_content_size:
                        full_content = raw_content[:max_content_size] + f"\n\n... [truncated, {len(raw_content)} chars total]"
                    else:
                        full_content = raw_content
            except Exception as e:
                logger.warning(f"Could not read full content for {r.file_path}: {e}")
            
            enhanced_results.append({
                "file_path": r.file_path,
                "score": r.score,
                "excerpt": r.excerpt,
                "content_type": r.content_type,
                "full_content": full_content  # Full content for expand (max 10KB)
            })
        
        return jsonify({
            "success": True,
            "results": enhanced_results
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/total_recall', methods=['POST'])
def total_recall():
    """
    Total Recall - Brute-force relevance check via vLLM parallel batching.
    
    Sends concurrent async requests to vLLM for maximum GPU utilization.
    Uses aiohttp for parallel HTTP requests - vLLM batches them automatically.
    
    Supports:
    - excluded_dirs: directories to skip (from Tree Viewer)
    - central_files: files that always appear with score 1.0
    - external_files: files from outside the project
    """
    import time
    import asyncio
    import aiohttp
    import html
    
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"success": False, "error": "No query provided"}), 400
    
    query = data['query']
    excluded_dirs = data.get('excluded_dirs', [])  # User-selected exclusions
    central_files = data.get('central_files', [])  # Files that always appear
    external_file_paths = data.get('external_files', [])  # External file paths
    
    logger.info(f"Total Recall for: {query[:50]}... | excluded={len(excluded_dirs)}, central={len(central_files)}, external={len(external_file_paths)}")
    start_time = time.time()
    
    # Collect all relevant files
    project_root = Path(__file__).resolve().parent.parent.parent  # Telegram_Parser
    
    all_files = []
    for ext in ['*.py', '*.md']:
        all_files.extend(project_root.glob(f'**/{ext}'))
    
    # Filter out unwanted directories + user-excluded dirs
    skip_dirs = ['__pycache__', '.git', 'node_modules', 'venv', '.venv', 'build', 'dist', '.eggs',
                 'output/', 'logs/', 'input/', 'backup', 'test_data', '.gemini']
    # Add user-excluded dirs
    skip_dirs.extend(excluded_dirs)
    
    filtered_files = []
    for f in all_files:
        rel_path = str(f.relative_to(project_root))
        skip = any(skip_dir in str(f) for skip_dir in skip_dirs)
        # Also check if excluded by relative path prefix
        skip = skip or any(rel_path.startswith(d) for d in excluded_dirs)
        if not skip and f.is_file():
            filtered_files.append(f)
    
    logger.info(f"Total Recall: scanning {len(filtered_files)} files (after scope filter)")
    
    # Read all files with FULL content for expand feature
    file_data = []
    for f in filtered_files:
        try:
            full_content = f.read_text(encoding='utf-8', errors='ignore')
            rel_path = str(f.relative_to(project_root))
            file_data.append({
                "file": f,
                "path": rel_path,
                "content_for_prompt": full_content[:1000],
                "full_content": full_content,
                "size_kb": len(full_content) / 1024,
                "is_central": rel_path in central_files or f.name in central_files
            })
        except Exception as e:
            logger.warning(f"Could not read {f}: {e}")
    
    # Add external files (with escaping for safety)
    for ext_path in external_file_paths:
        try:
            ext_file = Path(ext_path)
            if ext_file.exists() and ext_file.is_file():
                content = ext_file.read_text(encoding='utf-8', errors='ignore')
                escaped_content = html.escape(content)
                file_data.append({
                    "file": ext_file,
                    "path": str(ext_file),  # Absolute path for external
                    "content_for_prompt": escaped_content[:1000],
                    "full_content": escaped_content,
                    "size_kb": len(content) / 1024,
                    "is_central": False,
                    "is_external": True
                })
        except Exception as e:
            logger.warning(f"Could not read external file {ext_path}: {e}")
    
    logger.info(f"Total Recall: {len(file_data)} files total (incl. {len(external_file_paths)} external)")

    
    # vLLM endpoint config
    vllm_endpoint = "http://localhost:8000/v1/chat/completions"
    model_name = "qwen3-coder-30b-a3b-instruct_moe"
    
    relevance_prompt_template = """You are a STRICT code relevance classifier. Your job is to determine if a file is DIRECTLY relevant to the user's task.

TASK CONTEXT: {query}

FILE: {file_path}
CONTENT EXCERPT:
```
{content}
```

STRICT CRITERIA - answer YES only if ALL conditions are met:
1. File DIRECTLY implements, defines, or documents functionality mentioned in the task
2. File would be REQUIRED reading to complete the task
3. File is NOT just tangentially related or a dependency

If the file is only loosely related, a utility, or generic infrastructure - answer NO.

Think step by step:
1. What is the task asking for?
2. What does this file contain?
3. Is this file ESSENTIAL for the task?

VERDICT: YES or VERDICT: NO (use exact format)"""

    async def check_relevance(session: aiohttp.ClientSession, item: dict, semaphore: asyncio.Semaphore):
        """Check single file relevance via vLLM API."""
        async with semaphore:  # Limit concurrent requests
            prompt = relevance_prompt_template.format(
                query=query[:500],  # More context
                file_path=item["path"],
                content=item["content_for_prompt"]
            )
            
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a strict file relevance classifier. Be conservative - only mark files as relevant if they are ESSENTIAL for the task. When in doubt, answer NO."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.0,  # Deterministic for consistency
                "max_tokens": 150  # More room for reasoning
            }
            
            try:
                async with session.post(vllm_endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        result = await response.json()
                        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        # STRICT check - only exact "VERDICT: YES" counts
                        is_relevant = "VERDICT: YES" in answer.upper()
                        return {
                            "relevant": is_relevant,
                            "item": item,
                            "answer": answer[:200]
                        }
                    else:
                        logger.warning(f"vLLM returned {response.status} for {item['path']}")
                        return {"relevant": False, "item": item, "error": f"HTTP {response.status}"}
            except Exception as e:
                logger.warning(f"Request failed for {item['path']}: {e}")
                return {"relevant": False, "item": item, "error": str(e)}
    
    async def run_parallel_checks():
        """Run all relevance checks in parallel."""
        # Semaphore limits concurrent requests (vLLM handles batching internally)
        # Higher = more concurrent, but don't overwhelm
        max_concurrent = 64  # vLLM can handle many concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        connector = aiohttp.TCPConnector(limit=max_concurrent, limit_per_host=max_concurrent)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [check_relevance(session, item, semaphore) for item in file_data]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
    
    try:
        # Run async loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            check_results = loop.run_until_complete(run_parallel_checks())
        finally:
            loop.close()
        
        # Process results
        results = []
        relevant_count = 0
        error_count = 0
        added_paths = set()  # Track already-added files
        
        # First: add central files with score=1.0 (they ALWAYS appear)
        for item in file_data:
            if item.get("is_central"):
                max_content_size = 200000
                full_content = item["full_content"]
                if len(full_content) > max_content_size:
                    full_content = full_content[:max_content_size] + f"\n\n... [truncated]"
                results.append({
                    "file_path": item["path"],
                    "score": 1.0,
                    "excerpt": item["content_for_prompt"][:300],
                    "content_type": "code" if item["path"].endswith('.py') else "docs",
                    "full_content": full_content,
                    "is_central": True
                })
                added_paths.add(item["path"])
                relevant_count += 1
        
        # Then: add LLM-relevant files
        for res in check_results:
            if isinstance(res, Exception):
                error_count += 1
                continue
            
            if res.get("error"):
                error_count += 1
                continue
                
            if res.get("relevant"):
                item = res["item"]
                # Skip if already added as central
                if item["path"] in added_paths:
                    continue
                    
                relevant_count += 1
                max_content_size = 200000
                full_content = item["full_content"]
                if len(full_content) > max_content_size:
                    full_content = full_content[:max_content_size] + f"\n\n... [truncated, {len(item['full_content'])} chars total]"
                results.append({
                    "file_path": item["path"],
                    "score": 1.0,
                    "excerpt": item["content_for_prompt"][:300],
                    "content_type": "code" if item["path"].endswith('.py') else "docs",
                    "full_content": full_content
                })
                added_paths.add(item["path"])
        
        duration = time.time() - start_time
        
        logger.info(f"Total Recall: {relevant_count} relevant (incl {len([i for i in file_data if i.get('is_central')])} central), {error_count} errors in {duration:.1f}s")
        
        return jsonify({
            "success": True,
            "results": results,
            "files_scanned": len(file_data),
            "files_relevant": relevant_count,
            "files_errors": error_count,
            "duration_sec": duration
        })
        
    except Exception as e:
        logger.error(f"Total Recall error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/hypotheses', methods=['POST'])
def generate_hypotheses():
    """
    Generate 10 hypotheses based on Total Recall results.
    
    Input: query + list of relevant files with excerpts
    Output: 10 structured hypotheses about user intent
    """
    data = request.get_json()
    
    if not data or 'query' not in data or 'files' not in data:
        return jsonify({"success": False, "error": "Need query and files"}), 400
    
    query = data['query']
    files = data['files']  # List of {file_path, excerpt}
    
    logger.info(f"Generating hypotheses for: {query[:50]}... with {len(files)} files")
    
    # Build file list for prompt
    file_summaries = []
    for i, f in enumerate(files[:30]):  # Limit to 30 files for context
        excerpt = f.get('excerpt', '')[:200]  # First 200 chars
        file_summaries.append(f"{i+1}. {f['file_path']}: {excerpt}")
    
    file_list_text = "\n".join(file_summaries)
    
    hypothesis_prompt = f"""Based on the user's voice query and the relevant files found, generate exactly 10 hypotheses about what the user wants to accomplish.

USER QUERY (transcribed from voice):
"{query}"

RELEVANT FILES FOUND ({len(files)} files):
{file_list_text}

Generate 10 hypotheses. Each hypothesis should:
1. Be a specific, actionable interpretation of user intent
2. Reference relevant files by number
3. Explain HOW this connects to the codebase

Respond ONLY with valid JSON array:
[
  {{"id": 1, "title": "Short title", "description": "What user wants + how it connects to files", "file_indices": [1, 3, 7], "confidence": 0.9}},
  ...
]

Generate exactly 10 hypotheses, ordered by confidence (highest first)."""

    try:
        response = processor.llm.generate(
            system_prompt="You are an expert at understanding developer intent from voice queries and connecting them to codebase structure. Always respond with valid JSON.",
            user_prompt=hypothesis_prompt,
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse JSON from response
        import json
        
        # Try to extract JSON array from response
        json_start = response.find('[')
        json_end = response.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            hypotheses = json.loads(json_str)
        else:
            # Fallback: return raw response for debugging
            logger.warning(f"Could not parse JSON from hypothesis response")
            return jsonify({
                "success": False,
                "error": "Failed to parse hypotheses JSON",
                "raw_response": response[:500]
            }), 500
        
        logger.info(f"Generated {len(hypotheses)} hypotheses")
        
        return jsonify({
            "success": True,
            "hypotheses": hypotheses,
            "query": query,
            "files_analyzed": len(files)
        })
        
    except Exception as e:
        logger.error(f"Hypothesis generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/hypothesis_mapping', methods=['POST'])
def hypothesis_mapping():
    """
    Map files to selected hypotheses.
    
    Input: hypotheses + files
    Output: Which files belong to which hypothesis
    """
    data = request.get_json()
    
    if not data or 'hypotheses' not in data or 'files' not in data:
        return jsonify({"success": False, "error": "Need hypotheses and files"}), 400
    
    hypotheses = data['hypotheses']
    files = data['files']
    
    logger.info(f"Mapping {len(files)} files to {len(hypotheses)} hypotheses")
    
    # Build mapping from hypothesis file_indices
    mapping = {}
    for h in hypotheses:
        h_id = h.get('id', 0)
        file_indices = h.get('file_indices', [])
        # Convert 1-indexed to 0-indexed
        mapping[str(h_id)] = [i - 1 for i in file_indices if 0 < i <= len(files)]
    
    return jsonify({
        "success": True,
        "mapping": mapping,
        "hypotheses_count": len(hypotheses),
        "files_count": len(files)
    })


# ============================================================================
# TOTAL RECALL LITE - LLM Filter for Embedding Results
# ============================================================================

@app.route('/total_recall_lite', methods=['POST'])
def total_recall_lite():
    """
    Total Recall Lite - LLM binary classification for pre-filtered embedding results.
    
    Takes files from embedding search and checks each one for relevance using LLM.
    Similar to Total Recall but operates on pre-filtered 200 results instead of all files.
    """
    import time
    import asyncio
    import aiohttp
    
    data = request.get_json()
    
    if not data or 'query' not in data or 'files' not in data:
        return jsonify({"success": False, "error": "Need query and files"}), 400
    
    query = data['query']
    files = data['files']  # List of {file_path, excerpt, score}
    
    logger.info(f"Total Recall Lite: checking {len(files)} files with LLM")
    start_time = time.time()
    
    # vLLM endpoint config
    vllm_endpoint = "http://localhost:8000/v1/chat/completions"
    model_name = "qwen3-coder-30b-a3b-instruct_moe"
    
    relevance_prompt_template = """Is this file RELEVANT to the user's query?

USER QUERY: {query}

FILE PATH: {file_path}

FILE EXCERPT:
```
{excerpt}
```

Think briefly, then answer with "VERDICT: YES" or "VERDICT: NO"."""

    async def check_relevance(session: aiohttp.ClientSession, item: dict, semaphore: asyncio.Semaphore):
        """Check single file relevance via vLLM API."""
        async with semaphore:
            prompt = relevance_prompt_template.format(
                query=query[:300],
                file_path=item.get("file_path", ""),
                excerpt=item.get("excerpt", "")[:500]
            )
            
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a file relevance classifier. Answer YES or NO."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 50
            }
            
            try:
                async with session.post(vllm_endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        result = await response.json()
                        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        is_relevant = "VERDICT: YES" in answer.upper() or "YES" in answer.upper()[:50]
                        return {
                            "relevant": is_relevant,
                            "file_path": item.get("file_path"),
                            "answer": answer[:100]
                        }
                    else:
                        return {"relevant": False, "file_path": item.get("file_path"), "error": f"HTTP {response.status}"}
            except Exception as e:
                return {"relevant": False, "file_path": item.get("file_path"), "error": str(e)}
    
    async def run_parallel_checks():
        """Run all relevance checks in parallel."""
        max_concurrent = 64  # vLLM handles batching
        semaphore = asyncio.Semaphore(max_concurrent)
        connector = aiohttp.TCPConnector(limit=max_concurrent, limit_per_host=max_concurrent)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [check_relevance(session, item, semaphore) for item in files]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
    
    try:
        # Run async loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            check_results = loop.run_until_complete(run_parallel_checks())
        finally:
            loop.close()
        
        # Process results
        relevant_files = []
        error_count = 0
        
        for res in check_results:
            if isinstance(res, Exception):
                error_count += 1
                continue
            if res.get("error"):
                error_count += 1
                continue
            if res.get("relevant"):
                relevant_files.append({"file_path": res["file_path"]})
        
        duration = time.time() - start_time
        
        logger.info(f"Total Recall Lite complete: {len(relevant_files)}/{len(files)} relevant in {duration:.1f}s")
        
        return jsonify({
            "success": True,
            "results": relevant_files,
            "files_checked": len(files),
            "relevant_count": len(relevant_files),
            "errors": error_count,
            "duration_sec": duration
        })
        
    except Exception as e:
        logger.error(f"Total Recall Lite error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# TREE VIEWER API - Directory Structure & Scope Selection
# ============================================================================

@app.route('/api/project_tree', methods=['GET'])
def get_project_tree():
    """
    Returns project directory tree as JSON.
    
    Used by Tree Viewer UI for displaying project structure
    and allowing scope selection for Total Recall.
    """
    print("[PARANOID] /api/project_tree called")
    try:
        project_root = Path(__file__).resolve().parent.parent.parent  # Telegram_Parser
        print(f"[PARANOID] Project root: {project_root}")
        
        # Same skip_dirs as Total Recall for consistency
        skip_dirs = {
            '__pycache__', '.git', 'node_modules', 'venv', '.venv', 
            'build', 'dist', '.eggs', 'output', 'logs', 'input', 
            'backup', 'test_data', '.gemini'
        }
        
        # Allowed file extensions for display
        allowed_extensions = {'.py', '.md', '.txt', '.json'}
        max_depth = 5  # Limit tree depth
        
        def build_tree(path: Path, depth: int = 0) -> dict:
            """Recursively build tree structure."""
            if depth > max_depth:
                return None
                
            node = {
                "name": path.name or str(path),
                "path": str(path.relative_to(project_root)) if path != project_root else ".",
                "type": "dir" if path.is_dir() else "file"
            }
            
            if path.is_dir():
                children = []
                try:
                    for child in sorted(path.iterdir()):
                        # Skip hidden and excluded dirs
                        if child.name.startswith('.') and child.name != '.':
                            continue
                        if child.name in skip_dirs:
                            continue
                        # Only include allowed file types
                        if child.is_file() and child.suffix not in allowed_extensions:
                            continue
                        
                        child_node = build_tree(child, depth + 1)
                        if child_node:
                            children.append(child_node)
                except PermissionError:
                    pass
                    
                node["children"] = children
                node["file_count"] = sum(
                    1 for c in children if c["type"] == "file"
                ) + sum(
                    c.get("file_count", 0) for c in children if c["type"] == "dir"
                )
            
            return node
        
        tree = build_tree(project_root)
        
        logger.info(f"Project tree built: {tree.get('file_count', 0)} files")
        
        return jsonify({
            "success": True,
            "tree": tree,
            "project_root": str(project_root)
        })
        
    except Exception as e:
        logger.error(f"Project tree error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/external_files', methods=['POST'])
def add_external_files():
    """
    Load external files from anywhere in the OS.
    
    Validates file extensions and escapes content for safety.
    Allows: .md, .txt, .py, .json
    Max file size: 200KB
    """
    import html
    
    print("[PARANOID] /api/external_files called")
    
    data = request.get_json()
    print(f"[PARANOID] Received data: {data}")
    
    if not data or 'paths' not in data:
        print("[PARANOID] ERROR: No paths in request")
        return jsonify({"success": False, "error": "No paths provided"}), 400
    
    paths = data['paths']  # List of absolute file paths
    print(f"[PARANOID] Paths to process: {paths}")
    
    allowed_extensions = {'.md', '.txt', '.py', '.json'}
    max_file_size = 200 * 1024  # 200KB
    
    results = []
    errors = []
    
    for path_str in paths:
        print(f"[PARANOID] Processing path: {path_str}")
        try:
            path = Path(path_str).resolve()
            print(f"[PARANOID] Resolved path: {path}")
            
            # Validate extension
            print(f"[PARANOID] Extension: {path.suffix.lower()}")
            if path.suffix.lower() not in allowed_extensions:
                print(f"[PARANOID] ERROR: Invalid extension")
                errors.append({
                    "path": path_str,
                    "error": f"Invalid extension. Allowed: {', '.join(allowed_extensions)}"
                })
                continue
            
            # Check if file exists
            print(f"[PARANOID] Exists: {path.exists()}")
            if not path.exists():
                print(f"[PARANOID] ERROR: File not found")
                errors.append({"path": path_str, "error": "File not found"})
                continue
            
            # Check if it's a file (not directory)
            print(f"[PARANOID] Is file: {path.is_file()}")
            if not path.is_file():
                print(f"[PARANOID] ERROR: Not a file")
                errors.append({"path": path_str, "error": "Not a file"})
                continue
            
            # Check file size
            file_size = path.stat().st_size
            print(f"[PARANOID] File size: {file_size} bytes")
            if file_size > max_file_size:
                print(f"[PARANOID] ERROR: File too large")
                errors.append({
                    "path": path_str,
                    "error": f"File too large ({file_size // 1024}KB > 200KB)"
                })
                continue
            
            # Read and escape content
            print(f"[PARANOID] Reading file...")
            content = path.read_text(encoding='utf-8', errors='ignore')
            print(f"[PARANOID] Read {len(content)} chars")
            escaped_content = html.escape(content)
            print(f"[PARANOID] Escaped content length: {len(escaped_content)}")
            
            results.append({
                "path": str(path),
                "name": path.name,
                "content": escaped_content,
                "size_kb": round(file_size / 1024, 1),
                "extension": path.suffix
            })
            print(f"[PARANOID] SUCCESS: Added {path.name}")
            
        except Exception as e:
            print(f"[PARANOID] EXCEPTION: {e}")
            errors.append({"path": path_str, "error": str(e)})
    
    print(f"[PARANOID] Final: {len(results)} loaded, {len(errors)} errors")
    logger.info(f"External files: {len(results)} loaded, {len(errors)} errors")
    
    return jsonify({
        "success": True,
        "files": results,
        "errors": errors,
        "loaded_count": len(results),
        "error_count": len(errors)
    })


@app.route('/api/smart_preselect', methods=['POST'])
def smart_preselect():
    """
    LLM-based intelligent pre-selection of directories/files.
    
    Analyzes query + project tree to suggest relevant directories and files.
    Only works for PROJECT files, not external files.
    """
    print("[PARANOID] /api/smart_preselect called")
    
    data = request.get_json()
    print(f"[PARANOID] Received data keys: {data.keys() if data else None}")
    
    if not data or 'query' not in data:
        print("[PARANOID] ERROR: No query in request")
        return jsonify({"success": False, "error": "No query provided"}), 400
    
    query = data['query']
    print(f"[PARANOID] Query: {query[:100]}...")
    
    tree = data.get('tree', {})  # Optional: pre-fetched tree
    
    # Build tree if not provided
    print(f"[PARANOID] Tree provided: {bool(tree)}")
    if not tree:
        project_root = Path(__file__).resolve().parent.parent.parent
        print(f"[PARANOID] Building tree from: {project_root}")
        
        # Build simplified tree for LLM
        tree_lines = []
        for ext in ['*.py', '*.md']:
            for f in project_root.glob(f'**/{ext}'):
                rel_path = str(f.relative_to(project_root))
                # Skip excluded directories
                if any(skip in rel_path for skip in ['__pycache__', '.git', 'output', 'logs', 'input']):
                    continue
                tree_lines.append(rel_path)
        
        print(f"[PARANOID] Found {len(tree_lines)} files for tree")
        tree_text = "\n".join(sorted(tree_lines)[:200])  # Limit to 200 files
    else:
        # Use provided tree structure
        def flatten_tree(node, prefix=""):
            lines = []
            if node["type"] == "file":
                lines.append(node["path"])
            elif node["type"] == "dir":
                for child in node.get("children", []):
                    lines.extend(flatten_tree(child))
            return lines
        
        tree_text = "\n".join(flatten_tree(tree)[:200])
    
    # LLM prompt for smart pre-selection
    preselect_prompt = f"""Analyze the user's query and the project file structure.
Suggest which directories and files are most likely relevant.

USER QUERY: {query[:500]}

PROJECT FILES:
{tree_text}

Based on the query, suggest:
1. Directories to include in search (by prefix)
2. Specific files that are likely central to the task

Respond with JSON:
{{
    "suggested_dirs": ["docs/automation/", "processing/"],
    "suggested_files": ["voice_server.py", "voice_processor.py"],
    "reasoning": "Brief explanation"
}}"""

    try:
        response = processor.llm.generate(
            system_prompt="You are an expert at understanding code structure. Return valid JSON only.",
            user_prompt=preselect_prompt,
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse JSON from response
        import json
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            result = json.loads(response[json_start:json_end])
        else:
            result = {
                "suggested_dirs": [],
                "suggested_files": [],
                "reasoning": "Could not parse LLM response"
            }
        
        logger.info(f"Smart preselect: {len(result.get('suggested_dirs', []))} dirs, {len(result.get('suggested_files', []))} files")
        
        return jsonify({
            "success": True,
            "suggestions": result
        })
        
    except Exception as e:
        logger.error(f"Smart preselect error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the Flask server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VoicePal - Voice to AI Interface")
    parser.add_argument('--port', '-p', type=int, default=5000, help='Port to run on')
    parser.add_argument('--host', '-H', type=str, default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🎙️  VoicePal - Voice to AI Interface                        ║
╠══════════════════════════════════════════════════════════════╣
║  URL: http://{args.host}:{args.port}                              ║
║  Whisper: ~/whisper.cpp (GPU accelerated)                    ║
║  vLLM: localhost:8000                                        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Log startup
    logger.info("Starting VoicePal server", {
        "host": args.host,
        "port": args.port,
        "debug": args.debug
    })
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
