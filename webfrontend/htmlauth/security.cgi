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
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);parts=p.split(os.sep);return parts[parts.index('plugins')+1] if 'plugins' in parts else 'firetv'
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
def version():
 try:
  base=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__).split(os.sep+'webfrontend'+os.sep,1)[0]
  with open(os.path.join(base,'plugin.cfg'),encoding='utf-8') as f:
   for line in f:
    if line.startswith('VERSION='):return line.split('=',1)[1].strip()
 except Exception:pass
 return '0.3.1'
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
  m=c.setdefault('mqtt',{});m['allow_reboot']=bool(f.get('allow_reboot'));m['allow_text']=bool(f.get('allow_text'));m['allowed_actions']=[a for a in SAFE_ACTIONS if f.get('allow_'+a)];c.setdefault('security',{})['discovery_post_only']=True;c['config_version']=max(int(c.get('config_version',1)),3);save(c);msg='Sicherheitseinstellungen gespeichert.'
 except Exception as e:err=str(e)
m=c.get('mqtt',{});allowed=set(m.get('allowed_actions',SAFE_ACTIONS));listen=bool(m.get('listen_enabled',True));danger=bool(m.get('allow_reboot')) or bool(m.get('allow_text'));score=100
if listen:score-=15
if danger:score-=25
if not c.get('web_secret'):score-=40
if not c.get('security',{}).get('discovery_post_only',True):score-=15
level='Sehr gut' if score>=85 else ('Gut' if score>=70 else ('Verbesserbar' if score>=50 else 'Kritisch'))
print("Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'\r\nX-Frame-Options: DENY\r\nPermissions-Policy: camera=(), microphone=(), geolocation=()\r\n\r\n",end='')
print('''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Sicherheit</title><style>:root{--green:#73b72b;--text:#29323a;--muted:#71808d;--line:#dde4e8;--bg:#f6f8f9;--red:#d94343;--orange:#ee9c24}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Arial,Helvetica,sans-serif}.root{max-width:1180px;margin:auto;padding:12px}.head{display:flex;align-items:center;gap:14px;background:#fff;border:1px solid var(--line);border-radius:9px;padding:13px 16px;margin-bottom:12px}.logo{width:54px;height:54px;border-radius:8px;background:linear-gradient(145deg,#86ca42,#5ba21d);display:grid;place-items:center;color:#fff;font-size:27px}.title{flex:1}.title h1{margin:0;color:#257c31;font-size:23px}.title p{margin:3px 0 0;color:#56616b}.ver{font-size:12px;color:#687680}.nav{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px}.nav a{background:#fff;border:1px solid var(--line);border-radius:6px;padding:9px 11px;text-decoration:none;color:#34404a;font-weight:600}.nav a.active{background:#edf7e5;color:#2d7d29;border-color:#cbe1c1}.card{background:#fff;border:1px solid var(--line);border-radius:9px;margin-bottom:12px}.card h2{font-size:17px;margin:0;padding:13px 15px;border-bottom:1px solid #edf0f2}.body{padding:15px}.score{display:flex;align-items:center;gap:18px;flex-wrap:wrap}.score-num{width:86px;height:86px;border-radius:50%;display:grid;place-items:center;background:#edf8e8;border:7px solid #bddd9f;font-size:22px;font-weight:bold;color:#2d7d29}.grid{display:grid;grid-template-columns:repeat(4,minmax(150px,1fr));gap:9px}.metric{border:1px solid #e3e8eb;background:#fafbfb;border-radius:7px;padding:11px}.metric small{display:block;color:var(--muted);margin-bottom:4px}.good{color:#278c2b}.warn{color:#b87410}.bad{color:#cf3838}.actions{display:grid;grid-template-columns:repeat(3,minmax(170px,1fr));gap:8px}.actions label{padding:9px;border:1px solid #e2e7ea;border-radius:6px;background:#fafbfb}.dangerbox{margin-top:14px;padding:12px;border:1px solid #efc0c0;background:#fff5f5;border-radius:7px}.btn{border:1px solid #cdd6dc;background:#fff;border-radius:6px;padding:9px 12px;cursor:pointer;font-weight:600}.btn-green{background:var(--green);border-color:var(--green);color:#fff}.notice{padding:10px 12px;border-radius:6px;margin-bottom:12px}.okmsg{background:#edf8e8;border:1px solid #cbe5bd;color:#34751f}.errmsg{background:#fff0f0;border:1px solid #efc0c0;color:#a52828}.muted{color:var(--muted)}.footer{text-align:center;color:#66727b;padding:16px;font-size:13px}@media(max-width:800px){.grid{grid-template-columns:repeat(2,1fr)}.actions{grid-template-columns:1fr}.head{flex-wrap:wrap}}@media(max-width:480px){.grid{grid-template-columns:1fr}}</style></head><body><div class="root"><div class="head"><div class="logo">🔒</div><div class="title"><h1>Security Center</h1><p>Sicherheitsstatus und MQTT-Berechtigungen</p></div><div class="ver">Version __VER__</div></div><div class="nav"><a href="index.cgi">⌂ Übersicht</a><a href="config.cgi">⚙ Einstellungen</a><a href="discover.cgi">⌕ Fire TVs suchen</a><a class="active" href="security.cgi">🔒 Security Center</a><a href="debug.cgi">▤ Debug</a></div>'''.replace('__VER__',html.escape(version())))
if msg:print('<div class="notice okmsg">%s</div>'%html.escape(msg))
if err:print('<div class="notice errmsg">%s</div>'%html.escape(err))
cls='good' if score>=85 else 'warn' if score>=70 else 'bad'
print('<section class="card"><h2>Sicherheitsbewertung</h2><div class="body"><div class="score"><div class="score-num">%d</div><div><h3 class="%s" style="margin:0 0 5px">%s</h3><span class="muted">Bewertung der aktuellen Plugin-Konfiguration</span></div></div><div class="grid" style="margin-top:15px"><div class="metric"><small>Webschutz</small><b class="good">CSRF aktiv</b></div><div class="metric"><small>Gerätesuche</small><b class="good">POST + CSRF</b></div><div class="metric"><small>MQTT-Steuerung</small><b class="%s">%s</b></div><div class="metric"><small>Riskante Befehle</small><b class="%s">%s</b></div></div></div></section>'%(score,cls,level,'warn' if listen else 'good','Aktiv' if listen else 'Aus','bad' if danger else 'good','Freigegeben' if danger else 'Gesperrt'))
print('<section class="card"><h2>MQTT-Befehls-Whitelist</h2><div class="body"><p class="muted">Nur markierte Aktionen werden über MQTT akzeptiert.</p><form method="post"><input type="hidden" name="csrf" value="%s"><div class="actions">'%html.escape(token(c),quote=True))
for a in SAFE_ACTIONS:print('<label><input type="checkbox" name="allow_%s" %s> %s</label>'%(a,'checked' if a in allowed else '',html.escape(a)))
print('</div><div class="dangerbox"><b>Erweiterte Freigaben</b><p><label><input type="checkbox" name="allow_reboot" %s> Reboot über MQTT erlauben</label></p><p><label><input type="checkbox" name="allow_text" %s> Texteingabe über MQTT erlauben</label></p></div><p><button class="btn btn-green">Speichern</button></p></form></div></section>'%('checked' if m.get('allow_reboot') else '','checked' if m.get('allow_text') else ''))
print('<section class="card"><h2>Netzwerksicherheit</h2><div class="body"><p>ADB auf TCP-Port 5555 sollte in der Firewall ausschließlich vom LoxBerry zum jeweiligen Fire TV erlaubt sein.</p><p class="muted">Die Router-/UniFi-Firewall kann vom Plugin nicht automatisch bewertet werden.</p></div></section><div class="footer">Fire TV Control · Marco Düthorn · 2026 · v%s</div></div></body></html>'%html.escape(version()))
