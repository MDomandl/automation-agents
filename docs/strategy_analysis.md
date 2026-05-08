# Strategieanalyse & Risikoprofile

## Ziel

Diese Datei dokumentiert die fachliche Bewertung der vorhandenen Backtest-/Runner-Ergebnisse im Projekt `aktien_oop`.

Nach Abschluss von:

- Phase 1: Universe-Konfiguration
- Phase 2: Run-Vergleich & Reporting

beginnt nun Phase 3:

> Aus den vorhandenen Runs sollen Strategiequalität, Risiken und erste Risikoprofile abgeleitet werden.

---

## Grundprinzip

Ein Run gilt nicht automatisch als gut, nur weil er technisch erfolgreich war oder eine hohe Rendite erzielt hat.

Bewertet werden sollen immer mehrere Dimensionen:

- Rendite
- Risiko
- Drawdown
- Volatilität
- Benchmark-Vergleich
- Konzentration
- Sektorverteilung
- Turnover
- Cash-Verhalten
- Stabilität über unterschiedliche Zeiträume und Universes

---

# 1. Bewertungscheckliste pro Run

## 1.1 Basisdaten

| Kriterium | Wert |
|---|---|
| Run ID | |
| Universe | |
| Universe Count | |
| Risk Profile | |
| Startdatum | |
| Enddatum | |
| Rebalance-Frequenz | |
| Top K | |
| Buffer K | |
| Sector Limit aktiv | |
| Max per Sector | |
| Cash aktiv | |
| SMA/Regime-Filter aktiv | |

---

## 1.2 Performance

| Kennzahl | Wert | Bewertung |
|---|---:|---|
| Final Equity | | |
| Total Return % | | |
| Annual Return % | | |
| Benchmark Return SPY % | | |
| Benchmark Return SXR8.DE % | | |
| Alpha vs SPY | | |
| Alpha vs SXR8.DE | | |

Leitfragen:

- Hat die Strategie den Benchmark geschlagen?
- Ist die Outperformance groß genug, um Aufwand, Risiko und Steuern zu rechtfertigen?
- Ist das Ergebnis plausibel oder wirkt es wie ein Zufallstreffer?

---

## 1.3 Risiko

| Kennzahl | Wert | Bewertung |
|---|---:|---|
| Max Drawdown % | | |
| Volatilität % | | |
| Sharpe Ratio | | |
| Sortino Ratio | | |
| Worst Month | | |
| Best Month | | |

Leitfragen:

- Wie stark war der schlimmste Rückgang?
- Wäre dieser Rückgang emotional und finanziell akzeptabel?
- Ist die Rendite im Verhältnis zur Schwankung attraktiv?
- Gibt es Phasen, in denen die Strategie deutlich schlechter als der Benchmark läuft?

---

## 1.4 Konzentration

| Kennzahl | Wert | Bewertung |
|---|---:|---|
| Durchschnittliche Anzahl Positionen | | |
| Minimale Anzahl Positionen | | |
| Maximale Einzelposition | | |
| Maximales Sektorgewicht | | |
| Anzahl dominanter Sektoren | | |

Leitfragen:

- Ist das Depot zu stark auf wenige Titel konzentriert?
- Gibt es Klumpenrisiken in einzelnen Sektoren?
- Ist die Strategie faktisch ein Tech-/Growth-Bet?
- Passt die Konzentration zum gewünschten Risikoprofil?

---

## 1.5 Turnover und Handelbarkeit

| Kennzahl | Wert | Bewertung |
|---|---:|---|
| Durchschnittlicher Turnover | | |
| Maximaler Turnover | | |
| Anzahl Rebalances | | |
| Durchschnittliche Anzahl Käufe je Rebalance | | |
| Durchschnittliche Anzahl Verkäufe je Rebalance | | |

Leitfragen:

- Wird zu häufig umgeschichtet?
- Sind die Transaktionskosten realistisch berücksichtigt?
- Ist die Strategie praktisch handelbar?
- Würden Steuern die Performance deutlich reduzieren?

---

## 1.6 Cash- und Regime-Verhalten

| Kennzahl | Wert | Bewertung |
|---|---:|---|
| Durchschnittliche Cash-Quote | | |
| Maximale Cash-Quote | | |
| Anzahl defensiver Phasen | | |
| Verhalten bei Marktstress | | |

