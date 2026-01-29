FROM python:3.11-slim

WORKDIR /app

# Optional build deps (safe default)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Copy only what is needed to install + run
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./
COPY src ./src

# Install the module
RUN pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir .

# Standard MRB mount points
RUN mkdir -p /input /output

# Default execution: read /input, write /output
ENTRYPOINT ["python", "-m", "mrb_longterm.cli"]
CMD ["--input", "/input", "--output", "/output"]

