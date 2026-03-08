2. Rollen jeder Datei in v1a ganz konkret

Jetzt festzurren wir die Rollen.
Ich gehe Datei für Datei durch und sage jeweils:

Zweck

was dort hinein darf

was dort nicht hinein darf

Klasse oder pure Funktion?

app/common/
clock.py
Zweck

Abstraktion für Zeit.

Darf hinein

Clock Interface/Basis

SystemClock

FixedClock

Darf nicht hinein

Businesslogik

Formatierungslogik für Reports

Agentenlogik

Form

kleine Klassen

result.py
Zweck

Einheitlicher Rückgabetyp für Erfolg/Fehler.

Darf hinein

Result.ok(...)

Result.fail(...)

einfache Properties wie is_ok

Darf nicht hinein

Logging

Exception-Mapping aus 20 Systemen

domänenspezifische Sonderregeln

Form

eine kleine Dataclass / Generic-Klasse

errors.py
Zweck

Kleine, bewusst benannte Fehlerklassen für das System.

Darf hinein

AgentError

ConfigurationError

ComparisonError

Darf nicht hinein

große Fehlerbehandlungslogik

Infrastrukturcode

Form

kleine Exception-Klassen

app/domain/bt_run/
models.py
Zweck

Fachliche Datenobjekte für BT/RUN.

Darf hinein

DecisionBundleRef

ComparisonSummary

evtl. später WeightDifference, NameDifference

Darf nicht hinein

Parsing aus Dateien

Subprocess-Logik

Report schreiben

LLM

Form

Dataclasses

compare.py
Zweck

Reine Vergleichs- und Ableitungslogik.

Darf hinein

pure Funktionen

Summary-Aufbau

Auswertung fachlicher Unterschiede

Darf nicht hinein

Datei laden

Comparator per Prozess starten

Report schreiben

Logging

Form

pure Funktionen
Das ist eine der Dateien, die ausdrücklich keine große Klasse braucht.

app/application/bt_run/
dto.py
Zweck

Datentransport für Use Cases.

Darf hinein

RunBtRunnerRequest

RunBtRunnerResult

CompareLatestRequest

CompareLatestResult

Darf nicht hinein

Fachlogik

Seiteneffekte

Validierungsmonster

Form

Dataclasses

ports.py
Zweck

Schnittstellen definieren, die die Application-Schicht braucht.

Darf hinein

ProcessRunner

DecisionBundleStore

ComparatorGateway

ReportWriter

Darf nicht hinein

konkrete Implementierungen

subprocess

Filesystem-Code

Form

Protocols / abstrakte Interfaces

use_cases.py
Zweck

Anwendungsfälle koordinieren.

Darf hinein

RunBtRunnerUseCase

CompareLatestUseCase

Darf hinein an Logik

Reihenfolge innerhalb eines Anwendungsfalls

Port-Aufrufe

Fehler in Result umwandeln

einfache fachliche Guard Checks

Darf nicht hinein

echte Dateizugriffe

echte Prozessstarts

Markdown generieren

tiefe Domain-Logik, die besser pure Funktion wäre

Form

kleine Klassen
Hier sind Klassen sinnvoll, weil Dependencies injiziert werden.

app/tools/bt_run/

Hier beginnt die agentennahe Ebene.

run_backtest_tool.py
Zweck

Ein Werkzeug, das den Backtest startet.

Darf hinein

dünner Wrapper um RunBacktestUseCase oder ProcessRunner

klarer fachlicher Methodenname

Darf nicht hinein

gesamte Agentlogik

Reportlogik

Vergleichslogik

Form

kleine Klasse

run_runner_tool.py
Zweck

Runner starten.

Darf hinein

nur Runner-bezogener Ablauf

Darf nicht hinein

Vergleich

Report

Bundle-Finden

Form

kleine Klasse

compare_latest_runs_tool.py
Zweck

Die neuesten BT/RUN-Artefakte vergleichen.

Darf hinein

Aufruf des Compare-Use-Cases

evtl. kleines Zusammenfassen für Agentenebene

Darf nicht hinein

Subprocess-Implementierung

Markdown-Erzeugung

LLM-Erklärung

Form

kleine Klasse

write_bt_run_report_tool.py
Zweck

Aus einem ComparisonSummary einen Report erzeugen.

Darf hinein

delegierter Aufruf eines ReportWriters

evtl. kleiner Use Case

Darf nicht hinein

fachliche Vergleichslogik

Prozessstart

Bundle-Suche

Form

kleine Klasse

app/agents/
bt_run_agent.py
Zweck

Der eigentliche BT/RUN-Agent.
Er orchestriert die Tools in der richtigen Reihenfolge.

Darf hinein

Ablaufsteuerung

Fehlerabbruch

Zusammensetzen des Agent-Ergebnisses

Darf nicht hinein

Subprocess direkt

Filesystem direkt

tiefere Vergleichslogik

Markdown selbst bauen

Tradinglogik

Form

eine kleine Klasse
Das ist bewusst die Orchestrierungsschicht.

