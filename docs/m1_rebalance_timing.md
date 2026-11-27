# M1.50 – Stichtage, Ausführung und Kursverfügbarkeit

Grundlage ist D6 des [M1.10-Berechnungsvertrags](../../agentic-software-development-cookbook/docs/aktien-oop-m1-calculation-contract.md). Das Paket spezifiziert die zeitliche Reihenfolge für Modellentscheidungen mit Tageskursen. Die bestehenden Nachweise zur [effektiven Konfiguration](m1_effective_configuration.md) und [Datenqualität](m1_data_quality.md) gelten weiterhin.

## Abweichungen im Ausgangsstand

- RUN prüfte den Systemmonat. Historische Stichtage und Wochenintervalle bestimmten die Cadence dadurch nicht zuverlässig.
- BT leitete Rebalancing-Termine aus vorhandenen Preiszeilen ab, ergänzte ein signalähnliches Datum am Ende jedes Testfensters und konnte per Laufindex Termine überspringen.
- BT setzte das neue Portfolio am Signaltag ein. Die Legacy-Exposure bezog den Tageskurs derselben Renditeperiode in ihre Entscheidung ein.
- Eine fehlende Preiszeile am Modell-Ausführungstag hatte keinen eigenen Status. Bei der Übergabe von BT an RUN konnten Bestände schon am Signaltag als verfügbar gelten.

## Gemeinsame Zeitlogik

| Feld | Bedeutung |
| --- | --- |
| `signal_as_of` | Letzte zulässige Session der ISO-Woche Montag bis Sonntag oder des Kalendermonats. Signalpreise und notwendige Historie reichen höchstens bis zu diesem Tag. |
| `decision_time` | Früheste Zeitgrenze für verwendbare Tagesdaten. Da der vorhandene Anbieter keine belastbare Veröffentlichungszeit für den finalen Balken liefert, gilt konservativ Mitternacht des folgenden Ortskalendertags. Die tatsächlich vorliegenden Kurse werden anschließend geprüft. |
| `execution_date` | Nächste gemeinsame Session mit einem Schluss nach der Signalverfügbarkeit. Feiertage und verkürzte Sessions kommen aus dem in M1.40 verwendeten Börsenkalender. |
| `execution_time` | Offizieller Schluss dieser Session in UTC. Der Schlusskurs muss seinerseits vollständig verfügbar sein, bevor der Modellzustand bestätigt wird. |

Für die vorhandenen US-Aktienuniversen und das S&P-500-Gate gilt XNYS als gemeinsamer Kalender. Erkennbar fremde Handelssymbole werden abgewiesen. Der Legacy-Vergleich mit `SXR8.DE` verwendet XETR für die Verfügbarkeit; dessen Kurs ist kein Ausführungskurs. Exposure und VolTarget beziehen sich bei einer Tagesrendite auf die Information, die bereits beim vorigen Bewertungsschluss verfügbar war.

RUN verwendet `--as-of` als Beobachtungsgrenze. Ein Datum ohne Uhrzeit bezeichnet das Ende des Tages in New York. Uhrzeiten mit Offset sind eindeutig, Uhrzeiten ohne Offset gelten als New Yorker Ortszeit. In keinem Fall wird über die tatsächliche Uhr hinaus beobachtet. `--execution-as-of` kann für einen historischen Lauf das gewählte Signal festhalten und separat einen späteren Beobachtungszeitpunkt für den Ausführungskurs angeben. BT verwendet `start` und `end` für seinen historischen Zeitraum. Beide Loader berücksichtigen die explizite Intervallkonfiguration. Der alte BT-Laufindexfilter `rebalance_every_n` hat bei Werten ungleich 1 keine freigegebene Kalenderdefinition und wird mit Diagnose abgewiesen.

`--force` wählt auch außerhalb des üblichen Intervallendes die letzte vollständig verfügbare Session. Eine bereits bestätigte Ausführung für das Intervall bleibt bestehen. Reguläre wiederholte RUN-Aufrufe bearbeiten einen fälligen offenen Vorschlag zuerst und behalten dessen Ausführungsdatum und ursprünglichen Force-Status bei. Ein explizites `--execution-as-of` bindet den Lauf an das ausgewählte Signal. Historische Vorschläge werden gegen einen bereits veröffentlichten offenen Vorschlag geprüft. Eine veränderte Allokation oder ein veränderter Vorbestand erfordert Klärung.

## Modell-Ausführung und Grenzen

- Sobald alle Signaldaten gültig sind, kann ein ausstehender Vorschlag separat ausgegeben werden. Er ändert den Snapshot nicht. Fehlt ein erforderlicher Kauf-, Halte- oder Verkaufsschlusskurs am vorgesehenen Datum, bleibt der alte Zustand bestehen und der Lauf benennt Datum und Titel im Qualitätsfehler.
- BT bewertet den alten Bestand bis einschließlich Ausführungsschluss. Danach gelten die neuen Gewichte. Bestehende modellierte Gebühren werden am Ausführungsereignis gebucht. Festgewichtsmodell, Kostenformel und die Übergabe der Zielgewichte bleiben im bestehenden fachlichen Umfang.
- Das BT-Entscheidungsbundle behält `as_of` als Signalbezug. Positions- und Trade-Artefakte weisen zusätzlich `execution_date` aus. Bei der Bestandsübergabe verwendet der Seeder den validierten Ausführungstag. Der Vergleichswrapper reicht den im aktuellen, validierten BT-Bundle belegten Beobachtungshorizont getrennt als `--execution-as-of` weiter. RUN prüft seinen Ausführungskurs selbst am vorgesehenen Termin. Der Paper-Bericht berechnet Gewichtsänderungen erst für ein bestätigtes RUN-Bundle des aktuellen Aufrufs. Bei ausstehender Ausführung weist er den Termin und den bekannten Vorbestand aus. Die Zielgewichte bleiben offen. Im Paper-Modus ersetzt der Wrapper vorhandene Runner-Snapshots nicht durch BT-Vorbestände. Das BT-Seeding bleibt auf den Analysemodus beschränkt. Vollständige Vergleichs- und Portfolio-Parität gehören zu M1.90.
- Der Cache verwirft zu früh geladene Tagesbalken für diese Pfade. RUN verwendet nur vollständige Treffer für die feste Ausführungssession. Eine lückenhafte BT-Bulk-Reihe kann im Cache verbleiben und den gleichen Ausführungstermin erneut blockieren.
- Die Tagesreihen dürfen für den Signalschnitt keine später datierten Beobachtungen beitragen. Die verfügbare Quelle liefert keine revisionssicher versionierten historischen Balken. Nachträgliche Anbieter- oder Corporate-Action-Anpassungen bereits datierter Kurse sind deshalb nicht rückwirkend nachweisbar. Die Artefakte kennzeichnen diese Provenienz und bleiben gemäß M1-Konfigurationsnachweis von verbindlichen Ergebnissen ausgeschlossen. Die Modellrechnung ist keine Investitionsfreigabe.
