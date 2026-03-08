# Automation Agents

This repository contains a reusable architecture for building automation agents.

The goal is to create small, specialized agents that automate recurring tasks while remaining easy to test, extend and maintain.

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