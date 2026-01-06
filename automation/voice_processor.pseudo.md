# voice_processor.py - Pseudocode

<!--TAG:voicepal_processor_pseudocode-->

## PURPOSE
Text enhancement and context search pipeline for voice messages.
Corrects ASR errors, expands text, translates, and finds relevant context.

## DEPENDENCIES
- docs.utils.docs_logger (DocsLogger)
- docs.utils.docs_llm_backend (DocsLLMBackend)
- docs.utils.docs_dual_memory (DocsDualMemory)
- docs.automation.unified_searcher (UnifiedSearcher)

---

## DATA STRUCTURES

### SearchResultItem
```
DATACLASS SearchResultItem:
    file_path: str
    score: float
    excerpt: str
    line_range: Tuple[int, int] = (0, 0)
    content_type: str = "unknown"
```

### ProcessingResult
```
DATACLASS ProcessingResult:
    # Original text variants
    original_ru: str = ""
    original_en: str = ""
    enhanced: str = ""
    
    # Formatted outputs
    formatted: str = ""
    format_type: str = "as_is"
    
    # Context and metadata
    context_results: List[SearchResultItem] = []
    annotated_context: List[Dict] = []  # With source attribution
    context_summary: str = ""
    processing_time_sec: float = 0.0
    llm_calls: int = 0
    error: Optional[str] = None
    
    PROPERTY success:
        RETURN self.error IS None
```

---

## PROMPT TEMPLATES

### ENHANCE_PROMPT_RU
```
Исправь ошибки распознавания речи в следующем тексте.
Расширь текст примерно на 20%, добавляя конкретизацию и детали.
Сохрани оригинальный смысл и стиль. НЕ добавляй ничего, чего не было в оригинале.
Отвечай ТОЛЬКО исправленным текстом, без пояснений.

Текст:
{text}
```

### TRANSLATE_PROMPT
```
Translate the following Russian text to English.
Keep technical terms and code references unchanged.
Respond ONLY with the translated text.

Text:
{text}
```

### FORMAT_PROMPT_TEMPLATE (AI Prompt)
```
Преобразуй следующий текст в структурированный промпт для AI-ассистента.
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
[ограничения если есть]
```

### FORMAT_TICKET_TEMPLATE
```
Преобразуй следующий текст в формат тикета/задачи.
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
- [ ] Критерий 2
```

### FORMAT_SPEC_TEMPLATE
```
Преобразуй следующий текст в формат спецификации.
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
title: [название спецификации]
version: 1.0
date: {date}
---

# [Название спецификации]

## Обзор
[краткое описание]

## Требования
### Функциональные
[список требований]

### Нефункциональные
[производительность, безопасность и т.д.]

## Архитектура
[описание архитектуры с учётом контекста]

## Связанные файлы (с источниками)
[файлы из контекста]
```

---

## MAIN CLASS: VoiceProcessor

### Initialization
```
CLASS VoiceProcessor:
    CONSTRUCTOR(vllm_endpoint: str = None):
        self.llm_backend = DocsLLMBackend(vllm_endpoint)
        self._searcher = None  # Lazy-loaded
        self._dual_memory = None  # Lazy-loaded
        self.logger = DocsLogger("voice_processor")
```

### Lazy Loading
```
METHOD _get_searcher():
    IF self._searcher IS None:
        from docs.automation.unified_searcher import UnifiedSearcher
        self._searcher = UnifiedSearcher()
    RETURN self._searcher

METHOD _get_dual_memory():
    IF self._dual_memory IS None:
        from docs.utils.docs_dual_memory import DocsDualMemory
        self._dual_memory = DocsDualMemory()
    RETURN self._dual_memory
```

---

## CORE METHODS

### enhance_text (ASR Correction + Expansion)
```
METHOD enhance_text(text: str) -> str:
    """
    Correct ASR errors and expand text by ~20%.
    
    INPUT: Raw transcribed text with potential errors
    OUTPUT: Corrected and expanded text
    """
    
    prompt = ENHANCE_PROMPT_RU.format(text=text)
    
    enhanced = self.llm_backend.generate(
        prompt=prompt,
        temperature=0.3,  # Some creativity for expansion
        max_tokens=2000
    )
    
    self.logger.info(f"Enhanced: {len(text)} → {len(enhanced)} chars")
    
    RETURN enhanced.strip()
```

### translate_to_english
```
METHOD translate_to_english(text: str) -> str:
    """
    Translate Russian text to English.
    
    INPUT: Russian text
    OUTPUT: English translation
    """
    
    prompt = TRANSLATE_PROMPT.format(text=text)
    
    translation = self.llm_backend.generate(
        prompt=prompt,
        temperature=0.1,  # Low temp for accuracy
        max_tokens=2000
    )
    
    self.logger.info(f"Translated: {len(text)} chars")
    
    RETURN translation.strip()
```

