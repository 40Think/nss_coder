#!/usr/bin/env python3
"""
Documentation System Global Supervisor - Horizontal Analysis for System Health

<!--TAG:docs_global_supervisor-->

PURPOSE:
    Performs horizontal analysis across the entire documentation system.
    Aggregates intellectual logs from all automation scripts,
    generates executive summary with system health status,
    and provides recommendations for improvements.

DOCUMENTATION:
    Spec: docs/logging_system/README.MD
    Wiki: docs/wiki/verification_memory_systems.md
    Based on: utils/global_supervisor.py (main project)

TAGS: <!--TAG:automation--> <!--TAG:testing--> <!--TAG:ai_analysis-->

<!--/TAG:docs_global_supervisor-->
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Import required utilities
from utils.paranoid_logger import ParanoidLogger

# Try to import LLM client
try:
    from utils.llm_client import LLMClient
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Try to import SessionStats
try:
    from utils.session_stats import SessionStats
    SESSION_STATS_AVAILABLE = True
except ImportError:
    SESSION_STATS_AVAILABLE = False

# Initialize paranoid logger
logger = ParanoidLogger("docs_global_supervisor")


class DocsGlobalSupervisor:
    """
    Global Supervisor for Documentation System - Horizontal Analysis.
    
    Philosophy:
    - Horizontal Analysis: Analyze entire system health across all scripts.
    - Aggregation: Collect intellectual logs from all automation scripts.
    - Executive Summary: Generate high-level health report.
    - Recommendations: Provide actionable improvement suggestions.
    """
    
    def __init__(self):
        """Initialize the Global Supervisor with project paths."""
        self.project_root = project_root
        self.logs_dir = self.project_root / "logs"
        self.intellectual_dir = self.logs_dir / "intellectual"
        self.paranoid_dir = self.logs_dir / "paranoid"
        self.output_dir = self.project_root / "output" / "global_supervision"
        self.llm_requests_dir = self.project_root / "llm_requests"
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm_requests_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize LLM client if available
        self.llm_client = LLMClient() if LLM_AVAILABLE else None
        
        # Initialize stats
        self.stats = SessionStats() if SESSION_STATS_AVAILABLE else None
        
        logger.info("DocsGlobalSupervisor initialized", {
            "project_root": str(self.project_root),
            "intellectual_dir": str(self.intellectual_dir),
            "output_dir": str(self.output_dir)
        })
    
    def supervise(self) -> bool:
        """
        Main execution method for global supervision.
        
        Returns:
            True if supervision completed successfully
        """
        start_time = time.time()
        logger.log_step("Global Supervision", "STARTED", 0, 0)
        
        print(f"\n{'='*60}")
        print("🌍 DOCUMENTATION GLOBAL SUPERVISOR - Horizontal Analysis")
        print(f"{'='*60}\n")
        
        try:
            # 1. Gather intellectual logs from all scripts
            summaries = self._gather_intellectual_logs()
            
            if not summaries:
                logger.warning("No intellectual logs found")
                print("⚠️  No intellectual logs found in logs/intellectual/")
                print("Action: Run automation scripts first to generate logs.\n")
                
                # Generate empty report
                self._generate_empty_report()
                return True
            
            logger.info(f"Gathered {len(summaries)} intellectual logs")
            print(f"✓ Gathered {len(summaries)} intellectual logs.\n")
            
            # 2. Gather recent paranoid log statistics
            paranoid_stats = self._gather_paranoid_stats()
            
            # 3. Generate Executive Summary via LLM
            executive_summary = self._generate_executive_summary(summaries, paranoid_stats)
            
            # 4. Determine health status
            health_status = self._determine_health_status(executive_summary)
            
            # 5. Save report
            self._save_report(executive_summary, health_status, summaries)
            
            # 6. Generate intellectual log for this run
            self._generate_intellectual_log(summaries, health_status, time.time() - start_time)
            
            duration = time.time() - start_time
            logger.log_step("Global Supervision", "COMPLETED", duration, 0)
            
            # Print summary
            print(f"\n{'='*60}")
            print(f"System Health: {health_status}")
            print(f"{'='*60}")
            print(f"Report saved to: {self.output_dir / 'executive_summary.md'}")
            
            if self.stats:
                self.stats.print_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"Global Supervision failed: {e}")
            print(f"\n❌ Global Supervision Failed: {e}")
            
            if "connection" in str(e).lower() or "llm" in str(e).lower():
                print("\n💡 TIP: Is your LLM server running?")
            
            return False
    
    def _gather_intellectual_logs(self) -> Dict[str, str]:
        """
        Gather intellectual logs from all automation scripts.
        
        Returns:
            Dict mapping script name to log content
        """
        summaries = {}
        
        if not self.intellectual_dir.exists():
            logger.warning(f"Intellectual logs directory not found: {self.intellectual_dir}")
            return summaries
        
        # Get all log files
        log_files = sorted(self.intellectual_dir.glob("*.md"), key=os.path.getmtime, reverse=True)
        
        logger.log_file_interaction(
            str(self.intellectual_dir),
            "list_dir",
            "SUCCESS",
            {"count": len(log_files)}
        )
        
        # Read each log file
        for log_file in log_files:
            try:
                content = log_file.read_text(encoding='utf-8')
                script_name = log_file.stem
                summaries[script_name] = content
                
                logger.log_file_interaction(str(log_file), "read_log", "SUCCESS", {"size": len(content)})
            except Exception as e:
                logger.warning(f"Failed to read log {log_file}: {e}")
        
        return summaries
    
    def _gather_paranoid_stats(self) -> Dict[str, Any]:
        """
        Gather statistics from paranoid logs.
        
        Returns:
            Dict with aggregated statistics
        """
        stats = {
            "total_log_files": 0,
            "total_log_size_bytes": 0,
            "scripts_logged": [],
            "error_count": 0,
            "warning_count": 0
        }
        
        if not self.paranoid_dir.exists():
            return stats
        
        # Count log files and sizes
        for script_dir in self.paranoid_dir.iterdir():
            if script_dir.is_dir():
                stats["scripts_logged"].append(script_dir.name)
                
                for log_file in script_dir.glob("*.log"):
                    stats["total_log_files"] += 1
                    stats["total_log_size_bytes"] += log_file.stat().st_size
                    
                    # Quick scan for errors/warnings
                    try:
                        content = log_file.read_text(encoding='utf-8', errors='ignore')
                        stats["error_count"] += content.lower().count("[error]")
                        stats["warning_count"] += content.lower().count("[warning]")
                    except Exception:
                        pass
        
        return stats
    
    def _generate_executive_summary(self, summaries: Dict[str, str], paranoid_stats: Dict) -> str:
        """
        Generate executive summary using LLM.
        
        Args:
            summaries: Dict of intellectual log summaries
            paranoid_stats: Statistics from paranoid logs
            
        Returns:
            Executive summary string
        """
        # Build prompt
        summaries_text = "\n\n".join([
            f"## {script}\n{content}" 
            for script, content in summaries.items()
        ])
        
        prompt = f"""You are the GLOBAL SUPERVISOR for the NSS-DOCS Documentation System.
