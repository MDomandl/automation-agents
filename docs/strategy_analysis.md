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

## 03.27 Sektor-Metriken ergänzt

Die `max_per_sector`-Testmatrix wurde um Sektor-Metriken erweitert.

Ergänzte Kennzahlen:

- Max Sector Weight
- Dominant Sector
- Sector Count
- Sector Distribution
- Max Sector Positions
- Dominant Sector Positions
- Source
- Warning

Die Berechnung erfolgt rein im Reporting. Strategie-, Auswahl-, Scoring- und Finalisierungslogik wurden nicht verändert.

Datenquelle:

- primär: finale Portfolio-Gewichte aus Decision Bundles via `snapshot.behavior.last_portfolio`
- Sektorquelle: `sp500_meta.csv`
- Fallback: letzte `as_of`-Gruppe aus Positions-CSV

Tests:

- `72 passed`

### Wichtigste Ergebnisse

| Variante | Max Sector Weight | Dominant Sector | Sector Count |
|---|---:|---|---:|
| max_per_sector=2 | 22.22% | Consumer Discretionary / Information Technology | 7 |
| max_per_sector=3 | 33.33% | Information Technology | 6 |
| max_per_sector=4 | 44.44% | Information Technology | 6 |
| sector_off | 77.78% | Information Technology | 3 |

### Interpretation

Die Sektor-Metriken bestätigen, dass `sector_off` zwar renditestark ist, aber ein erhebliches Klumpenrisiko besitzt.

Ohne Sektorlimit konzentriert sich das Portfolio stark auf Information Technology. Damit ist `sector_off` eher ein offensiver Kandidat und kein sauberer Balanced-Kandidat.

`max_per_sector=2` zeigt dagegen die breiteste Sektorstreuung, den niedrigsten Max Sector Weight und zugleich starke Performance-Werte in MEDIUM und LONG.

### Vorläufiges Fazit

`sp500 + top_k=15 + max_per_sector=2` ist aktuell der stärkste Balanced-Kandidat.

## 03.28 Balanced-Kandidat v1 festlegen

Nach den bisherigen Universe-, `top_k`- und `max_per_sector`-Tests wird ein erster Balanced-Kandidat festgelegt.

Dieser Kandidat ist noch kein finales Live-Profil, sondern der aktuelle beste Ausgangspunkt für weitere Tests.

---

### 03.28.1 Ausgangslage

Bisherige Erkenntnisse:

| Testbereich | Ergebnis |
|---|---|
| Universe-Vergleich | `sp500_top100` ist defensiver, `sp500` hat mehr Renditepotenzial |
| `top_k`-Sensitivität | `top_k=15` ist auf `sp500` der beste Balanced-Kompromiss |
| `max_per_sector`-Sensitivität | `max_per_sector=2` ist für Balanced/Risk-Control am stärksten |
| Sektor-Metriken | `sector_off` ist stark renditeorientiert, aber extrem konzentriert |
| Performance-Cache | Matrixläufe sind nun deutlich schneller ausführbar |

Die Sektor-Metriken zeigen besonders deutlich, dass `sector_off` zwar hohe Renditen liefern kann, aber mit starkem Klumpenrisiko verbunden ist. Ohne Sektorlimit lag der maximale Sektoranteil bei 77,78% und der dominante Sektor war Information Technology; bei `max_per_sector=2` lag der maximale Sektoranteil nur bei 22,22% und das Portfolio war auf 7 Sektoren verteilt. :contentReference[oaicite:0]{index=0}

---

### 03.28.2 Balanced-Kandidat v1

Der aktuelle Balanced-Kandidat lautet:

| Parameter | Wert |
|---|---|
| Universe | `sp500` |
| `top_k` | 15 |
| `use_sector_limits` | true |
| `max_per_sector` | 2 |
| Profilziel | Balanced |
| Benchmark | `SXR8.DE` |

Kurzform:

```toml
universe = "sp500"
top_k = 15
use_sector_limits = true
max_per_sector = 2
```

## 03.29 Parameter-Testreihe: max_turnover_cap

Nach Festlegung des ersten Balanced-Kandidaten wird als nächster Parameter `max_turnover_cap` untersucht.

Ausgangspunkt ist der aktuelle Balanced-Kandidat v1:

| Parameter | Wert |
|---|---|
| Universe | `sp500` |
| `top_k` | 15 |
| `use_sector_limits` | true |
| `max_per_sector` | 2 |
| Profilziel | Balanced |
| Benchmark | `SXR8.DE` |

---

### 03.29.1 Ziel der Testreihe

Die Testreihe soll prüfen, ob sich der Turnover reduzieren lässt, ohne die bisherigen Vorteile des Balanced-Kandidaten deutlich zu verschlechtern.

Wichtige Fragen:

| Frage | Zweck |
|---|---|
| Reduziert ein niedrigeres `max_turnover_cap` die Umschichtung deutlich? | Handelbarkeit verbessern |
| Bleiben CAGR und Alpha stabil? | Rendite erhalten |
| Bleibt der Max Drawdown akzeptabel? | Risikoprofil sichern |
| Bleibt die Sharpe Ratio stark? | Rendite-Risiko-Verhältnis sichern |
| Wird die Strategie durch zu niedrigen Turnover träge? | Anpassungsfähigkeit prüfen |
| Gibt es einen guten Kompromiss für Balanced? | Profilbildung vorbereiten |

---

### 03.29.2 Zu testende Werte

| Variante | `max_turnover_cap` | Charakter |
|---|---:|---|
| sehr ruhig | 0.20 | starke Begrenzung der Umschichtung |
| ausgewogen | 0.35 | moderater Turnover-Cap |
| flexibel | 0.50 | mehr Anpassungsfreiheit |
| offen | n/a | keine beziehungsweise praktisch keine Begrenzung |

Falls `max_turnover_cap` in der aktuellen Config anders benannt oder anders interpretiert wird, soll Codex zuerst die bestehende Logik prüfen und die Testwerte daran sauber anpassen.

---

### 03.29.3 Testmatrix max_turnover_cap

Für jede Variante sollen SHORT, MEDIUM und LONG getestet werden.

| Test | Universe | top_k | max_per_sector | max_turnover_cap | Zeitraum |
|---|---|---:|---:|---:|---|
| T1 | `sp500` | 15 | 2 | 0.20 | SHORT |
| T2 | `sp500` | 15 | 2 | 0.20 | MEDIUM |
| T3 | `sp500` | 15 | 2 | 0.20 | LONG |
| T4 | `sp500` | 15 | 2 | 0.35 | SHORT |
| T5 | `sp500` | 15 | 2 | 0.35 | MEDIUM |
| T6 | `sp500` | 15 | 2 | 0.35 | LONG |
| T7 | `sp500` | 15 | 2 | 0.50 | SHORT |
| T8 | `sp500` | 15 | 2 | 0.50 | MEDIUM |
| T9 | `sp500` | 15 | 2 | 0.50 | LONG |
| T10 | `sp500` | 15 | 2 | off | SHORT |
| T11 | `sp500` | 15 | 2 | off | MEDIUM |
| T12 | `sp500` | 15 | 2 | off | LONG |

---

### 03.29.4 Zu messende Kennzahlen

Jeder Lauf soll mindestens folgende Werte enthalten:

| Kennzahl | Zweck |
|---|---|
| Total Return | Gesamtrendite |
| CAGR | annualisierte Rendite |
| Alpha | Benchmark-Abstand |
| Max Drawdown | Risiko |
| Volatilität | Schwankung |
| Sharpe Ratio | Rendite-Risiko-Verhältnis |
| Turnover | wichtigste Zielkennzahl dieser Testreihe |
| Trades Count | operativer Aufwand |
| Avg Positions | Kontrolle der Positionsanzahl |
| Benchmark CAGR | Benchmark-Vergleich |
| Benchmark Drawdown | Benchmark-Risiko |
| Benchmark Sharpe | Benchmark-Rendite-Risiko |
| Up Capture Ratio | Teilnahme an positiven Benchmark-Phasen |
| Down Capture Ratio | Verhalten in negativen Benchmark-Phasen |
| Max Sector Weight | Sektorstruktur kontrollieren |
| Dominant Sector | Sektorstruktur kontrollieren |
| Sector Count | Sektorstreuung kontrollieren |

---

### 03.29.5 Erwartete Interpretation

Mögliche Ergebnisse:

| Beobachtung | Interpretation |
|---|---|
| `0.20` reduziert Turnover stark, verliert aber Rendite | zu träge |
| `0.35` reduziert Turnover bei stabiler Sharpe | möglicher Balanced-Kandidat |
| `0.50` ähnelt offenem Verhalten | Cap eventuell zu locker |
| `off` liefert höchste Rendite, aber hohen Turnover | eher offensiv oder operativ teuer |
| Drawdown steigt bei niedrigem Cap | Strategie kann nicht schnell genug reagieren |
| Sharpe bleibt stabil trotz niedrigerem Turnover | sehr gutes Signal |

---

### 03.29.6 Entscheidung nach der Testreihe

Nach der Testreihe wird bewertet:

| Frage | Konsequenz |
|---|---|
| Gibt es einen Cap mit deutlich niedrigerem Turnover und stabiler Sharpe? | Balanced-Kandidat verbessern |
| Verschlechtert niedriger Cap die Rendite stark? | Cap nicht zu streng setzen |
| Ist `off` kaum schlechter beim Turnover? | Cap eventuell unnötig |
| Reduziert ein Cap Drawdown oder Volatilität? | Risikosteuerung bestätigt |
| Verändert ein Cap die Sektorstruktur? | prüfen, ob Nebeneffekte entstehen |

---

### 03.29.7 Vorläufiges Fazit

Die `max_turnover_cap`-Testreihe baut direkt auf dem aktuellen Balanced-Kandidat v1 auf.

Ziel ist nicht, maximale Rendite zu finden, sondern die praktische Handelbarkeit zu verbessern.

Der wichtigste Zielkonflikt lautet:

> Weniger Umschichtung, ohne Rendite, Sharpe und Drawdown deutlich zu verschlechtern.

Wenn ein Turnover-Cap diese Balance verbessert, wird daraus der nächste Balanced-Kandidat v2.


## 03.31 Balanced-Kandidat v2 festlegen

Nach der `max_turnover_cap`-Testreihe wird der bisherige Balanced-Kandidat v1 zu einem Balanced-Kandidat v2 erweitert.

Wichtig:

`max_turnover_cap` wirkt in der aktuellen Implementierung als Effektivturnover- beziehungsweise Kosten-Cap. Es handelt sich nicht um eine echte Handels- oder Rebalance-Bremse.

Das Portfolio, die Anzahl der Trades und die Sektorstruktur bleiben dadurch unverändert. Verändert werden der gemessene effektive Turnover, die Kostenwirkung und dadurch leicht die Performance-Kennzahlen.

---

### 03.31.1 Ausgangspunkt: Balanced-Kandidat v1

Der bisherige Balanced-Kandidat v1 lautete:

| Parameter | Wert |
|---|---|
| Universe | `sp500` |
| `top_k` | 15 |
| `use_sector_limits` | true |
| `max_per_sector` | 2 |
| Benchmark | `SXR8.DE` |

Dieser Kandidat wurde aus den bisherigen Tests abgeleitet:

| Testbereich | Ergebnis |
|---|---|
| Universe-Test | `sp500` bietet mehr Renditepotenzial als `sp500_top100` |
| `top_k`-Test | `top_k=15` ist der beste Balanced-Kompromiss |
| Sektorlimit-Test | `max_per_sector=2` ist für Balanced/Risk-Control am stärksten |
| Sektor-Metriken | `max_per_sector=2` reduziert Klumpenrisiko deutlich |

---

### 03.31.2 Ergebnis der max_turnover_cap-Testreihe

Getestet wurden:

| Variante | `max_turnover_cap` |
|---|---:|
| sehr ruhig | 0.20 |
| ausgewogen | 0.35 |
| flexibel | 0.50 |
| off | deaktiviert / 0.0 |

Die Testreihe zeigte:

| Profil | Bester Kandidat |
|---|---|
| SHORT | `max_turnover_cap=0.20` |
| MEDIUM | `max_turnover_cap=0.20` |
| LONG | `max_turnover_cap=0.20` |

`max_turnover_cap=0.20` gewann in allen Profilen bei:

- Return
- Max Drawdown
- Sharpe Ratio
- niedrigstem Turnover

---

### 03.31.3 Kennzahlen von max_turnover_cap=0.20

| Profil | Total Return | CAGR | Alpha | Max Drawdown | Sharpe | Turnover | Trades |
|---|---:|---:|---:|---:|---:|---:|---:|
| SHORT | 10.16% | 24.55% | -23.22% | -7.96% | 1.46 | 20.00% | 8 |
| MEDIUM | 36.51% | 24.13% | +8.77% | -22.12% | 1.02 | 18.48% | 20 |
| LONG | 64.63% | 13.48% | +2.31% | -22.12% | 0.69 | 16.78% | 50 |

Die Sektorstruktur blieb stabil:

| Kennzahl | Wert |
|---|---|
| Max Sector Weight | 22.22% |
| Dominant Sector | Consumer Discretionary |
| Sector Count | 7 |

---

### 03.31.4 Balanced-Kandidat v2

Der neue Balanced-Kandidat v2 lautet:

| Parameter | Wert |
|---|---|
| Universe | `sp500` |
| `top_k` | 15 |
| `use_sector_limits` | true |
| `max_per_sector` | 2 |
| `max_turnover_cap` | 0.20 |
| Benchmark | `SXR8.DE` |

Kurzform:

```toml
universe = "sp500"
top_k = 15
use_sector_limits = true
max_per_sector = 2
max_turnover_cap = 0.20
benchmark_ticker = "SXR8.DE"
```


## 03.32 Parameter-Testreihe: Regime/Cash

Nach Festlegung des Balanced-Kandidat v2 wird als nächster Bereich das Regime- und Cash-Verhalten untersucht.

Ausgangspunkt ist der aktuelle Balanced-Kandidat v2:

| Parameter | Wert |
|---|---|
| Universe | `sp500` |
| `top_k` | 15 |
| `use_sector_limits` | true |
| `max_per_sector` | 2 |
| `max_turnover_cap` | 0.20 |
| Benchmark | `SXR8.DE` |
| Profilziel | Balanced |

---

### 03.32.1 Ziel der Testreihe

Die Testreihe soll prüfen, ob Regime- und Cash-Logik den Drawdown weiter verbessern kann.

Wichtige Fragen:

| Frage | Zweck |
|---|---|
| Reduziert ein SMA-/Regime-Filter den Max Drawdown? | Risikosteuerung |
| Kostet der Regime-Filter zu viel Rendite? | Renditeverlust bewerten |
| Verbessert Cash das Verhalten in schlechten Marktphasen? | defensive Wirkung prüfen |
| Verschlechtert Cash die Erholungsphasen? | Opportunitätskosten prüfen |
| Bleibt die Sharpe Ratio stabil oder verbessert sie sich? | Qualität prüfen |
| Wie stark verändert sich die Time-in-Market? | Investitionsgrad verstehen |
| Wird der Kandidat konservativer oder bleibt er Balanced? | Profilgrenze bestimmen |

---

### 03.32.2 Zu testende Varianten

Die genaue Config-Logik soll vor Umsetzung im Code geprüft werden. Vorläufig werden folgende Varianten betrachtet:

| Variante | `require_above_sma` | `regime_below_action` | `include_cash` | Charakter |
|---|---|---|---|---|
| defensiv_cash | true | SELL | true | bei negativem Regime in Cash |
| defensiv_hold | true | HOLD | false | bei negativem Regime Positionen halten / keine neue aggressive Anpassung |
| immer_investiert | false | n/a | false | kein Regime-Filter, Referenz |
| cash_variante | false | n/a | true | nur sinnvoll, wenn logisch sauber unterstützt |

Wichtig:

Die tatsächlichen Werte müssen an die bestehende Config- und Code-Logik angepasst werden. Wenn einzelne Kombinationen fachlich oder technisch unsauber sind, sollen sie nicht erzwungen werden.

---

### 03.32.3 Referenz

Die Referenz ist der Balanced-Kandidat v2 ohne zusätzliche Regime-Verschärfung beziehungsweise mit der aktuell gültigen Standard-Regime-Konfiguration.

Vor dem Test muss Codex prüfen:

| Punkt | Frage |
|---|---|
| `require_above_sma` | aktueller Standardwert? |
| `regime_below_action` | erlaubte Werte? |
| `include_cash` | aktueller Standardwert? |
| `cash_yield_annual` | wird Cash verzinst? |
| Benchmark für Regime | welcher Index wird verwendet? |
| Regime-SMA | welcher Zeitraum, z. B. 200 Tage? |

---

### 03.32.4 Testmatrix Regime/Cash

Für jede gültige Variante sollen SHORT, MEDIUM und LONG getestet werden.

| Test | Universe | top_k | max_per_sector | max_turnover_cap | Regime/Cash-Variante | Zeitraum |
|---|---|---:|---:|---:|---|---|
| R1 | `sp500` | 15 | 2 | 0.20 | defensiv_cash | SHORT |
| R2 | `sp500` | 15 | 2 | 0.20 | defensiv_cash | MEDIUM |
| R3 | `sp500` | 15 | 2 | 0.20 | defensiv_cash | LONG |
| R4 | `sp500` | 15 | 2 | 0.20 | defensiv_hold | SHORT |
| R5 | `sp500` | 15 | 2 | 0.20 | defensiv_hold | MEDIUM |
| R6 | `sp500` | 15 | 2 | 0.20 | defensiv_hold | LONG |
| R7 | `sp500` | 15 | 2 | 0.20 | immer_investiert | SHORT |
| R8 | `sp500` | 15 | 2 | 0.20 | immer_investiert | MEDIUM |
| R9 | `sp500` | 15 | 2 | 0.20 | immer_investiert | LONG |

Optional nur, wenn sauber unterstützt:

| Test | Variante |
|---|---|
| R10–R12 | cash_variante |

---

### 03.32.5 Zu messende Kennzahlen

Jeder Lauf soll mindestens enthalten:

| Kennzahl | Zweck |
|---|---|
| Total Return | Gesamtrendite |
| CAGR | annualisierte Rendite |
| Alpha | Benchmark-Abstand |
| Max Drawdown | wichtigste Risikokennzahl |
| Volatility | Schwankung |
| Sharpe Ratio | Rendite-Risiko |
| Turnover | Handelbarkeit |
| Trades Count | operativer Aufwand |
| Benchmark CAGR | Vergleichsrendite |
| Benchmark Drawdown | Vergleichsrisiko |
| Benchmark Sharpe | Benchmark-Rendite-Risiko |
| Up Capture Ratio | Teilnahme an positiven Benchmark-Phasen |
| Down Capture Ratio | Verhalten in negativen Benchmark-Phasen |
| Max Sector Weight | Sektorstruktur kontrollieren |
| Dominant Sector | Sektorstruktur kontrollieren |
| Sector Count | Sektorstreuung kontrollieren |

Zusätzlich wären für diese Testreihe besonders wichtig:

| Kennzahl | Zweck |
|---|---|
| Average Cash % | durchschnittlicher Cash-Anteil |
| Max Cash % | maximale defensive Quote |
| Time in Market % | Investitionsgrad |
| Time in Cash % | defensive Zeit |
| Regime Off Count | Anzahl negativer Regime-Phasen |
| Regime Switch Count | Häufigkeit von Regimewechseln |

Falls diese Kennzahlen noch nicht im Reporting vorhanden sind, sollen sie als TODO aufgenommen oder, wenn klein umsetzbar, ergänzt werden.

---

### 03.32.6 Erwartete Interpretation

Mögliche Ergebnisse:

| Beobachtung | Interpretation |
|---|---|
| defensiv_cash reduziert Drawdown deutlich, CAGR bleibt stabil | starker Conservative/Balanced-Kandidat |
| defensiv_cash reduziert Drawdown, kostet aber stark Rendite | eher Conservative |
| defensiv_hold verändert wenig | Regime-Filter nicht wirksam genug |
| immer_investiert liefert deutlich mehr Rendite bei höherem Drawdown | eher Offensive/Balanced ohne Schutz |
| Cash-Quote sehr hoch, Rendite schwach | zu defensiv |
| Down Capture sinkt deutlich | defensiver Mehrwert plausibel |
| Up Capture fällt stark | Schutz zu teuer erkauft |

---

### 03.32.7 Entscheidung nach der Testreihe

Nach der Testreihe wird bewertet:

| Frage | Konsequenz |
|---|---|
| Gibt es eine Variante mit deutlich besserem Drawdown und stabiler Sharpe? | Balanced v3 prüfen |
| Kostet Regime/Cash zu viel Rendite? | eher Conservative statt Balanced |
| Bleibt der aktuelle v2-Kandidat besser? | Regime/Cash nicht priorisieren |
| Verbessert Cash nur SHORT, aber nicht LONG? | Zeitraumabhängigkeit dokumentieren |
| Gibt es starke Unterschiede bei Up/Down Capture? | Profilcharakter schärfen |

---

### 03.32.8 Vorläufiges Fazit

Die Regime-/Cash-Testreihe ist der nächste logische Schritt, weil der aktuelle Balanced-Kandidat v2 bereits eine gute Sektorstruktur und einen reduzierten effektiven Turnover besitzt.

Jetzt soll geprüft werden, ob sich der Drawdown zusätzlich über Marktregime und Cash-Verhalten verbessern lässt.

Wichtig ist dabei, nicht nur die Rendite zu betrachten, sondern besonders:

- Max Drawdown
- Down Capture
- Sharpe Ratio
- Time in Market
- Cash-Anteil
- Opportunitätskosten durch verpasste Erholungsphasen


## 03.34 Regime/Cash-Testmatrix ausgewertet

Die Regime/Cash-Testmatrix wurde auf Basis des Balanced-Kandidaten v2 durchgeführt.

Ausgangskonfiguration:

| Parameter | Wert |
|---|---|
| Universe | `sp500` |
| `top_k` | 15 |
| `use_sector_limits` | true |
| `max_per_sector` | 2 |
| `max_turnover_cap` | 0.20 |
| Benchmark | `SXR8.DE` |

Getestete Varianten:

| Variante | `require_above_sma` | `regime_below_action` | `include_cash` |
|---|---|---|---|
| `defensiv_cash` | true | SELL | true |
| `defensiv_hold` | true | HOLD | false |
| `immer_investiert` | false | HOLD | false |

Die Variante `cash_variante` wurde übersprungen, weil `include_cash=true` ohne aktive SELL-Regime-Transition in der aktuellen Logik keinen sauberen Effekt hat.

### Ergebnisübersicht LONG

| Variante | CAGR | Alpha | Max Drawdown | Volatility | Sharpe | Down Capture |
|---|---:|---:|---:|---:|---:|---:|
| `defensiv_cash` | 13.48% | +2.31% | -22.12% | 21.96% | 0.6900 | 0.3812 |
| `defensiv_hold` | 21.50% | +10.33% | -25.25% | 24.05% | 0.9300 | 0.4774 |
| `immer_investiert` | 24.32% | +13.15% | -29.63% | 26.85% | 0.9500 | 0.5430 |

### Interpretation

`defensiv_cash` reduziert den Drawdown am stärksten, kostet aber deutlich Rendite und Sharpe. Diese Variante wirkt daher eher wie ein Conservative-Kandidat.

`immer_investiert` liefert die höchste Rendite, hat aber den deutlich höchsten Drawdown. Diese Variante ist eher offensiv.

`defensiv_hold` liegt zwischen beiden Extremen. Es hält die Rendite deutlich höher als `defensiv_cash`, reduziert aber das Risiko gegenüber `immer_investiert`. Damit ist `defensiv_hold` der interessanteste Balanced-Kandidat aus dieser Testreihe.

### Vorläufige Profil-Einordnung

| Profil | Kandidat |
|---|---|
| Conservative | `defensiv_cash` |
| Balanced | `defensiv_hold` |
| Offensive | `immer_investiert` |

### Fazit

Die Regime/Cash-Testreihe führt nicht zu einem besseren Balanced-Kandidaten durch Cash, sondern zu einer klareren Profiltrennung.

Für Balanced wird `defensiv_hold` als neuer Kandidat vorgemerkt.

Für Conservative wird `defensiv_cash` vorgemerkt.

Für Offensive wird `immer_investiert` vorgemerkt.


## 03.35 Profilstruktur v1 aus bisherigen Tests ableiten

Nach den bisherigen Sensitivitätsanalysen wird eine erste Profilstruktur abgeleitet.

Diese Profile sind noch keine finalen Live-Konfigurationen, sondern erste reproduzierbare Kandidaten für den nächsten Profilvergleich.

---

### 03.35.1 Bisherige Erkenntnisse

| Testbereich | Ergebnis |
|---|---|
| Universe-Vergleich | `sp500_top100` ist defensiver, `sp500` hat mehr Renditepotenzial |
| `top_k` | `top_k=15` ist auf `sp500` der stärkste Balanced-Kompromiss |
| `max_per_sector` | `max_per_sector=2` verbessert Risiko und Sektorstreuung deutlich |
| Sektor-Metriken | `sector_off` ist stark auf Information Technology konzentriert und daher nicht Balanced |
| `max_turnover_cap` | `0.20` reduziert den effektiven Turnover deutlich, wirkt aktuell aber als Kosten-/Effektivturnover-Cap |
| Regime/Cash | trennt die Profile klar in defensiv, ausgewogen und offensiv |

---

### 03.35.2 Gemeinsame Basis der Profile

Alle drei ersten Profilkandidaten verwenden zunächst dieselbe strategische Basis:

| Parameter | Wert |
|---|---|
| Universe | `sp500` |
| `top_k` | 15 |
| `use_sector_limits` | true |
| `max_per_sector` | 2 |
| `max_turnover_cap` | 0.20 |
| Benchmark | `SXR8.DE` |
| `cash_yield_annual` | 0.00 |
| `regime_sma_days` | 200 |

Begründung:

Diese Basis entstand aus den bisherigen Tests als bester Kompromiss aus Rendite, Risiko, Sektorstreuung und effektivem Turnover.

---

### 03.35.3 Conservative v1

| Parameter | Wert |
|---|---|
| `require_above_sma` | true |
| `regime_below_action` | SELL |
| `include_cash` | true |

Kurzform:

```toml
profile = "conservative"
universe = "sp500"
top_k = 15
use_sector_limits = true
max_per_sector = 2
max_turnover_cap = 0.20
require_above_sma = true
regime_below_action = "SELL"
include_cash = true
cash_yield_annual = 0.00
regime_sma_days = 200
benchmark_ticker = "SXR8.DE"
```

## 03.37 Profilvergleich v1 auswerten und Profilstruktur bestätigen

Die Profilvergleichs-Matrix v1 wurde erfolgreich erzeugt.

Getestet wurden drei Profilkandidaten:

| Profil | `require_above_sma` | `regime_below_action` | `include_cash` |
|---|---|---|---|
| Conservative v1 | true | SELL | true |
| Balanced v1 | true | HOLD | false |
| Offensive v1 | false | HOLD | false |

Gemeinsame Basis aller Profile:

| Parameter | Wert |
|---|---|
| Universe | `sp500` |
| `top_k` | 15 |
| `use_sector_limits` | true |
| `max_per_sector` | 2 |
| `max_turnover_cap` | 0.20 |
| `cash_yield_annual` | 0.00 |
| `regime_sma_days` | 200 |
| Benchmark | `SXR8.DE` |

Die Profilvergleichs-Matrix wurde unter `reports/strategy_analysis/profile_compare_v1/profile_compare_v1_summary.md` erzeugt. Alle 9 Läufe waren erfolgreich; die Tests liefen mit `81 passed`. :contentReference[oaicite:0]{index=0}

---

### 03.37.1 Ergebnisübersicht LONG

