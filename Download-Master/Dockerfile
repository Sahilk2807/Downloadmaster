# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables for Python and the Port
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT=10000

# Set the working directory
WORKDIR /app

# Install system dependencies, including ffmpeg, without installing extra packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the application for security
RUN addgroup --system app && adduser --system --group app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Change ownership of the files to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Expose the port the app runs on
EXPOSE $PORT

# Run the app using gunicorn (This is the corrected line)
CMD gunicorn --bind 0.0.0.0:$PORT app:app