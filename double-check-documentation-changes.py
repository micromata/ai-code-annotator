import os
import subprocess
import logging
from openai import AzureOpenAI
import re
import asyncio
from dotenv import load_dotenv

from processing_index import ProcessingIndex, filter_files_already_processed

# Umgebungsvariablen aus .env laden
load_dotenv()

# Azure OpenAI Konfiguration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")

DRY_RUN = True
USE_LLM_ANALYSIS = True

BASE_DIR = os.getenv("BASE_DIR", ".")

azure_openai_client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_API_VERSION,
    max_retries=5
)


def get_modified_files():
    """Ermittelt alle Dateien im Git-Repository, die Änderungen enthalten."""
    try:
        files = subprocess.check_output(["git", "diff", "--name-only"], cwd=BASE_DIR).decode().splitlines()
        return files
    except subprocess.CalledProcessError:
        return []


def get_git_diff(filename):
    """Holt den Git-Diff für eine Datei mit minimalem Kontext."""
    try:
        diff_output = subprocess.check_output(["git", "diff", "--unified=0", filename], cwd=BASE_DIR).decode()
        return diff_output
    except subprocess.CalledProcessError:
        return ""


def is_whitespace_or_formatting_change(line):
    """Prüft, ob eine geänderte Zeile nur Formatierung (Leerzeichen/Einrückung) betrifft."""
    return re.match(r"^[+\-]\s*$", line) is not None  # Nur + oder - mit Leerzeichen


def is_comment_change(line):
    """Prüft, ob eine Zeile nur einen Kommentar enthält."""
    stripped = line[1:].strip()  # + oder - entfernen und Whitespaces entfernen
    comment_change = bool(re.match(r"^(#|//|/\*|\*|\*/|--).*", stripped))  # Unterstützt Python, Java, Kotlin, C, SQL
    if not comment_change:
        logging.debug(f"Kein Kommentar: {line}")
    return comment_change


def pre_analyze_diff(diff_output):
    """
    Führt eine Voranalyse des Diffs durch:
    1. Falls nur Kommentare/Formatierungen geändert wurden → Änderungen übernehmen
    2. Falls echter Code geändert wurde → LLM zur weiteren Analyse aufrufen
    """
    lines = [line.strip() for line in diff_output.split("\n")]
    only_comments_or_formatting = True  # Standard-Annahme
    needs_llm_analysis = False

    for line in lines:
        # Metadaten-Zeilen ignorieren
        if line.startswith("diff --git") or line.startswith("index ") or \
                line.startswith("--- ") or line.startswith("+++ ") or \
                line.startswith("@@ "):
            continue

        if line.startswith("+") or line.startswith("-"):  # Nur geänderte Zeilen prüfen
            if is_whitespace_or_formatting_change(line):
                continue  # Formatierung ignorieren

            if not is_comment_change(line):
                needs_llm_analysis = True
                only_comments_or_formatting = False

    return only_comments_or_formatting, needs_llm_analysis


def analyze_diff_with_llm(diff_output):
    """
    Nutzt Azure OpenAI LLM, um zu bestimmen, ob der Diff nur Kommentare/Formatierungen betrifft oder Code ändert.
    Antwortet ausschließlich mit "JA" oder "NEIN".
    """
    system_prompt = f"""
    Du bist ein Experte für Code-Analysen. Analysiere den folgenden Git-Diff und bestimme, ob die Änderungen nur Kommentare oder Formatierungen betreffen.

    Falls nur Kommentare/Formatierungen geändert wurden, antworte mit "JA".
    Falls Code geändert oder entfernt wurde, antworte mit "NEIN".
    Gib keine weiteren Erklärungen oder Inhalte aus.
    """
    user_prompt = f"""
    **Git-Diff:**
    ```
    {diff_output}
    ```
    """
    return generate_llm_response(system_prompt, user_prompt)


def generate_llm_response(system_prompt, user_prompt):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = azure_openai_client.chat.completions.create(
        model=AZURE_OPENAI_MODEL,
        messages=messages
    )
    return response.choices[0].message.content.strip()


def revert_code_changes(filename):
    """Setzt die gesamte Datei auf den letzten Git-Stand zurück."""
    if DRY_RUN:
        logging.info(f"Dry run: Würde {filename} zurücksetzen.")
    else:
        logging.info(f"Setze {filename} zurück...")
        subprocess.run(["git", "checkout", "--", filename], cwd=BASE_DIR)

async def process_repository(processing_index):
    """
    Führt den gesamten Ablauf aus:
    1. Dateien im Repository ermitteln
    2. Git-Diff abrufen und mit Voranalyse prüfen
    3. Falls unklar, LLM nutzen
    4. Falls nur Kommentare/Formatierungen geändert wurden → Datei im Index speichern
    5. Falls echter Code geändert wurde → Datei zurücksetzen
    """
    files = get_modified_files()
    logging.info(f"Prüfe {len(files)} Dateien im Repository:")

    files = filter_files_already_processed(files, processing_index)
    for file in files:
        logging.info(f" - {file}")

    code_changed_files = []  # Liste für Dateien mit Code-Änderungen
    for filename in files:
        diff_output = get_git_diff(filename)

        if not diff_output:
            continue  # Keine Änderungen in dieser Datei

        # Lokale Voranalyse
        only_comments_or_formatting, needs_llm_analysis = pre_analyze_diff(diff_output)

        if only_comments_or_formatting:
            logging.info(f"Nur Kommentare/Formatierung in {filename} geändert – Änderungen bleiben bestehen.")
            await processing_index.mark_file_processed(filename)  # ✅ Datei im Index speichern
            continue

        if needs_llm_analysis and USE_LLM_ANALYSIS:
            logging.info(f"Prüfe {filename} mit LLM...")
            llm_response = analyze_diff_with_llm(diff_output)
        else:
            llm_response = "NEIN"

        if llm_response == "NEIN":
            logging.info(f"Code-Änderungen in {filename} erkannt.")
            code_changed_files.append(filename)
            revert_code_changes(filename)
        else:
            logging.info(f"Nur Kommentare/Formatierung in {filename} geändert – Änderungen bleiben bestehen.")
            await processing_index.mark_file_processed(filename)  # ✅ Datei im Index speichern

    # Am Ende die Liste der betroffenen Dateien ausgeben
    if code_changed_files:
        if DRY_RUN:
            logging.info(f"{'=' * 100}\n[DRY RUN]: Folgende {len(code_changed_files)} Dateien haben Code-Änderungen:\n{chr(10).join(code_changed_files)}\n")
        else:
            logging.info(f"{'=' * 100}\nFolgende {len(code_changed_files)} Dateien wurden zurückgesetzt:\n{chr(10).join(code_changed_files)}\n")
    else:
        logging.info("\nKeine Dateien mit Code-Änderungen gefunden.\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Starte Double Checker for AI-Documentation.")
    asyncio.run(process_repository(ProcessingIndex("double_check_index.json")))
