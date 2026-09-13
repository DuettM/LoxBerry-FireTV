#!/bin/bash
# Wird von LoxBerry beim Entfernen des Plugins ausgeführt.
ROOT="${LBHOMEDIR:-${LBHOME:-}}"
[ -n "$ROOT" ] || exit 0
FOLDER="firetv"
CFG="$ROOT/config/plugins/$FOLDER/config.json"

# 1. Listener beenden
pkill -f "$ROOT/bin/plugins/.*/mqtt_listener.py.*$FOLDER" 2>/dev/null || true
sleep 1

# 2. Retained Topics beim Broker löschen. Ohne das bleiben die letzten Werte
#    dort stehen und der Miniserver zeigt nach der Deinstallation weiter
#    "online" an.
if [ -r "$CFG" ]; then
  python3 - "$CFG" "$ROOT" <<'PY' 2>/dev/null || true
import json, socket, struct, sys
cfgp, root = sys.argv[1:3]
try:
    with open(cfgp, encoding='utf-8') as f: c = json.load(f)
except Exception:
    raise SystemExit(0)
if not c.get('mqtt', {}).get('enabled', True):
    raise SystemExit(0)
base = str(c.get('mqtt', {}).get('base_topic', 'firetv') or 'firetv').strip('/')

host, port, user, pw = '127.0.0.1', 1883, '', ''
try:
    with open(root + '/config/system/general.json', encoding='utf-8') as f:
        g = json.load(f).get('Mqtt', {})
    host = g.get('Brokerhost', host); port = int(g.get('Brokerport', port))
    user = g.get('Brokeruser', ''); pw = g.get('Brokerpass', '')
except Exception:
    pass

def ms(v):
    b = str(v).encode(); return struct.pack('!H', len(b)) + b
def enc(n):
    o = b''
    while True:
        d = n % 128; n //= 128
        o += bytes([d | (128 if n else 0)])
        if not n: return o

topics = [base + '/availability', base + '/event', base + '/security']
for d in c.get('devices', []):
    ident = str(d.get('id') or d.get('name') or d.get('ip') or '').strip().lower()
    ident = ''.join(ch if ch.isalnum() else '-' for ch in ident).strip('-')
    if not ident: continue
    for suf in ('online', 'awake', 'display', 'app', 'authorized', 'state'):
        topics.append('%s/%s/%s' % (base, ident, suf))

try:
    flags = 2; pl = ms('lb-firetv-uninstall')
    if user:
        flags |= 0x80; pl += ms(user)
        if pw is not None: flags |= 0x40; pl += ms(pw)
    vh = ms('MQTT') + bytes([4, flags]) + struct.pack('!H', 15)
    s = socket.create_connection((host, port), timeout=4); s.settimeout(4)
    s.sendall(bytes([0x10]) + enc(len(vh) + len(pl)) + vh + pl)
    s.recv(4)
    for t in topics:
        body = ms(t)          # leere Nutzlast mit Retain löscht das Topic
        s.sendall(bytes([0x31]) + enc(len(body)) + body)
    s.sendall(b'\xe0\x00'); s.shutdown(socket.SHUT_WR); s.close()
except Exception:
    pass
PY
fi

# 3. Hilfsdateien entfernen, die neben der Konfiguration entstehen
rm -f "$CFG.heartbeat" "$CFG.lastpoll" "$CFG.cronlock" 2>/dev/null || true
exit 0
