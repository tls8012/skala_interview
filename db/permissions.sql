-- Run as the database owner after creating a notes_writer login role.
-- The application role can read and add records, but cannot change existing notes.
REVOKE ALL ON notes, login_attempts, notes_audit FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO notes_writer;
GRANT SELECT, INSERT ON notes, login_attempts TO notes_writer;
GRANT USAGE, SELECT ON SEQUENCE notes_id_seq, login_attempts_id_seq TO notes_writer;
