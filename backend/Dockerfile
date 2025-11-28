FROM python:3.11-slim

# základní nastavení
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# nainstalujeme systémové nástroje a knihovny potřebné pro kompilaci některých pip balíčků
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    cargo \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# zkopíruj requirements a aktualizuj pip/wheel/setuptools před instalací
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# zkopíruj aplikaci
COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

