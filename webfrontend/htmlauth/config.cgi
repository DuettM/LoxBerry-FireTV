#!/usr/bin/env python3
import hashlib,hmac,html,ipaddress,json,os,re,tempfile,sys
from urllib.parse import parse_qs

def root():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);m=os.sep+'webfrontend'+os.sep
 if m in p:return p.split(m,1)[0]
 r=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME')
 if r:return r
 raise RuntimeError('LoxBerry Basisverzeichnis konnte nicht ermittelt werden')
def folder():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);parts=p.split(os.sep);return parts[parts.index('plugins')+1] if 'plugins' in parts else 'firetv'
def form_data():
 data={k:v[-1] if v else '' for k,v in parse_qs(os.environ.get('QUERY_STRING',''),keep_blank_values=True).items()}
 if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
  try:length=min(max(int(os.environ.get('CONTENT_LENGTH','0') or 0),0),65536)
  except ValueError:length=0
  raw=sys.stdin.buffer.read(length) if length else b''
  if (os.environ.get('CONTENT_TYPE','') or '').split(';',1)[0].strip().lower()=='application/x-www-form-urlencoded':
   for k,v in parse_qs(raw.decode('utf-8','replace'),keep_blank_values=True).items():data[k]=v[-1] if v else ''
 return data
FOLDER=folder();CFG=os.path.join(root(),'config','plugins',FOLDER,'config.json')
def load():return json.load(open(CFG,encoding='utf-8'))
def save(c):
 fd,tmp=tempfile.mkstemp(prefix='.config-',dir=os.path.dirname(CFG),text=True)
 with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(c,f,ensure_ascii=False,indent=2);f.write('\n')
 os.chmod(tmp,0o600);os.replace(tmp,CFG)
def version():
 try:
  base=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__).split(os.sep+'webfrontend'+os.sep,1)[0]
  with open(os.path.join(base,'plugin.cfg'),encoding='utf-8') as f:
   for line in f:
    if line.startswith('VERSION='):return line.split('=',1)[1].strip()
 except Exception:pass
 return '0.3.1'
def csrf(c):return hmac.new(str(c.get('web_secret','')).encode(),(os.environ.get('HTTP_COOKIE','')+'|'+os.environ.get('HTTP_USER_AGENT','')).encode(),hashlib.sha256).hexdigest()
def same_site():
 if os.environ.get('HTTP_SEC_FETCH_SITE','').lower()=='cross-site':return False
 host=os.environ.get('HTTP_HOST','').lower()
 for k in ('HTTP_ORIGIN','HTTP_REFERER'):
  v=os.environ.get(k,'').lower();m=re.match(r'^https?://([^/]+)',v) if v and host else None
  if m and m.group(1)!=host:return False
 return True
def clean_topic(v):
 v=(v or 'firetv').strip().strip('/') or 'firetv'
 if len(v)>128 or re.search(r'[+#\s\x00]',v):raise ValueError('MQTT Basistopic ungültig.')
 return v
def valid_ip(v):
 try:ipaddress.ip_address(v);return True
 except ValueError:return bool(re.fullmatch(r'[A-Za-z0-9.-]{1,253}',v or ''))
try:c=load()
except Exception as e:
 print('Status: 500 Internal Server Error\r\nContent-Type: text/html; charset=utf-8\r\n\r\n',end='');print('<h1>Fire TV Control</h1><p>%s</p>'%html.escape(str(e)));sys.exit(0)
