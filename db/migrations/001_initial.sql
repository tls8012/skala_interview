CREATE TABLE IF NOT EXISTS notes (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    season_key varchar(7) NOT NULL CHECK (season_key ~ '^[0-9]{4}-H[12]$'),
    channel varchar(10) NOT NULL CHECK (channel IN ('info', 'chat')),
    title varchar(120),
    body text NOT NULL CHECK (char_length(body) BETWEEN 1 AND 5000),
    status varchar(20) NOT NULL DEFAULT 'visible'
        CHECK (status IN ('visible', 'quarantined', 'hidden')),
    session_hash varchar(64) NOT NULL,
    spam_score smallint NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz
);

CREATE INDEX IF NOT EXISTS notes_feed_idx
    ON notes (season_key, channel, status, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS notes_session_recent_idx
    ON notes (session_hash, created_at DESC);

CREATE TABLE IF NOT EXISTS login_attempts (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_hash varchar(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS login_attempts_recent_idx
    ON login_attempts (client_hash, created_at DESC);

CREATE TABLE IF NOT EXISTS notes_audit (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    note_id bigint NOT NULL,
    action varchar(10) NOT NULL,
    old_data jsonb NOT NULL,
    changed_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION audit_note_change() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO notes_audit (note_id, action, old_data)
    VALUES (OLD.id, TG_OP, to_jsonb(OLD));
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS notes_audit_trigger ON notes;
CREATE TRIGGER notes_audit_trigger
BEFORE UPDATE OR DELETE ON notes
FOR EACH ROW EXECUTE FUNCTION audit_note_change();
