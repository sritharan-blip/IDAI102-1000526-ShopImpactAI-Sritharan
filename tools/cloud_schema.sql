-- Run once in the hosted Postgres database. Use a dedicated app role with SELECT, INSERT and UPDATE.
CREATE TABLE IF NOT EXISTS shopimpact_workspaces (
    owner text PRIMARY KEY CHECK (owner ~ '^[0-9a-f]{64}$'),
    revision bigint NOT NULL CHECK (revision > 0),
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object')
);

-- The server connects directly as the app role. Do not expose workspace rows through a public API.
REVOKE ALL ON shopimpact_workspaces FROM PUBLIC;
