# M1.30 – Nachweis der effektiven Konfiguration

Stand: 22. November 2026. Grundlage ist der fachlich freigegebene
[Berechnungsvertrag K1/K6/K8](../../agentic-software-development-cookbook/docs/aktien-oop-m1-calculation-contract.md).
M1.30 beobachtet die vorhandene Auflösung; es implementiert keine der noch offenen
Änderungen an Datenvalidität, Cadence, Exposure, Kosten oder Bestandsfortschreibung.

## Artefakte und Gültigkeit

`write_strategy_profile_overlay()` ergänzt ausschließlich temporäre Laufkopien um
`[m1_profile]`: Profildeklarationen, Profilquelle sowie SHA256 von Profil- und
Basiskonfiguration. Diese Tabelle wird nicht zur Parameterauflösung verwendet.
Die drei Strategieprofile und sämtliche Basiskonfigurationen bleiben unverändert.
`short`, `medium`, `long` und `problem` bleiben getrennte Ausführungsprofile.

Beide realen Loader erfassen unter `configuration_evidence`:

- gelesene Dateien in Reihenfolge mit SHA256 und geparstem Inhalt;
- zusammengeführte/generierte TOML, deklarierte Profilwerte und CLI-Argumente;
- je Parameter die vorhandenen Root-/Abschnittswerte, CLI-Kandidaten,
  Vorrangregel, ausgewählte Quelle/Datei und tatsächlich geladenen Wert;
- tatsächlich erzeugte `CalcParams`, aktive Schalter, Gate-Entscheidung,
  Gate-SMA/-Zeitraum, Universe und verwendetes Sektormapping;
- explizite Findings für ignorierte, überschattete, unbekannte oder bei der
  Normalisierung/Fallbackbehandlung abweichende Werte.

Die Herkunftstabellen sind Diagnosebeschreibungen der bestehenden Loader, keine
zweite Konfigurationsauflösung. Runtime-Werte werden an den produktiven
Aufrufstellen beobachtet. `core_params_constructed` und `core_invoked` unterscheiden
konstruierte Parameter vom tatsächlichen Core-Aufruf; bei Cadence-Skip wird kein
neuer Core-Aufruf behauptet. Inaktive Schalter bedeuten keine ausgeführte Prüfung.

BT und Runner schreiben den Nachweis in bestehende Decision Bundles; der BT
schreibt ihn zusätzlich in seinen Parametersnapshot. Das Orchestrierungsmanifest
trennt unter `calculation_validation` die fachliche Gültigkeit vom bisherigen
Prozessfeld `success` und bezeichnet seine Profilfelder als Deklarationen.
Ein fehlendes Bundle oder ein vorzeitig abgebrochener Lauf ist kein Runtime-Nachweis.
Programmatisch erzeugte Konfigurationen ohne Loadernachweis werden entsprechend
markiert; `dataclasses.replace()` erhält die ursprüngliche Loaderbeobachtung,
spätere Runtime-Abweichungen werden zusätzlich sichtbar.

**Alle derzeitigen Ergebnisse sind `diagnostic_not_m1_accepted` und
`binding_eligible=false`.** Die Prüffunktion `require_binding_evidence()` weist
solche Nachweise zurück. Sie wird nicht als neue Handelsregel in Legacy-Läufe
eingebaut. Warnungen/Metadaten heilen keine fachlichen Abweichungen und erteilen
keine M1-Gesamtabnahme. Vollständige Ergebnisvalidierung bleibt M1.40–M1.90.

## Nachgewiesene Abweichungen, unverändert gelassen