Faustregel

Die Kernmethode execute() sollte knapp bleiben.
Eher so 20–40 Zeilen, nicht 150.

app/infrastructure/process/
subprocess_runner.py
Zweck

Konkrete technische Implementierung für Prozessaufrufe.

Darf hinein

subprocess.run(...)

Rückgabe von Exit Codes

evtl. einfache stdout/stderr-Rückgabe in späterem Ausbau

Darf nicht hinein

BT/RUN-Fachentscheidungen

Agentenlogik

Reportlogik

Form

kleine Klasse

app/infrastructure/storage/
file_decision_bundle_store.py
Zweck

Decision-Bundle-Dateien im Dateisystem finden.

Darf hinein

Pfadlogik

Dateisuche

Parsing des Dateinamens zu DecisionBundleRef

Darf nicht hinein

Vergleichslogik

Prozessstart

Agentenlogik

Form

kleine Klasse

markdown_file_writer.py
Zweck

Markdown-Dateien schreiben.

Darf hinein

Path(...)

write_text(...)

Reportdatei physisch speichern

Darf nicht hinein

Fachlogik zur Bewertung von Drift

Vergleichsberechnung

Prozesslogik

Form

kleine Klasse

app/infrastructure/compare/
comparator_gateway.py
Zweck

Brücke zum bestehenden Comparator.

Darf hinein

Import oder Subprocess-Aufruf deines bestehenden mini_comparator.py

Übersetzung des Ergebnisses in ComparisonSummary

Darf nicht hinein

Agentenlogik

BT/RUN komplett selbst starten

Report schreiben

Form

kleine Klasse

Wichtiger Punkt

Das ist genau die Stelle, an der wir deine bestehende Welt an die neue Architektur anschließen.

app/bootstrap/
bt_run_container.py
Zweck

Konkrete Verdrahtung aller Abhängigkeiten.

Darf hinein

Instanzen erzeugen

Tools zusammensetzen

Agent bauen

Darf nicht hinein

Businesslogik

echte Ablaufsteuerung

Vergleichslogik

Form

Factory-Funktionen
Hier würde ich eher Funktionen statt Klassen nehmen.

Zum Beispiel:

build_bt_run_agent()

tests/fakes/
fake_process_runner.py
Zweck

Echter Prozessstart wird im Test ersetzt.

Form

kleine Fake-Klasse

fake_bundle_store.py
Zweck

Bundle-Suche im Test kontrolliert vorgeben.

Form

kleine Fake-Klasse

fake_comparator_gateway.py
Zweck

Vergleichsergebnis gezielt simulieren.

Form

kleine Fake-Klasse

fake_report_writer.py
Zweck

Im Test keinen echten Report schreiben, sondern Aufruf prüfen.

Form

kleine Fake-Klasse

tests/unit/
test_compare.py
Zweck

Domain-Logik testen.

Testet

pure Vergleichsfunktionen

Note-/Summary-Ableitung

test_use_cases.py
Zweck

Application-Schicht testen.

Testet

Erfolg/Fehler bei Run/Compare-Use-Cases

Port-Zusammenspiel

test_bt_run_tools.py
Zweck

Tools einzeln testen.

Testet

delegieren sie korrekt?

geben sie sauber weiter?

kapseln sie den fachlichen Schritt richtig?

test_bt_run_agent.py
Zweck

Agent-Orchestrierung testen.

Testet

Reihenfolge

Fehlerabbruch

Report-Erzeugung

Result-Rückgabe

scripts/
run_bt_run_agent.py
Zweck

Manueller Startpunkt für das System.

Darf hinein

Agent bauen

Request erzeugen

Ergebnis drucken

Darf nicht hinein

Fachlogik

Infrastrukturdetails duplizieren

Vergleichslogik

Form

dünnes Skript

docs/
architecture.md
Zweck

Die Architekturentscheidungen dokumentieren.

Inhalt

Schichten

Regeln

Scope v1a

Rollen der Bausteine

spätere Erweiterungsideen

Form

kurzes lebendes Dokument

3. Was davon Klassen sein sollte und was lieber nicht

Das wollte ich ja noch sauber festzurren.

Klassen

Für diese Dateien sind Klassen sinnvoll:

clock.py

result.py

use_cases.py

alle tools/...

bt_run_agent.py

subprocess_runner.py

file_decision_bundle_store.py

markdown_file_writer.py

comparator_gateway.py

Warum?
Weil dort Abhängigkeiten injiziert werden oder ein klarer objektartiger Dienst vorliegt.

Pure Funktionen

Für diese Dateien würde ich bewusst auf Klassen verzichten:

domain/bt_run/compare.py

Warum?
Weil reine Fachlogik als Funktion oft:

klarer

kürzer

leichter testbar

weniger künstlich

ist.

Dataclasses / Typobjekte

Hier keine Service-Klassen, sondern reine Datenobjekte:

domain/bt_run/models.py

application/bt_run/dto.py

Factory-Funktionen

Hier eher Funktionen statt Klassen:

bootstrap/bt_run_container.py