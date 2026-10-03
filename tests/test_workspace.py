"""Tests for composed workspace and configuration context."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from forge.core.config import ForgeState, StateStore
from forge.core.environment import detect_environment
from forge.core.git import detect_git
from forge.core.workspace import WorkspaceContext, build_workspace_context


class WorkspaceTests(unittest.TestCase):
    def test_builds_workspace_context_for_project_metadata_and_venv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "demo"
            nested = root / "src"
            nested.mkdir(parents=True)
            (root / "Cargo.toml").touch()
            (root / ".venv").mkdir()
            context = build_workspace_context(nested)
            self.assertIsInstance(context, WorkspaceContext)
            self.assertEqual(context.project.project_root, root)
            self.assertIn("Cargo.toml", context.environment.indicators)
            self.assertEqual(context.environment.virtual_environment, root / ".venv")

    def test_detects_nested_repository_and_status_categories(self) -> None:
        if not shutil.which("git"):
            self.skipTest("Git is not installed")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-qm", "init"], check=True)
            (root / "staged.txt").write_text("stage")
            subprocess.run(["git", "-C", str(root), "add", "staged.txt"], check=True)
            (root / "modified.txt").write_text("before")
            subprocess.run(["git", "-C", str(root), "add", "modified.txt"], check=True)
            (root / "modified.txt").write_text("after")
            (root / "untracked.txt").write_text("new")
            nested = root / "a" / "b"
            nested.mkdir(parents=True)
            info = detect_git(nested).git
            self.assertIsNotNone(info)
            assert info is not None
            self.assertEqual(info.repository_root, root)
            self.assertFalse(info.detached_head)
            self.assertEqual(info.staged_files, ("modified.txt", "staged.txt"))
            self.assertEqual(info.modified_files, ("modified.txt",))
            self.assertEqual(info.untracked_files, ("untracked.txt",))

    def test_missing_git_is_graceful(self) -> None:
        with patch("forge.core.git.shutil.which", return_value=None):
            result = detect_git(Path.cwd())
        self.assertIsNone(result.git)
        self.assertFalse(result.git_available)

    def test_metadata_and_virtual_environment_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").touch()
            (root / "venv").mkdir()
            result = detect_environment(root)
            self.assertIn("package.json", result.indicators)
            self.assertEqual(result.virtual_environment, root / "venv")

    def test_malformed_configuration_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text("{broken", encoding="utf-8")
            state = StateStore(path).load()
            self.assertEqual(state, ForgeState())

    def test_configuration_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "state.json"
            store = StateStore(path)
            state = ForgeState("/workspace", ["/workspace"], {"theme": "dark"})
            store.save(state)
            self.assertEqual(store.load(), state)


if __name__ == "__main__":
    unittest.main()