Leitfragen:

- Geht die Strategie in schwachen Marktphasen ausreichend in Cash?
- Verpasst sie dadurch starke Erholungen?
- Ist der Regime-Filter eher hilfreich oder bremst er zu stark?
- Ist das Verhalten nachvollziehbar?

---

# 2. Erste Risikoprofile

## 2.1 Konservativ

Ziel:

> Möglichst robuste Strategie mit reduzierter Schwankung und geringerer Konzentration.

Mögliche Parameter:

```toml
profile_name = "conservative"

top_k = 15
buffer_k = 5
use_sector_limits = true
max_per_sector = 2
require_above_sma = true
include_cash = true
max_turnover_cap = 0.25

```

## 03 – Strategieanalyse & Risikoprofile

## 03.3 Fehlende Kennzahlen für die Strategieanalyse

Der aktuelle Run-Vergleich liefert bereits eine gute erste Basis für die fachliche Bewertung verschiedener Universes und Strategievarianten.

Bereits vorhanden sind unter anderem:

| Kennzahl | Status |
|---|---|
| Total Return % | vorhanden |
| CAGR % | vorhanden |
| Max Drawdown % | vorhanden |
| Volatilität % | vorhanden |
| Sharpe Ratio | vorhanden |
| Turnover % | vorhanden |
| Alpha % | vorhanden |
| Trades Count | vorhanden |
| Average Positions | vorhanden |
| Last Position Count | vorhanden |
| Last Decision Tickers | vorhanden |
| Portfolio Overlap | vorhanden |

Diese Kennzahlen reichen für eine erste grobe Bewertung aus.

Für eine belastbare Strategieanalyse und spätere Risikoprofile fehlen jedoch noch zusätzliche Kennzahlen.

---

### 03.3.1 Benchmark-Kennzahlen

Aktuell wird zwar `alpha_pct` ausgegeben, aber die zugrunde liegenden Benchmark-Kennzahlen sind im Vergleichsreport noch nicht sichtbar.

Benötigt werden:

| Kennzahl | Zweck |
|---|---|
| Benchmark Return % | Direkter Renditevergleich |
| Benchmark CAGR % | Annualisierter Vergleich |
| Benchmark Max Drawdown % | Risiko gegen Benchmark bewerten |
| Benchmark Volatilität % | Schwankung gegen Benchmark bewerten |
| Benchmark Sharpe Ratio | Risiko-Rendite-Verhältnis vergleichen |

Warum wichtig:

Eine Strategie mit leicht negativem Alpha kann trotzdem interessant sein, wenn sie deutlich weniger Drawdown oder Volatilität als der Benchmark hat.

Ohne Benchmark-Risiko sehen wir aktuell nur einen Teil des Bildes.

---

### 03.3.2 Monats- und Phasenanalyse

Benötigt werden:

| Kennzahl | Zweck |
|---|---|
| Monthly Returns | Verlauf besser verstehen |
| Worst Month % | Schlechteste Einzelphase erkennen |
| Best Month % | Positive Ausreißer erkennen |
| Negative Months Count | Häufigkeit negativer Monate |
| Positive Months Count | Stabilität positiver Monate |
| Max Losing Streak | Länge schwacher Phasen |

Warum wichtig:

Ein guter Gesamtertrag kann durch wenige starke Monate entstehen. Für ein Echtgeld-System ist aber wichtig, wie sich die Strategie in schlechten Phasen verhält.

---

### 03.3.3 Konzentration und Sektorstruktur

Benötigt werden:

| Kennzahl | Zweck |
|---|---|
| Max Single Position Weight | Einzelwertrisiko erkennen |
| Average Single Position Weight | typische Positionsgröße |
| Max Sector Weight | Klumpenrisiko erkennen |
| Sector Distribution | Portfolio-Struktur verstehen |
| Sector Count | Diversifikation über Sektoren |
| Dominant Sector | stärkste sektorale Abhängigkeit |

Warum wichtig:

Die aktuelle Strategie hält zuletzt 9 Positionen. Das ist grundsätzlich konzentriert. Entscheidend ist daher, ob diese 9 Positionen breit genug über Sektoren verteilt sind oder faktisch ein Tech-/Growth-Bet entstehen kann.

---

