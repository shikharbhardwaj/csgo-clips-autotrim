-- Add optional status column to ingest_queue.
ALTER TABLE ingest_queue ADD COLUMN status TEXT NULL;

