# 1. Verwende Python 3.12 im slim-Variant als Basis
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

# 2. Lege das Arbeitsverzeichnis im Container fest
WORKDIR /app

# 3. Kopiere die requirements.txt ins Image
COPY requirements.txt .

# 4. Installiere alle Abhängigkeiten
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Kopiere den restlichen Code (z. B. main.py) ins Image
COPY *.py .
COPY tasks_and_prompts.yaml .

# 6. Standard-Kommando: Führe main.py aus
ENTRYPOINT ["python", "main.py"]
