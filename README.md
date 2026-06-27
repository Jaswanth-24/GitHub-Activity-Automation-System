# GitHub Activity Automation System

A configurable automation system that keeps your GitHub profile active by making daily commits and periodically creating new starter projects — all via the GitHub REST API.

---

## Prerequisites

- Python 3.10+
- Git installed
- A GitHub account with a Personal Access Token

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/Jaswanth-24/GitHub-Activity-Automation-System.git
cd GitHub-Activity-Automation-System
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## API Key Setup

1. Go to [GitHub Settings](https://github.com/settings/tokens)
2. Click **Developer Settings** → **Personal Access Tokens** → **Tokens (classic)**
3. Click **Generate new token (classic)**
4. Give it a name, set expiration, check **`repo`** scope
5. Copy the token immediately

Create a `.env` file in the root folder:
```env
GITHUB_TOKEN=your_token_here
GITHUB_USERNAME=your_github_username
```

---

## Configuration Guide

All settings are in `config.yaml`:

| Key | Description | Default |
|-----|-------------|---------|
| `github.target_file` | File to commit to daily | `activity.log` |
| `github.commit_count_min` | Minimum commits per day | `1` |
| `github.commit_count_max` | Maximum commits per day | `3` |
| `github.commit_messages` | Pool of commit messages | 5 messages |
| `project_creator.languages` | Supported languages | `python, javascript` |
| `project_creator.simple_project_interval_days` | Days between new projects | `3` |
| `project_creator.project_ideas` | List of project names | 8 ideas |
| `kill_switch` | Set to `true` to stop all agents | `false` |
| `logging.log_file` | Log file path | `logs/automation.log` |
| `logging.level` | Log level | `INFO` |

---

## Running the Agents

### Daily Commit Agent
```bash
# Normal run (once per day)
python daily_commit.py

# Force run (bypass daily guard)
python daily_commit.py --force
```

### Project Creator Agent
```bash
# Normal run (respects interval)
python project_creator.py

# Force run (bypass interval)
python project_creator.py --force
```

## Running Tests

```bash
python test_agents.py
```

Tests cover:
- Idempotency logic — agent skips if already ran today
- Force flag — bypasses daily guard
- Repo selection — avoids last used repo
- Fallback — works with single repo
- Duplicate prevention — avoids already created projects

---

## Scheduling

### Windows (Task Scheduler)
1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Set trigger to **Daily**
4. Action: **Start a Program**
5. Program: `C:\path\to\venv\Scripts\python.exe`
6. Arguments: `C:\path\to\daily_commit.py`

### Linux/Mac (Cron)
```bash
crontab -e
# Add this line to run daily at 9am:
0 9 * * * /path/to/venv/bin/python /path/to/daily_commit.py
```

### GitHub Actions
Create `.github/workflows/daily.yml`:
```yaml
name: Daily Commit
on:
  schedule:
    - cron: '0 9 * * *'
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python daily_commit.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_USERNAME: ${{ secrets.GITHUB_USERNAME }}
```

---

## Kill Switch

To immediately stop both agents without crashing:

Open `config.yaml` and set:
```yaml
kill_switch: true
```

Both agents check this flag at startup and exit cleanly.

---

## Project Structure
GitHub-Activity-Automation-System/

├── daily_commit.py        # Bot 1 - makes daily commits

├── project_creator.py     # Bot 2 - creates new repos

├── test_agents.py         # Unit tests for idempotency and repo selection

├── config.yaml            # All configuration settings

├── state.json             # Tracks last run dates and repos

├── .env                   # GitHub token 

├── .gitignore             # Excludes secrets and temp files

├── requirements.txt       # Python dependencies

├── logs/                  # Log files directory

│   └── automation.log     # Combined log output

└── README.md  
   
---

## Troubleshooting

### 1. `GITHUB_TOKEN missing` error
- Make sure `.env` file exists in root folder
- Check token is not expired on GitHub
- Ensure no spaces around `=` in `.env`

### 2. `No eligible repositories found`
- Your GitHub account must have at least one non-forked, non-archived repo
- Check your token has `repo` scope enabled

### 3. `Already ran today` message
- This is normal — agent runs once per day
- Use `--force` flag to bypass: `python daily_commit.py --force`

### 4. `GitHub API error: 422`
- Repository name already exists on your account
- The project ideas list in `config.yaml` needs new unique names

### 5. Agent runs but no output
- Check `logs/automation.log` for details
- Make sure `kill_switch` is set to `false` in `config.yaml`

---

## Design Decisions

- **JSON file for state** — Simple, portable, no database setup needed
- **PyGithub library** — Cleaner than raw HTTP requests for GitHub API
- **Kill switch in config** — Easy to toggle without touching code
- **Idempotency** — Safe to run multiple times, no duplicate commits
- **Graceful fallback** — External API failure falls back to built-in list

---

## Data Persistence

State is stored in `state.json` which tracks:
- Last run date for each agent
- Last repository targeted by daily commit agent
- List of all projects created so far

This ensures idempotency across restarts.