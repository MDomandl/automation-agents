# Projektstatus aktien_oop

Kurzer Einstiegspunkt fuer neue oder zurueckkehrende Entwickler. Die fachliche Langdokumentation bleibt in den verlinkten Detaildokumenten.

## Zweck des Projekts

`aktien_oop` entwickelt einen nachvollziehbaren Backtest-/Runner-Workflow fuer Aktienstrategien. Der Fokus liegt auf Strategieanalyse, Profilvergleich, Paper-Reports und kontrollierter Human Review, nicht auf automatischer Orderausfuehrung.

## Aktueller Projektstand

Der letzte dokumentierte Stand ist `09.70 Phase-9-Zwischenabschluss` in `docs/strategy_analysis.md`.

Phase 9 ist dokumentarisch zwischenabgeschlossen. Sie hat Zielbild, Datenmodell, Quellenstrategie und Sicherheitsgrenzen fuer eine spaetere historische `balanced_v1`-Positionsdatenbasis geklaert. Es wurde bewusst keine technische Umsetzung gestartet und keine historische Datenbasis erzeugt.

Abgeschlossene relevante Vorarbeiten sind nur knapp einzuordnen: Strategieprofile sind dokumentiert und nutzbar, `balanced_v1` wurde in Robustheits-, Marktphasen-, Drawdown- und Risk-Metrics-Analysen als Hauptkandidat bestaetigt, und der Paper-Workflow fuer lokale Portfolio-Dateien ist dokumentiert.

## Aktueller fachlicher Hauptkandidat

`balanced_v1` ist der aktuelle fachliche Hauptkandidat.

Belegt ist das in `docs/strategy_analysis.md` durch Profilvergleiche, Marktphasen-Auswertungen und Risikoanalysen. Die Bewertung ist fachlich, nicht operativ: `balanced_v1` ist kein Live-Profil mit Handelsfreigabe.

## Sicherer operativer Modus

Der sichere operative Modus ist Paper-Betrieb mit Human Review.

Der Paper-Runner erzeugt technische Vorschlagsreports mit Buy/Sell/Hold-Proposals als Delta- und Gewichtungs-Pruefsignale. Diese Proposals sind keine Anlageempfehlung, keine Ordervorbereitung und keine Ausfuehrungslogik.

Explizite Grenzen:

- keine Broker-Verbindung
- keine Orderausfuehrung
- kein Live-Trading
- keine Stueckzahl- oder Euro-Berechnung
- keine automatische Anlageentscheidung
- Human Review bleibt verpflichtend

## Was derzeit vorhanden ist

- Layered-Agent-Architektur mit Agent, Tools, Application, Domain und Infrastructure laut ADR und Guidelines.
- Backtest-/Runner-Orchestrierung fuer den BT/RUN Agent.
- Strategieprofile unter `configs/profiles/`, darunter `balanced_v1`, `conservative_v1` und `offensive_v1`.
- Langdokumentation der Strategieanalyse in `docs/strategy_analysis.md`.
- Paper-Runner-Workflow mit lokaler Portfolio-CSV und Human Review in `docs/paper_runner_workflow.md`.
- Lokale Portfolio-Organisation unter `portfolios/` mit README und Beispielportfolio.
- Skripte zum Paper-Run, zur Paper-Run-History und zum Vergleich vorhandener Paper-Reports.
- ADRs und Development Guidelines fuer Architektur, Verantwortlichkeiten und Testbarkeit.

## Was ausdruecklich noch nicht vorhanden ist

- keine echte historische `balanced_v1`-Positionsdatenbasis
- keine echten historischen `balanced_v1`-Stichtagsdateien
- kein Manifest-/Index-Artefakt fuer historische `balanced_v1`-Stichtage
- kein Generator fuer historische Positionsdaten
- kein Validator fuer historische Positionsdaten
- keine Batch-Erzeugung historischer Stichtage
- keine Aenderung am Paper-Runner fuer Phase 9
- keine Broker-, Live-, Order-, Stueckzahl-, Euro- oder Depotgroessenlogik
- keine Investitions-, Handels-, Performance- oder Umsetzungsfreigabe

## Weiterfuehrende Dokumentation

- `docs/strategy_analysis.md`: fachliche Langdokumentation, aktueller letzter Stand `09.70`.
- `docs/paper_runner_workflow.md`: Paper-Workflow, Report-Felder, Sicherheitsgrenzen und Human Review.
- `portfolios/README.md`: lokale manuelle Portfolio-CSV-Dateien und Validierungsregeln.
- `docs/dev-guidelines.md`: Architektur- und Coding-Regeln.
- `docs/adr/001-v1a-architecture.md`: grundlegende Architekturentscheidung.
- `docs/adr/001-va1-current-state.md`, `docs/adr/001-va1-next-step.md`, `docs/adr/001-va1-reference.md`: frueher Projektkontext und Vertical-Slice-Ausgangspunkt.

Diese Datei soll mitgepflegt werden, wenn sich der uebergeordnete Projektstand aendert: aktueller Phasenstand, fachlicher Hauptkandidat, verfuegbarer Workflow, Sicherheitsgrenzen, wichtige vorhandene Artefakte oder ausdruecklich noch nicht vorhandene Bestandteile. Sie ist nicht fuer jede kleine Codeaenderung gedacht.