### 03.3.4 Cash- und Regime-Verhalten

Benötigt werden:

| Kennzahl | Zweck |
|---|---|
| Average Cash % | durchschnittliche defensive Quote |
| Max Cash % | stärkste defensive Phase |
| Cash Periods Count | Häufigkeit von Cash-Phasen |
| Time in Market % | investierte Zeit |
| Time in Cash % | defensive Zeit |
| Regime Filter Active Count | Häufigkeit aktiver Regime-Bremse |

Warum wichtig:

Wenn Cash und SMA-/Regime-Filter aktiv sind, muss sichtbar werden, ob sie wirklich schützen oder ob sie hauptsächlich Rendite kosten.

---

### 03.3.5 Turnover je Rebalance

Aktuell wird ein aggregierter Turnover angezeigt. Für die praktische Handelbarkeit sind detailliertere Werte hilfreich.

Benötigt werden:

| Kennzahl | Zweck |
|---|---|
| Average Turnover per Rebalance | typische Umschichtung |
| Max Turnover per Rebalance | Extremwert erkennen |
| Average Trades per Rebalance | operativer Aufwand |
| Max Trades per Rebalance | größter Handelsblock |
| Buy Count | Kaufaktivität |
| Sell Count | Verkaufsaktivität |

Warum wichtig:

Eine Strategie kann im Durchschnitt gut aussehen, aber einzelne Rebalance-Termine können sehr hohe Umschichtungen erzeugen. Für Steuern, Gebühren und praktische Umsetzung ist das wichtig.

---

### 03.3.6 Stabilität über Zeiträume

Benötigt werden:

| Kennzahl | Zweck |
|---|---|
| Performance by Year | Jahresstabilität |
| Drawdown by Year | Risikostabilität |
| Alpha by Year | Benchmark-Mehrwert je Jahr |
| Sharpe by Year | Risiko-Rendite je Jahr |
| Turnover by Year | Handelsaktivität je Jahr |

Warum wichtig:

Eine Strategie sollte nicht nur in einem einzelnen Zeitraum gut aussehen. Besonders wichtig ist, ob sie in unterschiedlichen Marktphasen plausibel bleibt.

---

## 03.4 Priorisierung für die Reporting-Erweiterung

Für die nächste technische Erweiterung sollten nicht alle Kennzahlen auf einmal umgesetzt werden.

Die erste sinnvolle Ausbaustufe ist:

### 03.4.1 Prio 1

| Kennzahl | Grund |
|---|---|
| Benchmark Return % | Alpha besser erklärbar machen |
| Benchmark CAGR % | annualisierter Vergleich |
| Benchmark Max Drawdown % | Risiko gegen Benchmark |
| Benchmark Volatilität % | Schwankung gegen Benchmark |
| Benchmark Sharpe Ratio | Rendite-Risiko-Vergleich |

### 03.4.2 Prio 2

| Kennzahl | Grund |
|---|---|
| Worst Month % | psychologisch wichtig |
| Best Month % | Ausreißer erkennen |
| Monthly Returns | Verlauf analysieren |
| Negative Months Count | Stabilität bewerten |

### 03.4.3 Prio 3

| Kennzahl | Grund |
|---|---|
| Max Sector Weight | Klumpenrisiko |
| Sector Distribution | Struktur verstehen |
| Max Single Position Weight | Einzelwertrisiko |

### 03.4.4 Prio 4

| Kennzahl | Grund |
|---|---|
| Average Cash % | defensive Wirkung |
| Max Cash % | Regime-Verhalten |
| Time in Market % | Investitionsgrad |

---

## 03.5 Erste technische Schlussfolgerung

Der aktuelle Report ist bereits ausreichend, um grob zu erkennen:

- `sp500_top100` war im ersten Vergleich besser als `sp500`
- die Verbesserung kam vor allem durch geringeren Drawdown, geringere Volatilität und weniger Turnover
- die Rendite war nur minimal besser
- das Portfolio unterschied sich stark, daher ist die Universe-Wahl fachlich sehr relevant

Für eine belastbare Entscheidung fehlen aber noch Benchmark-Risiko, Sektorstruktur, Cash-Verhalten und Monatsanalyse.

Die nächste technische Aufgabe lautet daher:

