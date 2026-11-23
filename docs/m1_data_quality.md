# M1.40 – Datenqualität an BT-/RUN-Entscheidungsgrenzen

M1.40 ergänzt den freigegebenen D5-Vertrag. Es ist keine Investitionsfreigabe;
M1.50–M1.90 und die M1.30-Kennzeichnung `binding_eligible=false` bleiben bestehen.

## Regeln und Geltungsbereich

- Unterstützt werden tägliche Schlusskursmatrizen für US-Aktien im bestehenden
  SP500-Pfad sowie das erforderliche `^GSPC`-Gate. Die erforderlichen Sitzungen
  stammen aus `exchange_calendars`/XNYS. Andere Börsenkalender benötigen eine
  ausdrückliche Erweiterung des Datenbereichs. Es gibt keine implizite FX- oder
  Corporate-Action-Behandlung.
- Nicht-Handelstagszeilen werden mit `NON_SESSION_OBSERVATION` ausgeschlossen;
  sie zählen weder zum SMA-/Historienfenster noch zur BT-Bewertung. Im aktiven
  Legacy-Exposure-Pfad gilt für `SXR8.DE` ausdrücklich XETR; für `SPY` und
  `^GSPC` XNYS. Andere Exposure-Symbole werden mangels Kalenderzuordnung gesperrt.
- Ein angefragter Börsenschließtag verwendet den vorherigen **Kalenderhandelstag**
  und erhält `CLOSED_SESSION_AS_OF` mit `effective_as_of`. Ein fehlender Kurs für
  diesen erforderlichen Handelstag wird nicht durch einen beliebigen älteren
  Kurs ersetzt. Die Cadence-/Ausführungsregeln aus M1.50 werden nicht verändert.
- Erforderliche Historie im Core: Maximum aus `max(score_days,63)+21`,
  `vol_days+1`, 100 und gegebenenfalls aktiviertem SMA-Fenster. BT berücksichtigt
  zusätzlich `min_history_days`. Das Gate benötigt `regime_sma_days` valide
  Beobachtungen. Fehlende XNYS-Sitzungen im erforderlichen Fenster sperren die
  gesamte Matrix; NaN/Inf, nicht positive oder nicht numerische Preise und
  unzureichende Historie eines Titels schließen diesen mit Diagnose aus.
- Doppelte Zeitstempel/Spalten, ungültige Tagesindizes und unsortierte Zeitreihen
  werden vor Sortierung, Deduplizierung oder Filling gesperrt. Im Core werden
  Preload-Zeilen nach dem Stichtag abgeschnitten; im ausdrücklich begrenzten
  Gate-Abruf gelten Zukunftsdaten als ungültig.
- Erforderliche Kurse gehaltener Titel dürfen nicht ausfallen. Dann ist keine
  neue Zielallokation bestätigbar. Im BT werden zusätzlich alle gehaltenen
  Intervallpreise und die tatsächlich genutzten Renditen vor einer Nullwert-
  Ersatzbehandlung geprüft. Fehlerhafte Kandidaten ohne Bestand blockieren
  nicht automatisch andere valide Kandidaten. Eine leere zulässige Auswahl
  ist `NO_VALID_SELECTION`, kein stilles SELL oder erfundenes Cash.
- Unbekannte Sektoren werden bei aktivem globalem Sektorlimit ausgeschlossen;
  bei betroffenen gehaltenen Titeln wird gesperrt. Ohne Limit ist das eine
  Warnung. Widersprüchliche Zuordnungen normalisierter Ticker sind unbekannt,
  identische Duplikate zulässig. Bestehende individuelle `sector_limits`, die
  der Core nicht durchsetzt, werden bei Aktivierung ausdrücklich gesperrt.
- Ein fehlendes oder leeres Runner-Universum erzeugt `INVALID_UNIVERSE`;
  es wird keine Ersatzliste aus AAPL/MSFT/NVDA erfunden.
- Das zentrale Gate unterscheidet boolesche positive/negative Signale von
  `ok=null`, `action=UNCONFIRMED`, `status=invalid`. Unknown ist keine negative
  Marktmeinung. Die bekannten HOLD-/SELL-Policies bleiben erhalten. HOLD ohne
  bekannten vorherigen Zustand ist nicht bestätigbar. Die gatefreie Offensive
  lädt keine Gate-Daten, validiert aber ihre eigenen Auswahl-/Bewertungskurse.
- Die bestehende BT-Exposure-Arithmetik bleibt bei gültigen Eingaben erhalten.
  Fehlende/undefinierte tatsächlich verwendete Exposure-/Volatilitätssignale
  erzeugen keine stillen niedrigen Faktoren oder eine automatische Abschaltung.
  Die Modellbereinigung der Legacy-Skalierung bleibt M1.60.

