# Dieses Skript dient der Integration von Azure OpenAI in eine asynchrone
# Python-Umgebung. Es ermöglicht die Verarbeitung und Dokumentation von
# lokalen (Sourcode) Dateien durch das automatische Hinzufügen von Kommentaren.
#
# Funktionen:
# -----------
# - Liest Dateien mit bestimmten Erweiterungen aus einem Verzeichnis.
# - Überprüft die Token-Anzahl, um OpenAI API-Beschränkungen einzuhalten.
# - Sendet die Inhalte an Azure OpenAI zusammen mit einem passenden Systemprompt (z.B. Dokumentationserstellung).
# - Speichert die Rückgabe von Azure OpenAI in der vorherigen Datei oder einer neuen Datei.
# - Nutzt asynchrone Verarbeitung zur Effizienzsteigerung.

import asyncio
import logging
from dotenv import load_dotenv

from process_files import run_processing_pipeline

load_dotenv()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Starte AI-Code-Annotator.")
    asyncio.run(run_processing_pipeline())
