#!/usr/bin/env python3
import hashlib,hmac,html,json,os,re,subprocess,sys
from urllib.parse import parse_qs

def root():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__)
 marker=os.sep+'webfrontend'+os.sep
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
  ctype=(os.environ.get('CONTENT_TYPE','') or '').split(';',1)[0].strip().lower()
  raw=sys.stdin.buffer.read(length) if length else b''
  if ctype=='application/x-www-form-urlencoded':
   body=parse_qs(raw.decode('utf-8','replace'),keep_blank_values=True)
   for k,v in body.items():data[k]=v[-1] if v else ''
 return data
FOLDER=folder();CFG=os.path.join(root(),'config','plugins',FOLDER,'config.json');BIN=os.path.join(root(),'bin','plugins',FOLDER)
def csrf(c):return hmac.new(str(c.get('web_secret','')).encode(),(os.environ.get('HTTP_COOKIE','')+'|'+os.environ.get('HTTP_USER_AGENT','')).encode(),hashlib.sha256).hexdigest()
def same_site():
 if os.environ.get('HTTP_SEC_FETCH_SITE','').lower()=='cross-site':return False
 host=os.environ.get('HTTP_HOST','').lower()
 for k in ('HTTP_ORIGIN','HTTP_REFERER'):
  v=os.environ.get(k,'').lower()
  if v and host:
   m=re.match(r'^https?://([^/]+)',v)
   if m and m.group(1)!=host:return False
 return True
try:
 c=json.load(open(CFG,encoding='utf-8'))
except Exception as e:
 print('Status: 500 Internal Server Error\r\nContent-Type: text/html; charset=utf-8\r\n\r\n',end='')
 print('<h1>Fire TV Control</h1><p>Konfiguration konnte nicht geladen werden: %s</p>'%html.escape(str(e)))
 sys.exit(0)
f=form_data();msg='';err='';token=csrf(c)
if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
 try:
  sent=f.get('csrf','') or ''
  if not same_site() or not sent or not hmac.compare_digest(sent,token):raise ValueError('Sicherheitsprüfung fehlgeschlagen.')
  dev=(f.get('device') or '').strip();action=(f.get('action') or '').strip().lower();value=f.get('value')
  allowed={'home','back','up','down','left','right','ok','menu','playpause','volumedown','mute','volumeup','wakeup','standby','app'}
  if action not in allowed:raise ValueError('Ungültiger Befehl.')
  if not dev or len(dev)>128 or re.search(r'[\r\n\x00]',dev):raise ValueError('Gerät ungültig.')
  if value is not None and len(value)>256:raise ValueError('Wert zu lang.')
  cmd=[os.path.join(BIN,'firetv.py'),'--config',CFG,'--device',dev,'--action',action]
  if value:cmd+=['--value',value]
  p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=15);msg=(p.stdout or '').strip()
 except Exception as e:err=str(e)
