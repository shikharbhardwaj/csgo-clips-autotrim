BEGIN;
    -- Backfill `status` for existing rows.
    UPDATE ingest_queue
        SET status = 'ACCEPTED'
        WHERE status is NULL;

    -- Make `status` mandatory
    ALTER TABLE ingest_queue ALTER COLUMN status SET NOT NULL;
COMMIT;