| Profil | CAGR | Alpha | Max Drawdown | Volatility | Sharpe | Turnover | Time in Cash |
|---|---:|---:|---:|---:|---:|---:|---:|
| Conservative v1 | 13.48% | +2.31% | -22.12% | 21.96% | 0.6900 | 16.78% | 24.49% |
| Balanced v1 | 21.50% | +10.33% | -25.25% | 24.05% | 0.9300 | 14.74% | 0.00% |
| Offensive v1 | 24.32% | +13.15% | -29.63% | 26.85% | 0.9500 | 19.64% | 0.00% |

---

### 03.37.2 Ergebnisübersicht MEDIUM

| Profil | CAGR | Alpha | Max Drawdown | Volatility | Sharpe | Turnover | Time in Cash |
|---|---:|---:|---:|---:|---:|---:|---:|
| Conservative v1 | 24.13% | +8.77% | -22.12% | 24.17% | 1.0200 | 18.48% | 10.53% |
| Balanced v1 | 29.13% | +13.77% | -25.25% | 25.36% | 1.1400 | 17.43% | 0.00% |
| Offensive v1 | 33.85% | +18.49% | -29.63% | 27.89% | 1.1900 | 19.53% | 0.00% |

---

### 03.37.3 Interpretation

Die Profilstruktur wird in MEDIUM und LONG klar bestätigt.

| Profil | Beobachtung | Bewertung |
|---|---|---|
| Conservative v1 | niedrigster Drawdown, Cash-Anteil, geringere Rendite | defensiver Charakter bestätigt |
| Balanced v1 | liegt zwischen Conservative und Offensive | Balanced-Charakter bestätigt |
| Offensive v1 | höchste Rendite, höchster Drawdown | offensiver Charakter bestätigt |

Besonders im LONG-Zeitraum entsteht eine saubere Staffelung:

| Profil | Rendite | Risiko |
|---|---|---|
| Conservative v1 | niedrigste Rendite | niedrigster Drawdown |
| Balanced v1 | mittlere Rendite | mittlerer Drawdown |
| Offensive v1 | höchste Rendite | höchster Drawdown |

Damit erfüllt die Profilstruktur v1 grundsätzlich ihren Zweck.

---

### 03.37.4 SHORT-Einschränkung

Im SHORT-Zeitraum trennt sich die Profilstruktur nicht sauber.

Auffällig ist:

| Profil | CAGR | Max Drawdown | Sharpe |
|---|---:|---:|---:|
| Conservative v1 | 24.55% | -7.96% | 1.4600 |
| Balanced v1 | 24.63% | -7.96% | 1.4600 |
| Offensive v1 | 47.84% | -7.92% | 2.1200 |

Im SHORT-Zeitraum gewinnt `Offensive v1` sogar minimal beim Drawdown und deutlich bei Rendite und Sharpe.

Das wird vorläufig nicht als strukturelles Signal gewertet, sondern als Zeitraum-Effekt.

Bewertung:

> Der SHORT-Zeitraum ist zu kurz, um die defensive Abstufung zuverlässig zu beurteilen.

Für die Profilbewertung sind MEDIUM und LONG belastbarer.

---

### 03.37.5 Sektorstruktur

Die Sektorstruktur bleibt über alle Profile hinweg kontrolliert:

| Kennzahl | Wert |
|---|---:|
| Max Sector Weight | ca. 22.22% |
| Sector Count | 7 |
| Dominant Sector | Consumer Discretionary |

Damit entstehen die Profilunterschiede nicht durch wechselnde Sektorkonzentration, sondern hauptsächlich durch Regime-/Cash-Verhalten.

Das ist positiv, weil die Profile dadurch fachlich sauberer vergleichbar bleiben.

---

### 03.37.6 Profilstruktur v1 bestätigt

Die Profilstruktur v1 wird für die weitere Arbeit bestätigt:

| Profil | Status | Begründung |
|---|---|---|
| Conservative v1 | bestätigt | bester Drawdown, Cash-Schutz, geringere Rendite |
| Balanced v1 | bestätigt | guter Mittelweg aus Rendite und Risiko |
| Offensive v1 | bestätigt | höchste Rendite, höheres Risiko |

Mit Einschränkung:

> Die Bestätigung gilt vor allem für MEDIUM und LONG.  
> SHORT bleibt als Zeitraum-Sonderfall zu behandeln.

---

### 03.37.7 Aktuelle Profilkonfigurationen

#### Conservative v1

```toml
profile = "conservative"
universe = "sp500"
top_k = 15
use_sector_limits = true
max_per_sector = 2
max_turnover_cap = 0.20
require_above_sma = true
regime_below_action = "SELL"
include_cash = true
cash_yield_annual = 0.00
regime_sma_days = 200
benchmark_ticker = "SXR8.DE"
```


### 03.39 Profil-Config-Dateien v1 angelegt und validiert

Die Profilstruktur v1 wurde in eigene versionierbare Profil-Dateien überführt.

#### Angelegt wurden:

configs/profiles/conservative_v1.toml
configs/profiles/balanced_v1.toml
configs/profiles/offensive_v1.toml

Die Profilvergleichs-Matrix lädt diese Profile nun aus den TOML-Dateien. Daraus werden interne StrategyProfile-Objekte erzeugt, die als Overlay auf backtest_config.toml und configs/runner_config.toml angewendet werden.

#### Validierung:

TOML wird mit tomllib geparst.
Alle Pflichtfelder werden geprüft.
regime_below_action erlaubt nur SELL oder HOLD.
Unbekannte Universes werden klar abgelehnt.
Die echten Config-Dateien werden nach dem Lauf wiederhergestellt.

#### Testergebnis:

test_run_profile_compare_v1.py: 5 passed
Gesamttests: 84 passed
Ruff: All checks passed

Die neu erzeugte Profilvergleichs-Matrix stimmt mit der vorherigen Profilvergleichs-Serie in Config-Werten und Kernmetriken für alle 9 Läufe überein. Unterschiede bestehen nur in neuen Run IDs und Zeitstempeln.

Damit ist die Profilstruktur v1 reproduzierbar aus Profil-Dateien ableitbar.


### 03.40 Profil-Runner / Agent-Integration vorbereiten

Nach dem Anlegen und Validieren der Profil-Dateien soll die Profilnutzung in die operative Ausführung vorbereitet werden.

Bisher liegen die Profile als Overlay-Dateien vor:

configs/profiles/conservative_v1.toml
configs/profiles/balanced_v1.toml
configs/profiles/offensive_v1.toml

Die Profilvergleichs-Matrix lädt diese Dateien bereits erfolgreich und erzeugt daraus reproduzierbare Läufe.

Der nächste Schritt ist, diese Profil-Dateien auch für normale Backtester-/Runner-/Agentenläufe nutzbar zu machen.

### 03.40.1 Ziel

Künftig soll ein Lauf nicht nur über technische Config-Dateien gesteuert werden, sondern zusätzlich über ein benanntes Strategieprofil.

Beispiel-Zielbild:

```
python -m scripts.run_bt_run_agent --profile medium --strategy-profile balanced_v1
```

oder alternativ:
```
python -m scripts.run_bt_run_agent --profile medium --strategy-profile configs/profiles/balanced_v1.toml
```

Damit kann der Agent später gezielt Profile vergleichen oder ausführen, ohne einzelne Strategieparameter manuell zu setzen.

### 03.40.2 Warum das wichtig ist

Die Profil-Dateien schaffen eine klare Trennung:

Ebene	Zweck
Backtest-/Runner-Config	technische Laufparameter, Pfade, Zeitraum, Dumps
Profil-Config	fachliche Strategieparameter
Agent	wählt Profil und Laufmodus aus

Dadurch wird das System besser steuerbar und reproduzierbarer.

### 03.40.3 Gewünschtes Verhalten

Ein Profil-Run soll:

Profil-Datei laden
Profil validieren
Profilwerte als Overlay auf Backtest-/Runner-Config anwenden
Backtester und Runner mit identischer Profilbasis starten
Run-Manifest um Profilinformationen erweitern
Reports um Profilinformationen ergänzen
Configs nach temporären Overrides wiederherstellen
bestehende Parität nicht brechen
03.40.4 Profilinformationen im Manifest

Künftig sollte im Run-Manifest erkennbar sein:

Feld	Beispiel
strategy_profile_name	balanced_v1
strategy_profile_label	Balanced v1
strategy_profile_file	configs/profiles/balanced_v1.toml
universe	sp500
top_k	15
max_per_sector	2
max_turnover_cap	0.20
require_above_sma	true
regime_below_action	HOLD
include_cash	false

Damit ist später nachvollziehbar, mit welchem Profil ein Lauf erzeugt wurde.

### 03.40.5 Noch nicht tun

In diesem Schritt soll noch keine neue Strategie optimiert werden.

Nicht ändern:

Auswahl-Logik
Scoring-Logik
Rebalance-Logik
Finalisierung
Decision-Bundle-Struktur
Kostenlogik
Turnover-Cap-Interpretation

Es geht nur darum, die Profilauswahl sauber in den Ausführungsweg vorzubereiten.




### 03.40 Profil-Runner / Agent-Integration umgesetzt

Die Profil-Dateien können nun auch für normale Backtester-/Runner-/Agentenläufe verwendet werden.

| Bereich                         | Ergebnis                                                              |
| ------------------------------- | --------------------------------------------------------------------- |
| Profil-Logik                    | ausgelagert nach `scripts/strategy_profiles.py`                       |
| Runner-Integration              | `scripts/run_bt_run_agent.py` unterstützt `--strategy-profile`        |
| Profilvergleich                 | `scripts/run_profile_compare_v1.py` nutzt die gemeinsame Profil-Logik |
| Tests                           | ergänzt in `tests/unit/scripts/test_run_bt_run_agent_manifest.py`     |
| Strategie-Logik                 | nicht geändert                                                        |
| Scoring/Rebalance/Finalisierung | nicht geändert                                                        |


```
python -m scripts.run_bt_run_agent --profile medium --strategy-profile balanced_v1
```

Alternativ per Pfad:

```
python -m scripts.run_bt_run_agent --profile medium --strategy-profile configs/profiles/balanced_v1.toml
```

#### Unterstützte Profilnamen
| Profilname        | Datei                                   | Label           |
| ----------------- | --------------------------------------- | --------------- |
| `conservative_v1` | `configs/profiles/conservative_v1.toml` | Conservative v1 |
| `balanced_v1`     | `configs/profiles/balanced_v1.toml`     | Balanced v1     |
| `offensive_v1`    | `configs/profiles/offensive_v1.toml`    | Offensive v1    |

#### Overlay-Verhalten
| Punkt               | Umsetzung                                                    |
| ------------------- | ------------------------------------------------------------ |
| Config-Verarbeitung | Backtester und Runner erhalten run-spezifische Config-Kopien |
| Speicherort         | `output_dir/config_overlays/`                                |
| Originalconfigs     | werden nicht dauerhaft überschrieben                         |
| Profilwerte         | werden auf Backtester- und Runner-Config gleich angewendet   |
| Reproduzierbarkeit  | Profilinformationen werden im Manifest gespeichert           |

#### Reporting / Manifest

Die zentrale maschinenlesbare Dokumentation erfolgt in run_manifest.json. Zusätzlich erscheinen die Profilinformationen auch in summary.txt.

| Manifest-Feld            | Bedeutung                      |
| ------------------------ | ------------------------------ |
| `strategy_profile_name`  | technischer Profilname         |
| `strategy_profile_label` | lesbarer Profilname            |
| `strategy_profile_file`  | verwendete Profil-Datei        |
| `universe`               | verwendetes Universe           |
| `top_k`                  | Anzahl Zielpositionen          |
| `use_sector_limits`      | Sektorbegrenzung aktiv         |
| `max_per_sector`         | maximales Sektorlimit          |
| `max_turnover_cap`       | Effektivturnover-/Kosten-Cap   |
| `require_above_sma`      | Regimefilter aktiv             |
| `regime_below_action`    | Verhalten bei negativem Regime |
| `include_cash`           | Cash-Position erlaubt          |
| `cash_yield_annual`      | angenommene Cash-Verzinsung    |
| `regime_sma_days`        | SMA-Zeitraum für Regimefilter  |
| `benchmark_ticker`       | verwendeter Benchmark          |

#### Validierung und Tests
| Prüfung                                            | Ergebnis  |
| -------------------------------------------------- | --------- |
| Profilname lädt `balanced_v1`                      | bestanden |
| Profilpfad lädt dieselbe Datei                     | bestanden |
| ungültiger Profilname erzeugt klare Fehlermeldung  | bestanden |
| ungültige Profil-Datei erzeugt klare Fehlermeldung | bestanden |
| Overlay wird korrekt angewendet                    | bestanden |
| Originalconfigs bleiben unverändert                | bestanden |
| Manifest enthält Profilinformationen               | bestanden |
| gezielte Tests                                     | 22 passed |
| Gesamttests                                        | 90 passed |

#### Smoke-Test

```
..venv\Scripts\python.exe -m scripts.run_bt_run_agent --profile short --strategy-profile balanced_v1
```

| Kennzahl                             | Wert              |
| ------------------------------------ | ----------------- |
| Run ID                               | `20260531_122722` |
| success                              | true              |
| compare_matched                      | true              |
| Manifest enthält Profilinformationen | ja                |
| Originalconfigs unverändert          | ja                |

#### Config-Hashes nach dem Smoke-Test
| Datei                        | Hash                                                               |
| ---------------------------- | ------------------------------------------------------------------ |
| `backtest_config.toml`       | `F2A7E8B17521CDB9A86663ADC712E80D8FEDFE766DE90A9DF4A48638FDE34900` |
| `configs/runner_config.toml` | `4E472B7CE528000A0D4D90D6760C1025C4ADF779D6F50C5581A287A4AF8B1228` |

#### Fazit

Die Profilnutzung für Backtester-/Runner-/Agentenläufe ist vorbereitet.

Die Profile sind nun nicht mehr nur Matrix-Overrides, sondern können direkt über --strategy-profile verwendet werden. Damit ist die Grundlage geschaffen, dass der Agent künftig gezielt Profile wie balanced_v1, conservative_v1 oder offensive_v1 ausführen und vergleichen kann.

### 03.41 Profil-Workflow konsolidieren

Nach der Integration von --strategy-profile können die Strategieprofile nun direkt in normalen Backtester-/Runner-/Agentenläufen verwendet werden.

Die Profile liegen als TOML-Dateien vor:

| Profil          | Datei                                   |
| --------------- | --------------------------------------- |
| Conservative v1 | `configs/profiles/conservative_v1.toml` |
| Balanced v1     | `configs/profiles/balanced_v1.toml`     |
| Offensive v1    | `configs/profiles/offensive_v1.toml`    |


Die Profile können per Name oder per Pfad geladen werden.

### 03.41.1 Einzelnes Profil ausführen

Ein Profil kann direkt über scripts.run_bt_run_agent gestartet werden.

Beispiel Balanced-Profil:

```
python -m scripts.run_bt_run_agent --profile medium --strategy-profile balanced_v1
```

Alternativ per Profil-Dateipfad:

```
python -m scripts.run_bt_run_agent --profile medium --strategy-profile configs/profiles/balanced_v1.toml
```

Damit wird das Profil als Overlay auf die normalen Laufconfigs angewendet.

### 03.41.2 Profile vergleichen

Der direkte Vergleich der drei aktuellen Profilkandidaten erfolgt über:

```
python -m scripts.run_profile_compare_v1
```

Dieser Lauf erzeugt die Vergleichsreports unter:

```
reports/strategy_analysis/profile_compare_v1/
```

Wichtige Summary:

```
reports/strategy_analysis/profile_compare_v1/profile_compare_v1_summary.md
```

### 03.41.3 Aktuelle Profilrollen
| Profil          | Charakter                                  | Einsatzidee                 |
| --------------- | ------------------------------------------ | --------------------------- |
| Conservative v1 | defensiv, Cash-Schutz, geringerer Drawdown | Risikoarme Variante         |
| Balanced v1     | Mittelweg aus Rendite und Risiko           | aktueller Hauptkandidat     |
| Offensive v1    | höchste Rendite, höherer Drawdown          | Renditeorientierte Variante |


Die Profile unterscheiden sich aktuell vor allem durch Regime-/Cash-Verhalten.

| Profil          | `require_above_sma` | `regime_below_action` | `include_cash` |
| --------------- | ------------------- | --------------------- | -------------- |
| Conservative v1 | true                | SELL                  | true           |
| Balanced v1     | true                | HOLD                  | false          |
| Offensive v1    | false               | HOLD                  | false          |

### 03.41.4 Gemeinsame strategische Basis

Alle drei Profile nutzen aktuell dieselbe Basis:

| Parameter           | Wert      |
| ------------------- | --------- |
| Universe            | `sp500`   |
| `top_k`             | 15        |
| `use_sector_limits` | true      |
| `max_per_sector`    | 2         |
| `max_turnover_cap`  | 0.20      |
| `cash_yield_annual` | 0.00      |
| `regime_sma_days`   | 200       |
| Benchmark           | `SXR8.DE` |


Damit bleibt die Sektorstruktur kontrolliert und die Profile sind sauber vergleichbar.

### 03.41.5 Run nachvollziehen

Jeder Lauf mit Strategieprofil schreibt die Profilinformationen in das Run-Manifest.

Zentrale Datei:

```
run_manifest.json
```

Dort sollten mindestens folgende Informationen nachvollziehbar sein:

| Manifest-Feld            | Bedeutung                      |
| ------------------------ | ------------------------------ |
| `strategy_profile_name`  | technischer Profilname         |
| `strategy_profile_label` | lesbarer Profilname            |
| `strategy_profile_file`  | verwendete Profil-Datei        |
| `universe`               | verwendetes Universe           |
| `top_k`                  | Anzahl Zielpositionen          |
| `use_sector_limits`      | Sektorbegrenzung aktiv         |
| `max_per_sector`         | maximales Sektorlimit          |
| `max_turnover_cap`       | Effektivturnover-/Kosten-Cap   |
| `require_above_sma`      | Regimefilter aktiv             |
| `regime_below_action`    | Verhalten bei negativem Regime |
| `include_cash`           | Cash-Position erlaubt          |
| `cash_yield_annual`      | angenommene Cash-Verzinsung    |
| `regime_sma_days`        | SMA-Zeitraum für Regimefilter  |
| `benchmark_ticker`       | verwendeter Benchmark          |


Damit bleibt ein Lauf auch später nachvollziehbar.

### 03.41.6 Neues Profil anlegen

Ein neues Profil entsteht künftig durch eine neue TOML-Datei unter:

```
configs/profiles/
```

Beispiel:

```
configs/profiles/balanced_v2.toml
```

Danach kann das Profil direkt verwendet werden:

```
python -m scripts.run_bt_run_agent --profile medium --strategy-profile balanced_v2
```

Wichtig:

Ein neues Profil sollte nicht durch freie Einzelparameter entstehen, sondern aus einer dokumentierten Analyse oder Testmatrix abgeleitet werden.

### 03.41.7 Profiländerungen testen

Wenn ein Profil geändert oder neu angelegt wird, sollte mindestens geprüft werden:

| Prüfung                      | Zweck                     |
| ---------------------------- | ------------------------- |
| TOML-Datei gültig            | Syntaxfehler vermeiden    |
| Pflichtfelder vorhanden      | Profil vollständig        |
| Profilname eindeutig         | keine Verwechslung        |
| Smoke-Test läuft             | technische Ausführbarkeit |
| `compare_matched=true`       | BT/RUN-Parität erhalten   |
| Manifest enthält Profilinfos | Reproduzierbarkeit        |
| Tests grün                   | technische Sicherheit     |


Empfohlener Smoke-Test:

```
python -m scripts.run_bt_run_agent --profile short --strategy-profile balanced_v1
```

### 03.41.8 Rolle des Agenten

Der Agent kann künftig Profile als Steuerparameter verwenden.

Statt einzelne Strategieparameter zu verändern, kann der Agent gezielt sagen:

| Aufgabe                  | Profil            |
| ------------------------ | ----------------- |
| defensive Prüfung        | `conservative_v1` |
| Standard-/Balanced-Lauf  | `balanced_v1`     |
| Renditeorientierter Lauf | `offensive_v1`    |
| Profilvergleich          | alle Profile      |
| neue Variante testen     | neues Profilfile  |


Damit wird die Agentensteuerung robuster, weil Profile klar benannt und versioniert sind.

### 03.41.9 Aktueller empfohlener Standard

Der aktuelle Hauptkandidat bleibt:

```
balanced_v1
```

Begründung:

| Kriterium      | Bewertung                                   |
| -------------- | ------------------------------------------- |
| Rendite        | deutlich stärker als Conservative           |
| Drawdown       | niedriger als Offensive                     |
| Sharpe         | nahe an Offensive                           |
| Turnover       | niedrigster Wert im Profilvergleich         |
| Sektorstruktur | kontrolliert                                |
| Cash           | kein dauerhafter Renditeverzicht durch Cash |


Balanced v1 ist damit aktuell der beste Kandidat für weitere Robustheits- und Live-Tauglichkeitsprüfungen.

### 03.41.10 Nächste sinnvolle Phase

Nach der Konsolidierung des Profil-Workflows bietet sich als nächste Phase an:

| Nächste Phase                    | Zweck                                              |
| -------------------------------- | -------------------------------------------------- |
| Profil-Robustheit / Walk-forward | Prüfen, ob Profile über Zeiträume stabil bleiben   |
| Weitere Universes                | Prüfen, ob Profile außerhalb `sp500` funktionieren |
| Live-Tauglichkeit                | Kosten, Slippage, Steuern, echte Handelsbremse     |
| Agentenautomatisierung           | Profile automatisch laufen lassen und vergleichen  |


Damit ist Phase 3 fachlich weitgehend abgeschlossen. Die Profile sind abgeleitet, versioniert, ausführbar und vergleichbar.


### 03.42 Offene Punkte und Roadmap für Phase 4

Phase 3 hat aus den bisherigen Strategieanalysen eine erste belastbare Profilstruktur hervorgebracht.

Aktueller Stand:

| Bereich                   | Status         |
| ------------------------- | -------------- |
| Universe-Konfiguration    | erledigt       |
| Run-Vergleich & Reporting | erledigt       |
| `top_k`-Analyse           | erledigt       |
| `max_per_sector`-Analyse  | erledigt       |
| Sektor-Metriken           | ergänzt        |
| Performance-Cache         | umgesetzt      |
| Regime/Cash-Analyse       | erledigt       |
| Profilstruktur v1         | bestätigt      |
| Profil-Dateien            | angelegt       |
| Profilvergleich           | reproduzierbar |
| `--strategy-profile`      | integriert     |
| Profil-Workflow           | konsolidiert   |


Damit ist Phase 3 fachlich weitgehend abgeschlossen.

### 03.42.1 Aktueller Profilstand
| Profil          | Datei                                   | Rolle                   |
| --------------- | --------------------------------------- | ----------------------- |
| Conservative v1 | `configs/profiles/conservative_v1.toml` | defensiv                |
| Balanced v1     | `configs/profiles/balanced_v1.toml`     | aktueller Hauptkandidat |
| Offensive v1    | `configs/profiles/offensive_v1.toml`    | renditeorientiert       |


Die Profile können direkt ausgeführt werden:

```
python -m scripts.run_bt_run_agent --profile medium --strategy-profile balanced_v1
```

Oder über den Profilvergleich:

```
python -m scripts.run_profile_compare_v1
```

### 03.42.2 Wichtigste offene fachliche Fragen
| Frage                                                      | Bedeutung                  |
| ---------------------------------------------------------- | -------------------------- |
| Sind die Profile über weitere Zeiträume stabil?            | Robustheit prüfen          |
| Funktionieren die Profile auch außerhalb `sp500`?          | Übertragbarkeit prüfen     |
| Ist `balanced_v1` wirklich live-tauglich?                  | Investierbarkeit prüfen    |
| Ist `max_turnover_cap` als weicher Kosten-Cap ausreichend? | Handelsrealität prüfen     |
| Brauchen wir eine echte Handelsbremse?                     | Turnover real begrenzen    |
| Wie wirken realistischere Kosten, Slippage und Steuern?    | Nettoergebnis prüfen       |
| Wie stabil ist die Sektorstruktur über die Zeit?           | Klumpenrisiko prüfen       |
| Wie verhält sich das Profil in Krisenphasen?               | Drawdown-Robustheit prüfen |

### 03.42.3 Offene technische Punkte
| Punkt                                          | Grund                       |
| ---------------------------------------------- | --------------------------- |
| Profil-Overlay weiter zentralisieren           | weniger Duplikate           |
| Config-Snapshot je Run prüfen                  | Reproduzierbarkeit          |
| echte Profil-Runs in Agent-Workflow aufnehmen  | Automatisierung             |
| Testlaufzeit weiter beobachten                 | Entwicklungsgeschwindigkeit |
| alte Test-/Store-Positions-Failures beobachten | saubere Testbasis           |
| temporäre Matrix-Skripte ggf. vereinheitlichen | Wartbarkeit                 |
| Report-Struktur standardisieren                | Vergleichbarkeit            |
| Run-Artefakte langfristig aufräumen            | Speicher/Übersicht          |

### 03.42.4 Empfohlene Phase 4

Die nächste fachliche Phase sollte sich auf Robustheit konzentrieren.

Vorschlag:

## Phase 4 – Profil-Robustheit & Walk-forward

Ziel:

Die drei Profilkandidaten sollen nicht nur auf den bisherigen SHORT/MEDIUM/LONG-Läufen funktionieren, sondern über zusätzliche Zeiträume und Marktphasen geprüft werden.

### 03.42.5 Phase-4-Arbeitspakete
| Abschnitt | Thema                                         | Ziel                                     |
| --------- | --------------------------------------------- | ---------------------------------------- |
| 04.01     | Robustheitsplan definieren                    | Testlogik festlegen                      |
| 04.02     | Walk-forward-Zeitfenster festlegen            | Zeitraumabhängigkeit prüfen              |
| 04.03     | Profilvergleich über mehrere Start-/Endpunkte | Stabilität messen                        |
| 04.04     | Krisen-/Stressphasen prüfen                   | Drawdown-Verhalten analysieren           |
| 04.05     | Profil-Ranking über Zeiträume                 | Gewinner nicht nur punktuell bestimmen   |
| 04.06     | Balanced v1 Robustheitsbewertung              | Hauptkandidat bestätigen oder verwerfen  |
| 04.07     | Profil v2 ableiten                            | falls nötig neue Profilversion erstellen |

### 03.42.6 Mögliche Walk-forward-Struktur

Eine erste Walk-forward-Struktur könnte so aussehen:

| Test | Zeitraum           | Zweck                         |
| ---- | ------------------ | ----------------------------- |
| WF1  | jüngerer Zeitraum  | aktuelles Marktverhalten      |
| WF2  | mittlerer Zeitraum | jüngere Historie              |
| WF3  | längerer Zeitraum  | Stabilität über mehrere Jahre |
| WF4  | Stressphase        | Krisenfestigkeit              |
| WF5  | Erholungsphase     | Teilnahme an Aufwärtsphasen   |


Die genaue technische Umsetzung muss noch festgelegt werden.

Wichtig ist, dass die Profile nicht nur einmalig auf einem günstigen Zeitraum gut aussehen.

### 03.42.7 Mögliche Bewertungslogik für Phase 4

Für jedes Profil sollten je Zeitraum mindestens folgende Werte verglichen werden:

| Kennzahl          | Bedeutung                      |
| ----------------- | ------------------------------ |
| CAGR              | Rendite                        |
| Alpha             | Benchmark-Abstand              |
| Max Drawdown      | Hauptrisiko                    |
| Volatility        | Schwankung                     |
| Sharpe            | Rendite-Risiko                 |
| Turnover          | Handelbarkeit                  |
| Down Capture      | Verhalten in fallenden Phasen  |
| Up Capture        | Teilnahme an steigenden Phasen |
| Time in Cash      | Defensive Wirkung              |
| Max Sector Weight | Sektorrisiko                   |
| Sector Count      | Diversifikation                |


Zusätzlich sollte ein Profil nicht nur nach maximaler Rendite bewertet werden, sondern nach Profilziel.

