#!/usr/bin/env python3
import cgi,hashlib,hmac,html,ipaddress,json,os,re,tempfile,sys

def root():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__)
 marker=os.sep+'webfrontend'+os.sep
 if marker in p:return p.split(marker,1)[0]
 r=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME')
 if r:return r
 raise RuntimeError('LoxBerry Basisverzeichnis konnte nicht ermittelt werden')
def folder():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__)
 parts=p.split(os.sep)
 return parts[parts.index('plugins')+1] if 'plugins' in parts else 'firetv'
FOLDER=folder();CFG=os.path.join(root(),'config','plugins',FOLDER,'config.json')
def load():
 with open(CFG,encoding='utf-8') as f:return json.load(f)
def save(c):
 fd,tmp=tempfile.mkstemp(prefix='.config-',dir=os.path.dirname(CFG),text=True)
 with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(c,f,ensure_ascii=False,indent=2);f.write('\n')
 os.chmod(tmp,0o600);os.replace(tmp,CFG)
def csrf(c):return hmac.new(str(c.get('web_secret','')).encode(),(os.environ.get('HTTP_COOKIE','')+'|'+os.environ.get('HTTP_USER_AGENT','')).encode(),hashlib.sha256).hexdigest()
def valid_csrf(c,v):return bool(v) and hmac.compare_digest(v,csrf(c))
def same_site():
 if os.environ.get('HTTP_SEC_FETCH_SITE','').lower()=='cross-site':return False
 host=os.environ.get('HTTP_HOST','').lower()
 for k in ('HTTP_ORIGIN','HTTP_REFERER'):
  v=os.environ.get(k,'').lower()
  if v and host:
   m=re.match(r'^https?://([^/]+)',v)
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
 print('Status: 500 Internal Server Error\r\nContent-Type: text/html; charset=utf-8\r\n\r\n',end='')
 print('<h1>Fire TV Control</h1><p>Konfiguration konnte nicht geladen werden: %s</p>'%html.escape(str(e)));sys.exit(0)
f=cgi.FieldStorage();notice='';error='';token=csrf(c)
if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
 try:
  if not same_site() or not valid_csrf(c,f.getfirst('csrf','')):raise ValueError('Sicherheitsprüfung fehlgeschlagen.')
  act=f.getfirst('form_action','')
  if act=='save_general':
   poll=int(f.getfirst('poll_interval','30'))
   if poll<10 or poll>3600:raise ValueError('Abfrageintervall muss zwischen 10 und 3600 Sekunden liegen.')
   c['poll_interval']=poll;c.setdefault('mqtt',{})['enabled']=bool(f.getfirst('mqtt_enabled'));c['mqtt']['listen_enabled']=bool(f.getfirst('mqtt_listen'));c['mqtt']['base_topic']=clean_topic(f.getfirst('base_topic','firetv'));c.setdefault('watchdog',{})['enabled']=bool(f.getfirst('watchdog_enabled'));save(c);notice='Einstellungen gespeichert.'
  elif act=='add_device':
   ip=(f.getfirst('ip','') or '').strip();name=(f.getfirst('name','Fire TV') or '').strip();port=int(f.getfirst('port','5555'))
   if not valid_ip(ip):raise ValueError('IP/Hostname ungültig.')
   if not name or len(name)>80 or re.search(r'[\r\n\x00]',name):raise ValueError('Gerätename ungültig.')
   if port<1 or port>65535:raise ValueError('Port ungültig.')
   ident=re.sub(r'[^a-zA-Z0-9_-]+','-',name.lower()).strip('-') or ip.replace('.','-')
   if any(str(d.get('id'))==ident for d in c.get('devices',[])):raise ValueError('Geräte-ID existiert bereits.')
   c.setdefault('devices',[]).append({'id':ident,'name':name,'ip':ip,'port':port,'enabled':True});save(c);notice='Gerät hinzugefügt. ADB-Verbindung am Fire TV bestätigen.'
  elif act=='delete':
   ident=f.getfirst('id','') or ''
   if len(ident)>128 or re.search(r'[\r\n\x00]',ident):raise ValueError('Geräte-ID ungültig.')
   c['devices']=[d for d in c.get('devices',[]) if str(d.get('id',''))!=ident];save(c);notice='Gerät gelöscht.'
  else:raise ValueError('Unbekannte Aktion.')
 except Exception as e:error=str(e)
print('Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\n\r\n')
print('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Konfiguration</title></head><body><h1>Fire TV Control – Konfiguration</h1><p><a href="index.cgi">Dashboard</a> · <a href="debug.cgi">Debug</a></p>')
if notice:print('<p><b>%s</b></p>'%html.escape(notice))
if error:print('<p><b>%s</b></p>'%html.escape(error))
csrf_h='<input type="hidden" name="csrf" value="%s">'%html.escape(token,quote=True)
print('<section><h2>Allgemein</h2><form method="post">%s<input type="hidden" name="form_action" value="save_general"><label>Abfrageintervall <input type="number" min="10" max="3600" name="poll_interval" value="%s"></label><br><label>MQTT Basistopic <input name="base_topic" maxlength="128" value="%s"></label><br><label><input type="checkbox" name="mqtt_enabled" %s> MQTT aktiv</label><br><label><input type="checkbox" name="mqtt_listen" %s> Befehle empfangen</label><br><label><input type="checkbox" name="watchdog_enabled" %s> Watchdog aktiv</label><br><button>Speichern</button></form></section>'%(csrf_h,c.get('poll_interval',30),html.escape(c.get('mqtt',{}).get('base_topic','firetv'),quote=True),'checked' if c.get('mqtt',{}).get('enabled',True) else '','checked' if c.get('mqtt',{}).get('listen_enabled',True) else '','checked' if c.get('watchdog',{}).get('enabled',True) else ''))
print('<section><h2>Fire TV hinzufügen</h2><form method="post">%s<input type="hidden" name="form_action" value="add_device"><input name="name" maxlength="80" placeholder="Wohnzimmer" required><input name="ip" maxlength="253" placeholder="192.168.1.50" required><input name="port" type="number" min="1" max="65535" value="5555"><button>Hinzufügen</button></form></section><section><h2>Geräte</h2>'%csrf_h)
for d in c.get('devices',[]): print('<p><b>%s</b> · %s:%s · MQTT-ID <code>%s</code></p>'%(html.escape(str(d.get('name',''))),html.escape(str(d.get('ip',''))),d.get('port',5555),html.escape(str(d.get('id','')))))
print('</section><footer>Fire TV Control · Düthorn Marco · 2026 · v0.2.3</footer></body></html>')
