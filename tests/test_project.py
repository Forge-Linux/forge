"""Tests for filesystem and Git project context detection."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from forge.core.project import detect_project


class DetectProjectTests(unittest.TestCase):
    def test_detects_project_from_nested_path_and_local_venv(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "sample"
            nested = root / "src" / "sample"
            nested.mkdir(parents=True)
            (root / "pyproject.toml").touch()
            (root / ".venv").mkdir()

            result = detect_project(nested)

            self.assertEqual(result.project_name, "sample")
            self.assertEqual(result.project_root, root)
            self.assertIn("pyproject.toml", result.project_files)
            self.assertEqual(result.virtual_environment, root / ".venv")

    def test_non_git_directory_returns_project_without_git_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "plain-project"
            root.mkdir()
            (root / "package.json").touch()

            result = detect_project(root)

            self.assertEqual(result.project_root, root)
            self.assertIn("package.json", result.project_files)
            self.assertIsNone(result.git)

    @unittest.skipUnless(shutil.which("git"), "Git is not installed")
    def test_reports_repository_branch_cleanliness_and_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "pyproject.toml").touch()

            clean_result = detect_project(root)
            self.assertIsNotNone(clean_result.git)
            assert clean_result.git is not None
            self.assertEqual(clean_result.git.repository_root, root)
            self.assertTrue(clean_result.git.current_branch)
            self.assertFalse(clean_result.git.is_clean)
            self.assertEqual(clean_result.git.changed_files, 1)

            subprocess.run(["git", "-C", str(root), "add", "pyproject.toml"], check=True)
            subprocess.run(
                ["git", "-C", str(root), "-c", "user.name=Forge Test", "-c",
                 "user.email=forge@example.invalid", "commit", "-qm", "initial"],
                check=True,
            )
            clean_result = detect_project(root)
            assert clean_result.git is not None
            self.assertTrue(clean_result.git.is_clean)
            self.assertEqual(clean_result.git.changed_files, 0)

            (root / "new-file.txt").write_text("untracked", encoding="utf-8")
            changed_result = detect_project(root)
            assert changed_result.git is not None
            self.assertFalse(changed_result.git.is_clean)
            self.assertEqual(changed_result.git.changed_files, 1)

    def test_missing_path_is_handled_gracefully(self) -> None:
        result = detect_project("/this/path/should/not/exist/forge-test")
        self.assertIsNone(result.project_root)
        self.assertIsNone(result.git)


if __name__ == "__main__":
    unittest.main()