### 03.42.8 Bewertungslogik je Profil
| Profil       | Primäre Ziele                                                    | Sekundäre Ziele          |
| ------------ | ---------------------------------------------------------------- | ------------------------ |
| Conservative | niedriger Drawdown, niedrige Down Capture, geringere Volatilität | akzeptable Rendite       |
| Balanced     | gutes Verhältnis aus CAGR, Drawdown und Sharpe                   | kontrollierter Turnover  |
| Offensive    | hohe CAGR und Alpha                                              | Drawdown noch akzeptabel |


Damit wird verhindert, dass alle Profile nur nach Rendite bewertet werden.

### 03.42.9 Phase 5 als Ausblick

Nach der Robustheitsphase kann die Agentenautomatisierung stärker ausgebaut werden.

Mögliche Phase 5:

## Phase 5 – Agentensteuerung & Strategieautomatisierung
| Thema                             | Ziel                   |
| --------------------------------- | ---------------------- |
| Agent startet Profil-Runs         | Automatisierung        |
| Agent vergleicht Profile          | Auswertung             |
| Agent erkennt schwache Profile    | Warnung                |
| Agent schlägt neue Testmatrix vor | iterative Verbesserung |
| Agent erzeugt Strategie-Reports   | Dokumentation          |
| Agent verwaltet Profilversionen   | Reproduzierbarkeit     |


Phase 5 sollte erst starten, wenn Phase 4 zeigt, welche Profile robust genug sind.

### 03.42.10 Vorläufige Entscheidung

Phase 3 kann nach aktuellem Stand als erfolgreich abgeschlossen werden.

Ergebnis:

| Ergebnis                        | Status                           |
| ------------------------------- | -------------------------------- |
| Profile abgeleitet              | ja                               |
| Profile versioniert             | ja                               |
| Profile ausführbar              | ja                               |
| Profile vergleichbar            | ja                               |
| Profilinformationen im Manifest | ja                               |
| Hauptkandidat identifiziert     | `balanced_v1`                    |
| nächste Phase klar              | Profil-Robustheit / Walk-forward |


Empfehlung:

Als nächstes sollte ein neuer Chat für Phase 4 gestartet werden:

```
04 – Profil-Robustheit & Walk-forward
```

Ziel dieses neuen Chats:

Die Profile conservative_v1, balanced_v1 und offensive_v1 über zusätzliche Zeiträume, Marktphasen und Robustheitskriterien prüfen.


## 04.10 – Robustheitsplan

Nach Abschluss der bisherigen Phasen ist die Strategie technisch stabil genug, um nicht nur einzelne Backtests zu betrachten, sondern die Robustheit der entwickelten Risikoprofile systematisch zu prüfen.

Bisherige Phasen:

| Phase                                      |   Status | Ergebnis                                    |
| ------------------------------------------ | -------: | ------------------------------------------- |
| Phase 1 – Universe-Konfiguration           | erledigt | Universes sind konfigurierbar und validiert |
| Phase 2 – Run-Vergleich & Reporting        | erledigt | Runs können strukturiert verglichen werden  |
| Phase 3 – Strategieanalyse & Risikoprofile | erledigt | Drei Risikoprofile wurden definiert         |

Aktuelle Risikoprofile:

| Profil          | Datei                                   | Rolle                   |
| --------------- | --------------------------------------- | ----------------------- |
| Conservative v1 | `configs/profiles/conservative_v1.toml` | defensiv                |
| Balanced v1     | `configs/profiles/balanced_v1.toml`     | aktueller Hauptkandidat |
| Offensive v1    | `configs/profiles/offensive_v1.toml`    | renditeorientiert       |

Die Profile können über `--strategy-profile` ausgeführt werden.

[CODE_START]
python -m scripts.run_bt_run_agent --profile medium --strategy-profile balanced_v1
[CODE_END]

### Ziel der Robustheitsprüfung

Ziel dieser Phase ist es nicht mehr, nur das im bisherigen Vergleich beste Profil zu finden.

Stattdessen soll geprüft werden:

> Welches Profil bleibt auch über zusätzliche Zeiträume, unterschiedliche Marktphasen und strengere Robustheitskriterien stabil?

Dabei steht besonders `balanced_v1` im Fokus, weil dieses Profil aktuell der Hauptkandidat ist. `conservative_v1` und `offensive_v1` dienen als Vergleichsprofile, um die Risiko-/Rendite-Eigenschaften besser einordnen zu können.

### Grundprinzip

Ein Profil gilt nicht deshalb als robust, weil es in einem einzelnen Backtest gut abschneidet.

Ein Profil gilt erst dann als belastbar, wenn es:

* über mehrere Zeiträume akzeptable Ergebnisse liefert,
* in schwierigen Marktphasen keine unvertretbaren Ausreißer zeigt,
* im Vergleich zur Benchmark nachvollziehbar abschneidet,
* Turnover und Handelsaktivität nicht unnötig erhöht,
* und seine Rolle im Risikoprofil erfüllt.

Das bedeutet:

| Profil            | Erwartung                                                                              |
| ----------------- | -------------------------------------------------------------------------------------- |
| `conservative_v1` | geringerer Drawdown, geringere Volatilität, dafür ggf. geringere Rendite               |
| `balanced_v1`     | guter Kompromiss aus Rendite, Risiko, Turnover und Stabilität                          |
| `offensive_v1`    | höhere Renditechance, aber nur akzeptabel, wenn Drawdown und Turnover nicht entgleisen |

### Prüfebenen

Die Robustheitsprüfung soll aus mehreren Prüfebenen bestehen.

| Prüfebene           | Zweck                                                              |
| ------------------- | ------------------------------------------------------------------ |
| Standard-Zeiträume  | Vergleich über `short`, `medium` und `long`                        |
| Marktphasen         | Verhalten in Crash-, Erholungs-, Seitwärts- und Trendphasen        |
| Walk-forward        | Stabilität über mehrere aufeinanderfolgende Stichtage              |
| Risikoanalyse       | Drawdown, Volatilität, Sharpe, Turnover und Cash-Verhalten         |
| Benchmark-Vergleich | Einordnung gegenüber SPY/SXR8.DE                                   |
| Profil-Ranking      | nachvollziehbare Entscheidung, welches Profil Hauptkandidat bleibt |

### Testblock A – Standard-Zeiträume

Im ersten Schritt sollen alle drei Profile über die bestehenden Zeitraumprofile ausgeführt werden.

| Zeitraumprofil | Zweck                                                 |
| -------------- | ----------------------------------------------------- |
| `short`        | jüngere Marktphase und schnelle Plausibilitätsprüfung |
| `medium`       | aktueller Hauptvergleich                              |
| `long`         | maximale verfügbare Historie und Langfristrobustheit  |

Daraus ergibt sich eine erste Testmatrix:

| Zeitraumprofil | Conservative v1 | Balanced v1 | Offensive v1 |
| -------------- | --------------: | ----------: | -----------: |
| `short`        |          prüfen |      prüfen |       prüfen |
| `medium`       |          prüfen |      prüfen |       prüfen |
| `long`         |          prüfen |      prüfen |       prüfen |

Diese Matrix ist bewusst einfach gehalten. Sie soll zuerst zeigen, ob eines der Profile bereits über die bekannten Standardzeiträume instabil wirkt.

### Testblock B – Marktphasen

Im zweiten Schritt sollen gezielte Marktphasen betrachtet werden.

Mögliche Marktphasen:

| Marktphase | Typ                         | Zweck                                |
| ---------- | --------------------------- | ------------------------------------ |
| 2020       | Crash und schnelle Erholung | Verhalten bei abruptem Markteinbruch |
| 2022       | Bärenmarkt / Zinsphase      | Verhalten in längerem Stressumfeld   |
| 2023       | Erholung / Momentumphase    | Verhalten bei starker Markterholung  |
| 2024/2025  | jüngere Marktphase          | Nähe zur aktuellen Marktsituation    |

Die konkreten Start- und Enddaten sollten erst festgelegt werden, wenn klar ist, welche historischen Daten im Backtester zuverlässig verfügbar sind.

Wichtig ist hier nicht nur die Rendite, sondern besonders:

* maximaler Drawdown,
* Erholungsverhalten,
* Cash-Anteil,
* Turnover,
* Benchmark-Abstand,
* und ob das Profil seiner Rolle entspricht.

### Testblock C – Walk-forward

Der Walk-forward-Test soll zunächst bewusst einfach bleiben.

Ziel ist keine automatische Parameteroptimierung, sondern eine Stabilitätsprüfung über mehrere Stichtage.

Grundidee:

| Element   | Beschreibung                                     |
| --------- | ------------------------------------------------ |
| Stichtage | mehrere aufeinanderfolgende `as_of`-Zeitpunkte   |
| Frequenz  | zunächst monatlich oder quartalsweise            |
| Profile   | `conservative_v1`, `balanced_v1`, `offensive_v1` |
| Ergebnis  | Kennzahlen je Profil und Stichtag                |
| Ziel      | prüfen, ob die Profile über Zeit stabil bleiben  |

Beispielhafte Fragestellungen:

* Bleibt `balanced_v1` über mehrere Stichtage der beste Kompromiss?
* Gibt es Zeitpunkte, an denen `offensive_v1` deutlich zu riskant wird?
* Liefert `conservative_v1` tatsächlich den erwarteten Schutz?
* Entstehen Ausreißer bei Turnover, Cash oder Drawdown?
* Sind die Ergebnisse stark abhängig von einzelnen Start- oder Endpunkten?

### Bewertungslogik

Die Bewertung soll nicht rein renditeorientiert erfolgen.

Stattdessen soll eine Scorecard verwendet werden, die Rendite, Risiko und praktische Handelbarkeit gemeinsam betrachtet.

| Kriterium                          | Bedeutung                                       |
| ---------------------------------- | ----------------------------------------------- |
| Total Return / CAGR                | Renditeleistung                                 |
| Max Drawdown                       | größter Kapitalrückgang                         |
| Sharpe / risikoadjustierte Rendite | Verhältnis von Rendite zu Schwankung            |
| Volatilität                        | Schwankungsintensität                           |
| Turnover                           | Handelsaktivität und Reibung                    |
| Cash-Anteil                        | Auswirkung der Regime- und Risikosteuerung      |
| Benchmark-Abstand                  | Vergleich zur passiven Alternative              |
| Stabilität über Zeiträume          | Robustheit gegen Zeitraumwahl                   |
| Ausreißer                          | Warnsignal bei einzelnen problematischen Läufen |

Für `balanced_v1` ist das Ziel nicht, in jeder Einzelwertung Platz 1 zu erreichen.

Das Ziel ist:

> möglichst oft gut, selten schlecht, keine gefährlichen Ausreißer.

### Vorläufige Entscheidungsregeln

Die Ergebnisse der Robustheitsprüfung sollen am Ende zu einer nachvollziehbaren Profilentscheidung führen.

| Beobachtung                                                      | Mögliche Konsequenz                               |
| ---------------------------------------------------------------- | ------------------------------------------------- |
| `balanced_v1` bleibt über die meisten Tests stabil               | Profil bleibt Hauptkandidat                       |
| `conservative_v1` ist ähnlich rentabel, aber deutlich stabiler   | Conservative als Alternative ernsthaft prüfen     |
| `offensive_v1` bringt kaum Mehrertrag, aber deutlich mehr Risiko | Offensive zurückstellen                           |
| alle Profile zeigen Schwächen in bestimmten Phasen               | gezielte Nachjustierung der Profilparameter       |
| starke Instabilität im Walk-forward                              | keine Optimierung starten, zuerst Ursachenanalyse |

### Geplante Reihenfolge

Die Umsetzung der Phase 4 soll schrittweise erfolgen.

| Schritt | Inhalt                                                      |
| ------- | ----------------------------------------------------------- |
| 04.10   | Robustheitsplan dokumentieren                               |
| 04.20   | vorhandene Agent-/Compare-Struktur prüfen                   |
| 04.30   | Profil-Matrix über `short`, `medium`, `long` automatisieren |
| 04.40   | Markdown-Report für Profilvergleiche erzeugen               |
| 04.50   | Marktphasen-Konzept ergänzen                                |
| 04.60   | Walk-forward-Runner planen                                  |
| 04.70   | Walk-forward-Auswertung erstellen                           |
| 04.80   | finale Profilentscheidung dokumentieren                     |

### Nächster technischer Schritt

Der erste technische Umsetzungsschritt sollte noch kein vollständiger Walk-forward-Test sein.

Sinnvoller ist zunächst:

> Eine automatisierte Profil-Matrix über `short`, `medium` und `long`, jeweils für `conservative_v1`, `balanced_v1` und `offensive_v1`.

Damit entsteht eine erste belastbare Vergleichsbasis, auf der spätere Marktphasen- und Walk-forward-Analysen aufbauen können.

## 04.20 – Vorhandene Struktur prüfen

Bevor neue Skripte oder Auswertungen gebaut werden, soll geprüft werden, welche bestehende Struktur bereits vorhanden ist und wiederverwendet werden kann.

Ziel ist ausdrücklich:

> Keine neue Parallelstruktur bauen, sondern die bestehende Agent-/Runner-/Compare-Struktur erweitern.

### Vorhandene Bausteine

Aus den bisherigen Phasen stehen bereits mehrere Bausteine zur Verfügung.

| Baustein                   | Zweck                                                        |
| -------------------------- | ------------------------------------------------------------ |
| `scripts.run_bt_run_agent` | zentraler Einstieg für Backtest, Runner und Vergleich        |
| `--profile`                | Auswahl des Zeitraumprofils, z. B. `short`, `medium`, `long` |
| `--strategy-profile`       | Auswahl des Strategieprofils, z. B. `balanced_v1`            |
| Profil-Dateien             | TOML-Dateien unter `configs/profiles/`                       |
| Run-Artefakte              | erzeugte Backtest-/Runner-/Compare-Ergebnisse                |
| Compare-Logik              | Vergleich von Backtester- und Runner-Ergebnissen             |
| Markdown-Reports           | bisherige strukturierte Ergebnisdokumentation                |

Damit ist die technische Basis für die Profil-Robustheitsprüfung bereits weitgehend vorhanden.

### Ziel der Prüfung

Codex soll zunächst nicht sofort einen Walk-forward-Runner bauen.

Stattdessen soll geprüft werden:

* Welche vorhandenen Skripte bereits `--strategy-profile` unterstützen.
* Ob `short`, `medium` und `long` mit allen drei Profilen ausführbar sind.
* Wo die Run-Ergebnisse gespeichert werden.
* Ob die vorhandenen Reports ausreichend Kennzahlen enthalten.
* Ob Profilname und Zeitraumprofil in den erzeugten Artefakten eindeutig dokumentiert werden.
* Ob bestehende Compare-/Reporting-Funktionen für eine Profil-Matrix wiederverwendet werden können.

### Zu prüfende Profile

| Profil            | Datei                                   |
| ----------------- | --------------------------------------- |
| `conservative_v1` | `configs/profiles/conservative_v1.toml` |
| `balanced_v1`     | `configs/profiles/balanced_v1.toml`     |
| `offensive_v1`    | `configs/profiles/offensive_v1.toml`    |

### Zu prüfende Zeitraumprofile

| Zeitraumprofil | Zweck                        |
| -------------- | ---------------------------- |
| `short`        | schneller Plausibilitätslauf |
| `medium`       | aktueller Hauptvergleich     |
| `long`         | Langfristprüfung             |

### Erwartete Testmatrix

Die spätere Robustheitsmatrix soll aus neun Läufen bestehen.

| Zeitraumprofil | Conservative v1 | Balanced v1 | Offensive v1 |
| -------------- | --------------: | ----------: | -----------: |
| `short`        |            Lauf |        Lauf |         Lauf |
| `medium`       |            Lauf |        Lauf |         Lauf |
| `long`         |            Lauf |        Lauf |         Lauf |

### Mindestanforderung an die Artefakte

Für jeden Lauf sollten mindestens folgende Informationen nachvollziehbar sein:

| Information       | Zweck                                 |
| ----------------- | ------------------------------------- |
| `run_id`          | eindeutige Zuordnung                  |
| Zeitraumprofil    | z. B. `short`, `medium`, `long`       |
| Strategieprofil   | z. B. `balanced_v1`                   |
| Universe          | z. B. `sp500` oder `sp500_top100`     |
| Universe-Hash     | Nachvollziehbarkeit der Datenbasis    |
| Backtest-Ergebnis | Performance- und Risikokennzahlen     |
| Runner-Ergebnis   | Paritätsprüfung gegen Backtest        |
| Compare-Ergebnis  | Aussage, ob BT und RUN übereinstimmen |
| Report-Pfad       | spätere Weiterverarbeitung            |

### Wichtige Kennzahlen

Für die Profil-Robustheit sind insbesondere folgende Kennzahlen relevant:

| Kennzahl                     | Bedeutung                                     |
| ---------------------------- | --------------------------------------------- |
| Total Return                 | Gesamtrendite                                 |
| CAGR                         | annualisierte Rendite                         |
| Max Drawdown                 | größter Verlust vom Hoch                      |
| Sharpe                       | risikoadjustierte Rendite                     |
| Volatilität                  | Schwankungsintensität                         |
| Turnover                     | Handelsaktivität                              |
| Cash-Anteil                  | Wirkung der Risikosteuerung                   |
| Benchmark Return             | Vergleich zur passiven Anlage                 |
| Alpha / Relative Performance | Mehr- oder Minderleistung gegenüber Benchmark |
| Compare matched              | technische Parität BT/RUN                     |

Falls einzelne Kennzahlen in bestehenden Reports noch nicht vorhanden sind, soll Codex zunächst nur feststellen, welche fehlen. Die Erweiterung der Reports kann danach gezielt erfolgen.

### Leitplanken für Codex

Für die Umsetzung gelten folgende Leitplanken:

* Keine Strategie-, Scoring-, Rebalance- oder Finalisierungslogik ändern.
* Keine bestehende Profil-Logik umbauen, wenn sie bereits funktioniert.
* Keine neue Parallel-Compare-Logik erstellen.
* Bestehende Agent-/Report-Struktur bevorzugt wiederverwenden.
* Neue Funktionen möglichst klein und klar abgrenzen.
* Profilname und Zeitraumprofil müssen in Reports eindeutig sichtbar sein.
* Änderungen sollen durch Tests oder zumindest nachvollziehbare Probeläufe abgesichert werden.

### Ergebnis von 04.20

Am Ende dieses Schritts soll klar sein:

1. Welche bestehenden Dateien für die Profil-Matrix genutzt werden können.
2. Ob `scripts.run_bt_run_agent` als zentraler Einstieg ausreicht.
3. Welche Kennzahlen bereits verfügbar sind.
4. Welche Report-Erweiterungen eventuell notwendig sind.
5. Ob für 04.30 ein neues kleines Wrapper-Skript sinnvoll ist.

### Vorläufige Einschätzung

Die wahrscheinlich sinnvollste Erweiterung ist ein kleines Matrix-Skript, das bestehende Läufe orchestriert.

Möglicher Name:

`python -m scripts.run_profile_robustness_matrix`

Dieses Skript sollte zunächst nur die Kombinationen aus Zeitraumprofil und Strategieprofil ausführen und die Ergebnisse einsammeln.

Die fachliche Logik bleibt dabei vollständig in den bestehenden Komponenten.

## 04.30 – Profil-Robustheitsmatrix

Für die erste technische Robustheitsprüfung wurde ein neues Matrix-Skript erstellt:

[CODE_START]
scripts/run_profile_robustness_matrix.py
[CODE_END]

Das Skript führt eine 3x3-Matrix aus Zeitraumprofilen und Strategieprofilen aus.

Zeitraumprofile:

* `short`
* `medium`
* `long`

Strategieprofile:

* `conservative_v1`
* `balanced_v1`
* `offensive_v1`

Jede Matrix-Zelle wird ausschließlich über den bestehenden zentralen Einstieg ausgeführt:

[CODE_START]
python -m scripts.run_bt_run_agent --profile <profile> --strategy-profile <strategy_profile>
[CODE_END]

Wichtig ist, dass keine Config-Dateien temporär mutiert werden. Dadurch entstehen saubere Run-Manifests inklusive der `strategy_profile_*`-Felder.

Das Skript schreibt die Ergebnisse nach:

[CODE_START]
reports/strategy_analysis/profile_robustness_matrix/
[CODE_END]

Erzeugte Dateien:

[CODE_START]
profile_robustness_matrix_summary.md
profile_robustness_matrix_summary.json
[CODE_END]

Fehler einzelner Läufe brechen die gesamte Matrix nicht ab, sondern werden pro Matrix-Zelle dokumentiert.

Verifikation:

[CODE_START]
python -m pytest tests\unit\scripts\test_run_profile_robustness_matrix.py tests\unit\scripts\test_run_profile_compare_v1.py tests\unit\scripts\test_run_bt_run_agent_manifest.py
[CODE_END]

Ergebnis:

[CODE_START]
27 passed
[CODE_END]

Ruff-Prüfung:

[CODE_START]
python -m ruff check scripts\run_profile_robustness_matrix.py tests\unit\scripts\test_run_profile_robustness_matrix.py
[CODE_END]

Ergebnis:

[CODE_START]
All checks passed
[CODE_END]

Die vollständige 9er-Matrix wurde nach der Implementierung noch nicht automatisch gestartet. Das ist bewusst sinnvoll, da dadurch neun Backtest-/Runner-Läufe ausgelöst werden.

## 04.40 – Auswertung der Profil-Robustheitsmatrix

Nach dem Fix des Multi-Compare-Seed-Verhaltens wurde die vollständige Profil-Robustheitsmatrix erneut ausgeführt.

Die Matrix umfasst:

* 3 Zeitraumprofile
* 3 Strategieprofile
* insgesamt 9 Läufe

Zeitraumprofile:

* `short`
* `medium`
* `long`

Strategieprofile:

* `conservative_v1`
* `balanced_v1`
* `offensive_v1`

### Technischer Status

Die erneute Matrixausführung war vollständig erfolgreich.

| Kennzahl              | Ergebnis |
| --------------------- | -------: |
| Läufe gesamt          |        9 |
| Erfolgreiche Läufe    |        9 |
| Fehlgeschlagene Läufe |        0 |
| Compare-Mismatches    |        0 |

Damit ist die BT/RUN-Parität für alle getesteten Kombinationen hergestellt.

### Ausgeführte Matrix

| Zeitraumprofil | Strategieprofil   | Compare matched |
| -------------- | ----------------- | --------------: |
| `short`        | `conservative_v1` |            true |
| `short`        | `balanced_v1`     |            true |
| `short`        | `offensive_v1`    |            true |
| `medium`       | `conservative_v1` |            true |
| `medium`       | `balanced_v1`     |            true |
| `medium`       | `offensive_v1`    |            true |
| `long`         | `conservative_v1` |            true |
| `long`         | `balanced_v1`     |            true |
| `long`         | `offensive_v1`    |            true |

Damit können die Kennzahlen der Robustheitsmatrix fachlich ausgewertet werden.

---

### Ergebnisblock `short`

| Profil            | Total Return |    CAGR | Max Drawdown | Sharpe | Volatility | Turnover |
| ----------------- | -----------: | ------: | -----------: | -----: | ---------: | -------: |
| `conservative_v1` |      10.16 % | 24.55 % |      -7.96 % |   1.46 |    15.79 % |  20.00 % |
| `balanced_v1`     |      10.19 % | 24.63 % |      -7.96 % |   1.46 |    15.79 % |  17.14 % |
| `offensive_v1`    |      18.81 % | 47.84 % |      -7.92 % |   2.12 |    19.21 % |  20.00 % |

Im kurzen Zeitraum liegt `offensive_v1` klar vorne. Das Profil erzielt die höchste Rendite und den höchsten Sharpe-Wert, ohne in diesem Zeitraum einen höheren Drawdown zu zeigen.

`balanced_v1` und `conservative_v1` liegen nahezu gleichauf. Der Vorteil von `balanced_v1` liegt hier vor allem im geringeren Turnover.

Zwischenfazit `short`:

| Profil            | Bewertung                                                       |
| ----------------- | --------------------------------------------------------------- |
| `conservative_v1` | solide, aber kaum Vorteil gegenüber `balanced_v1`               |
| `balanced_v1`     | ähnlich defensiv wie conservative, aber mit geringerem Turnover |
| `offensive_v1`    | klar stärkstes Profil im kurzen Zeitraum                        |

---

### Ergebnisblock `medium`

| Profil            | Total Return |    CAGR | Max Drawdown | Sharpe | Volatility | Turnover |
| ----------------- | -----------: | ------: | -----------: | -----: | ---------: | -------: |
| `conservative_v1` |      36.51 % | 24.13 % |     -22.12 % |   1.02 |    24.17 % |  18.48 % |
| `balanced_v1`     |      44.51 % | 29.13 % |     -25.25 % |   1.14 |    25.36 % |  17.43 % |
| `offensive_v1`    |      52.18 % | 33.85 % |     -29.63 % |   1.19 |    27.89 % |  19.53 % |

Im mittleren Zeitraum zeigt sich die Profilabstufung sehr sauber.

`conservative_v1` hat den geringsten Drawdown, verzichtet dafür aber deutlich auf Rendite.

`offensive_v1` erzielt die höchste Rendite und den höchsten Sharpe-Wert, allerdings mit dem höchsten Drawdown, der höchsten Volatilität und dem höchsten Turnover.

`balanced_v1` liegt zwischen beiden Profilen, erzielt aber den niedrigsten Turnover der drei Medium-Läufe. Das ist für die praktische Handelbarkeit positiv.

Zwischenfazit `medium`:

| Profil            | Bewertung                                              |
| ----------------- | ------------------------------------------------------ |
| `conservative_v1` | defensiv, aber mit deutlichem Renditeverzicht          |
| `balanced_v1`     | sehr guter Kompromiss aus Rendite, Risiko und Turnover |
| `offensive_v1`    | renditestark, aber sichtbar riskanter                  |

---

### Ergebnisblock `long`

| Profil            | Total Return |    CAGR | Max Drawdown | Sharpe | Volatility | Turnover |
| ----------------- | -----------: | ------: | -----------: | -----: | ---------: | -------: |
| `conservative_v1` |      64.63 % | 13.48 % |     -22.12 % |   0.69 |    21.96 % |  16.78 % |
| `balanced_v1`     |     115.48 % | 21.50 % |     -25.25 % |   0.93 |    24.05 % |  14.74 % |
| `offensive_v1`    |     135.89 % | 24.32 % |     -29.63 % |   0.95 |    26.85 % |  19.64 % |

Der lange Zeitraum ist besonders aussagekräftig.

`conservative_v1` reduziert den Drawdown, verliert aber langfristig deutlich an Rendite.

`offensive_v1` liefert die höchste Rendite, erkauft diese aber mit dem höchsten Drawdown, der höchsten Volatilität und dem höchsten Turnover.

`balanced_v1` zeigt im langen Zeitraum ein sehr gutes Verhältnis aus Rendite, Risiko und Handelbarkeit. Besonders auffällig ist der niedrigste Turnover der drei Long-Läufe.

Zwischenfazit `long`:

| Profil            | Bewertung                                      |
| ----------------- | ---------------------------------------------- |
| `conservative_v1` | stabiler, aber langfristig zu renditeschwach   |
| `balanced_v1`     | stärkster Kompromiss im Langfristvergleich     |
| `offensive_v1`    | renditestark, aber mit deutlich höherem Risiko |

---

### Gesamtvergleich

| Profil            | Stärke                               | Schwäche                                               | Gesamteindruck                              |
| ----------------- | ------------------------------------ | ------------------------------------------------------ | ------------------------------------------- |
| `conservative_v1` | geringerer Drawdown                  | deutlicher Renditeverzicht                             | defensiv, aber möglicherweise zu vorsichtig |
| `balanced_v1`     | guter Kompromiss, niedriger Turnover | nicht immer höchste Rendite                            | aktueller Hauptkandidat bestätigt           |
| `offensive_v1`    | höchste Rendite                      | höherer Drawdown, höhere Volatilität, höherer Turnover | interessant, aber riskanter                 |

### Bewertung von `balanced_v1`

