FROM python:3.11-slim

# Install system deps
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    git \
    aria2 \
    unzip \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Deno
RUN curl -fsSL https://deno.land/install.sh | sh
ENV DENO_INSTALL="/root/.deno"
ENV PATH="${DENO_INSTALL}/bin:${PATH}"

# Force yt-dlp to use Deno engine
ENV YT_DLP_JS_ENGINE=deno

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Optional — ensure cookies.txt readable
RUN chmod 644 /app/cookies.txt || true

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