Your job is to generate an Executive Summary (A4 equivalent) of the entire system's health.

# INPUT DATA

## Intellectual Logs from Scripts
{summaries_text[:10000]}

## Paranoid Log Statistics
- Total log files: {paranoid_stats['total_log_files']}
- Total log size: {paranoid_stats['total_log_size_bytes'] / 1024:.1f} KB
- Scripts with logging: {len(paranoid_stats['scripts_logged'])}
- Error count: {paranoid_stats['error_count']}
- Warning count: {paranoid_stats['warning_count']}

# TASK
Generate an Executive Summary covering:

1. **Overall Health Status**: 🟢 GREEN / 🟡 YELLOW / 🔴 RED
   - GREEN: All systems healthy, no critical issues
   - YELLOW: Some issues need attention
   - RED: Critical problems requiring immediate action

2. **Key Metrics**:
   - Documentation coverage
   - Quality scores (if available)
   - Error/warning rates

3. **Script-by-Script Health**:
   Brief status of each automation script

4. **System-wide Issues**:
   - Patterns across multiple scripts
   - Recurring problems
   - Bottlenecks

5. **Recommendations**:
   - Priority fixes (numbered 1, 2, 3)
   - Improvement suggestions
   - Next steps

Be concise but comprehensive. Use markdown formatting.
"""
        
        # Log request
        req_id = f"global_sup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        req_file = self.llm_requests_dir / f"{req_id}_req.txt"
        self._write_atomic(req_file, prompt)
        logger.log_file_interaction(str(req_file), "save_llm_request", "SUCCESS")
        
        # Call LLM
        if self.llm_client:
            try:
                logger.info("Sending request to LLM...")
                gen_start = time.time()
                
                summary = self.llm_client.generate(
                    system_prompt="You are the Chief Technical Supervisor for a documentation system.",
                    user_prompt=prompt,
                    model=None,  # Use default model
                    temperature=0.1
                )
                
                duration = time.time() - gen_start
                logger.info("LLM generation complete", {"duration": duration})
                
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                summary = self._generate_fallback_summary(summaries, paranoid_stats)
        else:
            summary = self._generate_fallback_summary(summaries, paranoid_stats)
        
        # Log response
        resp_file = self.llm_requests_dir / f"{req_id}_resp.md"
        self._write_atomic(resp_file, summary)
        logger.log_file_interaction(str(resp_file), "save_llm_response", "SUCCESS")
        
        return summary
    
    def _generate_fallback_summary(self, summaries: Dict[str, str], paranoid_stats: Dict) -> str:
        """
        Generate fallback summary when LLM is not available.
        
        Args:
            summaries: Dict of intellectual log summaries
            paranoid_stats: Statistics from paranoid logs
            
        Returns:
            Fallback summary string
        """
        # Determine health based on statistics
        if paranoid_stats['error_count'] > 10:
            health = "🔴 RED"
        elif paranoid_stats['warning_count'] > 20 or paranoid_stats['error_count'] > 0:
            health = "🟡 YELLOW"
        else:
            health = "🟢 GREEN"
        
        return f"""# Executive Summary

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Status**: {health}