`balanced_v1` erfüllt die Rolle als Hauptkandidat sehr gut.

Das Profil ist nicht in jedem Einzelkriterium der Spitzenreiter, zeigt aber über die Matrix hinweg den besten Kompromiss:

* deutlich höhere Rendite als `conservative_v1`,
* deutlich geringerer Drawdown als `offensive_v1`,
* gute Sharpe-Werte,
* sehr guter Turnover, besonders im `medium`- und `long`-Zeitraum,
* vollständige BT/RUN-Parität über alle getesteten Zeiträume.

Damit bestätigt die Profil-Robustheitsmatrix `balanced_v1` vorläufig als sinnvollsten Hauptkandidaten.

### Vorläufige Entscheidung

Auf Basis der 3x3-Robustheitsmatrix bleibt:

> `balanced_v1` der bevorzugte Hauptkandidat für die weitere Analyse.

`offensive_v1` bleibt als renditeorientierte Alternative interessant, sollte aber wegen höherem Drawdown und höherer Volatilität nicht vorschnell als Hauptprofil übernommen werden.

`conservative_v1` erfüllt seine defensive Rolle, wirkt aber im Verhältnis zum Renditeverzicht aktuell weniger attraktiv.

### Nächster Schritt

Nach der erfolgreichen Profil-Robustheitsmatrix sollte als nächstes nicht sofort optimiert werden.

Sinnvoller nächster Schritt:

> Marktphasen gezielt definieren und prüfen, ob `balanced_v1` auch in unterschiedlichen Marktumfeldern stabil bleibt.

Damit folgt als nächster Abschnitt:

`04.50 – Marktphasen-Test planen`


## 04.50 – Marktphasen-Test planen

Nach der erfolgreichen Profil-Robustheitsmatrix bleibt `balanced_v1` der aktuelle Hauptkandidat. Die Matrix über `short`, `medium` und `long` hat gezeigt, dass `balanced_v1` über mehrere Standardzeiträume einen guten Kompromiss aus Rendite, Risiko und Turnover liefert.

Als nächster Schritt soll geprüft werden, ob dieses Verhalten auch in gezielten Marktphasen stabil bleibt.

Ziel des Marktphasen-Tests ist es, die Profile nicht nur über allgemeine Zeiträume zu prüfen, sondern gezielt in unterschiedlichen Marktumfeldern:

| Phase                       | Zweck                                            |
| --------------------------- | ------------------------------------------------ |
| Bärenmarkt / Zinsphase 2022 | Verhalten in längerem Stressumfeld prüfen        |
| Erholung 2023               | Teilnahme an Erholungs- und Momentumphase prüfen |
| jüngere Phase 2024/2025     | aktuelle Marktnähe prüfen                        |

Die Marktphasen sollen nicht als neue technische Profile wie `short`, `medium` oder `long` modelliert werden. Diese Profile bleiben technische Lauf-/Validierungsprofile. Marktphasen sollen dagegen als fachliche Analysefenster behandelt werden.

---

## 04.55 – Technische Machbarkeit Marktphasen

Die technische Prüfung hat ergeben, dass `short`, `medium` und `long` keine TOML-Profile sind, sondern in `scripts/run_bt_run_agent.py` als Python-Logik über `ProfileBehavior` definiert werden.

Diese Profile steuern unter anderem:

* `compare_mode`
* `runner_extra_args`
* `backtest_lookback_months`
* `compare_point_count`
* Beschreibung des Laufverhaltens

Die zentrale Erkenntnis war:

> `short`, `medium` und `long` sind technische Lauf-/Validierungsprofile und sollten nicht mit fachlichen Marktphasen vermischt werden.

Der darunterliegende Backtest unterstützt bereits `--start` und `--end`. Der Runner unterstützt `--as-of` und `--period`. Der zentrale Wrapper `scripts.run_bt_run_agent` unterstützte zu diesem Zeitpunkt jedoch noch keine freien Zeitfenster.

Bewertete Varianten:

| Variante                            | Bewertung                                        |
| ----------------------------------- | ------------------------------------------------ |
| neue Zeitraumprofile                | technisch möglich, aber konzeptionell unsauber   |
| freie CLI-Parameter                 | sinnvoll als technische Basis                    |
| separates Marktphasen-Matrix-Skript | sauberste Zielarchitektur                        |
| Segmentanalyse aus Long-Runs        | nützlich als Ergänzung, aber nicht als Hauptpfad |

Entscheidung:

> Zuerst soll der zentrale Einstieg `scripts.run_bt_run_agent` saubere Zeitfenster-Overrides erhalten. Danach kann ein separates Marktphasen-Matrix-Skript gebaut werden.

---

## 04.60 – Zeitfenster-Overrides im zentralen Agent-Einstieg

Der zentrale Einstieg `scripts.run_bt_run_agent` wurde um freie Zeitfenster-Parameter erweitert:

[CODE_START]
--start YYYY-MM-DD
--end YYYY-MM-DD
--phase-name NAME
[CODE_END]

Semantik:

| Parameter      | Bedeutung                                          |
| -------------- | -------------------------------------------------- |
| `--start`      | expliziter Backtest-Start                          |
| `--end`        | explizites Backtest-Ende                           |
| `--phase-name` | fachlicher Name des Analysefensters, nur Metadaten |

Das Manifest wurde erweitert um:

[CODE_START]
phase_name
phase_start
phase_end
effective_backtest_start
effective_backtest_end
[CODE_END]

Tests:

[CODE_START]
42 passed
[CODE_END]

Ruff:

[CODE_START]
All checks passed
[CODE_END]

Es wurden keine Strategie-, Scoring-, Ranking-, Rebalance-, Finalisierungs- oder Compare-Logiken geändert.

---

## 04.66 – Diagnose erster Marktphasen-Kontrolllauf

Ein erster echter Kontrolllauf wurde für die Marktphase `bear_market_2022` gestartet:

[CODE_START]
python -m scripts.run_bt_run_agent 
--profile medium 
--strategy-profile balanced_v1 
--start 2022-01-01 
--end 2022-12-31 
--phase-name bear_market_2022
[CODE_END]

Der Lauf zeigte:

* `--start` und `--end` wurden korrekt an den Backtest durchgereicht.
* Das Manifest enthielt die neuen Phasenfelder korrekt.
* Der Backtest erzeugte jedoch keine Equity-Curve.
* Es entstanden keine `BT_*.json` im run-spezifischen Decisions-Ordner.
* Der Agent fiel anschließend auf ein Config-`as_of` aus 2025 zurück.

Die Ursache war:

> `--start` wirkte im Backtest als harter Datenstart. Für 2022 fehlte dadurch die notwendige Historie für `min_history_days`, Scoring, Volatilität und Regime-/SMA-Logik.

Damit wurde klar, dass Marktphasen technisch einen getrennten Warmup-Zeitraum benötigen.

---

## 04.67 – Fail-fast bei expliziten Zeitfenstern ohne BT-Bundles

Zur Absicherung wurde ein Fail-fast-Guard ergänzt.

Wenn ein explizites Zeitfenster aktiv ist und nach erfolgreichem Backtest keine gültigen `BT_*.json` im run-spezifischen Decisions-Ordner existieren, gilt jetzt:

* Runner wird nicht gestartet.
* Compare wird nicht gestartet.
* Kein Fallback auf Config-`as_of`.
* Kein Seeding aus alten/globalen Positionsdateien.
* Der Run wird als `success=false` markiert.
* Das Manifest enthält eine klare Warning.

Beispielmeldung:

[CODE_START]
No BT decision bundles produced for explicit time window 2022-01-01..2022-12-31 (bear_market_2022); runner skipped to avoid stale/config as_of fallback.
[CODE_END]

Tests:

[CODE_START]
45 passed
[CODE_END]

Ruff:

[CODE_START]
All checks passed
[CODE_END]

Es wurde keine Strategie-, Backtest-, Runner- oder Compare-Logik geändert. Der Fix betrifft nur die Agent-Orchestrierung.

---

## 04.68 – Warmup-Start / Phase-Start Konzept

Die Analyse ergab, dass Marktphasen drei Datumsbegriffe benötigen:

| Begriff        | Bedeutung                                                |
| -------------- | -------------------------------------------------------- |
| `warmup_start` | Datenstart für Historie, Indikatoren, Scoring und Regime |
| `phase_start`  | fachlicher Start der Marktphase                          |
| `phase_end`    | fachliches Ende der Marktphase                           |

Beispiel für 2022:

[CODE_START]
warmup_start = 2020-07-01
phase_start  = 2022-01-01
phase_end    = 2022-12-31
[CODE_END]

Der Backtest soll Daten ab `warmup_start` laden. Runner und Compare sollen aber nur auf BT-as_ofs innerhalb `phase_start..phase_end` laufen.

Entscheidung:

> Der Backtest-Code muss zunächst nicht geändert werden. Die Trennung kann im Wrapper/Agent erfolgen.

---

## 04.69 – Warmup-Start und Phasen-Compare-Punkte

`scripts.run_bt_run_agent` wurde um den neuen optionalen Parameter ergänzt:

[CODE_START]
--warmup-start YYYY-MM-DD
[CODE_END]

Neue Semantik:

| Parameter        | Bedeutung                                |
| ---------------- | ---------------------------------------- |
| `--warmup-start` | effektiver Backtest-Datenstart           |
| `--start`        | fachlicher `phase_start`                 |
| `--end`          | fachlicher `phase_end` und Backtest-Ende |
| `--phase-name`   | fachliche Metadaten                      |

Wenn `--warmup-start` gesetzt ist, wird dieser Wert an den Backtest als `--start` durchgereicht. Das bisherige `--start` bleibt als `phase_start` im Manifest erhalten.

Der Agent filtert die BT-as_ofs jetzt auf:

[CODE_START]
phase_start <= as_of <= phase_end
[CODE_END]

Erst danach wird `compare_point_count` angewendet. Der Runner wird nur für diese gefilterten Phasenpunkte gestartet. BT-Bundles aus der Warmup-Zeit erhalten kein RUN-Pendant und werden nicht verglichen.

Tests:

[CODE_START]
48 passed
[CODE_END]

Ruff:

[CODE_START]
All checks passed
[CODE_END]

Ein echter Kontrolllauf für `bear_market_2022` war erfolgreich:

[CODE_START]
python -m scripts.run_bt_run_agent 
--profile medium 
--strategy-profile balanced_v1 
--warmup-start 2020-07-01 
--start 2022-01-01 
--end 2022-12-31 
--phase-name bear_market_2022
[CODE_END]

Ergebnis:

[CODE_START]
success = true
Runner compare points = 2022-10-31, 2022-11-30, 2022-12-30
compare.success = true
compare.matched = true
compare.message = 3 matched, 0 mismatched
[CODE_END]

Damit ist die technische Grundlage für Marktphasenläufe hergestellt.

---

## 04.70 – Marktphasen-Matrix vorbereiten

Nach erfolgreichem Einzelkontrolllauf kann nun eine Marktphasen-Matrix aufgebaut werden.

Ziel ist ein neues Orchestrator-Skript:

[CODE_START]
scripts/run_market_phase_matrix.py
[CODE_END]

Das Skript soll mehrere Marktphasen und Strategieprofile ausführen, indem es ausschließlich den bestehenden zentralen Einstieg nutzt:

[CODE_START]
python -m scripts.run_bt_run_agent 
--profile medium 
--strategy-profile <strategy_profile> 
--warmup-start <warmup_start> 
--start <phase_start> 
--end <phase_end> 
--phase-name <phase_name>
[CODE_END]

Vorgesehene Default-Phasen:

| Phase              | Warmup Start | Phase Start | Phase End  | Typ                    |
| ------------------ | ------------ | ----------- | ---------- | ---------------------- |
| `bear_market_2022` | 2020-07-01   | 2022-01-01  | 2022-12-31 | Bärenmarkt / Zinsphase |
| `recovery_2023`    | 2021-07-01   | 2023-01-01  | 2023-12-31 | Erholung / Momentum    |
| `recent_2024_2025` | 2022-07-01   | 2024-01-01  | 2025-10-08 | jüngere Marktphase     |

Vorgesehene Strategieprofile:

* `conservative_v1`
* `balanced_v1`
* `offensive_v1`

Für den ersten Marktphasenvergleich wird als technisches Laufprofil weiterhin `medium` verwendet.

Wichtiger Hinweis:

> Die aktuell aus den Backtest-Artefakten extrahierten Performance-Kennzahlen können bei Warmup-Läufen den Zeitraum ab Warmup enthalten. Phase-only Performance-Metriken sollen später separat berechnet werden, indem Equity- und Benchmark-Zeitreihen auf `phase_start..phase_end` segmentiert werden.

04.70 baut daher zunächst nur:

* Orchestrierung,
* Manifest-Sammlung,
* Compare-Status,
* Runner-Compare-Punkte,
* bestehende Snapshot-Kennzahlen,
* Markdown-/JSON-Report.

Die eigentliche Phase-only Performance-Auswertung folgt später.


## 04.71 – Ergebnis der Marktphasen-Matrix

Nach der Umsetzung von `scripts/run_market_phase_matrix.py` wurde die vollständige Marktphasen-Matrix ausgeführt.

Der Matrixlauf umfasst:

* 3 Marktphasen
* 3 Strategieprofile
* insgesamt 9 Läufe

Verwendetes technisches Laufprofil:

[CODE_START]
--profile medium
[CODE_END]

Verwendete Strategieprofile:

* `conservative_v1`
* `balanced_v1`
* `offensive_v1`

Verwendete Marktphasen:

| Phase              | Typ                    | Warmup Start | Phase Start |  Phase End |
| ------------------ | ---------------------- | -----------: | ----------: | ---------: |
| `bear_market_2022` | Bärenmarkt / Zinsphase |   2020-07-01 |  2022-01-01 | 2022-12-31 |
| `recovery_2023`    | Erholung / Momentum    |   2021-07-01 |  2023-01-01 | 2023-12-31 |
| `recent_2024_2025` | jüngere Marktphase     |   2022-07-01 |  2024-01-01 | 2025-10-08 |

### Technischer Status

Die Marktphasen-Matrix lief technisch vollständig erfolgreich.

| Kennzahl              | Ergebnis |
| --------------------- | -------: |
| Läufe gesamt          |        9 |
| Erfolgreiche Läufe    |        9 |
| Fehlgeschlagene Läufe |        0 |
| Compare-Mismatches    |        0 |

Alle Läufe wurden über den zentralen Einstieg ausgeführt:

[CODE_START]
python -m scripts.run_bt_run_agent 
--profile medium 
--strategy-profile <strategy_profile> 
--warmup-start <warmup_start> 
--start <phase_start> 
--end <phase_end> 
--phase-name <phase_name>
[CODE_END]

Damit wurde keine neue Backtest-, Runner- oder Compare-Logik eingeführt. Das Matrix-Skript übernimmt nur die Orchestrierung und sammelt anschließend Manifest-, Snapshot- und Reportdaten.

### Ausgeführte Matrix

| Phase              | Strategieprofil   | Success | Compare matched | Compare message         |
| ------------------ | ----------------- | ------: | --------------: | ----------------------- |
| `bear_market_2022` | `conservative_v1` |    true |            true | 3 matched, 0 mismatched |
| `bear_market_2022` | `balanced_v1`     |    true |            true | 3 matched, 0 mismatched |
| `bear_market_2022` | `offensive_v1`    |    true |            true | 3 matched, 0 mismatched |
| `recovery_2023`    | `conservative_v1` |    true |            true | 3 matched, 0 mismatched |
| `recovery_2023`    | `balanced_v1`     |    true |            true | 3 matched, 0 mismatched |
| `recovery_2023`    | `offensive_v1`    |    true |            true | 3 matched, 0 mismatched |
| `recent_2024_2025` | `conservative_v1` |    true |            true | 3 matched, 0 mismatched |
| `recent_2024_2025` | `balanced_v1`     |    true |            true | 3 matched, 0 mismatched |
| `recent_2024_2025` | `offensive_v1`    |    true |            true | 3 matched, 0 mismatched |

### Runner-Compare-Punkte

Die Runner-Compare-Punkte lagen jeweils korrekt innerhalb der definierten Marktphase.

| Phase              | Runner Compare Points              |
| ------------------ | ---------------------------------- |
| `bear_market_2022` | 2022-10-31, 2022-11-30, 2022-12-30 |
| `recovery_2023`    | 2023-10-31, 2023-11-30, 2023-12-29 |
| `recent_2024_2025` | 2025-08-29, 2025-09-30, 2025-10-07 |

Damit ist der frühere Fehler behoben, bei dem ein Phasenlauf ohne gültige BT-Bundles auf ein Config-`as_of` aus 2025 zurückfallen konnte.

Die Marktphasen-Orchestrierung funktioniert jetzt sauber:

* Warmup-Datenstart wird verwendet.
* BT-as_ofs werden auf die Phase gefiltert.
* Runner startet nur für Phasenpunkte.
* BT/RUN-Compare bleibt innerhalb der Phase matched.
* Keine alten/globalen Positionsdaten werden als Fallback verwendet.

### Hinweis zu den Kennzahlen

Die aktuell ausgewiesenen Performance-Kennzahlen stammen noch aus bestehenden Backtest-Summary-/Artefaktdaten.

Bei Warmup-Läufen können diese Kennzahlen den Zeitraum ab Warmup bzw. ab erstem gültigem Rebalancepunkt enthalten. Sie sind daher noch nicht zwingend reine Marktphasen-Kennzahlen.

Für die spätere fachliche Bewertung sollen Phase-only-Metriken ergänzt werden, indem Equity- und Benchmark-Zeitreihen auf `phase_start..phase_end` segmentiert werden.

Bis dahin gelten die aktuellen Kennzahlen als technisch hilfreiche Orientierung, aber nicht als finale Marktphasen-Performance.

---

### Vorläufige Lesart der bestehenden Kennzahlen

Trotz des genannten Vorbehalts zeigen die aktuellen Kennzahlen bereits eine interessante Tendenz.

#### Phase `bear_market_2022`

| Profil            | Total Return |    CAGR | Max Drawdown | Sharpe | Volatility | Turnover |
| ----------------- | -----------: | ------: | -----------: | -----: | ---------: | -------: |
| `conservative_v1` |      -9.10 % | -6.51 % |     -19.61 % |  -0.29 |    17.81 % |  13.33 % |
| `balanced_v1`     |       3.82 % |  2.68 % |     -19.37 % |   0.23 |    22.33 % |  10.00 % |
| `offensive_v1`    |       5.44 % |  3.81 % |     -19.20 % |   0.27 |    26.12 % |  20.00 % |

In der Stressphase 2022 fällt auf, dass `balanced_v1` deutlich besser abschneidet als `conservative_v1` und gleichzeitig den niedrigsten Turnover zeigt.

`offensive_v1` liefert die höchste Rendite, hat aber auch den höchsten Turnover und die höchste Volatilität.

Vorläufige Bewertung:

| Profil            | Einschätzung                                                |
| ----------------- | ----------------------------------------------------------- |
| `conservative_v1` | defensiv, aber in dieser Auswertung nicht überzeugend genug |
| `balanced_v1`     | guter Stressphasen-Kompromiss mit niedrigem Turnover        |
| `offensive_v1`    | renditestärker, aber deutlich aktiver und volatiler         |

#### Phase `recovery_2023`

| Profil            | Total Return |    CAGR | Max Drawdown | Sharpe | Volatility | Turnover |
| ----------------- | -----------: | ------: | -----------: | -----: | ---------: | -------: |
| `conservative_v1` |      13.27 % |  9.18 % |     -13.46 % |   0.64 |    15.80 % |  16.67 % |
| `balanced_v1`     |      23.64 % | 16.14 % |     -13.46 % |   0.99 |    16.55 % |  13.33 % |
| `offensive_v1`    |      37.78 % | 25.36 % |     -13.46 % |   1.12 |    22.35 % |  20.00 % |

In der Erholungsphase 2023 ist `offensive_v1` erwartungsgemäß am stärksten. `balanced_v1` zeigt aber erneut einen guten Mittelweg: deutlich höhere Rendite als `conservative_v1`, gleicher Max Drawdown und niedrigerer Turnover.

Vorläufige Bewertung:

| Profil            | Einschätzung                               |
| ----------------- | ------------------------------------------ |
| `conservative_v1` | stabil, aber renditeschwächer              |
| `balanced_v1`     | guter Kompromiss aus Rendite und Aktivität |
| `offensive_v1`    | profitiert am stärksten von der Erholung   |

#### Phase `recent_2024_2025`

| Profil            | Total Return |    CAGR | Max Drawdown | Sharpe | Volatility | Turnover |
| ----------------- | -----------: | ------: | -----------: | -----: | ---------: | -------: |
| `conservative_v1` |      50.72 % | 20.63 % |     -22.12 % |   0.87 |    25.36 % |  18.65 % |
| `balanced_v1`     |      71.31 % | 27.90 % |     -25.25 % |   1.07 |    26.31 % |  17.22 % |
| `offensive_v1`    |      79.05 % | 30.51 % |     -29.63 % |   1.10 |    27.89 % |  19.37 % |

In der jüngeren Phase 2024/2025 bleibt `balanced_v1` nah an `offensive_v1`, zeigt aber niedrigeren Drawdown und geringeren Turnover.

Vorläufige Bewertung:

| Profil            | Einschätzung                                        |
| ----------------- | --------------------------------------------------- |
| `conservative_v1` | deutlich defensiver, aber mit Renditeverzicht       |
| `balanced_v1`     | sehr attraktiver Kompromiss                         |
| `offensive_v1`    | höchste Rendite, aber höherer Drawdown und Turnover |

---

### Vorläufiges Gesamtfazit

Die Marktphasen-Matrix bestätigt technisch, dass die aktuelle Agent-/Runner-/Compare-Struktur auch für Marktphasenläufe funktioniert.

Fachlich bleibt `balanced_v1` weiterhin der bevorzugte Hauptkandidat.

| Profil            | Vorläufiger Gesamteindruck                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------------- |
| `conservative_v1` | erfüllt die defensive Rolle, wirkt aber in den bisherigen Ergebnissen teilweise zu renditeschwach |
| `balanced_v1`     | stabiler Kompromiss über Stress-, Erholungs- und jüngere Marktphase                               |
| `offensive_v1`    | renditestark, aber mit höherem Risiko, höherer Volatilität und meist höherem Turnover             |

Wichtig:

> Die finale fachliche Bewertung der Marktphasen sollte erst nach Phase-only-Metriken erfolgen.

### Nächster Schritt

Als nächster Schritt sollen Phase-only-Metriken geplant werden.

Ziel:

> Performance, Drawdown, Volatilität, Sharpe, Benchmark-Vergleich und ggf. Turnover sollen nur innerhalb der jeweiligen Marktphase berechnet werden.

Dazu sollen Equity- und Benchmark-Zeitreihen auf `phase_start..phase_end` geschnitten und innerhalb des Segments neu normalisiert werden.

Möglicher nächster Abschnitt:

`04.72 – Phase-only-Metriken planen`

## 04.74 – Phase-only-Auswertung der Marktphasen-Matrix

Nach der Ergänzung der Phase-only-Metriken wurde die Marktphasen-Matrix erneut ausgeführt.

Die Matrix umfasst weiterhin:

* 3 Marktphasen
* 3 Strategieprofile
* insgesamt 9 Läufe

Alle Läufe waren technisch erfolgreich.

| Kennzahl              | Ergebnis |
| --------------------- | -------: |
| Läufe gesamt          |        9 |
| Erfolgreiche Läufe    |        9 |
| Fehlgeschlagene Läufe |        0 |
| Compare-Mismatches    |        0 |

Alle Kombinationen lieferten:

[CODE_START]
3 matched, 0 mismatched
[CODE_END]

Damit ist die BT/RUN-Parität auch für die Marktphasen-Matrix mit Phase-only-Auswertung hergestellt.

---

### Bedeutung der Phase-only-Metriken

Die bisherigen Snapshot-/Full-Artifact-Metriken konnten Warmup-Anteile enthalten.

Die neuen Phase-only-Metriken werden dagegen aus Equity- und Benchmark-Zeitreihen berechnet, die auf das jeweilige Phasenfenster geschnitten werden:

[CODE_START]
phase_start <= date <= phase_end
[CODE_END]

Danach wird das Segment intern auf den Segmentstart normalisiert.

Dadurch wird die jeweilige Marktphase isolierter bewertet.

Zusätzlich wurden Outperformance-Felder ergänzt:

| Feld                             | Bedeutung                                                             |
| -------------------------------- | --------------------------------------------------------------------- |
| `outperformed_benchmark`         | Portfolio Total Return > Benchmark Total Return                       |
| `cagr_outperformed_benchmark`    | Portfolio CAGR > Benchmark CAGR                                       |
| `drawdown_better_than_benchmark` | Portfolio Max Drawdown ist weniger negativ als Benchmark Max Drawdown |

Turnover wird aus `trades.csv` innerhalb des Phasenfensters berechnet. Der erste Trade innerhalb der Phase kann aber noch aus Vorphasen-Holdings resultieren.

---

## Phase `bear_market_2022`

| Profil            | Portfolio Return | Benchmark Return | Relative Return | Outperformed | Portfolio Max DD | Benchmark Max DD | DD Better |  Sharpe | Turnover |
| ----------------- | ---------------: | ---------------: | --------------: | -----------: | ---------------: | ---------------: | --------: | ------: | -------: |
| `conservative_v1` |         -14.65 % |         -13.42 % |         -1.23 % |        false |         -15.50 % |         -17.10 % |      true | -1.1431 |  10.00 % |
| `balanced_v1`     |          -2.52 % |         -13.42 % |         10.90 % |         true |         -15.25 % |         -17.10 % |      true | -0.0188 |   5.00 % |
| `offensive_v1`    |          -1.21 % |         -13.42 % |         12.22 % |         true |         -19.16 % |         -17.10 % |     false |  0.0862 |  20.00 % |

### Bewertung `bear_market_2022`

In der Bärenmarktphase 2022 zeigt `balanced_v1` ein sehr gutes Verhältnis aus Renditeschutz, Benchmark-Outperformance und Drawdown-Kontrolle.

`conservative_v1` hatte zwar einen besseren Drawdown als die Benchmark, verlor aber mehr als die Benchmark und verfehlte damit das Ziel einer defensiven Outperformance.

`offensive_v1` erzielte die beste Rendite, hatte aber einen schlechteren Drawdown als die Benchmark und den höchsten Turnover.

Zwischenfazit:

| Profil            | Bewertung                                           |
| ----------------- | --------------------------------------------------- |
| `conservative_v1` | defensiver Drawdown, aber schwache relative Rendite |
| `balanced_v1`     | stärkster Kompromiss in der Stressphase             |
| `offensive_v1`    | renditestärker, aber risikoreicher                  |

Für 2022 ist `balanced_v1` aus Sicht von Risiko/Rendite besonders überzeugend.

---

## Phase `recovery_2023`

| Profil            | Portfolio Return | Benchmark Return | Relative Return | Outperformed | Portfolio Max DD | Benchmark Max DD | DD Better | Sharpe | Turnover |
| ----------------- | ---------------: | ---------------: | --------------: | -----------: | ---------------: | ---------------: | --------: | -----: | -------: |
| `conservative_v1` |          17.49 % |          21.23 % |         -3.74 % |        false |         -13.46 % |          -7.08 % |     false | 0.9662 |  20.00 % |
| `balanced_v1`     |          29.78 % |          21.23 % |          8.55 % |         true |         -13.46 % |          -7.08 % |     false | 1.4481 |  18.33 % |
| `offensive_v1`    |          33.23 % |          21.23 % |         12.00 % |         true |         -13.46 % |          -7.08 % |     false | 1.4267 |  20.00 % |

### Bewertung `recovery_2023`

In der Erholungsphase 2023 zeigt `offensive_v1` die höchste absolute und relative Rendite.

`balanced_v1` schlägt die Benchmark ebenfalls deutlich und erreicht sogar den höchsten Sharpe-Wert der drei Profile. Der Max Drawdown ist allerdings bei allen Profilen schlechter als bei der Benchmark.

