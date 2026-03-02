#!/bin/bash
# AlertHub Cron Checker
# Check for new emails and notify

ALERT_HUB_URL="http://localhost:31436"
LOG_FILE="/var/log/alert_hub_check.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

# Check Gmail for important emails
check_gmail() {
    response=$(curl -s "$ALERT_HUB_URL/gmail/check?limit=5")
    
    # Check if we got valid JSON
    if echo "$response" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
        total=$(echo "$response" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('total', 0))" 2>/dev/null || echo "0")
        urgent=$(echo "$response" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('urgent_count', 0))" 2>/dev/null || echo "0")
        
        log "Gmail check: $total emails, $urgent urgent"
        
        # If there are urgent emails, send notification
        if [ "$urgent" -gt 0 ]; then
            log "Sending urgent email notification..."
            curl -s -X POST "$ALERT_HUB_URL/notify?message=+$urgent+emails+urgentes+en+Gmail&urgent=true" > /dev/null
        fi
    else
        log "Gmail check failed: $response"
    fi
}

# Check LinkedIn (placeholder for now)
check_linkedin() {
    response=$(curl -s "$ALERT_HUB_URL/linkedin/check")
    log "LinkedIn: $response"
}

# Main
log "=== Starting check ==="
check_gmail
check_linkedin
log "=== Check complete ==="
