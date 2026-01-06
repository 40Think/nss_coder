# voice_whisper.py - Pseudocode

<!--TAG:voicepal_whisper_pseudocode-->

> ⚠️ **DEPRECATED (2025-12-16)**: This describes the OLD whisper.cpp backend.
> See **voice_whisper_fast.py** for the CURRENT faster-whisper implementation.
> Migration achieved **82.7x real-time** performance on RTX PRO 6000 Blackwell.

## PURPOSE
GPU-accelerated speech-to-text transcription using whisper.cpp.
Isolated wrapper for docs/automation with ffmpeg audio conversion.

**STATUS**: LEGACY - kept as fallback. Primary backend is now `voice_whisper_fast.py`.

## DEPENDENCIES
- whisper.cpp binary (~/whisper.cpp/build/bin/whisper-cli) — LEGACY
- GGML model (~/whisper.cpp/models/ggml-large-v3.bin)
- ffmpeg (audio conversion)
- ffprobe (duration extraction)
- NVIDIA GPU (for acceleration)
- docs.utils.docs_logger (DocsLogger)

---

## CONFIGURATION

### Paths
```
WHISPER_BINARY = ~/whisper.cpp/build/bin/whisper-cli
WHISPER_MODEL = ~/whisper.cpp/models/ggml-large-v3.bin
```

---

## DATA STRUCTURES

### TranscriptionResult
```
DATACLASS TranscriptionResult:
    text: str = ""                      # Transcribed text content
    language: str = "unknown"           # Detected language (e.g., 'ru', 'en')
    duration_audio_sec: float = 0.0    # Audio duration in seconds
    duration_process_sec: float = 0.0  # Processing time in seconds
    error: Optional[str] = None         # Error message if failed
    raw_json: Dict = {}                 # Full whisper.cpp JSON output
    
    PROPERTY success:
        RETURN self.error IS None AND len(self.text) > 0
```

---

## MAIN CLASS: VoiceWhisper

### Initialization
```
CLASS VoiceWhisper:
    CONSTRUCTOR(binary_path: Path, model_path: Path):
        self.binary_path = binary_path
        self.model_path = model_path
        self.logger = DocsLogger("voice_whisper")
        
        # Validate paths
        IF NOT binary_path.exists():
            logger.warning(f"Binary not found: {binary_path}")
        
        IF NOT model_path.exists():
            logger.warning(f"Model not found: {model_path}")
```

---

## CORE METHODS

### _set_pdeathsig (Linux Process Management)
```
METHOD _set_pdeathsig():
    """
    Set process death signal for child processes.
    Ensures ffmpeg/whisper are killed if parent dies.
    """
    
    TRY:
        import ctypes
        import signal
        libc = ctypes.CDLL("libc.so.6")
        libc.prctl(1, signal.SIGTERM)  # PR_SET_PDEATHSIG = 1
    EXCEPT:
        PASS  # Silently ignore on non-Linux systems
```

### _convert_to_wav16k (Audio Conversion)
```
METHOD _convert_to_wav16k(input_path: Path, temp_dir: Path) -> Optional[Path]:
    """
    Convert audio to 16kHz mono WAV required by whisper.cpp.
    
    INPUT: Any audio format supported by ffmpeg
    OUTPUT: Path to converted WAV, or None on error
    """
    
    # Generate safe filename
    safe_name = f"convert_{timestamp}.wav"
    temp_wav = temp_dir / safe_name
    
    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        "-y",                    # Overwrite without asking
        "-v", "error",           # Quiet mode
        "-i", input_path,        # Input file
        "-ar", "16000",          # Sample rate: 16kHz (whisper requirement)
        "-ac", "1",              # Mono audio
        "-c:a", "pcm_s16le",     # Codec: signed 16-bit PCM
        temp_wav                 # Output file
    ]
    
    # Execute with process death signal
    TRY:
        process = Popen(cmd, 
                       stdout=PIPE, 
                       stderr=PIPE,
                       preexec_fn=self._set_pdeathsig)
        
        stdout, stderr = process.communicate()
        
        IF process.returncode != 0:
            logger.error(f"FFmpeg failed: {stderr}")
            RETURN None
        
        logger.info(f"Converted {input_path.name} to 16kHz WAV")
        RETURN temp_wav
    
    EXCEPT Exception as e:
        logger.error(f"FFmpeg error: {e}")
        RETURN None
```

### _get_audio_duration (Duration Extraction)
```
METHOD _get_audio_duration(input_path: Path) -> float:
    """
    Get audio duration in seconds using ffprobe.
    
    INPUT: Audio file path
    OUTPUT: Duration in seconds, or 0.0 on error
    """
    
    TRY:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        RETURN float(result.stdout.strip())
    
    EXCEPT:
        RETURN 0.0
```

---

## MAIN TRANSCRIPTION METHOD

