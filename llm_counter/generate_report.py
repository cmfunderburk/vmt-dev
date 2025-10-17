#!/usr/bin/env python3
"""
Repository Token Analysis Report Generator
==========================================

Simple CLI command to run token analysis and generate a markdown report.
Can be dropped into any repository to analyze its token usage.

Usage:
    python3 generate_report.py [--output FILENAME] [--repo-name NAME]
    
Examples:
    python3 generate_report.py
    python3 generate_report.py --output custom_report.md
    python3 generate_report.py --repo-name "My Project"
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
import json
import subprocess

def detect_repo_name():
    """Detect the repository name from the parent directory."""
    # Get the parent directory of llm_counter (the repo root)
    repo_root = Path(__file__).parent.parent
    
    # Try to get from git config first
    try:
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True,
            text=True,
            cwd=repo_root,
            timeout=2
        )
        if result.returncode == 0:
            # Extract repo name from git URL
            url = result.stdout.strip()
            # Handle both HTTPS and SSH URLs
            repo_name = url.rstrip('/').split('/')[-1].replace('.git', '')
            if repo_name:
                return repo_name
    except Exception:
        pass
    
    # Fallback to directory name
    repo_name = repo_root.name
    return repo_name if repo_name else "Repository"

def run_full_analysis():
    """Run the full token counter with repotokens and capture its output."""
    try:
        # Get the repository root (parent of llm_counter)
        repo_root = Path(__file__).parent.parent
        
        # Run token_counter.py with JSON output
        cmd = [sys.executable, 'token_counter.py', '--format', 'json', '--repo-root', str(repo_root)]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode != 0:
            print(f"Error running token_counter.py: {result.stderr}")
            print("Falling back to demo version...")
            return run_demo_analysis()
        
        if not result.stdout.strip():
            print("Warning: token_counter.py returned empty output")
            print(f"stderr: {result.stderr}")
            print("Falling back to demo version...")
            return run_demo_analysis()
            
        # Parse JSON output
        try:
            analysis_data = json.loads(result.stdout)
            analysis_data['analysis_method'] = 'full'
            return analysis_data
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from token_counter.py: {e}")
            print(f"Output was: {result.stdout[:500]}")
            print("Falling back to demo version...")
            return run_demo_analysis()
        
    except Exception as e:
        print(f"Failed to run full analysis: {e}")
        print("Falling back to demo version...")
        return run_demo_analysis()

def run_demo_analysis():
    """Run the demo counter and capture its output as structured data."""
    try:
        # Get the repository root (parent of llm_counter)
        repo_root = Path(__file__).parent.parent
        
        # Run demo_counter.py and capture output
        result = subprocess.run([
            sys.executable, 'demo_counter.py', '--json', '--repo-root', str(repo_root)
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode != 0:
            print(f"Error running demo_counter.py: {result.stderr}")
            return None
            
        # Parse JSON output
        analysis_data = json.loads(result.stdout)
        analysis_data['analysis_method'] = 'demo'
        return analysis_data
        
    except Exception as e:
        print(f"Failed to run analysis: {e}")
        return None

def format_number(num):
    """Format numbers with appropriate suffixes."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)

def format_percentage(value, total):
    """Format percentage with one decimal place."""
    if total == 0:
        return "0.0%"
    return f"{(value / total * 100):.1f}%"

def generate_recommendations(total_tokens, by_type):
    """Generate context-aware recommendations based on token count."""
    
    # Define context windows for reference
    context_windows = {
        'GPT-4': 128_000,
        'Claude 3/3.5': 200_000,
        'Gemini 1.5 Pro': 1_000_000
    }
    
    # Calculate documentation percentage
    doc_tokens = by_type.get('Markdown', {}).get('tokens', 0)
    doc_percentage = format_percentage(doc_tokens, total_tokens)
    
    recommendations = "### Recommendations\n\n"
    
    # Determine which models can handle full repo
    fits_in = []
    for model, window in context_windows.items():
        if total_tokens <= window * 0.8:  # Leave 20% margin for prompts/responses
            fits_in.append(f"{model} (~{format_number(window)})")
    
    if not fits_in:
        # Very large repository - needs chunking for all models
        recommendations += f"- **Full Repository**: {format_number(total_tokens)} tokens requires chunking for all LLMs\n"
        recommendations += f"- **Recommended Approach**: Use hierarchical analysis - start with file structure, then dive into specific areas\n"
        recommendations += f"- **Chunking Strategy**: Process 25-50% of files at a time based on functional areas\n"
    elif total_tokens < 50_000:
        # Small repository - fits easily in all modern LLMs
        recommendations += f"- **Full Repository**: {format_number(total_tokens)} tokens fits comfortably in all modern LLM context windows\n"
        recommendations += f"- **Single-Context Analysis**: Entire codebase can be analyzed in one prompt\n"
        recommendations += f"- **Recommended Models**: {', '.join(fits_in)}\n"
    elif total_tokens < 150_000:
        # Medium repository - fits in most modern LLMs
        recommendations += f"- **Full Repository**: {format_number(total_tokens)} tokens fits in: {', '.join(fits_in)}\n"
        recommendations += f"- **Single-Context Analysis**: Entire codebase can be analyzed without chunking\n"
        if total_tokens > 100_000:
            recommendations += f"- **Tip**: For faster processing, consider focused analysis on specific modules\n"
    else:
        # Large repository - fits in some LLMs
        recommendations += f"- **Full Repository**: {format_number(total_tokens)} tokens fits in: {', '.join(fits_in)}\n"
        recommendations += f"- **Targeted Analysis**: Consider focusing on 40-60% of files for detailed reviews\n"
        if total_tokens > 500_000:
            recommendations += f"- **Performance Note**: Even with large context windows, processing this size may be slow\n"
    
    # Add code review recommendation
    recommendations += f"- **Code Reviews**: Use token counts to prioritize which files/modules to include\n"
    
    # Add documentation note if significant
    if doc_tokens > 0:
        if doc_tokens > total_tokens * 0.15:
            recommendations += f"- **Documentation**: {doc_percentage} of tokens are documentation (substantial docs available)\n"
        else:
            recommendations += f"- **Documentation**: {doc_percentage} of tokens are documentation\n"
    
    return recommendations

