CREATE TABLE ingest_queue (
    ingest_id uuid NOT NULL,
    path TEXT NOT NULL,
    ingested_at_utc TIMESTAMP NOT NULL,
    PRIMARY KEY (ingest_id)
);