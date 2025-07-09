# Arbeitsagentur Job Tracker

**This README is available in English and German.**  
[English Version](README.en.md)

Dies ist ein Desktop-Tool, das ich entwickelt habe, um Bewerbungen besser und organisierter zu verwalten. Es verbindet sich mit der offiziellen API der Bundesagentur für Arbeit und ermöglicht das Suchen nach Jobs, das Speichern von Stellenanzeigen, das Hinzufügen persönlicher Notizen und das Verfolgen des Bewerbungsstatus.

## Funktionen

- Jobsuche nach Titel, Ort, Branche und Anstellungsart (z. B. Vollzeit, Praktikum, Ausbildung)
- Speichern von Stellenanzeigen mit Status und persönlichen Notizen
- Verfolgung des Status: New, Interested, Applied, Interview, Rejected, Accepted
- Direkter Link zur Originalanzeige auf arbeitsagentur.de
- Export aller gespeicherten Jobs als CSV-Datei

## Voraussetzungen

- Python 3
- Folgende Python-Pakete: `PyQt5`, `requests`

## Installation

### 1. Python 3 installieren

Falls noch nicht vorhanden, Python 3 herunterladen und installieren von:

https://www.python.org/downloads/

Stelle sicher, dass du das Kästchen **„Add Python to PATH“** während der Installation aktivierst (besonders unter Windows).

### 2. Projekt herunterladen

Entweder lade die Release-Version herunter und entpacke sie in einen Ordner,  
ODER  
öffne ein Terminal (oder die Eingabeaufforderung) und führe folgenden Befehl aus:

```bash
git clone https://github.com/your-username/arbeitsagentur-job-tracker.git
```

### 3. Abhängigkeiten installieren

Öffne das Windows-Terminal im entpackten Ordner oder navigiere im Terminal zu diesem Ordner und tippe:

```bash
pip install -r requirements.txt
```

### 4. Programm starten

Starte das Programm ganz normal  
ODER  
führe aus:

```bash
python main.py
```

## Anwendung

- Fülle das Suchformular mit Jobtitel, Ort und optionalen Filtern aus.
- Klicke auf „Suchen“, um Ergebnisse zu laden.
- Wähle einen Job aus der Liste aus, füge Notizen hinzu oder ändere den Status.
- Klicke auf „Job speichern“, um ihn zu speichern.
- Alle gespeicherten Jobs erscheinen in der unteren Tabelle und können bearbeitet oder gelöscht werden.
- Mit „Als CSV exportieren“ kannst du deine gespeicherten Jobs in ein Tabellenformat exportieren.

## Projektdateien

- `main.py` – Hauptanwendung
- `job_data.py` – Verwaltung gespeicherter Jobs
- `saved_jobs/` – Ordner, in dem die Daten gespeichert werden
- `requirements.txt` – Python-Abhängigkeiten

## Hinweise

Dieses Tool wurde ursprünglich für den Eigengebrauch entwickelt, um Bewerbungen zu verwalten. Falls es auch für andere hilfreich ist – gerne verwenden oder verbessern!
