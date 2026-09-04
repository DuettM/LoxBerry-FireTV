#!/bin/bash
# Restore user configuration after update and merge only missing defaults.
set -u
PDIR="${3:-}"
[ -n "$PDIR" ] || { echo "<FAIL> Plugin folder argument missing."; exit 1; }
PCONFIG="${LBPCONFIG:?LBPCONFIG missing}/$PDIR"
PBIN="${LBPBIN:?LBPBIN missing}/$PDIR"
PHTMLAUTH="${LBPHTMLAUTH:?LBPHTMLAUTH missing}/$PDIR"
PDATA="${LBPDATA:?LBPDATA missing}/$PDIR"
PLOG="${LBPLOG:?LBPLOG missing}/$PDIR"
BACKUP="/tmp/loxberry-firetv-${PDIR}-config-backup.json"
mkdir -p "$PCONFIG" "$PDATA" "$PLOG"

if [ -f "$BACKUP" ]; then
  if python3 -m json.tool "$BACKUP" >/dev/null 2>&1; then
    cp -p "$BACKUP" "$PCONFIG/config.json" || exit 1
    chmod 600 "$PCONFIG/config.json" 2>/dev/null || true
    echo "<INFO> Existing Fire TV configuration restored."
  else
    echo "<WARNING> Upgrade backup is invalid JSON and was not restored."
  fi
  rm -f "$BACKUP"
fi

if [ ! -f "$PCONFIG/config.json" ]; then
  cp "$PCONFIG/config.default.json" "$PCONFIG/config.json" || exit 1
  echo "<WARNING> No previous Fire TV configuration found; created defaults."
fi

python3 - "$PCONFIG/config.json" "$PCONFIG/config.default.json" <<'PY' || exit 1
import copy,json,os,secrets,sys,tempfile
p,dp=sys.argv[1:3]
with open(p,encoding='utf-8') as f:c=json.load(f)
with open(dp,encoding='utf-8') as f:d=json.load(f)
def merge(dst,defs):
    for k,v in defs.items():
        if k not in dst: dst[k]=copy.deepcopy(v)
        elif isinstance(v,dict) and isinstance(dst.get(k),dict): merge(dst[k],v)
merge(c,d)
if not c.get('web_secret'): c['web_secret']=secrets.token_hex(32)
m=c.setdefault('mqtt',{})
m.setdefault('allowed_actions',['tvon','tvoff','home','back','up','down','left','right','ok','menu','playpause','volumeup','volumedown','mute','app'])
m.setdefault('allow_reboot',False)
m.setdefault('allow_text',False)
m.setdefault('command_token_required',False)
if not m.get('command_token'): m['command_token']=secrets.token_urlsafe(32)
s=c.setdefault('security',{})
s.setdefault('discovery_post_only',True)
s.setdefault('private_adb_only',True)
c['config_version']=max(int(c.get('config_version',1)),4)
fd,tmp=tempfile.mkstemp(prefix='.config-',dir=os.path.dirname(p),text=True)
with os.fdopen(fd,'w',encoding='utf-8') as f:
    json.dump(c,f,ensure_ascii=False,indent=2);f.write('\n')
os.chmod(tmp,0o600);os.replace(tmp,p)
PY

chmod 700 "$PCONFIG" "$PLOG" 2>/dev/null || true
chmod 700 "$PBIN/firetv.py" "$PBIN/mqtt_listener.py" "$PBIN/watchdog.py" "$PBIN/secure_update.py" 2>/dev/null || true
chmod 755 "$PHTMLAUTH/index.cgi" "$PHTMLAUTH/dashboard.cgi" "$PHTMLAUTH/config.cgi" "$PHTMLAUTH/discover.cgi" "$PHTMLAUTH/security.cgi" "$PHTMLAUTH/debug.cgi" "$PHTMLAUTH/api.cgi" 2>/dev/null || true
chmod 600 "$PBIN/update_public_key.hex" "$PCONFIG/config.json" 2>/dev/null || true
touch "$PLOG/firetv.log" "$PLOG/mqtt-daemon.log" "$PLOG/watchdog.log" 2>/dev/null || true
chmod 600 "$PLOG/"*.log 2>/dev/null || true
chown -R loxberry:loxberry "$PCONFIG" "$PLOG" 2>/dev/null || true
pkill -f "$PBIN/mqtt_listener.py.*$PCONFIG/config.json" 2>/dev/null || true
exit 0