f=form_data();notice='';error='';token=csrf(c)
if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
 try:
  sent=f.get('csrf','') or ''
  if not same_site() or not sent or not hmac.compare_digest(sent,token):raise ValueError('Sicherheitsprüfung fehlgeschlagen.')
  act=f.get('form_action','')
  if act=='save_general':
   poll=int(f.get('poll_interval','30'))
   if poll<10 or poll>3600:raise ValueError('Abfrageintervall muss zwischen 10 und 3600 Sekunden liegen.')
   c['poll_interval']=poll;c.setdefault('mqtt',{})['enabled']=bool(f.get('mqtt_enabled'));c['mqtt']['listen_enabled']=bool(f.get('mqtt_listen'));c['mqtt']['base_topic']=clean_topic(f.get('base_topic','firetv'));c.setdefault('watchdog',{})['enabled']=bool(f.get('watchdog_enabled'));save(c);notice='Einstellungen gespeichert.'
  elif act=='add_device':
   ip=(f.get('ip','') or '').strip();name=(f.get('name','Fire TV') or '').strip();port=int(f.get('port','5555'))
   if not valid_ip(ip):raise ValueError('IP/Hostname ungültig.')
   if not name or len(name)>80 or re.search(r'[\r\n\x00]',name):raise ValueError('Gerätename ungültig.')
   if port<1 or port>65535:raise ValueError('Port ungültig.')
   if any(str(d.get('ip',''))==ip for d in c.get('devices',[])):raise ValueError('Dieses Gerät ist bereits vorhanden.')
   base=re.sub(r'[^a-zA-Z0-9_-]+','-',name.lower()).strip('-') or ip.replace('.','-');ident=base;n=2;ids={str(d.get('id','')) for d in c.get('devices',[])}
   while ident in ids:ident=f'{base}-{n}';n+=1
   c.setdefault('devices',[]).append({'id':ident,'name':name,'ip':ip,'port':port,'enabled':True});save(c);notice='Gerät hinzugefügt. Falls am Fire TV eine ADB-Abfrage erscheint, bitte bestätigen.'
  elif act=='delete':
   ident=f.get('id','') or ''
   if len(ident)>128 or re.search(r'[\r\n\x00]',ident):raise ValueError('Geräte-ID ungültig.')
   c['devices']=[d for d in c.get('devices',[]) if str(d.get('id',''))!=ident];save(c);notice='Gerät gelöscht.'
  else:raise ValueError('Unbekannte Aktion.')
 except Exception as e:error=str(e)
