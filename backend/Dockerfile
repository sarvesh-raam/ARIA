# Use a high-performance Python base image
FROM python:3.9-slim

# Set system environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

# Install system dependencies (Optimized for Debian Trixie/Slim)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Security: Add a non-root user (User ID 1000)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set working directory inside home
WORKDIR /home/user/app

# Copy requirements and install (as the non-root user)
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy the backend source code
COPY --chown=user . .

# Hugging Face Spaces run on port 7860 by default
EXPOSE 7860

# Start the high-performance production server
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
