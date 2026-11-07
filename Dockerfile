FROM python:3.11-slim
WORKDIR /app
COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt
COPY server server
COPY web web
WORKDIR /app/server
ENV DATABASE_URL=sqlite:///./data/dajeong.db AUDIO_DIR=./data/audio RUN_JOBS=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
