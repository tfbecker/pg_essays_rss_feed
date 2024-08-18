# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 9777 available to the world outside this container
EXPOSE 9777

# Define environment variable
ENV FLASK_APP=pg_essays.py

# Run app.py when the container launches
CMD ["waitress-serve", "--host=0.0.0.0", "--port=9777", "pg_essays:app"]