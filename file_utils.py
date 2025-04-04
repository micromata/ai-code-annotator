import os
import re
import aiofiles
import chardet
import logging

async def read_file_safely(file_path):
    """Read file content safely, detecting encoding if needed."""
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            return await file.read()
    except UnicodeDecodeError:
        async with aiofiles.open(file_path, "rb") as file:
            raw_data = await file.read()
            detected = chardet.detect(raw_data)
            encoding = detected.get("encoding", "utf-8") or "utf-8"
            return raw_data.decode(encoding, errors="ignore")

def get_file_list(base_dir, extensions, ignored_dirs, file_pattern, max_size=3 * 1024 * 1024):
    """Recursively fetch files matching the given criteria."""
    file_paths = []
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]  # Ignore specified directories
        for file in files:
            filepath = os.path.join(root, file)
            if any(file.endswith(ext) for ext in extensions) and re.match(file_pattern, file):
                if os.path.getsize(filepath) <= max_size:
                    file_paths.append(filepath)
    return file_paths

def filter_files_exceeding_token_limit(file_paths, tokenizer, max_tokens, token_rate_limit):
    """Filter files exceeding the token limit and calculate total token count."""
    filtered_files = []
    files_over_limit = 0
    total_tokens = 0

    for filepath in file_paths:
        with open(filepath, "r", encoding="utf-8") as file:
            file_content = file.read()

        input_tokens = len(tokenizer.encode(file_content))

        if input_tokens <= max_tokens:
            filtered_files.append(filepath)
            total_tokens += input_tokens
        else:
            files_over_limit += 1

    logging.info(f"Number of files exceeding the token limit: {files_over_limit}")
    logging.info(f"Total number of tokens to be processed upfront: {total_tokens}")

    estimated_time_minutes = total_tokens / token_rate_limit
    estimated_time_seconds = estimated_time_minutes * 60
    logging.info(
        f"Estimated time based on a quota of {token_rate_limit} tokens/minute: "
        f"{estimated_time_minutes:.2f} minutes ({estimated_time_seconds:.2f} seconds)"
    )

    return filtered_files
