#!/usr/bin/env python3
"""
Voice Whisper Fast - GPU-accelerated Whisper using faster-whisper

<!--TAG:tool_voice_whisper_fast-->

PURPOSE:
    Provides high-performance speech-to-text transcription using faster-whisper.
    Replaces whisper.cpp with CTranslate2 backend for better GPU utilization.
    Supports batched inference, VAD filtering, and long audio chunking.
    
DOCUMENTATION:
    Spec: docs/specs/voice_interface_spec.md (TBD)
    Wiki: docs/wiki/09_Documentation_System.md
    Research: ~/.gemini/.../whisper_inference_research.md
    
TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:transcription-->

DEPENDENCIES:
    Python:
        - faster-whisper>=1.2.0 (CTranslate2 backend)
        - torch (for GPU detection)
    Hardware:
        - NVIDIA GPU with CUDA support (primary)
        - CPU fallback available

PERFORMANCE (RTX PRO 6000 Blackwell, 96GB):
    - 1 hour audio: ~60-90 seconds
    - Batch 10 files × 5 min: ~30-45 seconds
    - Real-time factor: 40-80x

RECENT CHANGES:
    2025-12-16: Created with faster-whisper backend

<!--/TAG:tool_voice_whisper_fast-->
"""

import os  # Operating system interface
import time  # Time measurement for performance logging
import tempfile  # Temporary file management
import subprocess  # For ffmpeg audio conversion
from pathlib import Path  # Object-oriented filesystem paths
from typing import Optional, Dict, Any, List, Generator, Union  # Type hints
from dataclasses import dataclass, field  # Structured data classes
import sys  # System-specific parameters

# ============================================================================
# CUDA LIBRARY PATH SETUP (Must be done before importing faster-whisper)
# ============================================================================

def _setup_cuda_library_paths():
    """
    Automatically configure LD_LIBRARY_PATH for NVIDIA cuDNN/cuBLAS libraries.
    This is required for CTranslate2 to find the GPU libraries.
    """
    nvidia_lib_paths = []
    
    # Find nvidia-cudnn and nvidia-cublas installed via pip
    for site_packages in sys.path:
        cudnn_lib = Path(site_packages) / "nvidia" / "cudnn" / "lib"
        cublas_lib = Path(site_packages) / "nvidia" / "cublas" / "lib"
        
        if cudnn_lib.exists():
            nvidia_lib_paths.append(str(cudnn_lib))
        if cublas_lib.exists():
            nvidia_lib_paths.append(str(cublas_lib))
    
    # Add to LD_LIBRARY_PATH if not already present
    if nvidia_lib_paths:
        current_ld_path = os.environ.get("LD_LIBRARY_PATH", "")
        new_paths = [p for p in nvidia_lib_paths if p not in current_ld_path]
        
        if new_paths:
            os.environ["LD_LIBRARY_PATH"] = ":".join(new_paths + [current_ld_path])

# Apply CUDA library path setup
_setup_cuda_library_paths()

# Add docs to Python path for isolated utilities
DOCS_DIR = Path(__file__).resolve().parent.parent  # Navigate to docs/ directory
sys.path.insert(0, str(DOCS_DIR.parent))  # Add project root for imports

try:
    from docs.utils.docs_logger import DocsLogger  # Paranoid logging
    logger = DocsLogger("voice_whisper_fast")
except ImportError:
    # Fallback to simple logging
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("voice_whisper_fast")

# Check faster-whisper availability
try:
    from faster_whisper import WhisperModel, BatchedInferencePipeline
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed. Run: pip install faster-whisper")


# ============================================================================
# CONFIGURATION
# ============================================================================

# Model configuration
DEFAULT_MODEL_SIZE = "large-v3"  # Best quality for Russian and English
DEFAULT_DEVICE = "cuda"  # GPU acceleration
DEFAULT_COMPUTE_TYPE = "float16"  # FP16 for speed/memory balance
DEFAULT_BATCH_SIZE = 32  # Optimal for 96GB VRAM (can go up to 64)