> Das Run-Reporting so erweitern, dass Benchmark- und Risikokennzahlen vollständiger sichtbar werden.
## Erste Auswertung: sp500 vs sp500_top100

Verglichen wurden die Runs:

- A: 20260505_230805, Universe `sp500`, 503 Werte
- B: 20260505_205318, Universe `sp500_top100`, 100 Werte

Der Vergleich zeigt in diesem Zeitraum eine klare Tendenz zugunsten der Top100-Variante.

Während die Rendite nur geringfügig besser ist, verbessert sich das Risikoprofil deutlich:

- Total Return: 20,34 % vs. 20,66 %
- CAGR: 13,72 % vs. 13,93 %
- Max Drawdown: -24,45 % vs. -16,04 %
- Volatilität: 25,30 % vs. 17,70 %
- Sharpe Ratio: 0,64 vs. 0,83
- Turnover: 48,83 % vs. 34,21 %
- Trades Count: 20 vs. 6

Damit erreicht `sp500_top100` in diesem Vergleich eine leicht höhere Rendite bei deutlich geringerem Risiko und weniger Handelsaktivität.

Auffällig ist allerdings, dass sich die finalen Portfolios stark unterscheiden. Nur 2 von 9 Titeln überschneiden sich. Das zeigt, dass die Universe-Auswahl einen erheblichen Einfluss auf die Strategieentscheidungen hat.

Vorläufige Bewertung:

- `sp500`: beobachten, eher offensiver/volatiler
- `sp500_top100`: geeigneter Kandidat für weitere Prüfung, Profilnähe ausgewogen bis konservativ

Einschränkung:

Dieser Vergleich reicht noch nicht als endgültige Entscheidung. Die Top100-Variante sollte über weitere Zeiträume und gegen vollständige Benchmark-Kennzahlen geprüft werden.

## 03.6 Codex-Anweisung – Reporting-Erweiterung Prio 1

Wir arbeiten im Projekt `aktien_oop`.

Ausgangslage:
- Phase 1 Universe-Konfiguration ist erledigt.
- Phase 2 Run-Vergleich & Reporting ist erledigt.
- Der bestehende Vergleich läuft z. B. über:

```bash
python -m scripts.compare_runs 20260505_230805 20260505_205318
```

## 03.7 Erste Bewertung mit Benchmark SXR8.DE

Nach Erweiterung des Reports werden nun Benchmark-Kennzahlen für `SXR8.DE` sichtbar.

Verglichen wurden:

- A: `sp500`, Run `20260505_230805`
- B: `sp500_top100`, Run `20260505_205318`
- Benchmark: `SXR8.DE`

| Kennzahl | A: sp500 | B: sp500_top100 | Benchmark SXR8.DE |
|---|---:|---:|---:|
| Total Return | 20.34% | 20.66% | 22.85% |
| CAGR | 13.72% | 13.93% | 15.36% |
| Volatilität | 25.30% | 17.70% | 16.90% |
| Sharpe Ratio | 0.6400 | 0.8300 | 0.9300 |
| Max Drawdown | -24.45% | -16.04% | n/a |
| Turnover | 48.83% | 34.21% | n/a |

### Interpretation

Die Top100-Variante bleibt im direkten Strategievergleich klar besser als die Full-S&P500-Variante. Sie erzielt eine leicht höhere Rendite, deutlich geringere Volatilität, deutlich geringeren Drawdown, eine bessere Sharpe Ratio und weniger Turnover.

Gegen den Benchmark `SXR8.DE` ist das Bild jedoch weniger überzeugend. Beide Strategievarianten bleiben bei Total Return und CAGR hinter dem Benchmark zurück. Auch die Sharpe Ratio des Benchmarks ist höher als die der Strategien. Die Top100-Variante liegt bei der Volatilität nur knapp über dem Benchmark, erreicht aber dessen Rendite-Risiko-Verhältnis noch nicht.

Das negative `alpha_pct` ist damit fachlich nachvollziehbar.

### Vorläufige Bewertung

- `sp500`: Beobachten / aktuell nicht bevorzugt
- `sp500_top100`: Bester Strategiekandidat innerhalb dieses Vergleichs, aber noch kein klarer Benchmark-Schläger
- `SXR8.DE`: In diesem Zeitraum weiterhin stärkerer Referenzmaßstab

### Offene Lücke

