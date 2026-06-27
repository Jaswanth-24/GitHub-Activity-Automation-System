import unittest
import json
import os
from unittest.mock import MagicMock, patch
from datetime import date

# ── Test Daily Commit Agent ────────────────────────────────────────────────

class TestIdempotency(unittest.TestCase):

    def test_already_ran_today_skips(self):
        from daily_commit import run
        
        # Set state to today
        state = {
            "daily_commit": {
                "last_run_date": str(date.today()),
                "last_repo": "some-repo"
            },
            "project_creator": {
                "last_run_date": None,
                "created_projects": []
            }
        }
        with open("state.json", "w") as f:
            json.dump(state, f)

        with patch("daily_commit.Github"), \
             patch("daily_commit.get_repos") as mock_repos, \
             patch("daily_commit.make_commits") as mock_commits:
            
            run(force=False)
            
            # Should NOT make any commits
            mock_commits.assert_not_called()
            print("Idempotency test passed — skipped when already ran today")

    def test_force_flag_bypasses_idempotency(self):
        """Force flag should bypass the once-per-day guard"""
        from daily_commit import run

        state = {
            "daily_commit": {
                "last_run_date": str(date.today()),
                "last_repo": "some-repo"
            },
            "project_creator": {
                "last_run_date": None,
                "created_projects": []
            }
        }
        with open("state.json", "w") as f:
            json.dump(state, f)

        mock_repo = MagicMock()
        mock_repo.name = "test-repo"

        with patch("daily_commit.Github"), \
             patch("daily_commit.get_repos", return_value=[mock_repo]), \
             patch("daily_commit.select_repo", return_value=mock_repo), \
             patch("daily_commit.make_commits") as mock_commits, \
             patch("daily_commit.save_state"):

            run(force=True)
            mock_commits.assert_called_once()
            print("Force flag test passed — ran despite already ran today")


# ── Test Repo Selection ────────────────────────────────────────────────────

class TestRepoSelection(unittest.TestCase):

    def test_avoids_last_repo(self):
        """Should not select the same repo as last time"""
        from daily_commit import select_repo

        repo1 = MagicMock()
        repo1.name = "repo-one"
        repo2 = MagicMock()
        repo2.name = "repo-two"

        repos = [repo1, repo2]

        # Run 10 times — should never pick repo-one
        for _ in range(10):
            selected = select_repo(repos, "repo-one")
            self.assertNotEqual(selected.name, "repo-one")
        
        print("Repo selection test passed — avoided last repo")

    def test_falls_back_when_only_one_repo(self):
        """Should still work when only one repo exists"""
        from daily_commit import select_repo

        repo1 = MagicMock()
        repo1.name = "only-repo"

        repos = [repo1]
        selected = select_repo(repos, "only-repo")
        self.assertEqual(selected.name, "only-repo")
        print("Fallback test passed — used only available repo")

    def test_selects_from_available_repos(self):
        """Should select a repo from the list"""
        from daily_commit import select_repo

        repo1 = MagicMock()
        repo1.name = "repo-one"
        repo2 = MagicMock()
        repo2.name = "repo-two"
        repo3 = MagicMock()
        repo3.name = "repo-three"

        repos = [repo1, repo2, repo3]
        selected = select_repo(repos, None)
        self.assertIn(selected.name, ["repo-one", "repo-two", "repo-three"])
        print("Selection test passed — selected valid repo")


# ── Test Project Duplicate Prevention ─────────────────────────────────────

class TestDuplicatePrevention(unittest.TestCase):

    def test_avoids_duplicate_projects(self):
        """Should not create already created projects"""
        from project_creator import get_project_idea

        config = {
            "project_creator": {
                "project_ideas": ["todo-cli", "weather-fetcher", "expense-tracker"]
            }
        }
        created = ["todo-cli", "weather-fetcher"]

        # Run 10 times — should always pick expense-tracker
        for _ in range(10):
            idea = get_project_idea(config, created)
            self.assertEqual(idea, "expense-tracker")
        
        print("Duplicate prevention test passed — avoided created projects")


if __name__ == "__main__":
    unittest.main(verbosity=2)