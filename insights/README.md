# MLflow Server with PostgreSQL

This directory contains Docker configurations for running MLflow server with PostgreSQL backend, including the `pg_trgm` extension required for efficient span content search.

## Prerequisites

- Docker and Docker Compose installed
- Port 5001 (MLflow) and 5432 (PostgreSQL) available

## Quick Start

1. Navigate to the insights directory:

   ```bash
   cd insights
   ```

2. Build and start the services:

   ```bash
   docker-compose up -d --build
   ```

3. Verify services are running:

   ```bash
   docker-compose ps
   ```

4. Access MLflow UI at http://localhost:5001

## Architecture

- **PostgreSQL 15**: Database backend with `pg_trgm` extension pre-installed
- **MLflow Server**: Running from source with PostgreSQL backend store
- **Automatic Migrations**: MLflow will run database migrations on startup

## Configuration

### PostgreSQL

- Database: `mlflow`
- User: `mlflow`
- Password: `mlflow123`
- Port: `5432`
- Extension: `pg_trgm` (installed via init-db.sql)

### MLflow Server

- Port: `5001` (mapped from container port 5000)
- Backend Store: PostgreSQL
- Artifact Store: `/mlruns` (local volume)

## Testing the Setup

1. Check PostgreSQL connection and pg_trgm extension:

   ```bash
   docker exec mlflow-postgres psql -U mlflow -d mlflow -c "SELECT * FROM pg_extension WHERE extname = 'pg_trgm';"
   ```

2. Create a test experiment:

   ```bash
   curl -X POST http://localhost:5001/api/2.0/mlflow/experiments/create \
     -H "Content-Type: application/json" \
     -d '{"name": "test-experiment"}'
   ```

3. Verify database tables were created:
   ```bash
   docker exec -it mlflow-postgres psql -U mlflow -d mlflow -c "\dt"
   ```

## Docker CLI Commands

### Build the image:

```bash
docker build -f insights/Dockerfile -t mlflow-postgres:latest .
```

### Run PostgreSQL container:

```bash
docker run -d \
  --name mlflow-postgres \
  -e POSTGRES_DB=mlflow \
  -e POSTGRES_USER=mlflow \
  -e POSTGRES_PASSWORD=mlflow123 \
  -p 5432:5432 \
  -v $(pwd)/insights/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql \
  postgres:15-alpine
```

### Run MLflow container:

```bash
docker run -d \
  --name mlflow-server \
  --link mlflow-postgres:postgres \
  -p 5001:5000 \
  -e MLFLOW_BACKEND_STORE_URI=postgresql://mlflow:mlflow123@postgres:5432/mlflow \
  mlflow-postgres:latest
```

## Stopping Services

```bash
docker-compose down
```

To also remove volumes:

```bash
docker-compose down -v
```

## Troubleshooting

1. **Check logs**:

   ```bash
   docker-compose logs mlflow
   docker-compose logs postgres
   ```

2. **Verify pg_trgm extension**:

   ```bash
   docker exec -it mlflow-postgres psql -U mlflow -d mlflow -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
   ```

3. **Check MLflow health**:
   ```bash
   curl http://localhost:5001/health
   ```
