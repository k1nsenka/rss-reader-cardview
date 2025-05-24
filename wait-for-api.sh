#!/bin/sh
# wait-for-api.sh
# Wait for Miniflux API to be available before starting cron

echo "Waiting for Miniflux API to be available..."

MAX_TRIES=60
COUNTER=0

while [ $COUNTER -lt $MAX_TRIES ]; do
    if [ -n "$MINIFLUX_API_KEY" ]; then
        # If API key is set, try to access the API
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "X-Auth-Token: $MINIFLUX_API_KEY" \
            "$MINIFLUX_BASE_URL/v1/me")
        
        if [ "$RESPONSE" = "200" ]; then
            echo "Miniflux API is ready!"
            exit 0
        fi
    else
        # If no API key, just check if service is up
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$MINIFLUX_BASE_URL/healthcheck")
        
        if [ "$RESPONSE" = "200" ]; then
            echo "Miniflux is ready (no API key set yet)"
            exit 0
        fi
    fi
    
    COUNTER=$((COUNTER + 1))
    echo "Waiting for Miniflux... (attempt $COUNTER/$MAX_TRIES)"
    sleep 5
done

echo "Timeout waiting for Miniflux API"
exit 1