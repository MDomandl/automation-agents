# Automation Agents

This repository contains a reusable architecture for building automation agents.

The goal is to create small, specialized agents that automate recurring tasks while remaining easy to test, extend and maintain.

**Current aktien_oop project status:** see `docs/project-status.md` for the short human entry point to the current state, safe workflow and open boundaries.

The first implemented agent is the **BT/RUN Agent**, which orchestrates the following workflow:

1. Run the backtester
2. Run the runner
3. Compare decision bundles
4. Generate a report

---

# Architecture

The project follows a layered architecture:

Agent → Tools → Application → Domain → Infrastructure

Responsibilities:

Agent  
Orchestrates the workflow.

Tools  
Small reusable operations used by agents.

Application  
Use cases coordinating domain logic.

Domain  
Pure business logic without side effects.

Infrastructure  
External systems such as filesystem, subprocesses or APIs.

---

# Project Structure
app/
common/
domain/
application/
tools/
agents/
infrastructure/
bootstrap/

tests/
scripts/
docs/


---

# Running the agent
python scripts/run_bt_run_agent.py

---

# Explicit test profile

The test profile is Python 3.11 with its direct test dependencies declared in
the `test` extra in `pyproject.toml`. This is an explicit test profile, not a
transitive dependency lock. Provisioning is a separate, network-capable step:

```powershell
py -3.11 -m venv .venv311
.\.venv311\Scripts\python.exe -m pip install -e ".[test]"
```

The audit and test run use only the provisioned environment and local files.
Use a dedicated, clean AiAgents audit worktree at revision
`f5626a3b3ddb51651577ae7735af5133ed4ee712`; do not point the test profile at a
normal development checkout with local changes. Pass that worktree explicitly
as an absolute, source-only root:

```powershell
$env:AI_AGENTS_ROOT = "C:\absolute\path\to\clean\AiAgents-audit-worktree"
$env:PYTHONDONTWRITEBYTECODE = "1"
.\.venv311\Scripts\python.exe -m scripts.validate_ai_agents_test_environment `
  --ai-agents-root $env:AI_AGENTS_ROOT
.\.venv311\Scripts\python.exe -m pytest -p no:cacheprovider
```

The audit fails closed unless Python is 3.11, the worktree is clean at the
documented revision, the root is absolute and has the required `aktien_oop`
package structure, `aktien_oop.store` is imported from that root, and its
`PortfolioStore` provides the required snapshot API. The validator uses only
non-writing Git queries, disables Python bytecode writes during imports, and
treats AiAgents as source-only. It does not provide an OS-level read-only
capability or guarantee that every possible caller is unable to write there.
Enforcing read-only access at the OS/AO capability boundary remains a separate
Model A / Capability-Policy v0.2 prerequisite. The audit and test run require
no network access. Direct dependencies are declared, but without a transitive
lock this profile does not claim fully reproducible dependency resolution.

---

# Goals

- clean architecture
- small, testable components
- dependency injection
- reusable automation agents

---

# Planned Agents

- BT/RUN Agent
- Code Review Agent
- Theater Organization Agent
- Automation Agents for personal workflows
