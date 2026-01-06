#!/usr/bin/env python3
"""
Diagram Updater - Automatically update diagrams when code changes

<!--TAG:tool_update_diagrams-->

PURPOSE:
    Automatically regenerate diagrams when code changes.
    Integrates with Git hooks and CI/CD pipelines.
    Supports architecture, dependency, and call graph diagrams.
    Features: Mermaid validation, file watching, parallel processing.

DOCUMENTATION:
    Spec: docs/specs/Automation_Tools_Spec.md
    Wiki: docs/wiki/09_Documentation_System.md
    Pseudocode: docs/automation/update_diagrams.pseudo.md

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger (logging)
        - watchdog (optional, for watch mode)
    Config:
        - docs/diagrams/diagram_specs.json
    Data:
        - Input: Source files matching patterns in specs
        - Output: docs/diagrams/
    External:
        - mermaid-cli (optional, for validation)

RECENT CHANGES:
    2025-12-11: Added Mermaid validation, watch mode, parallel processing
    2025-12-12: Updated header for GEMINI.MD compliance

TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:documentation--> <!--TAG:automation--> <!--TAG:diagrams--> <!--TAG:maintenance-->

<!--/TAG:tool_update_diagrams-->
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Set, Optional
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add project root to path
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.docs_logger import DocsLogger

# Optional watchdog import for watch mode
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object

logger = DocsLogger("update_diagrams")


@dataclass
class DiagramSpec:
    """Specification for a diagram."""
    name: str
    type: str  # 'architecture', 'dependencies', 'call_graph', 'data_flow'
    source_files: List[str]  # Files that affect this diagram
    output_path: str
    generator_command: str
    last_updated: str = None


class DiagramFileHandler(FileSystemEventHandler):
    """Handle file changes and update diagrams automatically."""
    
    def __init__(self, updater: 'DiagramUpdater'):
        """Initialize handler with DiagramUpdater instance."""
        self.updater = updater
        self.last_update: Dict[str, float] = {}
        self.debounce_seconds = 2.0
    
    def on_modified(self, event):
        """Handle file modification events."""
        # Skip directories
        if event.is_directory:
            return
        
        # Only process Python files
        if not event.src_path.endswith('.py'):
            return
        
        # Debounce - avoid multiple updates for same file
        now = time.time()
        if event.src_path in self.last_update:
            if now - self.last_update[event.src_path] < self.debounce_seconds:
                return  # Too soon, skip
        
        self.last_update[event.src_path] = now
        
        logger.info(f"📁 File changed: {event.src_path}")
        
        # Find affected diagrams
        changed_file = Path(event.src_path)
        affected = self.updater.find_affected_diagrams(changed_file)
        
        if affected:
            logger.info(f"  → {len(affected)} diagram(s) affected")
            for spec in affected:
                logger.info(f"  → Updating {spec.name}...")
                self.updater.update_diagram(spec)
            self.updater._save_specs()
        else:
            logger.info("  → No diagrams affected")


class DiagramUpdater:
    """Update diagrams automatically with validation and parallel processing."""
    
    def __init__(self, project_root: Path):
        """Initialize DiagramUpdater."""
        self.project_root = project_root
        self.diagrams_dir = project_root / 'docs' / 'diagrams'
        self.specs_file = self.diagrams_dir / 'diagram_specs.json'
        self.specs: List[DiagramSpec] = []
        
        # Load or create specs
        self._load_specs()
    
    def _load_specs(self):
        """Load diagram specifications from JSON file."""
        if self.specs_file.exists():
            with open(self.specs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.specs = [DiagramSpec(**spec) for spec in data.get('diagrams', [])]
        else:
            # Create default specs
            self._create_default_specs()
    
    def _create_default_specs(self):
        """Create default diagram specifications."""
        self.specs = [
            # Architecture diagram
            DiagramSpec(
                name="Documentation System Architecture",
                type="architecture",
                source_files=["docs/README.MD", "docs/automation/*.py"],
                output_path="docs/diagrams/architecture/documentation_system.mmd",
                generator_command="manual"  # Manual creation
            ),
            
            # Dependency graphs
            DiagramSpec(
                name="Processing Dependencies",
                type="dependencies",
                source_files=["processing/*.py"],
                output_path="docs/diagrams/dependencies/processing_deps.mmd",
                generator_command="python3 docs/automation/generate_call_graph.py --directory processing/ --format mermaid --output {output}"
            ),
            
            DiagramSpec(
                name="Utils Dependencies",
                type="dependencies",
                source_files=["utils/*.py"],
                output_path="docs/diagrams/dependencies/utils_deps.mmd",
                generator_command="python3 docs/automation/generate_call_graph.py --directory utils/ --format mermaid --output {output}"
            ),
            
            # Call graphs
            DiagramSpec(
                name="Full Project Call Graph",
                type="call_graph",
                source_files=["processing/*.py", "utils/*.py"],
                output_path="docs/diagrams/dependencies/full_call_graph.json",
                generator_command="python3 docs/automation/generate_call_graph.py --all --format json --output {output}"
            ),
        ]
        
        self._save_specs()
    
    def _save_specs(self):
        """Save diagram specifications to JSON file."""
        self.specs_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'diagrams': [
                {
                    'name': spec.name,
                    'type': spec.type,
                    'source_files': spec.source_files,
                    'output_path': spec.output_path,
                    'generator_command': spec.generator_command,
                    'last_updated': spec.last_updated
                }
                for spec in self.specs
            ]
        }
        
        with open(self.specs_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _validate_mermaid(self, content: str) -> bool:
        """Validate Mermaid syntax using mermaid-cli.
        
        Args:
            content: Mermaid diagram content to validate
            
        Returns:
            True if valid or validation unavailable, False if invalid
        """
        try:
            # Use mermaid-cli to validate
            result = subprocess.run(
                ['mmdc', '--validate', '-i', '-'],
                input=content,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True
            else:
                logger.warning(f"Mermaid validation failed: {result.stderr}")
                return False
            
        except FileNotFoundError:
            # mermaid-cli not installed - skip validation
            logger.warning("mermaid-cli not installed, skipping validation")
            logger.info("  Install with: npm install -g @mermaid-js/mermaid-cli")
            return True  # Don't block on missing dependency
            
        except subprocess.TimeoutExpired:
            logger.error("Mermaid validation timed out")
            return False
            
        except Exception as e:
            logger.warning(f"Mermaid validation error: {e}")
            return True  # Don't block on validation errors
    
    def check_updates_needed(self) -> List[DiagramSpec]:
        """Check which diagrams need updating.
        
        Returns:
            List of DiagramSpec objects that need updating
        """
        needs_update = []
        
        for spec in self.specs:
            if spec.generator_command == "manual":
                continue  # Skip manual diagrams
            
            # Check if source files changed
            if self._sources_changed(spec):
                needs_update.append(spec)
        
        return needs_update
    
    def _sources_changed(self, spec: DiagramSpec) -> bool:
        """Check if source files changed since last update.
        
        Args:
            spec: DiagramSpec to check
            
        Returns:
            True if sources are newer than output
        """
        output_path = self.project_root / spec.output_path
        
        # If output doesn't exist, needs update
        if not output_path.exists():
            return True
        
        output_mtime = output_path.stat().st_mtime
        
        # Check each source file pattern
        for pattern in spec.source_files:
            # Expand glob pattern
            for source_file in self.project_root.glob(pattern):
                if source_file.is_file():
                    source_mtime = source_file.stat().st_mtime
                    if source_mtime > output_mtime:
                        return True
        
        return False
    
    def find_affected_diagrams(self, changed_file: Path) -> List[DiagramSpec]:
        """Find diagrams affected by a file change.
        
        Args:
            changed_file: Path to the changed file
            
        Returns:
            List of affected DiagramSpec objects
        """
        affected = []
        
        # Normalize path
        try:
            changed_file = changed_file.resolve()
        except Exception:
            pass
        
        for spec in self.specs:
            if spec.generator_command == "manual":
                continue
            
            # Check if changed file matches any source pattern
            for source_pattern in spec.source_files:
                # Handle glob patterns
                if '*' in source_pattern:
                    matching_files = list(self.project_root.glob(source_pattern))
                    matching_resolved = [m.resolve() for m in matching_files]
                    
                    if changed_file in matching_resolved:
                        affected.append(spec)
                        break
                else:
                    # Direct file path
                    source_path = (self.project_root / source_pattern).resolve()
                    if changed_file == source_path:
                        affected.append(spec)
                        break
        
        return affected
    
    def update_diagram(self, spec: DiagramSpec) -> bool:
        """Update a single diagram with validation.
        
        Args:
            spec: DiagramSpec to update
            
        Returns:
            True if update successful, False otherwise
        """
        logger.info(f"Updating diagram: {spec.name}")
        
        if spec.generator_command == "manual":
            logger.info("  → Manual diagram, skipping")
            return False
        
        # Prepare command
        output_path = self.project_root / spec.output_path
        command = spec.generator_command.replace('{output}', str(spec.output_path))
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Execute command
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Validate Mermaid diagrams
                if spec.output_path.endswith('.mmd') and output_path.exists():
                    content = output_path.read_text(encoding='utf-8')
                    if not self._validate_mermaid(content):
                        logger.error(f"  ✗ Invalid Mermaid syntax in {spec.name}")
                        return False
                
                spec.last_updated = datetime.now().isoformat()
                logger.info(f"  ✓ Updated: {spec.output_path}")
                return True
            else:
                logger.error(f"  ✗ Error: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            logger.error(f"  ✗ Timeout generating {spec.name}")
            return False
        except Exception as e:
            logger.error(f"  ✗ Exception: {e}")
            return False
    
    def update_all(self, diagram_type: str = None, force: bool = False) -> tuple:
        """Update all diagrams (optionally filtered by type).
        
        Args:
            diagram_type: Filter by diagram type (optional)
            force: Update all diagrams regardless of changes
            
        Returns:
            Tuple of (updated_count, failed_count)
        """
        updated = 0
        failed = 0
        skipped = 0
        
        for spec in self.specs:
            # Filter by type if specified
            if diagram_type and spec.type != diagram_type:
                continue
            
            # Skip if not changed (unless force)
            if not force and not self._sources_changed(spec):
                skipped += 1
                logger.info(f"⊡ Up-to-date: {spec.name}")
                continue
            
            if self.update_diagram(spec):
                updated += 1
            else:
                failed += 1
        
        # Save updated specs
        self._save_specs()
        
        logger.info(f"Summary: {updated} updated, {failed} failed, {skipped} skipped")
        return (updated, failed)
    
    def update_all_parallel(self, diagram_type: str = None, 
                           max_workers: int = 4, force: bool = False) -> tuple:
        """Update diagrams in parallel for faster processing.
        
        Args:
            diagram_type: Filter by diagram type (optional)
            max_workers: Number of parallel workers (default: 4)
            force: Update all diagrams regardless of changes
            
        Returns:
            Tuple of (updated_count, failed_count)
        """
        # Filter specs to update
        specs_to_update = []
        for spec in self.specs:
            # Filter by type
            if diagram_type and spec.type != diagram_type:
                continue
            
            # Skip manual diagrams
            if spec.generator_command == "manual":
                continue
            
            # Skip if not changed (unless force)
            if not force and not self._sources_changed(spec):
                logger.info(f"⊡ Up-to-date: {spec.name}")
                continue
            
            specs_to_update.append(spec)
        
        if not specs_to_update:
            logger.info("No diagrams need updating")
            return (0, 0)
        
        logger.info(f"Updating {len(specs_to_update)} diagram(s) in parallel (workers={max_workers})...")
        
        updated = 0
        failed = 0
        
        # Parallel execution
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_spec = {
                executor.submit(self._update_diagram_worker, spec): spec
                for spec in specs_to_update
            }
            
            # Collect results
            for future in as_completed(future_to_spec):
                spec = future_to_spec[future]
                try:
                    success, last_updated = future.result()
                    if success:
                        updated += 1
                        spec.last_updated = last_updated
                        logger.info(f"  ✓ {spec.name}")
                    else:
                        failed += 1
                        logger.error(f"  ✗ {spec.name}")
                except Exception as e:
                    failed += 1
                    logger.error(f"  ✗ {spec.name}: {e}")
        
        # Save updated specs
        self._save_specs()
        
        logger.info(f"Summary: {updated} updated, {failed} failed")
        return (updated, failed)
    
    def _update_diagram_worker(self, spec: DiagramSpec) -> tuple:
        """Worker function for parallel diagram updates.
        
        Args:
            spec: DiagramSpec to update
            
        Returns:
            Tuple of (success: bool, last_updated: str or None)
        """
        # Prepare command
        output_path = self.project_root / spec.output_path
        command = spec.generator_command.replace('{output}', str(spec.output_path))
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return (True, datetime.now().isoformat())
            else:
                return (False, None)
                
        except Exception:
            return (False, None)
    
    def watch_mode(self):
        """Watch for file changes and auto-update diagrams.
        
        Requires watchdog library: pip install watchdog
        """
        if not WATCHDOG_AVAILABLE:
            logger.error("Watch mode requires watchdog library")
            logger.info("Install with: pip install watchdog")
            return
        
        logger.info("👀 Starting watch mode...")
        logger.info(f"   Monitoring: {self.project_root}")
        logger.info("   Press Ctrl+C to stop")
        logger.info("")
        
        # Show monitored patterns
        patterns = set()
        for spec in self.specs:
            if spec.generator_command != "manual":
                for pattern in spec.source_files:
                    patterns.add(pattern)
        logger.info(f"   Patterns: {', '.join(sorted(patterns))}")
        logger.info("")
        
        # Create event handler and observer
        event_handler = DiagramFileHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.project_root), recursive=True)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("\n👋 Stopped watching")
        
        observer.join()
    
    def generate_index(self):
        """Generate index of all diagrams."""
        index_path = self.diagrams_dir / 'INDEX.md'
        
        lines = []
        lines.append("# Diagram Index\n")
        lines.append(f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Group by type
        by_type: Dict[str, List[DiagramSpec]] = {}
        for spec in self.specs:
            if spec.type not in by_type:
                by_type[spec.type] = []
            by_type[spec.type].append(spec)
        
        # Generate sections
        for diagram_type, specs in sorted(by_type.items()):
            lines.append(f"## {diagram_type.title()}\n")
            
            for spec in specs:
                output_path = Path(spec.output_path)
                try:
                    relative_path = output_path.relative_to(self.diagrams_dir)
                except ValueError:
                    relative_path = output_path
                
                lines.append(f"### {spec.name}\n")
                lines.append(f"- **File**: [{output_path.name}]({relative_path})")
                lines.append(f"- **Type**: {spec.type}")
                
                if spec.last_updated:
                    lines.append(f"- **Last Updated**: {spec.last_updated}")
                
                lines.append(f"- **Sources**: {', '.join(spec.source_files)}")
                lines.append("")
        
        # Write index (only once)
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Index generated: {index_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Update diagrams automatically',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --check                    # Check which diagrams need updating
  %(prog)s --update-all               # Update all diagrams that need it
  %(prog)s --update-all --force       # Force update all diagrams
  %(prog)s --update-all --parallel    # Update in parallel (faster)
  %(prog)s --watch                    # Watch for changes and auto-update
  %(prog)s --generate-index           # Generate diagram index
        """
    )
    
    parser.add_argument('--check', action='store_true', 
                       help='Check which diagrams need updating')
    parser.add_argument('--update-all', action='store_true', 
                       help='Update all diagrams')
    parser.add_argument('--type', type=str, 
                       help='Update specific diagram type')
    parser.add_argument('--force', action='store_true',
                       help='Force update even if not changed')
    parser.add_argument('--generate-index', action='store_true', 
                       help='Generate diagram index')
    parser.add_argument('--watch', action='store_true',
                       help='Watch for file changes and auto-update')
    parser.add_argument('--parallel', action='store_true',
                       help='Update diagrams in parallel (faster)')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers (default: 4)')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    updater = DiagramUpdater(project_root)
    
    if args.check:
        needs_update = updater.check_updates_needed()
        if needs_update:
            logger.info("Diagrams needing update:")
            for spec in needs_update:
                logger.info(f"  - {spec.name} ({spec.output_path})")
        else:
            logger.info("All diagrams are up to date")
    
    elif args.watch:
        updater.watch_mode()
    
    elif args.update_all:
        if args.parallel:
            updater.update_all_parallel(args.type, args.workers, args.force)
        else:
            updater.update_all(args.type, args.force)
    
    elif args.generate_index:
        updater.generate_index()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