`conservative_v1` bleibt in dieser Phase hinter der Benchmark zurück und erfüllt damit die Rolle als defensiver Schutz nur eingeschränkt.

Zwischenfazit:

| Profil            | Bewertung                                                                         |
| ----------------- | --------------------------------------------------------------------------------- |
| `conservative_v1` | zu renditeschwach in der Erholung                                                 |
| `balanced_v1`     | starke Outperformance mit bestem Sharpe                                           |
| `offensive_v1`    | höchste Rendite, aber nicht klar besser als balanced im Risiko/Rendite-Verhältnis |

Für 2023 bleibt `balanced_v1` sehr attraktiv, auch wenn `offensive_v1` bei der Rendite vorne liegt.

---

## Phase `recent_2024_2025`

| Profil            | Portfolio Return | Benchmark Return | Relative Return | Outperformed | Portfolio Max DD | Benchmark Max DD | DD Better | Sharpe | Turnover |
| ----------------- | ---------------: | ---------------: | --------------: | -----------: | ---------------: | ---------------: | --------: | -----: | -------: |
| `conservative_v1` |          68.03 % |          35.47 % |         32.57 % |         true |         -22.12 % |         -23.32 % |      true | 1.2649 |  18.28 % |
| `balanced_v1`     |          77.88 % |          35.47 % |         42.41 % |         true |         -25.25 % |         -23.32 % |     false | 1.3516 |  17.37 % |
| `offensive_v1`    |          85.98 % |          35.47 % |         50.51 % |         true |         -29.63 % |         -23.32 % |     false | 1.3653 |  19.19 % |

### Bewertung `recent_2024_2025`

In der jüngeren Marktphase schlagen alle drei Profile die Benchmark deutlich.

`offensive_v1` liefert die höchste Rendite und den höchsten Sharpe-Wert, hat aber auch den schlechtesten Max Drawdown.

`balanced_v1` liegt renditeseitig klar vor `conservative_v1` und relativ nah an `offensive_v1`. Gleichzeitig hat es weniger Drawdown und niedrigeren Turnover als `offensive_v1`.

`conservative_v1` ist defensiver und hat als einziges Profil einen besseren Drawdown als die Benchmark, verzichtet aber deutlich auf Rendite.

Zwischenfazit:

| Profil            | Bewertung                                               |
| ----------------- | ------------------------------------------------------- |
| `conservative_v1` | defensiv brauchbar, aber mit deutlichem Renditeverzicht |
| `balanced_v1`     | starker Kompromiss mit sehr guter Outperformance        |
| `offensive_v1`    | höchste Rendite, aber deutlich höherer Drawdown         |

Für 2024/2025 bleibt `balanced_v1` der robustere Hauptkandidat, während `offensive_v1` als risikoreichere Renditevariante interessant bleibt.

---

## Gesamtbewertung über alle Marktphasen

### Benchmark-Outperformance

| Profil            | 2022 | 2023 | 2024/2025 |
| ----------------- | ---: | ---: | --------: |
| `conservative_v1` | nein | nein |        ja |
| `balanced_v1`     |   ja |   ja |        ja |
| `offensive_v1`    |   ja |   ja |        ja |

`balanced_v1` schlägt die Benchmark in allen drei getesteten Marktphasen.

`offensive_v1` schlägt die Benchmark ebenfalls in allen drei Phasen, erkauft diese Stärke aber mit höheren Drawdowns.

`conservative_v1` schlägt die Benchmark nur in der jüngeren Phase 2024/2025.

### Drawdown im Vergleich zur Benchmark

| Profil            |       2022 |       2023 |  2024/2025 |
| ----------------- | ---------: | ---------: | ---------: |
| `conservative_v1` |     besser | schlechter |     besser |
| `balanced_v1`     |     besser | schlechter | schlechter |
| `offensive_v1`    | schlechter | schlechter | schlechter |

Beim Drawdown zeigt sich ein differenziertes Bild.

`balanced_v1` schützt in der Stressphase 2022 besser als die Benchmark, hat aber in den stärkeren Marktphasen 2023 und 2024/2025 höhere Drawdowns als die Benchmark.

`offensive_v1` hat in keiner der drei Phasen einen besseren Drawdown als die Benchmark.

`conservative_v1` zeigt in zwei von drei Phasen einen besseren Drawdown, liefert aber weniger zuverlässige Outperformance.

---

## Vorläufiges Fazit nach Phase-only-Metriken

Die Phase-only-Auswertung bestätigt `balanced_v1` als aktuellen Hauptkandidaten.

Wesentliche Gründe:

* Benchmark-Outperformance in allen drei getesteten Marktphasen.
* Sehr gute relative Rendite in 2022, 2023 und 2024/2025.
* Bessere Drawdown-Kontrolle als `offensive_v1`.
* In 2022 besserer Drawdown als die Benchmark.
* Geringerer Turnover als `offensive_v1` in allen drei Phasen.
* Deutlich bessere Rendite als `conservative_v1`.

`offensive_v1` bleibt als renditeorientierte Alternative interessant, zeigt aber klar höhere Drawdown-Risiken.

`conservative_v1` erfüllt teilweise die defensive Rolle, wirkt aber im Verhältnis zum Renditeverzicht aktuell weniger attraktiv.

### Entscheidung

`balanced_v1` bleibt der bevorzugte Hauptkandidat für die weitere Analyse.

---

## Offene Punkte

Trotz des positiven Ergebnisses sollten zwei Punkte weiter geprüft werden:

1. `balanced_v1` hat in 2023 und 2024/2025 einen schlechteren Max Drawdown als die Benchmark.
2. `offensive_v1` liefert häufig die höchste Rendite, aber mit klar höherem Drawdown.

Daraus ergibt sich als nächster sinnvoller Schritt:

> Keine sofortige Optimierung, sondern zunächst eine gezielte Risiko-/Drawdown-Analyse von `balanced_v1`.

Möglicher nächster Abschnitt:

`04.75 – Drawdown- und Risikoanalyse von balanced_v1 planen`

## 04.77 – Drawdown-Analyse von `balanced_v1`

Nach der Phase-only-Auswertung der Marktphasen-Matrix wurde für den aktuellen Hauptkandidaten `balanced_v1` eine separate Drawdown-Analyse umgesetzt.

Ziel war nicht, die Strategie zu optimieren, sondern die Drawdown-Seite besser zu verstehen.

### Umsetzung

Neu angelegt bzw. geändert:

* `scripts/drawdown_analysis.py`
* `scripts/run_drawdown_analysis.py`
* `tests/unit/scripts/test_drawdown_analysis.py`
* `tests/unit/scripts/test_run_drawdown_analysis.py`

Erzeugte Reports:

* `reports/strategy_analysis/drawdown_analysis/balanced_v1_drawdown_analysis.md`
* `reports/strategy_analysis/drawdown_analysis/balanced_v1_drawdown_analysis.json`

Die Analyse arbeitet ausschließlich lesend auf bestehenden Artefakten.

Es wurden keine Strategie-, Profil-, Scoring-, Ranking-, Rebalance-, Finalisierungs-, Backtest-, Runner-, Compare- oder Walk-forward-Logiken geändert.

### Methodik

Pro Marktphase wird die Portfolio-Equity auf das jeweilige Phasenfenster geschnitten:

[CODE_START]
phase_start <= date <= phase_end
[CODE_END]

Danach wird die Drawdown-Serie berechnet:

[CODE_START]
drawdown = equity / cummax(equity) - 1
[CODE_END]

Die Drawdowns werden in getrennte Episoden zerlegt. Dadurch werden nicht mehrere Tage derselben Episode mehrfach als eigene Top-Drawdowns gezählt.

Für jede Drawdown-Episode werden unter anderem ermittelt:

* Startdatum
* Tiefpunkt
* Recovery-Datum, falls vorhanden
* maximale Drawdown-Tiefe
* Dauer in Kalendertagen
* Dauer in Beobachtungen
* Benchmark-Drawdown im gleichen Fenster
* Benchmark-Drawdown am Portfolio-Tiefpunkt
* Drawdown-Differenz Portfolio vs. Benchmark

### Benchmark-Vergleich

Für den Benchmark wird explizit die erste Spalte mit Prefix `BM1_` verwendet, z. B.:

[CODE_START]
BM1_SXR8.DE
[CODE_END]

Die Spalte `equity` in der Benchmark-Datei wird nicht als Benchmark verwendet.

Für jedes Portfolio-Drawdown-Fenster werden berechnet:

* Benchmark-Drawdown am Portfolio-Tiefpunkt
* Benchmark-MaxDD im gleichen Fenster
* Differenz Portfolio-DD vs. Benchmark-DD

Da Drawdowns negativ sind, bedeutet:

| Wert                     | Bedeutung                       |
| ------------------------ | ------------------------------- |
| negativer DD-Unterschied | Portfolio war tiefer/schlechter |
| positiver DD-Unterschied | Portfolio war flacher/besser    |

### Positions-, Sektor- und Trade-Auswertung

Die Positions- und Sektorbetrachtung basiert auf Rebalance-Snapshots.

Wichtig:

> Die Analyse zeigt, welche Ticker und Sektoren während eines Drawdown-Fensters im Portfolio vertreten waren. Sie berechnet keine exakten Ticker-Drawdown-Beiträge.

Der Grund:

`positions.csv` enthält keine tägliche Positionshistorie und keine tägliche Ticker-Attribution.

Daher werden keine Aussagen dieser Art getroffen:

[CODE_START]
Ticker X verursachte Y Prozentpunkte Drawdown.
[CODE_END]

Zulässig sind dagegen Aussagen wie:

[CODE_START]
Ticker/Sektor X war während des Drawdown-Fensters häufig oder stark im Portfolio vertreten.
[CODE_END]

Trades werden innerhalb des Drawdown-Fensters aggregiert:

* Anzahl Trades
* Turnover-Summe
* durchschnittlicher Turnover
* Trade-Kosten
* rohe `enter`-/`exit`-Werte

### Verifikation

Die Umsetzung wurde erfolgreich geprüft.

| Prüfung             |          Ergebnis |
| ------------------- | ----------------: |
| Unit-Tests          |         28 passed |
| Ruff                | All checks passed |
| Echter Analyse-Lauf |       erfolgreich |
| Reports erzeugt     |                ja |

---

## Wichtigste Befunde für `balanced_v1`

### Übersicht der schlimmsten Drawdowns je Phase

| Phase              | Worst DD | Benchmark-MaxDD im selben Fenster | Differenz | Recovery        |
| ------------------ | -------: | --------------------------------: | --------: | --------------- |
| `bear_market_2022` | -15.25 % |                          -11.44 % |  -3.80 pp | 2022-04-08      |
| `recovery_2023`    | -13.46 % |                           -7.08 % |  -6.38 pp | 2023-12-19      |
| `recent_2024_2025` | -25.25 % |                          -23.32 % |  -1.93 pp | nicht recovered |

### Einordnung `bear_market_2022`

Im Bärenmarkt 2022 hatte `balanced_v1` im schlimmsten Drawdown-Fenster einen Drawdown von ca. `-15.25 %`.

Der Benchmark-MaxDD im gleichen Fenster lag bei ca. `-11.44 %`.

Damit war der Portfolio-Drawdown in diesem Fenster um ca. `-3.80 Prozentpunkte` schlechter als der Benchmark.

Wichtig ist aber:

* Der Drawdown wurde innerhalb der Phase wieder aufgeholt.
* Recovery-Datum: `2022-04-08`
* In der gesamten Phase hatte `balanced_v1` dennoch eine deutliche Rendite-Outperformance gegenüber der Benchmark.

Bewertung:

`balanced_v1` zeigte 2022 eine gute Gesamtrisikostruktur, aber einzelne Drawdown-Episoden konnten tiefer ausfallen als beim Benchmark.

### Einordnung `recovery_2023`

In der Erholungsphase 2023 lag der Worst Drawdown von `balanced_v1` bei ca. `-13.46 %`.

Der Benchmark-MaxDD im gleichen Fenster lag nur bei ca. `-7.08 %`.

Damit war der Portfolio-Drawdown um ca. `-6.38 Prozentpunkte` schlechter als der Benchmark.

Recovery-Datum:

[CODE_START]
2023-12-19
[CODE_END]

Bewertung:

Diese Phase ist fachlich besonders relevant.

`balanced_v1` lieferte zwar eine starke Rendite-Outperformance, hatte aber in der Zwischenbewegung einen deutlich schlechteren Drawdown als der Benchmark.

Das spricht nicht gegen das Profil, zeigt aber:

> Die Strategie kann in Erholungsphasen zwischenzeitlich stärker zurückfallen als der Index.

### Einordnung `recent_2024_2025`

In der jüngeren Marktphase 2024/2025 lag der Worst Drawdown bei ca. `-25.25 %`.

Der Benchmark-MaxDD im gleichen Fenster lag bei ca. `-23.32 %`.

Damit war der Portfolio-Drawdown um ca. `-1.93 Prozentpunkte` schlechter als der Benchmark.

Wichtig:

* Der Drawdown war der tiefste der drei untersuchten Phasen.
* Im betrachteten Phasenfenster wurde keine vollständige Recovery erreicht.

Bewertung:

`recent_2024_2025` ist aus Risikosicht die kritischste Phase.

Der Abstand zur Benchmark ist zwar geringer als in 2023, aber der absolute Drawdown ist deutlich höher und im betrachteten Fenster noch nicht aufgeholt.

---

## Fachliches Gesamtfazit

`balanced_v1` bleibt weiterhin der bevorzugte Hauptkandidat.

Die Drawdown-Analyse zeigt aber klarer:

> Die Stärke von `balanced_v1` liegt in der Rendite- und Benchmark-Outperformance. Die Schwäche liegt in zeitweise tieferen Drawdowns als die Benchmark.

Das Profil ist also nicht deshalb riskant, weil es dauerhaft schlechter läuft, sondern weil es innerhalb erfolgreicher Phasen zwischenzeitlich deutlicher zurückfallen kann.

### Positive Punkte

* Benchmark-Outperformance in allen drei untersuchten Marktphasen.
* In 2022 trotz Stressphase gute relative Gesamtleistung.
* Drawdowns in 2022 und 2023 wurden wieder aufgeholt.
* Besseres Risiko/Rendite-Verhältnis als `offensive_v1`.
* Deutlich bessere Rendite als `conservative_v1`.

### Kritische Punkte

* Drawdown-Fenster können tiefer ausfallen als beim Benchmark.
* Besonders `recovery_2023` zeigt einen deutlichen Drawdown-Nachteil.
* `recent_2024_2025` zeigt den tiefsten Drawdown und keine Recovery im betrachteten Fenster.
* Exakte Ticker-Ursachen können mit den aktuellen Artefakten noch nicht berechnet werden.

---

## Konsequenz für die weitere Analyse

Aktuell ergibt sich daraus noch kein direkter Optimierungsauftrag.

Stattdessen sollten als nächstes zusätzliche Risikokennzahlen ergänzt oder ausgewertet werden, um besser beurteilen zu können, ob der Drawdown-Nachteil durch die Outperformance ausreichend kompensiert wird.

Sinnvolle nächste Kennzahlen:

* Calmar Ratio
* Ulcer Index
* Time under Water
* Recovery Duration
* Downside Capture vs. Benchmark
* Upside Capture vs. Benchmark
* Turnover during Drawdown vs. outside Drawdown
* Sektor-Exposure während Drawdown-Phasen

### Vorläufige Entscheidung

`balanced_v1` bleibt Hauptkandidat.

Eine Strategieänderung ist auf Basis der Drawdown-Analyse noch nicht zwingend angezeigt.

Vor einer Optimierung sollte zuerst entschieden werden, ob der zusätzliche Drawdown gegenüber der Benchmark im Verhältnis zur erzielten Outperformance akzeptabel ist.

Möglicher nächster Abschnitt:

`04.78 – Erweiterte Risiko-Kennzahlen für balanced_v1 planen`


## 04.80 – Risk-Metrics-Ergebnis für `balanced_v1`

Nach der Drawdown-Analyse wurde für den aktuellen Hauptkandidaten `balanced_v1` ein separater Risk-Metrics-Report umgesetzt.

Ziel war es, nicht nur die Drawdown-Episoden zu betrachten, sondern besser zu bewerten:

> Ist der zeitweise höhere Drawdown von `balanced_v1` gegenüber der Benchmark durch die erzielte Outperformance ausreichend gerechtfertigt?

### Umsetzung

Neu angelegt:

* `scripts/risk_metrics.py`
* `scripts/run_risk_metrics.py`
* `tests/unit/scripts/test_risk_metrics.py`
* `tests/unit/scripts/test_run_risk_metrics.py`

Erzeugte Reports:

* `reports/strategy_analysis/risk_metrics/balanced_v1_risk_metrics.md`
* `reports/strategy_analysis/risk_metrics/balanced_v1_risk_metrics.json`

Die Analyse arbeitet ausschließlich lesend auf bestehenden Artefakten.

Es wurden keine Strategie-, Profil-, Scoring-, Ranking-, Rebalance-, Finalisierungs-, Backtest-, Runner-, Compare- oder Walk-forward-Logiken geändert.

### Methodik

Die Berechnung liest:

* `market_phase_matrix_summary.json`
* die zugehörigen `run_manifest.json`-Dateien
* Equity-Artefakte
* Benchmark-Artefakte
* Trades-Artefakte

Portfolio und Benchmark werden pro Phase auf das jeweilige Phasenfenster geschnitten, per Inner Join auf gemeinsame Datumswerte ausgerichtet und intern auf Startwert `1.0` normalisiert.

Für den Benchmark wird explizit die erste Spalte mit Prefix `BM1_` verwendet.

Die Spalte `equity` in der Benchmark-Datei wird nicht als Benchmark verwendet.

### Enthaltene Kennzahlen

Der Risk-Metrics-Report enthält unter anderem:

| Kennzahl                       | Bedeutung                                      |
| ------------------------------ | ---------------------------------------------- |
| Calmar Ratio                   | CAGR im Verhältnis zum maximalen Drawdown      |
| Ulcer Index                    | Tiefe und Dauer von Drawdowns                  |
| Pain Index                     | durchschnittlicher absoluter Drawdown          |
| Time under Water               | Anteil der Zeit unter dem letzten Hoch         |
| Downside Capture               | Mitfallen an Benchmark-Verlusttagen            |
| Upside Capture                 | Mitsteigen an Benchmark-Gewinntagen            |
| Downside Volatility            | annualisierte negative Volatilität             |
| Sortino Ratio                  | Rendite im Verhältnis zur Downside-Volatilität |
| Drawdown Duration Distribution | Verteilung von Drawdown-Dauer und -Tiefe       |
| Turnover Stress Check          | Turnover während/außerhalb von Drawdowns       |

Der Turnover-Stress-Check ist eingeschränkt zu interpretieren, da nur monatliche Trade-Zeilen verfügbar sind.

Hinweis im Report:

[CODE_START]
monthly trade rows only; turnover timing is approximate
[CODE_END]

### Verifikation

| Prüfung             |          Ergebnis |
| ------------------- | ----------------: |
| Unit-Tests          |         41 passed |
| Ruff                | All checks passed |
| Echter Analyse-Lauf |       erfolgreich |
| Reports erzeugt     |                ja |

---

## Wichtigste Befunde

### Phase `bear_market_2022`

| Kennzahl     | Portfolio | Benchmark | Bewertung                 |
| ------------ | --------: | --------: | ------------------------- |
| CAGR         |   -2.55 % |  -13.57 % | Portfolio deutlich besser |
| Max Drawdown |  -15.25 % |  -17.10 % | Portfolio besser          |
| Ulcer/Pain   | niedriger |     höher | Portfolio besser          |

### Einordnung

In der Stressphase 2022 zeigt `balanced_v1` ein starkes Ergebnis.

Das Profil verliert deutlich weniger als die Benchmark und weist gleichzeitig bessere Drawdown-Kennzahlen auf.

Bewertung:

> `bear_market_2022` ist eine überzeugende Phase für `balanced_v1`.

---

### Phase `recovery_2023`

| Kennzahl     |  Portfolio | Benchmark | Bewertung               |
| ------------ | ---------: | --------: | ----------------------- |
| CAGR         |    30.28 % |   21.57 % | Portfolio besser        |
| Max Drawdown | schlechter |    besser | Portfolio risikoreicher |
| Ulcer/Pain   |      höher | niedriger | Portfolio risikoreicher |

### Einordnung

In der Erholungsphase 2023 liefert `balanced_v1` eine deutliche Rendite-Outperformance.

Gleichzeitig sind Max Drawdown, Ulcer Index und Pain Index schlechter als bei der Benchmark.

Bewertung:

> `balanced_v1` erzeugt 2023 höhere Rendite, aber mit mehr zwischenzeitlichem Stress.

Diese Phase bleibt aus Risikosicht besonders relevant.

---

### Phase `recent_2024_2025`

| Kennzahl       |  Portfolio |  Benchmark | Bewertung                      |
| -------------- | ---------: | ---------: | ------------------------------ |
| CAGR           |    38.63 % |    18.79 % | Portfolio deutlich besser      |
| Calmar/Sortino |     besser | schlechter | Portfolio effizienter          |
| Max Drawdown   | schlechter |     besser | Portfolio tiefer               |
| Ulcer/Pain     |      höher |  niedriger | Portfolio stärker unter Wasser |

### Einordnung

In der jüngeren Marktphase 2024/2025 ist die Outperformance von `balanced_v1` sehr deutlich.

Gleichzeitig sind Max Drawdown, Ulcer Index und Pain Index schlechter als bei der Benchmark.

Interessant ist aber, dass Calmar und Sortino trotz schlechterem Drawdown besser ausfallen.

Bewertung:

> `balanced_v1` ist in 2024/2025 rendite- und risikoadjustiert stark, aber emotional bzw. drawdownseitig unruhiger als die Benchmark.

---

## Capture-Ratios

Ein besonders wichtiger Befund:

> Downside Capture liegt in allen Phasen unter `1.0`.
> Upside Capture liegt ebenfalls in allen Phasen unter `1.0`.

### Interpretation

`balanced_v1` fällt an Benchmark-Verlusttagen weniger stark mit.

Gleichzeitig steigt `balanced_v1` an Benchmark-Gewinntagen aber auch weniger stark mit.

Das bedeutet:

> Die Outperformance kommt nicht einfach aus stärkerer Teilnahme an Benchmark-Up-Tagen oder höherem Markthebel.

Die Strategie scheint also nicht nur „mehr Risiko“ bzw. „mehr Beta“ zu nehmen, sondern erzeugt ihre Outperformance aus der Selektions- und Rebalancing-Logik.

Das ist ein wichtiger positiver Befund.

---

## Gesamtbewertung

`balanced_v1` bleibt weiterhin der bevorzugte Hauptkandidat.

### Positive Punkte

* Benchmark-Outperformance in allen untersuchten Marktphasen.
* In `bear_market_2022` auch risikoseitig besser als die Benchmark.
* In `recent_2024_2025` trotz höherem Drawdown bessere Calmar-/Sortino-Werte.
* Downside Capture in allen Phasen unter `1.0`.
* Outperformance wirkt nicht wie reines Benchmark-Beta.
* Besseres Risiko-/Rendite-Profil als `offensive_v1`.
* Deutlich attraktiver als `conservative_v1` als Hauptprofil.

### Kritische Punkte

* In `recovery_2023` schlechtere Drawdown-, Ulcer- und Pain-Werte als die Benchmark.
* In `recent_2024_2025` ebenfalls höhere Drawdown-Belastung als die Benchmark.
* Das Profil kann zwischenzeitlich deutlich stärker unter Wasser liegen als der Index.
* Der höhere Renditepfad ist nicht unbedingt komfortabler.

---

## Vorläufige Entscheidung

`balanced_v1` bleibt Hauptkandidat.

Eine direkte Strategieänderung ist weiterhin nicht zwingend angezeigt.

Die bisherigen Analysen sprechen eher für:

> `balanced_v1` ist leistungsfähig, aber drawdownseitig nicht immer komfortabel.

Vor einer Optimierung sollte deshalb ein bewusstes Entscheidungs-Gate stehen.

---

## Nächster sinnvoller Schritt

Als nächstes sollte entschieden werden, ob wir:

1. `balanced_v1` als Hauptprofil zunächst bestätigen und mit Walk-forward-/OOS-Checks weiter prüfen, oder
2. eine sehr vorsichtige Risiko-Feinjustierung testen, z. B. bei Sektorlimit, Turnover-Cap oder Risk-Off-Verhalten.

Empfohlene Reihenfolge:

> Erst Entscheidungs-Gate, dann ggf. gezielte Mini-Experimente.

Möglicher nächster Abschnitt:

`04.81 – Entscheidungs-Gate: balanced_v1 bestätigen oder Risiko-Feinjustierung prüfen`


## 04.81 – Entscheidungs-Gate: `balanced_v1` bestätigen oder Risiko-Feinjustierung prüfen

Nach Profil-Robustheit, Marktphasen-Matrix, Phase-only-Metriken, Drawdown-Analyse und erweitertem Risk-Metrics-Report liegt nun eine ausreichende Datenbasis für ein erstes Entscheidungs-Gate vor.

Ziel dieses Schritts ist nicht, neue Parameter zu optimieren, sondern bewusst festzulegen:

> Bleibt `balanced_v1` der Hauptkandidat, oder soll vor weiteren Tests bereits eine Risiko-Feinjustierung vorgenommen werden?

---

## Bisherige Befunde

### Technische Stabilität

Die technische Basis ist stabil:

* Backtester und Runner liefern in den geprüften Szenarien paritätische Ergebnisse.
* Marktphasen-Matrix läuft erfolgreich.
* Phase-only-Metriken sind verfügbar.
* Drawdown-Analyse ist verfügbar.
* Risk-Metrics-Report ist verfügbar.
* Alle bisherigen Analyseerweiterungen lesen bestehende Artefakte und verändern keine Strategie-/Backtest-/Runner-Logik.

### Fachliche Befunde zu `balanced_v1`

`balanced_v1` hat sich über mehrere Analyseebenen als stärkster Hauptkandidat bestätigt.

Positive Punkte:

* Benchmark-Outperformance in allen geprüften Marktphasen.
* In `bear_market_2022` auch risikoseitig überzeugend.
* In `recent_2024_2025` trotz höherem Drawdown bessere Calmar-/Sortino-Werte.
* Downside Capture in allen Phasen unter `1.0`.
* Outperformance wirkt nicht wie reines höheres Benchmark-Beta.
* Besseres Risiko-/Rendite-Profil als `offensive_v1`.
* Deutlich attraktiver als `conservative_v1` als Hauptprofil.

Kritische Punkte:

* In `recovery_2023` schlechtere Drawdown-, Ulcer- und Pain-Werte als die Benchmark.
* In `recent_2024_2025` ebenfalls höhere Drawdown-Belastung als die Benchmark.
* Das Profil kann zeitweise deutlich stärker unter Wasser liegen als der Index.
* Der Renditepfad ist nicht immer komfortabler, auch wenn die Gesamtrendite besser ist.

---

## Bewertung

Die bisherigen Analysen zeigen kein klares Signal, dass `balanced_v1` sofort verändert werden muss.

Die Drawdown-Schwäche ist real, aber aktuell nicht stark genug, um direkt Parameteränderungen zu rechtfertigen.

Eine sofortige Optimierung wäre riskant, weil sie zu Overfitting auf einzelne Drawdown-Phasen führen könnte, insbesondere auf:

* `recovery_2023`
* `recent_2024_2025`

Daher sollte nicht direkt an Parametern wie Sektorlimit, Turnover-Cap, Risk-Off-Verhalten oder Gewichtungslogik gedreht werden.

---

## Entscheidung

`balanced_v1` bleibt der bevorzugte Hauptkandidat.

Es erfolgt zunächst keine Strategieänderung.

Die nächste Prüfung soll nicht Optimierung, sondern Robustheitsvalidierung außerhalb der bisher ausgewerteten Perspektiven sein.

Entscheidung:

