# Historische Positionen balanced_v1

## Zweck

Dieser Ablageort ist fuer eine spaeter kontrolliert aufgebaute historische `balanced_v1`-Positionsdatenbasis vorgesehen.

Aktuell enthaelt das Verzeichnis noch keine historischen Positionsdaten.

Die Struktur ist ausschliesslich eine technische Vorbereitung.

## Abgrenzung

Der Ablageort ist getrennt von:

* aktuellen Portfolios
* Paper-Runs
* Backtest-Artefakten
* Reports
* Runner-Zustaenden
* Live- oder Broker-Systemen

Dateien in diesem Verzeichnis duerfen nicht automatisch als aktuelle oder ausfuehrbare Portfoliozustaende interpretiert werden.

## Noch nicht vorhanden

Aktuell existieren hier ausdruecklich nicht:

* keine Stichtagsdateien
* kein Manifest
* kein Index
* kein Schema
* kein Validator
* kein Generator
* keine automatisierte Verarbeitung
* keine echte historische Positionsdatenbasis

## Grundregeln fuer spaetere Inhalte

Spaetere Dateien muessen einem eindeutig benannten Stichtag zugeordnet sein.

`balanced_v1` muss eindeutig erkennbar bleiben.

Die Datenherkunft muss nachvollziehbar dokumentiert sein.

Fehlende Daten duerfen nicht geschaetzt, automatisch ergaenzt oder aus benachbarten Stichtagen uebernommen werden.

Technische Validierung ersetzt keine fachliche Pruefung.

Human Review bleibt zwingend.

Das Vorhandensein einer Datei bedeutet weder technische Gueltigkeit noch fachliche Freigabe.

## Statusmodell

Vorgesehene Statuswerte fuer spaetere Inhalte:

* `planned`: vorgesehen, aber noch nicht vorhanden
* `missing`: fuer den vorgesehenen Stichtag liegen keine belastbaren Daten vor
* `draft`: Datei oder Inhalt ist vorhanden, aber noch ungeprueft
* `validated`: technisch beziehungsweise strukturell geprueft
* `approved`: nach bewusster fachlicher Human-Review freigegeben

`validated` bedeutet keine fachliche Freigabe.

`approved` darf nicht automatisch vergeben werden.

## Nicht zulaessige Nutzung

Nicht zulaessig sind:

* keine automatische Erkennung durch bestehende Runner
* keine automatische Strategieausfuehrung
* keine Paper- oder Backtest-Ausfuehrung aus diesem Verzeichnis
* keine Batch-Verarbeitung
* keine Broker-, Live-, Order-, Stueckzahl-, Euro- oder Depotgroessenlogik
* keine Portfolioausfuehrung
* keine Performance-, Benchmark-, Risiko- oder Drawdown-Aussage
* keine Investitionsfreigabe

## Verweise

Massgeblich sind die Abschnitte 09.10 bis 09.70 sowie 10.10, 10.20 und 10.30 in `../../../docs/strategy_analysis.md`.