# VAD (Voice Activity Detection) configuration
DEFAULT_VAD_FILTER = True  # Remove silence for efficiency
DEFAULT_VAD_PARAMETERS = {
    "min_silence_duration_ms": 500,  # Minimum silence to split on
    "speech_pad_ms": 400,  # Padding around speech segments
    "threshold": 0.5  # VAD confidence threshold
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class TranscriptionSegment:
    """Single segment of transcription with timing information."""
    text: str  # Transcribed text
    start: float  # Start time in seconds
    end: float  # End time in seconds
    words: List[Dict] = field(default_factory=list)  # Word-level timestamps


@dataclass
class TranscriptionResult:
    """
    Result of a transcription operation.
    Compatible with voice_whisper.py API.
    """
    text: str = ""  # Full transcribed text
    language: str = "unknown"  # Detected language code
    duration_audio_sec: float = 0.0  # Audio duration in seconds
    duration_process_sec: float = 0.0  # Processing time in seconds
    error: Optional[str] = None  # Error message if any
    segments: List[TranscriptionSegment] = field(default_factory=list)  # Detailed segments
    raw_info: Dict = field(default_factory=dict)  # Raw faster-whisper info
    
    @property
    def success(self) -> bool:
        """Check if transcription was successful."""
        return self.error is None and len(self.text) > 0
    
    @property
    def speed_factor(self) -> float:
        """Calculate real-time factor (RTF)."""
        if self.duration_process_sec > 0:
            return self.duration_audio_sec / self.duration_process_sec
        return 0.0


# ============================================================================
# FASTER WHISPER SERVICE
# ============================================================================

class FasterWhisperService:
    """
    High-performance speech-to-text using faster-whisper.
    
    Features:
        - GPU-accelerated inference with CTranslate2
        - Batched processing for multiple files
        - VAD filtering for efficient long audio
        - Automatic chunking for hours-long recordings
    
    Usage:
        service = FasterWhisperService()
        result = service.transcribe("audio.mp3", language="ru")
        print(result.text)
    """
    
    def __init__(
        self,
        model_size: str = DEFAULT_MODEL_SIZE,
        device: str = DEFAULT_DEVICE,
        compute_type: str = DEFAULT_COMPUTE_TYPE,
        batch_size: int = DEFAULT_BATCH_SIZE,
        cpu_threads: int = 0  # 0 = auto-detect
    ):
        """
        Initialize FasterWhisperService.
        
        Args:
            model_size: Whisper model size ("large-v3", "medium", etc.)
            device: Device to use ("cuda" or "cpu")
            compute_type: Compute precision ("float16", "int8", etc.)
            batch_size: Batch size for batched inference
            cpu_threads: Number of CPU threads (0 = auto)
        """
        if not FASTER_WHISPER_AVAILABLE:
            raise RuntimeError("faster-whisper not installed")
        
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.batch_size = batch_size
        self.cpu_threads = cpu_threads
        
        # Model instances (lazy loaded)
        self._model: Optional[WhisperModel] = None
        self._batched_pipeline: Optional[BatchedInferencePipeline] = None
        
        logger.info("FasterWhisperService initialized", {
            "model_size": model_size,
            "device": device,
            "compute_type": compute_type,
            "batch_size": batch_size
        })
    
    def _ensure_model_loaded(self) -> WhisperModel:
        """Lazy load the Whisper model."""
        if self._model is None:
            logger.info(f"Loading Whisper model: {self.model_size}")
            start = time.time()
            
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=self.cpu_threads if self.device == "cpu" else 0
            )
            
            load_time = time.time() - start
            logger.info(f"Model loaded in {load_time:.2f}s")
        
        return self._model
    
    def _ensure_batched_pipeline(self) -> BatchedInferencePipeline:
        """Lazy load the batched inference pipeline."""
        if self._batched_pipeline is None:
            model = self._ensure_model_loaded()
            self._batched_pipeline = BatchedInferencePipeline(model=model)
            logger.info("BatchedInferencePipeline initialized")
        
        return self._batched_pipeline
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration in seconds using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except Exception:
            return 0.0
    
    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: str = "ru",
        use_vad: bool = DEFAULT_VAD_FILTER,
        vad_parameters: Optional[Dict] = None,
        use_batched: bool = True,
        word_timestamps: bool = False
    ) -> TranscriptionResult:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to audio file (any format supported by ffmpeg)
            language: Language code ("ru", "en", or None for auto-detect)
            use_vad: Enable Voice Activity Detection filtering
            vad_parameters: Custom VAD parameters (optional)
            use_batched: Use batched inference pipeline (recommended)
            word_timestamps: Enable word-level timestamps
        
        Returns:
            TranscriptionResult with transcription data
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            return TranscriptionResult(error=f"Audio file not found: {audio_path}")
        
        logger.info(f"Starting transcription: {audio_path.name}", {
            "language": language,
            "use_vad": use_vad,
            "use_batched": use_batched
        })
        
        # Get audio duration for stats
        audio_duration = self._get_audio_duration(audio_path)
        
        start_time = time.time()
        
        try:
            # Prepare VAD parameters
            vad_params = vad_parameters or DEFAULT_VAD_PARAMETERS
            
            if use_batched:
                # Use batched pipeline for better performance
                pipeline = self._ensure_batched_pipeline()
                segments_gen, info = pipeline.transcribe(
                    str(audio_path),
                    batch_size=self.batch_size,
                    language=language,
                    vad_filter=use_vad,
                    vad_parameters=vad_params if use_vad else None,
                    word_timestamps=word_timestamps
                )
            else:
                # Use regular model
                model = self._ensure_model_loaded()
                segments_gen, info = model.transcribe(
                    str(audio_path),
                    language=language,
                    vad_filter=use_vad,
                    vad_parameters=vad_params if use_vad else None,
                    word_timestamps=word_timestamps
                )
            
            # Collect segments
            segments = []
            full_text_parts = []
            
            for segment in segments_gen:
                seg = TranscriptionSegment(
                    text=segment.text,
                    start=segment.start,
                    end=segment.end,
                    words=[{"word": w.word, "start": w.start, "end": w.end} 
                           for w in (segment.words or [])]
                )
                segments.append(seg)
                full_text_parts.append(segment.text)
            
            process_time = time.time() - start_time
            full_text = "".join(full_text_parts).strip()
            
            result = TranscriptionResult(
                text=full_text,
                language=info.language or language,
                duration_audio_sec=audio_duration or info.duration,
                duration_process_sec=process_time,
                segments=segments,
                raw_info={
                    "language_probability": info.language_probability,
                    "duration": info.duration,
                    "all_language_probs": getattr(info, 'all_language_probs', None)
                }
            )
            
            logger.info(f"Transcription complete", {
                "audio_sec": result.duration_audio_sec,
                "process_sec": result.duration_process_sec,
                "speed_factor": f"{result.speed_factor:.1f}x",
                "text_length": len(full_text)
            })
            
            return result
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Transcription failed: {e}")
            return TranscriptionResult(
                error=str(e),
                duration_audio_sec=audio_duration,
                duration_process_sec=process_time
            )
    
    def transcribe_batch(
        self,
        audio_paths: List[Union[str, Path]],
        language: str = "ru",
        use_vad: bool = True
    ) -> List[TranscriptionResult]:
        """
        Transcribe multiple audio files.
        
        Args:
            audio_paths: List of audio file paths
            language: Language code
            use_vad: Enable VAD filtering
        
        Returns:
            List of TranscriptionResult objects
        """
        results = []
        for path in audio_paths:
            result = self.transcribe(path, language=language, use_vad=use_vad)
            results.append(result)
        return results
    
    def check_health(self) -> tuple:
        """Check service health and GPU availability."""
        try:
            import torch
            
            gpu_available = torch.cuda.is_available()
            gpu_name = torch.cuda.get_device_name(0) if gpu_available else "N/A"
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3 if gpu_available else 0
            
            # Check if model is loaded
            model_loaded = self._model is not None
            
            return ("OK", {
                "mode": "faster-whisper",
                "model_size": self.model_size,
                "device": self.device,
                "gpu_available": gpu_available,
                "gpu_name": gpu_name,
                "gpu_memory_gb": f"{gpu_memory:.1f}",
                "model_loaded": model_loaded,
                "batch_size": self.batch_size
            })
        except Exception as e:
            return ("ERROR", {"message": str(e)})
    
    def unload_model(self):
        """Unload model to free GPU memory."""
        if self._model is not None:
            del self._model
            del self._batched_pipeline
            self._model = None
            self._batched_pipeline = None
            
            # Clear CUDA cache
            try:
                import torch
                torch.cuda.empty_cache()
            except:
                pass
            
            logger.info("Model unloaded, GPU memory freed")


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Create default instance (lazy loaded)
_faster_whisper_service: Optional[FasterWhisperService] = None