### search_context
```
METHOD search_context(text: str, top_k: int = 5) -> List[SearchResultItem]:
    """
    Search NSS-DOCS for relevant context.
    
    Uses dual_memory (embeddings) as primary source.
    
    INPUT: Text to find context for
    OUTPUT: List of SearchResultItem with relevant content
    """
    
    results = []
    
    TRY:
        # Primary: Embeddings search
        dual_memory = self._get_dual_memory()
        
        # Search descriptions (documentation)
        desc_results = dual_memory.search_descriptions(text, top_k=top_k)
        FOR result IN desc_results:
            results.append(SearchResultItem(
                file_path=result.source_file,
                score=result.score,
                excerpt=result.content[:500],
                content_type=result.content_type,
                line_range=(result.line_range[0], result.line_range[1])
            ))
        
        # Search code
        code_results = dual_memory.search_code(text, top_k=top_k)
        FOR result IN code_results:
            results.append(SearchResultItem(
                file_path=result.source_file,
                score=result.score,
                excerpt=result.content[:500],
                content_type="code"
            ))
    
    EXCEPT Exception as e:
        self.logger.warning(f"Dual memory search failed: {e}")
        
        # Fallback: UnifiedSearcher
        TRY:
            searcher = self._get_searcher()
            fallback_results = searcher.search(text, top_k=top_k)
            FOR result IN fallback_results:
                results.append(SearchResultItem(
                    file_path=result['file'],
                    score=result.get('score', 0.5),
                    excerpt=result.get('excerpt', ''),
                    content_type=result.get('type', 'unknown')
                ))
        EXCEPT Exception as e2:
            self.logger.error(f"Fallback search failed: {e2}")
    
    # Deduplicate and sort by score
    seen = set()
    unique_results = []
    FOR result IN sorted(results, key=lambda x: x.score, reverse=True):
        IF result.file_path NOT IN seen:
            seen.add(result.file_path)
            unique_results.append(result)
    
    RETURN unique_results[:top_k]
```

### _format_context_for_prompt
```
METHOD _format_context_for_prompt(results: List[SearchResultItem]) -> str:
    """
    Format search results as context string for prompts.
    
    Includes source attribution based on content_type.
    """
    
    IF NOT results:
        RETURN "[Контекст не найден]"
    
    context_parts = []
    
    FOR i, result IN enumerate(results, 1):
        # Determine source label
        IF result.content_type == "user_selected":
            source_label = "🧑 Human-in-the-Loop (100%)"
        ELIF result.content_type == "total_recall":
            source_label = "🧠 Total Recall (95%)"
        ELIF result.content_type == "smart_select":
            source_label = "⭐ Smart Select (95%)"
        ELIF result.content_type == "embeddings":
            source_label = "🔍 Embeddings (70-80%)"
        ELIF result.content_type == "external":
            source_label = "📁 External"
        ELSE:
            source_label = "🔍 Search"
        
        context_parts.append(f"""
### {i}. {result.file_path} ({source_label})
Score: {result.score:.2f}

```
{result.excerpt}
```
""")
    
    RETURN "\n".join(context_parts)
```

---

## FORMATTING METHODS

### format_as_prompt
```
METHOD format_as_prompt(text: str, context: List[SearchResultItem] = None) -> str:
    """
    Format text as AI prompt with context.
    """
    
    context_str = self._format_context_for_prompt(context) IF context ELSE "[Контекст не найден]"
    
    prompt = FORMAT_PROMPT_TEMPLATE.format(
        text=text,
        context=context_str
    )
    
    formatted = self.llm_backend.generate(
        prompt=prompt,
        temperature=0.2,
        max_tokens=3000
    )
    
    RETURN formatted.strip()
```

### format_as_ticket
```
METHOD format_as_ticket(text: str, context: List[SearchResultItem] = None) -> str:
    """
    Format text as ticket/task.
    """
    
    context_str = self._format_context_for_prompt(context) IF context ELSE "[Контекст не найден]"
    
    # Generate unique ticket ID
    ticket_id = datetime.now().strftime("%Y%m%d-%H%M")
    
    prompt = FORMAT_TICKET_TEMPLATE.format(
        text=text,
        context=context_str,
        id=ticket_id
    )
    
    formatted = self.llm_backend.generate(
        prompt=prompt,
        temperature=0.2,
        max_tokens=3000
    )
    
    RETURN formatted.strip()
```

### format_as_spec
```
METHOD format_as_spec(text: str, context: List[SearchResultItem] = None) -> str:
    """
    Format text as specification.
    """
    
    context_str = self._format_context_for_prompt(context) IF context ELSE "[Контекст не найден]"
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = FORMAT_SPEC_TEMPLATE.format(
        text=text,
        context=context_str,
        date=current_date
    )
    
    formatted = self.llm_backend.generate(
        prompt=prompt,
        temperature=0.2,
        max_tokens=4000
    )
    
    RETURN formatted.strip()
```

---

## MAIN PROCESSING PIPELINE

