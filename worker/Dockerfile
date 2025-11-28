FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
CMD ["dramatiq", "worker.py", "--processes", "1", "--threads", "4"]