| Bereich | Derzeitige Wirkung | Behandlung |
| --- | --- | --- |
| Drei Profile | top_k 15, Sektorlimit 2, Cap 0.20; Conservative Gate/SELL/Cash, Balanced Gate/HOLD/kein Cash, Offensive kein Gate/kein Cash | Deklaration, Laufkopie und reale Loader separat nachgewiesen |
| BT-Exposure | `[limits].regime_exposure_low=0.65` wird nicht geladen; effektiv Default 0.50 | Ignorierte Deklaration/Default sichtbar; keine Aktivierung von 0.65; M1.60 |
| Benchmark | Profilwert liegt beim BT unter `[limits]`; `SXR8.DE` entsteht durch Loaderdefault; Runner lädt keinen Performancebenchmark | Gleicher Wert wird nicht als erfolgreiche Profilweitergabe ausgegeben |
| Kosten | BT ignoriert `[limits].cost_bps=0` / `slippage_bps=7` und verwendet Root/CLI/Defaults 10/5; Runner ohne geladene bps verwendet 0/0 im Core | Geladene und aktive Werte getrennt; keine Kostenkorrektur; M1.70 |
| Runner-Normalisierung | `[limits]` kann geladene CLI-Limits, `[core].period` den CLI-Zeitraum und `[rebalance]` die CLI-Frequenz erneut übergehen | `runtime_overrides_loader`; keine Prioritätsänderung |
| Cadence | Runner prüft Systemmonat/Force statt deterministischer as-of-Cadence | Runtime-Konvention ausdrücklich benannt; M1.50 |
| BT-Gate-CLI | Akzeptierte `--regime-use-filter` / `--regime-sma-days` wirken nicht im Loader | `unused_cli_argument`; tatsächlicher Gate-SMA separat beobachtet |
| Weitere Deklarationen | `extends` wird nicht vererbt; manche Filter-/Adjustierungs-/Gewichtungswerte erreichen den Core nicht | Ignorierte/ unbekannte Werte melden; keine automatische Reparatur |
| Geladene Core-Felder | `vol_days`, `use_under_sma` und `sma_days` werden übergeben, vom aktuellen Core-Scoring aber nicht gelesen; SMA-Penalty wird aus `score_days` abgeleitet | Unter `core_parameter_usage` ausdrücklich beschrieben und mit echtem Core geprüft |
| Turnover | Cap beeinflusst Legacy-Kostenturnover, keine Trades | Wirkung bezeichnet; M1.70 bleibt offen |

Die einfachen BT-Bundlefelder für Cap und Sektorlimit erhalten jetzt explizite
Nullwerte korrekt; diese Diagnosekorrektur ändert keine Berechnung.
Ein wirksamer Override ist nicht automatisch ein Fehler. Herkunft und abweichende
Werte bleiben dennoch sichtbar. Fehlende Angaben werden nicht als Profilwerte
erfunden; Defaults und nicht geladene Parameter sind ausdrücklich markiert.

## Prüfung und Grenzen

Gezielte Tests liegen in
[`test_effective_configuration_contract.py`](../tests/unit/scripts/test_effective_configuration_contract.py),
unter dem vorhandenen
[`m1_isolation`](../tests/unit/scripts/m1_isolation.py)-Schutzrahmen. Sie verwenden
Python 3.11.9, reale Loader, synthetische Kurse und temporäre Konfigurationskopien.
Geprüft werden alle drei Profile, mehrere Runner-Dateien, Overrides, false/0,
Fallbacks, unbekannte Schlüssel, echte Bundle-/Snapshot-Ausgaben, deterministische
Nachweise und unveränderte Positionen/Trades/Equity bei deaktivierten Beobachtern.

Die Isolation ist kein OS-Sandboxversprechen. Produktive CLIs, historische oder
Batch-/Paper-Läufe sowie beliebige native Ein-/Ausgabe sind damit nicht freigegeben.
Dieser Nachweis ersetzt keine Datensatz-, Währungs-, Anfangsbestands- oder
Signalzeitvalidierung. Vollständige BT-/Runner-Parität einschließlich Cash wird
weiterhin erst in M1.90 abgenommen. M1.40 wird nicht automatisch gestartet.
