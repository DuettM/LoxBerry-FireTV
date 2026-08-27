#!/usr/bin/env python3
import cgi,html,json,os,subprocess
ROOT=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME') or '/opt/loxberry';FOLDER='firetv';CFG=os.path.join(ROOT,'config','plugins',FOLDER,'config.json');BIN=os.path.join(ROOT,'bin','plugins',FOLDER)
f=cgi.FieldStorage();c=json.load(open(CFG,encoding='utf-8'));msg=''
if f.getfirst('device') and f.getfirst('action'):
 cmd=[os.path.join(BIN,'firetv.py'),'--config',CFG,'--device',f.getfirst('device'),'--action',f.getfirst('action')]
 if f.getfirst('value'):cmd+=['--value',f.getfirst('value')]
 try:msg=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=15).stdout.strip()
 except Exception as e:msg=str(e)
print('Content-Type: text/html; charset=utf-8\n')
print('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Control</title><style>body{font-family:system-ui;background:#f3f5f7;margin:0;color:#1f2937}header{background:#232f3e;color:#fff;padding:18px}header a{color:#fff;margin-right:15px}.wrap{max-width:1100px;margin:20px auto;padding:0 15px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}.card{background:#fff;border-radius:12px;padding:18px;box-shadow:0 1px 4px #0002}.ok{color:#188038}.bad{color:#b3261e}button{background:#ff9900;border:0;border-radius:7px;padding:9px 12px;margin:3px}.remote{display:grid;grid-template-columns:repeat(3,56px);gap:4px;justify-content:center}.remote button{margin:0}input{padding:8px}</style></head><body><header><h1>Fire TV Control</h1><a href="config.cgi">Konfiguration</a><a href="debug.cgi">Debug</a></header><div class="wrap">')
if msg:print('<div class="card"><pre>%s</pre></div>'%html.escape(msg))
print('<div class="grid">')
for d in c.get('devices',[]):
 if not d.get('enabled',True):continue
 ident=d.get('id') or d.get('name') or d.get('ip')
 try:
  p=subprocess.run([os.path.join(BIN,'firetv.py'),'--config',CFG,'--device',str(ident),'--action','status'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=12);st=json.loads(p.stdout.strip().splitlines()[-1])
 except Exception as e:st={'online':False,'error':str(e)}
 print('<section class="card"><h2>%s</h2><p class="%s"><b>%s</b> · %s:%s</p><p>ADB: %s · Bildschirm: %s</p><p>App: <b>%s</b></p>'%(html.escape(str(d.get('name','Fire TV'))),'ok' if st.get('online') else 'bad','ONLINE' if st.get('online') else 'OFFLINE',html.escape(str(d.get('ip',''))),d.get('port',5555),'autorisiert' if st.get('authorized') else 'nicht autorisiert','an' if st.get('awake') else 'Standby',html.escape(st.get('app','—') or '—')))
 print('<form method="post"><input type="hidden" name="device" value="%s"><div class="remote"><span></span><button name="action" value="up">▲</button><span></span><button name="action" value="left">◀</button><button name="action" value="ok">OK</button><button name="action" value="right">▶</button><span></span><button name="action" value="down">▼</button><span></span></div><p style="text-align:center"><button name="action" value="back">Zurück</button><button name="action" value="home">Home</button><button name="action" value="menu">Menü</button></p><p style="text-align:center"><button name="action" value="playpause">Play/Pause</button><button name="action" value="volumedown">Vol −</button><button name="action" value="mute">Mute</button><button name="action" value="volumeup">Vol +</button></p><p style="text-align:center"><button name="action" value="wakeup">Aufwecken</button><button name="action" value="standby">Standby</button></p><p><input name="value" placeholder="netflix / youtube / Package-ID"><button name="action" value="app">App starten</button></p></form></section>'%html.escape(str(ident),quote=True))
print('</div>')
if not c.get('devices'):print('<div class="card"><h2>Noch kein Fire TV angelegt</h2><p>Unter Konfiguration ein Gerät hinzufügen.</p></div>')
print('<footer style="text-align:center;margin:30px">Düthorn Marco · 2026 · Fire TV Control v0.1.0</footer></div></body></html>')
