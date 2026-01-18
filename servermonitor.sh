#!/bin/bash

SERVER="10.0.0.400"
# WEBHOOK_URL="https://slack.com/shortcuts/Ft0A9C9K05D4/338f1f753f4d775d2358bbffcc886528"
STATE_FILE="$HOME/.mac_2014_server_state"

# ping once, wait max 2s
if ping -c 1 -W 2 "$SERVER" >/dev/null 2>&1; then
  STATUS="up"
else
  STATUS="down"
fi

LAST_STATUS=$(cat "$STATE_FILE" 2>/dev/null || echo "unknown")
    
# notify only on change
  if [[ "$STATUS" == "down" ]]; then
    TEXT="🚨 *Server DOWN*\nHost: $SERVER\nTime: $(date)"

  curl -s --location 'https://hooks.slack.com/triggers/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' \
    --header 'Content-Type: application/json' \
    --data "{\"text\":\"$TEXT\"}" \
    >/dev/null

  echo "$STATUS" > "$STATE_FILE"
fi
