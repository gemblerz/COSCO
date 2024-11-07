#!/bin/bash

echo "Removing existing COSCO container..."
docker rm -f cosco || true
echo "Done."

echo "Using the current directory as data folder inside the container."
echo "Current directory: $(pwd)"
echo "Running a Docker container for COSCO..."
sudo docker run -d \
  --name cosco \
  --pull always \
  --volume $(pwd):/data \
  gemblerz/cosco

echo "Done."