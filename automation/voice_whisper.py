#!/usr/bin/env python3
"""
Voice Whisper - Isolated Local Whisper Wrapper for docs/automation

<!--TAG:tool_voice_whisper-->

PURPOSE:
    Provides GPU-accelerated speech-to-text transcription using whisper.cpp.
    Isolated copy from utils/local_whisper.py for docs/ portability.
    
DOCUMENTATION:
    Spec: docs/specs/voice_interface_spec.md (TBD)
    Wiki: docs/wiki/09_Documentation_System.md
    
TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:transcription-->

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger (DocsLogger for logging)
    Config:
        - ~/whisper.cpp/build/bin/whisper-cli (binary)
        - ~/whisper.cpp/models/ggml-large-v3.bin (model)
    External:
        - ffmpeg (audio conversion)
        - NVIDIA GPU (for acceleration)

RECENT CHANGES:
    2025-12-12: Created isolated version for docs/automation

<!--/TAG:tool_voice_whisper-->
"""

import os  # Operating system interface for path and process management
import json  # JSON serialization for output parsing
import subprocess  # Subprocess management for whisper.cpp and ffmpeg
import time  # Time measurement for performance logging
import tempfile  # Temporary file management for audio processing
from pathlib import Path  # Object-oriented filesystem paths
from typing import Optional, Dict, Any, List  # Type hints for function signatures
from dataclasses import dataclass, field  # Structured data classes
import sys  # System-specific parameters for path manipulation

# Add docs to Python path for isolated utilities
DOCS_DIR = Path(__file__).resolve().parent.parent  # Navigate to docs/ directory
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))  # Add project root for imports
from utils.docs_logger import DocsLogger  # Paranoid logging from docs utilities

# Initialize paranoid logger for this module
logger = DocsLogger("voice_whisper")


# ============================================================================
# CONFIGURATION
# ============================================================================

# Whisper.cpp binary and model paths (user's system configuration)
WHISPER_BINARY = Path.home() / "whisper.cpp/build/bin/whisper-cli"  # Compiled whisper.cpp CLI
WHISPER_MODEL = Path.home() / "whisper.cpp/models/ggml-large-v3.bin"  # Large-v3 model for quality


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class TranscriptionResult:
    """
    Result of a transcription operation.
    
    Fields:
        text: Transcribed text content
        language: Detected language code (e.g., 'ru', 'en')
        duration_audio_sec: Duration of source audio in seconds
        duration_process_sec: Time taken to transcribe in seconds
        error: Error message if transcription failed
        raw_json: Full whisper.cpp JSON output for debugging
    """
    text: str = ""  # Transcribed text content
    language: str = "unknown"  # Detected language code
    duration_audio_sec: float = 0.0  # Audio duration in seconds
    duration_process_sec: float = 0.0  # Processing time in seconds
    error: Optional[str] = None  # Error message if any
    raw_json: Dict = field(default_factory=dict)  # Raw whisper.cpp output

    @property
    def success(self) -> bool:
        """Check if transcription was successful."""
        return self.error is None and len(self.text) > 0  # Success if no error and text exists


# ============================================================================
# VOICE WHISPER CLASS
# ============================================================================

