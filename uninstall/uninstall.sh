#!/bin/bash
ROOT="${LBHOMEDIR:-${LBHOME:-}}"
[ -n "$ROOT" ] || exit 0
pkill -f "$ROOT/bin/plugins/.*/mqtt_listener.py.*firetv" 2>/dev/null || true
exit 0
