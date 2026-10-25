# What goes on GitHub? — Aeron submission

**Public repository name:** `firstname-lastname`, replaced with your actual first and last names in lowercase, separated by a hyphen. Do not publish the weather data pack or your solution before the assignment deadline, per the brief.

## Required at repository root
- `checker.py` — one-command reusable checker (the critical requirement).
- `flags.csv` — output generated on the supplied pack; review it before upload.
- `report.html` — A4-printable one-page coordinator report.
- `DECISIONS.md` — **rewrite personally**, check evidence and the solar-noon calculation by hand; remove draft placeholders.
- `README.md` — **first four lines MUST be** full name, email, 3-minute recording link, `Run: python checker.py <pack_dir>`.
- `ai_logs/` — full, unedited exports of your actual AI conversations from first prompt onward. The included README placeholder does NOT satisfy this requirement.
- `tests/` and `requirements.txt` — tests and install instructions.

## Nice-to-have frontend files
- `app.py` — local dashboard; run with `python -m streamlit run app.py`.
- `generate_report.py` — printable report generator (currently has dataset-specific narrative; do not claim it generalizes as fully as checker.py).
- `FRONTEND_GUIDE.md`, `GITHUB_UPLOAD_GUIDE.md`, `VALIDATION.md`, `DATA_INVENTORY.csv`, `DEMO_SCRIPT.md` — supporting documentation.

## Do NOT upload
- **Original** `ridgeline_data_pack (2).zip`, raw `stations.csv`, `data/`, `gps/`, or `maintenance_log.md` from the private pack.
- `.venv/`, `__pycache__/`, downloaded ZIPs, secrets, personal tokens.
- Fabricated AI conversation exports, synthetic claims, or an invented video URL.

## Before pushing: command checklist
From the project folder:

```bash
python -m pytest -q
python checker.py "/Users/dhruv/Downloads/ridgeline_extracted"
python generate_report.py "/Users/dhruv/Downloads/ridgeline_extracted"
python -m streamlit run app.py
```

Review `flags.csv` and the report for consistency; also review `DECISIONS.md` yourself.

## Publishing once complete
Create a new empty **public** repository on GitHub using the required repository name; then from your project folder:

```bash
git init
git add checker.py tests/ requirements.txt .gitignore
git commit -m "Implement weather data quality checker and tests"
git add app.py generate_report.py flags.csv report.html README.md DECISIONS.md ai_logs/ FRONTEND_GUIDE.md GITHUB_UPLOAD_GUIDE.md VALIDATION.md DATA_INVENTORY.csv DEMO_SCRIPT.md
git status --short
git commit -m "Add coordinator report, reviewed findings and local dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/firstname-lastname.git
git push -u origin main
```

Before committing, inspect `git status --short` to ensure **no private weather source files** are staged. Replace placeholders and include your video and authentic `ai_logs/` files before the final push. Make truthful incremental commits only; do not backdate or fabricate history. No GitHub upload is performed by this ZIP.
