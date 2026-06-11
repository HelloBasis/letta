#!/bin/sh
set -eu

# ─────────────────────────────────────────────────────────────────────────────
#  rds-entrypoint.sh — assemble LETTA_PG_URI for an external RDS Postgres
# ─────────────────────────────────────────────────────────────────────────────
#
#  TLS
#    • asyncpg runtime : ssl=require auto-injected by letta/server/db.py
#    • pg8000 alembic  : cleartext; requires rds.force_ssl=0 on RDS param group
#
#  Password
#    • LETTA_PG_PASSWORD must be URL-safe (alphanumeric + -._~).
#    • Special chars percent-encode to %XX and alembic's configparser
#      raises InterpolationSyntaxError on '%' inside the URL.
#    • pg8000 has no PGPASSWORD fallback, so the password lives in the URL.
# ─────────────────────────────────────────────────────────────────────────────

# Overlay any patched modules dropped into /patches (mirroring /app's tree)
# onto the installed source. Lets compose ship a single bind mount instead of
# one line per file.
if [ -d /patches ]; then
    cp -RL /patches/. /app/
fi

if [ -z "${LETTA_PG_URI:-}" ]; then
    : "${LETTA_PG_USER:?LETTA_PG_USER is required when LETTA_PG_URI is unset}"
    : "${LETTA_PG_PASSWORD:?LETTA_PG_PASSWORD is required when LETTA_PG_URI is unset}"
    : "${LETTA_PG_HOST:?LETTA_PG_HOST is required when LETTA_PG_URI is unset}"
    : "${LETTA_PG_DB:?LETTA_PG_DB is required when LETTA_PG_URI is unset}"
    LETTA_PG_PORT="${LETTA_PG_PORT:-5432}"

    LETTA_PG_URI="postgresql://${LETTA_PG_USER}:${LETTA_PG_PASSWORD}@${LETTA_PG_HOST}:${LETTA_PG_PORT}/${LETTA_PG_DB}"
    export LETTA_PG_URI
fi

exec "$@"
