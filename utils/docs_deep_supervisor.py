#!/usr/bin/env python3
"""
Documentation System Deep Supervisor - Vertical Analysis for Documentation Quality

<!--TAG:docs_deep_supervisor-->

PURPOSE:
    Performs deep vertical analysis of documentation files using LLM.
    Traces individual documentation files through quality checks,
    evaluates completeness, accuracy, consistency, and AI-readability.
    Generates QA reports and bug tickets for issues found.

DOCUMENTATION:
    Spec: docs/logging_system/README.MD
    Wiki: docs/wiki/verification_memory_systems.md
    Based on: utils/deep_supervisor.py (main project)

TAGS: <!--TAG:automation--> <!--TAG:testing--> <!--TAG:ai_analysis-->

<!--/TAG:docs_deep_supervisor-->
"""

import os
import random
import re
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
import sys
sys.path.append(str(project_root))

# Import required utilities
from utils.paranoid_logger import ParanoidLogger

# Try to import LLM client - handle if not available
try:
    from utils.llm_client import call_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    def call_llm(system_prompt: str, user_prompt: str) -> str:
        """Fallback when LLM not available."""
        return json.dumps({
            "status": "WARN",
            "quality_score": 0,
            "issues": ["LLM client not available - manual review required"],
            "completeness_score": 0,
            "accuracy_score": 0,
            "consistency_score": 0,
            "ai_readability_score": 0
        })

# Try to import SessionStats
try:
    from utils.session_stats import SessionStats
    SESSION_STATS_AVAILABLE = True
except ImportError:
    SESSION_STATS_AVAILABLE = False

# Initialize Paranoid Logger for this script
paranoid = ParanoidLogger("docs_deep_supervisor")


