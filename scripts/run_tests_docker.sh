#!/bin/bash
# FR : Script pour lancer les tests unitaires dans un conteneur Docker
# EN: Script to run unit tests in a Docker container

set -e

docker build -f Dockerfile.test -t test-runner .
docker run --rm test-runner
