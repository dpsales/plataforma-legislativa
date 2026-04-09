FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Make scripts executable
RUN chmod +x /app/scripts/start-web.sh

# Create necessary directories
RUN mkdir -p /app/data /app/staticfiles /app/documentos_sei

EXPOSE 8080

CMD ["/app/scripts/start-web.sh"]