### transcribe (Full Pipeline)
```
METHOD transcribe(audio_path: Path, use_gpu: bool = True) -> TranscriptionResult:
    """
    Transcribe audio file using whisper.cpp.
    
    ARGS:
        audio_path: Path to audio file (any format)
        use_gpu: Whether to use GPU acceleration
    
    RETURNS:
        TranscriptionResult with text, language, timing, and error info
    
    PIPELINE:
        1. Validate binary/model/audio existence
        2. Get audio duration (ffprobe)
        3. Convert to 16kHz WAV (ffmpeg)
        4. Run whisper.cpp transcription
        5. Parse JSON output
        6. Extract text and metadata
    """
    
    logger.info(f"Starting transcription: {audio_path.name}", {
        "use_gpu": use_gpu,
        "file_size_kb": audio_path.stat().st_size / 1024
    })
    
    # Step 1: Validate paths
    IF NOT self.binary_path.exists():
        RETURN TranscriptionResult(error=f"Binary not found: {self.binary_path}")
    
    IF NOT self.model_path.exists():
        RETURN TranscriptionResult(error=f"Model not found: {self.model_path}")
    
    IF NOT audio_path.exists():
        RETURN TranscriptionResult(error=f"Audio not found: {audio_path}")
    
    # Step 2: Get audio duration
    audio_duration = self._get_audio_duration(audio_path)
    
    # Step 3: Create temp directory
    WITH tempfile.TemporaryDirectory(prefix="whisper_txn_") AS temp_dir:
        
        # Step 4: Convert to 16kHz WAV
        converted_path = self._convert_to_wav16k(audio_path, temp_dir)
        IF NOT converted_path:
            RETURN TranscriptionResult(error="Audio conversion failed")
        
        TRY:
            # Step 5: Build whisper.cpp command
            output_prefix = temp_dir / "output"
            
            cmd = [
                self.binary_path,
                "-m", self.model_path,      # Model file
                "-f", converted_path,       # Input audio (converted WAV)
                "-l", "ru",                 # Language: Russian (forced)
                "-oj",                      # Output JSON format
                "-np",                      # No progress output
                "-of", output_prefix        # Output file prefix
            ]
            
            # Add GPU flag if disabled
            IF NOT use_gpu:
                cmd.append("-ng")  # Disable GPU
            # Note: GPU is default when compiled with CUDA
            
            start_time = time.time()
            
            # Step 6: Execute whisper.cpp
            process = Popen(cmd,
                           stdout=PIPE,
                           stderr=PIPE,
                           text=True,
                           preexec_fn=self._set_pdeathsig)
            
            TRY:
                stdout, stderr = process.communicate()
            EXCEPT:
                process.kill()
                process.wait()
                RAISE
            
            duration = time.time() - start_time
            
            IF process.returncode != 0:
                logger.error(f"Whisper failed: {stderr}")
                RETURN TranscriptionResult(
                    error=f"Whisper failed with code {process.returncode}",
                    duration_process_sec=duration
                )
            
            # Step 7: Read JSON output
            json_output_path = output_prefix.with_suffix(".json")
            
            IF NOT json_output_path.exists():
                RETURN TranscriptionResult(
                    error=f"JSON not generated: {json_output_path}",
                    duration_process_sec=duration
                )
            
            TRY:
                content = json_output_path.read_text(encoding="utf-8")
                data = json.loads(content)
            EXCEPT Exception as e:
                RETURN TranscriptionResult(
                    error=f"JSON parse failed: {e}",
                    duration_process_sec=duration
                )
            
            # Step 8: Extract text from segments
            full_text = ""
            
            IF "transcription" IN data:
                # whisper.cpp format: array of segments
                full_text = "".join([s.get("text", "") FOR s IN data["transcription"]])
            ELIF "text" IN data:
                # Alternative format: single text field
                full_text = data["text"]
            
            # Extract language
            language = data.get("language", "unknown")
            
            # Calculate speed factor
            speed_factor = audio_duration / duration IF duration > 0 ELSE 0
            
            logger.info("Transcription complete", {
                "duration_process_sec": round(duration, 2),
                "duration_audio_sec": round(audio_duration, 2),
                "speed_factor": round(speed_factor, 1),
                "text_length": len(full_text),
                "language": language
            })
            
            RETURN TranscriptionResult(
                text=full_text.strip(),
                language=language,
                duration_audio_sec=audio_duration,
                duration_process_sec=duration,
                raw_json=data
            )
        
        EXCEPT Exception as e:
            logger.error(f"Transcription error: {e}")
            RETURN TranscriptionResult(error=str(e))
```

---

## HEALTH CHECK

