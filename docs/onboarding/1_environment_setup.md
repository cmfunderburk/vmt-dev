## Environment Setup

### System requirements
- Python 3.11 (recommended)
- macOS/Linux/WSL2 on Windows
- Git

### Create a virtual environment
```bash
cd vmt-dev
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\\Scripts\\activate # Windows PowerShell
python -V  # expect 3.11.x
```

### Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Verify installation
```bash
python -c "import pygame, PyQt6, yaml, numpy; print('ok')"
pytest -q
```

### IDE configuration
- Add `.` and `src/` to your workspace Python paths (pytest already does this for tests).
- Prefer imports without the `src.` prefix in tests (see project `README.md` testing section).

### Optional developer tools
- SQLite browser (DB Browser for SQLite)
- `ipython`, `black`, `ruff` (if you prefer local lint/format; project enforces clarity and determinism over tool-specific style)

### Troubleshooting
- If GUI fails to start, confirm PyQt6 is installed and your display environment is available.
- If tests fail nondeterministically, re-run with the same scenario/seed; determinism issues must be fixed before proceeding.