[CODE_START]
balanced_v1 bleibt Hauptprofil.
Keine sofortige Risiko-Feinjustierung.
Nächster Schritt: Walk-forward-/OOS-Planung.
[CODE_END]

---

## Begründung

Diese Entscheidung folgt aus drei Überlegungen:

1. `balanced_v1` liefert über alle geprüften Marktphasen eine klare Benchmark-Outperformance.
2. Die Risiko-Kennzahlen zeigen Schwächen, aber kein vollständiges Warnsignal gegen das Profil.
3. Eine Optimierung vor Walk-forward-/OOS-Prüfung würde das Risiko erhöhen, die Strategie auf bekannte historische Problemfenster zu überanpassen.

---

## Konsequenz

Der nächste Analyseblock soll prüfen, ob `balanced_v1` auch außerhalb der bisher stark betrachteten Analysefenster robust bleibt.

Dazu soll ein Walk-forward-/OOS-Konzept geplant werden.

Ziele:

* Robustheit auf zeitlich getrennten Abschnitten prüfen.
* Keine Parameter anhand der Testfenster optimieren.
* Profile nicht nur im Rückblick bewerten.
* Overfitting-Risiko reduzieren.
* Eine belastbarere Grundlage für spätere Mini-Experimente schaffen.

---

## Nächster Abschnitt

`04.82 – Walk-forward-/OOS-Prüfung planen`

## 04.84 – Walk-forward-/OOS-Ergebnis yearly für `balanced_v1`

Nach dem Entscheidungs-Gate wurde eine erste Walk-forward-/OOS-Prüfung für `balanced_v1` umgesetzt.

Ziel war es, `balanced_v1` nicht weiter zu optimieren, sondern in vorab definierten Jahres-OOS-Fenstern zu prüfen.

Die OOS-Ergebnisse sollen nicht zur nachträglichen Parameterwahl verwendet werden.

---

## Umsetzung

Neu angelegt:

* `scripts/run_walk_forward_matrix.py`
* `tests/unit/scripts/test_run_walk_forward_matrix.py`

Erzeugte Reports:

* `reports/strategy_analysis/walk_forward/walk_forward_summary.md`
* `reports/strategy_analysis/walk_forward/walk_forward_summary.json`

Das Walk-forward-Skript ruft pro Fenster ausschließlich den zentralen Einstieg auf:

[CODE_START]
python -m scripts.run_bt_run_agent 
--profile medium 
--strategy-profile balanced_v1 
--warmup-start <warmup_start> 
--start <oos_start> 
--end <oos_end> 
--phase-name <window_name>
[CODE_END]

Es werden keine Config-Dateien mutiert.

Es wurden keine Strategie-, Profil-, Scoring-, Ranking-, Rebalance-, Finalisierungs-, Backtest-, Runner-, Compare- oder bestehende Marktphasenlogiken geändert.

---

## Fensterlogik

Für 04.83 wurde bewusst `yearly` als erster Walk-forward-/OOS-Modus gewählt.

Rolling-6M wurde zurückgestellt, weil Halbjahresfenster für Risiko- und Drawdown-Kennzahlen stärker rauschanfällig sind.

Verwendete OOS-Fenster:

| Window         | Warmup Start |  OOS Start |    OOS End |
| -------------- | -----------: | ---------: | ---------: |
| `oos_2022`     |   2020-07-01 | 2022-01-01 | 2022-12-31 |
| `oos_2023`     |   2021-07-01 | 2023-01-01 | 2023-12-31 |
| `oos_2024`     |   2022-07-01 | 2024-01-01 | 2024-12-31 |
| `oos_2025_ytd` |   2023-01-01 | 2025-01-01 | 2025-10-08 |

---

## Technischer Status

Laut finalem Walk-forward-Report:

| Kennzahl             | Ergebnis |
| -------------------- | -------: |
| Runs total           |        4 |
| Runs successful      |        4 |
| Runs failed          |        0 |
| Compare mismatched   |        0 |
| Outperformed windows |        4 |

Alle vier OOS-Fenster lieferten:

[CODE_START]
3 matched, 0 mismatched
[CODE_END]

### Hinweis zu `profile medium`

Der Report weist korrekt darauf hin, dass `profile medium` nur die letzten 3 BT-as_of-Punkte technisch per Runner vergleicht.

Die OOS-Metriken selbst werden aber aus dem vollständigen Equity-/Benchmark-Segment des jeweiligen OOS-Fensters berechnet.

Damit gilt:

* BT/RUN-Parität wurde für die letzten 3 OOS-Rebalancepunkte geprüft.
* Die OOS-Performance-Metriken betrachten das gesamte OOS-Fenster.
* Es wird nicht behauptet, dass jeder einzelne monatliche OOS-Rebalancepunkt technisch verglichen wurde.

---

## OOS-Ergebnisse

| Window         | Portfolio Return | Benchmark Return | Relative Return | Outperformed | Portfolio MaxDD | Benchmark MaxDD | DD Better |  Sharpe | Turnover |
| -------------- | ---------------: | ---------------: | --------------: | -----------: | --------------: | --------------: | --------: | ------: | -------: |
| `oos_2022`     |          -2.52 % |         -13.42 % |         10.90 % |         true |        -15.25 % |        -17.10 % |      true | -0.0188 |   5.00 % |
| `oos_2023`     |          29.78 % |          21.23 % |          8.55 % |         true |        -13.46 % |         -7.08 % |     false |  1.4481 |  18.33 % |
| `oos_2024`     |          65.81 % |          33.66 % |         32.15 % |         true |        -14.29 % |         -8.27 % |     false |  1.8854 |  18.52 % |
| `oos_2025_ytd` |          10.58 % |           0.74 % |          9.84 % |         true |        -25.25 % |        -23.32 % |     false |  0.6691 |  16.00 % |

---

## Fachliche Bewertung

### Benchmark-Outperformance

`balanced_v1` schlägt die Benchmark in allen vier OOS-Fenstern.

| Window         | Relative Return |
| -------------- | --------------: |
| `oos_2022`     |         10.90 % |
| `oos_2023`     |          8.55 % |
| `oos_2024`     |         32.15 % |
| `oos_2025_ytd` |          9.84 % |

Der schwächste relative OOS-Wert ist:

[CODE_START]
oos_2023: +8.55 %
[CODE_END]

Damit bestätigt die yearly-OOS-Auswertung, dass die Outperformance von `balanced_v1` nicht nur aus einem einzelnen Marktphasenfenster stammt.

### Drawdown-Seite

Die bekannte Drawdown-Schwäche bleibt sichtbar.

| Window         | DD Better vs. Benchmark |
| -------------- | ----------------------: |
| `oos_2022`     |                    true |
| `oos_2023`     |                   false |
| `oos_2024`     |                   false |
| `oos_2025_ytd` |                   false |

`balanced_v1` hat also nur im Stressjahr 2022 einen besseren Max Drawdown als die Benchmark.

In 2023, 2024 und 2025 YTD ist der Portfolio-MaxDD schlechter als die Benchmark.

---

## Interpretation

Die OOS-Auswertung bestätigt das bisherige Profilbild:

### Stärken

* robuste Benchmark-Outperformance in allen OOS-Jahresfenstern
* kein isolierter Einmal-Effekt
* starke relative Rendite auch im schwächsten OOS-Fenster
* technische BT/RUN-Parität in allen geprüften OOS-Fenstern
* `balanced_v1` bleibt deutlich überzeugender als eine sofortige Risiko-Optimierung auf einzelne Drawdowns

### Schwächen

* Max Drawdown schlechter als Benchmark in 3 von 4 OOS-Fenstern
* Drawdown-Komfort bleibt die zentrale Schwäche
* `profile medium` prüft technisch nur 3 Runner-Compare-Punkte pro Fenster
* Risk-Metrics sind im Walk-forward-Report noch nicht integriert

---

## Unstimmigkeit im Codex-Fließtext

Im Codex-Fließtext wurde zwischendurch ein technischer Runner-Fehler für `oos_2024` erwähnt.

Der finale Report zeigt jedoch:

* `oos_2024` success = true
* compare matched = true
* compare message = `3 matched, 0 mismatched`

Für die Bewertung wird daher der finale Reportstand verwendet.

Diese Unstimmigkeit sollte lediglich als Hinweis dokumentiert werden, falls später Log-/Report-Abweichungen geprüft werden.

---

## Vorläufiges Fazit

Die Walk-forward-/OOS-Auswertung bestätigt `balanced_v1` deutlich als Hauptkandidat.

Die Strategie zeigt in allen geprüften OOS-Jahresfenstern Benchmark-Outperformance.

Die bekannte Drawdown-Schwäche bleibt bestehen, ist aber auf Basis der bisherigen Analysen kein Grund für eine sofortige Strategieänderung.

Entscheidung:

[CODE_START]
balanced_v1 bleibt Hauptprofil.
Keine unmittelbare Risiko-Feinjustierung.
Nächster Schritt: balanced_v1 als vorläufiges Produktions-/Runner-Hauptprofil markieren.
[CODE_END]

---

## Offene Folgepunkte

Sinnvolle nächste Schritte:

1. Risk-Metrics optional in Walk-forward-Reports integrieren.
2. Später Rolling-6M-OOS als zusätzliche Stabilitätsprüfung.
3. Später optional Profilvergleich in Walk-forward-Matrix als reine Stabilitätsanalyse.
4. Danach ggf. sehr vorsichtige Risiko-Mini-Experimente, aber erst nach expliziter Entscheidung.

Möglicher nächster Abschnitt:

`04.85 – balanced_v1 als vorläufiges Produktions-/Runner-Hauptprofil markieren`

## 04.85 – `balanced_v1` als vorläufiges Produktions-/Runner-Hauptprofil markieren

Nach Profil-Robustheit, Marktphasen-Matrix, Phase-only-Metriken, Drawdown-Analyse, Risk-Metrics und yearly Walk-forward-/OOS-Prüfung liegt eine ausreichende Entscheidungsbasis vor, um `balanced_v1` als vorläufiges Hauptprofil für die nächste Systemstufe zu markieren.

Ziel dieses Schritts ist keine produktive Investitionsfreigabe, sondern eine klare Projektentscheidung:

> `balanced_v1` ist der aktuelle Hauptkandidat für weitere Runner-/Produktionsvorbereitung.

---

## Grundlage der Entscheidung

Die Entscheidung basiert auf folgenden Analysebausteinen:

* Profil-Robustheitsmatrix
* Marktphasen-Matrix
* Phase-only-Metriken
* Drawdown-Analyse
* Risk-Metrics-Report
* Walk-forward-/OOS-Jahresfenster

Alle diese Schritte wurden durchgeführt, ohne Strategie-, Profil-, Scoring-, Ranking-, Rebalance-, Finalisierungs-, Backtest-, Runner- oder Compare-Logik zu verändern.

---

## Technischer Status

Die technische Basis ist stabil genug für die nächste Projektstufe.

Wichtige Punkte:

* Backtester/Runner-Parität ist in den geprüften Szenarien hergestellt.
* Decision-Bundles und Compare-Mechanik funktionieren.
* Marktphasenläufe funktionieren mit Warmup und OOS-/Phasenfenstern.
* Phase-only-Metriken werden aus Equity-/Benchmark-Segmenten berechnet.
* Drawdown- und Risk-Metrics-Reports lesen bestehende Artefakte.
* Walk-forward yearly wurde für `balanced_v1` erfolgreich ausgeführt.
* Keine Config-Mutation in den Analyse-Skripten.
* Analyse-Reports sind reproduzierbar erzeugbar.

---

## Fachlicher Status von `balanced_v1`

`balanced_v1` zeigt über die bisherigen Analysen das überzeugendste Gesamtbild.

### Stärken

* Benchmark-Outperformance in allen geprüften Marktphasen.
* Benchmark-Outperformance in allen yearly-OOS-Fenstern.
* Gute Leistung in der Stressphase `bear_market_2022`.
* Besseres Risiko-/Rendite-Profil als `offensive_v1`.
* Deutlich attraktiver als `conservative_v1` als Hauptprofil.
* Downside Capture in allen geprüften Phasen unter `1.0`.
* Outperformance wirkt nicht wie reines höheres Benchmark-Beta.
* Stabiler Kompromiss aus Rendite, Risiko und Turnover.

### Schwächen

* Max Drawdown ist in mehreren Phasen schlechter als die Benchmark.
* Ulcer-/Pain-Werte sind in 2023 und 2024/2025 schlechter als bei der Benchmark.
* Drawdown-Komfort bleibt die zentrale Schwäche.
* In `recent_2024_2025` wurde der größte Drawdown im Phasenfenster noch nicht recovered.
* `profile medium` prüft technisch nur die letzten 3 Runner-Compare-Punkte je Fenster.

---

## Entscheidung

`balanced_v1` wird als vorläufiges Produktions-/Runner-Hauptprofil markiert.

Diese Entscheidung bedeutet:

[CODE_START]
balanced_v1 ist der aktuelle Hauptkandidat.
Keine sofortige Risiko-Feinjustierung.
Keine Parameteränderung auf Basis einzelner Drawdown-Fenster.
Nächster Schritt: Runner-/Produktionsvorbereitung und Kontrollmechanismen.
[CODE_END]

---

## Keine sofortige Optimierung

Trotz der erkannten Drawdown-Schwächen wird aktuell keine Strategieänderung vorgenommen.

Begründung:

1. Die Outperformance ist über mehrere unabhängige Sichtweisen stabil.
2. Die Drawdown-Schwäche ist real, aber nicht stark genug für eine direkte Parameteränderung.
3. Eine Optimierung auf 2023 oder 2024/2025 könnte Overfitting erzeugen.
4. Die nächsten Schritte sollten Kontroll-, Reporting- und Runner-Sicherheit betreffen, nicht sofort neue Parameter.

---

## Bedeutung für die nächste Projektphase

Mit 04.85 endet die aktuelle Bewertungsrunde nicht vollständig, aber sie erreicht einen klaren Zwischenstand.

`balanced_v1` ist nun das Profil, mit dem die nächste Systemstufe vorbereitet werden kann.

Mögliche nächste Themen:

* Runner-Vorbereitung mit `balanced_v1`
* Produktions-/Paper-Run-Konzept
* Kontrollreport vor echter Nutzung
* Positions-/Order-Vorschlagsreport
* Sicherheitschecks vor Rebalance
* Logging und Auditierbarkeit
* Konfig-Snapshot pro Run
* manuelle Freigabe vor Orders
* klare Risiko-Hinweise im Report

---

## Vorläufiges Fazit

`balanced_v1` ist nicht perfekt, aber aktuell das überzeugendste Profil.

Die Strategie liefert robuste Outperformance, hat aber einen weniger komfortablen Drawdown-Pfad als die Benchmark.

Der nächste Schritt sollte deshalb nicht Optimierung sein, sondern:

> `balanced_v1` kontrolliert in Richtung Runner-/Produktionsvorbereitung bringen.

Möglicher nächster Projektabschnitt:

`05 – Produktionsprofil & Runner-Vorbereitung`

---

## 05.00 – Produktionsprofil & Paper-Runner-Vorbereitung

Ziel dieses Abschnitts ist die kontrollierte Überführung des vorläufigen Hauptprofils `balanced_v1` in einen Paper-Runner-Workflow.

Umsetzung:

* `balanced_v1` wird als Paper-Hauptkandidat geführt.
* `conservative_v1` bleibt defensiver Kontrollanker.
* `offensive_v1` bleibt Chancen-/Risiko-Gegenprobe.
* Die Vorbereitung fokussiert auf Reporting, Prüfbarkeit und Sicherheitsgrenzen.

Ergebnis:

* Es gibt weiterhin keine Investitionsfreigabe.
* Die Strategie-, Scoring-, Ranking-, Rebalance-, Finalisierungs- und Backtestlogik bleibt unverändert.
* Die nächste Systemstufe ist ein Paper-Workflow mit expliziter Human-Review-Pflicht.

Sicherheitsabgrenzung:

* Keine Broker-Anbindung.
* Kein Live-Trading.
* Keine echten Orders.
* Keine Stückzahl- oder Euro-Orderberechnung.
* Keine automatische Anlageentscheidung.

Relevante Artefakte:

* `scripts.run_bt_run_agent`
* `balanced_v1`
* `conservative_v1`
* `offensive_v1`

---

## 05.10 – Runner-Modus `analysis` / `paper`

Ziel war die saubere Trennung zwischen rückwärtskompatibler Analyse-Nutzung und explizitem Paper-Run.

Umsetzung:

* `--runner-mode paper` wurde eingeführt.
* `analysis` bleibt der rückwärtskompatible Default.
* Paper-Läufe erzeugen einen Vorschlagsreport, aber keine Ausführung.

Ergebnis:

* Bestehende Analyse-Aufrufe bleiben unverändert nutzbar.
* Paper-Runs sind explizit über den Runner-Modus erkennbar.
* Reports weisen klar aus, ob ein Lauf im Analyse- oder Paper-Modus erzeugt wurde.

Sicherheitsabgrenzung:

* `paper` bedeutet technische Simulation und Vorschlagsreport.
* `paper` bedeutet keine Orderanweisung und keine Ausführung.
* Es wurde keine Broker-, Order- oder Live-Trading-Logik ergänzt.

Relevante Artefakte:

* `--runner-mode analysis`
* `--runner-mode paper`
* `paper_run_report.json`
* `paper_run_report.txt`

---

## 05.20 – Paper-Run-Report fachlich stabilisiert

Ziel war ein fachlich verständlicher Report, der technische Runner-Informationen von fachlichen Warnungen trennt und die Nicht-Ausführung eindeutig dokumentiert.

Umsetzung:

* `paper_run_report.json` und `paper_run_report.txt` werden erzeugt.
* Reports enthalten klare No-Execution-/No-Broker-/No-Live-Trading-Hinweise.
* Eine Human-Review-Sektion ist vorhanden.
* Technische Runner-/Seeding-Informationen werden von fachlichen `warnings` getrennt.

Ergebnis:

* Der Paper-Report ist als Prüf- und Audit-Artefakt nutzbar.
* Fachliche Warnungen bleiben von technischen Laufdetails getrennt.
* Die manuelle Prüfung ist als Bestandteil des Workflows sichtbar.

Sicherheitsabgrenzung:

* `orders_executed` bleibt negativ.
* `broker_connected` bleibt negativ.
* `live_trading_enabled` bleibt negativ.
* `human_review_required` bleibt positiv.

Relevante Artefakte:

* `paper_run_report.json`
* `paper_run_report.txt`
* Report-Felder `technical_info`, `warnings`, `human_review_required`

---

## 05.30 – Lokale Ist-Depot-/Positionsdatei

Ziel war, Paper-Vorschläge gegen ein lokal gepflegtes Ist-Portfolio berechnen zu können.

Umsetzung:

* `--portfolio-file` wurde ergänzt.
* Unterstütztes CSV-Format: `symbol,weight`.
* Bei Nutzung einer Portfolio-Datei werden `previous_weight` und Deltas gegen diese lokale Datei berechnet.
* `portfolio_source` und `portfolio_file` werden im Report ausgewiesen.

Ergebnis:

* Buy/Sell/Hold-Proposals beziehen sich nicht nur auf Zielgewichte, sondern auf lokale Ist-Gewichte.
* Die Herkunft der Ist-Daten ist im Report nachvollziehbar.
* Die lokale Datei bleibt eine manuell gepflegte Datenquelle, keine Broker-Schnittstelle.

Sicherheitsabgrenzung:

* Die CSV ist kein Live-Depotabruf.
* Es findet keine Broker-Kommunikation statt.
* Die Datei erzeugt keine Orders.

Relevante Artefakte:

* `--portfolio-file`
* `examples/paper_portfolio_positions.csv`
* Report-Felder `portfolio_source`, `portfolio_file`, `previous_weight`

---

## 05.40 – Beispiel-Portfolio-Datei und echter Paper-Run

Ziel war ein nachvollziehbares Beispiel für einen Paper-Run mit lokaler Ist-Portfolio-Datei.

Umsetzung:

* Eine Beispiel-CSV liegt unter `examples/paper_portfolio_positions.csv`.
* Der Paper-Run kann mit `--runner-mode paper` und `--portfolio-file` gestartet werden.
* Die Zielpositionen werden gegen die lokalen Ist-Gewichte verglichen.

Beispielaufruf:

[CODE_START]
.venv\Scripts\python.exe -m scripts.run_bt_run_agent --profile short --strategy-profile balanced_v1 --runner-mode paper --portfolio-file examples/paper_portfolio_positions.csv
[CODE_END]

Ergebnis:

* Der Runner erzeugt Paper-Reports mit Zielgewichten, Ist-Gewichten und Proposal-Deltas.
* Buy/Sell/Hold dient als Vorschlagsklassifikation, nicht als Order.

Sicherheitsabgrenzung:

* Keine Stückzahlen.
* Keine Euro-Beträge.
* Keine Orderausführung.
* Keine Anlageberatung.

Relevante Artefakte:

* `examples/paper_portfolio_positions.csv`
* `paper_run_report.json`
* `paper_run_report.txt`

---

## 05.50 – Proposal-Toleranz und Report-Klarheit

Ziel war, minimale Rundungsdifferenzen nicht als künstliche Buy-/Sell-Signale auszuweisen.

Umsetzung:

* `PROPOSAL_DELTA_TOLERANCE = 0.00001` wurde eingeführt.
* Kleine Rundungsdeltas werden als `Hold` klassifiziert.
* `proposal_delta_tolerance` und `proposal_delta_basis` erscheinen in JSON und TXT.

Ergebnis:

* Proposal-Klassifikationen sind robuster gegen Rundungsrauschen.
* Die Toleranz ist im Report explizit dokumentiert.
* Die Delta-Basis ist fachlich nachvollziehbar.

Sicherheitsabgrenzung:

* Die Toleranz ändert keine Strategie-, Ranking- oder Rebalance-Logik.
* Sie betrifft nur die Klassifikation der Paper-Proposals im Report.
* Es wird weiterhin nichts ausgeführt.

Relevante Artefakte:

* `PROPOSAL_DELTA_TOLERANCE`
* Report-Felder `proposal_delta_tolerance`, `proposal_delta_basis`

---

## 05.60 – Kontroll-Paper-Run nach Proposal-Toleranz

Ziel war ein kontrollierter End-to-End-Lauf nach Einführung der Proposal-Toleranz.

Kontrolllauf:

* Run-ID: `20260618_203251`
* Run-Label: `2026-06-18_20-32-51_short_paper`
* `as_of`: `2025-10-08`
* `portfolio_source`: `portfolio_file`
* `proposal_delta_basis`: `local portfolio file`

Ergebnis der Proposal-Klassifikation:

* Buy: DASH, IVZ
* Sell: APTV, HUM
* Hold: CVS, EBAY, GE, NEM, PLTR, PSKY, WDC

Ergebnis:

* Rundungsdeltas wurden korrekt als `Hold` klassifiziert.
* Der Paper-Report weist lokale Ist-Daten, Delta-Basis und Sicherheitsgrenzen aus.
* `balanced_v1` bleibt Paper-Hauptkandidat; `conservative_v1` und `offensive_v1` bleiben Kontrollprofile.

Tests/Checks:

* Tests: `179 passed`
* Ruff für geänderte Dateien: clean

Sicherheitsabgrenzung:

* Keine Broker-Anbindung.
* Kein Live-Trading.
* Keine echten Orders.
* Keine Stückzahl- oder Euro-Orderberechnung.
* Keine Investitionsfreigabe.

05.70 – Paper-Workflow-Dokumentation

Die detaillierte Bedien- und Sicherheitsdokumentation des Paper-Runners wurde in einer separaten Datei abgelegt:

docs/paper_runner_workflow.md

Sie beschreibt Zweck, Ablauf, Portfolio-CSV, Beispielaufruf, Reportfelder, Buy/Sell/Hold-Logik, Proposal-Toleranz und Sicherheitsgrenzen.

## 05.90 – Phase-5-Zwischenabschluss

Phase 5 ist als Zwischenstand fachlich und technisch dokumentiert. Erreicht wurden:

* Paper-Runner-Modus über `--runner-mode paper`.
* Paper-Reports als `paper_run_report.json` und `paper_run_report.txt`.
* Human-Review-Sektion mit klarer manueller Prüfpflicht.
* Unterstützung einer lokalen Ist-Portfolio-Datei über `--portfolio-file` im CSV-Format `symbol,weight`.
* Optionaler `--portfolio-name` als reine Metadatenangabe für Report und Manifest.
* Proposal-Toleranz `proposal_delta_tolerance = 0.00001` zur Hold-Klassifikation kleiner Rundungsdeltas.
* Getrennte Ausgabe technischer Runner-/Seeding-Informationen und fachlicher Warnings.
* Kontrolllauf `20260618_203251` mit `as_of` `2025-10-08`, `portfolio_source` `portfolio_file`, Delta-Basis `local portfolio file` sowie Buy: DASH, IVZ; Sell: APTV, HUM; Hold: CVS, EBAY, GE, NEM, PLTR, PSKY, WDC.

Aktueller Nutzungszweck:

* Technische Simulation eines Strategieprofil-Laufs.
* Erzeugung eines Vorschlagsreports.
* Manuelle Prüfung der Buy/Sell/Hold-Proposals.
* Keine Ausführung und keine automatische Umsetzung.

Sicherheitsgrenzen:

* Keine Broker-Anbindung.
* Kein Live-Trading.
* Keine echten Orders.
* Keine Stückzahl- oder Euro-Orderberechnung.
* Keine Multi-Portfolio-Batch-Verarbeitung.
* Keine Personen-/Mandantenverwaltung.
* Keine Anlageberatung.
* Keine Investitionsfreigabe.

Bewusste Abgrenzung zu Phase 6:

Phase 6 kann später Portfolio-Organisation, mehrere lokale Portfolio-Dateien, Namenskonventionen, eine optionale Portfolio-Registry und weitere Paper-Betriebsorganisation behandeln.

Phase 5 wird nicht weiter in Richtung Multi-Portfolio-Architektur, Batch-Verarbeitung oder Personen-/Mandantenverwaltung ausgebaut.

Weiterführende Dokumentation:

* `docs/paper_runner_workflow.md`

Abschlusschecks:

* Letzter echter Kontrolllauf: `20260618_203251`.
* `pytest`: `179 passed`.
* Fokussierte Tests zuletzt: `42 passed`.
* Ruff für geänderte Python-Dateien: clean.

## 06.10 - Lokale Portfolio-Organisation

Mit 06.10 startet Phase 6 - Portfolio-Organisation.

Ziel ist eine einfache organisatorische Struktur fuer mehrere lokale Ist-Portfolios. Dafuer wird der Ordner `portfolios/` als Ablage fuer manuell gepflegte lokale Portfolio-CSV-Dateien eingefuehrt.

Die Portfolio-Dateien nutzen weiterhin das CSV-Format `symbol,weight`. `weight` wird als Dezimalgewicht interpretiert. Die Dateien bleiben lokale Ist-Portfolio-Eingaben fuer einzelne Paper-Runs.

Bewusste Abgrenzung:

* Keine Multi-Portfolio-Batch-Verarbeitung.
* Keine Broker-Anbindung.
* Keine Orderlogik.
* Keine Stueckzahl-Berechnung.
* Keine Euro-Berechnung.
* Keine Aenderung der bestehenden Paper-Runner-Logik.

Die bestehende Paper-Runner-Logik bleibt unveraendert. `--portfolio-file` zeigt weiterhin auf eine einzelne CSV-Datei. `--portfolio-name` bleibt eine optionale Bezeichnung fuer Reports.

## 06.20 - Portfolio-CSV-Validierung & Testabdeckung

Die bestehende `--portfolio-file`-Validierung wurde fuer lokale Portfolio-CSV-Dateien abgesichert.

Umsetzung:

* Die Validierungsregeln fuer `symbol,weight` wurden klarer dokumentiert.
* Tests fuer gueltige CSV-Dateien, Whitespace, Uppercase-Normalisierung, fehlende Spalten, leere Felder, ungueltige und negative Gewichte sowie doppelte Symbole wurden ergaenzt.
* Gewichte bleiben Dezimalgewichte und werden nicht normalisiert.
* Die Summe der Gewichte muss nicht `1.0` ergeben.
* Symbole ausserhalb des spaeteren Zielportfolios bleiben erlaubt.

