# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install system dependencies and required packages
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y gcc libpq-dev postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Django runs on
EXPOSE 8001

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=OrderService.settings

# Default command (this is overridden by docker-compose command)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
