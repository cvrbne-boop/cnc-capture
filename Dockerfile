FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# instalace systémových build-dep a nástrojů potřebných pro některé pip balíčky
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     build-essential \
     gcc \
     libpq-dev \
     libssl-dev \
     libffi-dev \
     libjpeg-dev \
     zlib1g-dev \
     cargo \
     git \
     ca-certificates \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# upgrade pip/setuptools/wheel -> častý zdroj problémů s wheel
RUN pip install --upgrade pip setuptools wheel

# nainstaluj požadavky
RUN pip install --no-cache-dir -r requirements.txt

# zkopíruj aplikaci
COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

