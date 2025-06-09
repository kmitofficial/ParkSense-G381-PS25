FROM python:3.9-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------
FROM python:3.9-slim as runtime

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app.py .
COPY best.pt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Use Python to handle the port logic
CMD ["sh", "-c", "python -c \"from app import app; import os; app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))\""]