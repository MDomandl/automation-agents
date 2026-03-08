AKTUELLER STAND

Ich habe ein neues Repository erstellt:

automation-agents

Folgende Dinge existieren bereits:

- pyproject.toml
- Projektstruktur (app/, tests/, scripts/, docs/)
- Dokumentation:
  docs/architecture.md
  docs/dev-guidelines.md
  docs/adr/001-v1a-architecture.md

Die grundlegende Ordnerstruktur entspricht:

app/
  common/
  domain/
  application/
  tools/
  agents/
  workflows/
  infrastructure/
  bootstrap/

Das Projekt verwendet absolute Imports:

from app.domain.bt_run.compare import ...

PyCharm ist so konfiguriert, dass der Projektordner der Import-Root ist.

pytest läuft über pyproject.toml.