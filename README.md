# AI-Code-Annotator

Das AI-Code-Annotator-Projekt nutzt Azure OpenAI, um automatisiert verschiedene Aufgaben auf lokalen Dateien auszuführen. Dazu zählen unter anderem das Kommentieren von Code, das Hinzufügen von Log-Statements, das Erstellen von Unit-Tests oder das Zusammenfassen von Inhalten. Die Aufgaben sind flexibel konfigurierbar und können an spezifische Anforderungen angepasst werden.

---

## Funktionsweise

### Aufgabenverwaltung
Das System lädt Aufgaben aus einer YAML-Datei, die Systemprompts und Dateioperationen definiert. Jede Aufgabe kann auf bestimmte Dateitypen oder Muster beschränkt werden.

### Datei-Scanning
Das Tool durchsucht das angegebene Verzeichnis (`BASE_DIR`) nach Dateien, die den in `TASKS` definierten Kriterien entsprechen. Dateien werden anhand von Mustern, Dateierweiterungen und Größenbeschränkungen (<= 3MB) gefiltert.

### Batch-Verarbeitung
Das Tool verarbeitet Dateien in konfigurierbaren Batches. Dies reduziert die Belastung von Systemressourcen und ermöglicht eine gleichmäßige Verarbeitung. Die Batch-Größe kann angepasst werden, um die Verarbeitungsgeschwindigkeit zu steuern.

### Aufgabenverarbeitung
Jede Datei wird an das Azure OpenAI-Modell gesendet, das die definierten Aufgaben ausführt. Dazu gehören:
- Hinzufügen von Kommentaren
- Ergänzen von Log-Statements
- Erstellen von Unit-Tests
- Weitere Aufgaben wie Refactoring oder Datenanreicherung

Nach Abschluss wird die Datei im Index als bearbeitet markiert.

### Index-Tracking
Eine Indexdatei (`INDEX_FILE`) speichert den Bearbeitungsstatus von Dateien. Dadurch werden bereits verarbeitete Dateien bei späteren Durchläufen übersprungen.

---

## Schnelleinstieg

1. **Docker Compose verwenden**  
   Kopiere die folgende Compose-Datei in dein Projekt und passe sie bei Bedarf an:

   ```yaml
   version: "3.9"
   
   # This version uses a local build of the image
   services:
      documentation:
         build: .
         container_name: ai-code-annotator
         volumes:
            # Pfad zum Projekt, das dokumentiert werden soll
            - /Users/xxx:/app/project
            # Spezifisches Mount für die tasks_and_prompts.yaml (nur anzugeben, wenn du spezifische Tasks, Dateifilter oder eigene Aufgaben verwenden willst)
            # - /Users/XXXX/tasks_and_prompts.yaml:/app/tasks_and_prompts.yaml
         environment:
            - BASE_DIR=/app/project
            # Wähle einen für dich passenden Task aus (siehe tasks_and_prompts.yaml)
            - TASKS=documentation
            # Azure OpenAI API Key (siehe Bitwarden AI Collection)
            - AZURE_OPENAI_API_KEY=xxx
         restart: "no"
   ```

   > **Hinweis**: Passe den Pfad `/Users/xxx` an dein lokales Dateisystem an.

2. **Container starten**  
   ```bash
   docker compose up
   ```
   Der Container verarbeitet die Dateien im angegebenen Verzeichnis.

---

## Wiederholte Ausführung

Wenn du das Skript erneut auf dieselben Dateien anwenden willst (z.B. nachdem du Änderungen vorgenommen hast), musst du **die bestehende Index-Datei löschen** (z.B. `/Users/XXX/project_index.json`), damit alle Dateien neu bearbeitet werden.

---

## Lokale Entwicklung

### Abhängigkeiten installieren

```bash
python3 -m venv venv
source ./venv/bin/activate 
pip install -r requirements.txt
```

### `.env`-Datei erstellen

```bash
cp .env.sample .env
```
Passe die Werte in der `.env`-Datei an (z. B. `BASE_DIR` und `AZURE_OPENAI_API_KEY`).

### Skript ausführen

```bash
python3 main.py
```

---

## Features

- **Batch-Verarbeitung**: Dateien werden in Batches verarbeitet, um die Systemressourcen effizient zu nutzen.
- **Flexibles Aufgabenmanagement**: Aufgaben wie Dokumentation, Logging oder Unit-Tests können in einer YAML-Datei definiert werden.
- **Index-Tracking**: Verhindert doppelte Bearbeitung bereits verarbeiteter Dateien.
- **Azure OpenAI Integration**: Nutzt KI-Modelle für die Verarbeitung.
- **Asynchrone Verarbeitung**: Unterstützt parallele Verarbeitung für bessere Performance.

---

## Kerndateien und Module

- **`main.py`**: Startet die Verarbeitungspipeline.
- **`file_utils.py`**: Funktionen zum Einlesen und Filtern von Dateien.
- **`open_ai_client.py`**: Schnittstelle zur Azure OpenAI API.
- **`process_files.py`**: Logik für die Verarbeitung von Dateien.
- **`processing_index.py`**: Verwaltung des Bearbeitungsstatus.
- **`task_and_prompt_manager.py`**: Laden und Verwalten von Aufgaben und Prompts.

---

## Double Checker for AI-Documentation

Dieses Skript prüft Änderungen in einem Git-Repository und erkennt, ob nur Kommentare oder Formatierungen geändert wurden. Falls Code-Änderungen festgestellt werden, können diese zurückgesetzt werden.

```bash
python3 double-check-documentation-changes.py
```

### Funktionsweise
1. Analysiert geänderte Dateien im Git-Repository.
2. Prüft, ob Änderungen nur Kommentare oder Formatierungen betreffen.
3. Erkennt Code-Änderungen und setzt diese bei Bedarf zurück.

### Konfigurationsoptionen
- **`DRY_RUN`**: Keine Änderungen vornehmen, nur protokollieren.
- **`USE_LLM_ANALYSIS`**: Nutzt Azure OpenAI für detaillierte Analysen.