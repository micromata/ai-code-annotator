import yaml
import logging


class TaskAndPromptManager:
    """Manages loading and retrieving tasks and system prompts efficiently."""
    tasks = {}

    def __init__(self, task_file="tasks_and_prompts.yaml"):
        """Initialize the PromptManager and load prompts into memory."""
        self._task_file = task_file
        self._load_tasks_and_prompts()

    def _load_tasks_and_prompts(self):
        """Load tasks from YAML file and return a dictionary of task configurations."""
        try:
            with open(self._task_file, "r", encoding="utf-8") as file:
                task_data = yaml.safe_load(file)
                self.tasks = task_data.get("tasks", {})
        except Exception as e:
            logging.error(f"Error loading task file '{self._task_file}': {e}")
            raise ValueError(f"Error loading task file '{self._task_file}': {e}")

        logging.info("\n===============================")
        logging.info("     SYSTEM-PROMPTS LOADED")
        logging.info("===============================")
        for task_name, task in self.tasks.items():
            logging.info(f"*** Task '{task_name}' ***")
            for ext, prompt in task.get("prompts", {}).items():
                logging.info(f"Extension '{ext}': {prompt[:120].replace(chr(10), ' ')}...")
            logging.info("\n")
        logging.info("===============================\n")


def get_prompt(task, file_extension):
    """Get the appropriate prompt for a given file extension."""
    prompts = task.get("prompts")
    prompt = prompts.get(file_extension.lstrip('.'), prompts.get("*"))
    if prompt is None:
        print(f"Kein System-Prompt für Task '{task}' mit Dateiendung '{file_extension}' gefunden.")
        exit(1)
    return prompt

def get_transformations(task):
    """Get the appropriate transformations (if any) for a given task."""
    return task.get("path_transformations", [])
