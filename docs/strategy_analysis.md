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


## 03.9 Bewertungslogik / Ampel für Strategievarianten

Um Strategievarianten vergleichbar zu bewerten, wird eine einfache Ampellogik eingeführt.

Ziel ist nicht, automatisch den höchsten Return zu bevorzugen, sondern ein belastbares Verhältnis aus Rendite, Risiko, Drawdown, Handelbarkeit und Benchmark-Vergleich zu bewerten.

---

### 03.9.1 Bewertungsstufen

| Status | Bedeutung |
|---|---|
| Geeignet | Kandidat für weitere Live-nahe Tests |
| Beobachten | Interessant, aber noch nicht ausreichend bestätigt |
| Nur Test | Fachlich lehrreich, aber aktuell nicht investierbar |
| Verwerfen | Kein sinnvoller Kandidat |

---

### 03.9.2 Geeignet

Eine Strategievariante kann als `Geeignet` gelten, wenn mehrere der folgenden Punkte erfüllt sind:

| Kriterium | Ziel |
|---|---|
| CAGR | nahe am Benchmark oder besser |
| Total Return | nahe am Benchmark oder besser |
| Max Drawdown | deutlich besser als Benchmark oder zumindest nicht schlechter |
| Volatilität | nicht deutlich höher als Benchmark |
| Sharpe Ratio | nahe am Benchmark oder besser |
| Turnover | praktisch handelbar |
| Trades Count | nicht unnötig hoch |
| Portfolio-Struktur | nachvollziehbar und nicht extrem konzentriert |
| Ergebnisstabilität | über mehrere Zeiträume plausibel |

Wichtig:

Eine Strategie muss nicht in jeder Kennzahl besser als der Benchmark sein. Besonders interessant sind Varianten, die etwas weniger Rendite liefern, dafür aber deutlich weniger Drawdown oder weniger Stress erzeugen.

---

### 03.9.3 Beobachten

Eine Strategievariante wird als `Beobachten` eingestuft, wenn sie grundsätzlich interessant ist, aber noch nicht ausreichend belastbar wirkt.

Typische Fälle:

| Situation | Beispiel |
|---|---|
| Drawdown besser, aber Rendite schwächer | geringeres Risiko, aber unklarer Mehrwert |
| Sharpe schwächer, aber Turnover niedrig | praktisch interessant, aber Rendite-Risiko noch nicht überzeugend |
| Nur ein Zeitraum getestet | Ergebnis noch nicht robust |
| Stark anderes Portfolio | Universe-Effekt noch unklar |
| Benchmark wird nicht geschlagen | Strategie braucht weitere Begründung |

Diese Kategorie ist wichtig, weil viele Varianten nicht sofort verworfen werden sollten. Gerade risikoärmere Varianten können trotz schwächerer Rendite sinnvoll sein.

---

### 03.9.4 Nur Test

Eine Strategievariante wird als `Nur Test` eingestuft, wenn sie fachlich interessant, aber für echtes Geld aktuell nicht geeignet ist.

Typische Fälle:

| Situation | Grund |
|---|---|
| Sehr hohe Rendite bei sehr hoher Konzentration | Klumpenrisiko |
| Sehr hoher Turnover | Kosten und Steuern problematisch |
| Sehr hohe Volatilität | emotional schwer durchhaltbar |
| Nur in einem Spezialzeitraum gut | Gefahr von Overfitting |
| Starke Abhängigkeit von wenigen Titeln | Einzelwertrisiko |

Diese Kategorie ist nützlich für offensive Experimente, aber nicht als Live-Kandidat.

---

### 03.9.5 Verwerfen

Eine Strategievariante wird verworfen, wenn sie keinen erkennbaren fachlichen Vorteil bietet.

Typische Fälle:

| Situation | Grund |
|---|---|
| Rendite schlechter als Benchmark | kein Mehrwert |
| Drawdown schlechter als Benchmark | höheres Risiko |
| Volatilität schlechter als Benchmark | mehr Schwankung |
| Sharpe deutlich schlechter als Benchmark | schlechtes Rendite-Risiko-Verhältnis |
| Turnover hoch | Aufwand/Kosten ohne Nutzen |
| Verhalten nicht erklärbar | mangelndes Vertrauen |

Eine Variante muss nicht sofort verworfen werden, nur weil sie einmal schlechter abschneidet. Wenn sie aber wiederholt schlechter als Benchmark und Alternativen ist, sollte sie nicht weiter priorisiert werden.

---

### 03.9.6 Vorläufige Anwendung auf den aktuellen Vergleich

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

#### Bewertung A: sp500

Status: `Beobachten / eher nicht bevorzugt`

Begründung:

- Rendite unter Benchmark
- CAGR unter Benchmark
- Max Drawdown schlechter als Benchmark
- Volatilität deutlich höher als Benchmark
- Sharpe Ratio deutlich niedriger als Benchmark
- mehr Turnover als Top100
- mehr Trades als Top100

A ist in diesem Vergleich nicht attraktiv genug, um als bevorzugter Kandidat zu gelten.

#### Bewertung B: sp500_top100

Status: `Beobachten mit Tendenz Geeignet`

Begründung:

- Rendite leicht unter Benchmark
- CAGR leicht unter Benchmark
- Sharpe Ratio unter Benchmark
- Volatilität nur leicht über Benchmark
- Max Drawdown deutlich besser als Benchmark
- deutlich besser als A
- weniger Turnover als A
- deutlich weniger Trades als A

B ist kein klarer Benchmark-Schläger, aber ein ernsthafter Kandidat für ein ausgewogenes Risikoprofil, weil der Drawdown deutlich besser kontrolliert wird.

---

### 03.9.7 Aktuelles Fazit

Die Top100-Variante ist im bisherigen Vergleich die interessantere Strategievariante.

Sie liefert zwar weniger Rendite und eine niedrigere Sharpe Ratio als `SXR8.DE`, reduziert aber den maximalen Drawdown deutlich.

Damit passt sie eher zu einem Profil, bei dem nicht maximale Rendite, sondern kontrolliertes Risiko und geringere Rückgänge im Vordergrund stehen.

Vorläufige Einstufung:

| Variante | Status |
|---|---|
| sp500 | Beobachten / aktuell nicht bevorzugt |
| sp500_top100 | Beobachten mit Tendenz Geeignet |
| SXR8.DE Benchmark | Starker Referenzmaßstab |

Nächste Prüfungen sollten zeigen, ob der Drawdown-Vorteil von `sp500_top100` auch über andere Zeiträume und weitere Runs stabil bleibt.


## 03.10 Nächste Testmatrix

Nach der ersten Bewertung zeigt `sp500_top100` gegenüber `sp500` ein deutlich besseres Risikoprofil und insbesondere einen besseren Max Drawdown.

Gleichzeitig schlägt `sp500_top100` den Benchmark `SXR8.DE` noch nicht bei Rendite, CAGR oder Sharpe Ratio.

Deshalb soll als nächster Schritt geprüft werden, ob der Drawdown-Vorteil der Top100-Variante stabil ist oder nur aus diesem einen Zeitraum stammt.

---

### 03.10.1 Ziel der Testmatrix

Die Testmatrix soll beantworten:

| Frage | Zweck |
|---|---|
| Bleibt `sp500_top100` über verschiedene Zeiträume risikoärmer? | Robustheit prüfen |
| Ist der geringere Drawdown stabil? | wichtig für Echtgeld-Einsatz |
| Wie stark hängt das Ergebnis vom Startzeitpunkt ab? | Zeitraumrisiko erkennen |
| Bleibt der Turnover niedriger? | Handelbarkeit prüfen |
| Wie oft schlägt die Strategie den Benchmark? | Mehrwert prüfen |
| Wie oft ist die Strategie defensiver als der Benchmark? | Risikoprofil prüfen |

---

### 03.10.2 Erste Testdimension: Universe

Zunächst werden nur die beiden bereits vorhandenen Universes verglichen:

| Universe | Beschreibung |
|---|---|
| `sp500` | vollständiges S&P500-Universe |
| `sp500_top100` | eingeschränktes Top100-Universe |

Weitere Universes werden später ergänzt, damit die Analyse nicht zu breit wird.

---

### 03.10.3 Zweite Testdimension: Zeitraum

Für die nächste Prüfung sollen mehrere Zeiträume verwendet werden.

| Zeitraum | Zweck |
|---|---|
| SHORT | schneller Smoke-/Plausibilitätstest |
| MEDIUM | mittlere Historie, erster robuster Vergleich |
| LONG | tieferer Validierungslauf |

Wenn technisch verfügbar, sollten zusätzlich explizite Startzeitpunkte getestet werden:

| Start | Zweck |
|---|---|
| 2023-04-08 | entspricht ungefähr MEDIUM |
| 2024-04-08 | entspricht ungefähr SHORT |
| kompletter verfügbarer Zeitraum | Langfristprüfung |

---

### 03.10.4 Dritte Testdimension: Profil

Zunächst bleibt das Strategieprofil unverändert.

Das bedeutet:

| Parameterbereich | Entscheidung |
|---|---|
| `top_k` | unverändert |
| `buffer_k` | unverändert |
| `max_per_sector` | unverändert |
| `use_sector_limits` | unverändert |
| `cash/regime_filter` | unverändert |
| `turnover_cap` | unverändert |

Begründung:

Bevor neue Risikoprofile gebaut werden, soll zuerst verstanden werden, ob die Universe-Wahl allein einen stabilen Effekt hat.