Bewusste Abgrenzung:

* Keine Batch-Verarbeitung.
* Keine Broker-Anbindung.
* Kein Live-Trading.
* Keine Orderlogik.
* Keine Stueckzahl-Berechnung.
* Keine Euro-Berechnung.
* Keine Aenderung von Strategieauswahl, Scoring, Ranking, Rebalancing, Proposal-Klassifikation, Backtest-Logik, Runner-Berechnung, Decision-Bundle-Erzeugung oder Paper-Report-Fachlogik.

## 06.30 - Portfolio-Referenz & Report-Nachvollziehbarkeit

Paper-Reports weisen die verwendete Portfolio-Referenz klarer aus. Ziel ist, alte Paper-Runs auch spaeter auditierbar nachvollziehen zu koennen.

Ergaenzt wurden reine Metadatenfelder fuer die Portfolio-Referenz:

* `portfolio_source`
* `portfolio_name`
* `portfolio_file`
* `portfolio_file_name`
* `portfolio_file_display`
* `portfolio_file_resolved`

Die Felder erscheinen im Paper-JSON und im Paper-Bereich des Manifests. Der TXT-Report zeigt eine kurze Portfolio-Reference-Sektion und laesst Datei-Zeilen weg, wenn kein `--portfolio-file` gesetzt wurde.

Bewusste Abgrenzung:

* Keine Berechnungsaenderung.
* Keine Proposal-Aenderung.
* Keine Portfolio-Normalisierung.
* Keine Batch-Verarbeitung.
* Keine Broker-Anbindung.
* Kein Live-Trading.
* Keine Orderlogik.
* Keine Stueckzahl-Berechnung.
* Keine Euro-Berechnung.

## 06.40 - Portfolio-Plausibilitaetscheck im Paper-Report

Paper-Reports enthalten jetzt Portfolio Checks, wenn ein lokales Ist-Portfolio ueber `--portfolio-file` verwendet wird.

Ziel ist eine bessere manuelle Pruefung der Ist-Basis vor der Bewertung der Buy/Sell/Hold-Proposals. Der Report zeigt dafuer Anzahl der gelesenen Positionen, Gewichtssumme, Abweichung zu `1.0`, eine einfache Nahe-1.0-Plausibilitaet und eine kurze Symbolvorschau.

Die Gewichtssumme wird nur angezeigt. Sie wird nicht normalisiert und loest keinen automatischen Abbruch aus, wenn sie deutlich von `1.0` abweicht.

Bewusste Abgrenzung:

* Keine Proposal-Aenderung.
* Keine Aenderung der Proposal-Toleranz.
* Keine Aenderung von Deltas oder Portfolio-Gewichten.
* Keine Gewichtungsnormalisierung.
* Keine Batch-Verarbeitung.
* Keine Broker-Anbindung.
* Kein Live-Trading.
* Keine Orderlogik.
* Keine Stueckzahl-Berechnung.
* Keine Euro-Berechnung.

## 06.50 - Phase-6-Zwischenreview & Workflow-Konsolidierung

Phase 6 ist bis hierhin als organisatorische und dokumentarische Erweiterung des Paper-Workflows konsolidiert.

Zusammenfassung der bisherigen Phase-6-Schritte:

* 06.10: Der Ordner `portfolios/` dient als lokale Ablage fuer manuell gepflegte Ist-Portfolio-CSV-Dateien.
* 06.20: Die CSV-Validierung fuer `symbol,weight` wurde abgesichert und dokumentiert.
* 06.30: Paper-Reports weisen die verwendete Portfolio-Referenz auditierbar aus.
* 06.40: Paper-Reports enthalten Portfolio Checks zur manuellen Plausibilitaetspruefung der lokalen CSV-Datei.

Einordnung:

* Phase 6 verbessert Organisation, Nachvollziehbarkeit und manuelle Pruefung lokaler Ist-Portfolios.
* `--portfolio-file` verweist weiterhin auf genau eine lokale CSV-Datei pro Paper-Run.
* `--portfolio-name` bleibt reine Metadatenangabe fuer Report und Manifest.
* Human Review bleibt verpflichtend; die Portfolio Checks sind nur ein Pruefhinweis.
* Bestehende Proposal-, Runner-, Backtest- und Decision-Bundle-Logik bleibt unveraendert.

Bewusste Abgrenzung:

* Keine Broker-Anbindung.
* Kein Live-Trading.
* Keine echten Orders.
* Keine Stueckzahl- oder Euro-Berechnung.
* Keine Gewichtungsnormalisierung.
* Keine Multi-Portfolio-Batch-Verarbeitung.
* Keine Personen- oder Mandantenverwaltung.

## 06.60 - Kontrolllauf mit lokalem Beispielportfolio

Ziel war ein fokussierter Paper-Kontrolllauf mit dem lokalen Beispielportfolio aus `portfolios/`.
Der Lauf sollte pruefen, ob Portfolio Reference, Portfolio Checks, Paper-Reports und Manifest die lokale Portfolio-Organisation praktisch nachvollziehbar ausweisen.

Verwendeter Befehl:

[CODE_START]
.venv\Scripts\python.exe -m scripts.run_bt_run_agent --profile short --strategy-profile balanced_v1 --runner-mode paper --portfolio-file portfolios\example_local_portfolio.csv --portfolio-name example_local
[CODE_END]

Kontrolllauf:

* Run-ID: `20260621_224555`
* Run-Ordner: `D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents\automation_runs\2026-06-21_22-45-55_short_paper`
* `as_of`: `2025-10-08`
* Portfolio-Datei: `portfolios\example_local_portfolio.csv`
* Portfolio-Name: `example_local`
* `portfolio_source`: `portfolio_file`
* `portfolio_file_name`: `example_local_portfolio.csv`
* `portfolio_file_display`: `portfolios\example_local_portfolio.csv`

Portfolio Checks:

* `position_count`: `3`
* `total_weight`: `0.12`
* `total_weight_delta_to_1`: `-0.88`
* `weight_sum_is_near_1`: `false`
* `symbols_preview`: `DASH`, `IVZ`, `CVS`

Proposal-Zusammenfassung:

* Buy: CVS, DASH, EBAY, GE, IVZ, NEM, PLTR, PSKY, WDC
* Sell: keine
* Hold: keine

Bewertung:

* Der Paper-Kontrolllauf war technisch erfolgreich.
* Backtest, Runner und Compare waren erfolgreich; der Compare war matched.
* `paper_run_report.json`, `paper_run_report.txt` und `run_manifest.json` wurden erzeugt.
* JSON-Report und Manifest enthalten Portfolio Reference, Portfolio Checks, Paper-Artefakte und Sicherheitsfelder.
* Der TXT-Report enthaelt Portfolio Reference, Portfolio Checks, Human Review sowie No-Execution-/No-Broker-/No-Live-Trading-Hinweise.
* Die geringe Gewichtssumme des Beispielportfolios wird sichtbar gemacht, aber nicht normalisiert und nicht automatisch blockiert.

Sicherheitsabgrenzung:

* Keine Investitionsfreigabe.
* Keine Broker-Anbindung.
* Kein Live-Trading.
* Keine echten Orders.
* Keine Stueckzahl- oder Euro-Berechnung.
* Keine Gewichtungsnormalisierung.
* Keine Batch-Logik oder Multi-Portfolio-Verarbeitung.
* Keine Aenderung an Strategieauswahl, Scoring, Ranking, Rebalancing, Proposal-Klassifikation, Backtest-Logik, Runner-Berechnung, Decision-Bundle-Erzeugung oder Portfolio-Deltas.

## 06.90 - Phase-6-Abschluss

Phase 6 ist dokumentarisch abgeschlossen. Erreicht wurden:

* Lokale Portfolio-Struktur ueber den Ordner `portfolios/`.
* CSV-Validierung und Testabdeckung fuer lokale Portfolio-Dateien im Format `symbol,weight`.
* Portfolio-Referenz im Paper-Report und im Manifest.
* Portfolio Checks im Paper-Report zur manuellen Plausibilitaetspruefung.
* Workflow-Konsolidierung mit klarer Human-Review-Pflicht.
* Erfolgreicher Kontrolllauf `20260621_224555` mit lokalem Beispielportfolio `portfolios\example_local_portfolio.csv`.

Einordnung:

* Phase 6 verbessert Organisation, Nachvollziehbarkeit und manuelle Pruefung lokaler Ist-Portfolios.
* Die Paper-Runner-Basis ist dadurch besser auditierbar.
* Es wurde keine Handelsautomatisierung eingefuehrt.
* Es gibt weiterhin genau einen Paper-Run mit genau einer Portfolio-Datei.
* Mehrere lokale CSV-Dateien koennen organisatorisch existieren, werden aber nicht als Batch verarbeitet.
* Human Review bleibt verpflichtend; Portfolio Reference und Portfolio Checks sind Pruef- und Audit-Hilfen, keine Freigabe.

Sicherheitsgrenzen:

* Kein Broker.
* Kein Live-Trading.
* Keine echten Orders.
* Keine Stueckzahlberechnung.
* Keine Euro- oder Ordergroessenberechnung.
* Keine Gewichtungsnormalisierung.
* Keine Multi-Portfolio-Batch-Verarbeitung.
* Keine Personen- oder Mandantenverwaltung.

Bewusst nicht eingefuehrt:

* Keine Aenderung an Strategieauswahl, Scoring, Ranking oder Rebalancing.
* Keine Aenderung an Proposal-Klassifikation, Proposal-Toleranz oder Portfolio-Deltas.
* Keine Aenderung an Backtest-Logik, Runner-Berechnung oder Decision-Bundle-Erzeugung.
* Keine Portfolio-Normalisierung.
* Keine Broker-, Order- oder Live-Trading-Logik.

Ausblick:

Phase 7 kann den Paper-Betrieb ueber mehrere Laeufe beobachten. Sinnvolles Ziel waere, Verlauf, Stabilitaet und Report-Vergleich ueber wiederholte Paper-Runs auszuwerten, weiterhin ohne Broker, Live-Trading oder Orders.

## 07.10 Phase-7-Zielbild & Beobachtungslogik

Phase 7 startet nach dem Abschluss von Phase 6. Nach der lokalen Portfolio-Organisation, der Portfolio Reference und den Portfolio Checks liegt der naechste Schwerpunkt auf dem Paper-Betrieb ueber mehrere Laeufe hinweg.

Ziel von Phase 7 ist die Beobachtung mehrerer Paper-Runs ueber die Zeit. Jeder Paper-Run bleibt dabei ein eigenstaendiger Einzelrun. Es wird keine Batch-Verarbeitung eingefuehrt, und aus mehreren beobachteten Laeufen entsteht keine gemeinsame Ausfuehrungslogik.

Die Verlaufsauswertung soll spaeter sichtbar machen, wie sich Proposals zwischen einzelnen Paper-Runs veraendern. Im Zentrum steht weiterhin das Strategieprofil `balanced_v1`, weil dieses Profil als zentrale, zu beobachtende Paper-Konfiguration dient.

### Abgrenzung der Auswertungsebenen

Phase 7 soll klar zwischen drei Ebenen unterscheiden:

* **Einzelrun-Report:** beschreibt einen einzelnen Paper-Run mit seinen Eingaben, Portfolio-Hinweisen, Zielgewichten, Vergleichswerten und Proposals.
* **Verlaufs-/Vergleichsreport:** kann spaeter mehrere eigenstaendige Paper-Runs gegenueberstellen und Proposal-Aenderungen zwischen Laeufen sichtbar machen.
* **Human Review:** bewertet Auffaelligkeiten manuell. Diese Ebene bleibt die einzige Stelle fuer fachliche Einordnung; sie erzeugt keine automatische Freigabe.

Ein Proposal-Wechsel ist keine Handlungsempfehlung. Die Auswertung dient ausschliesslich der manuellen Pruefung und erzeugt keine Investitionsfreigabe.

### Beobachtete Informationen

Fuer einzelne Paper-Runs und spaetere Verlaufsvergleiche sollen insbesondere folgende Informationen beobachtet werden:

* Run-ID
* Run-Zeitpunkt
* Profil
* Strategieprofil, insbesondere `balanced_v1`
* `runner_mode` `paper`
* `as_of`
* Portfolio-Datei
* optionaler Portfolio-Name
* Portfolio Reference
* Portfolio Checks
* Zielgewichte
* Ist-/Vergleichsgewichte
* Buy/Sell/Hold-Proposals
* Proposal-Delta
* Proposal-Toleranz

Diese Informationen dienen der Nachvollziehbarkeit. Sie sind Pruef- und Vergleichsdaten, keine Orderdaten.

### Beobachtungslogik ueber mehrere Laeufe

Die Beobachtung soll zeigen, welche Proposal- und Gewichtungsveraenderungen zwischen Paper-Runs auftreten. Relevant sind insbesondere:

* neue Positionen
* weggefallene Positionen
* unveraenderte Positionen
* geaenderte Zielgewichte
* geaenderte Proposal-Klassen
* haeufig wechselnde Vorschlaege
* stabile Vorschlaege
* auffaellige Spruenge

Die Beobachtung ist zeitbezogen, aber nicht transaktionsbezogen. Mehrere Paper-Runs koennen verglichen werden, bleiben jedoch jeweils eigenstaendige Analyseartefakte.

### Sicherheitsgrenzen

Phase 7 bleibt vollstaendig innerhalb des Paper-Betriebs. Nicht Teil von Phase 7 sind:

* keine Broker-Anbindung
* kein Live-Trading
* keine echten Orders
* keine Stueckzahl- oder Euro-Berechnung
* keine Gewichtungsnormalisierung
* keine Personen- oder Mandantenverwaltung

Die Verlaufsauswertung kann spaeter Hinweise fuer eine manuelle Pruefung liefern. Sie ersetzt keine Human Review, gibt keine Investition frei und leitet keine Handlung automatisch ab.

## 07.20 Paper-Run-History: Datenquelle & Vergleichsmodell festlegen

Ziel dieses Abschnitts ist die fachliche Festlegung, welche bestehenden Paper-Run-Artefakte spaeter fuer eine Verlaufsauswertung verwendet werden koennen und welches Vergleichsmodell dafuer sinnvoll ist.

### Datenquelle

Grundlage fuer spaetere Verlaufsauswertungen sind bestehende Paper-Run-Artefakte. Hauptquelle ist `paper_run_report.json` aus einzelnen `automation_runs/...`-Run-Ordnern.

Jeder Run bleibt ein eigenstaendiger, bereits erzeugter Paper-Run. Es wird in diesem Schritt keine automatische Run-Erzeugung eingefuehrt und keine Logik ergaenzt, die mehrere Paper-Runs automatisch ausfuehrt.

### Vergleichbarkeit von Runs

Runs sind fachlich vor allem dann sinnvoll vergleichbar, wenn die wichtigsten Rahmenbedingungen uebereinstimmen oder bewusst als Vergleichsdimension gewaehlt wurden:

* gleicher `runner_mode = paper`
* gleiches oder bewusst ausgewaehltes Strategieprofil, insbesondere `balanced_v1`
* gleicher Profiltyp, zum Beispiel `short`, `medium` oder `long`
* nachvollziehbarer `as_of`-Zeitpunkt
* gleiche oder bewusst unterschiedliche Portfolio-Datei
* optional gleicher Portfolio-Name
* konsistente Proposal-Toleranz

Abweichungen sind nicht ausgeschlossen, muessen aber im Vergleich sichtbar bleiben. Ein Vergleich zwischen unterschiedlichen Profilen, Portfolio-Dateien oder `as_of`-Zeitpunkten kann fachlich sinnvoll sein, ist aber anders zu interpretieren als ein Vergleich unter konstanten Rahmenbedingungen.

### Relevante Metadaten pro Run

Fuer eine spaetere History-Auswertung sollen pro Paper-Run insbesondere folgende Metadaten betrachtet werden:

* Run-ID
* Run-Zeitpunkt beziehungsweise Run-Ordner
* Profil
* Strategieprofil
* `runner_mode`
* `as_of`
* Portfolio-Quelle
* Portfolio-Datei
* Portfolio-Dateiname
* Portfolio-Anzeigename beziehungsweise Display-Pfad
* optionaler Portfolio-Name
* Portfolio Checks
* Proposal-Toleranz
* Sicherheitsfelder
* Human-Review-Hinweise

Diese Metadaten dienen der Einordnung, ob zwei Runs direkt vergleichbar sind oder ob der Vergleich bewusst unterschiedliche Eingaben gegenueberstellt.

### Relevante Positionsdaten pro Symbol

Fuer jedes Symbol sollen spaeter insbesondere folgende Informationen vergleichbar sein:

* Symbol
* Zielgewicht
* Ist- beziehungsweise Vergleichsgewicht
* Delta zwischen Ziel und Ist/Vergleich
* Proposal-Klasse `Buy`, `Sell` oder `Hold`
* Delta-Basis
* gegebenenfalls Sortierung oder Rang, sofern im Artefakt vorhanden

Die Positionsdaten bleiben reine Vergleichsdaten. Sie fuehren nicht zu Stueckzahl-, Euro- oder Orderberechnungen.

### Vergleichsmodell zwischen Laeufen

Ein Vergleich zwischen zwei Paper-Runs soll spaeter sichtbar machen, welche strukturellen und fachlichen Unterschiede zwischen den Artefakten bestehen. Relevant sind insbesondere:

* Symbol neu im Zielportfolio
* Symbol aus Zielportfolio verschwunden
* Symbol in beiden Laeufen vorhanden
* Zielgewicht gestiegen
* Zielgewicht gefallen
* Zielgewicht unveraendert
* Proposal-Klasse gewechselt
* Delta groesser geworden
* Delta kleiner geworden
* stabile Position ueber mehrere Laeufe
* auffaelliger Sprung

Das Vergleichsmodell beschreibt Unterschiede zwischen Paper-Run-Artefakten. Es erzeugt keine Ausfuehrungslogik und fuehrt keine automatische Bewertung als gut oder schlecht durch.

### Keine fachliche Bewertung automatisieren

Ein Vergleich zeigt Unterschiede, bewertet sie aber nicht automatisch als gut oder schlecht. Proposal-Aenderungen sind Pruefsignale, keine Handlungsempfehlungen.

Aus einer History-Auswertung entsteht keine Investitionsfreigabe. Human Review bleibt zwingend und ist die einzige Ebene, auf der Auffaelligkeiten fachlich eingeordnet werden duerfen.

### Moegliche spaetere Artefakte

Als moegliches Zielbild fuer spaetere Schritte koennen zusaetzliche Artefakte entstehen, zum Beispiel:

* `paper_run_history.json`
* `paper_run_history.md` oder `.txt`
* Vergleich zweier Runs
* spaeter eventuell Verlauf ueber mehrere Runs

Diese Artefakte sind hier nur als Zielbild beschrieben. Sie werden in diesem Schritt nicht implementiert. Der Paper-Betrieb bleibt weiterhin ohne automatische Paper-Run-Ausfuehrung, ohne Batch-Verarbeitung, ohne Broker-Anbindung, ohne Live-Trading und ohne echte Orders.

## 07.30 Beobachtungsdauer & Belastbarkeit der Paper-Ergebnisse

Ziel dieses Abschnitts ist die fachliche Einordnung, wie lange Paper-Runs beobachtet werden sollten, bevor Ergebnisse als aussagekraeftiger gelten koennen.

### Grundsatz

Es kann nicht serioes garantiert werden, ab welchem Zeitpunkt `balanced_v1` besser als der passende Index oder die passende Benchmark sein wird.

Eine laengere Beobachtungsdauer kann nur helfen, die Aussagekraft der Paper-Ergebnisse besser einzuschaetzen. Sie erzeugt keine Sicherheit ueber kuenftige Outperformance.

Der Paper-Betrieb ist ein Forward-Test beziehungsweise eine Beobachtung ausserhalb der urspruenglichen Backtest-Auswertung. Er zeigt, wie sich die Strategie nach der Backtest-Phase unter fortlaufend neuen Marktdaten verhaelt.

### Ergebnis versus Belastbarkeit

Nach jedem Paper-Run kann festgestellt werden, ob die Strategie im beobachteten Zeitraum besser oder schlechter als die Benchmark war.

Daraus folgt aber noch keine belastbare Aussage ueber eine dauerhafte Ueberlegenheit. Kurzfristige Outperformance kann Zufall sein oder aus einer bestimmten Marktphase entstehen, die fuer `balanced_v1` guenstig war.

Ein einzelnes Ergebnis beschreibt daher nur den beobachteten Zeitraum. Die Belastbarkeit entsteht erst durch wiederholbare, nachvollziehbare Beobachtung ueber ausreichend lange Zeitraeume und unterschiedliche Marktbedingungen.

### Beobachtungsstufen

Fuer Paper-Ergebnisse gilt folgende einfache, konservative Einordnung:

* **weniger als 6 Monate:** Beobachtung laeuft, Aussagekraft gering, starkes Rauschen moeglich.
* **ab ca. 6 Monaten:** erste Tendenz erkennbar, aber noch nicht belastbar.
* **ab ca. 12 Monaten:** vorlaeufig brauchbarer Eindruck, sofern genuegend Vergleichspunkte vorhanden sind.
* **ab ca. 18 bis 24 Monaten:** deutlich interessanter, weil mehrere Marktbewegungen enthalten sein koennen.
* **ab ca. 36 Monaten oder ueber mehrere unterschiedliche Marktphasen:** robusterer Eindruck moeglich, aber weiterhin keine Garantie.

Diese Stufen sind keine automatische Qualitaetsbewertung. Sie beschreiben nur, wie vorsichtig Paper-Ergebnisse zeitlich eingeordnet werden sollten.

### Mindestbeobachtung fuer `aktien_oop`

Fuer `balanced_v1` gilt als Arbeitsregel:

* mindestens 12 Monate Paper-Beobachtung fuer eine erste belastbarere Einschaetzung
* besser 18 bis 24 Monate
* idealerweise mehrere unterschiedliche Marktphasen
* monatliche oder anderweitig klar nachvollziehbare Vergleichspunkte
* Vergleich immer gegen passende Benchmark beziehungsweise passenden Index

Die Arbeitsregel dient nur der Einordnung der Beobachtungsqualitaet. Sie leitet keine Investitionsfreigabe ab und ersetzt keine fachliche Pruefung.

### Relevante Bewertungskriterien

Die Paper-Beobachtung soll nicht nur Rendite betrachten. Relevant sind insbesondere:

* relative Rendite gegenueber Benchmark
* Volatilitaet
* Maximum Drawdown
* Ulcer-/Pain-Werte, sofern vorhanden
* Trefferquote gegenueber Benchmark pro Zeitraum
* Stabilitaet der Zielpositionen
* Stabilitaet der Buy/Sell/Hold-Proposals
* Turnover beziehungsweise Haeufigkeit der Wechsel
* auffaellige Spruenge
* Verhalten in unterschiedlichen Marktphasen

Eine reine Renditebetrachtung kann irrefuehrend sein, wenn sie Risiko, Schwankung, Drawdown, Wechselhaeufigkeit oder Marktphasen nicht beruecksichtigt.

### Vertrauensstufen statt Freigabe

Phase 7 soll eher eine Vertrauens- beziehungsweise Belastbarkeitsstufe dokumentieren als eine Entscheidung ableiten. Sinnvolle Stufen sind:

* Beobachtung laeuft
* erste Tendenz
* vorlaeufig belastbarer Eindruck
* robusterer Eindruck
* marktphasen-geprueft

Diese Stufen sind keine Anlageempfehlung und keine Freigabe fuer Investitionen. Sie dienen nur dazu, Paper-Historien nachvollziehbar und vorsichtig einzuordnen.

### Human Review

Jede Einschaetzung bleibt manuell zu pruefen. Eine gute Paper-Historie ersetzt keine fachliche Entscheidung.

Proposal-Aenderungen und Outperformance sind Pruefsignale, keine Handlungsanweisungen. Auffaelligkeiten muessen im Kontext von Marktphase, Benchmark, Strategieprofil, Portfolio-Eingaben und vorhandenen Risikokennzahlen geprueft werden.

### Sicherheitsgrenze

Auch bei langer Paper-Beobachtung gilt:

* keine Garantie auf kuenftige Outperformance
* keine automatische Entscheidung
* keine Investitionsfreigabe
* keine Ordervorbereitung
* kein Broker
* kein Live-Trading
* keine echten Orders

## 07.40 History-Report-Kennzahlen festlegen

Ziel dieses Abschnitts ist die fachliche Festlegung, welche Kennzahlen ein spaeterer Paper-Run-History-Report aus bestehenden Paper-Run-Artefakten auswerten soll.

Der History-Report soll vorhandene Paper-Run-Artefakte auswerten. Er startet keine neuen Paper-Runs und fuehrt keine automatische Paper-Run-Ausfuehrung ein.

Der Report soll Verlauf, Stabilitaet und Auffaelligkeiten ueber mehrere bestehende Paper-Runs sichtbar machen. Er dient ausschliesslich der manuellen Pruefung und ersetzt keine Human Review.

### Run-Historie

Fuer die Einordnung der ausgewerteten Paper-Runs sollen insbesondere folgende Kennzahlen und Metadaten betrachtet werden:

* Anzahl ausgewerteter Paper-Runs
* erster Run
* letzter Run
* abgedeckter Zeitraum
* erste und letzte `as_of`-Angabe
* verwendete Profile
* verwendete Strategieprofile
* verwendete Portfolio-Dateien
* verwendete Portfolio-Namen
* Konsistenz von `runner_mode = paper`
* Konsistenz der Proposal-Toleranz

Diese Angaben dienen dazu, die Vergleichbarkeit der Runs sichtbar zu machen. Wechselnde Profile, Portfolio-Dateien, Portfolio-Namen oder Proposal-Toleranzen koennen fachlich relevant sein und muessen im Report nachvollziehbar bleiben.

### Benchmark-/Index-Vergleich

Falls die erforderlichen Daten verfuegbar sind, soll spaeter betrachtet werden:

* Strategie-Rendite im Beobachtungszeitraum
* Benchmark-/Index-Rendite im Beobachtungszeitraum
* relative Differenz Strategie vs. Benchmark
* Anzahl Perioden mit Outperformance
* Anzahl Perioden mit Underperformance
* Trefferquote gegenueber Benchmark

Diese Kennzahlen sind Beobachtungswerte. Sie beweisen keine kuenftige Ueberlegenheit und erzeugen keine Investitionsfreigabe.

### Proposal-Stabilitaet

Fuer Buy/Sell/Hold-Proposals sollen spaeter insbesondere folgende Kennzahlen betrachtet werden:

* Anzahl Buy-Proposals je Run
* Anzahl Sell-Proposals je Run
* Anzahl Hold-Proposals je Run
* Anzahl Proposal-Wechsel zwischen zwei Laeufen
* haeufig wechselnde Symbole
* ueber mehrere Laeufe stabile Symbole
* neue Buy-Signale
* neue Sell-Signale
* Symbole mit wiederholtem Hin und Her zwischen Buy/Sell/Hold

Proposal-Stabilitaet beschreibt die Nachvollziehbarkeit und Veraenderung der Vorschlaege. Sie ist keine automatische Bewertung der Qualitaet eines Symbols und keine Handlungsempfehlung.

### Positionsverlauf

Der spaetere Report soll sichtbar machen koennen, wie sich Zielportfolio-Symbole ueber mehrere Paper-Runs entwickeln. Moegliche Kennzahlen sind:

* neue Symbole im Zielportfolio
* entfernte Symbole aus dem Zielportfolio
* durchgehend vorhandene Symbole
* einmalig auftauchende Symbole
* wiederkehrende Symbole
* durchschnittliche Haltedauer im Zielportfolio, sofern spaeter sinnvoll ableitbar
* Konzentration der Zielpositionen

