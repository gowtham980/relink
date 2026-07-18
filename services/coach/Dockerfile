FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8787 \
    RELINK_LLM_PROVIDER=ollama \
    RELINK_LLM_FALLBACK=vertex \
    RELINK_ALLOW_MOCK_FALLBACK=0 \
    OLLAMA_API_BASE=https://ollama.com/v1

COPY pyproject.toml ./
COPY relink_coach ./relink_coach
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir .

EXPOSE 8787
CMD exec uvicorn relink_coach.main:app --host 0.0.0.0 --port ${PORT}