---

### 03.10.5 Konkrete erste Testmatrix

| Test | Universe A | Universe B | Profil | Zeitraum | Ziel |
|---|---|---|---|---|---|
| T1 | `sp500` | `sp500_top100` | aktuelles Standardprofil | SHORT | schneller Plausibilitätscheck |
| T2 | `sp500` | `sp500_top100` | aktuelles Standardprofil | MEDIUM | Hauptvergleich |
| T3 | `sp500` | `sp500_top100` | aktuelles Standardprofil | LONG | Robustheitsprüfung |

---

### 03.10.6 Auswertung je Test

Jeder Test soll mindestens folgende Kennzahlen enthalten:

| Kennzahl | Bewertung |
|---|---|
| Total Return | Strategie vs Strategie und Benchmark |
| CAGR | annualisierte Rendite |
| Alpha | Benchmark-Mehrwert |
| Max Drawdown | wichtigste Risikokennzahl |
| Volatilität | Schwankungsrisiko |
| Sharpe Ratio | Rendite-Risiko-Verhältnis |
| Turnover | Handelbarkeit |
| Trades Count | praktischer Aufwand |
| Avg Positions | Konzentration |
| Last Decision Overlap | Universe-Effekt |

---

### 03.10.7 Entscheidungskriterien nach der Testmatrix

`sp500_top100` wird stärker priorisiert, wenn es in mehreren Zeiträumen:

- niedrigeren Max Drawdown als `sp500` zeigt
- niedrigeren oder ähnlichen Turnover zeigt
- ähnliche oder bessere Rendite als `sp500` liefert
- nicht deutlich schlechter als der Benchmark abschneidet
- nachvollziehbare Portfolioentscheidungen erzeugt

`sp500_top100` bleibt nur Beobachtungskandidat, wenn:

- der Drawdown-Vorteil nur in einem Zeitraum auftritt
- die Rendite dauerhaft deutlich unter Benchmark liegt
- Sharpe Ratio dauerhaft deutlich unter Benchmark liegt
- die Ergebnisse stark vom Zeitraum abhängen

`sp500` wird wieder interessanter, wenn:

- es in längeren Zeiträumen deutlich mehr Rendite liefert
- der Drawdown-Nachteil nicht stabil ist
- der höhere Turnover durch deutlich bessere Performance gerechtfertigt wird

---

### 03.10.8 Vorläufige technische Aufgabe

Als nächstes soll ein reproduzierbarer Vergleich für SHORT, MEDIUM und LONG erzeugt werden.

Zielausgabe pro Vergleich:

- Run A
- Run B
- Benchmark
- Performance-Kennzahlen
- Benchmark-Kennzahlen
- Trading-/Portfolio-Kennzahlen
- Ampelbewertung nach Abschnitt 03.9

Die Ergebnisse werden anschließend in `strategy_analysis.md` dokumentiert.

## 03.11 Testmatrix sp500 vs sp500_top100

Die Testmatrix für `sp500` gegen `sp500_top100` wurde für die Profile SHORT, MEDIUM und LONG erzeugt.

Erzeugte Reports:

- `reports/strategy_analysis/compare_sp500_vs_top100_SHORT.md`
- `reports/strategy_analysis/compare_sp500_vs_top100_MEDIUM.md`
- `reports/strategy_analysis/compare_sp500_vs_top100_LONG.md`
- `reports/strategy_analysis/testmatrix_summary.md`

Run IDs:

| Test | Profil | Run A sp500 | Run B sp500_top100 |
|---|---|---|---|
| T1 | SHORT | 20260510_084005 | 20260510_084937 |
| T2 | MEDIUM | 20260510_085124 | 20260510_090928 |
| T3 | LONG | 20260510_091300 | 20260510_094326 |

### Ergebnisübersicht

| Test | Return Winner | Risk Winner | Sharpe Winner | Turnover Winner |
|---|---|---|---|---|
| SHORT | sp500 | sp500_top100 | sp500_top100 | sp500_top100 |
| MEDIUM | sp500_top100 | sp500_top100 | sp500_top100 | sp500_top100 |
| LONG | sp500 | sp500_top100 | sp500 | sp500_top100 |

### Interpretation

`sp500_top100` gewinnt in allen drei Zeiträumen beim Risiko beziehungsweise Max Drawdown und beim Turnover. Damit zeigt die Top100-Variante ein stabil defensiveres Verhalten.

Bei Return und Sharpe ist das Bild gemischt:

- In SHORT gewinnt `sp500` bei Return.
- In MEDIUM gewinnt `sp500_top100` bei Return und Sharpe.
- In LONG gewinnt `sp500` bei Return und Sharpe.

Gegenüber dem Benchmark `SXR8.DE` zeigt `sp500_top100` durchgehend einen besseren beziehungsweise minimal besseren Drawdown, bleibt aber bei CAGR und Sharpe hinter dem Benchmark zurück.

### Fachliche Schlussfolgerung

Die Top100-Variante ist kein klarer Benchmark-Schläger, aber ein robuster Kandidat für ein risikoärmeres Profil.

Die Full-S&P500-Variante bleibt interessant für renditeorientiertere Tests, zeigt aber durchgehend höhere Risiken und mehr Turnover.

Vorläufige Einordnung:

| Universe | Vorläufiges Profil |
|---|---|
| sp500_top100 | Conservative / Balanced |
| sp500 | Balanced / Offensive |

### Fazit

Die Universe-Wahl hat einen stabilen fachlichen Effekt.

`sp500_top100` reduziert Drawdown und Turnover konsistent über SHORT, MEDIUM und LONG. Damit eignet sich diese Variante besonders als Basis für die ersten konservativen und ausgewogenen Risikoprofile.

`sp500` kann in längeren oder kürzeren Zeiträumen mehr Rendite liefern, ist aber risikoreicher und handelsaktiver.



## 03.12 Parameter-Sensitivität und Agenten-Spielwiese

Die aktuellen Tests dienen zunächst dazu, Reporting, Benchmark-Vergleich und Bewertungslogik zu stabilisieren.

Die eigentliche Untersuchung der Config-Parameter erfolgt danach systematisch als Parameter-Sensitivitätsanalyse.

Ziel ist nicht, wahllos viele Kombinationen zu testen, sondern jeweils gezielt einen Parameter oder eine kleine Parametergruppe zu verändern und deren Einfluss auf Rendite, Drawdown, Volatilität, Sharpe, Turnover und Benchmark-Abstand zu messen.

Wichtige Parametergruppen:

| Gruppe | Parameter | Zweck |
|---|---|---|
| Positionsanzahl | top_k, buffer_k | Konzentration vs. Diversifikation |
| Sektorsteuerung | use_sector_limits, max_per_sector | Klumpenrisiko |
| Regime/Cash | require_above_sma, regime_below_action, include_cash | defensives Verhalten |
| Turnover | max_turnover_cap, friction_eps | Handelbarkeit |
| Signalzeitraum | score_days, vol_days | Stabilität der Auswahl |
| Kosten/Realismus | slippage_bps, cost_bps, weight_round_step | Live-Nähe |

Die spätere Aufgabe des Agenten ist es, diese Parameter-Sensitivitätsanalysen automatisiert auszuführen, Reports zu erzeugen und Varianten nach der Ampellogik zu bewerten.

Vorher müssen jedoch die Messgrößen und Bewertungskriterien stabil sein, damit der Agent keine zufälligen oder überoptimierten Ergebnisse bevorzugt.


## 03.12 Parameter-Sensitivität und Agenten-Spielwiese

Die bisherigen Tests dienen zunächst dazu, Reporting, Benchmark-Vergleich, Universe-Vergleich und Bewertungslogik zu stabilisieren.

Die eigentliche Untersuchung der Config-Parameter erfolgt danach systematisch als Parameter-Sensitivitätsanalyse.

Ziel ist nicht, wahllos viele Kombinationen zu testen, sondern jeweils gezielt einen Parameter oder eine kleine Parametergruppe zu verändern und deren Einfluss auf Rendite, Drawdown, Volatilität, Sharpe Ratio, Turnover und Benchmark-Abstand zu messen.

---

### 03.12.1 Warum Parameter nicht sofort breit optimiert werden

Das Projekt enthält mehrere strategierelevante Parameter, zum Beispiel:

| Parameter | Wirkung |
|---|---|
| `top_k` | Anzahl der Zielpositionen |
| `buffer_k` | Stabilität der Auswahl / weniger Wechsel |
| `max_per_sector` | Begrenzung von Sektorklumpen |
| `use_sector_limits` | Aktivierung der Sektorbegrenzung |
| `require_above_sma` | defensiver Regime-Filter |
| `regime_below_action` | Verhalten bei negativem Marktregime |
| `include_cash` | Cash-Komponente im Portfolio |
| `max_turnover_cap` | Begrenzung der Umschichtung |
| `score_days` | Zeitraum für Momentum-/Score-Berechnung |
| `vol_days` | Zeitraum für Volatilitätsberechnung |
| `slippage_bps` | angenommene Handelskosten durch Slippage |
| `cost_bps` | angenommene Transaktionskosten |
| `weight_round_step` | Rundung der Zielgewichte |

Wenn diese Parameter gleichzeitig verändert werden, ist später nicht mehr klar erkennbar, welcher Parameter welchen Effekt verursacht hat.

Deshalb gilt:

> Erst Ursache und Wirkung einzelner Parameter verstehen, dann Kombinationen testen.

---

### 03.12.2 Ziel der Parameter-Sensitivität

Die Parameter-Sensitivität soll beantworten:

| Frage | Zweck |
|---|---|
| Welche Parameter beeinflussen den Drawdown am stärksten? | Risikosteuerung |
| Welche Parameter beeinflussen die Rendite am stärksten? | Renditechance |
| Welche Parameter reduzieren Turnover? | Handelbarkeit |
| Welche Parameter verschlechtern Sharpe oder CAGR? | Qualitätskontrolle |
| Welche Parameter führen zu instabilen Ergebnissen? | Overfitting vermeiden |
| Welche Parameter sind nahezu wirkungslos? | Komplexität reduzieren |

Wichtig ist dabei nicht nur die beste Einzelkombination, sondern das Verhalten über mehrere Zeiträume und Universes.

---

### 03.12.3 Parametergruppen

Die Parameter werden in Gruppen betrachtet.

| Gruppe | Parameter | Ziel |
|---|---|---|
| Positionsanzahl | `top_k`, `buffer_k` | Konzentration vs. Diversifikation |
| Sektorsteuerung | `use_sector_limits`, `max_per_sector` | Klumpenrisiko begrenzen |
| Regime/Cash | `require_above_sma`, `regime_below_action`, `include_cash` | defensives Verhalten |
| Turnover | `max_turnover_cap`, `friction_eps`, `friction_eps_pct` | Handelsaktivität reduzieren |
| Signalzeitraum | `score_days`, `vol_days` | Stabilität der Auswahl |
| Kosten/Realismus | `slippage_bps`, `cost_bps`, `weight_round_step` | Live-Nähe verbessern |

---

### 03.12.4 Erste sinnvolle Testreihen

#### Positionsanzahl: `top_k`

| Variante | `top_k` | Erwartung |
|---|---:|---|
| konzentriert | 8 | höhere Renditechance, höheres Einzelwertrisiko |
| Standard | 12 | aktueller Referenzwert |
| breiter | 15 | weniger Einzelwertrisiko, eventuell weniger Signalstärke |
| sehr breit | 20 | defensiver, aber möglicherweise verwässerte Auswahl |

Zu messen:

- Return
- CAGR
- Max Drawdown
- Volatilität
- Sharpe Ratio
- Turnover
- Benchmark-Abstand
- durchschnittliche Positionsanzahl

---

#### Sektorbegrenzung: `max_per_sector`

| Variante | `max_per_sector` | Erwartung |
|---|---:|---|
| streng | 2 | weniger Klumpenrisiko |
| Standard | 3 | aktueller Referenzwert |
| locker | 4 | mehr Renditechance, mehr Sektorrisiko |
| offen | deaktiviert | maximale Freiheit, höheres Klumpenrisiko |

Zu messen:

- Max Sector Weight
- Sector Count
- Drawdown
- Sharpe Ratio
- Return
- Portfolio-Konzentration

---

#### Turnover-Begrenzung: `max_turnover_cap`

| Variante | `max_turnover_cap` | Erwartung |
|---|---:|---|
| sehr ruhig | 0.20 | wenig Handel, eventuell träger |
| ausgewogen | 0.35 | kontrollierter Wechsel |
| flexibel | 0.50 | mehr Anpassung |
| offen | 1.00 | fast ungebremst |

Zu messen:

- Turnover
- Trades Count
- Return
- CAGR
- Drawdown
- Sharpe Ratio
- steuerliche/praktische Handelbarkeit

---

#### Regime- und Cash-Verhalten

| Variante | `require_above_sma` | `include_cash` | Erwartung |
|---|---|---|---|
| defensiv | true | true | geringerer Drawdown, eventuell Renditeverlust |
| investiert mit Regime | true | false | Signalfilter ohne Cash-Puffer |
| immer investiert | false | false | höhere Renditechance, höherer Drawdown |
| Cash ohne strengen Filter | false | true | nur sinnvoll, wenn logisch sauber definiert |

Zu messen:

- Time in Market
- Average Cash %
- Max Cash %
- Max Drawdown
- verpasste Erholungsphasen
- Benchmark-Abstand

---

#### Signalzeitraum: `score_days` und `vol_days`

| Variante | `score_days` | `vol_days` | Erwartung |
|---|---:|---:|---|
| kurzfristiger | 126 | 42 | reagiert schneller, mehr Wechsel |
| Standard | 200 | 63 | aktueller Referenzwert |
| langfristiger | 252 | 63 | stabiler, langsamer |
| sehr langfristig | 252 | 126 | defensiver, eventuell träger |

Zu messen:

- Auswahlstabilität
- Turnover
- Return
- Drawdown
- Sharpe Ratio
- Portfolio-Overlap zwischen Rebalances

---

### 03.12.5 Vorgehensweise für Parameter-Tests

Für Parameter-Tests gilt:

1. Es wird immer ein Referenzlauf definiert.
2. Pro Testreihe wird nur ein Parameter oder eine eng zusammenhängende Parametergruppe verändert.
3. Jeder Test wird über SHORT, MEDIUM und LONG geprüft.
4. Jeder Test wird gegen Benchmark ausgewertet.
5. Jeder Test erhält eine Ampelbewertung nach Abschnitt 03.9.
6. Ergebnisse werden in einer Matrix dokumentiert.
7. Auffällige Varianten werden nicht sofort übernommen, sondern in weiteren Zeiträumen validiert.

Beispiel:

| Testreihe | Parameter | Varianten | Universe |
|---|---|---|---|
| P1 | `top_k` | 8 / 12 / 15 / 20 | zunächst `sp500_top100` |
| P2 | `max_per_sector` | 2 / 3 / 4 / off | zunächst `sp500_top100` |
| P3 | `max_turnover_cap` | 0.20 / 0.35 / 0.50 / 1.00 | zunächst `sp500_top100` |
| P4 | Regime/Cash | defensiv / investiert / immer investiert | zunächst `sp500_top100` |
| P5 | `score_days`, `vol_days` | mehrere Fenster | zunächst `sp500_top100` |

---

### 03.12.6 Rolle des Agenten

Die spätere Aufgabe des Agenten ist es, diese Parameter-Sensitivitätsanalysen automatisiert auszuführen.

Der Agent soll perspektivisch:

- Parameter-Sets erzeugen
- Backtests ausführen
- Runner/Compare ausführen
- Reports sammeln
- Kennzahlen extrahieren
- Benchmark-Vergleich durchführen
- Ampelbewertung anwenden
- auffällige Varianten markieren
- Zusammenfassungen schreiben
- Kandidaten für weitere Tests vorschlagen

Der Agent darf dabei nicht einfach die höchste Rendite bevorzugen.

Er soll Varianten bevorzugen, die über mehrere Zeiträume hinweg ein stabiles Verhältnis aus Rendite, Drawdown, Volatilität, Sharpe Ratio, Turnover und Benchmark-Abstand zeigen.

---

### 03.12.7 Schutz vor Overfitting

Bei Parameter-Tests besteht die Gefahr, dass eine Variante nur zufällig im getesteten Zeitraum gut aussieht.

Deshalb gelten folgende Regeln:

| Regel | Zweck |
|---|---|
| Keine Bewertung nur anhand eines einzelnen Runs | Zeitraum-Zufall vermeiden |
| SHORT, MEDIUM und LONG gemeinsam betrachten | Stabilität prüfen |
| Benchmark immer mitführen | ETF-Vergleich sichern |
| Drawdown und Turnover ernst nehmen | Live-Tauglichkeit prüfen |
| Keine zu feine Parametersuche am Anfang | Scheingenauigkeit vermeiden |
| Ergebnisse dokumentieren, nicht nur Gewinner merken | Nachvollziehbarkeit |

Eine Variante ist erst dann interessant, wenn sie nicht nur eine Kennzahl verbessert, sondern das Gesamtbild stabil bleibt.

---

### 03.12.8 Vorläufige Priorisierung

Die erste Parameter-Sensitivität sollte nicht mit allen Parametern gleichzeitig starten.

Empfohlene Reihenfolge:

| Priorität | Testreihe | Grund |
|---|---|---|
| 1 | `top_k` | beeinflusst Konzentration und Risiko direkt |
| 2 | `max_per_sector` | wichtig gegen Klumpenrisiko |
| 3 | `max_turnover_cap` | wichtig für Handelbarkeit |
| 4 | Regime/Cash | wichtig für Drawdown-Schutz |
| 5 | `score_days` / `vol_days` | wichtig für Signallogik |

Als Start-Universe bietet sich `sp500_top100` an, weil es in der bisherigen Testmatrix stabilere Risiko- und Turnover-Werte gezeigt hat.

---

### 03.12.9 Fazit

Die bisherigen Universe- und Benchmark-Tests schaffen die Grundlage für spätere Risikoprofile und Agenten-gesteuerte Parameteranalysen.

Die eigentliche Optimierung der Config-Parameter erfolgt bewusst erst nach Stabilisierung der Mess- und Bewertungslogik.

Damit wird verhindert, dass der Agent später zufällige oder überoptimierte Varianten bevorzugt.

Die nächsten sinnvollen Schritte sind:

1. Benchmark-Korrelation und Down-Capture ergänzen.
2. Erste Risikoprofile grob definieren.
3. Danach gezielte Parameter-Sensitivitätsanalysen vorbereiten.


