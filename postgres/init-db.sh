#!/bin/bash
set -e

echo "Running custom-init.sh script..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;
    CREATE TABLE IF NOT EXISTS public.knowledge_base (
        document_id varchar PRIMARY KEY,
        embedding vector(1536),
        additional_information jsonb,
        text text
    );
    CREATE INDEX ON public.knowledge_base USING ivfflat (embedding) WITH (lists = 100);
EOSQL

sleep 10

echo "Script execution completed."