#!/usr/bin/env python3
"""
NSS-Spec IDE - Browser-based Specification Generation IDE

<!--TAG:tool_nss_spec_ide-->

PURPOSE: Spec-First IDE for generating specifications, documentation, and tickets.
         Uses 6-stage pipeline with 24 buttons. Кодинговые агенты исполняют спецификации.

DOCUMENTATION:
    Spec: docs/specs/nss_spec_ide_vision.md
    Analysis: docs/automation/nss_spec_pipeline_analysis.md
    Plan: implementation_plan.md

DEPENDENCIES (Quick Reference):
    - Flask: Web framework
    - voice_whisper_fast.py: FasterWhisper integration (MIGRATED 2025-12-16, 82.7x real-time)
    - voice_processor.py: vLLM backend
    - semantic_search.py, search_by_tag.py: NSS-DOCS memory

TAGS: <!--TAG:nss_spec_ide--> <!--TAG:spec_generation--> <!--TAG:voice_input-->

<!--/TAG:tool_nss_spec_ide-->
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

# ============================================================================
# CONFIGURATION
# ============================================================================

# Add parent directories to path for imports
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent.parent))

# Default directories
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nss_spec_ide")

# ============================================================================
# FLASK APP
# ============================================================================

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

# ============================================================================
# 10 STAGES DEFINITION (Complete Architecture from Pipeline Analysis)
# ============================================================================

STAGES = {
    # Stage -1: Deep Context Understanding
    "-1": {
        "name": "🔮 Deep Context",
        "description": "Глубокое понимание контекста: проблема, картина, экосистема",
        "color": "#f97316",  # orange
        "buttons": [
            {"id": "primary_problem", "label": "🎯 Primary Problem", "action": "analyze_primary_problem"},
            {"id": "global_picture", "label": "🌐 Global Picture", "action": "create_global_picture"},
            {"id": "ecosystem_map", "label": "🔗 Ecosystem Map", "action": "map_ecosystem"},
            {"id": "failure_scenarios", "label": "💀 Failure Scenarios", "action": "analyze_failures"},
            {"id": "summary_m1", "label": "📋 Конспект", "action": "summarize"}
        ]
    },
    
    # Stage -0.5: True Needs Discovery
    "-0.5": {
        "name": "❓ True Needs",
        "description": "Выявление истинных потребностей: 5 Whys, JTBD, User Stories",
        "color": "#eab308",  # yellow
        "buttons": [
            {"id": "five_whys", "label": "❓ 5 Whys", "action": "analyze_5_whys"},
            {"id": "jtbd", "label": "💼 JTBD", "action": "jobs_to_be_done"},
            {"id": "user_story_map", "label": "📊 User Story Map", "action": "create_user_story_map"},
            {"id": "process_mining", "label": "⛏️ Process Mining", "action": "process_mining"},
            {"id": "summary_m05", "label": "📋 Конспект", "action": "summarize"}
        ]
    },
    
    # Stage 0: Philosophy & Alternatives
    "0": {
        "name": "🧠 Philosophy",
        "description": "Философский анализ и альтернативы: Deep Research, Build vs Buy",
        "color": "#84cc16",  # lime
        "buttons": [
            {"id": "voice_input", "label": "🎤 Voice", "action": "capture_voice"},
            {"id": "text_import", "label": "📝 Text Input", "action": "import_text"},
            {"id": "deep_research", "label": "🔍 Deep Research", "action": "deep_research", "placeholder": True},
            {"id": "alternatives", "label": "🔀 Alternatives", "action": "analyze_alternatives"},
            {"id": "build_vs_buy", "label": "🏗️ Build vs Buy", "action": "build_vs_buy"},
            {"id": "summary_0", "label": "📋 Конспект", "action": "summarize"}
        ]
    },
    
    # Stage 1: Architecture Vision
    "1": {
        "name": "🏛️ Architecture",
        "description": "Архитектурное видение: компоненты, паттерны, структуры данных",
        "color": "#22c55e",  # green
        "buttons": [
            {"id": "components", "label": "🧱 Components", "action": "design_components"},
            {"id": "design_patterns", "label": "🎨 Patterns", "action": "apply_patterns"},
            {"id": "data_structures", "label": "📊 Data Structures", "action": "design_data_structures"},
            {"id": "hardware_aware", "label": "⚡ Hardware-Aware", "action": "hardware_optimization"},
            {"id": "diagrams", "label": "📐 Diagrams", "action": "generate_diagrams"},
            {"id": "summary_1", "label": "📋 Конспект", "action": "summarize"}
        ]
    },
    
    # Stage 2: UI/CLI Design
    "2": {
        "name": "🖥️ UI/CLI Design",
        "description": "Дизайн интерфейса: GUI wireframes, CLI commands, Error UX",
        "color": "#14b8a6",  # teal
        "buttons": [
            {"id": "interface_type", "label": "🔧 Interface Type", "action": "define_interface_type"},
            {"id": "gui_wireframes", "label": "🖼️ GUI Wireframes", "action": "create_wireframes"},
            {"id": "cli_commands", "label": "💻 CLI Commands", "action": "design_cli"},
            {"id": "error_handling", "label": "⚠️ Error UX", "action": "design_error_ux"},
            {"id": "summary_2", "label": "📋 Конспект", "action": "summarize"}
        ]
    },
    
    # Stage 3: Technical Specification
    "3": {
        "name": "📋 Tech Spec",
        "description": "Техническая спецификация: FR, NFR, API, Edge Cases",
        "color": "#3b82f6",  # blue
        "buttons": [
            {"id": "functional_req", "label": "📝 Functional Req", "action": "write_functional_req"},
            {"id": "nonfunctional_req", "label": "⚙️ Non-Functional", "action": "write_nonfunctional_req"},
            {"id": "api_spec", "label": "🔌 API Spec", "action": "write_api_spec"},
            {"id": "edge_cases", "label": "🔪 Edge Cases", "action": "analyze_edge_cases"},
            {"id": "summary_3", "label": "📋 Конспект", "action": "summarize"}
        ]
    },
    
    # Stage 4: Holographic Tickets
    "4": {
        "name": "🎫 Holographic Tickets",
        "description": "Голографические тикеты: ~700 токенов, семантические теги",
        "color": "#8b5cf6",  # violet
        "buttons": [
            {"id": "decompose_700", "label": "✂️ Decompose (~700)", "action": "decompose_cognitive_units"},
            {"id": "holographic", "label": "🔮 Holographic", "action": "create_holographic_tickets"},
            {"id": "semantic_tags", "label": "🏷️ Semantic Tags", "action": "add_semantic_tags"},
            {"id": "ticket_index", "label": "📇 Index", "action": "create_ticket_index"},
            {"id": "summary_4", "label": "📋 Конспект", "action": "summarize"}
        ]
    },
    
    # Stage 5: Pseudocode & Semantic Glue
    "5": {
        "name": "💻 Pseudocode",
        "description": "Псевдокод и семантический клей: 80-90% комментариев",
        "color": "#a855f7",  # purple
        "buttons": [
            {"id": "pseudocode", "label": "📜 Pseudocode", "action": "write_pseudocode"},
            {"id": "semantic_glue", "label": "🍯 Semantic Glue 90%", "action": "add_semantic_glue"},
            {"id": "ascii_diagrams", "label": "📊 ASCII Diagrams", "action": "create_ascii_diagrams"},
            {"id": "complexity", "label": "📈 Complexity", "action": "analyze_complexity"},
            {"id": "summary_5", "label": "📋 Конспект", "action": "summarize"}
        ]
    },
    
    # Stage 6: Code Specification
    "6": {
        "name": "📦 Code Spec",
        "description": "Спецификация кода: сигнатуры, структура файлов, naming",
        "color": "#ec4899",  # pink
        "buttons": [
            {"id": "function_sigs", "label": "📝 Function Sigs", "action": "define_function_signatures"},
            {"id": "file_structure", "label": "📁 File Structure", "action": "design_file_structure"},
            {"id": "naming", "label": "🏷️ Naming", "action": "define_naming_conventions"},
            {"id": "assembly_markers", "label": "🔧 Assembly Markers", "action": "add_assembly_markers"},
            {"id": "summary_6", "label": "📋 Конспект", "action": "summarize"}
        ]
    },
    
    # Stage 7: Verification Plan
    "7": {
        "name": "✅ Verification",
        "description": "План верификации: Unit, Integration, Performance, Adversarial",
        "color": "#f43f5e",  # rose
        "buttons": [
            {"id": "unit_tests", "label": "🧪 Unit Tests", "action": "spec_unit_tests"},
            {"id": "integration_tests", "label": "🔗 Integration Tests", "action": "spec_integration_tests"},
            {"id": "performance_tests", "label": "⚡ Performance", "action": "spec_performance_tests"},
            {"id": "adversarial", "label": "👹 Adversarial AI", "action": "spec_adversarial_tests"},
            {"id": "manual_checklist", "label": "📝 Manual Checklist", "action": "create_manual_checklist"},
            {"id": "summary_7", "label": "📋 Конспект", "action": "summarize"}
        ]
    },
    
    # Stage 8: Handoff to Coding Agent
    "8": {
        "name": "🚀 Handoff",
        "description": "Передача агенту: README, проверка полноты, промпты, пакет",
        "color": "#ef4444",  # red
        "buttons": [
            {"id": "readme", "label": "📖 README", "action": "generate_readme"},
            {"id": "completeness", "label": "✅ Completeness", "action": "check_completeness"},
            {"id": "agent_prompts", "label": "🤖 Agent Prompts", "action": "generate_agent_prompts"},
            {"id": "split_agents", "label": "👥 Split (10)", "action": "split_to_agents"},
            {"id": "package", "label": "📦 Package", "action": "create_handoff_package"},
            {"id": "summary_8", "label": "📋 Конспект", "action": "summarize"}
        ]
    }
}

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class Session:
    """Manages a single IDE session (folder-based)."""
    
    def __init__(self, session_id: str = None):
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = session_id
        self.path = SESSIONS_DIR / session_id
        self._init_structure()
    
    def _init_structure(self):
        """Create session folder structure."""
        self.path.mkdir(exist_ok=True)
        (self.path / "audio").mkdir(exist_ok=True)
        (self.path / "transcripts").mkdir(exist_ok=True)
        (self.path / "memory").mkdir(exist_ok=True)
        for stage in range(6):
            (self.path / f"stage{stage}").mkdir(exist_ok=True)
        
        # Init state file
        state_file = self.path / "session_state.json"
        if not state_file.exists():
            self._save_state({
                "session_id": self.session_id,
                "created": datetime.now().isoformat(),
                "current_stage": 0,
                "button_states": {},  # Which buttons have been used
                "context_selections": {}  # Per-button memory selections
            })
    
    def _save_state(self, state: dict):
        with open(self.path / "session_state.json", "w") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def load_state(self) -> dict:
        with open(self.path / "session_state.json") as f:
            return json.load(f)
    
    def update_state(self, updates: dict):
        state = self.load_state()
        state.update(updates)
        state["updated"] = datetime.now().isoformat()
        self._save_state(state)
    
    def save_document(self, stage: int, filename: str, content: str):
        """Save a document to stage folder."""
        filepath = self.path / f"stage{stage}" / filename
        filepath.write_text(content, encoding="utf-8")
        return str(filepath)
    
    def list_documents(self, stage: int) -> list:
        """List documents in a stage folder."""
        stage_path = self.path / f"stage{stage}"
        return [f.name for f in stage_path.glob("*.md")]

# Current session (global for simplicity)
current_session: Session = None

# ============================================================================
# HTML TEMPLATE
# ============================================================================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-tertiary: #1a1a25;
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --accent-purple: #8b5cf6;
            --accent-blue: #3b82f6;
            --accent-green: #22c55e;
            --accent-orange: #f59e0b;
            --border-color: #2a2a3a;
            --glass-bg: rgba(30, 30, 45, 0.8);
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            height: 100vh;
            overflow: hidden;
        }
        
        /* Layout: 4 panels - optimized for 3440x1440 ultrawide */
        .container {
            display: grid;
            grid-template-columns: 220px 1fr;
            grid-template-rows: auto 1fr;
            height: 100vh;
            gap: 1px;
            background: var(--border-color);
        }
        
        /* Header spans full width */
        .header {
            grid-column: 1 / -1;
            background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
            padding: 0.75rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-color);
        }
        
        .header h1 {
            font-size: 1.3rem;
            background: linear-gradient(90deg, var(--accent-purple), var(--accent-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .session-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .session-badge {
            background: var(--glass-bg);
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        
        /* Revolutionary Concepts Toolbar */
        .concepts-toolbar {
            display: flex;
            gap: 0.4rem;
            align-items: center;
        }
        
        .concept-btn {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(59, 130, 246, 0.2));
            border: 1px solid rgba(139, 92, 246, 0.4);
            border-radius: 6px;
            padding: 0.35rem 0.6rem;
            color: var(--accent-purple);
            cursor: pointer;
            font-size: 0.75rem;
            transition: all 0.2s;
        }
        
        .concept-btn:hover {
            background: var(--accent-purple);
            color: white;
            transform: scale(1.05);
        }
        
        /* Left panel: File browser - narrower for ultrawide */
        .left-panel {
            background: var(--bg-secondary);
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        
        .panel-header {
            padding: 0.75rem;
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-color);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .file-tree {
            padding: 0.5rem;
            flex: 1;
            overflow-y: auto;
        }
        
        .file-item {
            padding: 0.4rem 0.6rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        
        .file-item:hover {
            background: var(--bg-tertiary);
        }
        
        .file-item.folder { color: var(--accent-blue); }
        .file-item.file { color: var(--text-primary); padding-left: 1.2rem; }
        
        /* Main panel */
        .main-panel {
            background: var(--bg-primary);
            display: grid;
            grid-template-rows: auto 1fr auto;
            gap: 1px;
            overflow: hidden;
        }
        
        /* ============= STAGES SECTION - ADAPTIVE GRID ============= */
        .stages-section {
            background: var(--bg-secondary);
            padding: 0.75rem;
            overflow-y: auto;
            max-height: 40vh;
        }
        
        /* Stages container - horizontal flex grid */
        .stages-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        
        /* Each stage - flex item with min/max width */
        .stage-row {
            flex: 1 1 auto;
            min-width: 280px;
            max-width: 550px;
            padding: 0.6rem;
            background: var(--glass-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            transition: box-shadow 0.2s;
        }
        
        .stage-row:hover {
            box-shadow: 0 0 15px rgba(139, 92, 246, 0.15);
        }
        
        .stage-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.4rem;
        }
        
        .stage-name {
            font-weight: 600;
            color: var(--accent-purple);
            font-size: 0.85rem;
        }
        
        .stage-number {
            background: var(--accent-purple);
            color: white;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
            font-weight: bold;
        }
        
        /* Stage buttons - flex wrap inside each stage */
        .stage-buttons {
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
        }
        
        .stage-btn {
            display: inline-flex;
            align-items: center;
            gap: 0.2rem;
            padding: 0.4rem 0.6rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 5px;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.15s;
            white-space: nowrap;
        }
        
        .stage-btn:hover {
            background: var(--accent-purple);
            border-color: var(--accent-purple);
            transform: translateY(-1px);
        }
        
        .stage-btn.active {
            background: var(--accent-green);
            border-color: var(--accent-green);
        }
        
        .stage-btn.placeholder { opacity: 0.5; }
        
        .stage-btn input[type="checkbox"] {
            width: 12px;
            height: 12px;
            accent-color: var(--accent-green);
        }
        
        .brain-btn {
            background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
            border: none;
            padding: 0.4rem;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: transform 0.15s;
        }
        
        .brain-btn:hover { transform: scale(1.1); }
        
        /* ============= WORKSPACE SECTION ============= */
        .workspace-section {
            background: var(--bg-primary);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .workspace-header {
            padding: 0.5rem 1rem;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .workspace-tabs {
            display: flex;
            gap: 0.5rem;
        }
        
        .workspace-tab {
            padding: 0.4rem 0.8rem;
            background: var(--bg-tertiary);
            border-radius: 5px 5px 0 0;
            cursor: pointer;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        
        .workspace-tab.active {
            background: var(--bg-primary);
            color: var(--text-primary);
        }
        
        .editor-container {
            flex: 1;
            padding: 1rem;
            overflow-y: auto;
        }
        
        .editor {
            width: 100%;
            height: 100%;
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 0.9rem;
            line-height: 1.5;
            resize: none;
            outline: none;
        }
        
        /* ============= MEMORY SECTION ============= */
        .memory-section {
            background: var(--bg-secondary);
            padding: 0.75rem;
            border-top: 1px solid var(--border-color);
            max-height: 30vh;
            overflow-y: auto;
        }
        
        .memory-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }
        
        .memory-title {
            font-weight: 600;
            color: var(--text-secondary);
            font-size: 0.8rem;
        }
        
        .memory-controls {
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
        }
        
        .memory-btn {
            padding: 0.35rem 0.6rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 5px;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 0.75rem;
        }
        
        .memory-btn:hover { background: var(--accent-blue); }
        
        .memory-btn.occam {
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }
        
        /* Memory list - horizontal flex for ultrawide */
        .memory-list {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
        }
        
        .memory-item {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 0.6rem;
            background: var(--bg-tertiary);
            border-radius: 5px;
            border-left: 3px solid var(--accent-green);
            min-width: 200px;
            max-width: 400px;
            flex: 1 1 auto;
        }
        
        .memory-badge {
            font-size: 0.85rem;
            min-width: 20px;
            text-align: center;
        }
        
        .memory-badge.total-recall { color: #f59e0b; }
        .memory-badge.memory-lite { color: #3b82f6; }
        .memory-badge.embeddings { color: #8b5cf6; }
        .memory-badge.nss-docs { color: #ef4444; }
        
        .memory-path {
            flex: 1;
            font-size: 0.8rem;
            color: var(--text-secondary);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .memory-score {
            font-size: 0.75rem;
            color: var(--accent-green);
        }
        
        /* Voice indicator */
        .voice-recording {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 0.8rem;
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid #ef4444;
            border-radius: 6px;
            color: #ef4444;
            font-size: 0.85rem;
        }
        
        .voice-recording .dot {
            width: 6px;
            height: 6px;
            background: #ef4444;
            border-radius: 50%;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        
        /* Loading overlay */
        .loading {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .loading.active { display: flex; }
        
        .loading-content { text-align: center; }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid var(--border-color);
            border-top-color: var(--accent-purple);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 0.75rem;
        }
        
        @keyframes spin { to { transform: rotate(360deg); } }
        
        /* ============= RESPONSIVE BREAKPOINTS ============= */
        
        /* Large ultrawide (3440px+) - 6 stages in one row */
        @media (min-width: 2560px) {
            .stage-row {
                flex: 1 1 calc(16.66% - 0.5rem);
                min-width: 200px;
                max-width: none;
            }
        }
        
        /* Medium ultrawide (2560-3440px) - 3 stages per row */
        @media (min-width: 1920px) and (max-width: 2559px) {
            .stage-row {
                flex: 1 1 calc(33.33% - 0.5rem);
                min-width: 280px;
            }
        }
        
        /* Standard (1920px) - 2 stages per row */
        @media (max-width: 1919px) {
            .stage-row {
                flex: 1 1 calc(50% - 0.5rem);
                min-width: 280px;
            }
        }
        
        /* Smaller screens - 1 stage per row */
        @media (max-width: 1200px) {
            .stage-row {
                flex: 1 1 100%;
                max-width: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>🧠 NSS-Spec IDE</h1>
            <!-- Revolutionary Concepts Toolbar -->
            <div class="concepts-toolbar">
                <button class="concept-btn" title="Cognitive Units: ~700 tokens per function">🧩 700t</button>
                <button class="concept-btn" title="Holographic Principle: 10% → 80% recovery">🔮 Holo</button>
                <button class="concept-btn" title="Token Gravity: precise terms attract quality">🌌 Gravity</button>
                <button class="concept-btn" title="Semantic Glue: 80-90% comments">🍯 Glue</button>
                <button class="concept-btn" title="N2S Overlay: neuro-symbolic network">🧬 N2S</button>
            </div>
            <div class="session-info">
                <span class="session-badge" id="sessionBadge">Session: --</span>
                <button class="memory-btn" onclick="newSession()">➕ New</button>
                <button class="memory-btn" onclick="loadSessions()">📂 Load</button>
            </div>
        </header>
        
        <!-- Left Panel: File Browser -->
        <aside class="left-panel">
            <div class="panel-header">📁 Session Files</div>
            <div class="file-tree" id="fileTree">
                <div class="file-item folder">📂 audio/</div>
                <div class="file-item folder">📂 transcripts/</div>
                <div class="file-item folder" style="color: #f97316;">📂 stage-1/ (Deep Context)</div>
                <div class="file-item folder" style="color: #eab308;">📂 stage-0.5/ (True Needs)</div>
                <div class="file-item folder" style="color: #84cc16;">📂 stage0/ (Philosophy)</div>
                <div class="file-item folder" style="color: #22c55e;">📂 stage1/ (Architecture)</div>
                <div class="file-item folder" style="color: #14b8a6;">📂 stage2/ (UI/CLI)</div>
                <div class="file-item folder" style="color: #3b82f6;">📂 stage3/ (Tech Spec)</div>
                <div class="file-item folder" style="color: #8b5cf6;">📂 stage4/ (Tickets)</div>
                <div class="file-item folder" style="color: #a855f7;">📂 stage5/ (Pseudocode)</div>
                <div class="file-item folder" style="color: #ec4899;">📂 stage6/ (Code Spec)</div>
                <div class="file-item folder" style="color: #f43f5e;">📂 stage7/ (Verification)</div>
                <div class="file-item folder" style="color: #ef4444;">📂 stage8/ (Handoff)</div>
                <div class="file-item folder">📂 memory/</div>
            </div>
        </aside>
        
        <!-- Main Panel -->
        <main class="main-panel">
            <!-- Stages Section -->
            <section class="stages-section" id="stagesSection">
                <!-- Will be populated by JS -->
            </section>
            
            <!-- Workspace Section -->
            <section class="workspace-section">
                <div class="workspace-header">
                    <div class="workspace-tabs">
                        <span class="workspace-tab active">📝 Editor</span>
                    </div>
                    <div class="voice-recording" id="voiceIndicator" style="display: none;">
                        <span class="dot"></span>
                        <span id="voiceTime">00:00</span>
                    </div>
                </div>
                <div class="editor-container">
                    <textarea class="editor" id="editor" placeholder="Текст появится здесь...

🎤 Нажмите Voice для голосового ввода
📝 Или введите текст вручную"></textarea>
                </div>
            </section>
            
            <!-- Memory Section -->
            <section class="memory-section">
                <div class="memory-header">
                    <span class="memory-title">🔗 Memory (0 files)</span>
                    <div class="memory-controls">
                        <button class="memory-btn" onclick="searchTotalRecall()">🧠 TR</button>
                        <button class="memory-btn" onclick="searchMemoryLite()">⚡ Lite</button>
                        <button class="memory-btn" onclick="searchEmbeddings()">🗄️ Emb</button>
                        <button class="memory-btn" onclick="searchNssDocs()">S NSS</button>
                        <button class="memory-btn occam" onclick="occamRazor()">🔪 Оккам</button>
                    </div>
                </div>
                <div class="memory-list" id="memoryList">
                    <!-- Memory items will appear here -->
                </div>
            </section>
        </main>
    </div>
    
    <!-- Loading Overlay -->
    <div class="loading" id="loading">
        <div class="loading-content">
            <div class="spinner"></div>
            <div id="loadingText">Загрузка...</div>
        </div>
    </div>
    
    <script>
        // ====================================================================
        // GLOBAL STATE
        // ====================================================================
        let currentSession = null;
        let stages = {};
        let memoryData = [];
        let isRecording = false;
        let mediaRecorder = null;
        
        // ====================================================================
        // INITIALIZATION
        // ====================================================================
        document.addEventListener('DOMContentLoaded', async () => {
            await loadStages();
            await initSession();
        });
        
        async function loadStages() {
            // Fetch stages definition from server
            const response = await fetch('/api/stages');
            stages = await response.json();
            renderStages();
        }
        
        async function initSession() {
            const response = await fetch('/api/session/current');
            const data = await response.json();
            currentSession = data.session_id;
            document.getElementById('sessionBadge').textContent = `Session: ${currentSession}`;
        }
        
        // ====================================================================
        // STAGES RENDERING
        // ====================================================================
        function renderStages() {
            const container = document.getElementById('stagesSection');
            // Sort stages by numeric value (handle -1, -0.5, 0, 1, ...)
            const sortedStages = Object.entries(stages).sort((a, b) => parseFloat(a[0]) - parseFloat(b[0]));
            
            container.innerHTML = `<div class="stages-grid">` + sortedStages.map(([num, stage]) => `
                <div class="stage-row" data-stage="${num}" style="border-left: 4px solid ${stage.color || '#8b5cf6'};">
                    <div class="stage-header">
                        <span class="stage-name" style="color: ${stage.color || '#8b5cf6'};">${stage.name}</span>
                        <span class="stage-number" style="background: ${stage.color || '#8b5cf6'};">${num}</span>
                    </div>
                    <div class="stage-buttons">
                        ${stage.buttons.map(btn => `
                            <button class="stage-btn ${btn.placeholder ? 'placeholder' : ''}" 
                                    data-button="${btn.id}" 
                                    data-action="${btn.action}"
                                    onclick="executeButton('${num}', '${btn.id}', '${btn.action}')">
                                <input type="checkbox" onclick="event.stopPropagation()" title="Include in context">
                                ${btn.label}
                            </button>
                        `).join('')}
                        <button class="brain-btn" onclick="smartContext('${num}')" title="🧠 Auto-select context">
                            🧠
                        </button>
                    </div>
                </div>
            `).join('') + `</div>`;
        }
        
        // ====================================================================
        // BUTTON ACTIONS
        // ====================================================================
        async function executeButton(stage, buttonId, action) {
            showLoading(`Executing: ${buttonId}...`);
            
            try {
                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        stage: stage,
                        button_id: buttonId,
                        action: action,
                        context: document.getElementById('editor').value,
                        memory_selection: getSelectedMemory()
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('editor').value = data.result;
                    // Mark button as used
                    const btn = document.querySelector(`[data-button="${buttonId}"]`);
                    if (btn) btn.classList.add('active');
                }
            } catch (err) {
                console.error('Execute error:', err);
                alert('Error: ' + err.message);
            }
            
            hideLoading();
        }
        
        // ====================================================================
        // MEMORY FUNCTIONS
        // ====================================================================
        async function searchTotalRecall() {
            const query = document.getElementById('editor').value;
            if (!query.trim()) {
                alert('Enter text first');
                return;
            }
            
            showLoading('🧠 Total Recall: Searching all files...');
            
            try {
                const response = await fetch('/api/memory/total_recall', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                
                const data = await response.json();
                if (data.success) {
                    addMemoryResults(data.results, 'total_recall');
                }
            } catch (err) {
                console.error('Total Recall error:', err);
            }
            
            hideLoading();
        }
        
        async function searchMemoryLite() {
            showLoading('⚡ Memory Lite...');
            // TODO: Implement
            hideLoading();
        }
        
        async function searchEmbeddings() {
            showLoading('🗄️ Embeddings...');
            // TODO: Implement
            hideLoading();
        }
        
        async function searchNssDocs() {
            showLoading('S NSS-DOCS...');
            // TODO: Implement
            hideLoading();
        }
        
        function occamRazor() {
            // Remove low-priority selections based on priority:
            // Total Recall > Memory Lite > Embeddings > NSS-DOCS
            const checkboxes = document.querySelectorAll('.memory-item input[type="checkbox"]:checked');
            const priorities = { 'total_recall': 4, 'memory_lite': 3, 'embeddings': 2, 'nss_docs': 1 };
            
            // Sort by priority, keep top 20
            const items = Array.from(checkboxes).map(cb => ({
                checkbox: cb,
                source: cb.closest('.memory-item').dataset.source,
                priority: priorities[cb.closest('.memory-item').dataset.source] || 0
            })).sort((a, b) => b.priority - a.priority);
            
            items.slice(20).forEach(item => item.checkbox.checked = false);
            updateMemoryCount();
        }
        
        function addMemoryResults(results, source) {
            const container = document.getElementById('memoryList');
            const badges = {
                total_recall: { icon: '🧠', class: 'total-recall' },
                memory_lite: { icon: '⚡', class: 'memory-lite' },
                embeddings: { icon: '🗄️', class: 'embeddings' },
                nss_docs: { icon: 'S', class: 'nss-docs' }
            };
            
            const badge = badges[source] || { icon: '?', class: '' };
            
            results.forEach(r => {
                const item = document.createElement('div');
                item.className = 'memory-item';
                item.dataset.source = source;
                item.innerHTML = `
                    <input type="checkbox" checked>
                    <span class="memory-badge ${badge.class}">${badge.icon}</span>
                    <span class="memory-path">${r.file_path}</span>
                    <span class="memory-score">${Math.round((r.score || 0) * 100)}%</span>
                `;
                container.appendChild(item);
            });
            
            updateMemoryCount();
        }
        
        function getSelectedMemory() {
            return Array.from(document.querySelectorAll('.memory-item input:checked'))
                .map(cb => cb.closest('.memory-item').querySelector('.memory-path').textContent);
        }
        
        function updateMemoryCount() {
            const count = document.querySelectorAll('.memory-item input:checked').length;
            document.querySelector('.memory-title').textContent = `🔗 Memory (${count} files)`;
        }
        
        function smartContext(stage) {
            // TODO: 3-layer intelligent context selection
            alert('🧠 Smart context selection not yet implemented');
        }
        
        // ====================================================================
        // SESSION MANAGEMENT
        // ====================================================================
        async function newSession() {
            showLoading('Creating new session...');
            const response = await fetch('/api/session/new', { method: 'POST' });
            const data = await response.json();
            currentSession = data.session_id;
            document.getElementById('sessionBadge').textContent = `Session: ${currentSession}`;
            document.getElementById('editor').value = '';
            document.getElementById('memoryList').innerHTML = '';
            hideLoading();
        }
        
        function loadSessions() {
            // TODO: Show session picker
            alert('Session picker not yet implemented');
        }
        
        // ====================================================================
        // HELPERS
        // ====================================================================
        function showLoading(text) {
            document.getElementById('loadingText').textContent = text;
            document.getElementById('loading').classList.add('active');
        }
        
        function hideLoading() {
            document.getElementById('loading').classList.remove('active');
        }
    </script>
</body>
</html>
'''

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve main IDE interface."""
    return HTML_TEMPLATE