Der Benchmark-Max-Drawdown wird aktuell noch als `n/a` ausgegeben. Diese Kennzahl ist wichtig, um zu bewerten, ob die Strategie zumindest beim maximalen Rückgang einen Vorteil gegenüber dem Benchmark bietet.

## 03.8 Benchmark Max Drawdown ergänzt

Der Vergleich wurde um `benchmark_max_drawdown_pct` erweitert. Damit ist der Benchmark-Vergleich nun deutlich aussagekräftiger.

Verglichen wurden:

- A: `sp500`, Run `20260505_230805`
- B: `sp500_top100`, Run `20260505_205318`
- Benchmark: `SXR8.DE`

| Kennzahl | A: sp500 | B: sp500_top100 | Benchmark SXR8.DE |
|---|---:|---:|---:|
| Total Return | 20.34% | 20.66% | 22.85% |
| CAGR | 13.72% | 13.93% | 15.36% |
| Max Drawdown | -24.45% | -16.04% | -23.32% |
| Volatilität | 25.30% | 17.70% | 16.90% |
| Sharpe Ratio | 0.6400 | 0.8300 | 0.9300 |
| Turnover | 48.83% | 34.21% | n/a |
| Trades Count | 20 | 6 | n/a |

### Interpretation

Die Top100-Variante bleibt im direkten Strategievergleich klar besser als die Full-S&P500-Variante.

Auffällig ist nun der Benchmark-Drawdown:

- `sp500_top100`: -16.04%
- `SXR8.DE`: -23.32%

Damit zeigt die Top100-Variante in diesem Zeitraum einen deutlich besseren maximalen Rückgang als der Benchmark.

Gleichzeitig bleibt sie bei Total Return, CAGR und Sharpe Ratio hinter dem Benchmark zurück. Die Strategie liefert also aktuell keinen klaren Rendite- oder Sharpe-Vorteil gegenüber `SXR8.DE`, zeigt aber einen relevanten Drawdown-Vorteil.

### Vorläufige Bewertung

- `sp500`: aktuell nicht bevorzugt, da Rendite-Risiko-Profil schwächer als Top100 und Benchmark
- `sp500_top100`: ernsthafter Kandidat für ein ausgewogenes Risikoprofil
- `SXR8.DE`: bleibt in Rendite und Sharpe stärker, hat aber den deutlich höheren Drawdown

### Fazit

`sp500_top100` ist kein klarer Benchmark-Schläger, aber ein interessanter Kandidat, wenn das Ziel nicht maximale Rendite, sondern ein besser kontrollierter Drawdown bei akzeptabler Rendite ist.














## Erste Auswertung: sp500 vs sp500_top100

Verglichen wurden die Runs:

- A: 20260505_230805, Universe `sp500`, 503 Werte
- B: 20260505_205318, Universe `sp500_top100`, 100 Werte

Der Vergleich zeigt in diesem Zeitraum eine klare Tendenz zugunsten der Top100-Variante.

Während die Rendite nur geringfügig besser ist, verbessert sich das Risikoprofil deutlich:

- Total Return: 20,34 % vs. 20,66 %
- CAGR: 13,72 % vs. 13,93 %
- Max Drawdown: -24,45 % vs. -16,04 %
- Volatilität: 25,30 % vs. 17,70 %
- Sharpe Ratio: 0,64 vs. 0,83
- Turnover: 48,83 % vs. 34,21 %
- Trades Count: 20 vs. 6

Damit erreicht `sp500_top100` in diesem Vergleich eine leicht höhere Rendite bei deutlich geringerem Risiko und weniger Handelsaktivität.

Auffällig ist allerdings, dass sich die finalen Portfolios stark unterscheiden. Nur 2 von 9 Titeln überschneiden sich. Das zeigt, dass die Universe-Auswahl einen erheblichen Einfluss auf die Strategieentscheidungen hat.

Vorläufige Bewertung:

- `sp500`: beobachten, eher offensiver/volatiler
- `sp500_top100`: geeigneter Kandidat für weitere Prüfung, Profilnähe ausgewogen bis konservativ

Einschränkung:

Dieser Vergleich reicht noch nicht als endgültige Entscheidung. Die Top100-Variante sollte über weitere Zeiträume und gegen vollständige Benchmark-Kennzahlen geprüft werden.