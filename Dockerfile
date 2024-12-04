# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies and gunicorn globally
RUN pip install --no-cache-dir gunicorn
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and set up permissions
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Copy application code after setting permissions
COPY --chown=appuser:appuser . .

# Make the startup script executable
USER root
RUN chmod +x start.sh
USER appuser

# Set environment variables
ENV PORT=3000
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Run both scripts when the container launches
CMD ["./start.sh"]