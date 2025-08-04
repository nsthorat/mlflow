FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install MLflow from the local source
# Copy the entire MLflow source code
COPY . /app/

# Install MLflow in development mode and PostgreSQL driver
RUN pip install --no-cache-dir -e . psycopg2

# Expose MLflow server port
EXPOSE 5000

# Default command to run MLflow server
CMD ["mlflow", "server", \
     "--host", "0.0.0.0", \
     "--port", "5000", \
     "--backend-store-uri", "${MLFLOW_BACKEND_STORE_URI}", \
     "--default-artifact-root", "/mlruns"]