## 03.13 Benchmark-Korrelation und Down-Capture

Nach der Erweiterung um Benchmark-Kennzahlen ist sichtbar, dass `sp500_top100` gegenüber dem Benchmark `SXR8.DE` zwar bei CAGR und Sharpe Ratio zurückbleibt, aber einen deutlich besseren Max Drawdown zeigt.

Um diesen Risiko-Vorteil besser beurteilen zu können, sollen zusätzliche Benchmark-Relationskennzahlen ergänzt werden.

---

### 03.13.1 Ziel

Die neuen Kennzahlen sollen beantworten:

| Frage | Zweck |
|---|---|
| Wie stark korreliert die Strategie mit dem Benchmark? | Benchmark-Abhängigkeit erkennen |
| Wie stark fällt die Strategie, wenn der Benchmark fällt? | Downside-Schutz messen |
| Wie stark steigt die Strategie, wenn der Benchmark steigt? | Upside-Teilnahme messen |
| Ist die Strategie nur ein komplizierter ETF-Ersatz? | Mehrwert prüfen |
| Ist der Drawdown-Vorteil plausibel erklärbar? | Vertrauen erhöhen |

---

### 03.13.2 Neue Kennzahlen

| Kennzahl | Bedeutung |
|---|---|
| `correlation_to_benchmark` | Korrelation der Strategie-Renditen mit Benchmark-Renditen |
| `relative_volatility` | Volatilität der Strategie relativ zur Benchmark-Volatilität |
| `up_capture_ratio` | Teilnahme an positiven Benchmark-Phasen |
| `down_capture_ratio` | Teilnahme an negativen Benchmark-Phasen |
| `tracking_difference` | Renditedifferenz Strategie minus Benchmark |
| `tracking_error` | Schwankung der Differenzrenditen |

---

### 03.13.3 Interpretation der Kennzahlen

#### `correlation_to_benchmark`

Eine hohe Korrelation bedeutet:

> Die Strategie bewegt sich stark ähnlich zum Benchmark.

Eine niedrige Korrelation bedeutet:

> Die Strategie verhält sich eigenständiger.

Bewertung:

| Wert | Interpretation |
|---:|---|
| > 0.90 | sehr benchmarknah |
| 0.70 – 0.90 | deutlich benchmarkabhängig |
| 0.40 – 0.70 | teilweise eigenständiges Verhalten |
| < 0.40 | stark eigenständig oder instabil |

---

#### `relative_volatility`

Diese Kennzahl zeigt:

> Wie stark schwankt die Strategie im Verhältnis zum Benchmark?

Beispiel:

| Wert | Interpretation |
|---:|---|
| 0.80 | Strategie schwankt ca. 20% weniger als Benchmark |
| 1.00 | ähnlich wie Benchmark |
| 1.20 | Strategie schwankt ca. 20% stärker als Benchmark |

---

#### `up_capture_ratio`

Diese Kennzahl zeigt:

> Wie viel von positiven Benchmark-Phasen nimmt die Strategie mit?

Beispiel:

| Wert | Interpretation |
|---:|---|
| 0.80 | Strategie nimmt ca. 80% der positiven Benchmark-Bewegung mit |
| 1.00 | Strategie nimmt ähnlich stark teil |
| 1.20 | Strategie steigt stärker als Benchmark in positiven Phasen |

---

#### `down_capture_ratio`

Diese Kennzahl ist für die Risikobewertung besonders wichtig.

Sie zeigt:

> Wie stark fällt die Strategie, wenn der Benchmark fällt?

Beispiel:

| Wert | Interpretation |
|---:|---|
| 0.60 | Strategie fällt nur ca. 60% so stark wie Benchmark |
| 1.00 | Strategie fällt ähnlich stark |
| 1.20 | Strategie fällt stärker als Benchmark |

Für ein defensives oder ausgewogenes Profil ist besonders interessant:

> `down_capture_ratio < 1.0`

Noch besser:

> `down_capture_ratio` deutlich unter `up_capture_ratio`

Das würde bedeuten:

> Die Strategie nimmt an positiven Phasen teil, verliert aber in negativen Phasen weniger.

---

#### `tracking_difference`

Diese Kennzahl zeigt die Gesamtdifferenz zur Benchmark-Rendite.

Beispiel:

| Wert | Interpretation |
|---:|---|
| +2.00pp | Strategie lag 2 Prozentpunkte über Benchmark |
| -2.00pp | Strategie lag 2 Prozentpunkte unter Benchmark |

---

#### `tracking_error`

Diese Kennzahl zeigt, wie stark die Strategie vom Benchmark abweicht.

Ein hoher Tracking Error bedeutet:

> Die Strategie verhält sich deutlich anders als der Benchmark.

Ein niedriger Tracking Error bedeutet:

> Die Strategie läuft sehr benchmarknah.

---

### 03.13.4 Fachliche Bedeutung für `sp500_top100`

Für `sp500_top100` ist besonders wichtig:

| Kennzahl | Erwartete Aussage |
|---|---|
| `down_capture_ratio` | sollte deutlich unter 1.0 liegen |
| `up_capture_ratio` | sollte nicht zu niedrig sein |
| `correlation_to_benchmark` | darf hoch sein, sollte aber nicht alles erklären |
| `relative_volatility` | sollte ungefähr bei oder unter 1.0 liegen |
| `tracking_difference` | erklärt Renditeabstand zum Benchmark |

Wenn `sp500_top100` eine niedrige Down-Capture-Ratio zeigt, wäre der bessere Drawdown fachlich plausibel.

Wenn die Down-Capture-Ratio dagegen nahe 1.0 liegt, könnte der bessere Max Drawdown eher vom konkreten Zeitraum oder Timing abhängen.

---

### 03.13.5 Priorisierung

Für die nächste Reporting-Erweiterung sollten zuerst diese drei Kennzahlen ergänzt werden:

| Priorität | Kennzahl | Grund |
|---|---|---|
| 1 | `correlation_to_benchmark` | zeigt Benchmark-Abhängigkeit |
| 2 | `down_capture_ratio` | wichtigste Defensiv-Kennzahl |
| 3 | `up_capture_ratio` | zeigt Teilnahme an positiven Phasen |

Danach können ergänzt werden:

| Priorität | Kennzahl | Grund |
|---|---|---|
| 4 | `relative_volatility` | einfach interpretierbar |
| 5 | `tracking_difference` | erklärt Renditeabstand |
| 6 | `tracking_error` | wichtig für aktive Strategien |

---

### 03.13.6 Fazit

Die bisherigen Kennzahlen zeigen, dass `sp500_top100` gegenüber `SXR8.DE` einen besseren Drawdown, aber schwächere CAGR und Sharpe Ratio hat.

Mit Benchmark-Korrelation, Up-Capture und Down-Capture soll geprüft werden, ob dieser Drawdown-Vorteil strukturell nachvollziehbar ist.

Diese Kennzahlen sind wichtig, bevor die ersten Risikoprofile final bewertet oder Parameter-Sensitivitäten automatisiert durch den Agenten getestet werden.


## 03.14 Benchmark-Relationskennzahlen ergänzt

Die Kennzahlen `correlation_to_benchmark`, `up_capture_ratio` und `down_capture_ratio` wurden dem Report hinzugefügt.

Im ersten Lauf wurden für A und B jedoch exakt identische Werte ausgegeben. Da A und B unterschiedliche Universes, Portfolios, Drawdowns und Volatilitäten haben, ist dieses Ergebnis auffällig.

Die Berechnung muss daher geprüft werden, bevor die Werte fachlich interpretiert werden.


## 03.14.1 Korrektur der Benchmark-Relationskennzahlen

Bei der ersten Implementierung wurden für A und B identische Benchmark-Relationskennzahlen ausgegeben. Die Prüfung zeigte, dass die Berechnung nicht zuverlässig aus getrennten run-spezifischen Zeitreihen erfolgte.

Die Logik wurde korrigiert:

- Relationsberechnung erhält nun die jeweilige `run_id`
- CSVs mit `# run_id=...` werden nur genutzt, wenn die ID zum angefragten Run passt
- bei fehlenden oder nicht passenden Zeitreihen werden die Relationskennzahlen als `n/a` ausgegeben
- Tests wurden ergänzt
- vollständige Testsuite läuft mit `64 passed`

Für alte Runs ohne verlässliche run-spezifische Zeitreihen werden die Relationskennzahlen daher korrekt als `n/a` ausgegeben.


## 03.15 Benchmark-Relation nach frischem LONG-Lauf

Nach dem Fix der Benchmark-Relationskennzahlen wurde die Testmatrix neu erzeugt. Im LONG-Report liegen nun echte Werte für die Benchmark Relation vor.

Verglichen wurden:

- A: `sp500`, Run `20260514_215223`
- B: `sp500_top100`, Run `20260514_230455`
- Benchmark: `SXR8.DE`

| Kennzahl | A: sp500 | B: sp500_top100 | Benchmark |
|---|---:|---:|---:|
| Total Return | 89.13% | 21.78% | 51.82% |
| CAGR | 17.54% | 5.12% | 11.17% |
| Alpha | +6.37% | -6.05% | n/a |
| Max Drawdown | -24.45% | -23.27% | -23.32% |
| Volatilität | 24.84% | 18.35% | 16.01% |
| Sharpe Ratio | 0.7800 | 0.3700 | 0.7400 |

Benchmark Relation:

