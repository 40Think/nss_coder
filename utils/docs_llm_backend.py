#!/usr/bin/env python3
"""
DocsLLMBackend - LLM Backend for Documentation System

<!--TAG:docs_utils_llm_backend-->

PURPOSE:
    Provides LLM generation capabilities for docs/automation scripts.
    Supports vLLM, LM Studio, and OpenAI-compatible endpoints.
    Independent from main project's utils/vllm_backend.py.

<!--/TAG:docs_utils_llm_backend-->
"""

import time
import requests
from typing import Optional, Dict, List, Any
from pathlib import Path

# Import local utilities
from .docs_logger import DocsLogger
from .docs_config import docs_config

# Initialize logger
logger = DocsLogger("docs_llm_backend")


class DocsLLMBackend:
    """
    LLM Backend for documentation system.
    
    Supports vLLM/OpenAI-compatible endpoints.
    """
    
    def __init__(self, endpoint: str = None, model: str = None):
        """
        Initialize LLM backend.
        
        Args:
            endpoint: API endpoint URL (default from config)
            model: Model name (default from config)
        """
        self.endpoint = endpoint or docs_config.get(
            "llm.vllm_endpoint", 
            "http://localhost:8000/v1/chat/completions"
        )
        self.model = model or docs_config.get(
            "llm.model_name",
            "qwen3-coder-30b-a3b-instruct_moe"  # Matches start_vllm_server.sh --served-model-name
        )
        self.timeout = int(docs_config.get("llm.timeout", 120))
        
        logger.info(f"Initialized LLM backend", {
            "endpoint": self.endpoint,
            "model": self.model
        })
    
    def generate(self, system_prompt: str, user_prompt: str, 
                 temperature: float = None, max_tokens: int = None) -> Optional[str]:
        """
        Generate text using LLM.
        
        Args:
            system_prompt: System/instruction prompt
            user_prompt: User message
            temperature: Sampling temperature (default from config)
            max_tokens: Maximum tokens to generate (default from config)
            
        Returns:
            Generated text or None on error
        """
        start_time = time.time()
        
        # Use config defaults if not specified
        if temperature is None:
            temperature = float(docs_config.get("llm.temperature", 0.7))
        if max_tokens is None:
            max_tokens = int(docs_config.get("llm.max_tokens", 4000))
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                self.endpoint, 
                json=payload, 
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            result = data['choices'][0]['message']['content']
            
            duration = time.time() - start_time
            logger.log_llm_interaction(
                system_prompt, user_prompt, result,
                {"duration": duration, "status": "success", "model": self.model}
            )
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"LLM request timed out after {self.timeout}s")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM request failed: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None
    
    def check_health(self) -> tuple:
        """
        Check if LLM server is available.
        
        Returns:
            Tuple of (status, details) where status is 'OK', 'ERROR', or 'NO_SERVER'
        """
        try:
            # Try health endpoint
            health_url = self.endpoint.replace("/v1/chat/completions", "/health")
            response = requests.get(health_url, timeout=5)
            
            if response.ok:
                return ("OK", {"message": "LLM server is healthy"})
            else:
                return ("ERROR", {"message": f"Server returned {response.status_code}"})
                
        except requests.exceptions.RequestException as e:
            return ("NO_SERVER", {"message": f"Cannot connect: {e}"})
    
    def is_available(self) -> bool:
        """Check if LLM backend is available."""
        status, _ = self.check_health()
        return status == "OK"


# Singleton instance
_default_backend = None


def get_backend() -> DocsLLMBackend:
    """Get default LLM backend instance."""
    global _default_backend
    if _default_backend is None:
        _default_backend = DocsLLMBackend()
    return _default_backend


def generate(system_prompt: str, user_prompt: str, **kwargs) -> Optional[str]:
    """Convenience function to generate text."""
    return get_backend().generate(system_prompt, user_prompt, **kwargs)