print('Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\n\r\n')
print('''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Control</title><style>
:root{--bg:#0f141a;--panel:#18212b;--panel2:#202c38;--line:#2a3948;--text:#f7f9fb;--muted:#9fb0c0;--accent:#ff9900;--accent2:#ffb547;--ok:#35c36f;--bad:#ff5b64;--shadow:0 18px 45px rgba(0,0,0,.28)}
*{box-sizing:border-box}body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:linear-gradient(180deg,#0c1117 0,#121923 100%);margin:0;color:var(--text);min-height:100vh}a{color:inherit;text-decoration:none}
.topbar{position:sticky;top:0;z-index:20;background:rgba(15,20,26,.92);backdrop-filter:blur(14px);border-bottom:1px solid #24303c}.topbar-inner{max-width:1240px;margin:auto;padding:14px 18px;display:flex;align-items:center;justify-content:space-between;gap:18px}.brand{display:flex;align-items:center;gap:12px}.logo{width:42px;height:42px;border-radius:12px;background:var(--accent);display:grid;place-items:center;box-shadow:0 8px 24px rgba(255,153,0,.25)}.logo svg{width:24px;height:24px}.brand h1{font-size:18px;margin:0}.brand small{display:block;color:var(--muted);margin-top:2px}.nav{display:flex;gap:8px}.nav a{padding:9px 13px;border-radius:10px;background:#1a2530;color:#d9e3ec;border:1px solid #2c3946;font-size:14px}.nav a:hover{border-color:#46586a;background:#22303d}
.wrap{max-width:1240px;margin:0 auto;padding:24px 18px 38px}.hero{display:flex;justify-content:space-between;align-items:end;gap:18px;margin-bottom:20px}.hero h2{margin:0 0 6px;font-size:28px}.hero p{margin:0;color:var(--muted)}.version{font-size:12px;color:var(--muted);background:#18212b;border:1px solid var(--line);padding:7px 10px;border-radius:999px}
.notice{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:16px;box-shadow:var(--shadow)}.notice pre{white-space:pre-wrap;margin:0;color:#dce6ef}.notice.error{border-color:rgba(255,91,100,.5);color:#ffd7da}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:18px}.card{background:linear-gradient(180deg,#18212b 0,#141c25 100%);border:1px solid var(--line);border-radius:20px;padding:20px;box-shadow:var(--shadow);overflow:hidden}.device-head{display:flex;justify-content:space-between;gap:14px;align-items:start;margin-bottom:16px}.device-title{display:flex;align-items:center;gap:12px}.device-icon{width:44px;height:44px;border-radius:14px;background:#202c38;display:grid;place-items:center;border:1px solid #334353}.device-icon svg{width:26px;height:26px;fill:var(--accent)}.device-title h3{margin:0;font-size:20px}.device-title .addr{font-size:12px;color:var(--muted);margin-top:3px}.pill{padding:6px 10px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.04em}.pill.ok{background:rgba(53,195,111,.14);color:#75e2a0;border:1px solid rgba(53,195,111,.35)}.pill.bad{background:rgba(255,91,100,.13);color:#ff9ca3;border:1px solid rgba(255,91,100,.35)}
.status-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:18px}.status-box{background:#111820;border:1px solid #263440;border-radius:13px;padding:11px 10px}.status-box span{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em}.status-box b{display:block;margin-top:4px;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.section-label{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:#8194a7;margin:18px 0 9px;font-weight:800}
.remote-wrap{display:grid;grid-template-columns:180px 1fr;gap:18px;align-items:center}.remote{width:174px;height:174px;border-radius:50%;background:radial-gradient(circle at center,#253341 0 36%,#18232d 37% 100%);border:1px solid #344554;position:relative;box-shadow:inset 0 0 0 9px #111820}.remote button{position:absolute;width:54px;height:46px;margin:0;border-radius:12px;background:transparent;color:#f5f7f9;font-size:20px}.remote .up{top:9px;left:59px}.remote .down{bottom:9px;left:59px}.remote .left{left:7px;top:64px}.remote .right{right:7px;top:64px}.remote .okbtn{left:55px;top:58px;width:64px;height:58px;border-radius:50%;background:var(--accent);color:#141414;font-size:14px;font-weight:900;box-shadow:0 8px 22px rgba(255,153,0,.25)}
button{font:inherit;border:1px solid #3a4a59;background:#202c38;color:#f7f9fb;border-radius:11px;padding:10px 12px;cursor:pointer;transition:.15s ease}button:hover{transform:translateY(-1px);border-color:#5b6f82;background:#263646}button:active{transform:translateY(0)}button.primary{background:var(--accent);border-color:var(--accent);color:#181818;font-weight:800}.quick{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.quick button{min-height:44px}.power{display:grid;grid-template-columns:1fr 1fr;gap:8px}.power .wake{background:rgba(53,195,111,.13);border-color:rgba(53,195,111,.35);color:#86e8aa}.power .sleep{background:rgba(255,91,100,.11);border-color:rgba(255,91,100,.3);color:#ffadb3}
.app-launch{display:flex;gap:8px}.app-launch input{flex:1;background:#10171f;border:1px solid #31404e;color:#fff;border-radius:11px;padding:11px 12px;min-width:0}.app-launch input:focus{outline:2px solid rgba(255,153,0,.3);border-color:var(--accent)}.empty{padding:32px;text-align:center}.empty h3{margin-top:0}.empty p{color:var(--muted)}footer{text-align:center;color:#718395;font-size:12px;margin-top:30px;padding:10px}
@media(max-width:720px){.topbar-inner{align-items:flex-start}.brand small{display:none}.nav a{padding:8px 9px;font-size:12px}.hero{align-items:flex-start;flex-direction:column}.grid{grid-template-columns:1fr}.card{padding:16px}.remote-wrap{grid-template-columns:1fr}.remote{margin:auto}.status-grid{grid-template-columns:1fr 1fr}.status-grid .status-box:last-child{grid-column:1/-1}.quick{grid-template-columns:1fr 1fr}.app-launch{flex-direction:column}}
</style></head><body><header class="topbar"><div class="topbar-inner"><div class="brand"><div class="logo"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#17202a" d="M4 5h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-6v2h3v1H7v-1h3v-2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zm6 3v8l6-4z"/></svg></div><div><h1>Fire TV Control</h1><small>LoxBerry · Geräte & Steuerung</small></div></div><nav class="nav"><a href="config.cgi">⚙ Konfiguration</a><a href="debug.cgi">⌘ Debug</a></nav></div></header><main class="wrap"><div class="hero"><div><h2>Fire TV Übersicht</h2><p>Status, Apps und Fernbedienung an einem Ort.</p></div><div class="version">v0.2.6</div></div>''')
if msg:print('<div class="notice"><pre>%s</pre></div>'%html.escape(msg))
if err:print('<div class="notice error"><b>%s</b></div>'%html.escape(err))
print('<div class="grid">')
for d in c.get('devices',[]):
 if not d.get('enabled',True):continue
 ident=str(d.get('id') or d.get('name') or d.get('ip'))
 try:
  p=subprocess.run([os.path.join(BIN,'firetv.py'),'--config',CFG,'--device',ident,'--action','status'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=12);st=json.loads((p.stdout or '').strip().splitlines()[-1])
 except Exception as e:st={'online':False,'error':str(e)}
 name=html.escape(str(d.get('name','Fire TV')));addr='%s:%s'%(html.escape(str(d.get('ip',''))),d.get('port',5555));app=html.escape(str(st.get('app','—') or '—'))
 print('<section class="card"><div class="device-head"><div class="device-title"><div class="device-icon"><svg viewBox="0 0 24 24"><path d="M3 5h18a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zm7 3v9l7-4.5z"/></svg></div><div><h3>%s</h3><div class="addr">%s</div></div></div><span class="pill %s">%s</span></div>'%(name,addr,'ok' if st.get('online') else 'bad','ONLINE' if st.get('online') else 'OFFLINE'))
 print('<div class="status-grid"><div class="status-box"><span>ADB</span><b>%s</b></div><div class="status-box"><span>Bildschirm</span><b>%s</b></div><div class="status-box"><span>Aktive App</span><b title="%s">%s</b></div></div>'%('Autorisiert' if st.get('authorized') else 'Nicht autorisiert','An' if st.get('awake') else 'Standby',app,app))
 hidden='<input type="hidden" name="csrf" value="%s"><input type="hidden" name="device" value="%s">'%(html.escape(token,quote=True),html.escape(ident,quote=True))
 print('<form method="post">%s<div class="section-label">Fernbedienung</div><div class="remote-wrap"><div class="remote"><button class="up" name="action" value="up" title="Hoch">▲</button><button class="left" name="action" value="left" title="Links">◀</button><button class="okbtn" name="action" value="ok">OK</button><button class="right" name="action" value="right" title="Rechts">▶</button><button class="down" name="action" value="down" title="Runter">▼</button></div><div><div class="quick"><button name="action" value="back">↩ Zurück</button><button class="primary" name="action" value="home">⌂ Home</button><button name="action" value="menu">☰ Menü</button><button name="action" value="playpause">⏯ Play/Pause</button><button name="action" value="volumedown">− Lautstärke</button><button name="action" value="volumeup">+ Lautstärke</button><button name="action" value="mute">🔇 Mute</button></div><div class="section-label">Power</div><div class="power"><button class="wake" name="action" value="wakeup">● Aufwecken</button><button class="sleep" name="action" value="standby">◐ Standby</button></div></div></div><div class="section-label">App starten</div><div class="app-launch"><input name="value" maxlength="256" placeholder="netflix, youtube oder Package-ID"><button class="primary" name="action" value="app">Starten</button></div></form></section>'%hidden)
print('</div>')
if not c.get('devices'):print('<div class="card empty"><h3>Noch kein Fire TV angelegt</h3><p>Lege unter Konfiguration dein erstes Gerät an.</p><a class="nav" href="config.cgi">Konfiguration öffnen</a></div>')
print('<footer>Fire TV Control · Marco Düthorn · 2026 · v0.2.6</footer></main></body></html>')
