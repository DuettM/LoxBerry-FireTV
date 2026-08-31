#!/usr/bin/env python3
import hashlib,hmac,html,ipaddress,json,os,re,socket,subprocess,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import parse_qs

def root():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);marker=os.sep+'webfrontend'+os.sep
 if marker in p:return p.split(marker,1)[0]
 r=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME')
 if r:return r
 raise RuntimeError('LoxBerry Basisverzeichnis konnte nicht ermittelt werden')
def folder():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);parts=p.split(os.sep);return parts[parts.index('plugins')+1] if 'plugins' in parts else 'firetv'
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
def version():
 try:
  base=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__).split(os.sep+'webfrontend'+os.sep,1)[0]
  with open(os.path.join(base,'plugin.cfg'),encoding='utf-8') as f:
   for line in f:
    if line.startswith('VERSION='):return line.split('=',1)[1].strip()
 except Exception:pass
 return '0.3.1'
def local_net():
 try:
  out=subprocess.check_output(['ip','-o','-4','addr','show','scope','global'],text=True,timeout=3)
  for line in out.splitlines():
   parts=line.split()
   if 'inet' in parts:
    cidr=parts[parts.index('inet')+1];net=ipaddress.ip_network(cidr,strict=False)
    if not net.is_loopback:
     if net.prefixlen<24:net=ipaddress.ip_network(str(next(net.hosts()))+'/24',strict=False)
     return net
 except Exception:pass
 return None
def open5555(ip):
 try:
  with socket.create_connection((str(ip),5555),timeout=.18):return str(ip)
 except OSError:return None