@app.route('/api/stages')
def get_stages():
    """Return stages definition."""
    return jsonify(STAGES)

@app.route('/api/session/current')
def get_current_session():
    """Get or create current session."""
    global current_session
    if current_session is None:
        current_session = Session()
    return jsonify({
        "session_id": current_session.session_id,
        "state": current_session.load_state()
    })

@app.route('/api/session/new', methods=['POST'])
def new_session():
    """Create a new session."""
    global current_session
    current_session = Session()
    logger.info(f"New session created: {current_session.session_id}")
    return jsonify({
        "success": True,
        "session_id": current_session.session_id
    })

@app.route('/api/execute', methods=['POST'])
def execute_action():
    """Execute a button action."""
    global current_session
    data = request.get_json()
    
    stage = data.get('stage', 0)
    button_id = data.get('button_id', '')
    action = data.get('action', '')
    context = data.get('context', '')
    memory_selection = data.get('memory_selection', [])
    
    logger.info(f"Execute: stage={stage}, button={button_id}, action={action}")
    
    # Placeholder response for now
    result = f"""# Generated by {button_id}

**Stage**: {stage}
**Action**: {action}
**Context length**: {len(context)} chars
**Memory files**: {len(memory_selection)}

---

TODO: Implement actual {action} logic using vLLM.

## Input Context
{context[:500]}{'...' if len(context) > 500 else ''}
"""
    
    # Save to session
    if current_session:
        filename = f"{button_id}_{int(time.time())}.md"
        current_session.save_document(stage, filename, result)
    
    return jsonify({
        "success": True,
        "result": result
    })

@app.route('/api/memory/total_recall', methods=['POST'])
def total_recall_search():
    """Total Recall search (placeholder)."""
    data = request.get_json()
    query = data.get('query', '')
    
    logger.info(f"Total Recall search: {query[:50]}...")
    
    # Placeholder - will integrate with voice_whisper_fast.py (faster-whisper, 82.7x real-time)
    return jsonify({
        "success": True,
        "results": [
            {"file_path": "docs/automation/voice_whisper_fast.py", "score": 0.95},
            {"file_path": "docs/automation/voice_server.py", "score": 0.85},
            {"file_path": "docs/automation/voice_processor.py", "score": 0.72}
        ]
    })

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='NSS-Spec IDE Server')
    parser.add_argument('--port', type=int, default=5002, help='Port to run on')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    global current_session
    current_session = Session()
    
    logger.info(f"Starting NSS-Spec IDE on http://{args.host}:{args.port}")
    logger.info(f"Session: {current_session.session_id}")
    
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()
