#!/usr/bin/env bash
set -e

LOCAL_DB="backend/db/jobcv.db"
CONTAINER="latex-tool-backend"
CONTAINER_DB="/app/db/jobcv.db"

if [ ! -f "$LOCAL_DB" ]; then
    echo "ERROR: Local DB not found at $LOCAL_DB"
    exit 1
fi

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "ERROR: Container '$CONTAINER' is not running. Start it first with: docker compose up backend"
    exit 1
fi

echo "Suppression des fichiers WAL SQLite dans le container..."
docker exec "$CONTAINER" rm -f "${CONTAINER_DB}-shm" "${CONTAINER_DB}-wal"

echo "Copying $LOCAL_DB → $CONTAINER:$CONTAINER_DB ..."
docker cp "$LOCAL_DB" "$CONTAINER:$CONTAINER_DB"

echo "Restarting $CONTAINER to pick up the new DB..."
docker restart "$CONTAINER"
echo "Done. The admin panel should now show your data."