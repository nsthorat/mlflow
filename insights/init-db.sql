-- Enable the pg_trgm extension for trigram search functionality
-- This is required for efficient span content search in MLflow
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Verify the extension is installed
SELECT * FROM pg_extension WHERE extname = 'pg_trgm';