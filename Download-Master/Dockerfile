# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, including ffmpeg
# -y flag automatically answers yes to prompts
# --no-install-recommends reduces the image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir ensures that pip does not store the downloaded packages, reducing image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 80 available to the world outside this container
# Render will automatically map this to its public-facing ports
EXPOSE 80

# Define the command to run the app using gunicorn
# This is a production-grade WSGI server
# 0.0.0.0 makes the server accessible from outside the container
CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]