| Kennzahl | A: sp500 | B: sp500_top100 |
|---|---:|---:|
| Correlation to Benchmark | 0.3336 | 0.3681 |
| Up Capture Ratio | 0.6178 | 0.4738 |
| Down Capture Ratio | 0.4746 | 0.4621 |

### Interpretation

Im LONG-Zeitraum liefert `sp500` deutlich bessere Rendite, CAGR, Alpha und Sharpe Ratio als `sp500_top100`. `sp500` schlägt außerdem den Benchmark `SXR8.DE` bei CAGR und Sharpe Ratio.

`sp500_top100` zeigt zwar geringere Volatilität und niedrigeren Turnover, der Drawdown-Vorteil gegenüber dem Benchmark ist im LONG-Zeitraum jedoch nur minimal.

Die Capture Ratios zeigen, dass `sp500_top100` deutlich weniger an positiven Benchmark-Phasen teilnimmt als `sp500`, aber nur minimal weniger an negativen Benchmark-Phasen verliert.

Damit wirkt `sp500_top100` im LONG-Zeitraum zu defensiv: Der Schutzvorteil ist gering, der Renditeverzicht jedoch hoch.

### Vorläufige Bewertung LONG

| Variante | Bewertung |
|---|---|
| `sp500` | Geeignet / offensiver Kandidat |
| `sp500_top100` | Beobachten / defensiv, aber im LONG-Zeitraum nicht überzeugend |


## 03.15.2 Benchmark-Relation im MEDIUM-Lauf

Verglichen wurden:

- A: `sp500`, Run `20260514_212311`
- B: `sp500_top100`, Run `20260514_214730`
- Benchmark: `SXR8.DE`

| Kennzahl | A: sp500 | B: sp500_top100 | Benchmark |
|---|---:|---:|---:|
| Total Return | 20.34% | 20.66% | 22.85% |
| CAGR | 13.72% | 13.93% | 15.36% |
| Alpha | -1.64% | -1.43% | n/a |
| Max Drawdown | -24.45% | -16.04% | -23.32% |
| Volatilität | 25.30% | 17.70% | 16.90% |
| Sharpe Ratio | 0.6400 | 0.8300 | 0.9300 |
| Turnover | 48.83% | 34.21% | n/a |

Benchmark Relation:

| Kennzahl | A: sp500 | B: sp500_top100 |
|---|---:|---:|
| Correlation to Benchmark | 0.2798 | 0.3650 |
| Up Capture Ratio | 0.4898 | 0.4775 |
| Down Capture Ratio | 0.3809 | 0.3929 |

### Interpretation

Im MEDIUM-Zeitraum ist `sp500_top100` die klar stärkere Strategievariante gegenüber `sp500`.

`sp500_top100` gewinnt bei Total Return, CAGR, Alpha, Max Drawdown, Volatilität, Sharpe Ratio und Turnover.

Gegenüber dem Benchmark `SXR8.DE` bleibt `sp500_top100` bei CAGR und Sharpe Ratio leicht zurück, zeigt aber einen deutlich besseren Max Drawdown.

Die Benchmark-Relationskennzahlen zeigen keine klare Überlegenheit von `sp500_top100` bei Up- oder Down-Capture. Der Vorteil der Top100-Variante entsteht daher eher aus dem gesamten Portfolioverlauf, der geringeren Volatilität und dem deutlich besseren Max Drawdown.

### Vorläufige Bewertung MEDIUM

| Variante | Bewertung |
|---|---|
| `sp500` | Beobachten / nicht bevorzugt |
| `sp500_top100` | Geeignet für weitere Tests / starker Balanced-Kandidat |


## 03.15.3 Benchmark-Relation im SHORT-Lauf

Verglichen wurden:

- A: `sp500`, Run `20260514_211123`
- B: `sp500_top100`, Run `20260514_212124`
- Benchmark: `SXR8.DE`

| Kennzahl | A: sp500 | B: sp500_top100 | Benchmark |
|---|---:|---:|---:|
| Total Return | 12.57% | 10.29% | 18.78% |
| CAGR | 30.82% | 24.88% | 47.77% |
| Alpha | -16.95% | -22.89% | n/a |
| Max Drawdown | -6.92% | -2.68% | -3.77% |
| Volatilität | 16.81% | 10.85% | 13.44% |
| Sharpe Ratio | 1.6800 | 2.1000 | 2.9500 |
| Turnover | 53.17% | 35.71% | n/a |

Benchmark Relation:

| Kennzahl | A: sp500 | B: sp500_top100 |
|---|---:|---:|
| Correlation to Benchmark | 0.2687 | 0.2722 |
| Up Capture Ratio | 0.5401 | 0.3619 |
| Down Capture Ratio | 0.4236 | 0.2406 |

### Interpretation

Im SHORT-Zeitraum erzielt `sp500` die höhere Rendite und CAGR, während `sp500_top100` bei Risiko, Volatilität, Sharpe Ratio und Turnover besser abschneidet.

`sp500_top100` zeigt einen deutlich niedrigeren Max Drawdown als `sp500` und auch einen besseren Drawdown als der Benchmark `SXR8.DE`.

Die Capture Ratios zeigen ein klares defensives Profil:

- `sp500_top100` nimmt deutlich weniger an positiven Benchmark-Phasen teil.
- `sp500_top100` verliert aber auch deutlich weniger in negativen Benchmark-Phasen.

Damit ist `sp500_top100` im SHORT-Lauf defensiv überzeugend, aber renditeschwächer.

### Vorläufige Bewertung SHORT

| Variante | Bewertung |
|---|---|
| `sp500` | Renditestärker, aber riskanter |
| `sp500_top100` | Defensiv stark / Conservative-Kandidat |


## 03.16 Zusammenfassung der Testmatrix und erste Profil-Hypothesen

Nach der erneuten Testmatrix liegen für `sp500` gegen `sp500_top100` nun Auswertungen für SHORT, MEDIUM und LONG inklusive Benchmark-Relationskennzahlen vor.

Verglichen wurden:

- Universe A: `sp500`
- Universe B: `sp500_top100`
- Benchmark: `SXR8.DE`

---

### 03.16.1 Ergebnisübersicht

| Zeitraum | Return Winner | Risk Winner | Sharpe Winner | Turnover Winner | Kurzbewertung |
|---|---|---|---|---|---|
| SHORT | `sp500` | `sp500_top100` | `sp500_top100` | `sp500_top100` | Top100 defensiv stark |
| MEDIUM | `sp500_top100` | `sp500_top100` | `sp500_top100` | `sp500_top100` | Top100 klar bester Strategiekandidat |
| LONG | `sp500` | `sp500_top100` | `sp500` | `sp500_top100` | sp500 renditestärker, Top100 defensiver |

---

### 03.16.2 Kernerkenntnisse

Aus der Testmatrix ergibt sich ein klares Muster:

| Erkenntnis | Bedeutung |
|---|---|
| `sp500_top100` gewinnt durchgehend beim Risiko | stabil defensiver Charakter |
| `sp500_top100` gewinnt durchgehend beim Turnover | bessere Handelbarkeit |
| `sp500` gewinnt in SHORT und LONG bei Rendite | höheres Renditepotenzial |
| `sp500` gewinnt in LONG auch bei Sharpe | in längeren Zeiträumen stärkerer Rendite-Risiko-Kandidat |
| `sp500_top100` gewinnt MEDIUM klar | im mittleren Zeitraum sehr attraktives Verhältnis |
| `sp500_top100` hat oft niedrigere Up-Capture | weniger Teilnahme an Aufwärtsphasen |
| `sp500_top100` hat teils niedrigere Down-Capture | bessere defensive Wirkung in schwachen Phasen |

Die Universe-Wahl hat damit einen stabilen fachlichen Effekt.

---

### 03.16.3 Charakter von `sp500`

`sp500` zeigt sich in der bisherigen Matrix eher als renditeorientierte Variante.

Typisches Verhalten:

- höhere Renditechance
- höhere Volatilität
- höherer Drawdown
- höherer Turnover
- stärkere Teilnahme an positiven Benchmark-Phasen
- in LONG besser als `sp500_top100` bei CAGR, Alpha und Sharpe

Vorläufige Einordnung:

| Profilrichtung | Einschätzung |
|---|---|
| Conservative | eher ungeeignet |
| Balanced | möglich, aber nur mit Risikoparametern |
| Offensive | naheliegend |

`sp500` ist damit ein guter Kandidat für ein offensiveres Profil oder für ein Balanced-Profil mit zusätzlicher Risikosteuerung.

---

### 03.16.4 Charakter von `sp500_top100`

`sp500_top100` zeigt sich in der bisherigen Matrix als defensivere Variante.

Typisches Verhalten:

- geringerer Drawdown
- geringere Volatilität
- geringerer Turnover
- weniger Aufwärts-Teilnahme
- in SHORT defensiv stark
- in MEDIUM sehr überzeugend
- in LONG renditeschwach im Vergleich zu `sp500`

Vorläufige Einordnung:

| Profilrichtung | Einschätzung |
|---|---|
| Conservative | naheliegend |
| Balanced | möglich, aber nicht automatisch |
| Offensive | eher ungeeignet |

`sp500_top100` ist damit ein guter Kandidat für ein konservatives Profil. Für Balanced ist die Variante interessant, aber noch nicht eindeutig genug, weil der LONG-Zeitraum einen deutlichen Renditeverzicht zeigt.

