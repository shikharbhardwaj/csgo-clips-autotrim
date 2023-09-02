-- Add migration script here
CREATE TABLE result (
    ingest_id uuid NOT NULL,
    timeline json,
    clutch_detection_result json,
    PRIMARY KEY (ingest_id)
);