def get_faster_whisper_service() -> FasterWhisperService:
    """Get or create the singleton FasterWhisperService instance."""
    global _faster_whisper_service
    if _faster_whisper_service is None:
        _faster_whisper_service = FasterWhisperService()
    return _faster_whisper_service


# ============================================================================
# CONVENIENCE FUNCTIONS (Compatible with voice_whisper.py API)
# ============================================================================

def transcribe(audio_path: Path, use_gpu: bool = True, language: str = "ru") -> TranscriptionResult:
    """
    Convenience function to transcribe an audio file.
    API compatible with voice_whisper.py.
    
    Args:
        audio_path: Path to audio file
        use_gpu: Whether to use GPU (ignored, always uses configured device)
        language: Language code ("ru", "en")
    
    Returns:
        TranscriptionResult with transcription data
    """
    service = get_faster_whisper_service()
    return service.transcribe(audio_path, language=language)


def check_whisper_health() -> tuple:
    """Check if faster-whisper is ready."""
    if not FASTER_WHISPER_AVAILABLE:
        return ("ERROR", {"message": "faster-whisper not installed"})
    
    service = get_faster_whisper_service()
    return service.check_health()


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(
        description="Voice Whisper Fast - GPU-accelerated transcription using faster-whisper"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Audio file to transcribe"
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="ru",
        help="Language code (ru, en, auto)"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check service health status"
    )
    parser.add_argument(
        "--no-vad",
        action="store_true",
        help="Disable Voice Activity Detection"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for inference"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    if args.health:
        # Health check mode
        status, info = check_whisper_health()
        if args.json:
            print(json.dumps({"status": status, **info}, indent=2))
        else:
            print(f"Status: {status}")
            for k, v in info.items():
                print(f"  {k}: {v}")
    
    elif args.file:
        # Transcription mode
        audio_path = Path(args.file)
        
        service = FasterWhisperService(batch_size=args.batch_size)
        result = service.transcribe(
            audio_path,
            language=args.language if args.language != "auto" else None,
            use_vad=not args.no_vad
        )
        
        if args.json:
            print(json.dumps({
                "success": result.success,
                "text": result.text,
                "language": result.language,
                "duration_audio_sec": result.duration_audio_sec,
                "duration_process_sec": result.duration_process_sec,
                "speed_factor": result.speed_factor,
                "error": result.error
            }, indent=2, ensure_ascii=False))
        elif result.success:
            print(f"\n{'='*60}")
            print(f"Transcription ({result.language})")
            print(f"{'='*60}")
            print(result.text)
            print(f"\n{'='*60}")
            print(f"Audio: {result.duration_audio_sec:.2f}s | Process: {result.duration_process_sec:.2f}s")
            print(f"Speed: {result.speed_factor:.1f}x real-time")
        else:
            print(f"Error: {result.error}")
    
    else:
        parser.print_help()
