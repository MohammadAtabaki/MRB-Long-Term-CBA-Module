FROM python:3.11-slim

WORKDIR /app

# (Optional but handy) system deps for building wheels from source
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy the project
COPY pyproject.toml ./
COPY poetry.lock* ./
COPY src ./src
COPY demo ./demo

# Install the package
RUN pip install --no-cache-dir -U pip \
 && pip install --no-cache-dir .

# Run the demo script
