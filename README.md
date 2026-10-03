# Forge-Linux 

> **A developer-focused Linux desktop environment built around context, workflow, and an intelligent computer-side agent.**

Forge is an experimental Linux desktop environment focused on combining **power, usability, customization, and intelligent assistance** into one cohesive workspace.

Instead of treating an AI assistant as another application you open when you need it, Forge aims to make the computer itself **context-aware** — understanding the user's system, projects, workflow, and current task so it can assist without constantly interrupting the user's flow.

## Current Status

**Early development — Phase 1**

Forge is currently a prototype. The first milestone is establishing the desktop foundation and gradually giving Forge awareness of the system it is running on.

Current progress:

* [x] Initial project structure
* [x] Python development environment
* [x] PySide6 desktop shell
* [x] First Forge window
* [x] GitHub repository and development workflow
* [ ] System information/context
* [ ] Project detection
* [ ] Git/workspace awareness
* [ ] Agent architecture
* [ ] AI integration
* [ ] Context-aware assistance
* [ ] Desktop customization system

## The Idea

Modern computers already provide thousands of tools, but the user is still responsible for manually connecting everything together.

Forge explores a different approach:

```text
                    ┌──────────────┐
                    │     User     │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    Forge     │
                    │   Desktop    │
                    └──────┬───────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        ┌─────────┐   ┌─────────┐   ┌─────────┐
        │ System  │   │ Projects│   │ Workflow│
        └─────────┘   └─────────┘   └─────────┘
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                    ┌──────────────┐
                    │    Agent     │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Actions    │
                    └──────────────┘
```

The long-term goal is for Forge to understand **what the user is doing**, rather than simply responding to isolated commands.

For example, while developing a project, Forge could eventually understand the current repository, inspect its Git state, identify the development environment, help with dependencies, and perform requested actions while the developer stays focused on their work.

##  Long-Term Vision

Forge aims to explore features such as:

* A modern Linux desktop environment
* An integrated computer-side AI agent
* Context awareness across the desktop
* Automatic project and workspace detection
* Git-aware development workflows
* Tool and dependency management
* Deep desktop customization
* Adaptive resource usage based on the user's current task
* An extensible widget and plugin system
* Native Linux integration

The goal isn't to replace every existing Linux tool.

The goal is to **connect them into a smarter workspace.**

## Technology

Forge currently uses:

* **Python**
* **PySide6 / Qt**
* **Git**
* **Linux**

The architecture is expected to evolve substantially as development progresses.

## Desktop UI architecture

The Qt presentation is organized under `src/forge/desktop/`: `theme.py` owns
the palette and shared stylesheet, `components.py` contains reusable workspace
cards and controls, `motion.py` provides short event-driven animations, and
`window.py` composes those pieces. The window consumes `WorkspaceContext` from
`forge.core`; detection and other business logic stay independent of Qt.
Workspace refresh runs on a worker thread so Git and filesystem checks do not
block interaction. Startup and refresh transitions can be disabled with the
saved `reduced_motion` preference or `FORGE_REDUCED_MOTION=1`.

## Development Roadmap

### Phase 1 — Foundation

Build the desktop shell and establish the core architecture.

### Phase 2 — System Awareness

Teach Forge about the machine it is running on.

### Phase 3 — Workspace Awareness

Detect projects, repositories, development environments, and active workflows.

### Phase 4 — Agent Core

Build the internal agent architecture and tool system.

### Phase 5 — Intelligence

Connect Forge to an AI model and provide context-aware assistance.

### Phase 6 — Desktop Integration

Allow the agent to safely interact with applications, files, system tools, and development workflows.

### Phase 7 — Forge Ecosystem

Explore widgets, extensions, themes, plugins, and deeper Linux integration.

> **This roadmap is intentionally flexible. Forge is an experimental project, and the architecture will change as we learn.**

##  Contributing

Forge is currently being developed collaboratively as an experimental open-source project.

Development happens through Git branches and pull requests.

```text
main
 │
 ├── feature/...
 ├── fix/...
 └── experiment/...
```

Contributions, ideas, experiments, and technical discussions are welcome as the project develops.

## Disclaimer

Forge is **experimental software** and is not currently intended to replace an existing desktop environment or production workflow.

Expect bugs, architectural changes, broken experiments, and occasional questionable engineering decisions.

We're building it to learn what a Linux desktop environment with an integrated computer-side agent could become.

---

**Forge-Linux**
*Build the environment. Forge the workflow.*