---

### 03.16.5 Erste Profil-Hypothesen

Aus den bisherigen Ergebnissen ergeben sich folgende Hypothesen:

| Profil | Wahrscheinliche Basis | Begründung |
|---|---|---|
| Conservative | `sp500_top100` | geringerer Drawdown, geringere Volatilität, geringerer Turnover |
| Balanced | offen | Top100 überzeugt in MEDIUM, sp500 überzeugt in LONG |
| Offensive | `sp500` | höhere Renditechance und bessere LONG-Performance |

Diese Hypothesen sind noch keine finalen Profile.

Sie dienen als Ausgangspunkt für gezielte Parameter-Sensitivitätsanalysen.

---

### 03.16.6 Warum Balanced noch offen bleibt

Balanced ist aktuell der spannendste, aber auch unklarste Bereich.

Mögliche Varianten:

| Variante | Idee |
|---|---|
| `sp500_top100` als Balanced | ruhiger, weniger Turnover, defensiver |
| `sp500` mit strengeren Limits | mehr Renditechance behalten, Risiko reduzieren |
| `sp500` mit niedrigerem `max_per_sector` | weniger Klumpenrisiko |
| `sp500` mit niedrigerem `max_turnover_cap` | weniger Umschichtung |
| `sp500` mit anderem `top_k` | Konzentration steuern |
| `sp500_top100` mit offensiveren Parametern | defensive Basis etwas renditestärker machen |

Die bisherigen Ergebnisse sprechen dagegen, Balanced sofort fest auf `sp500_top100` zu setzen.

Stattdessen sollte Balanced über gezielte Parameter-Tests entwickelt werden.

---

### 03.16.7 Konsequenz für die nächsten Tests

Die nächste Phase sollte keine breite Optimierung sein, sondern eine gezielte Sensitivitätsanalyse.

Empfohlene erste Testreihe:

| Priorität | Testreihe | Zweck |
|---|---|---|
| 1 | `top_k` | Konzentration vs. Diversifikation prüfen |
| 2 | `max_per_sector` | Klumpenrisiko reduzieren |
| 3 | `max_turnover_cap` | Handelbarkeit verbessern |
| 4 | Regime/Cash | Drawdown-Schutz prüfen |
| 5 | `score_days` / `vol_days` | Signallogik stabilisieren |

Als erster Kandidat bietet sich `top_k` an, weil dieser Parameter direkt beeinflusst:

- Positionsanzahl
- Konzentration
- Drawdown
- Volatilität
- Renditechance
- Portfolio-Stabilität

---

### 03.16.8 Vorläufiges Fazit

Die bisherige Testmatrix zeigt:

- `sp500_top100` ist stabil defensiver.
- `sp500_top100` reduziert Risiko und Turnover zuverlässig.
- `sp500` besitzt das höhere Renditepotenzial.
- `sp500` ist im LONG-Zeitraum deutlich stärker.
- `sp500_top100` ist im MEDIUM-Zeitraum der klar beste Strategiekandidat.
- Balanced ist noch nicht eindeutig entschieden.

Daraus folgt:

> Conservative kann wahrscheinlich auf `sp500_top100` aufbauen.  
> Offensive kann wahrscheinlich auf `sp500` aufbauen.  
> Balanced muss über Parameter-Sensitivität entwickelt werden.


## 03.17 Erste Parameter-Testreihe: top_k

Nach der Auswertung der Universe-Testmatrix bleibt insbesondere das Balanced-Profil offen.

`sp500_top100` zeigt ein defensiveres Verhalten, verliert im LONG-Zeitraum aber deutlich an Rendite. `sp500` zeigt höheres Renditepotenzial, aber auch höhere Risiken und höheren Turnover.

Als erste gezielte Parameter-Sensitivität wird daher `top_k` untersucht.

---

### 03.17.1 Ziel der Testreihe

Die Testreihe soll beantworten:

| Frage | Zweck |
|---|---|
| Wie verändert `top_k` die Rendite? | Renditechance bewerten |
| Wie verändert `top_k` den Max Drawdown? | Risiko bewerten |
| Wie verändert `top_k` die Volatilität? | Schwankung bewerten |
| Wie verändert `top_k` die Sharpe Ratio? | Rendite-Risiko-Verhältnis bewerten |
| Wie verändert `top_k` den Turnover? | Handelbarkeit prüfen |
| Wie verändert `top_k` die Benchmark-Relation? | Benchmark-Abhängigkeit verstehen |
| Gibt es einen sinnvollen Kompromiss für Balanced? | Profilbildung vorbereiten |

---

### 03.17.2 Zu testende Werte

Als erste sinnvolle Testreihe werden folgende Werte verwendet:

| Variante | `top_k` | Charakter |
|---|---:|---|
| konzentriert | 8 | höheres Renditepotenzial, höheres Einzelwertrisiko |
| Standard | 12 | aktueller Referenzwert |
| breiter | 15 | mehr Diversifikation |
| sehr breit | 20 | defensiver, eventuell Signalverwässerung |

---

### 03.17.3 Start-Universe

Die erste Testreihe sollte auf `sp500` laufen.

Begründung:

- `sp500` zeigt im LONG-Zeitraum das höhere Renditepotenzial.
- Das Balanced-Profil könnte entstehen, wenn `sp500` durch breitere Streuung ruhiger wird.
- Wir prüfen, ob sich Risiko und Turnover reduzieren lassen, ohne den Renditevorteil komplett zu verlieren.

Damit lautet die erste Hypothese:

> `sp500` mit höherem `top_k` könnte ein besserer Balanced-Kandidat sein als `sp500_top100`.

---

### 03.17.4 Testmatrix top_k

| Test | Universe | `top_k` | Profil | Zeitraum |
|---|---|---:|---|---|
| K1 | `sp500` | 8 | Standardstrategie mit geänderter Positionsanzahl | SHORT / MEDIUM / LONG |
| K2 | `sp500` | 12 | Referenz | SHORT / MEDIUM / LONG |
| K3 | `sp500` | 15 | breiter | SHORT / MEDIUM / LONG |
| K4 | `sp500` | 20 | sehr breit | SHORT / MEDIUM / LONG |

Optional danach dieselbe Testreihe für `sp500_top100`, falls `sp500` keine überzeugende Balanced-Variante liefert.

---

### 03.17.5 Zu messende Kennzahlen

Jeder Test soll mindestens folgende Kennzahlen enthalten:

| Kennzahl | Zweck |
|---|---|
| Total Return | Gesamtrendite |
| CAGR | annualisierte Rendite |
| Alpha | Benchmark-Abstand |
| Max Drawdown | wichtigster Risikowert |
| Volatilität | Schwankung |
| Sharpe Ratio | Rendite-Risiko-Verhältnis |
| Turnover | Handelbarkeit |
| Trades Count | operativer Aufwand |
| Avg Positions | Kontrolle der tatsächlichen Positionsanzahl |
| Correlation to Benchmark | Benchmark-Nähe |
| Up Capture Ratio | Teilnahme an positiven Benchmark-Phasen |
| Down Capture Ratio | Verhalten in negativen Benchmark-Phasen |

---

### 03.17.6 Erwartete Interpretation

Mögliche Ergebnisse:

| Beobachtung | Interpretation |
|---|---|
| `top_k=8` liefert mehr Rendite, aber mehr Drawdown | eher offensiv |
| `top_k=12` bleibt guter Standard | Referenz bleibt sinnvoll |
| `top_k=15` reduziert Risiko bei akzeptabler Rendite | möglicher Balanced-Kandidat |
| `top_k=20` reduziert Risiko, aber Rendite fällt stark | eher konservativ oder zu stark verwässert |

---

### 03.17.7 Entscheidung nach der Testreihe

Nach der Testreihe wird geprüft:

| Frage | Konsequenz |
|---|---|
| Gibt es bei `sp500` einen besseren Balanced-Kompromiss? | Balanced auf `sp500` weiterentwickeln |
| Bleibt `sp500` trotz höherem `top_k` zu volatil? | Balanced eher auf `sp500_top100` prüfen |
| Wird `top_k=20` zu schwach? | nicht weiter priorisieren |
| Ist `top_k=15` stabil besser als 12? | als Balanced-Kandidat merken |
| Ist `top_k=8` deutlich renditestärker? | als Offensive-Kandidat prüfen |

---

### 03.17.8 Vorläufiges Fazit

Die erste Parameter-Testreihe konzentriert sich bewusst nur auf `top_k`.

Damit wird geprüft, ob sich aus dem renditestärkeren `sp500` durch breitere Streuung ein besseres Balanced-Profil ableiten lässt.

Erst danach sollten weitere Parameter wie `max_per_sector`, `max_turnover_cap` oder Regime/Cash angepasst werden.


## 03.20 Abschluss der top_k-Sensitivität

Die erste Parameter-Sensitivität wurde für das Universe `sp500` durchgeführt.

Untersucht wurde der Einfluss von `top_k` auf Rendite, Risiko, Benchmark-Abstand, Turnover und Benchmark-Relationskennzahlen.

Getestete Werte:

| top_k | Status |
|---:|---|
| 8 | invalid / übersprungen |
| 12 | gültig |
| 15 | gültig |
| 20 | gültig |

---

### 03.20.1 Hinweis zu top_k=8

Die Variante `top_k=8` konnte in dieser Testreihe nicht ausgewertet werden.

Grund:

