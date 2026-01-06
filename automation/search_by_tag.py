#!/usr/bin/env python3
"""
Tag Search Tool - Find files by semantic tags

<!--TAG:tool_search_by_tag-->

PURPOSE:
    Searches for files containing specific semantic tags.
    Resilient to line shifts and code changes.
    Supports listing all available tags.

DOCUMENTATION:
    Spec: docs/specs/Automation_Tools_Spec.md
    Wiki: docs/wiki/09_Documentation_System.md
    Dependencies: docs/memory/dependencies/search_by_tag_dependencies.json

DEPENDENCIES (Quick Reference):
    Code:
        - docs.utils.docs_logger (DocsLogger for isolated logging)
    Config:
        - None (standalone tool)
    Data:
        - Input: docs/, processing/, utils/, scripts/ directories
        - Output: stdout or specified output file
    External:
        - None

RECENT CHANGES:
    2025-12-12: Migrated from utils.paranoid_logger to docs.utils.docs_logger
                for NSS-DOCS isolation (see developer_diary/20251212_docs_autonomy.md)

TAGS: <!--TAG:component:automation--> <!--TAG:type:script--> <!--TAG:feature:search--> <!--TAG:automation--> <!--TAG:search--> <!--TAG:tags-->

USAGE:
    python3 search_by_tag.py --tag component_name
    python3 search_by_tag.py --tag feature_entropy --show-context

<!--/TAG:tool_search_by_tag-->
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
# Add project root to Python path for portable imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.docs_logger import DocsLogger

logger = DocsLogger("search_by_tag")

@dataclass
class TagMatch:
    """A match for a semantic tag"""
    tag: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    context_before: str = ""
    context_after: str = ""

class TagSearcher:
    """Search for semantic tags in documentation"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    def search(self, tag: str, include_context: bool = False) -> List[TagMatch]:
        """Search for a tag across all documentation"""
        matches = []
        
        # Search in docs directory
        docs_dir = self.project_root / 'docs'
        for file_path in docs_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.md', '.py', '.yaml', '.yml']:
                file_matches = self._search_file(file_path, tag, include_context)
                matches.extend(file_matches)
        
        # Search in code directories
        for code_dir in ['processing', 'utils', 'scripts']:
            code_path = self.project_root / code_dir
            if code_path.exists():
                for file_path in code_path.rglob('*.py'):
                    file_matches = self._search_file(file_path, tag, include_context)
                    matches.extend(file_matches)
        
        return matches
    
    def _search_file(self, file_path: Path, tag: str, include_context: bool) -> List[TagMatch]:
        """Search for tag in a single file.
        
        Algorithm:
            1. Read file content as UTF-8
            2. Build opening and closing tag patterns
            3. Iteratively find all tag pairs
            4. Extract content and calculate line numbers
            5. Optionally extract surrounding context
        """
        matches = []  # Accumulator for all tag matches found in this file
        
        try:
            # Open file in read mode with UTF-8 encoding to handle international characters
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()  # Read entire file content into memory for searching
            
            # Build tag patterns using HTML comment format for semantic tagging
            opening_tag = f"<!--TAG:{tag}-->"  # Opening semantic tag marker
            closing_tag = f"<!--/TAG:{tag}-->"  # Closing semantic tag marker
            
            # Iterative search for all occurrences of the tag in the file
            # We use a while loop to find multiple tag pairs in the same file
            start_pos = 0  # Current search position in content string
            while True:
                # Find next opening tag after current position
                start_idx = content.find(opening_tag, start_pos)
                if start_idx == -1:  # No more opening tags found - exit loop
                    break
                
                # Find matching closing tag after the opening tag
                end_idx = content.find(closing_tag, start_idx)
                if end_idx == -1:  # Unclosed tag detected - malformed document
                    logger.warning(f"Unclosed tag {tag} in {file_path}")
                    break  # Stop searching this file to avoid incorrect matches
                
                # Extract content between opening and closing tags
                # Add length of opening tag to skip past it
                tag_content = content[start_idx + len(opening_tag):end_idx].strip()
                
                # Calculate line numbers by counting newlines before tag positions
                # Line numbers are 1-indexed (first line is line 1, not 0)
                start_line = content[:start_idx].count('\n') + 1  # Line where opening tag appears
                end_line = content[:end_idx].count('\n') + 1  # Line where closing tag appears
                
                # Extract context lines if requested via --show-context flag
                context_before = ""  # Lines before the tag (for context)
                context_after = ""  # Lines after the tag (for context)
                if include_context:
                    lines = content.split('\n')  # Split content into individual lines
                    # Get 3 lines before the tag (or fewer if near start of file)
                    context_before = '\n'.join(lines[max(0, start_line-4):start_line-1])
                    # Get 3 lines after the tag (or fewer if near end of file)
                    context_after = '\n'.join(lines[end_line:min(len(lines), end_line+3)])
                
                # Create TagMatch object with all extracted information
                match = TagMatch(
                    tag=tag,  # The tag we searched for
                    file_path=str(file_path.relative_to(self.project_root)),  # Relative path for readability
                    start_line=start_line,  # Starting line number
                    end_line=end_line,  # Ending line number
                    content=tag_content,  # Content between tags
                    context_before=context_before,  # Optional context before
                    context_after=context_after  # Optional context after
                )
                matches.append(match)  # Add match to results list
                
                # Move search position past the current closing tag to find next occurrence
                start_pos = end_idx + len(closing_tag)
        
        except Exception as e:
            # Log any file reading errors with context for debugging
            logger.error(f"Error reading {file_path}: {e}")
        
        return matches  # Return all matches found in this file (may be empty list)
    
    def find_all_tags(self) -> List[str]:
        """Find all unique tags in the project.
        
        Scans all documentation and code files to extract semantic tags.
        Returns sorted list of unique tag identifiers.
        """
        tags = set()  # Use set to automatically deduplicate tag names
        
        # Search all relevant directories for tag definitions
        for root_dir in [self.project_root / 'docs', 
                         self.project_root / 'processing',
                         self.project_root / 'utils']:
            if not root_dir.exists():  # Skip if directory doesn't exist
                continue
            
            # Recursively scan all files in this directory tree
            for file_path in root_dir.rglob('*'):
                if file_path.is_file():  # Only process files, not directories
                    try:
                        # Read file content to search for tag patterns
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()  # Full file content
                        
                        # Find all opening tags using regex pattern
                        # Pattern matches: <!--TAG:tag_name--> where tag_name is alphanumeric + underscores
                        tag_pattern = r'<!--TAG:([a-zA-Z0-9_]+)-->'
                        found_tags = re.findall(tag_pattern, content)  # Extract all tag names
                        
                        # Add all found tags to the set (duplicates automatically ignored)
                        tags.update(found_tags)
                    
                    except Exception as e:  # Catch file reading errors (permissions, encoding, etc.)
                        # Silently skip files that can't be read (binary files, permission issues)
                        # We don't log here to avoid spam from binary files
                        pass
        
        return sorted(list(tags))  # Return alphabetically sorted list of unique tags