class VoiceWhisper:
    """
    GPU-accelerated speech-to-text using whisper.cpp.
    
    Isolated from main project's utils/local_whisper.py for docs/ portability.
    Uses ffmpeg for audio format conversion and whisper.cpp for transcription.
    """
    
    def __init__(
        self, 
        binary_path: Path = WHISPER_BINARY, 
        model_path: Path = WHISPER_MODEL,
        api_url: str = "http://127.0.0.1:8002"
    ):
        """
        Initialize VoiceWhisper with hybrid API/CLI support.
        
        Args:
            binary_path: Path to whisper-cli binary (fallback)
            model_path: Path to GGML model file (fallback)
            api_url: URL of the running whisper-server (primary)
        """
        self.binary_path = binary_path
        self.model_path = model_path
        self.api_url = api_url.rstrip('/')
        
        # Log initialization status
        logger.info("Initializing VoiceWhisper (Hybrid Mode)", {
            "api_url": self.api_url,
            "binary": str(self.binary_path),
            "model": str(self.model_path)
        })
        
        # Check binary availability (Warning only, as API might be primary)
        if not self.binary_path.exists():
            logger.warning(f"Whisper binary not found at {self.binary_path} (CLI fallback unavailable)")
        
        # Check model availability
        if not self.model_path.exists():
            logger.warning(f"Whisper model not found at {self.model_path} (CLI fallback unavailable)")

    def _set_pdeathsig(self):
        """
        Set process death signal for child processes (Linux only).
        """
        try:
            import ctypes
            import signal
            libc = ctypes.CDLL("libc.so.6")
            libc.prctl(1, signal.SIGTERM)
        except Exception:
            pass
    
    def _convert_to_wav16k(self, input_path: Path, temp_dir: Path) -> Optional[Path]:
        """
        Convert audio to 16kHz mono WAV required by whisper.cpp.
        """
        safe_name = f"convert_{int(time.time() * 1000)}.wav"
        temp_wav = temp_dir / safe_name
        
        try:
            cmd = [
                "ffmpeg", "-y", "-v", "error",
                "-i", str(input_path),
                "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
                str(temp_wav)
            ]
            
            with subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                preexec_fn=self._set_pdeathsig
            ) as process:
                _, stderr = process.communicate()
                
                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else 'Unknown error'
                    logger.error(f"FFmpeg conversion failed: {error_msg}")
                    return None
                    
            return temp_wav
            
        except Exception as e:
            logger.error(f"FFmpeg error: {e}")
            return None
    
    def _get_audio_duration(self, input_path: Path) -> float:
        """Get audio duration in seconds using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(input_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    def _transcribe_api(self, audio_path: Path) -> Optional[TranscriptionResult]:
        """Attempt transcription via HTTP API."""
        import urllib.request
        import urllib.error
        import mimetypes

        # Simple health check first
        try:
            with urllib.request.urlopen(f"{self.api_url}/health", timeout=1) as response:
                if response.status != 200:
                    return None
        except Exception:
            # If health check fails, assume server down (or non-standard endpoint), try inference anyway
            # or just failover. Let's try failover to be safe.
            # Actually, whisper.cpp server might not have /health, it has /inference
            pass

        start_time = time.time()
        
        # Prepare multipart upload manually (to avoid requests dependency fallback)
        # Or just use requests if we assume it's there (it is in our environment)
        try:
            import requests
        except ImportError:
            logger.warning("Requests library not found, skipping API mode")
            return None

        try:
            # Whisper.cpp server (OpenAI compatible) expects:
            # POST /v1/audio/transcriptions (or /inference matching our server script)
            # Body: multipart/form-data; file=@audio; model=whatever; language=ru
            
            # Note: Our script starts with --convert, so it might handle formats, 
            # but ffmpeg conversion locally is safer.
            
            files = {
                'file': ('audio.wav', open(audio_path, 'rb'), 'audio/wav')
            }
            data = {
                'language': 'ru',
                'response_format': 'json'
            }
            
            # Try typical OpenAI endpoint
            endpoint = f"{self.api_url}/inference" 
            
            logger.info(f"Attempting API transcription at {endpoint}")
            
            response = requests.post(endpoint, files=files, data=data, timeout=300)
            
            if response.status_code == 200:
                data = response.json()
                text = data.get('text', '')
                
                duration = time.time() - start_time
                audio_duration = self._get_audio_duration(audio_path)
                
                return TranscriptionResult(
                    text=text.strip(),
                    language='ru', # Forced
                    duration_audio_sec=audio_duration,
                    duration_process_sec=duration,
                    raw_json=data
                )
            else:
                logger.warning(f"API returned {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.warning(f"API transcription failed: {e}")
            return None

    def _transcribe_cli(self, audio_path: Path, use_gpu: bool = True) -> TranscriptionResult:
        """Fallback transcription using CLI."""
        # Get audio duration before processing
        audio_duration = self._get_audio_duration(audio_path)
        
        with tempfile.TemporaryDirectory(prefix="whisper_txn_") as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            
            # Step 1: Convert
            converted_path = self._convert_to_wav16k(audio_path, temp_dir)
            if not converted_path:
                return TranscriptionResult(error="Audio conversion failed")
            
            try:
                # Step 2: Build command
                output_prefix = temp_dir / "output"
                
                cmd = [
                    str(self.binary_path),
                    "-m", str(self.model_path),
                    "-f", str(converted_path),
                    "-l", "ru",
                    "-oj", "-np",
                    "-of", str(output_prefix)
                ]
                
                if not use_gpu:
                    cmd.append("-ng")
                
                start_time = time.time()
                
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=self._set_pdeathsig
                )
                
                try:
                    stdout, stderr = process.communicate()
                except Exception:
                    process.kill()
                    process.wait()
                    raise
                
                duration = time.time() - start_time
                
                if process.returncode != 0:
                    return TranscriptionResult(
                        error=f"Whisper failed with code {process.returncode}",
                        duration_process_sec=duration
                    )
                
                # Step 4: Read JSON
                json_output_path = output_prefix.with_suffix(".json")
                if not json_output_path.exists():
                    return TranscriptionResult(error="JSON output not generated", duration_process_sec=duration)
                    
                data = json.loads(json_output_path.read_text(encoding="utf-8"))
                
                full_text = ""
                if "transcription" in data:
                    full_text = "".join([s.get("text", "") for s in data["transcription"]])
                elif "text" in data:
                    full_text = data["text"]
                
                return TranscriptionResult(
                    text=full_text.strip(),
                    language=data.get("language", "unknown"),
                    duration_audio_sec=audio_duration,
                    duration_process_sec=duration,
                    raw_json=data
                )
                
            except Exception as e:
                return TranscriptionResult(error=str(e))

    def transcribe(self, audio_path: Path, use_gpu: bool = True) -> TranscriptionResult:
        """
        Transcribe audio using API (preferred) or CLI (fallback).
        """
        logger.info(f"Starting transcription of {audio_path.name}")
        
        if not audio_path.exists():
             return TranscriptionResult(error=f"Audio file not found: {audio_path}")

        # Try API first
        api_result = self._transcribe_api(audio_path)
        if api_result:
            logger.info("API Transcription Successful")
            return api_result
            
        logger.info("API unavailable or failed, falling back to CLI")
        
        # Fallback to CLI
        if not self.binary_path.exists() or not self.model_path.exists():
            return TranscriptionResult(error="CLI tools not found and API failed")
            
        return self._transcribe_cli(audio_path, use_gpu)
    
    def check_health(self) -> tuple:
        """Check availability of API or CLI."""
        # Check API
        import requests
        try:
            # Trying root or health
            resp = requests.get(f"{self.api_url}/health", timeout=0.5)
            if resp.status_code == 200:
                return ("OK", {"mode": "API", "url": self.api_url})
        except:
            pass
            
        # Check CLI
        if self.binary_path.exists() and self.model_path.exists():
            return ("OK", {"mode": "CLI", "binary": str(self.binary_path)})
            
        return ("ERROR", {"message": "Neither API nor CLI available"})


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Create default instance for convenience
whisper_service = VoiceWhisper()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def transcribe(audio_path: Path, use_gpu: bool = True) -> TranscriptionResult:
    """
    Convenience function to transcribe an audio file.
    
    Args:
        audio_path: Path to audio file
        use_gpu: Whether to use GPU acceleration
        
    Returns:
        TranscriptionResult with transcription data
    """
    return whisper_service.transcribe(audio_path, use_gpu)


def check_whisper_health() -> tuple:
    """Check if whisper.cpp is ready."""
    return whisper_service.check_health()


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Voice Whisper - GPU-accelerated transcription for docs/automation"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Audio file to transcribe"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check whisper.cpp health status"
    )
    parser.add_argument(
        "--no-gpu",
        action="store_true",
        help="Disable GPU acceleration"
    )
    
    args = parser.parse_args()
    
    if args.health:
        # Health check mode
        status, info = check_whisper_health()
        print(f"Status: {status}")
        print(json.dumps(info, indent=2))
    elif args.file:
        # Transcription mode
        audio_path = Path(args.file)
        result = transcribe(audio_path, use_gpu=not args.no_gpu)
        
        if result.success:
            print(f"\n{'='*60}")
            print(f"Transcription ({result.language})")
            print(f"{'='*60}")
            print(result.text)
            print(f"\n{'='*60}")
            print(f"Audio: {result.duration_audio_sec:.2f}s | Process: {result.duration_process_sec:.2f}s")
            print(f"Speed: {result.duration_audio_sec/result.duration_process_sec:.1f}x real-time")
        else:
            print(f"Error: {result.error}")
    else:
        parser.print_help()
