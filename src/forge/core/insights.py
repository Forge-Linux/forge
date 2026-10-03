"""Deterministic, read-only observations derived from workspace context."""

from __future__ import annotations

from dataclasses import dataclass

from forge.core.workspace import WorkspaceContext


@dataclass(frozen=True)
class WorkspaceInsight:
    """An actionable observation with a stable identifier for the UI."""

    identifier: str
    title: str
    detail: str
    tone: str = "info"
    action_id: str | None = None


def analyze_workspace(context: WorkspaceContext) -> tuple[WorkspaceInsight, ...]:
    """Build concise insights without running commands or modifying the project."""
    insights: list[WorkspaceInsight] = []
    project = context.project
    git = context.git

    if project.project_root is None:
        insights.append(WorkspaceInsight(
            "project-missing", "Choose a project", "Forge could not read the current project path.",
            "warning", "open_project",
        ))
        return tuple(insights)

    if git is None:
        if project.git_available:
            insights.append(WorkspaceInsight(
                "git-missing", "No Git repository", "Open or initialize a repository to enable Git actions.",
                "info",
            ))
        else:
            insights.append(WorkspaceInsight(
                "git-unavailable", "Git is not installed", "Git-aware actions are unavailable on this system.",
                "warning",
            ))
    else:
        if git.is_clean is False:
            insights.append(WorkspaceInsight(
                "git-changes", f"{git.changed_files} pending change(s)",
                f"{len(git.staged_files)} staged · {len(git.modified_files)} modified · "
                f"{len(git.untracked_files)} untracked", "warning", "review_diff",
            ))
        elif git.is_clean is True:
            insights.append(WorkspaceInsight(
                "git-clean", "Working tree is clean", f"On {git.current_branch or 'detached HEAD'}.", "success",
            ))
        if git.behind:
            insights.append(WorkspaceInsight(
                "git-behind", f"{git.behind} commit(s) behind upstream",
                "Your branch has commits available from its upstream.", "warning",
            ))
        if git.ahead:
            insights.append(WorkspaceInsight(
                "git-ahead", f"{git.ahead} commit(s) ahead of upstream",
                "Your local commits have not been pushed yet.", "info",
            ))

    indicators = context.environment.indicators
    if not indicators:
        insights.append(WorkspaceInsight(
            "metadata-missing", "No development metadata found",
            "Add a project manifest such as pyproject.toml, package.json, Cargo.toml, or go.mod.", "info",
        ))
    if context.environment.virtual_environment:
        active = context.environment.active_virtual_environment
        root_env = context.environment.virtual_environment
        details = f"Python environment found at {root_env}"
        if active and active != root_env:
            details += f" · active environment: {active}"
        insights.append(WorkspaceInsight("python-env", "Python environment detected", details, "success"))
    if not (project.project_root / "README.md").is_file() and not (project.project_root / "README.rst").is_file():
        insights.append(WorkspaceInsight(
            "readme-missing", "Project has no README", "A README can help document setup and common commands.", "info",
        ))

    return tuple(insights)