class DocsDeepSupervisor:
    """
    Deep Supervisor for Documentation System - Vertical Analysis.
    
    Philosophy:
    - Vertical Analysis: Traces individual documentation file's quality.
    - Contextual Awareness: Uses project structure to judge quality.
    - QA/Bug Generation: Produces actionable tickets for issues.
    - Focus: Completeness, accuracy, consistency, AI-readability.
    """
    
    def __init__(self):
        """Initialize the Deep Supervisor with project paths."""
        self.root_dir = project_root  # Project root directory
        self.docs_dir = self.root_dir / "docs"  # Documentation directory
        self.output_dir = self.root_dir / "output" / "deep_supervision"  # Output directory for reports
        self.tickets_dir = self.output_dir / "tickets"  # Directory for bug tickets
        self.llm_requests_dir = self.root_dir / "llm_requests"  # Directory for LLM request/response logs
        
        # Create output directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tickets_dir.mkdir(parents=True, exist_ok=True)
        self.llm_requests_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize session stats if available
        self.stats = SessionStats() if SESSION_STATS_AVAILABLE else None
        
        # Log initialization
        paranoid.info("DocsDeepSupervisor initialized", {
            "root_dir": str(self.root_dir),
            "docs_dir": str(self.docs_dir),
            "output_dir": str(self.output_dir)
        })
    
    def run(self, sample_size: int = 20) -> bool:
        """
        Main execution method for deep documentation analysis.
        
        Args:
            sample_size: Number of documentation files to analyze
            
        Returns:
            True if analysis completed, False if aborted
        """
        start_time = time.time()
        paranoid.log_step("Deep Supervision", "STARTED", 0, 0)
        paranoid.info(f"Starting Deep Supervision with sample_size={sample_size}")
        
        print(f"\n{'='*60}")
        print("📊 DOCUMENTATION DEEP SUPERVISOR - Vertical Analysis")
        print(f"{'='*60}\n")
        
        # 1. Select sample documentation files
        sample_files = self._select_sample_files(sample_size)
        if not sample_files:
            msg = "❌ FATAL ERROR: No documentation files found!"
            paranoid.error("No documentation files found for analysis")
            print(f"\n{msg}")
            print("Action: Ensure docs/ directory contains .md files.\n")
            return False
        
        paranoid.info(f"Selected {len(sample_files)} files for analysis")
        print(f"✓ Selected {len(sample_files)} documentation files for analysis.\n")
        
        # 2. Collect project context
        project_context = self._collect_project_context()
        
        # 3. Analyze each file
        analyses = []
        llm_failures = 0
        
        for i, file_path in enumerate(sample_files, 1):
            print(f"[{i}/{len(sample_files)}] Analyzing: {file_path.name}...")
            analysis_start = time.time()
            
            try:
                # Perform vertical analysis on this file
                analysis = self._analyze_file_vertical(file_path, project_context)
                analysis["filename"] = str(file_path.relative_to(self.root_dir))
                analyses.append(analysis)
                
                # Log result
                status = analysis.get("status", "UNKNOWN")
                score = analysis.get("quality_score", 0)
                
                if status == "PASS":
                    print(f"    ✅ PASS (Score: {score}/100)")
                    paranoid.log_step(f"Analyze {file_path.name}", "COMPLETED", time.time() - analysis_start)
                elif status == "WARN":
                    print(f"    ⚠️  WARN (Score: {score}/100)")
                    paranoid.log_step(f"Analyze {file_path.name}", "COMPLETED", time.time() - analysis_start)
                else:
                    print(f"    ❌ FAIL (Score: {score}/100)")
                    paranoid.log_step(f"Analyze {file_path.name}", "FAILED", time.time() - analysis_start)
                    
            except Exception as e:
                error_msg = str(e)
                print(f"    ❌ Error: {error_msg[:50]}...")
                paranoid.error(f"Failed to analyze {file_path.name}: {e}")
                
                if "connection" in error_msg.lower() or "llm" in error_msg.lower():
                    llm_failures += 1
        
        # Check if all LLM calls failed
        if llm_failures == len(sample_files):
            print("\n❌ CRITICAL: 100% of LLM calls failed. Is the LLM server running?")
        
        # 4. Generate consolidated QA report
        if analyses:
            self._generate_qa_report(analyses)
        
        # 5. Generate intellectual log
        self._generate_intellectual_log(analyses, time.time() - start_time)
        
        # Log completion
        duration = time.time() - start_time
        paranoid.log_step("Deep Supervision", "COMPLETED", duration, 0)
        paranoid.info(f"Deep Supervision complete. Duration: {duration:.2f}s")
        
        # Print statistics if available
        if self.stats:
            self.stats.print_summary()
        
        return True
    
    def _select_sample_files(self, limit: int) -> List[Path]:
        """
        Select sample documentation files for analysis.
        
        Args:
            limit: Maximum number of files to select
            
        Returns:
            List of Path objects to documentation files
        """
        # Find all markdown files in docs directory
        all_files = list(self.docs_dir.rglob("*.md"))
        
        # Log file discovery
        paranoid.log_file_interaction(
            str(self.docs_dir),
            "glob_search",
            "SUCCESS",
            {"pattern": "*.md", "found": len(all_files)}
        )
        
        if not all_files:
            return []
        
        # Filter out temp files and very small files
        valid_files = []
        for f in all_files:
            # Skip temp directory files
            if "temp" in str(f).lower():
                continue
            # Skip very small files (likely placeholders)
            if f.stat().st_size < 100:
                continue
            valid_files.append(f)
        
        # If we have fewer files than limit, take all
        if len(valid_files) <= limit:
            selected = valid_files
        else:
            # Randomly sample
            selected = random.sample(valid_files, limit)
        
        paranoid.info(f"Selected {len(selected)} files from {len(valid_files)} valid candidates")
        return selected
    
    def _collect_project_context(self) -> str:
        """
        Collect project context for analysis.
        
        Returns:
            String containing project structure and key documentation
        """
        context_parts = []
        
        # Key documentation files to include
        key_files = [
            "docs/README.MD",
            "GEMINI.MD",
            "README.md"
        ]
        
        for rel_path in key_files:
            path = self.root_dir / rel_path
            if path.exists():
                try:
                    content = path.read_text(encoding='utf-8')
                    # Limit content size
                    if len(content) > 5000:
                        content = content[:5000] + "\n... (truncated)"
                    context_parts.append(f"--- FILE: {rel_path} ---\n{content}")
                    
                    paranoid.log_file_interaction(str(path), "read_context", "SUCCESS", {"size": len(content)})
                except Exception as e:
                    paranoid.warning(f"Failed to read context file {rel_path}: {e}")
        
        # Get directory structure
        structure = self._get_directory_structure()
        context_parts.append(f"--- DIRECTORY STRUCTURE ---\n{structure}")
        
        return "\n\n".join(context_parts)
    
    def _get_directory_structure(self) -> str:
        """Get simplified directory structure of docs folder."""
        lines = []
        
        def add_dir(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
            if current_depth >= max_depth:
                return
            
            try:
                items = sorted(path.iterdir())
                dirs = [i for i in items if i.is_dir() and not i.name.startswith('.')]
                files = [i for i in items if i.is_file() and i.suffix == '.md']
                
                for d in dirs[:10]:  # Limit directories
                    lines.append(f"{prefix}📁 {d.name}/")
                    add_dir(d, prefix + "  ", max_depth, current_depth + 1)
                
                for f in files[:5]:  # Limit files shown
                    lines.append(f"{prefix}📄 {f.name}")
                    
                if len(files) > 5:
                    lines.append(f"{prefix}... and {len(files) - 5} more files")
            except Exception:
                pass
        
        add_dir(self.docs_dir)
        return "\n".join(lines[:50])  # Limit total lines
    
    def _analyze_file_vertical(self, file_path: Path, project_context: str) -> Dict[str, Any]:
        """
        Perform deep vertical analysis of a single documentation file.
        
        Args:
            file_path: Path to the documentation file
            project_context: String containing project context
            
        Returns:
            Dict with analysis results
        """
        # Read file content
        try:
            content = file_path.read_text(encoding='utf-8')
            paranoid.log_file_interaction(str(file_path), "read_target", "SUCCESS", {"size": len(content)})
        except Exception as e:
            paranoid.error(f"Failed to read file {file_path}: {e}")
            return {
                "status": "FAIL",
                "quality_score": 0,
                "issues": [f"File read error: {e}"]
            }
        
        # Construct analysis prompt
        system_prompt = """You are the Deep Supervisor for Documentation Quality Analysis.

Your goal is to perform PARANOID, VERTICAL analysis of a documentation file.

# THE VISION: AI-First Documentation
We are building a documentation system designed for AI agents. The documentation must be:
- Accurate and complete
- Semantically tagged for line-shift resistance
- Hierarchically organized for easy navigation
- Cross-referenced correctly
- AI-readable and human-readable

# YOUR TASK
Evaluate this documentation file on these criteria:

1. **COMPLETENESS** (0-100):
   - Are all expected sections present?
   - Are semantic tags (<!--TAG:...-->) used?
   - Are cross-references included?
   - Is the content substantive (not just placeholders)?

2. **ACCURACY** (0-100):
   - Do file references point to real files?
   - Are code examples syntactically correct?
   - Is technical information accurate?

3. **CONSISTENCY** (0-100):
   - Consistent formatting throughout?
   - Consistent terminology?
   - Consistent structure?

4. **AI-READABILITY** (0-100):
   - Clear context for AI?
   - Good metadata and tags?
   - Hierarchical structure?
   - Comments explaining purpose?

You must be STRICT. Flag any issue you find.

# OUTPUT FORMAT
Return a JSON object with EXACTLY this structure:
{
    "status": "PASS" | "WARN" | "FAIL",
    "quality_score": 0-100,
    "completeness_score": 0-100,
    "accuracy_score": 0-100,
    "consistency_score": 0-100,
    "ai_readability_score": 0-100,
    "issues": ["specific issue 1", "specific issue 2"],
    "strengths": ["strength 1", "strength 2"],
    "recommendations": ["recommendation 1", "recommendation 2"]
}

Use these thresholds:
- PASS: quality_score >= 80
- WARN: quality_score >= 50 and < 80
- FAIL: quality_score < 50
"""

        user_prompt = f"""# ANALYSIS REQUEST

## Project Context
{project_context[:3000]}

---

## Target File: {file_path.name}
## Path: {file_path.relative_to(self.root_dir)}

## Content:
{content[:8000]}

---

Analyze this documentation file. Return ONLY the JSON object, no other text.
"""

        # Log LLM request
        request_id = f"docs_deep_{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        request_file = self.llm_requests_dir / f"{request_id}_req.json"
        
        try:
            request_data = {
                "timestamp": datetime.now().isoformat(),
                "file": str(file_path),
                "request_id": request_id
            }
            self._write_atomic(request_file, json.dumps(request_data, indent=2, ensure_ascii=False))
        except Exception as e:
            paranoid.warning(f"Failed to save LLM request log: {e}")
        
        # Call LLM
        llm_start = time.time()
        response = call_llm(system_prompt, user_prompt)
        llm_duration = time.time() - llm_start
        
        # Log LLM response
        response_file = self.llm_requests_dir / f"{request_id}_resp.txt"
        try:
            self._write_atomic(response_file, response)
            paranoid.log_file_interaction(str(response_file), "save_llm_response", "SUCCESS")
        except Exception as e:
            paranoid.warning(f"Failed to save LLM response: {e}")
        
        paranoid.info("LLM Analysis Complete", {
            "filename": file_path.name,
            "duration": f"{llm_duration:.2f}s",
            "response_length": len(response)
        })
        
        # Parse response
        return self._parse_llm_response(response, file_path)
    
    def _parse_llm_response(self, response: str, file_path: Path) -> Dict[str, Any]:
        """
        Parse LLM response into structured analysis result.
        
        Args:
            response: Raw LLM response string
            file_path: Path to analyzed file (for error context)
            
        Returns:
            Dict with parsed analysis
        """
        # Try direct JSON parse
        try:
            # Clean markdown code blocks
            clean = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            pass
        
        # Try regex extraction
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Fallback response
        paranoid.warning(f"Failed to parse LLM response for {file_path.name}")
        return {
            "status": "WARN",
            "quality_score": 0,
            "issues": ["LLM response parsing failed - manual review required"],
            "raw_response": response[:500]
        }
    
    def _generate_qa_report(self, analyses: List[Dict]) -> None:
        """
        Generate consolidated QA report from all analyses.
        
        Args:
            analyses: List of analysis results
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"QA_Report_{timestamp}.md"
        
        # Count results
        pass_count = sum(1 for a in analyses if a.get("status") == "PASS")
        warn_count = sum(1 for a in analyses if a.get("status") == "WARN")
        fail_count = sum(1 for a in analyses if a.get("status") == "FAIL")
        
        # Calculate averages
        scores = [a.get("quality_score", 0) for a in analyses if isinstance(a.get("quality_score"), (int, float))]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Build report
        report = f"""# 📊 Documentation Deep Supervision QA Report

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Files Analyzed**: {len(analyses)}  
**Average Quality Score**: {avg_score:.1f}/100

---

## Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ PASS | {pass_count} | {pass_count*100/len(analyses):.1f}% |
| ⚠️ WARN | {warn_count} | {warn_count*100/len(analyses):.1f}% |
| ❌ FAIL | {fail_count} | {fail_count*100/len(analyses):.1f}% |

## Overall Assessment

"""
        # Add overall assessment
        if avg_score >= 80:
            report += "🟢 **HEALTHY**: Documentation system is in good shape.\n\n"
        elif avg_score >= 50:
            report += "🟡 **ATTENTION NEEDED**: Some documentation requires improvement.\n\n"
        else:
            report += "🔴 **CRITICAL**: Documentation quality is below acceptable levels.\n\n"
        
        # Add detailed findings
        report += "---\n\n## Detailed Findings\n\n"
        
        for analysis in sorted(analyses, key=lambda x: x.get("quality_score", 0)):
            filename = analysis.get("filename", "Unknown")
            status = analysis.get("status", "UNKNOWN")
            score = analysis.get("quality_score", 0)
            
            icon = "✅" if status == "PASS" else "⚠️" if status == "WARN" else "❌"
            
            report += f"### {icon} {filename} (Score: {score}/100)\n\n"
            
            # Add sub-scores if available
            if "completeness_score" in analysis:
                report += f"- Completeness: {analysis.get('completeness_score', 'N/A')}/100\n"
                report += f"- Accuracy: {analysis.get('accuracy_score', 'N/A')}/100\n"
                report += f"- Consistency: {analysis.get('consistency_score', 'N/A')}/100\n"
                report += f"- AI-Readability: {analysis.get('ai_readability_score', 'N/A')}/100\n\n"
            
            # Add issues
            issues = analysis.get("issues", [])
            if issues:
                report += "**Issues**:\n"
                for issue in issues[:5]:  # Limit to 5 issues
                    report += f"- {issue}\n"
                report += "\n"
            
            # Add recommendations
            recommendations = analysis.get("recommendations", [])
            if recommendations:
                report += "**Recommendations**:\n"
                for rec in recommendations[:3]:
                    report += f"- {rec}\n"
                report += "\n"
            
            # Generate ticket for WARN/FAIL
            if status in ["WARN", "FAIL"]:
                self._generate_ticket(filename, analysis)
            
            report += "---\n\n"
        
        # Write report
        self._write_atomic(report_file, report)
        paranoid.log_file_interaction(str(report_file), "save_report", "SUCCESS", {"size": len(report)})
        
        print(f"\n📋 QA Report saved to: {report_file}")
        print(f"   Summary: {pass_count} PASS, {warn_count} WARN, {fail_count} FAIL")
        print(f"   Average Score: {avg_score:.1f}/100\n")
    
    def _generate_ticket(self, filename: str, analysis: Dict) -> None:
        """
        Generate a bug ticket for documentation issues.
        
        Args:
            filename: Name of the analyzed file
            analysis: Analysis results containing issues
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ticket_id = f"DOC_{Path(filename).stem}_{timestamp}"
        
        status = analysis.get("status", "UNKNOWN")
        score = analysis.get("quality_score", 0)
        issues = analysis.get("issues", ["No specific issues identified"])
        recommendations = analysis.get("recommendations", ["Review and improve documentation"])
        
        ticket_content = f"""---
ticket_id: {ticket_id}
severity: {status}
category: documentation_quality
file: {filename}
score: {score}/100
status: open
created: {datetime.now().isoformat()}
---

# Documentation Issue: {filename}

## Summary
Quality score: **{score}/100** ({status})

## Issues Found

"""
        for i, issue in enumerate(issues, 1):
            ticket_content += f"{i}. {issue}\n"
        
        ticket_content += f"""
## Detailed Scores

- Completeness: {analysis.get('completeness_score', 'N/A')}/100
- Accuracy: {analysis.get('accuracy_score', 'N/A')}/100
- Consistency: {analysis.get('consistency_score', 'N/A')}/100
- AI-Readability: {analysis.get('ai_readability_score', 'N/A')}/100

## Recommended Actions

"""
        for i, rec in enumerate(recommendations, 1):
            ticket_content += f"{i}. {rec}\n"
        
        ticket_content += f"""
## Context

File path: `{filename}`
Analyzed by: DocsDeepSupervisor
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---
*This ticket was auto-generated by the Documentation Deep Supervisor.*
"""
        
        ticket_file = self.tickets_dir / f"TICKET_{status}_{Path(filename).stem}.md"
        self._write_atomic(ticket_file, ticket_content)
        paranoid.log_file_interaction(str(ticket_file), "create_ticket", "SUCCESS")
    
    def _generate_intellectual_log(self, analyses: List[Dict], duration: float) -> None:
        """
        Generate intellectual log summary for this session.
        
        Args:
            analyses: List of analysis results
            duration: Total duration in seconds
        """
        pass_count = sum(1 for a in analyses if a.get("status") == "PASS")
        warn_count = sum(1 for a in analyses if a.get("status") == "WARN")
        fail_count = sum(1 for a in analyses if a.get("status") == "FAIL")
        
        scores = [a.get("quality_score", 0) for a in analyses if isinstance(a.get("quality_score"), (int, float))]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        log_content = f"""# Intellectual Log: docs_deep_supervisor

## Session Statistics
- **Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Duration**: {duration:.2f}s
- **Files Analyzed**: {len(analyses)}

## Results Summary
- ✅ PASS: {pass_count}
- ⚠️ WARN: {warn_count}
- ❌ FAIL: {fail_count}
- **Average Score**: {avg_score:.1f}/100

## Health Status
"""
        if avg_score >= 80:
            log_content += "🟢 GREEN - Documentation is healthy\n"
        elif avg_score >= 50:
            log_content += "🟡 YELLOW - Some issues need attention\n"
        else:
            log_content += "🔴 RED - Critical issues found\n"
        
        log_content += f"""
## Key Issues
"""
        # Collect top issues across all files
        all_issues = []
        for a in analyses:
            for issue in a.get("issues", []):
                all_issues.append(issue)
        
        for issue in all_issues[:10]:
            log_content += f"- {issue}\n"
        
        log_content += f"""
## Output
- QA Report: output/deep_supervision/QA_Report_*.md
- Tickets: {warn_count + fail_count} tickets generated
"""
        
        # Save intellectual log
        log_dir = self.root_dir / "logs" / "intellectual"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"docs_deep_supervisor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._write_atomic(log_file, log_content)
        
        paranoid.log_file_interaction(str(log_file), "save_intellectual_log", "SUCCESS")
    
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
            paranoid.error(f"Atomic write failed for {path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise


def main():
    """CLI entry point for the Documentation Deep Supervisor."""
    parser = argparse.ArgumentParser(
        description="Documentation Deep Supervisor - Vertical Analysis for Documentation Quality"
    )
    parser.add_argument(
        "--sample-size", "-s",
        type=int,
        default=20,
        help="Number of documentation files to analyze (default: 20)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Run supervisor
    supervisor = DocsDeepSupervisor()
    success = supervisor.run(sample_size=args.sample_size)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