def adb_info(ip):
 serial=f'{ip}:5555';state='erreichbar';model='Fire TV';authorized=False
 try:
  subprocess.run(['adb','connect',serial],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=4)
  p=subprocess.run(['adb','-s',serial,'shell','getprop','ro.product.model'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=4)
  txt=(p.stdout or '').strip()
  if txt and 'unauthorized' not in txt.lower() and 'error' not in txt.lower():model=txt;authorized=True;state='ADB autorisiert'
  else:state='Autorisierung am Fire TV bestätigen'
 except Exception:pass
 return {'ip':ip,'port':5555,'model':model,'authorized':authorized,'state':state}
FOLDER=folder();CFG=os.path.join(root(),'config','plugins',FOLDER,'config.json')
c=json.load(open(CFG,encoding='utf-8'));f=post_data();scan=False;err='';results=[];net=local_net();known={str(d.get('ip','')) for d in c.get('devices',[])}
if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
 if not same_site() or not f.get('csrf') or not hmac.compare_digest(f.get('csrf',''),csrf(c)):err='Sicherheitsprüfung fehlgeschlagen.'
 elif f.get('action')=='scan':scan=True
 else:err='Unbekannte Aktion.'
if scan and net:
 hosts=list(net.hosts())[:254];found=[]
 with ThreadPoolExecutor(max_workers=64) as ex:
  futs=[ex.submit(open5555,h) for h in hosts]
  for fut in as_completed(futs):
   ip=fut.result()
   if ip:found.append(ip)
 for ip in sorted(found,key=lambda x:tuple(int(p) for p in x.split('.'))):results.append(adb_info(ip))
print("Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'\r\nX-Frame-Options: DENY\r\nPermissions-Policy: camera=(), microphone=(), geolocation=()\r\n\r\n",end='')
print('''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Suche</title><style>:root{--green:#73b72b;--text:#29323a;--muted:#71808d;--line:#dde4e8;--bg:#f6f8f9;--red:#d94343;--orange:#ee9c24}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Arial,Helvetica,sans-serif}.root{max-width:1180px;margin:auto;padding:12px}.head{display:flex;align-items:center;gap:14px;background:#fff;border:1px solid var(--line);border-radius:9px;padding:13px 16px;margin-bottom:12px}.logo{width:54px;height:54px;border-radius:8px;background:linear-gradient(145deg,#86ca42,#5ba21d);display:grid;place-items:center;color:#fff;font-size:28px}.title{flex:1}.title h1{margin:0;color:#257c31;font-size:23px}.title p{margin:3px 0 0;color:#56616b}.ver{font-size:12px;color:#687680}.nav{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px}.nav a{background:#fff;border:1px solid var(--line);border-radius:6px;padding:9px 11px;text-decoration:none;color:#34404a;font-weight:600}.nav a.active{background:#edf7e5;color:#2d7d29;border-color:#cbe1c1}.card{background:#fff;border:1px solid var(--line);border-radius:9px;margin-bottom:12px}.card h2{font-size:17px;margin:0;padding:13px 15px;border-bottom:1px solid #edf0f2}.body{padding:15px}.network{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center}.btn{border:1px solid #cdd6dc;background:#fff;border-radius:6px;padding:9px 12px;cursor:pointer;font-weight:600}.btn-green{background:var(--green);border-color:var(--green);color:#fff}.result{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center;padding:12px 0;border-bottom:1px solid #edf0f2}.result:last-child{border-bottom:0}.result h3{margin:0 0 4px}.status{display:inline-block;padding:3px 8px;border-radius:5px;font-size:12px;font-weight:bold}.ok{background:#eff8eb;border:1px solid #cbe1c1;color:#23802a}.warn{background:#fff7e8;border:1px solid #f0d39c;color:#a66b0c}.bad{background:#fff0f0;border:1px solid #efc0c0;color:#a52828}.muted{color:var(--muted);font-size:12px}.add{display:flex;gap:7px;align-items:center;flex-wrap:wrap}.add input{height:38px;border:1px solid #cbd4da;border-radius:6px;padding:0 10px}.notice{padding:10px 12px;border-radius:6px;margin-bottom:12px}.footer{text-align:center;color:#66727b;padding:16px;font-size:13px}@media(max-width:650px){.head{flex-wrap:wrap}.network,.result{grid-template-columns:1fr}.ver{margin-left:68px}}</style></head><body><div class="root"><div class="head"><div class="logo">⌕</div><div class="title"><h1>Fire TVs suchen</h1><p>ADB-Geräte im lokalen Netzwerk automatisch finden</p></div><div class="ver">Version __VER__</div></div><div class="nav"><a href="index.cgi">⌂ Übersicht</a><a href="config.cgi">⚙ Einstellungen</a><a class="active" href="discover.cgi">⌕ Fire TVs suchen</a><a href="security.cgi">🔒 Security Center</a><a href="debug.cgi">▤ Debug</a></div>'''.replace('__VER__',html.escape(version())))
if err:print('<div class="notice bad">%s</div>'%html.escape(err))
if not net:print('<section class="card"><div class="body"><b>Lokales IPv4-Netz konnte nicht automatisch ermittelt werden.</b></div></section>')
else:
 print('<section class="card"><h2>Netzwerksuche</h2><div class="body"><div class="network"><div><b>Erkanntes Netz: %s</b><br><span class="muted">Es wird ausschließlich nach ADB auf TCP-Port 5555 gesucht. Maximal 254 Hosts.</span></div><form method="post"><input type="hidden" name="csrf" value="%s"><input type="hidden" name="action" value="scan"><button class="btn btn-green">⌕ Suche starten</button></form></div></div></section>'%(html.escape(str(net)),html.escape(csrf(c),quote=True)))
if scan and net and not results:print('<section class="card"><div class="body"><b>Kein Fire TV gefunden.</b><p class="muted">Prüfe ADB-Debugging und ob Port 5555 vom LoxBerry erreichbar ist.</p></div></section>')
if results:
 print('<section class="card"><h2>Gefundene Geräte</h2><div class="body">')
 for r in results:
  already=r['ip'] in known;cls='ok' if r['authorized'] else 'warn'
  print('<div class="result"><div><h3>%s</h3><b>%s:5555</b><br><span class="status %s">%s</span></div>'%(html.escape(r['model']),html.escape(r['ip']),cls,html.escape(r['state'])))
  if already:print('<span class="status ok">Bereits hinzugefügt</span></div>')
  else:
   name=html.escape(r['model'],quote=True);ip=html.escape(r['ip'],quote=True);tok=html.escape(csrf(c),quote=True)
   print('<form class="add" method="post" action="config.cgi"><input type="hidden" name="csrf" value="%s"><input type="hidden" name="form_action" value="add_device"><input type="hidden" name="ip" value="%s"><input type="hidden" name="port" value="5555"><input name="name" maxlength="80" value="%s"><button class="btn btn-green">Hinzufügen</button></form></div>'%(tok,ip,name))
 print('</div></section>')
print('<div class="footer">Fire TV Control · Marco Düthorn · 2026 · v%s</div></div></body></html>'%html.escape(version()))
