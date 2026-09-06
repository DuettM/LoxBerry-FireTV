#!/usr/bin/env python3
import hashlib,hmac,html,json,os,re,subprocess,sys
from urllib.parse import parse_qs

def root():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);m=os.sep+'webfrontend'+os.sep
 if m in p:return p.split(m,1)[0]
 r=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME')
 if r:return r
 raise RuntimeError('LoxBerry Basisverzeichnis konnte nicht ermittelt werden')
def folder():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);parts=p.split(os.sep);return parts[parts.index('plugins')+1] if 'plugins' in parts else 'firetv'
def version():
 base=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__).split(os.sep+'webfrontend'+os.sep,1)[0]
 # LoxBerry installiert plugin.cfg nicht mit; die installierte Version steht in der
 # Plugindatenbank. plugin.cfg bleibt nur Fallback fuer den Betrieb aus dem Quellordner.
 try:
  db=json.load(open(os.path.join(os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME') or base,'data','system','plugindatabase.json'),encoding='utf-8'))
  for p in db.get('plugins',[]):
   if str(p.get('folder',''))==FOLDER or str(p.get('name',''))=='firetv':
    v=str(p.get('version','') or '').strip()
    if v:return v
 except Exception:pass
 try:
  for line in open(os.path.join(base,'plugin.cfg'),encoding='utf-8'):
   if line.startswith('VERSION='):return line.split('=',1)[1].strip()
 except Exception:pass
 return '0.3.12'
def post_data():
 if os.environ.get('REQUEST_METHOD','GET').upper()!='POST':return {}
 try:n=min(max(int(os.environ.get('CONTENT_LENGTH','0') or 0),0),65536)
 except ValueError:n=0
 raw=sys.stdin.buffer.read(n) if n else b''
 return {k:v[-1] if v else '' for k,v in parse_qs(raw.decode('utf-8','replace'),keep_blank_values=True).items()}
def csrf(c):return hmac.new(str(c.get('web_secret','')).encode(),(os.environ.get('HTTP_COOKIE','')+'|'+os.environ.get('HTTP_USER_AGENT','')).encode(),hashlib.sha256).hexdigest()
def same_site():
 if os.environ.get('HTTP_SEC_FETCH_SITE','').lower()=='cross-site':return False
 host=os.environ.get('HTTP_HOST','').lower()
 for k in ('HTTP_ORIGIN','HTTP_REFERER'):
  v=os.environ.get(k,'').lower();m=re.match(r'^https?://([^/]+)',v) if v and host else None
  if m and m.group(1)!=host:return False
 return True
def broker_secrets(base):
 """Broker-Zugangsdaten stehen in general.json, nicht in der Plugin-Config."""
 try:
  g=json.load(open(os.path.join(base,'config','system','general.json'),encoding='utf-8')).get('Mqtt',{})
  return [str(g.get('Brokerpass','')),str(g.get('Brokeruser',''))]
 except Exception:return []
def redact(line,c,extra=()):
 for s in [str(c.get('web_secret','')),str(c.get('web_api_key','')),str(c.get('mqtt',{}).get('command_token',''))]+list(extra):
  if len(s)>=4:line=line.replace(s,'[REDACTED]')
 line=re.sub(r'(?i)(authorization\s*:\s*(?:bearer|basic)\s+)[^\s,;]+',r'\1[REDACTED]',line)
 line=re.sub(r'(?i)((?:password|passwd|token|secret)\s*[=:]\s*)[^\s,;]+',r'\1[REDACTED]',line)
 return line
def plugin_loglevel(base,folder):
 try:
  db=json.load(open(os.path.join(base,'data','system','plugindatabase.json'),encoding='utf-8'))
  for p in db.get('plugins',[]):
   if str(p.get('folder','')).lower()==folder.lower() or str(p.get('name','')).lower()=='firetv':return int(p.get('loglevel',6))
 except Exception:pass
 return 6
BASE=root();FOLDER=folder();CFG=os.path.join(BASE,'config','plugins',FOLDER,'config.json');LOGDIR=os.path.join(BASE,'log','plugins',FOLDER);LOG=os.path.join(LOGDIR,'firetv.log')
try:c=json.load(open(CFG,encoding='utf-8'))
except Exception:c={}
f=post_data();msg='';err='';diag=None
if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
 try:
  if not same_site() or not hmac.compare_digest(f.get('csrf',''),csrf(c)):raise ValueError('Sicherheitsprüfung fehlgeschlagen.')
  if f.get('action')=='clear':
   os.makedirs(LOGDIR,exist_ok=True);open(LOG,'w',encoding='utf-8').close();os.chmod(LOG,0o600);msg='Fire-TV-Log wurde geleert.'
  elif f.get('action')=='diag':
   ident=str(f.get('device','')).strip()
   if not ident or len(ident)>128:raise ValueError('Kein Gerät gewählt.')
   BIN=os.path.join(BASE,'bin','plugins',FOLDER)
   p=subprocess.run([os.path.join(BIN,'firetv.py'),'--config',CFG,'--device',ident,'--action','powerdump'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=25)
   try:diag=json.loads((p.stdout or '').strip().splitlines()[-1])
   except Exception:diag={'ok':False,'error':(p.stdout or 'keine Ausgabe').strip()[:2000]}
   diag['_device']=ident;msg='Diagnose ausgeführt.'
  else:raise ValueError('Unbekannte Aktion.')
 except Exception as e:err=str(e)
ll=plugin_loglevel(BASE,FOLDER);llname={0:'Aus/Kritisch',1:'Alert',2:'Critical',3:'Error',4:'Warning',5:'Notice',6:'Info',7:'Debug'}.get(ll,str(ll))
def cmdinfo(cmd):
 try:return (subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=5).stdout or '').strip()
 except Exception as e:return str(e)
adb=cmdinfo(['adb','version']);py=cmdinfo(['python3','--version']);lines=[]
try:lines=open(LOG,encoding='utf-8',errors='replace').read().splitlines()[-300:]
except Exception as e:lines=['Log konnte nicht gelesen werden: '+str(e)]
_extra=broker_secrets(BASE)
logtext='\n'.join(redact(x,c,_extra) for x in lines)
print("Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'self'\r\nX-Frame-Options: SAMEORIGIN\r\n\r\n",end='')
CSS='''<style>:root{--g:#73b72b;--gs:#eaf5df;--t:#29323a;--m:#71808d;--l:#dde4e8;--bg:#f6f8f9}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--t);font-family:Arial,Helvetica,sans-serif}.root{max-width:1480px;margin:auto;padding:12px}.head{display:flex;align-items:center;gap:14px;background:#fff;border:1px solid var(--l);border-radius:9px;padding:13px 16px;margin-bottom:12px}.logo{width:58px;height:58px;border-radius:8px;background:linear-gradient(145deg,#86ca42,#5ba21d);display:grid;place-items:center;color:#fff;font-size:29px}.title{flex:1}.title h1{margin:0;color:#257c31;font-size:24px}.title p{margin:4px 0 0;color:#56616b}.ver{font-size:12px;color:#687680}.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:12px}.nav{background:#fff;border:1px solid var(--l);border-radius:9px;padding:8px;height:max-content;position:sticky;top:8px}.nav small{display:block;color:#8a959e;padding:8px 12px 4px;font-size:10px;text-transform:uppercase}.nav a{display:block;padding:11px 12px;border-radius:6px;color:#34404a;font-weight:600;text-decoration:none}.nav a:hover{background:#f5f8f3}.nav a.active{background:var(--gs);color:#2d7d29}.sep{height:1px;background:#edf0f2;margin:7px 4px}.card{background:#fff;border:1px solid var(--l);border-radius:9px;margin-bottom:12px}.card h2{font-size:17px;margin:0;padding:13px 15px;border-bottom:1px solid #edf0f2}.body{padding:15px}.grid{display:grid;grid-template-columns:repeat(4,minmax(130px,1fr));gap:9px}.metric{background:#fafbfb;border:1px solid #e4e9ec;border-radius:7px;padding:11px}.metric small{display:block;color:var(--m);margin-bottom:4px}.log{background:#171b1f;color:#dfe7ed;border-radius:7px;padding:12px;min-height:320px;max-height:620px;overflow:auto;white-space:pre-wrap;font:12px Consolas,monospace}.btn{border:1px solid #cdd6dc;background:#fff;border-radius:6px;padding:9px 12px;cursor:pointer;font-weight:600}.red{border-color:#efb8b8;color:#b92e2e}.notice{padding:10px 12px;border-radius:6px;margin-bottom:12px;background:#edf8e8;border:1px solid #cbe5bd;color:#34751f}.err{background:#fff0f0;border-color:#efc0c0;color:#a52828}.muted{color:var(--m);font-size:12px}.footer{text-align:center;color:#66727b;padding:16px;font-size:13px}.mobile{display:none}@media(max-width:850px){.layout{grid-template-columns:1fr}.nav{display:none}.mobile{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}.mobile a{background:#fff;border:1px solid var(--l);padding:8px;border-radius:6px;text-decoration:none;color:#34404a}.mobile a.active{background:var(--g);border-color:var(--g);color:#fff;font-weight:700}.grid{grid-template-columns:repeat(2,1fr)}}</style>'''
V=html.escape(version());print(f'<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Debug</title>{CSS}</head><body><div class="root"><div class="head"><div class="logo">▤</div><div class="title"><h1>Debug & Log</h1><p>Diagnoseinformationen und Fire-TV-Protokoll</p></div><div class="ver">Version {V}</div></div><div class="mobile"><a href="dashboard.cgi">⌂ Übersicht</a><a href="config.cgi">⚙ Einstellungen</a><a href="discover.cgi">⌕ Suche</a><a href="security.cgi">🔒 Sicherheit</a><a href="loxone.cgi">⇄ Loxone</a><a class="active" href="debug.cgi">▤ Debug</a></div><div class="layout"><nav class="nav"><small>Fire TV Control</small><a href="dashboard.cgi">⌂ Übersicht</a><a href="discover.cgi">⌕ Fire TVs suchen</a><div class="sep"></div><a href="config.cgi">⚙ Einstellungen</a><a href="security.cgi">🔒 Security Center</a><a href="loxone.cgi">⇄ Loxone</a><a class="active" href="debug.cgi">▤ Debug-Log</a></nav><main>')
if msg:print('<div class="notice">%s</div>'%html.escape(msg))
if err:print('<div class="notice err">%s</div>'%html.escape(err))
print('<section class="card"><h2>Systemstatus</h2><div class="body"><div class="grid"><div class="metric"><small>LoxBerry Loglevel</small><b>%s (%s)</b></div><div class="metric"><small>MQTT</small><b>%s</b></div><div class="metric"><small>Watchdog</small><b>%s</b></div><div class="metric"><small>Pluginordner</small><b>%s</b></div></div><p class="muted">Den Loglevel stellst du zentral in der LoxBerry-Pluginverwaltung ein.</p></div></section>'%(html.escape(llname),ll,'Aktiv' if c.get('mqtt',{}).get('enabled',True) else 'Aus','Aktiv' if c.get('watchdog',{}).get('enabled',True) else 'Aus',html.escape(FOLDER)))
print('<section class="card"><h2>Laufzeit</h2><div class="body"><b>ADB:</b> %s<br><br><b>Python:</b> %s</div></section>'%(html.escape(adb),html.escape(py)))
devs=[d for d in c.get('devices',[]) if d.get('enabled',True)]
print('<section class="card"><h2>Bildschirm-Diagnose</h2><div class="body">')
print('<p>Zeigt die Rohwerte aus <code>dumpsys power</code>. Einmal bei laufendem Bild ausführen und einmal bei ausgeschaltetem Fernseher – die Zeile, die sich unterscheidet, ist die brauchbare.</p>')
if not devs:print('<p>Es ist kein Gerät eingerichtet.</p>')
else:
 print('<form method="post"><input type="hidden" name="csrf" value="%s"><input type="hidden" name="action" value="diag"><select name="device" style="height:38px;border:1px solid #cbd4da;border-radius:6px;padding:0 8px;max-width:100%%">'%html.escape(csrf(c),quote=True))
 for d in devs:
  ident=str(d.get('id') or d.get('name') or d.get('ip'))
  print('<option value="%s">%s</option>'%(html.escape(ident,quote=True),html.escape(str(d.get('name','Fire TV')))))
 print('</select> <button class="btn">Jetzt abfragen</button></form>')
if diag is not None:
 print('<p style="margin-top:12px"><b>Gerät:</b> %s'%html.escape(str(diag.get('_device',''))))
 if diag.get('ok'):
  print(' &nbsp; <b>eingestelltes Verfahren:</b> %s &rarr; %s</p>'%(html.escape(str(diag.get('method','auto'))),'Bildschirm an' if diag.get('awake') else 'Bildschirm aus'))
  print('<table style="width:100%;border-collapse:collapse;margin-bottom:12px"><tr><th style="text-align:left;padding:6px;border-bottom:1px solid #eef1f3;font-size:11px;text-transform:uppercase;color:#87949e">Verfahren</th><th style="text-align:left;padding:6px;border-bottom:1px solid #eef1f3;font-size:11px;text-transform:uppercase;color:#87949e">Ergebnis</th></tr>')
  for mm in diag.get('methods') or []:
   mark=' style="font-weight:bold"' if mm.get('id')==diag.get('method') else ''
   print('<tr%s><td style="padding:6px;border-bottom:1px solid #f3f5f6">%s</td><td style="padding:6px;border-bottom:1px solid #f3f5f6">%s</td></tr>'%(mark,html.escape(str(mm.get('label',''))),'Bildschirm an' if mm.get('awake') else 'Bildschirm aus'))
  print('</table>')
  print('<p style="color:#71808d;font-size:13px">Führe die Diagnose einmal bei laufendem Bild und einmal bei ausgeschaltetem Fernseher aus. Das Verfahren, dessen Ergebnis sich zwischen beiden Läufen unterscheidet, ist das richtige – in den Einstellungen auswählen.</p>')
  print('<div class="log">%s</div>'%html.escape('\n'.join(diag.get('lines') or ['(keine passenden Zeilen gefunden)'])))
 else:
  print('</p><div class="log">%s</div>'%html.escape(str(diag.get('error') or 'unbekannter Fehler')))
print('</div></section>')
print('<section class="card"><h2>Fire-TV-Log</h2><div class="body"><form method="post" style="margin-bottom:10px"><input type="hidden" name="csrf" value="%s"><input type="hidden" name="action" value="clear"><button class="btn red">Log leeren</button></form><div class="log">%s</div></div></section>'%(html.escape(csrf(c),quote=True),html.escape(logtext)))
print(f'</main></div><div class="footer">Fire TV Control · Marco Düthorn · 2026 · v{V}</div></div></body></html>')
