#!/usr/bin/env python3
import hashlib,hmac,html,json,os,re,subprocess,sys
from urllib.parse import parse_qs

def root():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);marker=os.sep+'webfrontend'+os.sep
 if marker in p:return p.split(marker,1)[0]
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
FOLDER=folder();CFG=os.path.join(root(),'config','plugins',FOLDER,'config.json');BIN=os.path.join(root(),'bin','plugins',FOLDER)
def plugin_version():
 try:
  base=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__).split(os.sep+'webfrontend'+os.sep,1)[0]
  with open(os.path.join(base,'plugin.cfg'),encoding='utf-8') as f:
   for line in f:
    if line.startswith('VERSION='):return line.split('=',1)[1].strip()
 except Exception:pass
 return '0.3.5'
VERSION=plugin_version()
def csrf(c):return hmac.new(str(c.get('web_secret','')).encode(),(os.environ.get('HTTP_COOKIE','')+'|'+os.environ.get('HTTP_USER_AGENT','')).encode(),hashlib.sha256).hexdigest()
def same_site():
 if os.environ.get('HTTP_SEC_FETCH_SITE','').lower()=='cross-site':return False
 host=os.environ.get('HTTP_HOST','').lower()
 for k in ('HTTP_ORIGIN','HTTP_REFERER'):
  v=os.environ.get(k,'').lower();m=re.match(r'^https?://([^/]+)',v) if v and host else None
  if m and m.group(1)!=host:return False
 return True
try:c=json.load(open(CFG,encoding='utf-8'))
except Exception as e:
 print('Status: 500 Internal Server Error\r\nContent-Type: text/html; charset=utf-8\r\n\r\n',end='');print('<h1>Fire TV Control</h1><p>%s</p>'%html.escape(str(e)));sys.exit(0)
f=form_data();msg='';err='';token=csrf(c)
if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
 try:
  if not same_site() or not f.get('csrf') or not hmac.compare_digest(f.get('csrf',''),token):raise ValueError('Sicherheitsprüfung fehlgeschlagen.')
  dev=(f.get('device') or '').strip();action=(f.get('action') or '').strip().lower();value=f.get('value')
  allowed={'home','back','up','down','left','right','ok','menu','playpause','volumedown','mute','volumeup','wakeup','standby','app'}
  if action not in allowed:raise ValueError('Ungültiger Befehl.')
  if not dev or len(dev)>128 or re.search(r'[\r\n\x00]',dev):raise ValueError('Gerät ungültig.')
  if value is not None and len(value)>256:raise ValueError('Wert zu lang.')
  cmd=[os.path.join(BIN,'firetv.py'),'--config',CFG,'--device',dev,'--action',action]
  if value:cmd+=['--value',value]
  p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=15);msg=(p.stdout or '').strip()
 except Exception as e:err=str(e)
