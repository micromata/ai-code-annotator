# AI-Code-Annotator

The AI-Code-Annotator project utilizes Azure OpenAI to automatically execute various tasks on local files. These include commenting on code, adding log statements, creating unit tests, or summarizing content. The tasks are flexibly configurable and can be tailored to specific requirements.

---

## Functionality

### Task Management

The system loads tasks from a YAML file that defines system prompts and file operations. Each task can be restricted to specific file types or patterns.

### File Scanning

The tool scans the specified directory (`BASE_DIR`) for files that match the criteria defined in `TASKS`. Files are filtered based on patterns, file extensions, and size limitations (<= 3MB).

### Batch Processing

The tool processes files in configurable batches. This reduces the load on system resources and enables consistent processing. The batch size can be adjusted to control processing speed.

### Task Execution

Each file is sent to the Azure OpenAI model, which performs the defined tasks. These include:
- Adding comments
- Adding log statements
- Creating unit tests
- Additional tasks such as refactoring or data enrichment

Once completed, the file is marked as processed in the index.

### Index Tracking

An index file (`INDEX_FILE`) stores the processing status of files. This ensures that already processed files are skipped in later runs.

---

## Quick Start

1. **Use Docker Compose**

   Copy the following Compose file into your project and adjust it if necessary:

   ```yaml
   version: "3.9" # This version uses a local build of the image
   services:
     documentation:
       build: .
       container_name: ai-code-annotator
       volumes:
         # Path to the project to be documented
         - /Users/xxx:/app/project
         # Specific mount for tasks_and_prompts.yaml (specify only if you want to use specific tasks, file filters, or custom tasks)
         # - /Users/XXXX/tasks_and_prompts.yaml:/app/tasks_and_prompts.yaml
       environment:
         - BASE_DIR=/app/project # Choose a task suitable for you (see tasks_and_prompts.yaml)
         - TASKS=documentation
         # Azure OpenAI API Key (see Bitwarden AI Collection)
         - AZURE_OPENAI_API_KEY=xxx
       restart: "no"
   ```

   > **Note**: Adjust the path `/Users/xxx` to your local file system.

2. **Start Container**

   ```bash
   docker compose up
   ```

   The container processes the files in the specified directory.

---

## Repeated Execution

If you want to reapply the script to the same files (e.g., after making modifications), you must **delete the existing index file** (e.g., `/Users/XXX/project_index.json`) so all files are reprocessed.

---

## Local Development

### Install Dependencies

```bash
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

### Create `.env` File

```bash
cp .env.sample .env
```

Adjust the values in the `.env` file (e.g., `BASE_DIR` and `AZURE_OPENAI_API_KEY`).

### Run Script

```bash
python3 main.py
```

---

## Features

- **Batch Processing**: Files are processed in batches to efficiently use system resources.
- **Flexible Task Management**: Tasks like documentation, logging, or unit tests can be defined in a YAML file.
- **Index Tracking**: Prevents duplicate processing of already-processed files.
- **Azure OpenAI Integration**: Utilizes AI models for processing.
- **Asynchronous Processing**: Supports parallel processing for better performance.

---

## Core Files and Modules

- **`main.py`**: Initiates the processing pipeline.
- **`file_utils.py`**: Functions for reading and filtering files.
- **`open_ai_client.py`**: Interface to the Azure OpenAI API.
- **`process_files.py`**: Logic for processing files.
- **`processing_index.py`**: Management of processing status.
- **`task_and_prompt_manager.py`**: Loading and managing tasks and prompts.

---

## Double Checker for AI-Documentation

This script verifies changes in a Git repository and detects whether only comments or formatting have been altered. If code changes are identified, they can be reverted.

```bash
python3 double-check-documentation-changes.py
```

### Functionality

1. Analyzes changed files in the Git repository.
2. Checks whether changes only concern comments or formatting.
3. Detects code changes and reverts them if necessary.

### Configuration Options

- **`DRY_RUN`**: Do not make any changes, only log them.
- **`USE_LLM_ANALYSIS`**: Uses Azure OpenAI for detailed analysis.