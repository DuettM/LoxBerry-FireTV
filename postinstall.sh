#!/bin/bash
set -u
PDIR="${3:-firetv}"
PCONFIG="${LBPCONFIG:?LBPCONFIG missing}/$PDIR"
PBIN="${LBPBIN:?LBPBIN missing}/$PDIR"
PLOG="${LBPLOG:?LBPLOG missing}/$PDIR"
mkdir -p "$PCONFIG" "$PLOG"
if [ ! -f "$PCONFIG/config.json" ]; then cp "$PCONFIG/config.default.json" "$PCONFIG/config.json" || exit 1; fi
chmod 600 "$PCONFIG/config.json" 2>/dev/null || true
chmod 700 "$PBIN/firetv.py" "$PBIN/mqtt_listener.py" "$PBIN/watchdog.py" 2>/dev/null || true
if ! command -v adb >/dev/null 2>&1; then
 echo "<INFO> ADB wird installiert..."
 if command -v apt-get >/dev/null 2>&1; then
  apt-get update >/dev/null 2>&1 || true
  apt-get install -y adb >/dev/null 2>&1 || apt-get install -y android-tools-adb >/dev/null 2>&1 || true
 fi
fi
if ! command -v adb >/dev/null 2>&1; then echo "<WARNING> ADB konnte nicht automatisch installiert werden."; else echo "<INFO> ADB vorhanden: $(adb version 2>/dev/null | head -n1)"; fi
touch "$PLOG/firetv.log" "$PLOG/mqtt-daemon.log" "$PLOG/watchdog.log"
chmod 600 "$PLOG/"*.log 2>/dev/null || true
nohup "$PBIN/mqtt_listener.py" --config "$PCONFIG/config.json" --core "$PBIN/firetv.py" >>"$PLOG/mqtt-daemon.log" 2>&1 &
echo "<INFO> Fire TV Control 0.1.0 installiert."
exit 0
