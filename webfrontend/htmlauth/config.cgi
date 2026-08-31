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
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);parts=p.split(os.sep)
 return parts[parts.index('plugins')+1] if 'plugins' in parts else 'firetv'
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
print('''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Konfiguration</title><style>body{font-family:system-ui;background:#0f141a;color:#fff;margin:0}.wrap{max-width:950px;margin:auto;padding:24px}.card{background:#18212b;border:1px solid #2a3948;border-radius:16px;padding:18px;margin:14px 0}a,button{background:#ff9900;color:#111;border:0;border-radius:9px;padding:9px 13px;text-decoration:none;font-weight:700}input{padding:9px;border-radius:8px;border:1px solid #3a4a59;margin:4px}.muted{color:#9fb0c0}.danger{background:#5d2529;color:#fff}</style></head><body><div class="wrap"><h1>Fire TV Control – Konfiguration</h1><p><a href="index.cgi">Dashboard</a> <a href="discover.cgi">🔎 Fire TVs suchen</a> <a href="security.cgi">🔒 Security Center</a> <a href="debug.cgi">Debug</a></p>''')
if notice:print('<div class="card"><b>%s</b></div>'%html.escape(notice))
if error:print('<div class="card"><b>%s</b></div>'%html.escape(error))
csrf_h='<input type="hidden" name="csrf" value="%s">'%html.escape(token,quote=True)
print('<div class="card"><h2>Allgemein</h2><form method="post">%s<input type="hidden" name="form_action" value="save_general"><label>Abfrageintervall <input type="number" min="10" max="3600" name="poll_interval" value="%s"></label><br><label>MQTT Basistopic <input name="base_topic" maxlength="128" value="%s"></label><br><label><input type="checkbox" name="mqtt_enabled" %s> MQTT aktiv</label><br><label><input type="checkbox" name="mqtt_listen" %s> Befehle empfangen</label><br><label><input type="checkbox" name="watchdog_enabled" %s> Watchdog aktiv</label><br><button>Speichern</button></form><p class="muted">MQTT-Befehlsrechte werden im Security Center festgelegt.</p></div>'%(csrf_h,c.get('poll_interval',30),html.escape(c.get('mqtt',{}).get('base_topic','firetv'),quote=True),'checked' if c.get('mqtt',{}).get('enabled',True) else '','checked' if c.get('mqtt',{}).get('listen_enabled',True) else '','checked' if c.get('watchdog',{}).get('enabled',True) else ''))
print('<div class="card"><h2>Fire TV hinzufügen</h2><p class="muted">Oder komfortabel über „Fire TVs suchen“ oben.</p><form method="post">%s<input type="hidden" name="form_action" value="add_device"><input name="name" maxlength="80" placeholder="Wohnzimmer" required><input name="ip" maxlength="253" placeholder="192.168.1.50" required><input name="port" type="number" min="1" max="65535" value="5555"><button>Hinzufügen</button></form></div><div class="card"><h2>Geräte</h2>'%csrf_h)
for d in c.get('devices',[]):
 ident=html.escape(str(d.get('id','')),quote=True)
 print('<p><b>%s</b> · %s:%s · <code>%s</code></p><form method="post">%s<input type="hidden" name="form_action" value="delete"><input type="hidden" name="id" value="%s"><button class="danger">Löschen</button></form>'%(html.escape(str(d.get('name',''))),html.escape(str(d.get('ip',''))),d.get('port',5555),html.escape(str(d.get('id',''))),csrf_h,ident))
print('</div><footer class="muted">Fire TV Control · Marco Düthorn · 2026 · v0.3.0</footer></div></body></html>')
