import os
import json
import aiofiles
import logging


class ProcessingIndex:
    processed_files = {}

    def __init__(self, index_file):
        """Load the index file and return a dictionary of processed files."""
        index_directory = os.path.dirname(index_file)
        if index_directory and not os.path.exists(index_directory):
            os.makedirs(index_directory)

        if os.path.exists(index_file):
            with open(index_file, "r") as f:
                try:
                    self.processed_files = json.load(f)
                except json.JSONDecodeError as e:
                    logging.error("***ERROR*** Error loading index file. Starting fresh.", e)
                    self.processed_files = {}
        self.index_file = index_file

    async def mark_file_processed(self, file_path):
        """Mark a file as processed in the index."""
        self.processed_files[file_path] = True
        async with aiofiles.open(self.index_file, "w") as f:
            await f.write(json.dumps(self.processed_files))


def filter_files_already_processed(file_paths, processing_index):
    """Filter out already processed files from the file list."""
    initial_file_count = len(file_paths)
    file_paths = [fp for fp in file_paths if not processing_index.processed_files.get(fp, False)]
    remaining_file_count = len(file_paths)

    logging.info(f"Planned {initial_file_count} files")
    logging.info(f"Total remaining files: {remaining_file_count}")
    logging.info(f"Already processed: {initial_file_count - remaining_file_count} files")

    return file_paths