Die bestehende Schutzregel `max_active_names <= top_k` wurde verletzt.

Da in dieser Testreihe bewusst nur `top_k` verändert werden sollte, wurde `max_active_names` nicht automatisch angepasst.

Damit gilt:

> `top_k=8` ist unter der aktuellen Standardkonfiguration ungültig.

Für spätere Offensive-Tests kann `top_k=8` erneut geprüft werden, dann aber mit passender gemeinsamer Konfiguration:

| Parameter | Wert |
|---|---:|
| `top_k` | 8 |
| `max_active_names` | 8 |

Diese Prüfung gehört dann nicht mehr zur reinen `top_k`-Sensitivität, sondern zu einer eigenen Offensive-Profil-Testreihe.

---

### 03.20.2 Ergebnisübersicht top_k

| top_k | SHORT | MEDIUM | LONG | Gesamtbewertung |
|---:|---|---|---|---|
| 12 | stärkste SHORT-Variante | schwächer als 15 | schwächer als 15 | guter Standard, kurzfristig stark |
| 15 | schwächer als 12 | stärkste MEDIUM-Variante | stärkste LONG-Variante | bester Balanced-Kandidat |
| 20 | schwach in SHORT | solide, aber schwächer als 15 | solide, aber schwächer als 15 | reduziert Turnover, wirkt teilweise verwässert |

---

### 03.20.3 SHORT-Auswertung

| top_k | Total Return | CAGR | Max Drawdown | Volatility | Sharpe | Turnover |
|---:|---:|---:|---:|---:|---:|---:|
| 12 | 12.57% | 30.82% | -6.92% | 16.81% | 1.6800 | 53.17% |
| 15 | 10.71% | 25.97% | -6.92% | 15.97% | 1.5200 | 50.00% |
| 20 | 6.00% | 14.14% | -8.73% | 16.25% | 0.9000 | 46.83% |

Interpretation:

Im SHORT-Zeitraum bleibt `top_k=12` die stärkste Variante.

`top_k=15` reduziert Turnover und Volatilität leicht, verliert aber Rendite und Sharpe.

`top_k=20` reduziert zwar den Turnover, verschlechtert aber Rendite, CAGR, Sharpe und Drawdown deutlich.

Vorläufige SHORT-Bewertung:

| top_k | Bewertung |
|---:|---|
| 12 | bevorzugt |
| 15 | beobachtenswert |
| 20 | eher nicht bevorzugt |

---

### 03.20.4 MEDIUM-Auswertung

| top_k | Total Return | CAGR | Alpha | Max Drawdown | Volatility | Sharpe | Turnover |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 20.34% | 13.72% | -1.64% | -24.45% | 25.30% | 0.6400 | 48.83% |
| 15 | 23.23% | 15.61% | +0.25% | -23.48% | 25.21% | 0.7100 | 47.08% |
| 20 | 20.51% | 13.83% | -1.53% | -23.49% | 25.29% | 0.6400 | 45.32% |

Interpretation:

Im MEDIUM-Zeitraum ist `top_k=15` die beste Variante.

`top_k=15` verbessert gegenüber `top_k=12`:

- Total Return
- CAGR
- Alpha
- Max Drawdown
- Sharpe Ratio
- Turnover

`top_k=20` reduziert den Turnover weiter, liefert aber nicht die Rendite- und Sharpe-Verbesserung von `top_k=15`.

Vorläufige MEDIUM-Bewertung:

| top_k | Bewertung |
|---:|---|
| 12 | Referenz, aber unterlegen |
| 15 | bevorzugt |
| 20 | Turnover-Alternative, aber schwächer als 15 |

---

### 03.20.5 LONG-Auswertung

| top_k | Total Return | CAGR | Alpha | Max Drawdown | Volatility | Sharpe | Turnover |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 89.13% | 17.54% | +6.37% | -24.45% | 24.84% | 0.7800 | 47.28% |
| 15 | 94.48% | 18.38% | +7.21% | -23.48% | 24.73% | 0.8100 | 45.01% |
| 20 | 93.56% | 18.24% | +7.06% | -23.49% | 24.93% | 0.8000 | 42.29% |

Interpretation:

Im LONG-Zeitraum ist `top_k=15` erneut die stärkste Variante.

`top_k=15` verbessert gegenüber `top_k=12`:

- Total Return
- CAGR
- Alpha
- Max Drawdown
- Volatility leicht
- Sharpe Ratio
- Turnover

`top_k=20` liegt nahe bei `top_k=15`, reduziert den Turnover stärker, bleibt aber bei Return, CAGR, Alpha und Sharpe leicht zurück.

Vorläufige LONG-Bewertung:

| top_k | Bewertung |
|---:|---|
| 12 | solide, aber unterlegen |
| 15 | bevorzugt |
| 20 | defensive Turnover-Alternative |

---

### 03.20.6 Gesamtbewertung

Die top_k-Sensitivität zeigt ein klares Zwischenergebnis:

| top_k | Gesamtbewertung |
|---:|---|
| 12 | guter Standard, besonders im SHORT-Zeitraum stark |
| 15 | bester Gesamtkompromiss, starker Balanced-Kandidat |
| 20 | reduziert Turnover, wirkt aber teilweise zu breit / verwässert |
| 8 | später separat als Offensive-Test prüfen |

`top_k=15` ist aktuell der interessanteste Kandidat für ein Balanced-Profil auf Basis von `sp500`.

Besonders relevant ist, dass `top_k=15` in MEDIUM und LONG nicht nur defensiver ist, sondern gleichzeitig auch bessere Rendite- und Sharpe-Werte liefert.

Damit unterscheidet sich `top_k=15` positiv von einer reinen Defensivvariante.

---

### 03.20.7 Profil-Hypothese nach top_k-Test

Die bisherigen Profil-Hypothesen werden angepasst:

| Profil | Vorherige Hypothese | Aktualisierte Hypothese |
|---|---|---|
| Conservative | eher `sp500_top100` | weiterhin `sp500_top100` |
| Balanced | offen | `sp500` mit `top_k=15` wird erster Kandidat |
| Offensive | eher `sp500` | später `sp500` mit `top_k=8` und `max_active_names=8` separat prüfen |

---

### 03.20.8 Nächster Parameter

Als nächster Parameter bietet sich `max_per_sector` an.

Begründung:

Nachdem `top_k=15` als Balanced-Kandidat sichtbar wurde, sollte geprüft werden, ob strengere Sektorlimits das Risiko weiter reduzieren können, ohne Rendite und Sharpe zu stark zu verschlechtern.

Nächste Testreihe:

| Parameter | Werte |
|---|---|
| `max_per_sector` | 2 / 3 / 4 / off |

Startkonfiguration:

| Parameter | Wert |
|---|---|
| Universe | `sp500` |
| `top_k` | 15 |
| Profilziel | Balanced |



## 03.21 Parameter-Testreihe: max_per_sector

Nach Abschluss der `top_k`-Sensitivität wurde `top_k=15` als erster starker Balanced-Kandidat auf Basis von `sp500` identifiziert.

Als nächster Parameter wird `max_per_sector` untersucht.

Ziel ist es zu prüfen, ob strengere oder lockerere Sektorlimits das Verhältnis aus Rendite, Drawdown, Volatilität, Sharpe Ratio und Turnover verbessern.

---

### 03.21.1 Ausgangspunkt

Die neue Referenz für diese Testreihe lautet:

| Parameter | Wert |
|---|---|
| Universe | `sp500` |
| `top_k` | 15 |
| Profilziel | Balanced |
| Benchmark | `SXR8.DE` |

Die vorherige Testreihe zeigte, dass `top_k=15` in MEDIUM und LONG gegenüber `top_k=12` bessere Werte bei Rendite, CAGR, Alpha, Max Drawdown, Sharpe Ratio und Turnover lieferte.

Damit ist `top_k=15` ein geeigneter Startpunkt für weitere Balanced-Tests.

---

### 03.21.2 Ziel der max_per_sector-Testreihe

Die Testreihe soll beantworten:

| Frage | Zweck |
|---|---|
| Reduziert ein strengeres Sektorlimit den Drawdown? | Klumpenrisiko prüfen |
| Verbessert ein Sektorlimit die Sharpe Ratio? | Rendite-Risiko-Verhältnis prüfen |
| Kostet ein strengeres Limit zu viel Rendite? | Renditeverlust bewerten |
| Erhöht ein lockeres Limit die Rendite? | Renditechance prüfen |
| Führt ein lockeres Limit zu höherem Klumpenrisiko? | Risiko bewerten |
| Ist das aktuelle Limit sinnvoll? | Standard validieren |

---

### 03.21.3 Zu testende Werte

| Variante | `use_sector_limits` | `max_per_sector` | Charakter |
|---|---|---:|---|
| streng | true | 2 | weniger Klumpenrisiko, defensiver |
| Standard | true | 3 | aktueller Referenzwert |
| locker | true | 4 | mehr Freiheit, eventuell mehr Rendite |
| offen | false | n/a | keine Sektorbegrenzung |

Wichtig:

Die Variante `offen` wird nicht als `max_per_sector = unlimited` getestet, sondern sauber über:

| Parameter | Wert |
|---|---|
| `use_sector_limits` | false |

Damit bleibt die Konfiguration eindeutig.

---

### 03.21.4 Testmatrix max_per_sector

Für jede Variante sollen SHORT, MEDIUM und LONG getestet werden.