print("Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'\r\nX-Frame-Options: DENY\r\nPermissions-Policy: camera=(), microphone=(), geolocation=()\r\n\r\n",end='')
print('''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Einstellungen</title><style>:root{--green:#73b72b;--green-dark:#4d8e1a;--green-soft:#edf7e5;--text:#29323a;--muted:#71808d;--line:#dde4e8;--bg:#f6f8f9;--red:#d94343}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Arial,Helvetica,sans-serif}.root{max-width:1180px;margin:auto;padding:12px}.head{display:flex;align-items:center;gap:14px;background:#fff;border:1px solid var(--line);border-radius:9px;padding:13px 16px;margin-bottom:12px}.logo{width:54px;height:54px;border-radius:8px;background:linear-gradient(145deg,#86ca42,#5ba21d);display:grid;place-items:center;color:white;font-size:27px}.title{flex:1}.title h1{margin:0;color:#257c31;font-size:23px}.title p{margin:3px 0 0;color:#56616b}.ver{font-size:12px;color:#687680}.nav{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px}.nav a{background:#fff;border:1px solid var(--line);border-radius:6px;padding:9px 11px;text-decoration:none;color:#34404a;font-weight:600}.nav a.active{background:var(--green-soft);color:#2d7d29;border-color:#cbe1c1}.card{background:#fff;border:1px solid var(--line);border-radius:9px;margin-bottom:12px}.card h2{font-size:17px;margin:0;padding:13px 15px;border-bottom:1px solid #edf0f2}.body{padding:15px}.form-grid{display:grid;grid-template-columns:repeat(2,minmax(220px,1fr));gap:12px}.field label{display:block;font-weight:bold;font-size:12px;margin-bottom:5px}.field input{width:100%;height:38px;border:1px solid #cbd4da;border-radius:6px;padding:0 10px;background:#fff}.checks{display:flex;gap:18px;flex-wrap:wrap;margin:14px 0}.btn{border:1px solid #cdd6dc;background:#fff;border-radius:6px;padding:9px 12px;cursor:pointer;font-weight:600;color:#2f3942}.btn-green{background:var(--green);border-color:var(--green);color:#fff}.btn-red{border-color:#efb8b8;color:#b92e2e}.notice{padding:10px 12px;border-radius:6px;margin-bottom:12px}.ok{background:#edf8e8;border:1px solid #cbe5bd;color:#34751f}.err{background:#fff0f0;border:1px solid #efc0c0;color:#a52828}.muted{color:var(--muted);font-size:12px}.device{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center;padding:11px 0;border-bottom:1px solid #edf0f2}.device:last-child{border-bottom:0}.device code{color:#687680}.footer{text-align:center;color:#66727b;padding:16px;font-size:13px}@media(max-width:700px){.head{flex-wrap:wrap}.form-grid{grid-template-columns:1fr}.device{grid-template-columns:1fr}.ver{margin-left:68px}}</style></head><body><div class="root"><div class="head"><div class="logo">⚙</div><div class="title"><h1>Fire TV Einstellungen</h1><p>Geräte, MQTT und Systemverhalten konfigurieren</p></div><div class="ver">Version __VER__</div></div><div class="nav"><a href="index.cgi">⌂ Übersicht</a><a class="active" href="config.cgi">⚙ Einstellungen</a><a href="discover.cgi">⌕ Fire TVs suchen</a><a href="security.cgi">🔒 Security Center</a><a href="debug.cgi">▤ Debug</a></div>'''.replace('__VER__',html.escape(version())))
if notice:print('<div class="notice ok">%s</div>'%html.escape(notice))
if error:print('<div class="notice err">%s</div>'%html.escape(error))
csrf_h='<input type="hidden" name="csrf" value="%s">'%html.escape(token,quote=True)
print('<section class="card"><h2>Allgemein</h2><div class="body"><form method="post">%s<input type="hidden" name="form_action" value="save_general"><div class="form-grid"><div class="field"><label>Abfrageintervall</label><input type="number" min="10" max="3600" name="poll_interval" value="%s"></div><div class="field"><label>MQTT Basistopic</label><input name="base_topic" maxlength="128" value="%s"></div></div><div class="checks"><label><input type="checkbox" name="mqtt_enabled" %s> MQTT aktiv</label><label><input type="checkbox" name="mqtt_listen" %s> Befehle empfangen</label><label><input type="checkbox" name="watchdog_enabled" %s> Watchdog aktiv</label></div><button class="btn btn-green">Speichern</button></form><p class="muted">MQTT-Befehlsrechte werden separat im Security Center festgelegt.</p></div></section>'%(csrf_h,c.get('poll_interval',30),html.escape(c.get('mqtt',{}).get('base_topic','firetv'),quote=True),'checked' if c.get('mqtt',{}).get('enabled',True) else '','checked' if c.get('mqtt',{}).get('listen_enabled',True) else '','checked' if c.get('watchdog',{}).get('enabled',True) else ''))
print('<section class="card"><h2>Fire TV hinzufügen</h2><div class="body"><p class="muted">Bequemer geht es über die automatische Gerätesuche.</p><form method="post">%s<input type="hidden" name="form_action" value="add_device"><div class="form-grid"><div class="field"><label>Name</label><input name="name" maxlength="80" placeholder="Wohnzimmer" required></div><div class="field"><label>IP / Hostname</label><input name="ip" maxlength="253" placeholder="192.168.1.50" required></div><div class="field"><label>ADB-Port</label><input name="port" type="number" min="1" max="65535" value="5555"></div></div><p><button class="btn btn-green">Hinzufügen</button> <a class="btn" href="discover.cgi" style="text-decoration:none">Automatisch suchen</a></p></form></div></section>'%csrf_h)
print('<section class="card"><h2>Geräte</h2><div class="body">')
if not c.get('devices'):print('<p class="muted">Noch keine Geräte angelegt.</p>')
for d in c.get('devices',[]):
 ident=html.escape(str(d.get('id','')),quote=True)
 print('<div class="device"><div><b>%s</b><br><span class="muted">%s:%s · <code>%s</code></span></div><form method="post">%s<input type="hidden" name="form_action" value="delete"><input type="hidden" name="id" value="%s"><button class="btn btn-red">Löschen</button></form></div>'%(html.escape(str(d.get('name',''))),html.escape(str(d.get('ip',''))),d.get('port',5555),html.escape(str(d.get('id',''))),csrf_h,ident))
print('</div></section><div class="footer">Fire TV Control · Marco Düthorn · 2026 · v%s</div></div></body></html>'%html.escape(version()))
