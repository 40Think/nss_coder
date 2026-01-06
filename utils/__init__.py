"""
Documentation System Utilities

Isolated utilities for docs/automation scripts.
Independent from main project's utils/ directory.
"""

from .docs_logger import DocsLogger, get_logger
from .docs_config import DocsConfig, docs_config, get_config
from .docs_llm_backend import DocsLLMBackend, get_backend, generate
from .docs_dual_memory import (
    DocsDualMemory, 
    DocsDualMemoryIndex,
    ContentChunk,
    SearchResult,
    unified_search,
    build_dual_memory
)

__all__ = [
    # Logger
    'DocsLogger',
    'get_logger',
    
    # Config
    'DocsConfig', 
    'docs_config',
    'get_config',
    
    # LLM Backend
    'DocsLLMBackend',
    'get_backend',
    'generate',
    
    # Dual Memory
    'DocsDualMemory',
    'DocsDualMemoryIndex',
    'ContentChunk',
    'SearchResult',
    'unified_search',
    'build_dual_memory',
]
