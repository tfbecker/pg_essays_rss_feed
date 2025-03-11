# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies and gunicorn
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY . .

# Ensure scripts have Unix line endings and are executable
RUN apt-get update && apt-get install -y dos2unix && \
    dos2unix start_angular.sh start_all.sh start_gwern.sh && \
    chmod +x start_angular.sh start_all.sh start_gwern.sh && \
    apt-get remove -y dos2unix && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Make port 3000 available
EXPOSE 3000

# Run the Angular Ventures feed by default
CMD ["./start_angular.sh"]