import os
import sys
import random
import logging
import argparse
from datetime import date, datetime, timedelta
from github import Github, GithubException, Auth
from dotenv import load_dotenv
import yaml
import json
import requests

load_dotenv()

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def load_state():
    with open("state.json", "r") as f:
        return json.load(f)

def save_state(state):
    with open("state.json", "w") as f:
        json.dump(state, f, indent=2)

def setup_logging(config):
    log_file = config["logging"]["log_file"]
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    level = getattr(logging, config["logging"]["level"])
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

def get_project_idea(config, created_projects):
    ideas = config["project_creator"]["project_ideas"]
    available = [i for i in ideas if i not in created_projects]
    if not available:
        available = ideas
    return random.choice(available)

def get_project_description(project_name):
    try:
        response = requests.get("https://api.quotable.io/random", timeout=5)
        if response.status_code == 200:
            quote = response.json().get("content", "")
            return f"A project called {project_name}. Inspired by: {quote}"
    except Exception:
        pass
    return f"A starter project for {project_name}. Built with automation."

def get_starter_files(project_name, language, description):
    if language == "python":
        return {
            "README.md": f"# {project_name}\n\n{description}\n\n## Setup\n```bash\npip install -r requirements.txt\npython main.py\n```\n",
            ".gitignore": "venv/\n__pycache__/\n*.pyc\n.env\n",
            "main.py": f'# {project_name}\n# {description}\n\ndef main():\n    print("Welcome to {project_name}")\n\nif __name__ == "__main__":\n    main()\n',
            "requirements.txt": "# Add your dependencies here\n"
        }
    elif language == "javascript":
        return {
            "README.md": f"# {project_name}\n\n{description}\n\n## Setup\n```bash\nnpm install\nnode index.js\n```\n",
            ".gitignore": "node_modules/\n.env\n*.log\n",
            "index.js": f'// {project_name}\n// {description}\n\nfunction main() {{\n    console.log("Welcome to {project_name}");\n}}\n\nmain();\n',
            "package.json": json.dumps({
                "name": project_name,
                "version": "1.0.0",
                "description": description,
                "main": "index.js",
                "scripts": {"start": "node index.js"},
                "keywords": [],
                "author": "",
                "license": "MIT"
            }, indent=2)
        }

def create_github_repo(g, project_name, description):
    user = g.get_user()
    repo = user.create_repo(
        name=project_name,
        description=description,
        private=False,
        auto_init=False
    )
    logging.info(f"Created repository: {repo.full_name}")
    return repo

def push_starter_files(repo, files):
    for filename, content in files.items():
        repo.create_file(filename, f"chore: add {filename}", content)
        logging.info(f"Added file: {filename}")

def run(force=False):
    config = load_config()
    setup_logging(config)
    logging.info("Project creator started...")

    if config.get("kill_switch", False):
        logging.warning("Kill switch is ON. Exiting.")
        return

    token = os.getenv("GITHUB_TOKEN")
    username = os.getenv("GITHUB_USERNAME")

    if not token or not username:
        logging.error("GITHUB_TOKEN or GITHUB_USERNAME missing in .env")
        sys.exit(1)

    state = load_state()
    today = str(date.today())
    last_run = state["project_creator"]["last_run_date"]
    created_projects = state["project_creator"]["created_projects"]

    interval = config["project_creator"]["simple_project_interval_days"]
    if last_run and not force:
        last_run_date = datetime.strptime(last_run, "%Y-%m-%d").date()
        next_run = last_run_date + timedelta(days=interval)
        if date.today() < next_run:
            logging.info(f"Next run scheduled for {next_run}. Use --force to override.")
            return

    try:
        g = Github(auth=Auth.Token(token))
        language = random.choice(config["project_creator"]["languages"])
        project_name = get_project_idea(config, created_projects)
        description = get_project_description(project_name)

        logging.info(f"Creating project: {project_name} ({language})")

        repo = create_github_repo(g, project_name, description)
        files = get_starter_files(project_name, language, description)
        push_starter_files(repo, files)

        state["project_creator"]["last_run_date"] = today
        state["project_creator"]["created_projects"].append(project_name)
        save_state(state)

        logging.info(f"Project '{project_name}' created successfully!")

    except GithubException as e:
        logging.error(f"GitHub API error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Bypass interval guard")
    args = parser.parse_args()
    run(force=args.force)