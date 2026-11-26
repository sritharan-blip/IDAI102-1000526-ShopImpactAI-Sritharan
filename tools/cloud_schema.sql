-- Run as the database owner. Keep this schema outside any provider's public data API.
BEGIN;
CREATE SCHEMA IF NOT EXISTS shopimpact_private;
REVOKE ALL ON SCHEMA shopimpact_private FROM PUBLIC;

ALTER TABLE IF EXISTS public.shopimpact_workspaces SET SCHEMA shopimpact_private;
CREATE TABLE IF NOT EXISTS shopimpact_private.shopimpact_workspaces (
    owner text PRIMARY KEY CHECK (owner ~ '^[0-9a-f]{64}$'),
    revision bigint NOT NULL CHECK (revision > 0),
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object')
);

-- The server connects directly as the app role. Do not expose workspace rows through a public API.
REVOKE ALL ON shopimpact_private.shopimpact_workspaces FROM PUBLIC;

CREATE TABLE IF NOT EXISTS shopimpact_private.shopimpact_accounts (
    email text PRIMARY KEY CHECK (length(email) <= 254),
    owner text UNIQUE NOT NULL CHECK (owner ~ '^[0-9a-f]{64}$'),
    display_name text NOT NULL CHECK (length(display_name) BETWEEN 1 AND 80),
    password_hash text NOT NULL
);

CREATE TABLE IF NOT EXISTS shopimpact_private.shopimpact_auth_limits (
    bucket text PRIMARY KEY CHECK (bucket ~ '^[0-9a-f]{64}$'),
    starts_at timestamptz NOT NULL,
    attempts integer NOT NULL
);

REVOKE ALL ON shopimpact_private.shopimpact_accounts, shopimpact_private.shopimpact_auth_limits FROM PUBLIC;
COMMIT;
