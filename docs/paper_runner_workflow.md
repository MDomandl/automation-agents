# Paper-Runner-Workflow

## Zweck

Der Paper-Runner erzeugt eine technische Simulation und einen Vorschlagsreport für ein Strategieprofil. Er dient dazu, Zielpositionen, lokale Ist-Gewichte und daraus abgeleitete Buy/Sell/Hold-Proposals nachvollziehbar zu prüfen.

Der Paper-Runner ist keine Anlageberatung, keine Orderanweisung und keine Ausführungslogik. Es gibt keine Broker-Anbindung, kein Live-Trading und keine echten Orders.

## Typischer Ablauf

1. Ist-Portfolio als CSV-Datei pflegen.
2. Paper-Run mit `--runner-mode paper` starten.
3. Zielpositionen berechnen lassen.
4. Buy/Sell/Hold-Proposals prüfen.
5. Human Review durchführen.
6. Keine automatische Ausführung vornehmen.

Die persönliche Verantwortung bleibt beim Menschen. Der Report ist ein Prüfartefakt, keine Freigabe.

## Beispiel-Portfolio-Datei

Beispieldatei:

[CODE_START]
examples/paper_portfolio_positions.csv
[CODE_END]

Unterstütztes Format:

[CODE_START]
symbol,weight
CVS,0.111111
EBAY,0.111111
GE,0.111111
[CODE_END]

`symbol` enthält das Ticker-Symbol. `weight` enthält das lokale Ist-Gewicht als Dezimalzahl.

Die CSV-Validierung verlangt die Spalten `symbol` und `weight`, nicht-leere Symbole, numerische und nicht-negative Gewichte sowie eindeutige Symbole nach Trimming und Uppercase-Normalisierung. Gewichte werden nicht normalisiert; die Summe muss nicht `1.0` ergeben. Details und Beispiele stehen in `portfolios/README.md`.

## Beispielaufruf

[CODE_START]
.venv\Scripts\python.exe -m scripts.run_bt_run_agent --profile short --strategy-profile balanced_v1 --runner-mode paper --portfolio-file examples/paper_portfolio_positions.csv
[CODE_END]

Wenn lokal mehrere Portfolio-Dateien gepflegt werden, kann der Paper-Report optional
einen technischen Namen fÃ¼r die Zuordnung ausweisen:

[CODE_START]
--portfolio-file portfolios/manfred_real.csv --portfolio-name manfred_real
[CODE_END]

## Lokale Portfolio-Organisation

Lokale Ist-Portfolios koennen im Ordner `portfolios/` organisiert werden. Diese CSV-Dateien sind manuell gepflegte lokale Demo- oder Ist-Portfolios und keine Broker-Daten.

Beispiel:

[CODE_START]
.venv\Scripts\python.exe -m scripts.run_bt_run_agent --profile short --strategy-profile balanced_v1 --runner-mode paper --portfolio-file portfolios/example_local_portfolio.csv --portfolio-name example_local
[CODE_END]

`--portfolio-file` zeigt dabei immer auf eine einzelne CSV-Datei. `--portfolio-name` ist nur eine optionale Bezeichnung fuer Reports. Pro Paper-Run wird immer nur ein Portfolio verarbeitet; es gibt keine Multi-Portfolio-Batch-Verarbeitung.

## Bedeutung der Report-Felder

* `runner_mode`: Runner-Modus des Laufs, im Paper-Workflow `paper`.
* `strategy_profile_name`: verwendetes Strategieprofil, z. B. `balanced_v1`.
* `portfolio_name`: optionaler lokaler Name zur technischen Zuordnung des verwendeten Ist-Portfolios.
* `portfolio_source`: Herkunft der Ist-Portfolio-Daten, z. B. `portfolio_file`.
* `portfolio_file`: Pfad der verwendeten lokalen Portfolio-Datei.
* `proposal_delta_tolerance`: Toleranz für die Buy/Sell/Hold-Klassifikation.
* `proposal_delta_basis`: fachliche Basis der Delta-Berechnung, z. B. `local portfolio file`.
* `orders_executed`: zeigt an, ob Orders ausgeführt wurden; im Paper-Workflow `false`.
* `broker_connected`: zeigt an, ob eine Broker-Verbindung bestand; im Paper-Workflow `false`.
* `live_trading_enabled`: zeigt an, ob Live-Trading aktiv war; im Paper-Workflow `false`.
* `human_review_required`: zeigt an, dass eine manuelle Prüfung erforderlich ist.
* `technical_info`: technische Runner- und Seeding-Informationen.
* `warnings`: fachliche Warnungen und Hinweise.

## Bedeutung von Buy/Sell/Hold

* Buy: Zielgewicht ist größer als Istgewicht oberhalb der Toleranz.
* Sell: Zielgewicht ist kleiner als Istgewicht unterhalb der negativen Toleranz.
* Hold: Delta liegt innerhalb der Toleranz.

Diese Klassifikation enthält keine Stückzahlen, keine Euro-Beträge und keine Orderausführung.

## Sicherheitsgrenzen

* Keine Broker-Anbindung.
* Kein Live-Trading.
* Keine echten Orders.
* Keine automatische Anlageentscheidung.
* Keine Anlageberatung.
* Manuelle Prüfung erforderlich.
* Persönliche Verantwortung bleibt beim Menschen.

## Beispiel aus Kontrolllauf

Erfolgreicher Kontrolllauf:

* Run-ID: `20260618_203251`
* `as_of`: `2025-10-08`
* Buy: DASH, IVZ
* Sell: APTV, HUM
* Hold: CVS, EBAY, GE, NEM, PLTR, PSKY, WDC

Rundungsdeltas wurden korrekt als `Hold` klassifiziert. Der Lauf bestätigt die Report-Klarheit für lokale Ist-Portfolio-Datei, Proposal-Delta-Basis und Sicherheitsgrenzen.
