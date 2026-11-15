---
title: Plausibilitätsprüfung (Logikfehler)
---

# Plausibilitätsprüfung (Logikfehler)

**Prinzip:** Die Prüfung macht der **Code**, nicht das Modell, weil Datumsrechnung im Code zuverlässig ist.
Das Backend-Modell ruft das Tool `provjeri_podatke` auf, sobald Stationen bzw. Angaben gesammelt sind. Das Tool liefert eine Liste von Auffälligkeiten zurück. Lina fragt **pro Auffälligkeit genau einmal** freundlich nach. Bestätigt der Kandidat, wird die Angabe **übernommen und als Hinweis markiert**, nicht korrigiert und nicht erneut gefragt.

## Regeln
| Nr. | Regel | Beispiel | Reaktion |
|---|---|---|---|
| L1 | Zwei Jobs überschneiden sich | 2010–2015 Firma A, 2013–2017 Firma B | nachfragen: parallel oder Versprecher? |
| L2 | Ende vor Beginn | od 2018, do 2015 | nachfragen und korrigieren lassen |
| L3 | Datum in der Zukunft | do 2027 | nachfragen |
| L4 | Arbeit vor dem 15. Lebensjahr | rođen 2000, posao od 2012 | nachfragen |
| L5 | Vollzeitschule und Vollzeitjob gleichzeitig | škola 2005–2009, posao 2006–2010 | nachfragen |
| L6 | Mehr Erfahrungsjahre als möglich | 20 Jahre Erfahrung bei Alter 30 | nachfragen |
| L7 | „Aktuell“ und zugleich ein Enddatum | aktuelno + do 2023 | nachfragen |
| L8 | Lücke von mehr als 12 Monaten zwischen Stationen | 2015–2019 nichts | einmal neutral nachfragen („Šta si radio u tom periodu?“), Antwort akzeptieren |
| L9 | Kinderalter unplausibel | dijete 15, kandidat 20 | nachfragen |
| L10 | Schulende vor Schulbeginn oder Schule vor dem 6. Lebensjahr | – | nachfragen |

## Grundlage für die Prüfung
- **Heute:** aktuelles Datum in `Europe/Sarajevo` (siehe CLAUDE.md, Datum und Zeit)
- **Geburtsdatum:** aus `Datum rođenja`. Fehlt es, entfallen L4, L6, L9 und L10.
- Unscharfe Angaben („oko 2015“, „ljeto 2018“) werden auf das Jahr bzw. den Monat normalisiert und mit `approx=true` geprüft.

## Ausgabe des Tools (Beispiel)
```json
{"auffaelligkeiten":[{"regel":"L1","text":"Firma A 2010–2015 i Firma B 2013–2017 se preklapaju","stationen":[1,2]}]}
```

## Tests (Pflichtszenarien)
- Überschneidung → Lina fragt genau einmal, Kandidat sagt „ja, parallel“ → wird übernommen, Hinweis gespeichert
- Ende vor Beginn → Lina fragt, Kandidat korrigiert → korrigierter Wert wird gespeichert
- Keine Auffälligkeit → Lina fragt nichts nach
