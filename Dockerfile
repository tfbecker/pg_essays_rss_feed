# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure scripts have Unix line endings and are executable
RUN dos2unix start_all.sh && \
    chmod +x start_all.sh && \
    apt-get remove -y dos2unix && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Create directory for logs
RUN mkdir -p /app/logs

# Make port 3000 available
EXPOSE 3000

# Run the application with all feeds
CMD ["./start_all.sh"]