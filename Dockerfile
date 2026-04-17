FROM mcr.microsoft.com/playwright/python:v1.51.0-jammy

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Europe/London

WORKDIR /app

# Python dependencies — separate layer so rebuilds stay cheap.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# If you switch MESSAGING_PLATFORM to whatsapp, uncomment to install Node + deps:
# RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
#     apt-get install -y --no-install-recommends nodejs && \
#     rm -rf /var/lib/apt/lists/*
# COPY package.json package-lock.json* ./
# RUN npm ci --omit=dev

# App source.
COPY . .

# Create runtime directories. These get masked by volume mounts in production.
RUN mkdir -p /app/session /app/data /app/.wwebjs_auth

# Default command — docker-compose overrides this per service.
CMD ["python", "scheduler.py"]
