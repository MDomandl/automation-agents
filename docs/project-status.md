# Projektstatus aktien_oop

Kurzer Einstiegspunkt fuer neue oder zurueckkehrende Entwickler. Die fachliche Langdokumentation bleibt in den verlinkten Detaildokumenten.

## Zweck des Projekts

`aktien_oop` entwickelt einen nachvollziehbaren Workflow zur Analyse und Auswahl von Aktienstrategien im Backtest- und Paper-Betrieb. Der Fokus liegt auf Strategieanalyse, Profilvergleich, Paper-Reports und kontrollierter menschlicher Bewertung, nicht auf produktivem Handel oder automatischer Orderausfuehrung.

## Aktueller Projektstand

Der letzte dokumentierte Stand ist `09.70 Phase-9-Zwischenabschluss` in `docs/strategy_analysis.md`.

Phase 9 ist dokumentarisch zwischenabgeschlossen. Sie hat Zielbild, Datenmodell, Quellenstrategie und Sicherheitsgrenzen fuer eine spaetere historische `balanced_v1`-Positionsdatenbasis geklaert. Es wurde bewusst keine technische Umsetzung gestartet und keine historische Datenbasis erzeugt.

Der historische Paper-Replay-Minimalstand aus Phase 8 ist technisch mit einer kleinen synthetischen Positionsdatenbasis erprobt. Das ist keine echte historische `balanced_v1`-Positionsdatenbasis.

Abgeschlossene relevante Vorarbeiten sind nur knapp einzuordnen: Strategieprofile sind implementiert und fuer Backtests sowie kontrollierte Runner-Auswertungen verwendbar, daraus folgt aber keine Live- oder Handelsfreigabe. `balanced_v1` wurde in Robustheits-, Marktphasen-, Drawdown- und Risk-Metrics-Analysen als Hauptkandidat bestaetigt, und der Paper-Workflow fuer lokale Portfolio-Dateien ist dokumentiert.

## Aktueller fachlicher Hauptkandidat

`balanced_v1` ist der aktuelle fachliche Hauptkandidat.

Belegt ist das in `docs/strategy_analysis.md` durch Profilvergleiche, Marktphasen-Auswertungen und Risikoanalysen. Die Bewertung ist fachlich, nicht operativ: `balanced_v1` ist kein Live-Profil mit Handelsfreigabe.

## Sicherer operativer Modus

Der sichere operative Modus ist Paper-Betrieb mit Human Review.

Der Paper-Runner vergleicht ein manuell gepflegtes Portfolio mit der aktuellen Zielauswahl eines Strategieprofils. Daraus entstehen technische Buy-, Sell- und Hold-Vorschlaege, die ausschliesslich der menschlichen Pruefung dienen.

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

- keine echte historische `balanced_v1`-Positionsdatenbasis mit Stichtagsdateien, Manifest oder Index
- kein Generator, Validator oder Batch-Prozess fuer historische Positionsdaten
- keine Integration historischer Positionsdaten in den Paper-Runner
- keine Broker-, Live-, Order-, Stueckzahl-, Euro- oder Depotgroessenlogik
- keine Investitions-, Handels-, Performance- oder Umsetzungsfreigabe

## Weiterfuehrende Dokumentation

- `docs/strategy_analysis.md`: fachliche Langdokumentation, aktueller letzter Stand `09.70`.
- `docs/paper_runner_workflow.md`: Paper-Workflow, Report-Felder, Sicherheitsgrenzen und Human Review.
- `portfolios/README.md`: lokale manuelle Portfolio-CSV-Dateien und Validierungsregeln.
- `docs/dev-guidelines.md`: Architektur- und Coding-Regeln.
- `docs/adr/001-v1a-architecture.md`: grundlegende Architekturentscheidung.
- `docs/adr/001-va1-current-state.md`, `docs/adr/001-va1-next-step.md`, `docs/adr/001-va1-reference.md`: frueher Projektkontext und Vertical-Slice-Ausgangspunkt.

## Pflege dieses Dokuments

Diese Datei wird nur aktualisiert, wenn sich uebergeordnete Aussagen aendern, zum Beispiel aktueller Phasen- oder Projektstand, fachlicher Hauptkandidat, verfuegbarer Workflow, Sicherheitsgrenzen, wichtige vorhandene Artefakte oder ausdruecklich noch nicht vorhandene Bestandteile. Sie ist nicht fuer jede kleine Code-, Test- oder Refactoring-Aenderung gedacht.
