# Use a high-performance Python base image
FROM python:3.9-slim

# Set system environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

# Install system dependencies (needed for PDF processing and ChromaDB)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source code
COPY . .

# Hugging Face Spaces run on port 7860 by default
EXPOSE 7860

# Start the high-performance production server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
