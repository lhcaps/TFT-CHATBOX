#!/usr/bin/env bash
# Refresh ngrok webhook URL for n8n
# Usage: ./refresh-webhook-url.sh <auth-token> <url>

set -e

AUTH_TOKEN="${1}"
CURRENT_URL="${2}"

echo "Registering ngrok webhook: ${CURRENT_URL}"

curl -s -X POST "https://api.ngrok.com/api/v1/http_edges" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"module\": {\"request_headers\": {}, \"response\": {}}, \"metadata\": {\"description\": \"TFT Copilot n8n webhook\"}}"
