FROM python:3.14-alpine

WORKDIR /app

# System deps:
# - sqlite: sqlite3 CLI (serve per .recover/.dump)
# - openssl/libffi: runtime per paramiko/cryptography
# - build deps: per compilare wheels su alpine quando necessario
RUN apk add --no-cache \
    sqlite sqlite-libs \
    openssl \
    libffi \
    && apk add --no-cache --virtual .build-deps \
    build-base \
    openssl-dev \
    libffi-dev \
    cargo \
    rust

# Install Poetry (stessa versione che ha generato il lock)
ENV POETRY_VERSION=2.3.2 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Copy only dependency files first (cache friendly)
COPY pyproject.toml poetry.lock ./

# Install only main deps; do not install the project package itself
RUN poetry install --no-root --without dev --no-ansi

# Copy app code
COPY . .

# Remove build deps to shrink image
RUN apk del .build-deps

# Gunicorn
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:5000", "--timeout", "600", "app:app"]