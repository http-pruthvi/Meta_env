# Use a lightweight Python base image
FROM python:3.11-slim

# Set environment variables for non-interactive installs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependencies first for caching
COPY pyproject.toml uv.lock ./

# Install project dependencies using uv
RUN uv sync --no-dev --no-install-project

# Copy the rest of the application
COPY . .

# Install the project itself in editable mode so 'server' script is available
RUN pip install -e .

# Expose the standard port for Hugging Face Spaces
EXPOSE 7860

# Run the project script 'server'
CMD ["server"]
