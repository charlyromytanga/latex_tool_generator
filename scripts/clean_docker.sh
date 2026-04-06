#!/bin/bash
# Nettoyage complet Docker : images, conteneurs, volumes, cache
set -e

echo "=== Nettoyage Docker : images, conteneurs, volumes, cache ==="
docker system prune -a -f

echo "=== Nettoyage Docker terminé ==="
