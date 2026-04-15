#!/bin/bash
# FR : Script pour lancer les services API, Streamlit et Worker avec Docker Compose
# EN: Script to run API, Streamlit and Worker services with Docker Compose

set -e

docker compose up --build api streamlit worker
