#!/usr/bin/env python3
import cgi,hashlib,hmac,html,json,os,re,subprocess

def root(): return os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME') or '/opt/loxberry'
def folder():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);parts=p.split(os.sep);return parts[parts.index('plugins')+1] if 'plugins' in parts else 'firetv'
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
c=json.load(open(CFG,encoding='utf-8'));f=cgi.FieldStorage();msg='';err='';token=csrf(c)
if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
 try:
  sent=f.getfirst('csrf','') or ''
  if not same_site() or not sent or not hmac.compare_digest(sent,token):raise ValueError('Sicherheitsprüfung fehlgeschlagen.')
  dev=(f.getfirst('device') or '').strip();action=(f.getfirst('action') or '').strip().lower();value=f.getfirst('value')
  allowed={'home','back','up','down','left','right','ok','menu','playpause','volumedown','mute','volumeup','wakeup','standby','app'}
  if action not in allowed:raise ValueError('Ungültiger Befehl.')
  if not dev or len(dev)>128 or re.search(r'[\r\n\x00]',dev):raise ValueError('Gerät ungültig.')
  if value is not None and len(value)>256:raise ValueError('Wert zu lang.')
  cmd=[os.path.join(BIN,'firetv.py'),'--config',CFG,'--device',dev,'--action',action]
  if value:cmd+=['--value',value]
  p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=15);msg=(p.stdout or '').strip()
 except Exception as e:err=str(e)
print('Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\n\r\n')
print('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Control</title><style>body{font-family:system-ui;background:#f3f5f7;margin:0;color:#1f2937}header{background:#232f3e;color:#fff;padding:18px}header a{color:#fff;margin-right:15px}.wrap{max-width:1100px;margin:20px auto;padding:0 15px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}.card{background:#fff;border-radius:12px;padding:18px;box-shadow:0 1px 4px #0002}.ok{color:#188038}.bad{color:#b3261e}button{background:#ff9900;border:0;border-radius:7px;padding:9px 12px;margin:3px}.remote{display:grid;grid-template-columns:repeat(3,56px);gap:4px;justify-content:center}.remote button{margin:0}input{padding:8px}.err{color:#b3261e}</style></head><body><header><h1>Fire TV Control</h1><a href="config.cgi">Konfiguration</a><a href="debug.cgi">Debug</a></header><div class="wrap">')
if msg:print('<div class="card"><pre>%s</pre></div>'%html.escape(msg))
if err:print('<div class="card err"><b>%s</b></div>'%html.escape(err))
print('<div class="grid">')
for d in c.get('devices',[]):
 if not d.get('enabled',True):continue
 ident=str(d.get('id') or d.get('name') or d.get('ip'))
 try:
  p=subprocess.run([os.path.join(BIN,'firetv.py'),'--config',CFG,'--device',ident,'--action','status'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=12);st=json.loads((p.stdout or '').strip().splitlines()[-1])
 except Exception as e:st={'online':False,'error':str(e)}
 print('<section class="card"><h2>%s</h2><p class="%s"><b>%s</b> · %s:%s</p><p>ADB: %s · Bildschirm: %s</p><p>App: <b>%s</b></p>'%(html.escape(str(d.get('name','Fire TV'))),'ok' if st.get('online') else 'bad','ONLINE' if st.get('online') else 'OFFLINE',html.escape(str(d.get('ip',''))),d.get('port',5555),'autorisiert' if st.get('authorized') else 'nicht autorisiert','an' if st.get('awake') else 'Standby',html.escape(str(st.get('app','—') or '—'))))
 hidden='<input type="hidden" name="csrf" value="%s"><input type="hidden" name="device" value="%s">'%(html.escape(token,quote=True),html.escape(ident,quote=True))
 print('<form method="post">%s<div class="remote"><span></span><button name="action" value="up">▲</button><span></span><button name="action" value="left">◀</button><button name="action" value="ok">OK</button><button name="action" value="right">▶</button><span></span><button name="action" value="down">▼</button><span></span></div><p style="text-align:center"><button name="action" value="back">Zurück</button><button name="action" value="home">Home</button><button name="action" value="menu">Menü</button></p><p style="text-align:center"><button name="action" value="playpause">Play/Pause</button><button name="action" value="volumedown">Vol −</button><button name="action" value="mute">Mute</button><button name="action" value="volumeup">Vol +</button></p><p style="text-align:center"><button name="action" value="wakeup">Aufwecken</button><button name="action" value="standby">Standby</button></p><p><input name="value" maxlength="256" placeholder="netflix / youtube / Package-ID"><button name="action" value="app">App starten</button></p></form></section>'%hidden)
print('</div>')
if not c.get('devices'):print('<div class="card"><h2>Noch kein Fire TV angelegt</h2><p>Unter Konfiguration ein Gerät hinzufügen.</p></div>')
print('<footer style="text-align:center;margin:30px">Fire TV Control · v0.2.0</footer></div></body></html>')
