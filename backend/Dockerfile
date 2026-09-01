# Backend image — FastAPI + LangGraph + Sentence-Transformers.
# Note: sentence-transformers pulls in torch, so this image is large and the
# first build is slow. The all-MiniLM-L6-v2 embedding model downloads on the
# first alignment call (needs network once) and is then cached in the layer's
# HF cache for the container's lifetime.
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/data/.hf-cache

WORKDIR /app

# libgomp1 is required by torch/scikit-learn at runtime; curl powers the healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app

# SQLite app DB + LangGraph checkpoint DB live on a mounted volume (see compose).
ENV APP_ENV=production \
    LOG_LEVEL=INFO \
    DATABASE_URL=sqlite:////data/hackathon_planner.db \
    CHECKPOINT_DB_PATH=/data/checkpoints.sqlite
RUN mkdir -p /data

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