### check_health
```
METHOD check_health() -> Tuple[str, Dict]:
    """
    Check if whisper.cpp is ready for transcription.
    
    RETURNS:
        Tuple of (status, details)
        status: 'OK' | 'NO_BINARY' | 'NO_MODEL' | 'NO_FFMPEG'
    """
    
    # Check binary
    IF NOT self.binary_path.exists():
        RETURN ("NO_BINARY", {"message": f"Binary not found: {self.binary_path}"})
    
    # Check model
    IF NOT self.model_path.exists():
        RETURN ("NO_MODEL", {"message": f"Model not found: {self.model_path}"})
    
    # Check ffmpeg
    TRY:
        result = subprocess.run(["ffmpeg", "-version"], 
                               capture_output=True, 
                               timeout=5)
        IF result.returncode != 0:
            RETURN ("NO_FFMPEG", {"message": "ffmpeg not working"})
    EXCEPT Exception as e:
        RETURN ("NO_FFMPEG", {"message": f"ffmpeg not available: {e}"})
    
    RETURN ("OK", {
        "message": "Whisper ready",
        "binary": str(self.binary_path),
        "model": str(self.model_path)
    })
```

---

## SINGLETON AND CONVENIENCE

### Global Instance
```
# Default instance for convenience
whisper_service = VoiceWhisper()
```

### Convenience Functions
```
FUNCTION transcribe(audio_path: Path, use_gpu: bool = True) -> TranscriptionResult:
    """Convenience function to transcribe audio."""
    RETURN whisper_service.transcribe(audio_path, use_gpu)

FUNCTION check_whisper_health() -> Tuple:
    """Check if whisper.cpp is ready."""
    RETURN whisper_service.check_health()
```

---

## CLI INTERFACE

### Command-Line Usage
```
IF __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--file", "-f", help="Audio file to transcribe")
    parser.add_argument("--health", action="store_true", help="Health check")
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU")
    
    args = parser.parse_args()
    
    IF args.health:
        # Health check mode
        status, info = check_whisper_health()
        print(f"Status: {status}")
        print(json.dumps(info, indent=2))
    
    ELIF args.file:
        # Transcription mode
        audio_path = Path(args.file)
        result = transcribe(audio_path, use_gpu=NOT args.no_gpu)
        
        IF result.success:
            print(f"Transcription ({result.language})")
            print(result.text)
            print(f"Audio: {result.duration_audio_sec:.2f}s")
            print(f"Process: {result.duration_process_sec:.2f}s")
            print(f"Speed: {speed_factor:.1f}x real-time")
        ELSE:
            print(f"Error: {result.error}")
    
    ELSE:
        parser.print_help()
```

---

## KEY FEATURES

### Audio Format Support
```
Supported Input Formats (via ffmpeg):
- .ogg, .oga (Telegram voice messages)
- .mp3, .wav, .flac, .m4a
- Any format ffmpeg can decode

Output Format (whisper.cpp requirement):
- 16kHz mono WAV
- PCM signed 16-bit little-endian
```

### GPU Acceleration
```
Default: GPU enabled (CUDA)
- Requires whisper.cpp compiled with CUDA support
- Uses NVIDIA GPU for inference
- ~10-20x faster than CPU

Disable: --no-gpu or use_gpu=False
- Falls back to CPU inference
- Slower but works without GPU
```

### Process Management
```
Parent Death Signal (Linux):
- Uses prctl(PR_SET_PDEATHSIG, SIGTERM)
- Ensures child processes (ffmpeg, whisper) die with parent
- Prevents orphaned processes

Timeout Protection:
- ffprobe: 10s timeout
- No timeout for whisper (long audio files)
```

### Error Handling
```
Validation Errors:
- Binary not found
- Model not found
- Audio file not found

Conversion Errors:
- FFmpeg conversion failed
- Invalid audio format

Transcription Errors:
- Whisper process failed
- JSON output not generated
- JSON parse failed
```

---

## PERFORMANCE

### Typical Processing Times
```
Audio Duration: 10s
- Conversion (ffmpeg): ~0.5s
- Transcription (GPU): ~1-2s
- Total: ~2-3s
- Speed: 5x real-time

Audio Duration: 60s
- Conversion: ~1s
- Transcription (GPU): ~5-8s
- Total: ~6-9s
- Speed: 7-10x real-time
```

### Model Quality
```
Model: ggml-large-v3.bin
- Size: ~3GB
- Quality: Best available
- Languages: 99+ languages
- Russian: Excellent accuracy
```

---

## INTEGRATION WITH VOICEPAL

### Usage in voice_server.py
```
# Import
from voice_whisper import transcribe

# Transcribe uploaded audio
@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    audio_file = request.files['audio']
    temp_path = save_temp_file(audio_file)
    
    result = transcribe(temp_path, use_gpu=True)
    
    IF result.success:
        RETURN jsonify({
            "success": True,
            "text": result.text,
            "language": result.language,
            "duration": result.duration_audio_sec
        })
    ELSE:
        RETURN jsonify({
            "success": False,
            "error": result.error
        })
```

---

<!--/TAG:voicepal_whisper_pseudocode-->
