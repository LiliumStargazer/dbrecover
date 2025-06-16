FROM python:3.13.3-alpine3.21
WORKDIR /app
COPY . /app

# Installa sqlite3 e altre dipendenze necessarie utilizzando apk
RUN apk add --no-cache sqlite

# Installa le librerie Python necessarie
RUN pip install --no-cache-dir flask gunicorn

# Comando per avviare l'applicazione
CMD ["gunicorn", "-w", "4", "-k", "gthread", "-b", "0.0.0.0:5000", "--timeout", "600", "app:app"]