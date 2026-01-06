#!/usr/bin/env python3
"""
Voice Processor - Text Enhancement and Context Search Pipeline

<!--TAG:tool_voice_processor-->

PURPOSE:
    Processes transcribed voice messages with AI enhancement, translation,
    context search from NSS-DOCS, and formatting (prompt/ticket/spec).
    
DOCUMENTATION:
    Spec: docs/specs/voice_interface_spec.md (TBD)
    Wiki: docs/wiki/09_Documentation_System.md
    
TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:voice-->

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger (DocsLogger for logging)
        - docs.utils.docs_llm_backend (DocsLLMBackend for AI)
        - docs.utils.docs_dual_memory (DocsDualMemory for search)
        - docs.automation.semantic_search (UnifiedSearcher)
    External:
        - vLLM server on localhost:8000

RECENT CHANGES:
    2025-12-12: Created voice processing pipeline

<!--/TAG:tool_voice_processor-->
"""

import json  # JSON serialization for structured output
import time  # Timing for performance measurement
from pathlib import Path  # Object-oriented filesystem paths
from typing import Optional, List, Dict, Any, Tuple  # Type hints
from dataclasses import dataclass, field  # Structured data classes
from datetime import datetime  # Timestamp generation
import sys  # System path manipulation
import re  # Regular expressions for text processing

# Add docs to Python path for isolated utilities
DOCS_DIR = Path(__file__).resolve().parent.parent  # Navigate to docs/ directory
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))  # Add project root for imports

# Import docs utilities
from utils.docs_logger import DocsLogger  # Paranoid logging
from utils.docs_llm_backend import DocsLLMBackend  # LLM calls

# Initialize logger
logger = DocsLogger("voice_processor")


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class SearchResultItem:
    """Single search result from NSS-DOCS."""
    file_path: str  # Relative path to found file
    score: float  # Relevance score (0.0-1.0)
    excerpt: str  # Matching content excerpt
    line_range: Tuple[int, int] = (0, 0)  # Line range in file
    content_type: str = "unknown"  # 'code', 'doc', 'spec'


@dataclass
class ProcessingResult:
    """
    Complete result of voice processing pipeline.
    
    Contains original text in 3 variants plus optional formatted output.
    """
    # Original transcription (Russian, with ASR errors)
    original_ru: str = ""
    
    # English translation (without corrections)
    original_en: str = ""
    
    # AI-enhanced version (corrected + expanded ~20%)
    enhanced: str = ""
    
    # Formatted version (prompt/ticket/spec)
    formatted: str = ""
    formatted_type: str = ""  # 'prompt', 'ticket', 'spec', 'as_is'
    
    # Context from NSS-DOCS search
    context_results: List[SearchResultItem] = field(default_factory=list)
    context_summary: str = ""
    
    # Metadata
    processing_time_sec: float = 0.0
    llm_calls: int = 0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Check if processing was successful."""
        return self.error is None and len(self.original_ru) > 0


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

# Prompt for correcting ASR errors and expanding text
ENHANCE_PROMPT_RU = """Исправь ошибки распознавания речи в следующем тексте.
Расширь текст примерно на 20%, добавляя конкретизацию и детали.
Сохрани оригинальный смысл и стиль. НЕ добавляй ничего, чего не было в оригинале.
Отвечай ТОЛЬКО исправленным текстом, без пояснений.

Текст:
{text}"""

# Prompt for translation to English
TRANSLATE_PROMPT = """Translate the following Russian text to English.
Keep technical terms and code references unchanged.
Respond ONLY with the translated text.

Text:
{text}"""

# Prompt for formatting as AI prompt
FORMAT_PROMPT_TEMPLATE = """Преобразуй следующий текст в структурированный промпт для AI-ассистента.
Учти контекст из проекта, обращая внимание на источники информации.

## Контекст из проекта (с источниками)
{context}

