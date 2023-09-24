-- Add migration script here
ALTER TABLE result ADD COLUMN comment TEXT NULL;
ALTER TABLE result ADD COLUMN used BOOLEAN DEFAULT false;