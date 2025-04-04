# This script integrates Azure OpenAI into an asynchronous Python environment.
# It enables the processing and documentation of local (source code) files by automatically adding comments.
#
# Functions:
# ----------
# - Reads files with specific extensions from a directory.
# - Checks the token count to comply with OpenAI API limitations.
# - Sends the content to Azure OpenAI along with an appropriate system prompt (e.g., for documentation generation).
# - Saves the response from Azure OpenAI into the original file or a new file.
# - Uses asynchronous processing to improve efficiency.

import asyncio
import logging
from dotenv import load_dotenv

from process_files import run_processing_pipeline

load_dotenv()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Starting AI-Code-Annotator.")
    asyncio.run(run_processing_pipeline())