def main():
    """Main entry point for tag search CLI tool."""
    import argparse
    
    # Set up command-line argument parser with description
    parser = argparse.ArgumentParser(description='Search documentation by semantic tags')
    parser.add_argument('--tag', type=str, help='Tag to search for')
    parser.add_argument('--list-tags', action='store_true', help='List all available tags')
    parser.add_argument('--show-context', action='store_true', help='Show context around matches')
    parser.add_argument('--output', type=str, help='Save results to file')
    
    args = parser.parse_args()  # Parse command-line arguments
    
    # Detect project root from script location (3 levels up: automation/ -> docs/ -> project/)
    project_root = Path(__file__).parent.parent
    searcher = TagSearcher(project_root)  # Initialize searcher with project root
    
    # Handle --list-tags mode: show all available tags and exit
    if args.list_tags:
        print("Available tags:")
        tags = searcher.find_all_tags()  # Scan project for all tag definitions
        for tag in tags:
            print(f"  - {tag}")  # Print each tag with bullet point
        return  # Exit after listing tags
    
    # Validate that --tag argument was provided (required for search mode)
    if not args.tag:
        parser.print_help()  # Show usage information
        return  # Exit if no tag specified
    
    # Execute tag search across all documentation and code files
    matches = searcher.search(args.tag, args.show_context)
    
    # Handle case where no matches found
    if not matches:
        print(f"No matches found for tag: {args.tag}")
        return  # Exit if no results
    
    # Format output as human-readable text with separators
    output = []  # Accumulator for output lines
    logger.info(f"Found {len(matches)} match(es) for tag: {args.tag}")
    output.append(f"Found {len(matches)} match(es) for tag: {args.tag}\n")
    output.append("=" * 60)  # Header separator
    
    # Format each match with file path, line range, and content
    for i, match in enumerate(matches, 1):
        output.append(f"\n[{i}] {match.file_path} (lines {match.start_line}-{match.end_line})")
        output.append("-" * 60)  # Match separator
        
        # Show context before tag if --show-context flag was used
        if match.context_before and args.show_context:
            output.append("\n... context before ...")
            output.append(match.context_before)
            output.append("")  # Blank line for readability
        
        # Show main tag content
        output.append(match.content)
        
        # Show context after tag if --show-context flag was used
        if match.context_after and args.show_context:
            output.append("")  # Blank line for readability
            output.append("... context after ...")
            output.append(match.context_after)
        
        output.append("")  # Blank line between matches
    
    result = '\n'.join(output)  # Combine all output lines into single string
    
    # Output results: either save to file or print to stdout
    if args.output:
        output_path = project_root / args.output  # Resolve output path relative to project root
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)  # Write formatted results to file
        logger.info(f"Results saved to: {output_path}")
    else:
        print(result)  # Print results to console

if __name__ == '__main__':
    main()
