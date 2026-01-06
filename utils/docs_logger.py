#!/usr/bin/env python3
"""
DocsLogger - Isolated Paranoid Logger for Documentation System

<!--TAG:docs_utils_logger-->

PURPOSE:
    Thread-safe logger for docs/automation scripts.
    Writes logs to docs/logs/ directory, independent from main project.
    Simplified version of utils/paranoid_logger.py for portability.

DOCUMENTATION:
    Wiki: docs/wiki/nss_docs_standalone.md (planned)
    
<!--/TAG:docs_utils_logger-->
"""

import os
import logging
import threading
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

# Docs directory (parent of utils/)
DOCS_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = DOCS_DIR / "logs"


class DocsLogger:
    """
    Thread-safe logger for documentation automation scripts.
    
    Writes logs to docs/logs/{script_name}/ directory.
    """
    
    _instances = {}  # Singleton per script name
    _lock = threading.RLock()  # Thread safety lock

    def __new__(cls, script_name: str, log_to_console: bool = False):
        """Singleton pattern - one logger per script name."""
        with cls._lock:
            if script_name not in cls._instances:
                cls._instances[script_name] = super(DocsLogger, cls).__new__(cls)
                cls._instances[script_name]._initialize(script_name, log_to_console)
            return cls._instances[script_name]

    def _initialize(self, script_name: str, log_to_console: bool = False):
        """Initialize logger with file and optional console output."""
        self.script_name = script_name
        
        # Create log directory
        self.log_dir = LOGS_DIR / script_name
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{timestamp}_{os.getpid()}.log"
        
        # Configure python logger
        self.logger = logging.getLogger(f"docs_{script_name}_{os.getpid()}")
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # File handler
        fh = logging.FileHandler(self.log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # Format: [Time] [Thread] [Level] Message
        formatter = logging.Formatter(
            '%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s'
        )
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        # Console handler (optional)
        if log_to_console:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
        
        # Don't propagate to root logger
        self.logger.propagate = False

    def log(self, message: str, level: str = "INFO", context: Optional[Dict[str, Any]] = None):
        """Log message with optional context."""
        if context:
            context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
            full_message = f"{message} | Context: [{context_str}]"
        else:
            full_message = message
        
        level_map = {
            "DEBUG": self.logger.debug,
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "CRITICAL": self.logger.critical
        }
        
        log_func = level_map.get(level.upper(), self.logger.info)
        log_func(full_message)
        
        # Force flush for crash forensics
        for handler in self.logger.handlers:
            handler.flush()

    def log_json(self, message: str, data: Any, level: str = "INFO"):
        """Log structured data as JSON."""
        try:
            json_str = json.dumps(data, default=str, ensure_ascii=False)
            self.log(f"{message} | JSON: {json_str}", level)
        except Exception as e:
            self.log(f"{message} | JSON_ERROR: {e}", "ERROR")

    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self.log(message, "INFO", context)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self.log(message, "ERROR", context)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self.log(message, "WARNING", context)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self.log(message, "DEBUG", context)

    def log_step(self, name: str, status: str = "COMPLETED", 
                 duration: float = 0.0, context: Optional[Dict] = None):
        """Log a logical step in processing."""
        msg = f"STEP: {name} | Status: {status} | Duration: {duration:.2f}s"
        level = "INFO" if status == "COMPLETED" else "ERROR"
        self.log(msg, level=level, context=context)

    def log_file_interaction(self, file_path: str, action: str, 
                            status: str = "SUCCESS", metadata: Optional[Dict] = None):
        """Log file operations with metadata."""
        path = Path(file_path)
        file_info = {
            "path": str(path),
            "action": action,
            "status": status,
            "exists": path.exists()
        }
        
        if path.exists() and path.is_file():
            try:
                stat = path.stat()
                file_info["size_bytes"] = stat.st_size
                file_info["mtime"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except Exception as e:
                file_info["error"] = str(e)
        
        if metadata:
            file_info.update(metadata)
        
        self.log_json(f"FILE_INTERACTION: {action}", file_info)

    def log_llm_interaction(self, system_prompt: str, user_prompt: str, 
                           response: str, metadata: Dict = None):
        """Log LLM API interactions."""
        separator = "=" * 60
        msg = f"""
{separator}
LLM INTERACTION
{separator}
METADATA: {metadata}
{separator}
SYSTEM PROMPT:
{system_prompt[:500]}{'...' if len(system_prompt) > 500 else ''}
{separator}
USER PROMPT:
{user_prompt[:500]}{'...' if len(user_prompt) > 500 else ''}
{separator}
RESPONSE:
{response[:1000]}{'...' if len(response) > 1000 else ''}
{separator}
"""
        self.logger.info(msg)
        for handler in self.logger.handlers:
            handler.flush()


def get_logger(script_name: str, log_to_console: bool = False) -> DocsLogger:
    """Convenience function to get a logger instance."""
    return DocsLogger(script_name, log_to_console=log_to_console)
