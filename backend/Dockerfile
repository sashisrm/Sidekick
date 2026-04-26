FROM python:3.12-slim

WORKDIR /app

# System deps for playwright + pdfplumber
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=300 -r requirements.txt

# Install playwright browser dependencies manually (--with-deps fails on Debian trixie)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    fonts-liberation \
    fonts-unifont \
    && rm -rf /var/lib/apt/lists/*

RUN playwright install chromium

COPY . .

EXPOSE 8000
