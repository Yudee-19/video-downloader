# Backend Dockerfile for FastAPI + yt-dlp
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
  ffmpeg \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure cookies.txt has proper permissions
RUN chmod 644 /app/cookies.txt

# Create directory for video storage
RUN mkdir -p /app/tmp_videos

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
