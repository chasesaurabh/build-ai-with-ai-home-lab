FROM python:3.12.16-slim-trixie@sha256:8523d6abeb48ceae0b7240d30c5808fc26cb79c1a635bacdf19cf3baecfbec07 AS test

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.txt requirements-dev.txt constraints.txt ./
RUN python -m pip install --no-cache-dir --only-binary=:all: pip==26.2.1 \
    && python -m pip install --no-cache-dir --only-binary=:all: -r requirements-dev.txt
COPY app ./app
COPY fixtures ./fixtures
COPY fixtures-holdout ./fixtures-holdout
COPY evals ./evals
COPY tests ./tests
CMD ["python", "-m", "pytest", "-q"]

FROM python:3.12.16-slim-trixie@sha256:8523d6abeb48ceae0b7240d30c5808fc26cb79c1a635bacdf19cf3baecfbec07 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --system app && useradd --system --gid app --home-dir /nonexistent --shell /usr/sbin/nologin app
WORKDIR /app
COPY requirements.txt constraints.txt ./
RUN python -m pip install --no-cache-dir --only-binary=:all: pip==26.2.1 \
    && python -m pip install --no-cache-dir --only-binary=:all: -r requirements.txt
COPY app ./app
COPY fixtures ./fixtures
RUN chown -R app:app /app
USER app
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
