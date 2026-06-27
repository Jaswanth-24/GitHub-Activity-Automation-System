import os
import sys
import random
import logging
import argparse
from datetime import date
from github import Github, GithubException, Auth
from dotenv import load_dotenv
import yaml
import json

# ── Load environment & config ──────────────────────────────────────────────
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

# ── Logging setup ──────────────────────────────────────────────────────────
def setup_logging(config):
    log_file = config["logging"]["log_file"]
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    level = getattr(logging, config["logging"]["level"])
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

# ── Core logic ─────────────────────────────────────────────────────────────
def get_repos(github_client, username):
    user = github_client.get_user(username)
    repos = [
        r for r in user.get_repos()
        if not r.fork and not r.archived
    ]
    return repos

def select_repo(repos, last_repo):
    available = [r for r in repos if r.name != last_repo]
    if not available:
        available = repos
    return random.choice(available)

def make_commits(repo, config):
    target_file = config["github"]["target_file"]
    messages = config["github"]["commit_messages"]
    count = random.randint(
        config["github"]["commit_count_min"],
        config["github"]["commit_count_max"]
    )

    today = str(date.today())

    for i in range(count):
        message = random.choice(messages)
        content = f"[{today}] commit {i+1} - automated activity\n"

        try:
            file = repo.get_contents(target_file)
            existing = file.decoded_content.decode("utf-8")
            repo.update_file(
                target_file,
                message,
                existing + content,
                file.sha
            )
        except GithubException:
            repo.create_file(
                target_file,
                message,
                content
            )

        logging.info(f"Commit {i+1}/{count} made to {repo.name}: {message}")

def run(force=False):
    config = load_config()
    setup_logging(config)

    # Kill switch check
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
    last_run = state["daily_commit"]["last_run_date"]
    last_repo = state["daily_commit"]["last_repo"]

    # Idempotency check
    if last_run == today and not force:
        logging.info("Already ran today. Use --force to override.")
        return

    try:
        g = Github(auth = Auth.Token(token))
        repos = get_repos(g, username)

        if not repos:
            logging.error("No eligible repositories found.")
            return

        repo = select_repo(repos, last_repo)
        logging.info(f"Selected repo: {repo.name}")

        make_commits(repo, config)

        # Save state
        state["daily_commit"]["last_run_date"] = today
        state["daily_commit"]["last_repo"] = repo.name
        save_state(state)

        logging.info("Daily commit agent completed successfully.")

    except GithubException as e:
        logging.error(f"GitHub API error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Bypass once-per-day guard")
    args = parser.parse_args()
    run(force=args.force)