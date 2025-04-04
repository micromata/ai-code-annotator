import os
import re
import logging

from openai import AsyncAzureOpenAI

class AzureOpenAIClient:
    def __init__(self):
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not api_key:
            raise ValueError("***ERROR*** Missing environment variable: AZURE_OPENAI_API_KEY. Check your .env file or environment settings.")

        model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        api_version = os.getenv("AZURE_API_VERSION")
        max_retries = 5

        logging.info("\n===============================")
        logging.info("     Azure AI Client Setup")
        logging.info("===============================")
        logging.info("Azure OpenAI API Key: xxxx")
        logging.info(f"Azure Endpoint: {azure_endpoint}")
        logging.info(f"Azure Deployment: {azure_deployment}")
        logging.info(f"Model Name: {model_name}")
        logging.info(f"API Version: {api_version}")
        logging.info(f"Max Retries: {max_retries}")
        logging.info("===============================\n")

        self.client = AsyncAzureOpenAI(
            azure_endpoint=azure_endpoint,
            azure_deployment=azure_deployment,
            api_key=api_key,
            api_version=api_version,
            max_retries=max_retries
        )
        self.model_name = model_name

    async def generate_code_response(self, system_prompt, user_input, tokenizer):
        """Send prompt to OpenAI, get response, and clean the output."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
        response = await self.client.chat.completions.create(
            model=self.model_name, messages=messages
        )
        llm_response = response.choices[0].message.content.strip()

        input_tokens = sum(
            [len(tokenizer.encode(message["content"])) for message in messages]
        )
        output_tokens = len(tokenizer.encode(llm_response))
        total_tokens = input_tokens + output_tokens

        cleaned_text = self._clean_response(llm_response)
        return cleaned_text, total_tokens

    @staticmethod
    def _clean_response(response_text):
        """Cleans response by removing Markdown code blocks and ensuring newline at the end."""

        # Remove surrounding triple backtick blocks with "javascript" or any other language
        cleaned_text = re.sub(r"^```[a-zA-Z0-9]*\n(.*?)\n```$", r"\1", response_text, flags=re.DOTALL).strip()

        # Ensure a newline at the end
        if not cleaned_text.endswith("\n"):
            cleaned_text += "\n"

        return cleaned_text