| Test | Universe | top_k | use_sector_limits | max_per_sector | Zeitraum |
|---|---|---:|---|---:|---|
| S1 | `sp500` | 15 | true | 2 | SHORT |
| S2 | `sp500` | 15 | true | 2 | MEDIUM |
| S3 | `sp500` | 15 | true | 2 | LONG |
| S4 | `sp500` | 15 | true | 3 | SHORT |
| S5 | `sp500` | 15 | true | 3 | MEDIUM |
| S6 | `sp500` | 15 | true | 3 | LONG |
| S7 | `sp500` | 15 | true | 4 | SHORT |
| S8 | `sp500` | 15 | true | 4 | MEDIUM |
| S9 | `sp500` | 15 | true | 4 | LONG |
| S10 | `sp500` | 15 | false | n/a | SHORT |
| S11 | `sp500` | 15 | false | n/a | MEDIUM |
| S12 | `sp500` | 15 | false | n/a | LONG |

---

### 03.21.5 Zu messende Kennzahlen

Jeder Test soll mindestens folgende Werte enthalten:

| Kennzahl | Zweck |
|---|---|
| Total Return | Gesamtrendite |
| CAGR | annualisierte Rendite |
| Alpha | Benchmark-Abstand |
| Max Drawdown | Risiko |
| Volatilität | Schwankung |
| Sharpe Ratio | Rendite-Risiko-Verhältnis |
| Turnover | Handelbarkeit |
| Trades Count | operativer Aufwand |
| Avg Positions | Kontrolle der Positionsanzahl |
| Benchmark CAGR | Vergleichsrendite |
| Benchmark Max Drawdown | Vergleichsrisiko |
| Benchmark Sharpe | Benchmark-Rendite-Risiko |
| Correlation to Benchmark | Benchmark-Nähe |
| Up Capture Ratio | Teilnahme an positiven Benchmark-Phasen |
| Down Capture Ratio | Verhalten in negativen Benchmark-Phasen |

Zusätzlich wären für diese Testreihe besonders wichtig:

| Kennzahl | Zweck |
|---|---|
| Max Sector Weight | tatsächliches Klumpenrisiko |
| Dominant Sector | stärkste Sektorabhängigkeit |
| Sector Count | Anzahl vertretener Sektoren |
| Sector Distribution | Struktur des Portfolios |

Falls diese Sektor-Kennzahlen im Reporting noch fehlen, sollen sie als spätere Reporting-Erweiterung vorgemerkt werden.

---

### 03.21.6 Erwartete Interpretation

Mögliche Ergebnisse:

| Beobachtung | Interpretation |
|---|---|
| `max_per_sector=2` reduziert Drawdown, kostet aber Rendite | Conservative/Balanced-Kandidat |
| `max_per_sector=3` bleibt bester Kompromiss | aktueller Standard bestätigt |
| `max_per_sector=4` verbessert Rendite ohne deutlichen Risikoanstieg | Balanced/Offensive-Kandidat |
| `use_sector_limits=false` verbessert Rendite stark, erhöht aber Risiko | eher offensiv oder riskant |
| `use_sector_limits=false` verschlechtert Sharpe/Drawdown | Sektorlimits sind wichtig |

---

### 03.21.7 Entscheidung nach der Testreihe

Nach der Testreihe wird bewertet:

| Frage | Konsequenz |
|---|---|
| Ist `max_per_sector=2` deutlich risikoärmer? | Conservative/Balanced prüfen |
| Ist `max_per_sector=3` weiterhin bester Kompromiss? | Standard beibehalten |
| Ist `max_per_sector=4` renditestärker ohne großen Drawdown-Nachteil? | Balanced/Offensive prüfen |
| Sind Sektorlimits insgesamt hilfreich? | `use_sector_limits=true` bestätigen |
| Werden Sektorlimits unnötig restriktiv? | Lockerung prüfen |

---

### 03.21.8 Vorläufiges Fazit

Die `max_per_sector`-Testreihe baut direkt auf dem bisherigen Balanced-Kandidaten auf:

| Parameter | Wert |
|---|---|
| Universe | `sp500` |
| `top_k` | 15 |

Damit wird nicht mehr die Universe-Frage untersucht, sondern die Frage:

> Wie stark beeinflusst die Sektorbegrenzung das Risiko-Rendite-Verhältnis des neuen Balanced-Kandidaten?

Diese Testreihe ist besonders wichtig, weil Sektorlimits verhindern können, dass die Strategie faktisch zu einem konzentrierten Tech-/Growth-Bet wird.


## 03.23 Runtime-Profiling Backtester/Runner

Zur Vorbereitung weiterer Matrixläufe wurde ein Runtime-Profiling durchgeführt.

Messlauf:

| Kennzahl | Wert |
|---|---:|
| run_id | 20260521_233424 |
| Profil | SHORT |
| Gesamtlaufzeit | 591.5s |
| Backtester | 334.1s |
| Runner | 257.5s |
| Compare/Orchestration | 0.008s |
| Report/Manifest/Artifacts | 0.008s |
| Ticker Count | 503 |
| Price Matrix | 742 x 497 |
| Rebalance Dates | 7 |
| BT Decision Bundles | 7 |
| RUN Decision Bundles | 1 |
| Compare Matched | true |

### Hotspots

| Hotspot | Zeit |
|---|---:|
| backtest.download_close | ca. 326s |
| Runner DataClient.get_prices / download_ohlc | ca. 254s |
| yfinance.download / yfinance.history | dominiert |
| time.sleep innerhalb yfinance | ca. 323s |
| Scoring/Volatilität | ca. 1.1s |

### Interpretation

Der Hauptengpass liegt nicht in der Strategie-, Scoring- oder Rebalance-Logik, sondern im wiederholten Laden von Marktdaten über yfinance.

Scoring und Volatilitätsberechnung sind aktuell kein relevanter Laufzeitengpass.

Besonders Matrixläufe wiederholen nahezu identische Preis- und Benchmark-Downloads mehrfach. Dadurch vervielfacht sich die Laufzeit mit jeder getesteten Variante.

### Konsequenz

Als nächste technische Optimierung soll ein read-only Marktdaten-Cache eingeführt werden.

Ziel:

- Preis-/Benchmark-Daten nicht bei jedem Run neu laden
- Backtester und Runner möglichst aus denselben gecachten Daten versorgen
- Matrixläufe deutlich beschleunigen
- Strategieergebnisse und Parität unverändert lassen

### Niedrigrisiko-Optimierungen

| Optimierung | Risiko |
|---|---|
| Preis-Cache keyed by Tickerliste, Zeitraum, adjusted/as_of | niedrig |
| Benchmark-Cache | niedrig |
| Cache-Hit/Miss Logging | niedrig |
| Matrixläufe mit gemeinsamem Datenbestand | mittel |
| Report-Erzeugung nach Matrix bündeln | niedrig |

### Riskante Optimierungen, vorerst vermeiden

| Optimierung | Risiko |
|---|---|
| Rebalance-Schleifen umbauen | Paritätsrisiko |
| Scoring/Volatilität vektorisieren | NaN-/Fenster-/Tie-Break-Risiko |
| Previous-position seeding ändern | Paritätsrisiko |
| Decision-Bundle-Schema ändern | Analyse-/Compare-Risiko |
| BT/RUN getrennt optimieren | Drift-Risiko |

### Fazit

Die nächste Optimierung sollte nicht bei der Strategie-Logik ansetzen, sondern beim wiederholten Marktdaten-Download.

Ein stabiler, transparenter Preis- und Benchmark-Cache ist die wichtigste Voraussetzung, bevor weitere große Parameter-Matrizen ausgeführt werden.


## 03.24 Performance-Optimierung: Market-Data-Cache

Nach dem Runtime-Profiling wurde ein Market-Data-Cache eingeführt, um wiederholte yfinance-Downloads zu vermeiden.

Geänderte Dateien:

- `market_data_cache.py`
- `backtest.py`
- `data_client.py`
- `test_market_data_cache.py`

### Ergebnis

| Lauf | Backtest | Runner | Summe |
|---|---:|---:|---:|
| Kaltlauf, leerer finaler Cache | 332.37s | 132.18s | 464.55s |
| Warmlauf | 2.06s | 8.58s | 10.64s |

### Parität

| Lauf | compare_matched |
|---|---|
| Kaltlauf | true |
| Warmlauf | true |

Strategie-, Rebalance-, Scoring-/Volatilitätslogik und Decision-Bundle-Struktur wurden nicht geändert.

### Cache

| Punkt | Wert |
|---|---|
| Verzeichnis | `aktien_oop/data_cache/market_data` |
| Format | Pickle-Payload mit Metadata und originalem DataFrame |
| Cache-Key | data_kind, Tickerliste, Universe-Hash, Zeitraum/period/as_of, adjusted, benchmark_symbol, Schema-Version |
| Logging | `[market-cache] HIT/MISS/STORE` |
| Validierung | unvollständige oder unpassende Cache-Daten werden verworfen |

### Bewertung

Die Optimierung ist erfolgreich. Der Hauptengpass yfinance-Download wurde für Wiederholungsläufe massiv reduziert, ohne die Parität zu brechen.

Offene Punkte:

- Cache-Verzeichnis in `.gitignore` prüfen.
- Bestehende `test_store_positions.py`-Failures separat klären.
- Später optional prüfen, ob Runner-OHLC-Daten noch effizienter gebündelt werden können.













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