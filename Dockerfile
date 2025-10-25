FROM python:3.11-slim
ARG DEBIAN_FRONTEND="noninteractive"

# Install git (updated version)
RUN apt-get update \
    && apt-get install --yes git \
    && git --version \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
ADD . /app
WORKDIR /app

# Install Python dependencies
RUN pip install --target=/app -r /app/requirements.txt

# Run the sync script
CMD ["python", "/app/main.py"]