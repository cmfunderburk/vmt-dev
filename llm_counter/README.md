# Repository Token Counter

A portable toolkit for analyzing token counts in any code repository. Drop this folder into your project to estimate LLM context window usage.

## ✨ Features

- **Accurate Token Counting**: Uses OpenAI's `tiktoken` library via `repotokens`
- **Portable**: Drop into any repository - auto-detects repo name and structure
- **Beautiful Output**: Rich terminal UI with tables and progress indicators
- **Multiple Formats**: JSON, table, and summary views
- **Markdown Reports**: Auto-generates comprehensive analysis reports
- **Smart Filtering**: Excludes venv, node_modules, caches, logs, etc.

## 🚀 Quick Start

### 1. Setup (One-time)

```bash
cd llm_counter
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Analyze Your Repository

```bash
# Activate the virtual environment
source venv/bin/activate

# Run quick analysis
python token_counter.py

# Generate markdown report
python generate_report.py

# View detailed breakdown
python token_counter.py --by-directory --by-filetype
```

## 📊 Usage Examples

### Basic Token Analysis

```bash
# Summary view (default)
python token_counter.py

# JSON output for scripting
python token_counter.py --format json

# Show top 20 largest files
python token_counter.py --top-files 20
```

### Generate Reports

```bash
# Generate markdown report (auto-detects repo name)
python generate_report.py

# Custom repo name
python generate_report.py --repo-name "My Amazing Project"

# Add timestamp to filename
python generate_report.py --timestamp

# Custom output file
python generate_report.py --output my_analysis.md
```

### Advanced Options

```bash
# Analyze from different root
python token_counter.py --repo-root /path/to/repo

# Group by directory
python token_counter.py --by-directory

# Group by file type
python token_counter.py --by-filetype

# Save to file
python token_counter.py --output analysis.json --format json
```

## 🛠️ Installation in Another Repository

1. Copy the entire `llm_counter/` folder to your repository
2. Follow the Quick Start steps above
3. Run `python generate_report.py`

That's it! The tool auto-detects your repository name and structure.

## 📦 Dependencies

- `repotokens` - Accurate token counting using tiktoken
- `click` - Command-line interface
- `rich` - Beautiful terminal output

## 🎯 What Gets Analyzed?

**Included:**
- Source code: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.go`, etc.
- Documentation: `.md`, `.txt`, `.rst`
- Config files: `.json`, `.yaml`, `.toml`, `.ini`
- Build files: `Makefile`, `.sh`, `.bat`

**Excluded:**
- Virtual environments (`venv`, `node_modules`)
- Build artifacts (`__pycache__`, `.pytest_cache`)
- Version control (`.git`)
- Logs and data files (`*.log`, `*.jsonl`)
- Binary files

## 📈 Understanding the Output

### Token Count
- Uses OpenAI's tokenization (same as GPT models)
- Accurate for estimating LLM context window usage
- 1 token ≈ 0.75 words (English)

### Context Window Compatibility
The report shows what percentage of major LLM context windows your repo fills:
- **GPT-4**: ~128K tokens
- **Claude 3/3.5 Sonnet**: ~200K tokens
- **Gemini 1.5 Pro**: ~1M tokens

### Recommendations
- **< 100K tokens**: Can fit most of repo in one context
- **100K - 200K tokens**: Use Claude or chunk strategically  
- **> 200K tokens**: Need careful chunking for any LLM

## 🔧 Customization

Edit the exclusion patterns in `token_counter.py` if needed:

```python
self.exclude_patterns = [
    "__pycache__", ".git", ".pytest_cache", "node_modules", "venv",
    "logs", "*.log", "*.pyc", ...
]
```

## 🐛 Troubleshooting

**No files found?**
- Check that you're not accidentally excluding your files
- Verify the `--repo-root` path is correct
- Check `exclude_patterns` in `token_counter.py`

**Import errors?**
- Make sure the virtual environment is activated
- Run `pip install -r requirements.txt`

**Inaccurate counts?**
- Use `--format json` for exact numbers
- Demo version (`demo_counter.py`) uses estimation

## 📝 Output Files

- `token_report.md` - Generated markdown report (default name)
- Can customize with `--output` flag

## 🤝 Contributing

This is a standalone tool. Feel free to modify for your needs!

## 📄 License

Free to use and modify. Part of the larger project toolkit.
