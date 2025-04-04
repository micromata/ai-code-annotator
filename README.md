# AI-Code-Annotator

Das AI-Code-Annotator-Projekt nutzt Azure OpenAI, um automatisch verschiedene Aufgaben auf lokalen Dateien auszuführen. Diese Aufgaben können weit über das Hinzufügen von Kommentaren hinausgehen und sind flexibel konfigurierbar. Das System kann beispielsweise dazu verwendet werden, Code zu dokumentieren, Log-Statements hinzuzufügen, Inhalte zusammenzufassen oder Unit-Tests zu erstellen.

## Funktionsweise
### Aufgabenverwaltung:
Das System lädt und verwaltet Aufgaben, die in einer YAML-Datei definiert sind. Jede Aufgabe kann spezifische Systemprompts und Dateioperationen umfassen.

### Datei Scannen und Einlesen:
Das Tool durchforstet das angegebene Verzeichnis (BASE_DIR) nach Dateien, die den in TASKS definierten Aufgaben entsprechen und die festgelegten Dateierweiterungen besitzen.
Dateien werden identifiziert und auf Basis von Mustern oder Größenbeschränkungen (<= 3MB) zur Verarbeitung ausgewählt.

### Aufgabenverarbeitung:
Jede ausgewählte Datei wird an das Azure OpenAI-Modell gesendet, welches die konfigurierten Aufgaben durchführt. Dazu gehören:
- Kommentierung von Code
- Hinzufügen von Log-Statements
- Inhaltliche Zusammenfassung
- Erstellen von Unit-Tests
- beliebige weitere Aufgaben (z.B. Code-Refactoring)

**Die Aufgabe wird nach Beendigung im Index als bearbeitet protokolliert.**

### Index-Tracking:
Eine Indexdatei (INDEX_FILE) steht bereit, um abgeschlossene Aufgaben zu protokollieren, sodass Dateien bei zukünftigen Durchläufen nicht erneut bearbeitet werden.

---

## Schnelleinstieg

Wenn du keinen Änderungen an den Prompts und Dateifiltern vornehmen möchtest, kannst du das Skript einfach ausführen, indem du die folgenden Schritte befolgst:

1. **Docker Compose verwenden**
   Kopiere die folgende Compose-Datei in deine Umgebung und passe sie bei Bedarf an:

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

   > **Hinweis**: Passe den Projektpfad (`/Users/XXX`) an dein lokales Dateisystem an.
   
2. **Container starten**  
   Wechsle in das Verzeichnis, in dem deine `docker-compose.yml` liegt, und führe folgende Befehle aus:
   ```bash
   docker compose up
   ```
   Der Container startet, liest die Dateien im angegebenen Projektordner ein und kommentiert sie.

---

## Wiederholte Ausführung

Wenn du das Skript erneut auf dieselben Dateien anwenden willst (z.B. nachdem du Änderungen vorgenommen hast), musst du **die bestehende Index-Datei löschen** (z.B. `/Users/XXX/project_index.json`), damit alle Dateien neu bearbeitet werden.

---

## Lokale Entwicklung

### Install dependencies

```bash
python3 -m venv venv
source ./venv/bin/activate 
pip install -r requirements.txt
```

### Kopie der .env anlegen

```bash
cp .env.sample .env
```
Anschließend die Werte in der `.env` anpassen (insbesondere `BASE_DIR` und `AZURE_OPENAI_API_KEY`).

### Run Script

```bash
python3 main.py
```

### Kerndateien und Module
- main.py: Hauptskript zur Initialisierung der asynchronen Aufgabenverarbeitung.
- file_utils.py: Hilfsfunktionen für das sichere Einlesen und Filtern von Dateien.
- open_ai_client.py: API-Schnittstelle zur Interaktion mit Azure OpenAI.
- process_files.py: Kernlogik für die Verarbeitungspipeline.
- processing_index.py: Verwaltung und Aktualisierung des Bearbeitungsindex der Dateien.
- task_and_prompt_manager.py: Laden und Organisieren von Aufgaben und Systemprompts.

_AI generierte README_

# Double Checker for AI-Documentation
Dieses Skript analysiert Änderungen in einem Git-Repository und entscheidet, ob nur Kommentare oder Formatierungen geändert wurden oder ob tatsächlich Code-Modifikationen vorliegen. Falls Code-Änderungen festgestellt werden, werden diese automatisch zurückgesetzt.

Hilfreich, nachdem man in einem großen Repo alle Datein vom LLM mit Kommentaren versehen hat, da hierbei durch das LLM versehentliche Code-Änderungen gemacht werden können.

```bash
python3 double-check-documentation-changes.py
```

*Hinweis:* Das BASE_DIR muss in der .env-Datei angegeben werden und für dieses Skript immer auf das GIT Root Verzeichnis des jeweiligen Projekts verweisen!

## Funktionsweise
1. Ermittelt geänderte Dateien im Git-Repository.
2. Analysiert den Git-Diff der Dateien:
3. Falls nur Kommentare oder Formatierungen geändert wurden, bleiben die Änderungen bestehen.
4. Falls Code geändert wurde, wird dies erkannt und die Datei kann zurückgesetzt werden.
5. Falls notwendig, nutzt das Skript ein Azure OpenAI-Modell zur weiteren Analyse.

## Konfigurationsoptionen
- **DRY_RUN**: Falls aktiviert, werden keine Änderungen an Dateien vorgenommen, sondern nur protokolliert. (Empfohlen für den ersten Durchlauf, danach False setzen)
- **USE_LLM_ANALYSIS**: Falls aktiviert, wird Azure OpenAI genutzt, um unklare Änderungen zu analysieren. (Empfohlen für deutlich bessere Genauigkeit!)