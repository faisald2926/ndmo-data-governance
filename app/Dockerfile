FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal; psycopg[binary] ships its own libpq.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Tables are created on startup; then serve the API.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
