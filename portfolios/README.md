# Lokale Portfolio-Dateien

## Zweck

Dieser Ordner dient zur einfachen lokalen Organisation manuell gepflegter Ist-Portfolios fuer Paper-Runs.

Die Dateien in diesem Ordner sind lokale CSV-Dateien. Sie sind keine Broker-Daten, kein Live-Depotabruf und keine Orderquelle.

## CSV-Format

Unterstuetztes Format:

```csv
symbol,weight
DASH,0.05
IVZ,0.04
CVS,0.03
```

`symbol` enthaelt das Ticker-Symbol. `weight` wird als Dezimalgewicht interpretiert, zum Beispiel `0.05` fuer 5 Prozent.

CSV-Dateien in diesem Ordner sind manuell gepflegte lokale Ist-Portfolios. Es besteht keine Broker-Anbindung. Es werden keine echten Orders erzeugt. Es erfolgt keine Stueckzahl- oder Euro-Berechnung.

## Validierungsregeln

`--portfolio-file` verarbeitet genau eine CSV-Datei mit den Spalten `symbol` und `weight`.

Regeln:

* `symbol` und `weight` muessen als Spalten vorhanden sein.
* `symbol` darf nicht leer sein.
* `weight` darf nicht leer sein.
* `weight` muss als Dezimalzahl lesbar sein.
* `weight` darf nicht negativ sein.
* Symbole werden getrimmt und auf Uppercase normalisiert.
* Doppelte Symbole sind nach Trimming und Uppercase-Normalisierung nicht erlaubt.
* Whitespace um `weight` wird toleriert, sofern der Wert als Dezimalzahl lesbar ist.
* Gewichte werden nicht normalisiert.
* Die Summe der Gewichte muss nicht `1.0` ergeben.
* Symbole ausserhalb des spaeteren Zielportfolios bleiben erlaubt.

Gueltiges Beispiel:

```csv
symbol,weight
 aapl , 0.12
MSFT,0.08
UNKNOWN,0.03
```

Ungueltige Beispiele:

```csv
ticker,weight
AAPL,0.12
```

```csv
symbol,weight
,0.12
MSFT,
NVDA,not-a-number
TSLA,-0.05
 aapl ,0.10
AAPL,0.20
```

## Nutzung im Paper-Runner

`--portfolio-file` zeigt auf eine einzelne CSV-Datei:

```powershell
--portfolio-file portfolios/example_local_portfolio.csv
```

`--portfolio-name` ist nur eine optionale Bezeichnung fuer Reports:

```powershell
--portfolio-name example_local
```

Der Paper-Report dokumentiert den verwendeten Portfolio-Pfad beziehungsweise Dateinamen. So bleibt spaeter nachvollziehbar, welche lokale CSV-Datei als Ist-Portfolio fuer den Run verwendet wurde.

## Praxis mit mehreren lokalen Dateien

Mehrere lokale CSV-Dateien koennen parallel im Ordner liegen, zum Beispiel:

```text
portfolios/example_local_portfolio.csv
portfolios/watchlist_style_portfolio.csv
portfolios/balanced_reference_portfolio.csv
```

Gestartet wird weiterhin jeweils ein einzelner Paper-Run mit genau einer Datei:

```powershell
--portfolio-file portfolios/example_local_portfolio.csv --portfolio-name example_local
```

Es gibt keine Batch-Verarbeitung und keine Personen- oder Mandantenverwaltung. Die Dateinamen dienen nur der lokalen Organisation.

CSV-Gewichte bleiben manuell gepflegte Ist-Gewichte. Sie werden nicht normalisiert und muessen im Human Review bewusst geprueft werden.

## Portfolio Checks im Paper-Report

Paper-Reports zeigen fuer lokale Portfolio-Dateien eine kurze Plausibilitaetsuebersicht. Dazu gehoeren die Anzahl der gelesenen Positionen, die Gewichtssumme, die Abweichung der Gewichtssumme von `1.0` und eine kurze Symbolvorschau.

Die Gewichte werden weiterhin manuell gepflegt und muessen manuell geprueft werden. Eine Summe ungleich `1.0` bleibt erlaubt und fuehrt nicht automatisch zu einem Abbruch. Sie soll im Human Review bewusst bewertet werden.

Die Report-Werte normalisieren keine Gewichte und sind keine Order-, Broker-, Live-Trading- oder Investmentfreigabe.

Es erfolgt keine Multi-Portfolio-Batch-Verarbeitung. Pro Paper-Run wird immer nur die ueber `--portfolio-file` angegebene einzelne CSV-Datei verarbeitet.

Es gibt keine Batch-Verarbeitung, keine Broker- oder Live-Trading-Anbindung, keine Orderlogik und keine Stueckzahl- oder Euro-Berechnung.