## Diagnosen und Zustand

Gemeinsame Helfer liegen in `AiAgents/aktien_oop/core_calc.py`, Gate-Aufbereitung
in `data_client.py`; es gibt kein zweites Datenqualitätsframework.

`DataQualityError` beendet den Versuch vor einer gültigen Bestätigung. BT und RUN
schreiben gesonderte `BT_data_quality_invalid.json` beziehungsweise
`RUN_data_quality_invalid.json` in das konfigurierte Ausgabeverzeichnis. Diese
enthalten `status=invalid`, `decision_confirmed=false`, `action=UNCONFIRMED`,
Ursachencodes, Schweregrad, betroffene Titel/Felder, Stichtag, Quelle und die
M1.30-Konfigurationsnachweise. `core_invoked` beschreibt den tatsächlichen
Aufrufversuch; ein Validierungsfehler innerhalb des Core löscht ihn nicht.

Erfolgreiche Decision Bundles enthalten Warnungen/Ausschlüsse als
`configuration_evidence.runtime.data_quality`. Ein Fehler erzeugt kein gültiges
Bundle für den gesperrten Stichtag und überschreibt keine Runner-Positionen.
Frühere gültige Bundles bleiben erhalten. Ein BT-Abbruch schreibt keinen neuen
aggregierten Erfolgsreport; bereits entstandene Diagnosen/Teilbundles und ältere
Reports dürfen nicht als Abnahme eines neuen Gesamtlaufs interpretiert werden.
Die vollständige Report-/Kennzahlenabnahme bleibt M1.90, die Zustandsmechanik
und Portfoliofortschreibung bleiben M1.80.

Wichtige Codes: `EMPTY_PRICES`, `EMPTY_REGIME`, `MISSING_AS_OF`,
`INSUFFICIENT_HISTORY`, `UNRESOLVED_SESSION_GAP`, `DUPLICATE_TIMESTAMP`,
`UNSORTED_TIMESTAMPS`, `NONFINITE_PRICE`, `NONPOSITIVE_PRICE`, `NONNUMERIC_PRICE`,
`UNKNOWN_SECTOR`, `UNKNOWN_PREVIOUS_STATE`, `UNKNOWN_LEGACY_EXPOSURE`,
`UNDEFINED_REGIME_SMA`, `NONFINITE_VALUATION_RETURN`.

## Synthetische Verifikation

Neue Fälle stehen in `tests/unit/scripts/test_data_quality_contract.py`.
Die zwei bestehenden Charakterisierungen wurden gezielt fortgeschrieben:
Unknown-Gate/Exposure und beliebige Stichtagsrückdatierung sind seit M1.40
gesperrt. Vollständig gültige Profil-, Cash-, Turnover-, Gate- und
Konfigurationsfälle bleiben Regressionstests; die alten Checkpoint-Inhalte
bleiben als unveränderte Referenz gesichert.

Python 3.11.9, Interpreter `AiAgents/.venv311/Scripts/python.exe`; vorher
`-m pip install -r aktien_oop/requirements-dev.txt` aus AiAgents. Für die
Vertragstests `AI_AGENTS_ROOT` auf AiAgents setzen, dann aus automation-agents:

```powershell
..\AiAgents\.venv311\Scripts\python.exe -B -m pytest `
  tests/unit/scripts/test_data_quality_contract.py `
  tests/unit/scripts/test_effective_configuration_contract.py `
  tests/unit/scripts/test_strategy_profile_cash_contract.py `
  tests/unit/scripts/test_strategy_profile_turnover_contract.py `
  tests/unit/scripts/test_strategy_profile_regime_exposure_contract.py `
  tests/unit/scripts/test_m1_isolation.py `
  -p no:cacheprovider --basetemp=<frischer-TEMP-Pfad>
```

Der vorhandene M1.20-Guard bleibt aktiv: keine Downloads, produktiven Datenlese-
oder Schreibzugriffe, Brokerzugriffe oder Kindprozesse in den Testfällen.
Die native AiAgents-Suite wird ebenfalls mit diesem Guard ausgeführt; ein
temporärer Adapter ergänzt für sechs Legacy-Loader-Tests nur den normalen
CLI-Schalter `--save-dir` nach TEMP. Die fachlichen Implementierungen bleiben echt.

Kalender-API: [exchange_calendars – Sessions und XNYS](https://github.com/gerrymanoim/exchange_calendars#working-with-sessions).
