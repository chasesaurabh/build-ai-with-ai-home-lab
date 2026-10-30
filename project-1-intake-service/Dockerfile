FROM python:3.12.16-slim-trixie@sha256:8523d6abeb48ceae0b7240d30c5808fc26cb79c1a635bacdf19cf3baecfbec07 AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

FROM base AS test
COPY requirements.txt requirements-dev.txt constraints.txt ./
RUN python -m pip install --no-cache-dir --only-binary=:all: pip==26.2.1 \
    && python -m pip install --no-cache-dir --only-binary=:all: -r requirements-dev.txt
COPY app ./app
COPY tests ./tests
COPY evals ./evals
CMD ["python", "-m", "pytest", "-q"]

FROM base AS runtime
COPY requirements.txt constraints.txt ./
RUN python -m pip install --no-cache-dir --only-binary=:all: pip==26.2.1 \
    && python -m pip install --no-cache-dir --only-binary=:all: -r requirements.txt \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app
COPY --chown=app:app app ./app
USER app
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=5 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
