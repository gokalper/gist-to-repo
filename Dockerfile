FROM python:3-slim
ARG DEBIAN_FRONTEND="noninteractive"

# Install git
RUN apt-get update \
    && apt-get install --yes git \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
ADD . /app
WORKDIR /app

# Install Python dependencies
RUN pip install --target=/app -r /app/requirements.txt

# Run the sync script
CMD ["python", "/app/main.py"]