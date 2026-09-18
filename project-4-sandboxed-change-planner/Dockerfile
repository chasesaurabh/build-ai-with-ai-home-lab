FROM python:3.12.14-slim-trixie AS test

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN python -m pip install --no-cache-dir -r requirements-dev.txt
COPY app ./app
COPY fixtures ./fixtures
COPY fixtures-holdout ./fixtures-holdout
COPY evals ./evals
COPY sandbox ./sandbox
COPY tests ./tests
CMD ["python", "-m", "pytest", "-q"]

FROM python:3.12.14-slim-trixie AS sandbox-runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --system app && useradd --system --gid app --home-dir /nonexistent --shell /usr/sbin/nologin app
WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY sandbox ./sandbox
RUN chown -R app:app /app
USER app
EXPOSE 8000
CMD ["python", "-m", "sandbox.server"]
