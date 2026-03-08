SESSION START

Kontext:
Ich entwickle ein Python-Projekt für persönliche Automations-Agenten.
Ziel ist eine saubere, wiederverwendbare Architektur, mit der mehrere spezialisierte Agenten gebaut werden können.

Der erste Agent orchestriert mein bestehendes Projekt "aktien_oop".

Dieses Projekt enthält bereits:
- Backtester
- Runner
- Decision Bundles
- Comparator (mini_comparator.py)

Der Agent soll diese Komponenten automatisieren.

------------------------------------------------

ARCHITEKTUR

Das System folgt einer Layered Architecture:

Agent
↓
Tools
↓
Application (Use Cases)
↓
Domain
↓
Infrastructure

Regeln:

1. Abhängigkeiten zeigen nur nach innen
Agent → Tools → Application → Domain

2. Seiteneffekte nur in Infrastructure

3. Domain enthält nur pure Logik

4. Dependency Injection erfolgt im bootstrap

5. Agenten kommunizieren nicht direkt miteinander
   Kooperation erfolgt über Workflows

------------------------------------------------

PROJEKTSTRUKTUR

automation-agents

app/
common/
domain/
application/
tools/
agents/
workflows/
infrastructure/
bootstrap/

tests/
scripts/
docs/

------------------------------------------------

TECH STACK

Python ≥ 3.11

Tools:
- pytest
- ruff
- coverage

IDE:
PyCharm Community

Codex Plugin installiert (kann für Boilerplate genutzt werden)

------------------------------------------------

STATUS

Folgende Dinge sind bereits entworfen:

✔ Architektur
✔ Projektstruktur
✔ pyproject.toml
✔ Dokumentationsstruktur
✔ Demo-Multi-Agent-Beispiel
✔ Workflow-Konzept

Das Demo-Beispiel enthält:

RunAgent
CompareAgent
Workflow

als Proof of Concept.

------------------------------------------------

ZIEL DER NÄCHSTEN SCHRITTE

Jetzt soll ein erster **Vertical Slice** implementiert werden.

Schritte:

1. Domain Layer
   models.py
   compare.py

2. Application Layer
   dto.py
   ports.py
   use_cases.py

3. Tools
   run_backtest_tool.py
   run_runner_tool.py
   compare_latest_runs_tool.py
   write_bt_run_report_tool.py

4. Agent
   bt_run_agent.py

5. Workflow
   bt_run_workflow.py

6. Infrastructure
   subprocess_runner.py
   comparator_gateway.py
   decision_bundle_store.py

7. Bootstrap
   bt_run_container.py

8. Startscript
   scripts/run_bt_run_agent.py

------------------------------------------------

WICHTIG

Fokus liegt auf:

- sauberer Architektur
- kleinen testbaren Komponenten
- SRP
- Dependency Injection
- klarer Verantwortlichkeit

Nicht auf schneller Implementierung.

------------------------------------------------

Bitte hilf mir beim nächsten sinnvollen Implementierungsschritt.