print("Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: frame-ancestors 'self'\r\nX-Frame-Options: SAMEORIGIN\r\n\r\n",end='')
print('''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Control</title><style>
:root{--green:#73b72b;--green-dark:#4d8e1a;--green-soft:#edf7e5;--text:#29323a;--muted:#71808d;--line:#dde4e8;--bg:#f6f8f9;--red:#d94343;--orange:#ee9c24;--blue:#2f7fc7;--shadow:0 1px 3px #0000000c}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Arial,Helvetica,sans-serif}.root{max-width:1480px;margin:0 auto;padding:12px 12px 28px}.head{display:flex;align-items:center;gap:14px;background:#fff;border:1px solid var(--line);border-radius:9px;padding:13px 16px;margin-bottom:12px}.logo{width:58px;height:58px;border-radius:8px;background:linear-gradient(145deg,#86ca42,#5ba21d);display:grid;place-items:center;box-shadow:0 2px 8px #00000012}.logo svg{width:39px;height:39px}.title{flex:1}.title h1{margin:0 0 4px;color:#257c31;font-size:24px}.title p{margin:0;color:#56616b}.ver{font-size:12px;color:#687680;background:#f7f9fa;border:1px solid var(--line);padding:7px 10px;border-radius:6px}.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:12px}.nav{background:#fff;border:1px solid var(--line);border-radius:9px;padding:8px;height:max-content;position:sticky;top:8px}.nav small{display:block;color:#8a959e;padding:8px 12px 4px;font-size:10px;text-transform:uppercase;letter-spacing:.07em}.nav a{display:flex;gap:10px;align-items:center;padding:11px 12px;border-radius:6px;color:#34404a;font-weight:600;text-decoration:none}.nav a:hover{background:#f5f8f3}.nav a.active{background:#eaf5df;color:#2d7d29}.nav .sep{height:1px;background:#edf0f2;margin:7px 4px}.content{min-width:0}.notice{padding:10px 12px;border-radius:6px;margin-bottom:12px;background:#edf8e8;border:1px solid #cbe5bd;color:#34751f}.notice.err{background:#fff0f0;border-color:#efc0c0;color:#a52828}.metrics{display:grid;grid-template-columns:repeat(4,minmax(150px,1fr));gap:10px;margin-bottom:12px}.metric{background:#fff;border:1px solid var(--line);border-radius:9px;padding:14px;display:flex;align-items:center;gap:12px;min-height:86px}.mic{width:46px;height:46px;border-radius:7px;background:var(--green);color:#fff;display:grid;place-items:center;font-size:22px}.metric b{display:block;font-size:20px}.metric small{color:var(--muted)}.card{background:#fff;border:1px solid var(--line);border-radius:9px;margin-bottom:12px;box-shadow:var(--shadow)}.card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:13px 15px;border-bottom:1px solid #edf0f2}.card-head h2{font-size:17px;margin:0}.state{display:inline-block;padding:4px 8px;border-radius:5px;font-size:12px;font-weight:bold}.state.ok{background:#eff8eb;border:1px solid #cbe1c1;color:#23802a}.state.bad{background:#fff0f0;border:1px solid #efc0c0;color:#b23232}.body{padding:15px}.device-meta{display:grid;grid-template-columns:repeat(4,minmax(120px,1fr));gap:9px;margin-bottom:14px}.meta{background:#fafbfb;border:1px solid #e6ebee;border-radius:7px;padding:10px}.meta span{display:block;color:var(--muted);font-size:11px;text-transform:uppercase}.meta b{display:block;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.remote-grid{display:grid;grid-template-columns:190px 1fr;gap:18px;align-items:center}.remote{width:176px;height:176px;border:1px solid #d5dde2;border-radius:50%;background:#f7f9fa;position:relative;box-shadow:inset 0 0 0 9px #fff}.remote button{position:absolute;width:54px;height:44px;border:0;background:transparent;font-size:19px;color:#3f4a53;cursor:pointer}.remote .up{top:8px;left:60px}.remote .down{bottom:8px;left:60px}.remote .left{left:7px;top:65px}.remote .right{right:7px;top:65px}.remote .okbtn{left:55px;top:57px;width:65px;height:60px;border-radius:50%;background:var(--green);color:#fff;font-weight:bold}.label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#87949e;margin:12px 0 7px;font-weight:bold}.quick{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}.btn{border:1px solid #cdd6dc;background:#fff;border-radius:6px;padding:9px 10px;cursor:pointer;font-weight:600;color:#2f3942}.btn:hover{background:#f5f7f8}.btn-green{background:var(--green);border-color:var(--green);color:#fff}.btn-red{border-color:#f1b3b3;color:var(--red)}.power{display:grid;grid-template-columns:1fr 1fr;gap:7px}.app{display:flex;gap:7px}.app input{flex:1;min-width:0;height:38px;border:1px solid #cbd4da;border-radius:6px;padding:0 10px}.empty{padding:28px;text-align:center}.footer{text-align:center;color:#66727b;padding:14px;font-size:13px}.mobile{display:none}@media(max-width:900px){.layout{grid-template-columns:1fr}.nav{display:none}.mobile{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap}.mobile a{background:#fff;border:1px solid var(--line);padding:9px 11px;border-radius:6px;text-decoration:none;color:#34404a}.metrics{grid-template-columns:repeat(2,1fr)}.device-meta{grid-template-columns:repeat(2,1fr)}}@media(max-width:600px){.head{align-items:flex-start;flex-wrap:wrap}.ver{margin-left:72px}.metrics{grid-template-columns:1fr}.remote-grid{grid-template-columns:1fr}.remote{margin:auto}.quick{grid-template-columns:repeat(2,1fr)}.app{flex-direction:column}}
</style></head><body><div class="root"><div class="head"><div class="logo"><svg viewBox="0 0 64 64"><rect x="8" y="12" width="48" height="34" rx="5" fill="none" stroke="white" stroke-width="4"/><path d="M28 22v14l13-7z" fill="white"/><path d="M24 52h16" stroke="white" stroke-width="4" stroke-linecap="round"/></svg></div><div class="title"><h1>Fire TV Control</h1><p>Fire TV Geräte steuern und in Loxone integrieren</p></div><div class="ver">Version __VER__</div></div><div class="mobile"><a href="dashboard.cgi">⌂ Übersicht</a><a href="config.cgi">⚙ Einstellungen</a><a href="discover.cgi">⌕ Suche</a><a href="security.cgi">🔒 Sicherheit</a><a href="debug.cgi">▤ Debug</a></div><div class="layout"><nav class="nav"><small>Fire TV Control</small><a class="active" href="dashboard.cgi">⌂ Übersicht</a><a href="discover.cgi">⌕ Fire TVs suchen</a><div class="sep"></div><a href="config.cgi">⚙ Einstellungen</a><a href="security.cgi">🔒 Security Center</a><a href="debug.cgi">▤ Debug-Log</a></nav><main class="content">'''.replace('__VER__',html.escape(VERSION)))
if msg:print('<div class="notice"><b>Ausgeführt:</b> %s</div>'%html.escape(msg))
if err:print('<div class="notice err"><b>Fehler:</b> %s</div>'%html.escape(err))
devices=[d for d in c.get('devices',[]) if d.get('enabled',True)]
print('<div class="metrics"><div class="metric"><div class="mic">▣</div><div><b>%d</b>Geräte<br><small>konfiguriert</small></div></div><div class="metric"><div class="mic">↔</div><div><b>%s</b>MQTT<br><small>%s</small></div></div><div class="metric"><div class="mic">✓</div><div><b>%s</b>Watchdog<br><small>Systemüberwachung</small></div></div><div class="metric"><div class="mic">⌁</div><div><b>%ss</b>Polling<br><small>Statusintervall</small></div></div></div>'%(len(devices),'Aktiv' if c.get('mqtt',{}).get('enabled',True) else 'Aus','Befehle aktiv' if c.get('mqtt',{}).get('listen_enabled',True) else 'nur Status','Aktiv' if c.get('watchdog',{}).get('enabled',True) else 'Aus',c.get('poll_interval',30)))
for d in devices:
 ident=str(d.get('id') or d.get('name') or d.get('ip'))
 try:
  p=subprocess.run([os.path.join(BIN,'firetv.py'),'--config',CFG,'--device',ident,'--action','status'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=12);st=json.loads((p.stdout or '').strip().splitlines()[-1])
 except Exception as e:st={'online':False,'error':str(e)}
 name=html.escape(str(d.get('name','Fire TV')));addr='%s:%s'%(html.escape(str(d.get('ip',''))),d.get('port',5555));app=html.escape(str(st.get('app','—') or '—'));model=html.escape(str(st.get('model','—') or '—'))
 print('<section class="card"><div class="card-head"><h2>▣ %s</h2><span class="state %s">%s</span></div><div class="body">'%(name,'ok' if st.get('online') else 'bad','ONLINE' if st.get('online') else 'OFFLINE'))
 print('<div class="device-meta"><div class="meta"><span>Adresse</span><b>%s</b></div><div class="meta"><span>ADB</span><b>%s</b></div><div class="meta"><span>Bildschirm</span><b>%s</b></div><div class="meta"><span>Aktive App</span><b title="%s">%s</b></div></div>'%(addr,'Autorisiert' if st.get('authorized') else 'Nicht autorisiert','An' if st.get('awake') else 'Standby',app,app))
 hidden='<input type="hidden" name="csrf" value="%s"><input type="hidden" name="device" value="%s">'%(html.escape(token,quote=True),html.escape(ident,quote=True))
 print('<form method="post">%s<div class="remote-grid"><div class="remote"><button class="up" name="action" value="up">▲</button><button class="left" name="action" value="left">◀</button><button class="okbtn" name="action" value="ok">OK</button><button class="right" name="action" value="right">▶</button><button class="down" name="action" value="down">▼</button></div><div><div class="label">Fernbedienung</div><div class="quick"><button class="btn" name="action" value="back">↩ Zurück</button><button class="btn btn-green" name="action" value="home">⌂ Home</button><button class="btn" name="action" value="menu">☰ Menü</button><button class="btn" name="action" value="playpause">⏯ Play/Pause</button><button class="btn" name="action" value="volumedown">− Leiser</button><button class="btn" name="action" value="volumeup">+ Lauter</button><button class="btn" name="action" value="mute">🔇 Mute</button></div><div class="label">Power / CEC</div><div class="power"><button class="btn btn-green" name="action" value="wakeup">● Einschalten</button><button class="btn btn-red" name="action" value="standby">◐ Standby</button></div><div class="label">App starten</div><div class="app"><input name="value" maxlength="256" placeholder="netflix, youtube oder Package-ID"><button class="btn btn-green" name="action" value="app">Starten</button></div><div class="label">Gerät</div><div style="color:var(--muted);font-size:12px">%s</div></div></div></form></div></section>'%(hidden,model))
if not devices:print('<div class="card"><div class="empty"><h2>Noch kein Fire TV eingerichtet</h2><p>Nutze die automatische Suche oder trage ein Gerät manuell ein.</p><a class="btn btn-green" href="discover.cgi" style="text-decoration:none;display:inline-block">Fire TVs suchen</a></div></div>')
print('</main></div><div class="footer">Fire TV Control · Marco Düthorn · 2026 · v%s</div></div></body></html>'%html.escape(VERSION))
