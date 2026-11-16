#!/bin/sh
# Runs once on first start. Tables themselves are created by the backend (SQLAlchemy).
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -c "ALTER DATABASE \"$POSTGRES_DB\" SET timezone TO 'Africa/Tunis';"
