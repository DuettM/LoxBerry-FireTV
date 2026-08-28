#!/bin/bash
set -u
PDIR="${3:-firetv}"
PCONFIG="${LBPCONFIG:?LBPCONFIG missing}/$PDIR"
PBIN="${LBPBIN:?LBPBIN missing}/$PDIR"
PLOG="${LBPLOG:?LBPLOG missing}/$PDIR"
mkdir -p "$PCONFIG" "$PLOG"
if [ ! -f "$PCONFIG/config.json" ]; then cp "$PCONFIG/config.default.json" "$PCONFIG/config.json" || exit 1; fi
python3 - "$PCONFIG/config.json" <<'PY'
import json,secrets,sys,os,tempfile
p=sys.argv[1]
try:c=json.load(open(p,encoding='utf-8'))
except Exception:c={}
if not c.get('web_secret'):c['web_secret']=secrets.token_hex(32)
c['config_version']=max(int(c.get('config_version',1)),2)
fd,tmp=tempfile.mkstemp(prefix='.config-',dir=os.path.dirname(p),text=True)
with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(c,f,ensure_ascii=False,indent=2);f.write('\n')
os.chmod(tmp,0o600);os.replace(tmp,p)
PY
chmod 700 "$PCONFIG" "$PLOG" 2>/dev/null || true
chmod 600 "$PCONFIG/config.json" 2>/dev/null || true
chmod 700 "$PBIN/firetv.py" "$PBIN/mqtt_listener.py" "$PBIN/watchdog.py" "$PBIN/secure_update.py" 2>/dev/null || true
chmod 600 "$PBIN/update_public_key.hex" 2>/dev/null || true
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
chown -R loxberry:loxberry "$PCONFIG" "$PLOG" 2>/dev/null || true
echo "<INFO> Fire TV Control 0.2.0 installiert. MQTT-Listener wird über den nativen LoxBerry-Daemonmechanismus gestartet."
exit 0