Der Positionsverlauf bleibt eine Beobachtung der Zielportfolio-Struktur. Er fuehrt nicht zu Stueckzahl-, Euro- oder Orderberechnungen.

### Gewichtungsaenderungen

Fuer Zielgewichte und Vergleichsgewichte sollen spaeter insbesondere folgende Kennzahlen betrachtet werden:

* Zielgewicht gestiegen
* Zielgewicht gefallen
* Zielgewicht unveraendert
* groesste absolute Zielgewichtsaenderung
* durchschnittliche Zielgewichtsaenderung
* Summe absoluter Zielgewichtsaenderungen
* auffaellige Gewichtungsspruenge
* Entwicklung des Abstands zwischen Zielgewicht und Vergleichsgewicht

Gewichtungsaenderungen dienen der Stabilitaetsbeobachtung. Sie fuehren nicht zu Gewichtungsnormalisierung, Ordervorbereitung oder echter Portfolio-Umschichtung.

### Portfolio-Checks

Der spaetere History-Report soll auch pruefen beziehungsweise anzeigen koennen:

* ob Portfolio Checks in allen ausgewerteten Runs vorhanden sind
* ob Portfolio-Gewichtssummen auffaellig sind
* ob fehlende Symbole auftreten
* ob zusaetzliche Symbole auftreten
* ob Warnungen wiederholt auftreten
* ob dieselbe Portfolio-Referenz konsistent verwendet wurde

Portfolio-Checks bleiben Pruefhinweise. Wiederholte Warnungen sollen sichtbar werden, aber nicht automatisch als gut oder schlecht bewertet werden.

### Risiko- und Belastbarkeitskennzahlen

Falls die erforderlichen Daten verfuegbar sind, sollen spaeter betrachtet werden:

* Volatilitaet
* Maximum Drawdown
* Ulcer-/Pain-Werte, sofern vorhanden
* Turnover beziehungsweise Wechselhaeufigkeit
* Stabilitaet ueber mehrere Marktphasen
* Vertrauensstufe gemaess 07.30

Diese Kennzahlen ergaenzen die reine Renditebetrachtung um Risiko, Schwankung, Wechselhaeufigkeit und Marktphasen. Auch daraus entsteht keine automatische Entscheidung.

### Auffaelligkeiten

Der spaetere Report soll Auffaelligkeiten markieren koennen, zum Beispiel:

* starke Proposal-Wechsel
* starke Zielgewichtsaenderungen
* stark schwankende Deltas
* haeufige Portfolio-Check-Warnungen
* unklare Vergleichbarkeit von Runs
* wechselnde Portfolio-Dateien oder Portfolio-Namen
* uneinheitliche Proposal-Toleranzen
* fehlende Pflichtinformationen

Auffaelligkeiten sind Pruefsignale fuer die manuelle Auswertung. Der Report bewertet sie nicht automatisch als gut oder schlecht.

### Abgrenzung

Der History-Report bleibt ein Nachvollziehbarkeits- und Pruefartefakt. Er erzeugt keine Handlungsempfehlungen, keine Orders und keine Investitionsfreigabe.

Er ersetzt keinen Human Review. Seine Aufgabe ist ausschliesslich die Nachvollziehbarkeit, Stabilitaetsbeobachtung und manuelle Pruefung bestehender Paper-Run-Artefakte.

Nicht Teil dieses Zielbilds sind:

* keine neuen Paper-Runs
* keine Batch-Verarbeitung
* keine automatische Paper-Run-Ausfuehrung
* keine Broker-Anbindung
* kein Live-Trading
* keine echten Orders
* keine Stueckzahl- oder Euro-Berechnung
* keine Gewichtungsnormalisierung
* keine Personen- oder Mandantenverwaltung
* keine Investitionsfreigabe

### Moegliche spaetere Artefakte

Als moegliches Zielbild fuer spaetere Schritte koennen zusaetzliche Artefakte entstehen, zum Beispiel:

* `paper_run_history.json`
* `paper_run_history.md`
* optional `.txt`
* optional Vergleich zweier Runs
* optional Verlauf ueber mehrere Runs

Diese Artefakte werden hier nur fachlich beschrieben. Sie werden in diesem Schritt nicht implementiert und nicht erzeugt.

## 07.50 Paper-Run-History Reader / Collector

Ziel dieses Abschnitts ist ein kleiner defensiver Reader fuer bestehende Paper-Run-Artefakte.

Der Collector liest rekursiv vorhandene `paper_run_report.json`-Dateien unter einem Run-Basisverzeichnis, standardmaessig `automation_runs`. Er startet keine Paper-Runs, ruft keine Runner-Logik auf und veraendert keine Backtest-, Runner- oder Proposal-Berechnung.

Er erzeugt neutrale History-Artefakte:

* `reports/paper_run_history/paper_run_history.json`
* `reports/paper_run_history/paper_run_history.md`

Die Artefakte enthalten eine Uebersicht ueber gefundene und einbezogene Paper-Reports, wichtige Run-Metadaten, Proposal-Zaehler, Portfolio-Referenzen, vorhandene Portfolio Checks, Sicherheitsfelder und Human-Review-Hinweise. Ungueltige JSON-Dateien oder nicht als Paper-Reports erkennbare Dateien werden uebersprungen und als Warnung dokumentiert.

Beispiel:

```bash
python -m scripts.collect_paper_run_history --runs-dir automation_runs --out-dir reports/paper_run_history --strategy-profile balanced_v1
```

Optional kann zusaetzlich nach `--profile` gefiltert werden. Fehlt ein Feld, das fuer einen aktiven Filter benoetigt wird, wird der betroffene Report uebersprungen und mit Warnung dokumentiert.

Der Collector dient nur der Nachvollziehbarkeit und manuellen Pruefung bestehender Paper-Run-Reports. Er erzeugt keine Bewertung, keine Handlungsempfehlung und keine Investitionsfreigabe.

Die Sicherheitsgrenzen bleiben unveraendert:

* keine neuen Paper-Runs
* keine automatische Paper-Run-Ausfuehrung
* keine Batch-Verarbeitung von Runs
* keine Broker-Anbindung
* kein Live-Trading
* keine echten Orders
* keine Stueckzahl- oder Euro-Berechnung
* keine Gewichtungsnormalisierung
* keine Personen- oder Mandantenverwaltung
* keine Investitionsfreigabe

## 07.60 Paper-Run-History Collector Kontrolllauf mit echtem Paper-Artefakt

Ziel dieses Kontrolllaufs war, genau einen lokalen Paper-Einzelrun mit dem bekannten Beispielportfolio zu erzeugen und den Paper-Run-History Collector danach gegen ein echtes vorhandenes Paper-Artefakt laufen zu lassen.

Vorab wurde geprueft:

* `docs/paper_runner_workflow.md` dokumentiert lokale Paper-Runs mit `--runner-mode paper`, `--portfolio-file` und optional `--portfolio-name`.
* `scripts/run_bt_run_agent.py` legt Run-Artefakte unter `D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents\automation_runs\<run_label>` ab.
* `portfolios/example_local_portfolio.csv` ist vorhanden.
* `balanced_v1` ist als geeignetes Strategieprofil fuer den Kontrolllauf dokumentiert.

Ausgefuehrtes Paper-Run-Kommando:

```bash
.venv\Scripts\python.exe -m scripts.run_bt_run_agent --profile short --strategy-profile balanced_v1 --runner-mode paper --portfolio-file portfolios\example_local_portfolio.csv --portfolio-name example_local
```

Erzeugter Run-Ordner:

```text
D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents\automation_runs\2026-06-27_15-34-57_short_paper
```

Erzeugtes Paper-Artefakt:

```text
D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents\automation_runs\2026-06-27_15-34-57_short_paper\paper_run_report.json
```

Der Paper-Report enthaelt fuer den Kontrolllauf:

* `run_id`: `20260627_153457`
* `runner_mode`: `paper`
* `strategy_profile_name`: `balanced_v1`
* `portfolio_name`: `example_local`
* `portfolio_file_display`: `portfolios\example_local_portfolio.csv`
* `orders_executed`: `false`
* `broker_connected`: `false`
* `live_trading_enabled`: `false`

Ausgefuehrtes Collector-Kommando:

```bash
.venv\Scripts\python.exe -m scripts.collect_paper_run_history --runs-dir "D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents\automation_runs" --out-dir reports\paper_run_history --strategy-profile balanced_v1
```

Erzeugte beziehungsweise aktualisierte History-Artefakte:

* `reports/paper_run_history/paper_run_history.json`
* `reports/paper_run_history/paper_run_history.md`

Collector-Ergebnis:

* `total_reports_found`: `5`
* `total_reports_included`: `5`
* `total_reports_skipped`: `0`
* Der Kontrolllauf `2026-06-27_15-34-57_short_paper` erscheint in der Run-Tabelle.
* Der Lauf ist als `paper` mit Strategieprofil `balanced_v1` und Portfolio `example_local` nachvollziehbar.
* Die Sicherheitsgrenzen bleiben im History-Markdown sichtbar.

Qualitaetssicherung:

```bash
.venv\Scripts\python.exe -m pytest tests\unit\scripts\test_collect_paper_run_history.py
.venv\Scripts\python.exe -m ruff check scripts\collect_paper_run_history.py tests\unit\scripts\test_collect_paper_run_history.py
```

Ergebnis:

* `10 passed`
* `All checks passed!`

Abgrenzung:

* genau ein Paper-Run wurde gestartet
* Collector liest nur vorhandene Artefakte
* keine Batch-Verarbeitung eingefuehrt
* keine automatische Ausfuehrung mehrerer Runs eingefuehrt
* keine Runner-Logik geaendert
* keine Backtest-, Strategie- oder Portfolio-Berechnung geaendert
* keine Broker-Anbindung
* kein Live-Trading
* keine echten Orders
* keine Stueckzahl- oder Euro-Berechnung
* keine Gewichtungsnormalisierung
* keine Personen- oder Mandantenverwaltung
* keine Investitionsfreigabe

## 07.70 History-Report fachlich pruefen & naechste Vergleichsstufe festlegen

Ziel dieses Abschnitts ist die fachliche Pruefung der erzeugten Paper-Run-History. Die Pruefung klaert, ob die einbezogenen Reports nur technisch gesammelt wurden oder auch fachlich sinnvoll vergleichbar sind. Ausserdem wird festgelegt, welche naechste Vergleichsstufe auf Basis vorhandener Paper-Reports sinnvoll ist.

Gepruefte Artefakte:

* `reports/paper_run_history/paper_run_history.json`
* `reports/paper_run_history/paper_run_history.md`

### Ergebnis der Artefaktpruefung

Der History-Report wurde gegen das tatsaechliche Run-Basisverzeichnis `D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents\automation_runs` erzeugt.

Die Zusammenfassung ist technisch konsistent:

* `total_reports_found`: `5`
* `total_reports_included`: `5`
* `total_reports_skipped`: `0`
* `warnings`: keine

Einbezogene Run-Ordner beziehungsweise Run-Labels:

* `2026-06-14_01-10-45_short_paper`
* `2026-06-14_23-14-21_short_paper`
* `2026-06-18_20-32-51_short_paper`
* `2026-06-21_22-45-55_short_paper`
* `2026-06-27_15-34-57_short_paper`

Alle fuenf einbezogenen Reports haben:

* Profil `short`
* Strategieprofil `balanced_v1`
* Strategieprofil-Label `Balanced v1`
* `runner_mode = paper`
* `as_of = 2025-10-08`
* vorhandene Sicherheitsfelder
* vorhandene Human-Review-Hinweise

Die Proposal-Zaehlungen und Portfolio-Metadaten unterscheiden sich jedoch:

| Run | Portfolio-Datei | Portfolio-Name | Toleranz | Buy | Sell | Hold | Checks |
|---|---|---|---:|---:|---:|---:|---|
| `2026-06-14_01-10-45_short_paper` | nicht gesetzt | nicht gesetzt | nicht gesetzt | 2 | 2 | 7 | nein |
| `2026-06-14_23-14-21_short_paper` | `examples\paper_portfolio_positions.csv` | nicht gesetzt | nicht gesetzt | 9 | 2 | 0 | nein |
| `2026-06-18_20-32-51_short_paper` | `examples\paper_portfolio_positions.csv` | nicht gesetzt | `0.00001` | 2 | 2 | 7 | nein |
| `2026-06-21_22-45-55_short_paper` | `portfolios\example_local_portfolio.csv` | `example_local` | `0.00001` | 9 | 0 | 0 | ja |
| `2026-06-27_15-34-57_short_paper` | `portfolios\example_local_portfolio.csv` | `example_local` | `0.00001` | 9 | 0 | 0 | ja |

### Einschaetzung der Vergleichbarkeit

Die fuenf Reports sind technisch einbezogen und grundsaetzlich als Paper-Run-History lesbar. Fachlich sind sie aber nicht alle gleich stark vergleichbar.

**Technisch einbezogen:** Alle fuenf Reports wurden korrekt gefunden, als Paper-Reports erkannt und in die History aufgenommen. Es gibt keine Collector-Warnungen und keine uebersprungenen Reports.

**Fachlich gut vergleichbar:** Die beiden letzten Runs `2026-06-21_22-45-55_short_paper` und `2026-06-27_15-34-57_short_paper` erscheinen am besten vergleichbar. Sie verwenden denselben Modus, dasselbe Profil, dasselbe Strategieprofil, dasselbe `as_of`, dieselbe Portfolio-Datei `portfolios\example_local_portfolio.csv`, denselben Portfolio-Namen `example_local`, dieselbe Proposal-Toleranz `0.00001`, vorhandene Portfolio-Checks, Sicherheitsfelder und Human-Review-Hinweise. Auch die aggregierten Proposal-Zaehlungen sind identisch mit 9 Buy, 0 Sell und 0 Hold.

**Nur eingeschraenkt vergleichbar:** Die ersten drei Runs sind technisch enthalten und teilen wichtige Rahmenbedingungen wie `runner_mode = paper`, Profil `short`, Strategieprofil `balanced_v1` und `as_of = 2025-10-08`. Sie unterscheiden sich aber bei Portfolio-Referenz, Portfolio-Name, Proposal-Toleranz und Portfolio-Checks. Dadurch eignen sie sich eher fuer eine historische Einordnung der Reporterweiterung als fuer einen strengen Run-zu-Run-Fachvergleich.

**Nicht direkt vergleichbar:** Der erste Run hat keine Portfolio-Datei, keinen Portfolio-Namen, keine Proposal-Toleranz und keine Portfolio-Checks. Er kann nicht als direkte Vergleichsbasis fuer aktuelle lokale Portfolio-File-Runs gewertet werden. Auch der zweite Run ist wegen fehlender Toleranz und fehlender Portfolio-Checks nur eingeschraenkt mit den spaeteren Runs vergleichbar.

### Luecken und Auffaelligkeiten

Festgestellte Luecken beziehungsweise Auffaelligkeiten:

* Portfolio-Referenzen sind uneinheitlich: kein Portfolio, `examples\paper_portfolio_positions.csv` und `portfolios\example_local_portfolio.csv`.
* Portfolio-Namen fehlen in den ersten drei Runs und sind erst in den letzten zwei Runs als `example_local` vorhanden.
* Proposal-Toleranz fehlt in den ersten zwei Runs und ist erst ab `2026-06-18_20-32-51_short_paper` als `0.00001` sichtbar.
* Portfolio-Checks fehlen in den ersten drei Runs und sind erst in den letzten zwei Runs vorhanden.
* Die Proposal-Zaehlungen springen zwischen 2/2/7, 9/2/0 und 9/0/0. Das kann aus geaenderten Portfolio-Eingaben oder Report-Feldverfuegbarkeit entstehen und sollte nicht ohne Kontext als Strategieaenderung interpretiert werden.
* Die Run-IDs sind technisch ableitbar und vorhanden, aber fuer die fachliche Lesbarkeit sind die Run-Labels aussagekraeftiger, weil sie Datum, Uhrzeit, Profil und Modus enthalten.
* Sicherheitsfelder und Human-Review-Hinweise sind in allen fuenf Runs vorhanden und damit fuer die Sicherheitsabgrenzung konsistent.
* Fuer spaetere Vergleiche koennten zusaetzliche Felder hilfreich sein, insbesondere explizite Symbol-Listen je Proposal-Klasse, Zielgewichte je Symbol, Vergleichsgewichte je Symbol, Deltas je Symbol, Delta-Basis, Portfolio-Check-Details und gegebenenfalls eine markierte Vergleichbarkeitsklasse pro Run-Paar.

### Entscheidung fuer die naechste Vergleichsstufe

Die naechste sinnvolle Stufe ist ein neutraler Run-zu-Run-Vergleich zweier vorhandener Paper-Reports.

Dabei soll kein neuer Paper-Run automatisch gestartet werden. Die Vergleichsbasis sind ausschliesslich vorhandene `paper_run_report.json`-Artefakte.

Als erster fachlich sinnvoller Vergleich bietet sich an:

* letzter einbezogener Run: `2026-06-27_15-34-57_short_paper`
* direkt vorheriger vergleichbarer Run: `2026-06-21_22-45-55_short_paper`

Dieser Paarvergleich ist sinnvoll, weil beide Runs dieselbe Portfolio-Datei, denselben Portfolio-Namen, dieselbe Toleranz, Portfolio-Checks, Sicherheitsfelder und Human Review enthalten.

Der spaetere Run-zu-Run-Vergleich soll sichtbar machen:

* neue Symbole
* entfernte Symbole
* durchgehend vorhandene Symbole
* Buy/Sell/Hold-Wechsel
* Zielgewichtsaenderungen
* Delta-Veraenderungen
* auffaellige Spruenge

Der Vergleich bleibt neutral. Er erzeugt keine Handlungsempfehlung, keine automatische Bewertung als gut oder schlecht und keine Investitionsfreigabe.

### Sicherheitsabgrenzung

Auch die naechste Vergleichsstufe bleibt ein reines Analyse- und Dokumentationsartefakt:

* keine neuen Paper-Runs
* keine Batch-Verarbeitung
* keine automatische Ausfuehrung mehrerer Runs
* keine Runner-Logikaenderung
* keine Backtest-, Strategie- oder Portfolio-Berechnungsaenderung
* keine Broker-Anbindung
* kein Live-Trading
* keine echten Orders
* keine Stueckzahl- oder Euro-Berechnung
* keine Gewichtungsnormalisierung
* keine Personen- oder Mandantenverwaltung
* keine Investitionsfreigabe

Qualitaetssicherung: Fuer diese Phase wurden keine Tests ausgefuehrt, weil ausschliesslich vorhandene Artefakte fachlich geprueft und Dokumentation ergaenzt wurden. Es gab keine Codeaenderung.

## 07.80 Run-zu-Run-Vergleich vorhandener Paper-Reports

Ziel dieses Abschnitts ist ein neutraler Vergleich zweier bereits vorhandener `paper_run_report.json`-Artefakte. Der Vergleich startet keine Paper-Runs, durchsucht keine Run-Verzeichnisse und fuehrt keine Batch-Verarbeitung ein. Die beiden Report-Dateien werden explizit uebergeben.

Vor der Umsetzung wurden die vorhandenen Report-Strukturen geprueft:

* `target_positions` enthaelt Zielgewichte je Symbol.
* `buy_proposals`, `sell_proposals` und `hold_proposals` enthalten Proposal-Zeilen mit `ticker`, `previous_weight`, `target_weight` und `delta_weight`.
* `previous_weight` dient im Vergleich als lokales Vergleichsgewicht.
* `reports/paper_run_history/paper_run_history.json` enthaelt Run-Metadaten, Proposal-Zaehler, Portfolio-Referenzen und Pfade, aber keine vollstaendigen Symbolvergleiche.
* Hilfslogik aus `scripts.collect_paper_run_history` wird nur fuer die Run-Metadaten-Zusammenfassung wiederverwendet. Der eigentliche Run-zu-Run-Vergleich bleibt auf zwei explizite Report-Dateien begrenzt.

Neu angelegte Vergleichslogik:

```bash
python -m scripts.compare_paper_runs --previous-report <previous-paper_run_report.json> --current-report <current-paper_run_report.json> --out-dir reports/paper_run_comparison
```

Das Skript erzeugt:

* `reports/paper_run_comparison/paper_run_comparison.json`
* `reports/paper_run_comparison/paper_run_comparison.md`

Der Vergleich macht sichtbar:

* neue Symbole
* entfernte Symbole
* gemeinsame Symbole
* Zielgewicht vorher/nachher und Richtung
* lokales Vergleichsgewicht vorher/nachher
* Delta vorher/nachher und Richtung
* Proposal-Klasse vorher/nachher
* Proposal-Wechsel
* auffaellige Zielgewichtsspruenge ab `--max-jump-threshold`, standardmaessig `0.05`
* Metadatenunterschiede und fehlende optionale Felder als Warnungen

Verwendete Reports fuer den Kontrolllauf:

* Previous: `D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents\automation_runs\2026-06-21_22-45-55_short_paper\paper_run_report.json`
* Current: `D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents\automation_runs\2026-06-27_15-34-57_short_paper\paper_run_report.json`

Ausgefuehrtes Vergleichskommando:

```bash
.venv\Scripts\python.exe -m scripts.compare_paper_runs --previous-report "D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents\automation_runs\2026-06-21_22-45-55_short_paper\paper_run_report.json" --current-report "D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents\automation_runs\2026-06-27_15-34-57_short_paper\paper_run_report.json" --out-dir reports\paper_run_comparison
```

Ergebnis des Kontrolllaufs:

* neue Symbole: `0`
* entfernte Symbole: `0`
* gemeinsame Symbole: `9`
* Proposal-Wechsel: `0`
* Zielgewichtsaenderungen: `0`
* Delta-Aenderungen: `0`
* auffaellige Zielgewichtsspruenge: `0`
* Warnungen: `0`

Alle geprueften Metadaten waren zwischen den beiden Reports gleich:

* `runner_mode = paper`
* Profil `short`
* Strategieprofil `balanced_v1`
* `as_of = 2025-10-08`
* Portfolio-Datei `portfolios\example_local_portfolio.csv`
* Portfolio-Name `example_local`
* Proposal-Toleranz `0.00001`

Die neun gemeinsamen Symbole waren in beiden Reports unveraendert: `CVS`, `DASH`, `EBAY`, `GE`, `IVZ`, `NEM`, `PLTR`, `PSKY`, `WDC`.

Qualitaetssicherung:

```bash
.venv\Scripts\python.exe -m pytest tests\unit\scripts\test_compare_paper_runs.py
.venv\Scripts\python.exe -m pytest tests\unit\scripts\test_collect_paper_run_history.py
.venv\Scripts\python.exe -m ruff check scripts\compare_paper_runs.py tests\unit\scripts\test_compare_paper_runs.py scripts\collect_paper_run_history.py tests\unit\scripts\test_collect_paper_run_history.py
```

Sicherheitsabgrenzung:

* keine neuen Paper-Runs
* keine Batch-Verarbeitung
* keine automatische Ausfuehrung mehrerer Runs
* keine Runner-Logikaenderung
* keine Backtest-, Strategie- oder Portfolio-Berechnungsaenderung
* keine Broker-Anbindung
* kein Live-Trading
* keine echten Orders
* keine Stueckzahl- oder Euro-Berechnung
* keine Gewichtungsnormalisierung
* keine Personen- oder Mandantenverwaltung
* keine Investitionsfreigabe

## 07.90 Phase-7-Zwischenabschluss & weiteres Beobachtungsvorgehen

Ziel dieses Abschnitts ist der Zwischenabschluss von Phase 7. Die bisherige Arbeit hat den Paper-Betrieb ueber mehrere Laeufe fachlich eingeordnet, technisch auswertbar gemacht und einen ersten kontrollierten Run-zu-Run-Vergleich auf Basis vorhandener Artefakte ermoeglicht.

Zwischenstand Phase 7:

* Das Zielbild fuer Paper-Betrieb ueber mehrere Laeufe ist dokumentiert.
* Datenquelle und Vergleichsmodell fuer Paper-Run-History sind dokumentiert.
* Beobachtungsdauer und Belastbarkeit der Paper-Ergebnisse sind fachlich eingeordnet.
* Kennzahlen fuer History-Reports sind festgelegt.
* Der History-Collector ist implementiert.
* Ein Kontrolllauf mit echtem Paper-Artefakt wurde durchgefuehrt.
* Vorhandene History-Artefakte wurden fachlich geprueft.
* Der Run-zu-Run-Vergleich vorhandener Paper-Reports ist implementiert.

Technischer Stand:

* `scripts/collect_paper_run_history.py`
* `scripts/compare_paper_runs.py`
* `reports/paper_run_history/paper_run_history.json`
* `reports/paper_run_history/paper_run_history.md`
* `reports/paper_run_comparison/paper_run_comparison.json`
* `reports/paper_run_comparison/paper_run_comparison.md`

Ergebnis des ersten Run-zu-Run-Vergleichs:

Verglichene Runs:

* `2026-06-21_22-45-55_short_paper`
* `2026-06-27_15-34-57_short_paper`

Beide Runs waren fachlich gut vergleichbar. Die geprueften Rahmenbedingungen waren gleich genug, um einen ersten neutralen Vergleich der Zielgewichte, Proposals und Deltas vorzunehmen.

Ergebnis:

* neue Symbole: `0`
* entfernte Symbole: `0`
* gemeinsame Symbole: `9`
* Proposal-Wechsel: `0`
* auffaellige Zielgewichtsspruenge: `0`
* Delta-Aenderungen: `0`
* Warnungen: `0`

Einordnung:

* Das Ergebnis ist ein Stabilitaetssignal fuer diesen kurzen Vergleichszeitraum.
* Es ist kein Beweis fuer dauerhafte Stabilitaet.
* Es ist kein Beweis fuer zukuenftige Outperformance.
* Es ist keine Investitionsfreigabe.

Aussagekraft und Grenzen:

* Die bisherige Paper-Historie ist noch kurz.
* Die Beobachtung deckt noch keine laengere echte Forward-Test-Phase ab.
* Die Aussagekraft waechst erst ueber mehrere Monate und unterschiedliche Marktphasen.
* Die ersten drei aelteren Reports sind nur eingeschraenkt vergleichbar.
* Die letzten zwei Reports sind fuer den ersten Vergleich gut geeignet.
* Der aktuelle Vergleich zeigt technische und kurzfristige fachliche Stabilitaet, aber keine langfristige Belastbarkeit.

Weiteres Beobachtungsvorgehen als Arbeitsregel:

* Paper-Runs nicht kuenstlich haeufig erzeugen.
* Sinnvoll sind wiederholte Einzelruns in klaren zeitlichen Abstaenden.
* Nach jedem neuen geeigneten Paper-Run:
  1. History-Collector ausfuehren.
  2. Fachlich pruefen, ob der neue Run vergleichbar ist.
  3. Run-zu-Run-Vergleich gegen den vorherigen vergleichbaren Run ausfuehren.
  4. Auffaelligkeiten manuell pruefen.
* Bei stabilen Ergebnissen weiter beobachten.
* Bei starken Aenderungen nicht automatisch handeln, sondern Gruende pruefen.

Moeglicher naechster sinnvoller Schritt:

* Phase 7 kann nun in den beobachtenden Paper-Betrieb uebergehen.
* Weitere Code-Erweiterungen sollten nur erfolgen, wenn mehrere neue Paper-Runs vorliegen oder konkrete Report-Luecken sichtbar werden.
* Ein spaeterer Schritt koennte ein Multi-Run-Verlaufsvergleich sein, aber erst wenn ausreichend vergleichbare Runs vorhanden sind.
* Aktuell ist kein zusaetzlicher Automatisierungsschritt zwingend noetig.

Sicherheitsabgrenzung:

* kein Broker
* kein Live-Trading
* keine echten Orders
* keine Stueckzahl- oder Euro-Berechnung
* keine Gewichtungsnormalisierung
* keine Batch-Verarbeitung von Runs
* keine automatische Paper-Run-Ausfuehrung
* keine Personen-/Mandantenverwaltung
* keine Investitionsfreigabe
* keine Handlungsempfehlung
