# M1.60 – Exposure und VolTarget

## Modellpfad nach D1

Backtester und Runner verwenden weiterhin das gemeinsame Handelsregime auf dem
nicht adjustierten Schlusskurs von `^GSPC`. Das Gate prüft strikt `Close > SMA`.
Bei einem bekannten negativen Signal bleibt Conservative bei SELL und Balanced
bei HOLD. Offensive läuft ohne Gate. Die Verarbeitung unbekannter Signale
folgt D5.

Der BT bewertet seine Aktienpositionen mit den bestehenden Intervallgewichten
und addiert den bestehenden Cash-Ertrag. Equity, Reportkennzahlen, Positionen
und Trades erhalten keine positionslose Skalierung. Vergleichsbenchmark-Kurse
gehen ausschließlich in die Vergleichsauswertung ein. Bei fehlenden Kursen
weist die Zusammenfassung den Vergleich als nicht verfügbar aus. D2–D4
einschließlich Bestandsdrift, Cash/NAV und Kosten liegen weiterhin in ihren
eigenen Arbeitspaketen.

Beide Engines beziehen die Startgewichte aus
`core_calc.calculate_portfolio → size_weights`. Auswahl, Sektorgrenzen,
Rundung und Gewichtsnormalisierung sind unverändert. `use_equal_weight`
erzeugt im derzeitigen Core keine inverse Volatilitätsgewichtung. Die beiden
unbenutzten BT-Hilfsfunktionen dafür wurden entfernt. Die Methode
`Rebalancer.inverse_vol_allocation` unter `aktien_oop/rebalance.py` hat
keinen produktiven Aufrufer. Die getrennte ältere Anwendung `aktien` hat
einen eigenen inversen Volatilitätsansatz außerhalb von `aktien_oop`.
Bei aktivem `max_active_names` normiert der Core die verbleibenden
Aktiengewichte auf `1 - Cash` und wendet anschließend die bestehenden
Friction-Regeln an. Der separate Helfer `_apply_max_active_names` wird
nicht aufgerufen. `[limits].max_weight_per_name` bleibt eine ignorierte
Deklaration. Eine neue Exposure-Grenze wurde fachlich nicht festgelegt.

## Optionale historische BT-Diagnose

Mit `--legacy-exposure-diagnostics` oder
`legacy_exposure_diagnostics = true` am TOML-Root schreibt BT
`*_legacy_exposure_diagnostic.json`. Die Einstellung ist standardmäßig aus.
`--no-legacy-exposure-diagnostics` überschreibt eine Aktivierung in TOML.
Der Runner hat keinen entsprechenden Ausführungspfad.

| Einstellung | Wirksamer Wert für die Diagnose |
| --- | --- |
| `regime_exposure_low` | CLI vor TOML-Root, Standard 0,50. Bei aktivem Gate verwendet die Diagnose den Faktor unter dem Benchmark-SMA. Gleichstand verwendet Faktor 1. Der Faktor 1 neutralisiert diese Komponente. Zulässig sind Werte von 0 bis 1. |
| `vol_target_ann` | CLI vor TOML-Root. Fehlender Wert oder 0 deaktiviert die Komponente. Ein positiver Wert aktiviert sie auch ohne Handelsgate. |
| `vol_lookback_days` | CLI vor TOML-Root, Standard 20. Bei positivem Ziel erfordert die rollierende Standardabweichung mindestens zwei tägliche Renditen. |
| Benchmark-Reihe | Bestehende BT-Auflösung für `benchmark_ticker` und die CLI-Aliase. Die Diagnose verwendet XETR für `SXR8.DE` sowie XNYS für `SPY` und `^GSPC`. |

Alte `[limits]`-Deklarationen wie `regime_exposure_low = 0.65` behalten
ihren dokumentierten Status als ignorierte Werte. Die Herkunft der
Parameter ist im Konfigurationsnachweis sichtbar.

VolTarget verwendet das jährliche Ziel geteilt durch die Quadratwurzel
aus 252 und anschließend durch die rollierende Standardabweichung der
täglichen Benchmark-Rendite. Der Multiplikator ist nach oben auf 1 begrenzt.
Die beiden Multiplikatoren wirken auf die hypothetischen Aktienrenditen
der Diagnose. Der Cash-Ertrag bleibt unverändert. Die Diagnose verwendet
den verfügbaren Benchmark-Schluss vor Beginn der Renditeperiode nach D6.

Das Artefakt enthält hypothetische Tagesrenditen vor Kosten und setzt
`binding_eligible = false`. Ungültige Parameter oder fehlende Diagnosekurse
ergeben `unavailable` samt Ursache und ohne Renditewerte. Ohne aktive
Skalierung oder Aktienintervalle steht dort `inactive`. Der aktuelle
`*_params.json`-Stand enthält Status und Artefaktpfad. Ein Schreibfehler
erscheint dort als `write_failed`. Historische
Resultate mit aktiver Skalierung verwenden eine andere Methodik.
