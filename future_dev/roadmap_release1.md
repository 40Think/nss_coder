# NSS Coder Roadmap — Release 1.0

> **Goal**: Transform a collection of AI-agent scripts into a full-fledged product accessible to any user without technical knowledge.

---

## 🏁 Starting State (v0.1 — Current)

### Documentation (Project Root)

| File | Purpose |
|------|---------|
| `README.MD` | Main README with project description |
| `GEMINI.MD` | Constitution for AI agents, working rules |
| `SYSTEM_PROMPT.md` | Compact system prompt (Quick Reference) |
| `AGENT_ONBOARDING.md` | Quick onboarding guide for AI agents |
| `requirements.txt` | Python dependencies |
| `start_voicepal.sh` | Shell script for VoicePal launch (requires venv) |

---

### Automation Scripts (20+ Tools)

#### Core Analysis Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `analyze_dependencies.py` | 5-layer dependency analysis via AST | ✅ Ready |
| `search_dependencies.py` | Dependency search and visualization | ✅ Ready |
| `assemble_context.py` | Automatic context assembly for AI | ✅ Ready |
| `semantic_search.py` | Semantic documentation search | ✅ Ready |
| `search_by_tag.py` | Semantic tag-based search | ✅ Ready |

#### Validation and Testing

| Script | Purpose | Status |
|--------|---------|--------|
| `validate_docs.py` | Documentation validation, drift detection | ✅ Ready |
| `validate_system.py` | Multi-level system validation | ✅ Ready |
| `test_system.py` | Tests with paranoia levels 1-5 | ✅ Ready |
| `tag_validator.py` | Semantic tag validation | ✅ Ready |

#### Indexing and Documentation

| Script | Purpose | Status |
|--------|---------|--------|
| `index_project.py` | Index and embedding construction | ✅ Ready |
| `chunk_documents.py` | Semantic document chunking | ✅ Ready |
| `summarize_docs.py` | AI documentation summarization | ✅ Ready |
| `generate_call_graph.py` | Call graph generation | ✅ Ready |
| `update_diagrams.py` | Automatic diagram updates | ✅ Ready |
| `ast_auto_tagger.py` | Automatic tag placement | ✅ Ready |

#### VoicePal — Voice System

| Script | Purpose | Status |
|--------|---------|--------|
| `voice_server.py` | Flask server with web interface | ✅ Ready |
| `voice_processor.py` | Voice processing via vLLM | ✅ Ready |
| `voice_whisper_fast.py` | faster-whisper ASR (82.7x real-time) | ✅ Ready |
| `voice_whisper_client.py` | Remote Whisper client | ✅ Ready |
| `nss_spec_ide.py` | 10-stage specification generator | ✅ Ready |

---

### Utils (Utilities)

| Module | Purpose | Status |
|--------|---------|--------|
| `docs_config.py` | Configuration loading from YAML | ✅ Ready |
| `docs_logger.py` | Paranoid logging system | ✅ Ready |
| `docs_llm_backend.py` | vLLM/OpenAI client | ✅ Ready |
| `docs_dual_memory.py` | Dual-index memory (descriptions/code) | ✅ Ready |
| `docs_deep_supervisor.py` | Vertical analysis (single file) | ✅ Ready |
| `docs_global_supervisor.py` | Horizontal analysis (entire system) | ✅ Ready |

---

### Documentation (Pseudocode and Visualizations)

For each main script there is:
- `*.pseudo.md` — Pseudocode with 80-90% comments
- `*.mmd` — Mermaid diagrams
- `*.png` — Architecture visualizations

**Total**: 103 files in `automation/`

---

## 🚀 Release 1.0 — "One-Click Launch"

### Goal

**Launch VoicePal with one click** for users who:
- Don't know what a terminal is
- Are afraid of GitHub
- Don't understand Python/venv
- Just want to download and run

---

### Success Criteria for Release 1.0 (codename Voicepal)

#### Option A: Windows EXE (Standalone)

| Criterion | Description |
|-----------|-------------|
| **Single file** | `VoicePal.exe` (or `VoicePal-Setup.exe`) |
| **No dependencies** | Python, CUDA, venv packaged inside |
| **Tray icon** | Minimalist interface |
| **Auto-launch browser** | Opens `localhost:5000` automatically |
| **GPU Detection** | Auto-detect NVIDIA/AMD/CPU mode |

**Technologies**: PyInstaller / Nuitka / cx_Freeze

#### Option B: Web Interface (Online/Local)

| Criterion | Description |
|-----------|-------------|
| **Hosted Demo** | Demo at `voicepal.example.com` |
| **Docker Compose** | `docker-compose up` for local launch |
| **One-liner install** | `curl -sSL install.sh \| bash` |
| **Web UI** | Full interface without terminal |
| **Cloud GPU** | Optional connection to cloud GPUs |

**Technologies**: Docker + nginx + Let's Encrypt

#### Option C: Hybrid (Recommended)

| Component | Description |
|-----------|-------------|
| **Windows Installer** | `.msi` with GUI installer |
| **macOS App** | `.dmg` file |
| **Linux AppImage** | Portable AppImage |
| **Web Demo** | For "try without installing" |

---

### Tasks for Release 1.0

#### Phase 1: Packaging (2-3 weeks)

- [ ] Research PyInstaller vs Nuitka for CUDA-dependent applications
- [ ] Create `build_exe.py` build script
- [ ] Test on clean Windows 10/11
- [ ] Solve size problem (faster-whisper + CUDA = ~2GB)
- [ ] Create Splash Screen and icons

#### Phase 2: Installer (1-2 weeks)

- [ ] Create NSIS/Inno Setup installer
- [ ] Add "Desktop Shortcut" option
- [ ] Add "Start Menu" entry
- [ ] Add Uninstaller
- [ ] Code Signing (optional)

#### Phase 3: Web Mode (1-2 weeks)

- [ ] Dockerfile for VoicePal
- [ ] docker-compose.yml with GPU support
- [ ] Nginx reverse proxy
- [ ] SSL certificates
- [ ] Demo deployment on VPS

#### Phase 4: Documentation for Non-Technical Users (1 week)

- [ ] Video tutorial "Installation in 2 minutes"
- [ ] FAQ: "What to do if it doesn't work"
- [ ] Screenshots of each step
- [ ] Troubleshooting guide

---

### Success Metrics

| Metric | Target Value |
|--------|--------------|
| **Time from download to first launch** | < 5 minutes |
| **Number of clicks for installation** | ≤ 5 |
| **Required technical knowledge** | Zero |
| **Works on Windows 10/11** | 100% |
| **Works without GPU** | Yes (CPU fallback) |

---

## 📋 Future Releases (Ideas)

### Release 2.0 — "AI Fleet Integration"
- Connection to distributed AI cluster
- Fallback between local and cloud GPU
- Multi-user support

### Release 3.0 — "BrainStep Integration"
- EEG control via Muse headband
- "Thought-to-Code" prototype
- Neuro-feedback for focus

### Release 4.0 — "Enterprise"
- Team collaboration
- On-premise deployment guide
- SSO/LDAP integration

---

**Created**: 2026-01-08  
**Status**: Planning  
**Owner**: AI Agent (supervised by Human)
