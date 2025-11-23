#!/bin/bash

# Script to restart Docker Compose containers every 24 hours
# Add this to crontab with: crontab -e
# Then add: 0 0 * * * /path/to/wa_llm/restart-containers.sh

echo "$(date): Restarting Docker Compose containers..."

# Stop containers gracefully
docker compose down

# Wait a moment for clean shutdown
sleep 5

# Start containers again
docker compose up -d

echo "$(date): Containers restarted successfully"