## Overview

This is an auto-generated fallback summary (LLM not available).

## Key Metrics

- Total paranoid log files: {paranoid_stats['total_log_files']}
- Total log size: {paranoid_stats['total_log_size_bytes'] / 1024:.1f} KB
- Scripts with logging: {len(paranoid_stats['scripts_logged'])}
- Errors detected: {paranoid_stats['error_count']}
- Warnings detected: {paranoid_stats['warning_count']}

## Scripts Status

{chr(10).join([f"- {script}" for script in paranoid_stats['scripts_logged']])}

## Intellectual Logs Available

{chr(10).join([f"- {script}" for script in summaries.keys()])}

## Recommendations

1. Enable LLM for detailed analysis
2. Review any scripts with errors/warnings
3. Run docs_deep_supervisor.py for vertical analysis

---
*Note: This is a fallback summary. Connect LLM for AI-powered analysis.*
"""
    
    def _determine_health_status(self, summary: str) -> str:
        """
        Determine health status from executive summary.
        
        Args:
            summary: Executive summary string
            
        Returns:
            Health status string
        """
        summary_upper = summary.upper()
        
        if "🔴" in summary or "RED" in summary_upper:
            return "🔴 RED - Critical issues require immediate attention"
        elif "🟡" in summary or "YELLOW" in summary_upper:
            return "🟡 YELLOW - Some issues need attention"
        else:
            return "🟢 GREEN - Documentation system is healthy"
    
    def _save_report(self, summary: str, health_status: str, 
                     summaries: Dict[str, str]) -> None:
        """
        Save the executive summary report.
        
        Args:
            summary: Executive summary content
            health_status: Overall health status
            summaries: Dict of intellectual logs (for metadata)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save executive summary
        summary_file = self.output_dir / "executive_summary.md"
        
        full_report = f"""# 🌍 Documentation System - Global Supervision Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Health Status**: {health_status}

---

{summary}

---

## Metadata

- **Report ID**: {timestamp}
- **Scripts Analyzed**: {len(summaries)}
- **Generated by**: DocsGlobalSupervisor

---
*This report was generated by the Documentation Global Supervisor.*
"""
        
        self._write_atomic(summary_file, full_report)
        logger.log_file_interaction(str(summary_file), "save_report", "SUCCESS")
        
        # Also save timestamped version
        archive_file = self.output_dir / f"executive_summary_{timestamp}.md"
        self._write_atomic(archive_file, full_report)
    
    def _generate_empty_report(self) -> None:
        """Generate empty report when no logs are available."""
        report = f"""# 🌍 Documentation System - Global Supervision Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Health Status**: ⚪ UNKNOWN - No data available

---

## Summary

No intellectual logs were found. This means either:

1. Automation scripts haven't been run yet
2. Scripts don't have paranoid logging enabled
3. Logs directory is not configured correctly

## Next Steps

1. Run automation scripts to generate logs:
   ```bash
   python3 docs/automation/analyze_dependencies.py --target utils/paranoid_logger.py
   python3 docs/automation/validate_docs.py
   ```

2. Run deep supervision for vertical analysis:
   ```bash
   python3 utils/docs_deep_supervisor.py --sample-size 10
   ```

3. Re-run this global supervisor:
   ```bash
   python3 utils/docs_global_supervisor.py
   ```

---
*This report was generated by the Documentation Global Supervisor.*
"""
        
        summary_file = self.output_dir / "executive_summary.md"
        self._write_atomic(summary_file, report)
        logger.log_file_interaction(str(summary_file), "save_empty_report", "SUCCESS")
        
        print(f"📋 Empty report saved to: {summary_file}")
    
    def _generate_intellectual_log(self, summaries: Dict[str, str], 
                                    health_status: str, duration: float) -> None:
        """
        Generate intellectual log for this supervision run.
        
        Args:
            summaries: Dict of analyzed logs
            health_status: Overall health status
            duration: Run duration in seconds
        """
        log_content = f"""# Intellectual Log: docs_global_supervisor

## Session Statistics
- **Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Duration**: {duration:.2f}s
- **Scripts Analyzed**: {len(summaries)}

## Health Status
{health_status}

## Logs Analyzed
{chr(10).join([f"- {script}" for script in summaries.keys()])}

## Output
- Executive Summary: output/global_supervision/executive_summary.md
"""
        
        log_dir = self.logs_dir / "intellectual"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"docs_global_supervisor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._write_atomic(log_file, log_content)
        
        logger.log_file_interaction(str(log_file), "save_intellectual_log", "SUCCESS")
    
    def _write_atomic(self, path: Path, content: str) -> None:
        """
        Write content to file atomically.
        
        Args:
            path: Target file path
            content: Content to write
        """
        temp_path = path.with_suffix(".tmp")
        try:
            temp_path.write_text(content, encoding='utf-8')
            temp_path.replace(path)
        except Exception as e:
            logger.error(f"Atomic write failed for {path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise


def main():
    """CLI entry point for the Documentation Global Supervisor."""
    print("Starting Documentation Global Supervisor...")
    
    supervisor = DocsGlobalSupervisor()
    success = supervisor.supervise()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