## Пояснение по источникам:
- 🧑 Human-in-the-Loop (человек выбрал) = 100% надёжность, наивысший приоритет
- ⭐ Smart Select (LLM предложил) = 95% надёжность
- 🧠 Total Recall = 95% надёжность (LLM проверил все файлы)
- 🔍 Embeddings = 70-80% надёжность (векторный поиск)
- 📁 External (внешний файл) = пользователь добавил вручную

## Исходный текст
{text}

Формат вывода:
## Цель
[цель задачи из текста]

## Контекст
[релевантные файлы и документация из контекста выше, указать источник]

## Требования
[конкретные требования из текста]

## Ограничения
[ограничения если есть]"""

# Prompt for formatting as ticket
FORMAT_TICKET_TEMPLATE = """Преобразуй следующий текст в формат тикета/задачи.
Учти контекст из проекта с указанием источников информации.

## Контекст из проекта (с источниками)
{context}

## Пояснение по источникам:
- 🧑 Human-in-the-Loop = высший приоритет (человек выбрал вручную)
- ⭐ Smart Select / 🧠 Total Recall = 95% надёжность
- 🔍 Embeddings = 70-80% надёжность

## Исходный текст
{text}

Формат вывода:
## [TICKET-{id}] [краткий заголовок]

**Приоритет**: Medium/High/Low
**Тип**: Task/Bug/Feature/Documentation

### Описание
[детальное описание]

### Связанные файлы (с источниками)
[файлы из контекста с указанием источника]

### Acceptance Criteria
- [ ] Критерий 1
- [ ] Критерий 2"""

# Prompt for formatting as specification
FORMAT_SPEC_TEMPLATE = """Преобразуй следующий текст в формат спецификации.
Используй контекст из проекта с учётом источников информации.

## Контекст из проекта (с источниками)
{context}

## Пояснение по источникам:
- 🧑 Human-in-the-Loop = 100% надёжность (пользователь выбрал)
- ⭐ Smart Select / 🧠 Total Recall = 95% надёжность
- 🔍 Embeddings = 70-80% надёжность

## Исходный текст
{text}

Формат вывода:
---
title: [заголовок]
date: {date}
status: Draft
---

# [заголовок]

## Overview
[обзор из текста]

## Requirements
[требования]

## Technical Details
[технические детали]