### process (Full Pipeline)
```
METHOD process(
    text: str,
    format_type: str = "enhanced",
    search_context: bool = True,
    pre_selected_context: List[str] = None
) -> ProcessingResult:
    """
    Full processing pipeline for voice message.
    
    ARGS:
        text: Raw transcribed text (Russian)
        format_type: One of 'as_is', 'enhanced', 'prompt', 'ticket', 'spec'
        search_context: Whether to search for context
        pre_selected_context: Pre-selected file paths (Human-in-the-Loop)
    
    RETURNS:
        ProcessingResult with all variants and metadata
    """
    
    start_time = time.time()
    llm_calls = 0
    result = ProcessingResult()
    
    TRY:
        # Step 1: Store original
        result.original_ru = text
        
        # Step 2: Enhance text (correct ASR + expand)
        IF format_type != "as_is":
            result.enhanced = self.enhance_text(text)
            llm_calls += 1
        ELSE:
            result.enhanced = text
        
        # Step 3: Translate to English
        result.original_en = self.translate_to_english(result.enhanced)
        llm_calls += 1
        
        # Step 4: Search for context
        context_results = []
        
        IF search_context:
            # Use pre-selected context if provided
            IF pre_selected_context:
                FOR file_path IN pre_selected_context:
                    context_results.append(SearchResultItem(
                        file_path=file_path,
                        score=1.0,
                        excerpt="[User selected]",
                        content_type="user_selected"
                    ))
            ELSE:
                # Auto-search
                context_results = self.search_context(result.enhanced, top_k=5)
        
        result.context_results = context_results
        
        # Build annotated context with source attribution
        result.annotated_context = []
        FOR ctx IN context_results:
            result.annotated_context.append({
                'path': ctx.file_path,
                'excerpt': ctx.excerpt,
                'source': ctx.content_type,
                'score': ctx.score
            })
        
        # Step 5: Format according to type
        result.format_type = format_type
        
        IF format_type == "as_is":
            result.formatted = result.enhanced
        
        ELIF format_type == "enhanced":
            result.formatted = result.enhanced
        
        ELIF format_type == "prompt":
            result.formatted = self.format_as_prompt(result.enhanced, context_results)
            llm_calls += 1
        
        ELIF format_type == "ticket":
            result.formatted = self.format_as_ticket(result.enhanced, context_results)
            llm_calls += 1
        
        ELIF format_type == "spec":
            result.formatted = self.format_as_spec(result.enhanced, context_results)
            llm_calls += 1
        
        ELSE:
            result.error = f"Unknown format_type: {format_type}"
            RETURN result
        
        # Step 6: Generate context summary
        IF context_results:
            result.context_summary = f"Found {len(context_results)} relevant files"
        ELSE:
            result.context_summary = "No context found"
        
        # Metadata
        result.processing_time_sec = time.time() - start_time
        result.llm_calls = llm_calls
        
        self.logger.info(f"Processing complete: {llm_calls} LLM calls, {result.processing_time_sec:.2f}s")
    
    EXCEPT Exception as e:
        result.error = str(e)
        self.logger.error(f"Processing error: {e}")
    
    RETURN result
```

---

## SINGLETON AND CONVENIENCE

### Global Instance
```
_processor: Optional[VoiceProcessor] = None

FUNCTION get_processor() -> VoiceProcessor:
    """Get default VoiceProcessor instance."""
    GLOBAL _processor
    IF _processor IS None:
        _processor = VoiceProcessor()
    RETURN _processor
```

### Convenience Function
```
FUNCTION process_voice(text: str, format_type: str = "enhanced") -> ProcessingResult:
    """Convenience function for voice processing."""
    processor = get_processor()
    RETURN processor.process(text, format_type=format_type)
```

---

## KEY FEATURES

### Source Attribution System
```
Source Labels (by reliability):
1. 🧑 Human-in-the-Loop (100%) - User manually selected
2. 🧠 Total Recall (95%) - LLM verified all files
3. ⭐ Smart Select (95%) - LLM suggested
4. 🔍 Embeddings (70-80%) - Vector search
5. 📁 External - User uploaded file

Used in:
- FORMAT_PROMPT_TEMPLATE
- FORMAT_TICKET_TEMPLATE
- FORMAT_SPEC_TEMPLATE
- _format_context_for_prompt()
```

### Text Expansion Strategy
```
ASR Correction + Expansion:
- Temperature: 0.3 (balanced)
- Target: ~20% expansion
- Constraint: "НЕ добавляй ничего, чего не было в оригинале"
- Focus: Конкретизация и детали

Translation:
- Temperature: 0.1 (accurate)
- Constraint: "Keep technical terms unchanged"
```

### Context Search Fallback
```
Priority:
1. DocsDualMemory (embeddings) - descriptions + code
2. UnifiedSearcher (fallback)
3. Empty context (still works)

Deduplication:
- By file_path
- Sort by score (descending)
- Top K results
```

---

## PERFORMANCE

### LLM Calls Per Format Type
- `as_is`: 1 call (translate only)
- `enhanced`: 2 calls (enhance + translate)
- `prompt`: 3 calls (enhance + translate + format)
- `ticket`: 3 calls (enhance + translate + format)
- `spec`: 3 calls (enhance + translate + format)

### Typical Processing Time
- Enhancement: ~2-3s
- Translation: ~2-3s
- Formatting: ~3-5s
- Context search: ~0.5-1s
- **Total**: 5-12s depending on format_type

---

<!--/TAG:voicepal_processor_pseudocode-->
