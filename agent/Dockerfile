FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential curl cron \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r agentuser && useradd --no-log-init -r -g agentuser agentuser

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set ownership for the app directory
RUN chown -R agentuser:agentuser /app

# Switch to non-root user
USER agentuser

# Expose the webhook port
EXPOSE 8000

# Command to run the webhook server
CMD ["python", "webhook_server.py"]