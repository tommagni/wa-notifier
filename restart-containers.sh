#!/bin/bash

# Script to restart Docker Compose containers every 24 hours
# Add this to crontab with: crontab -e
# Then add: 0 0 * * * /path/to/wa_llm/restart-containers.sh

echo "$(date): Restarting Docker Compose containers..."

cd /Users/tom/code/wa-notifier || exit 1

# Stop containers gracefully
/usr/local/bin/docker compose down

# Wait a moment for clean shutdown
sleep 5

# Remove existing WhatsApp image to free space before pull
#/usr/local/bin/docker image rm aldinokemal2104/go-whatsapp-web-multidevice:latest || true

# Re-pull latest WhatsApp image
#/usr/local/bin/docker compose pull whatsapp

# Start containers again
/usr/local/bin/docker compose up -d

echo "$(date): Containers restarted successfully"
