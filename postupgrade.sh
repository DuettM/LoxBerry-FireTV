#!/bin/bash
set -u
PDIR="${3:-firetv}"
PCONFIG="${LBPCONFIG:?LBPCONFIG missing}/$PDIR"
PBIN="${LBPBIN:?LBPBIN missing}/$PDIR"
PLOG="${LBPLOG:?LBPLOG missing}/$PDIR"
if [ ! -f "$PCONFIG/config.json" ]; then cp "$PCONFIG/config.default.json" "$PCONFIG/config.json"; fi
chmod 700 "$PBIN/firetv.py" "$PBIN/mqtt_listener.py" "$PBIN/watchdog.py" 2>/dev/null || true
chmod 600 "$PCONFIG/config.json" 2>/dev/null || true
pkill -f "$PBIN/mqtt_listener.py.*$PCONFIG/config.json" 2>/dev/null || true
nohup "$PBIN/mqtt_listener.py" --config "$PCONFIG/config.json" --core "$PBIN/firetv.py" >>"$PLOG/mqtt-daemon.log" 2>&1 &
exit 0