## References (с источниками)
[ссылки на файлы из контекста с указанием источника]"""


# ============================================================================
# VOICE PROCESSOR CLASS
# ============================================================================

class VoiceProcessor:
    """
    Processes transcribed voice messages with AI enhancement.
    
    Features:
    - ASR error correction via local LLM
    - ~20% text expansion with details
    - Translation to English
    - Context search from NSS-DOCS
    - Formatting options (prompt/ticket/spec)
    """
    
    def __init__(self, vllm_endpoint: str = None):
        """
        Initialize voice processor.
        
        Args:
            vllm_endpoint: Optional vLLM endpoint override
        """
        # Initialize LLM backend for text enhancement
        if vllm_endpoint:
            self.llm = DocsLLMBackend(endpoint=vllm_endpoint)
        else:
            self.llm = DocsLLMBackend()  # Use default from config
        
        # Initialize search components (lazy loading)
        self._searcher = None
        self._dual_memory = None
        
        logger.info("VoiceProcessor initialized", {
            "llm_endpoint": self.llm.endpoint
        })
    
    def _get_searcher(self):
        """Lazy-load UnifiedSearcher for context search."""
        if self._searcher is None:
            try:
                from automation.semantic_search import UnifiedSearcher
                self._searcher = UnifiedSearcher()
                logger.info("UnifiedSearcher loaded")
            except ImportError as e:
                logger.warning(f"Could not load UnifiedSearcher: {e}")
        return self._searcher
    
    def _get_dual_memory(self):
        """Lazy-load DocsDualMemory for embeddings search."""
        if self._dual_memory is None:
            try:
                from utils.docs_dual_memory import DocsDualMemory
                self._dual_memory = DocsDualMemory()
                logger.info("DocsDualMemory loaded")
            except ImportError as e:
                logger.warning(f"Could not load DocsDualMemory: {e}")
        return self._dual_memory
    
    # ========================================================================
    # CORE PROCESSING METHODS
    # ========================================================================
    
    def enhance_text(self, text: str) -> str:
        """
        Correct ASR errors and expand text by ~20%.
        
        Args:
            text: Raw transcribed text with potential errors
            
        Returns:
            Corrected and expanded text
        """
        logger.info(f"Enhancing text ({len(text)} chars)")
        
        # Skip if text is too short
        if len(text.strip()) < 10:
            return text
        
        # Build enhancement prompt
        prompt = ENHANCE_PROMPT_RU.format(text=text)
        
        # Call LLM for enhancement
        result = self.llm.generate(
            system_prompt="Ты помощник по исправлению текста. Отвечай только исправленным текстом.",
            user_prompt=prompt,
            temperature=0.3,  # Low temperature for consistency
            max_tokens=len(text) * 3  # Allow for expansion
        )
        
        if result:
            logger.info(f"Text enhanced: {len(text)} -> {len(result)} chars")
            return result
        else:
            logger.warning("Enhancement failed, returning original")
            return text
    
    def translate_to_english(self, text: str) -> str:
        """
        Translate Russian text to English.
        
        Args:
            text: Russian text to translate
            
        Returns:
            English translation
        """
        logger.info(f"Translating to English ({len(text)} chars)")
        
        # Build translation prompt
        prompt = TRANSLATE_PROMPT.format(text=text)
        
        # Call LLM for translation
        result = self.llm.generate(
            system_prompt="You are a translator. Respond only with the translation.",
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=len(text) * 2  # English may be longer
        )
        
        if result:
            logger.info(f"Translation complete: {len(result)} chars")
            return result
        else:
            logger.warning("Translation failed, returning original")
            return text
    
    def search_context(self, text: str, top_k: int = 5) -> List[SearchResultItem]:
        """
        Search NSS-DOCS for relevant context.
        
        Args:
            text: Text to find context for
            top_k: Maximum number of results
            
        Returns:
            List of SearchResultItem with relevant content
        """
        logger.info(f"Searching context for: {text[:50]}...")
        
        results = []
        
        # Try UnifiedSearcher first
        searcher = self._get_searcher()
        if searcher:
            try:
                search_results = searcher.search(text, mode='auto', top_k=top_k)
                for r in search_results:
                    results.append(SearchResultItem(
                        file_path=r.file_path,
                        score=r.score,
                        excerpt=r.excerpt[:200],
                        line_range=r.line_range if hasattr(r, 'line_range') else (0, 0),
                        content_type=r.content_type if hasattr(r, 'content_type') else 'unknown'
                    ))
                logger.info(f"Found {len(results)} context results via UnifiedSearcher")
                return results
            except Exception as e:
                logger.warning(f"UnifiedSearcher failed: {e}")
        
        # Fallback to DocsDualMemory
        dual_memory = self._get_dual_memory()
        if dual_memory:
            try:
                search_results = dual_memory.unified_search(text, top_k=top_k)
                for r in search_results:
                    results.append(SearchResultItem(
                        file_path=r.source_file if hasattr(r, 'source_file') else '',
                        score=r.score if hasattr(r, 'score') else 0.0,
                        excerpt=r.content[:200] if hasattr(r, 'content') else '',
                        line_range=r.line_range if hasattr(r, 'line_range') else (0, 0),
                        content_type=r.content_type if hasattr(r, 'content_type') else 'unknown'
                    ))
                logger.info(f"Found {len(results)} context results via DualMemory")
            except Exception as e:
                logger.warning(f"DualMemory search failed: {e}")
        
        return results
    
    def _format_context_for_prompt(self, results: List[SearchResultItem]) -> str:
        """Format search results as context string for prompts."""
        if not results:
            return "(контекст не найден)"
        
        lines = []
        for i, r in enumerate(results[:5], 1):
            lines.append(f"{i}. **{r.file_path}** (score: {r.score:.2f})")
            lines.append(f"   {r.excerpt[:150]}...")
            lines.append("")
        
        return "\n".join(lines)
    
    # ========================================================================
    # FORMAT METHODS
    # ========================================================================
    
    def format_as_prompt(self, text: str, context: List[SearchResultItem] = None) -> str:
        """Format text as AI prompt with context."""
        context_str = self._format_context_for_prompt(context or [])
        
        prompt = FORMAT_PROMPT_TEMPLATE.format(
            context=context_str,
            text=text
        )
        
        result = self.llm.generate(
            system_prompt="Форматируй текст в структурированный промпт.",
            user_prompt=prompt,
            temperature=0.4,
            max_tokens=2000
        )
        
        return result or text
    
    def format_as_ticket(self, text: str, context: List[SearchResultItem] = None) -> str:
        """Format text as ticket/task."""
        context_str = self._format_context_for_prompt(context or [])
        ticket_id = datetime.now().strftime("%Y%m%d%H%M")
        
        prompt = FORMAT_TICKET_TEMPLATE.format(
            context=context_str,
            text=text,
            id=ticket_id
        )
        
        result = self.llm.generate(
            system_prompt="Форматируй текст как тикет/задачу.",
            user_prompt=prompt,
            temperature=0.4,
            max_tokens=2000
        )
        
        return result or text
    
    def format_as_spec(self, text: str, context: List[SearchResultItem] = None) -> str:
        """Format text as specification."""
        context_str = self._format_context_for_prompt(context or [])
        
        prompt = FORMAT_SPEC_TEMPLATE.format(
            context=context_str,
            text=text,
            date=datetime.now().strftime("%Y-%m-%d")
        )
        
        result = self.llm.generate(
            system_prompt="Форматируй текст как спецификацию.",
            user_prompt=prompt,
            temperature=0.4,
            max_tokens=3000
        )
        
        return result or text
    
    # ========================================================================
    # MAIN PROCESSING PIPELINE
    # ========================================================================
    
    def process(
        self, 
        text: str, 
        format_type: str = "enhanced",
        search_context: bool = True,
        pre_selected_context: List[str] = None
    ) -> ProcessingResult:
        """
        Full processing pipeline for voice message.
        
        Args:
            text: Raw transcribed text (Russian)
            format_type: One of 'as_is', 'enhanced', 'prompt', 'ticket', 'spec'
            search_context: Whether to search for relevant context
            pre_selected_context: List of file paths to use instead of auto-search
            
        Returns:
            ProcessingResult with all variants and metadata
        """
        start_time = time.time()
        llm_calls = 0
        
        logger.info(f"Processing voice message", {
            "text_length": len(text),
            "format_type": format_type,
            "search_context": search_context,
            "pre_selected_count": len(pre_selected_context) if pre_selected_context else 0
        })
        
        result = ProcessingResult()
        result.original_ru = text  # Store original
        
        try:
            # Step 1: Use pre-selected context OR search for new context
            if pre_selected_context:
                # Use user-selected files (from Total Recall)
                logger.info(f"Using {len(pre_selected_context)} pre-selected context files")
                for file_path in pre_selected_context:
                    result.context_results.append(SearchResultItem(
                        file_path=file_path,
                        score=1.0,  # User-selected = highest relevance
                        excerpt=f"[User-selected file]",
                        content_type="selected"
                    ))
                result.context_summary = self._format_context_for_prompt(result.context_results)
            elif search_context:
                result.context_results = self.search_context(text, top_k=5)
                result.context_summary = self._format_context_for_prompt(result.context_results)
            
            # Step 2: Enhance text (correct ASR errors + expand)
            result.enhanced = self.enhance_text(text)
            llm_calls += 1
            
            # Step 3: Translate to English
            result.original_en = self.translate_to_english(text)
            llm_calls += 1
            
            # Step 4: Format based on type
            if format_type == "as_is":
                result.formatted = result.enhanced
                result.formatted_type = "as_is"
            elif format_type == "enhanced":
                result.formatted = result.enhanced
                result.formatted_type = "enhanced"
            elif format_type == "prompt":
                result.formatted = self.format_as_prompt(result.enhanced, result.context_results)
                result.formatted_type = "prompt"
                llm_calls += 1
            elif format_type == "ticket":
                result.formatted = self.format_as_ticket(result.enhanced, result.context_results)
                result.formatted_type = "ticket"
                llm_calls += 1
            elif format_type == "spec":
                result.formatted = self.format_as_spec(result.enhanced, result.context_results)
                result.formatted_type = "spec"
                llm_calls += 1
            else:
                result.formatted = result.enhanced
                result.formatted_type = format_type
            
            # Metadata
            result.processing_time_sec = time.time() - start_time
            result.llm_calls = llm_calls
            
            logger.info(f"Processing complete", {
                "processing_time_sec": round(result.processing_time_sec, 2),
                "llm_calls": llm_calls,
                "context_results": len(result.context_results)
            })
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            result.error = str(e)
        
        return result


# ============================================================================
# SINGLETON AND CONVENIENCE
# ============================================================================

# Default processor instance
_processor: Optional[VoiceProcessor] = None


def get_processor() -> VoiceProcessor:
    """Get default VoiceProcessor instance."""
    global _processor
    if _processor is None:
        _processor = VoiceProcessor()
    return _processor


def process_voice(text: str, format_type: str = "enhanced") -> ProcessingResult:
    """Convenience function for voice processing."""
    return get_processor().process(text, format_type=format_type)


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Voice Processor - AI-powered text enhancement"
    )
    parser.add_argument(
        "text",
        type=str,
        nargs="?",
        help="Text to process"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["as_is", "enhanced", "prompt", "ticket", "spec"],
        default="enhanced",
        help="Output format (default: enhanced)"
    )
    parser.add_argument(
        "--no-context",
        action="store_true",
        help="Skip context search"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    
    args = parser.parse_args()
    
    if not args.text:
        # Interactive mode - read from stdin
        print("Enter text (Ctrl+D to finish):")
        args.text = sys.stdin.read()
    
    # Process
    processor = VoiceProcessor()
    result = processor.process(
        args.text, 
        format_type=args.format,
        search_context=not args.no_context
    )
    
    if args.json:
        # JSON output
        output = {
            "success": result.success,
            "original_ru": result.original_ru,
            "original_en": result.original_en,
            "enhanced": result.enhanced,
            "formatted": result.formatted,
            "formatted_type": result.formatted_type,
            "context_count": len(result.context_results),
            "processing_time_sec": result.processing_time_sec,
            "llm_calls": result.llm_calls,
            "error": result.error
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # Human-readable output
        print(f"\n{'='*60}")
        print("ORIGINAL (RU)")
        print(f"{'='*60}")
        print(result.original_ru)
        
        print(f"\n{'='*60}")
        print("ENGLISH")
        print(f"{'='*60}")
        print(result.original_en)
        
        print(f"\n{'='*60}")
        print(f"FORMATTED ({result.formatted_type.upper()})")
        print(f"{'='*60}")
        print(result.formatted)
        
        if result.context_results:
            print(f"\n{'='*60}")
            print(f"CONTEXT ({len(result.context_results)} results)")
            print(f"{'='*60}")
            for r in result.context_results:
                print(f"  • {r.file_path} (score: {r.score:.2f})")
        
        print(f"\n[Stats: {result.processing_time_sec:.2f}s, {result.llm_calls} LLM calls]")
