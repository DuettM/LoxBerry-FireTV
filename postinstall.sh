#!/bin/bash
set -u
PDIR="${3:-}"
PVERSION="${4:-unknown}"
[ -n "$PDIR" ] || { echo "<FAIL> Plugin folder argument missing."; exit 1; }
PCONFIG="${LBPCONFIG:?LBPCONFIG missing}/$PDIR"
PBIN="${LBPBIN:?LBPBIN missing}/$PDIR"
PHTMLAUTH="${LBPHTMLAUTH:?LBPHTMLAUTH missing}/$PDIR"
PHTML="${LBPHTML:?LBPHTML missing}/$PDIR"
PDATA="${LBPDATA:?LBPDATA missing}/$PDIR"
PLOG="${LBPLOG:?LBPLOG missing}/$PDIR"
mkdir -p "$PCONFIG" "$PDATA" "$PLOG"

if [ ! -f "$PCONFIG/config.json" ]; then
  cp "$PCONFIG/config.default.json" "$PCONFIG/config.json" || { echo "<ERROR> config.default.json konnte nicht kopiert werden."; exit 2; }
  echo "<INFO> Fire TV Konfiguration angelegt."
fi

python3 - "$PCONFIG/config.json" <<'PYCFG' || exit 2
import json,secrets,sys,os,tempfile
p=sys.argv[1]
with open(p,encoding='utf-8') as f:c=json.load(f)
if not c.get('web_secret'): c['web_secret']=secrets.token_hex(32)
c['config_version']=max(int(c.get('config_version',1)),2)
fd,tmp=tempfile.mkstemp(prefix='.config-',dir=os.path.dirname(p),text=True)
with os.fdopen(fd,'w',encoding='utf-8') as f:
    json.dump(c,f,ensure_ascii=False,indent=2); f.write('\n')
os.chmod(tmp,0o600); os.replace(tmp,p)
PYCFG

chmod 700 "$PBIN/firetv.py" "$PBIN/mqtt_listener.py" "$PBIN/watchdog.py" "$PBIN/secure_update.py" 2>/dev/null || true
chmod 755 "$PHTMLAUTH/index.cgi" "$PHTMLAUTH/config.cgi" "$PHTMLAUTH/debug.cgi" "$PHTMLAUTH/api.cgi" "$PHTML/firetv.cgi" 2>/dev/null || true
chmod 600 "$PCONFIG/config.json" "$PBIN/update_public_key.hex" 2>/dev/null || true

touch "$PLOG/firetv.log" "$PLOG/mqtt-daemon.log" "$PLOG/watchdog.log" 2>/dev/null || true
chmod 600 "$PLOG/"*.log 2>/dev/null || true

if command -v adb >/dev/null 2>&1; then
  echo "<INFO> ADB vorhanden: $(adb version 2>/dev/null | head -n1)"
else
  echo "<WARNING> ADB ist nicht verfügbar. Erwartetes Debian-Paket: adb (dpkg/apt)."
fi

echo "<OK> Fire TV Control $PVERSION installiert."
exit 0