def generate_markdown_report(analysis_data, repo_name="Repository"):
    """Generate a markdown report from analysis data."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    analysis_method = analysis_data.get('analysis_method', 'demo')
    
    # Extract data
    summary = analysis_data.get('summary', {})
    by_type = analysis_data.get('by_file_type', {})
    top_files = analysis_data.get('top_files', [])
    
    total_tokens = summary.get('total_tokens', 0)
    total_files = summary.get('total_files', 0)
    total_size = summary.get('total_size_mb', 0)
    avg_tokens = summary.get('average_tokens_per_file', 0)
    
    report = f"""# {repo_name} - Token Analysis Report

*Generated on {timestamp}*

## 📊 Executive Summary

| Metric | Value |
|--------|--------|
| **Total Tokens** | {format_number(total_tokens)} tokens |
| **Total Files** | {total_files:,} files |
| **Repository Size** | {total_size:.1f} MB |
| **Average Tokens/File** | {avg_tokens:.0f} tokens |

## 📄 File Type Breakdown

"""

    # Add file type breakdown table
    if by_type:
        report += "| File Type | Token Count | Percentage | Files |\n"
        report += "|-----------|-------------|------------|-------|\n"
        
        # Sort by token count (descending)
        sorted_types = sorted(by_type.items(), key=lambda x: x[1]['tokens'], reverse=True)
        
        for file_type, data in sorted_types:
            tokens = data.get('tokens', 0)
            files = data.get('files', 0)
            percentage = format_percentage(tokens, total_tokens)
            
            report += f"| {file_type} | {format_number(tokens)} | {percentage} | {files} |\n"

    # Add top files section
    if top_files:
        report += f"\n## 🔥 Top {len(top_files)} Largest Files\n\n"
        report += "| File | Tokens | Size |\n"
        report += "|------|--------|------|\n"
        
        for file_info in top_files:
            path = file_info.get('path', 'Unknown')
            tokens = file_info.get('tokens', 0)
            size_mb = file_info.get('size_mb', 0)
            
            # Truncate long paths
            display_path = path
            if len(path) > 60:
                display_path = "..." + path[-57:]
            
            report += f"| `{display_path}` | {format_number(tokens)} | {size_mb:.1f} MB |\n"

    # Add context interpretation
    report += f"""

## 🤖 LLM Context Analysis

### Context Window Compatibility

| Model | Context Window | Repo Coverage |
|-------|---------------|---------------|
| GPT-4 | ~128K tokens | {format_percentage(128_000, total_tokens)} |
| Claude 3 | ~200K tokens | {format_percentage(200_000, total_tokens)} |
| Claude 3.5 Sonnet | ~200K tokens | {format_percentage(200_000, total_tokens)} |
| Gemini 1.5 Pro | ~1M tokens | {format_percentage(1_000_000, total_tokens)} |

{generate_recommendations(total_tokens, by_type)}

## 📈 Analysis Metadata

- **Analysis Tool**: Repository Token Counter ({'full version with repotokens' if analysis_method == 'full' else 'demo version'})
- **Tokenization**: {'Accurate repotokens library' if analysis_method == 'full' else 'Simple estimation (~1.3 tokens/word)'}
- **Files Processed**: {total_files:,} code files
- **Excluded**: Binary files, caches, logs, virtual environments
- **Repository**: {repo_name}

---

*This report was automatically generated by the Repository Token Counter.*
"""

    return report

def main():
    parser = argparse.ArgumentParser(description="Generate repository token analysis markdown report")
    parser.add_argument(
        '--output', '-o',
        default='token_report.md',
        help='Output markdown file name (default: token_report.md)'
    )
    parser.add_argument(
        '--repo-name', '-r',
        help='Repository name (auto-detected if not provided)'
    )
    parser.add_argument(
        '--timestamp', '-t',
        action='store_true',
        help='Add timestamp to output filename'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        default=True,
        help='Use full token counter with repotokens (default: True)'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Use demo version instead of full counter'
    )
    
    args = parser.parse_args()
    
    # Detect or use provided repository name
    repo_name = args.repo_name if args.repo_name else detect_repo_name()
    
    # Generate output filename with optional timestamp
    output_filename = args.output
    if args.timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(output_filename).stem
        extension = Path(output_filename).suffix
        output_filename = f"{base_name}_{timestamp}{extension}"
    
    print(f"🔍 Running token analysis for {repo_name}...")
    
    # Run analysis (full or demo)
    if args.demo:
        analysis_data = run_demo_analysis()
    else:
        analysis_data = run_full_analysis()
    
    if not analysis_data:
        print("❌ Failed to run token analysis")
        sys.exit(1)
    
    print("📄 Generating markdown report...")
    
    # Generate report
    report_content = generate_markdown_report(analysis_data, repo_name)
    
    # Write to file
    output_path = Path(__file__).parent / output_filename
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Report generated successfully!")
        print(f"📁 Output: {output_path}")
        print(f"📊 Summary: {analysis_data['summary']['total_tokens']:,} tokens across {analysis_data['summary']['total_files']:,} files")
        
    except Exception as e:
        print(f"❌ Failed to write report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()