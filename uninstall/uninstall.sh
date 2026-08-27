#!/bin/bash
ROOT="${LBHOMEDIR:-${LBHOME:-/opt/loxberry}}"
pkill -f "$ROOT/bin/plugins/.*/mqtt_listener.py.*firetv" 2>/dev/null || true
exit 0
