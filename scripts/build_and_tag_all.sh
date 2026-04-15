#!/bin/bash
# FR : Script pour builder toutes les images Docker Compose, lancer les services, puis taguer les images pour un push sur une registry Docker Hub
# EN: Script to build all Docker Compose images, run services, then tag images for Docker Hub registry

set -e

# Build all images

echo "[INFO] Build de toutes les images Docker Compose..."
docker compose build

echo "[INFO] Lancement des services pour vérification..."
docker compose up -d api streamlit worker

echo "[INFO] Tag des images pour Docker Hub (remplacez <username> et <repo> selon vos besoins)"
docker tag api-service:latest <username>/<repo>:api-latest
docker tag streamlit-frontend:latest <username>/<repo>:streamlit-latest
docker tag worker-service:latest <username>/<repo>:worker-latest

echo "[INFO] Prêt à push : docker push <username>/<repo>:api-latest (et autres tags)"
