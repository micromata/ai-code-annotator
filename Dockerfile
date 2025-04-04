# 1. Use Python 3.13 in the slim variant as the base image
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

# 2. Set the working directory in the container
WORKDIR /app

# 3. Copy the requirements.txt file into the image
COPY requirements.txt .

# 4. Install all dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy the remaining code (e.g., main.py) into the image
COPY *.py .
COPY tasks_and_prompts.yaml .

# 6. Default command: Run main.py
ENTRYPOINT ["python", "main.py"]
