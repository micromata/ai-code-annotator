import asyncio
import os
import aiofiles
import time
import tiktoken
import logging

from file_utils import read_file_safely, get_file_list, filter_files_exceeding_token_limit
from open_ai_client import AzureOpenAIClient
from processing_index import filter_files_already_processed, ProcessingIndex
from task_and_prompt_manager import TaskAndPromptManager, get_prompt, get_transformations

TOKEN_RATE_LIMIT = 450000
MAX_FILE_TOKENS = 12000

async def run_processing_pipeline(batch_size=40):
    """Run the entire processing pipeline asynchronously in batches."""
    # Initialize Azure OpenAI Client, Task Manager and Tokenizer
    client = AzureOpenAIClient()
    task_and_prompt_manager = TaskAndPromptManager()
    tokenizer = tiktoken.get_encoding("cl100k_base")
    base_dir, ignored_dirs, task_names = load_base_config()

    for task_name, task in task_and_prompt_manager.tasks.items():
        if task_name not in task_names:
            continue
        index_file, file_name_pattern, file_extensions = await load_conf_for_task(base_dir, task_name, task)
        processing_index = ProcessingIndex(index_file)

        input_file_paths = get_file_list(base_dir, file_extensions, ignored_dirs, file_name_pattern)
        input_file_paths = filter_files_already_processed(input_file_paths, processing_index)
        input_file_paths = filter_files_exceeding_token_limit(input_file_paths, tokenizer, MAX_FILE_TOKENS, TOKEN_RATE_LIMIT)

        print_configuration(base_dir, file_extensions, file_name_pattern, ignored_dirs, index_file, task_name, input_file_paths)

        if not input_file_paths:
            logging.info(f"No files to process for task '{task_name}'.")
            return

        # Warn user and wait before starting
        warn_user_and_wait_before_start(input_file_paths, task_name, base_dir)

        logging.info("=" * 100)
        logging.info(f"Start processing '{task_name}'...")
        total_time = await run_in_batches(batch_size, client, input_file_paths, processing_index, task_name, task, tokenizer)
        logging.info(f"Finished processing '{task_name}' in {total_time:.2f}s")

    logging.info("All Done!")
    logging.info("Exiting...")

async def run_in_batches(batch_size, client, input_file_paths, processing_index, task_name, task, tokenizer):
    # Split the list of files into batches
    batches = [input_file_paths[i:i + batch_size] for i in range(0, len(input_file_paths), batch_size)]
    start_total_time = time.time()
    for batch_index, batch in enumerate(batches):
        batch_number = batch_index + 1
        logging.info(f"Batch {batch_number}: Start ({batch_number}/{len(batches)}) - {task_name}")

        # Use asyncio.gather to run tasks concurrently for the current batch
        results = await asyncio.gather(
            *(process_file(filepath, client, task, tokenizer, processing_index) for filepath in batch))

        update_times, token_counts = zip(*results)

        update_times = [t for t in update_times if t is not None]
        token_counts = [tokens for tokens in token_counts if tokens is not None]

        total_files = len(update_times)
        average_time = sum(update_times) / total_files if total_files > 0 else 0
        total_tokens_processed = sum(token_counts)

        logging.info(
            f"Batch {batch_number}: Done | Avg Time: {average_time:.2f}s | "
            f"Files: {total_files} | Tokens: {total_tokens_processed}"
        )
    end_total_time = time.time()
    total_time = end_total_time - start_total_time
    return total_time

def warn_user_and_wait_before_start(input_file_paths, task_name, base_dir):
    # -----------------------------
    # Warnung vor dem Start
    # -----------------------------
    logging.info("*" * 70)
    logging.info("!!!!!!!!!!!!!!!!   W A R N I N G   !!!!!!!!!!!!!!!!")
    logging.info(f"Task '{task_name}' will process {len(input_file_paths)} files in that directory.\n")

    if base_dir.lower().startswith("/app/project"):
        logging.info("Running in Docker container, waiting for 20 seconds...")
        logging.info("Kill the container, if you want to abort!!!")
        time.sleep(20)
    else:
        input("Press Enter to continue or CMD + C to abort...")

async def process_file(filepath, client, task, tokenizer, processing_index):
    """Process a file asynchronously, send it to OpenAI, and save output."""
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[-1]
    system_prompt = get_prompt(task, ext)

    # Read file content
    file_content = await read_file_safely(filepath)

    # Send request to OpenAI
    start_time = time.time()
    new_code, total_tokens = await client.generate_code_response(system_prompt, file_content, tokenizer)
    update_time = time.time() - start_time

    # Modify file paths based on transformation rules
    output_path = filepath
    for rule in get_transformations(task):
        output_path = output_path.replace(rule["match"], rule["replace"])

    try:
        # If output path is different, create the directory if it doesn't exist
        output_directory = os.path.dirname(output_path)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Save output in a new file or overwrite existing file
        async with aiofiles.open(output_path, "w", encoding="utf-8") as file:
            await file.write(new_code)
        # Update processing index
        await processing_index.mark_file_processed(filepath)
    except Exception as e:
        logging.error(f'***ERROR*** Error saving file "{output_path}": {e}')

    logging.info(f'"{filename}": Update time {update_time:.2f} seconds for {total_tokens} tokens')
    return update_time, total_tokens

def load_base_config():
    # Load configuration from environment variables
    base_dir = os.getenv("BASE_DIR", "/app/project")
    if not base_dir.endswith("/"):
        base_dir += "/"
    ignored_dirs = os.getenv("IGNORED_DIRS", "node_modules;venv;.venv;.git;__pycache__;.idea;.vscode;target;build;coverage;lib").split(";")
    task_names = os.getenv("TASKS").split(";")
    if not task_names:
        raise ValueError("***ERROR*** Missing environment variable: TASKS. Check your .env file or environment settings.")

    return base_dir, ignored_dirs, task_names

async def load_conf_for_task(base_dir, task_name, task):
    index_file = base_dir + task_name + "_" + os.getenv("INDEX_FILE", "project_index.json")
    file_name_pattern = task.get("file_name_pattern", ".*")
    file_extensions = [f".{ext}" if not ext.startswith(".") else ext for ext in task.get("file_extensions").split(";")]
    if not file_extensions:
            raise ValueError(f"***ERROR*** Missing file_extensions for task '{task_name}. Check your yaml file.")
    return index_file, file_name_pattern, file_extensions

def print_configuration(base_dir, file_extensions, file_name_pattern, ignored_dirs, index_file, task_name, input_file_paths):
    # Konfigurationsübersicht ausgeben
    logging.info("\n===============================")
    logging.info(f"   {task_name} CONFIGURATION")
    logging.info("===============================")
    logging.info(f"BASE_DIR: {base_dir}")
    logging.info(f"INDEX_FILE: {index_file}")
    logging.info(f"FILE_EXTENSIONS: {file_extensions}")
    logging.info(f"FILE_NAME_PATTERN: {file_name_pattern}")
    logging.info(f"IGNORED_DIRS: {ignored_dirs}\n")
    logging.info(f"In total {len(input_file_paths)} files found for task '{task_name}'.")
    logging.info(f"The first 10 paths:\n{chr(10).join(input_file_paths[:10])}\n...")
    logging.info("===============================\n")

