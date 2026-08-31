#!/usr/bin/env python3
import hashlib,hmac,html,json,os,re,tempfile,sys
from urllib.parse import parse_qs
SAFE_ACTIONS=['tvon','tvoff','home','back','up','down','left','right','ok','menu','playpause','volumeup','volumedown','mute','app']
def root():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);m=os.sep+'webfrontend'+os.sep
 if m in p:return p.split(m,1)[0]
 r=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME')
 if r:return r
 raise RuntimeError('LoxBerry Basisverzeichnis konnte nicht ermittelt werden')
def folder():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);parts=p.split(os.sep)
 return parts[parts.index('plugins')+1] if 'plugins' in parts else 'firetv'
def form():
 data={}
 if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
  try:n=min(max(int(os.environ.get('CONTENT_LENGTH','0') or 0),0),65536)
  except ValueError:n=0
  raw=sys.stdin.buffer.read(n) if n else b''
  for k,v in parse_qs(raw.decode('utf-8','replace'),keep_blank_values=True).items():data[k]=v[-1] if v else ''
 return data
FOLDER=folder();CFG=os.path.join(root(),'config','plugins',FOLDER,'config.json')
def load():return json.load(open(CFG,encoding='utf-8'))
def save(c):
 fd,tmp=tempfile.mkstemp(prefix='.config-',dir=os.path.dirname(CFG),text=True)
 with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(c,f,ensure_ascii=False,indent=2);f.write('\n')
 os.chmod(tmp,0o600);os.replace(tmp,CFG)
def token(c):return hmac.new(str(c.get('web_secret','')).encode(),(os.environ.get('HTTP_COOKIE','')+'|'+os.environ.get('HTTP_USER_AGENT','')).encode(),hashlib.sha256).hexdigest()
def same_site():
 if os.environ.get('HTTP_SEC_FETCH_SITE','').lower()=='cross-site':return False
 host=os.environ.get('HTTP_HOST','').lower()
 for k in ('HTTP_ORIGIN','HTTP_REFERER'):
  v=os.environ.get(k,'').lower();m=re.match(r'^https?://([^/]+)',v) if v and host else None
  if m and m.group(1)!=host:return False
 return True
c=load();f=form();msg='';err=''
if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
 try:
  if not same_site() or not hmac.compare_digest(f.get('csrf',''),token(c)):raise ValueError('Sicherheitsprüfung fehlgeschlagen.')
  m=c.setdefault('mqtt',{})
  m['allow_reboot']=bool(f.get('allow_reboot'));m['allow_text']=bool(f.get('allow_text'))
  selected=[a for a in SAFE_ACTIONS if f.get('allow_'+a)]
  m['allowed_actions']=selected;c.setdefault('security',{})['discovery_post_only']=True;c['config_version']=max(int(c.get('config_version',1)),3);save(c);msg='Sicherheitseinstellungen gespeichert.'
 except Exception as e:err=str(e)
m=c.get('mqtt',{});allowed=set(m.get('allowed_actions',SAFE_ACTIONS));listen=bool(m.get('listen_enabled',True));danger=bool(m.get('allow_reboot')) or bool(m.get('allow_text'));score=100
if listen:score-=15
if danger:score-=25
if not c.get('web_secret'):score-=40
if not c.get('security',{}).get('discovery_post_only',True):score-=15
level='Sehr gut' if score>=85 else ('Gut' if score>=70 else ('Verbesserbar' if score>=50 else 'Kritisch'))
headers='Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src \'none\'; style-src \'unsafe-inline\'; form-action \'self\'; base-uri \'none\'; frame-ancestors \'none\'\r\nX-Frame-Options: DENY\r\nPermissions-Policy: camera=(), microphone=(), geolocation=()\r\n\r\n'
print(headers,end='')
print('''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Sicherheit</title><style>body{font-family:system-ui;background:#0f141a;color:#fff;margin:0}.wrap{max-width:950px;margin:auto;padding:24px}.card{background:#18212b;border:1px solid #2a3948;border-radius:16px;padding:18px;margin:14px 0}a,button{background:#ff9900;color:#111;border:0;border-radius:9px;padding:9px 13px;text-decoration:none;font-weight:700}.good{color:#71e39b}.warn{color:#ffbd66}.bad{color:#ff8088}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}.pill{padding:8px 10px;border-radius:10px;background:#101820}.muted{color:#9fb0c0}label{display:block;margin:7px 0}</style></head><body><div class="wrap"><p><a href="config.cgi">← Konfiguration</a> <a href="discover.cgi">Gerätesuche</a></p><h1>Security Center</h1>''')
if msg:print('<div class="card good">%s</div>'%html.escape(msg))
if err:print('<div class="card bad">%s</div>'%html.escape(err))
print('<div class="card"><h2>Bewertung: <span class="%s">%s · %d/100</span></h2><div class="grid">'%('good' if score>=85 else 'warn' if score>=70 else 'bad',level,score))
print('<div class="pill">CSRF/Webschutz<br><b class="good">Aktiv</b></div><div class="pill">Discovery<br><b class="good">POST + CSRF</b></div><div class="pill">MQTT-Steuerung<br><b class="%s">%s</b></div><div class="pill">Riskante MQTT-Befehle<br><b class="%s">%s</b></div></div></div>'%('warn' if listen else 'good','Aktiv' if listen else 'Aus','bad' if danger else 'good','Freigegeben' if danger else 'Gesperrt'))
print('<div class="card"><h2>MQTT-Befehls-Whitelist</h2><p class="muted">Nur markierte Aktionen werden über MQTT akzeptiert.</p><form method="post"><input type="hidden" name="csrf" value="%s">'%html.escape(token(c),quote=True))
for a in SAFE_ACTIONS:print('<label><input type="checkbox" name="allow_%s" %s> %s</label>'%(a,'checked' if a in allowed else '',html.escape(a)))
print('<hr><label><input type="checkbox" name="allow_reboot" %s> Reboot über MQTT erlauben</label><label><input type="checkbox" name="allow_text" %s> Texteingabe über MQTT erlauben</label><p><button>Speichern</button></p></form></div>'%('checked' if m.get('allow_reboot') else '','checked' if m.get('allow_text') else ''))
print('<div class="card"><h2>Netzwerkhinweis</h2><p>ADB auf TCP 5555 sollte in der Firewall nur vom LoxBerry zum Fire TV erlaubt sein. Das Security Center kann die UniFi-/Router-Firewall nicht automatisch prüfen.</p></div><footer class="muted">Fire TV Control · Marco Düthorn · 2026 · v0.3.0</footer></div></body></html>')
