# Agent System Architecture (v1)

## Ziel

Dieses Projekt stellt eine wiederverwendbare Architektur für spezialisierte
Automations-Agenten bereit.

Die Architektur soll:

- testbar sein
- SRP und Dependency Injection unterstützen
- kurze Funktionen und kleine Klassen fördern
- Seiteneffekte isolieren
- Erweiterungen für weitere Agenten ermöglichen

Der Fokus liegt zunächst auf einem Agenten:

BT/RUN Agent – orchestriert Backtester, Runner und Comparator.

---

# Architekturprinzipien

## 1. Schichtenmodell

Die Architektur folgt einer klaren Schichtung:

Agent
↓
Tools
↓
Use Cases (Application)
↓
Domain
↓
Infrastructure

### Rollen

Agent  
Orchestriert Tools und definiert den Ablauf.

Tools  
Agenten-nahe Werkzeuge, die einen fachlichen Schritt ausführen.

Application (Use Cases)  
Koordination eines konkreten Anwendungsfalls.

Domain  
Reine Fachlogik ohne Seiteneffekte.

Infrastructure  
Technische Implementierung (Files, Prozesse, APIs, LLM).

---

# Grundregeln

## Domain

- keine Seiteneffekte
- reine Funktionen bevorzugen
- nur Fachlogik
- vollständig unit-testbar

## Use Cases

- orchestrieren Domain-Funktionen
- definieren Ports (Interfaces)

## Tools

- ein fachlicher Schritt pro Tool
- kapseln Use Cases
- werden vom Agent verwendet

## Agent

- orchestriert Tools
- kennt keine Infrastrukturdetails
- enthält keine Fachlogik

## Infrastructure

- implementiert Ports
- enthält Seiteneffekte
- darf Domain/UseCases verwenden

---

# Dependency Injection

Alle Abhängigkeiten werden über Konstruktoren übergeben.

Die konkrete Verdrahtung erfolgt im Bootstrap-Modul.

Beispiel:

bootstrap/bt_run_container.py

---

# Ergebnis-Handling

Alle Use Cases und Agenten liefern einen `Result`-Typ zurück:

Result.ok(value)
Result.fail(error)

Damit wird Fehlerbehandlung explizit und testbar.

---

# Zeitabhängigkeit

Zeit wird über eine `Clock` abstrahiert.

Production:
SystemClock

Tests:
FixedClock

---

# Agenten-Zusammenarbeit

In v1 arbeiten Agenten unabhängig.

Regel:

Agenten kommunizieren über Ergebnisse, nicht über direkte Abhängigkeiten.

Später kann ein Workflow-Layer eingeführt werden.

---

# v1 Scope

Erster implementierter Agent:

BT/RUN Agent

Ablauf:

1. Backtester ausführen
2. Runner ausführen
3. Decision Bundles finden
4. Vergleich durchführen
5. Bericht erzeugen

---

# Projektstruktur
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

# Erweiterungsstrategie

Neue Agenten werden als eigener Vertical Slice ergänzt:

domain/<agent>
application/<agent>
tools/<agent>
agents/<agent>

Beispiel:

theater_agent

---

# Wichtige Designprinzipien

- SRP
- kurze Funktionen
- geringe Kopplung
- hohe Testbarkeit
- klare Verantwortlichkeiten

---

# v2 Ideen (noch nicht implementiert)

- Workflow Layer für Multi-Agent-Orchestrierung
- LLM-basierte Analyse
- GitLab Merge Request Automation
- Theater-Agent für Event-Organisation