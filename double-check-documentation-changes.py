import os
import subprocess
import logging
from openai import AzureOpenAI
import re
import asyncio
from dotenv import load_dotenv

from processing_index import ProcessingIndex, filter_files_already_processed

# Load environment variables from .env
load_dotenv()

# Azure OpenAI configuration
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
    """Retrieves all files in the Git repository that have changes."""
    try:
        files = subprocess.check_output(["git", "diff", "--name-only"], cwd=BASE_DIR).decode().splitlines()
        return files
    except subprocess.CalledProcessError:
        return []


def get_git_diff(filename):
    """Fetches the Git diff for a file with minimal context."""
    try:
        diff_output = subprocess.check_output(["git", "diff", "--unified=0", filename], cwd=BASE_DIR).decode()
        return diff_output
    except subprocess.CalledProcessError:
        return ""


def is_whitespace_or_formatting_change(line):
    """Checks if a changed line only involves formatting (whitespace/indentation)."""
    return re.match(r"^[+\-]\s*$", line) is not None  # Only + or - with whitespace


def is_comment_change(line):
    """Checks if a line only contains a comment."""
    stripped = line[1:].strip()  # Remove + or - and strip whitespace
    comment_change = bool(re.match(r"^(#|//|/\*|\*|\*/|--).*", stripped))  # Supports Python, Java, Kotlin, C, SQL
    if not comment_change:
        logging.debug(f"Not a comment: {line}")
    return comment_change


def pre_analyze_diff(diff_output):
    """
    Performs a preliminary analysis of the diff:
    1. If only comments/formatting were changed → keep changes
    2. If actual code was changed → call LLM for further analysis
    """
    lines = [line.strip() for line in diff_output.split("\n")]
    only_comments_or_formatting = True  # Default assumption
    needs_llm_analysis = False

    for line in lines:
        # Ignore metadata lines
        if line.startswith("diff --git") or line.startswith("index ") or \
                line.startswith("--- ") or line.startswith("+++ ") or \
                line.startswith("@@ "):
            continue

        if line.startswith("+") or line.startswith("-"):  # Only check changed lines
            if is_whitespace_or_formatting_change(line):
                continue  # Ignore formatting

            if not is_comment_change(line):
                needs_llm_analysis = True
                only_comments_or_formatting = False

    return only_comments_or_formatting, needs_llm_analysis


def analyze_diff_with_llm(diff_output):
    """
    Uses Azure OpenAI LLM to determine if the diff only involves comments/formatting or changes code.
    Responds exclusively with "YES" or "NO".
    """
    system_prompt = f"""
    You are an expert in code analysis. Analyze the following Git diff and determine if the changes only involve comments or formatting.

    If only comments/formatting were changed, respond with "YES".
    If code was changed or removed, respond with "NO".
    Do not provide any further explanations or content.
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
    """Reverts the entire file to the last Git state."""
    if DRY_RUN:
        logging.info(f"Dry run: Would revert {filename}.")
    else:
        logging.info(f"Reverting {filename}...")
        subprocess.run(["git", "checkout", "--", filename], cwd=BASE_DIR)

async def process_repository(processing_index):
    """
    Executes the entire workflow:
    1. Identify files in the repository
    2. Fetch Git diff and check with preliminary analysis
    3. If unclear, use LLM
    4. If only comments/formatting were changed → mark file in index
    5. If actual code was changed → revert file
    """
    files = get_modified_files()
    logging.info(f"Checking {len(files)} files in the repository:")

    files = filter_files_already_processed(files, processing_index)
    for file in files:
        logging.info(f" - {file}")

    code_changed_files = []  # List for files with code changes
    for filename in files:
        diff_output = get_git_diff(filename)

        if not diff_output:
            continue  # No changes in this file

        # Local preliminary analysis
        only_comments_or_formatting, needs_llm_analysis = pre_analyze_diff(diff_output)

        if only_comments_or_formatting:
            logging.info(f"Only comments/formatting changed in {filename} – keeping changes.")
            await processing_index.mark_file_processed(filename)  # ✅ Mark file in index
            continue

        if needs_llm_analysis and USE_LLM_ANALYSIS:
            logging.info(f"Checking {filename} with LLM...")
            llm_response = analyze_diff_with_llm(diff_output)
        else:
            llm_response = "NO"

        if llm_response == "NO":
            logging.info(f"Code changes detected in {filename}.")
            code_changed_files.append(filename)
            revert_code_changes(filename)
        else:
            logging.info(f"Only comments/formatting changed in {filename} – keeping changes.")
            await processing_index.mark_file_processed(filename)  # ✅ Mark file in index

    # Output the list of affected files at the end
    if code_changed_files:
        if DRY_RUN:
            logging.info(f"{'=' * 100}\n[DRY RUN]: The following {len(code_changed_files)} files have code changes:\n{chr(10).join(code_changed_files)}\n")
        else:
            logging.info(f"{'=' * 100}\nThe following {len(code_changed_files)} files were reverted:\n{chr(10).join(code_changed_files)}\n")
    else:
        logging.info("\nNo files with code changes found.\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Starting Double Checker for AI-Documentation.")
    asyncio.run(process_repository(ProcessingIndex("double_check_index.json")))
