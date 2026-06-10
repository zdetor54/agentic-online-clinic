<!-- This project was generated from the [AI Specialist Template](https://github.com/bjss/ai-specialist-template)-->
# AI Specialist Project Template

> ⚠️ IMPORTANT: This template is a starting point, not a prescription.

Only firm recommendation is:  `use uv for internal projects`

Use it to kick off client, internal, or personal AI projects, but adapt it freely to suit your needs.
Most choices here are opinionated defaults, not requirements. Use your best judgement.

This template should evolve over time. If something feels off, missing, or overly rigid, open a PR and help improve it for everyone.

## 🚀 Quick Start

You can also select this template from the “Use this template” button when creating new repos on [github.com](https://github.com)

```bash
# Clone & enter project (or use GitHub online UI)
git clone https://github.com/bjss/ai-specialist-template.git my-project
cd my-project

# Setup secrets (manually edit .env file afterwards)
# Your .env file will be specific for your project, so change as you need it
cp .env.example .env

# Run Streamlit app (uv creates your .venv for you)
uv run streamlit run ui/app.py

# Optional one-off developer setup
uv run pre-commit install            # Enable git hooks
./scripts/uv_dependency_relock.sh    # Update all packages to latest

streamlit run .\ui\clinic.py
```

## Overview

Standardised, production-ready template for AI/ML projects at BJSS/CGI. Follows best practices and modern Python tooling.

Docs & Standards: [AI Specialists SharePoint](https://bjss.sharepoint.com/sites/AISpecialists/SitePages/Python-Coding-Standards.aspx).

## ✨ Key Features

* **Dependency & env management** using [UV](https://docs.astral.sh/uv/)
  * If you are migrating from `poetry` you can simply run `uvx migrate-to-uv` to change your project to use uv
* **Strict linting & formatting** with [Ruff](https://docs.astral.sh/ruff/) and **static typing** via [TY](https://docs.astral.sh/ty/)
  * Uses strict but sensible defaults — [full rule list](https://docs.astral.sh/ruff/rules/)
  * Feel free to add/remove/ignore linting rules in `pyproject.toml` to fit your project and your preferred style.
* **Modern logging** with [Loguru](https://github.com/Delgan/loguru)
  * Template includes optional function for rotating file logs in `logs/` folder
* **Pre-commit hooks** via [Pre-commit](https://pre-commit.com/):
  * linting, formatting, type checks, notebook cleanup (`nbstripout`), safety checks
* **Typed, validated config/secrets** with [pydantic](https://docs.pydantic.dev/latest) and [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings):
  * Loads `.env` and `configs/config.yaml` into structured Pydantic objects
* **Streamlit** for quick experimentation and demos
* **Project layout**: all code lives in `src/` and is treated as a proper Python package
  * Supports editable installs and clean imports like `from src.llm import ...`
* **Lightweight CI**: lint + unit tests

## 📁 Key Files

* `ui/app.py`: Example Streamlit app using config/env
* `src/core/config.py`: Reads `configs/config.yaml` into pydantic object
  * Example: paths, name of LLM/Embedding/ML model to use, flags to turn functionality on/off, default values.
* `src/core/env.py`: Reads `.env` into pydantic object
  * Example: API keys, database passwords
* `src/core/logger.py`: How to persist `loguru` logs to file with rotation
* `.pre-commit-config.yaml`: Code quality hooks
* `.github/workflows/ci.yaml`: CI pipeline
* `scripts/uv_dependency_relock.sh`: Bash script to upgrade all uv packages to latest


## ✅ First time setup Checklist

* (Optional) Run `./scripts/uv_dependency_relock.sh`
  * This auto-update all packages in `pyproject.toml` to the latest versions
* Manually update `pyproject.toml`
  * Update the project name, author lists
  * Remove packages that you don't want
* Add new deps with `uv add` or `uv add --dev`
  * Use the `--dev` flag when adding packages that are not needed to run your code, but only for development. Things like jupyter, ruff, pytest.
* Edit `.env` and `.env.example`
  * Align `src/core/env.py` with `.env`/`.env.example`
* Edit `configs/config.yaml`
  * Align `src/core/config.py` with `configs/config.yaml`
! uv sync --python .venv\Scripts\python.exe (gettign errors without it)

Github settings suggestions:

* Protect `main` branch in GitHub.
  * Settings > Branches > Create new branch protection rule
  * You should never commit straight to the main branch, always use a PR.
* Change pull request defaults:
  * Settings > General > Pull Requests
  * Make sure these are ticked, and nothing else:
    * `Allow squash Merging`
    * `Always suggest updating pull request branches`
    * `Automatically delete head branches `
  * Under squash merging, change default commit message to `Pull request title and description`

## 📦 Install UV

**Mac/Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 🧱 Project Structure

```bash
.
├── .github/             # CI configs, PR templates
├── configs/             # YAML config
├── data/                # Raw or interim datasets (git-ignored)
├── docs/                # Project-level documentation
├── notebooks/           # Jupyter notebooks
├── plots/               # Generated plots (git-ignored)
├── scripts/             # Utility scripts and runners
├── src/                 # Core codebase
│   ├── ai.py            # Entrypoint or orchestration logic
│   ├── core/            # Config/env management
│   ├── llm/             # LLM-related modules
│   ├── plotting/        # Plotting utilities
│   ├── rag/             # Retrieval-augmented generation logic
│   └── utils/           # General utilities
├── tests/               # Unit tests
├── ui/                  # Streamlit UI or similar frontends
├── .env                 # Environment secrets (git-ignored)
├── pyproject.toml       # Project and tooling config
├── README.md            # Project overview
└── uv.lock              # Locked dependency versions
```

###  🚀 Useful UV Commands

```bash
# activate environment, but don't have to if you put `uv run ...` before your code
# for example, `uv run streamlit run ui/app.py`
source .venv/bin/activate

uv sync                      # Sync project dependencies (installs all, including dev by default)
uv sync --no-dev             # Sync only production dependencies (skip dev/test tools)
uv lock                      # Update lockfile (pin exact versions)
uv add pandas                # Add a new dependency (production)
uv add --dev pytest          # Add a new development-only dependency
uv run --no-sync python main.py  # Run your script with installed deps, skip re-sync
uv remove --dev pytest       # Remove a development dependency
uv remove pandas             # Remove a production dependency

# uv Python commands (not often needed),
# uv auto-installs necessary python versions based on the `.python-version` file
uv python list               # see list of installed python versions
uv python install 3.12.9     # installs specific version of python
```

## 🧪 Useful Dev commands

>NOTE: Pre-commit & CI pipeline runs all of these automatically

```bash
# Lint / Format (Ruff)
uv run ruff check .
uv run ruff check . --fix --unsafe-fixes
uv run ruff format .

# Type Check (Ty)
uv run ty check

# Pre-commit Hooks
uv run pre-commit run --all-files

# Tests
uv run pytest
```

### Update versions in pyproject.toml to the latest version

```bash
./scripts/uv_dependency_relock.sh
```


uv run uvicorn src.api.main:app --reload
uv run streamlit run .\ui\clinic.py
