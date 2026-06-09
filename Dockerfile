# Use Python 3.11 slim image for a lightweight, production-ready environment
FROM python:3.11-slim

# Prevent Python from writing pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set the working directory in the container
WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Set default entrypoint for CLI execution
ENTRYPOINT ["python", "main.py"]
