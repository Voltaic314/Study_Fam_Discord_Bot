FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Runtime state (DB, cookies, downloads, transcripts) lives here.
# Mount a host volume to /app/data so files persist across container restarts.
RUN mkdir -p /app/data/session_cookies
ENV DATA_DIR=/app/data

CMD ["python", "src/study_bot_client.py"]
