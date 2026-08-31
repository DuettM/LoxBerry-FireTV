#!/usr/bin/env python3
import hashlib,hmac,html,ipaddress,json,os,re,socket,subprocess,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import parse_qs

def root():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__)
 marker=os.sep+'webfrontend'+os.sep
 if marker in p:return p.split(marker,1)[0]
 r=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME')
 if r:return r
 raise RuntimeError('LoxBerry Basisverzeichnis konnte nicht ermittelt werden')
def folder():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);parts=p.split(os.sep)
 return parts[parts.index('plugins')+1] if 'plugins' in parts else 'firetv'
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
print('''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Suche</title><style>body{font-family:system-ui;background:#0f141a;color:#fff;margin:0}.wrap{max-width:900px;margin:auto;padding:24px}.card{background:#18212b;border:1px solid #2a3948;border-radius:16px;padding:18px;margin:12px 0}a,button{background:#ff9900;color:#111;border:0;border-radius:10px;padding:10px 14px;text-decoration:none;font-weight:700}small{color:#9fb0c0}.ok{color:#71e39b}.warn{color:#ffbd66}.bad{color:#ff8088}.row{display:flex;justify-content:space-between;gap:16px;align-items:center;flex-wrap:wrap}input{padding:9px;border-radius:8px;border:1px solid #3a4a59}</style></head><body><div class="wrap"><p><a href="config.cgi">← Konfiguration</a> <a href="security.cgi">🔒 Security Center</a></p><h1>Fire TVs suchen</h1>''')
if err:print('<div class="card bad">%s</div>'%html.escape(err))
if not net:print('<div class="card">Lokales IPv4-Netz konnte nicht automatisch ermittelt werden.</div>')
else:
 print('<div class="card"><b>Netz:</b> %s<br><small>Gesucht wird nach ADB auf TCP-Port 5555. Der Scan ist auf maximal 254 Adressen begrenzt.</small><form method="post"><input type="hidden" name="csrf" value="%s"><input type="hidden" name="action" value="scan"><p><button>🔎 Suche starten</button></p></form></div>'%(html.escape(str(net)),html.escape(csrf(c),quote=True)))
if scan and net and not results:print('<div class="card">Kein Gerät mit offenem ADB-Port 5555 gefunden. Prüfe, ob ADB-Debugging am Fire TV aktiviert ist.</div>')
for r in results:
 already=r['ip'] in known;cls='ok' if r['authorized'] else 'warn'
 print('<div class="card"><div class="row"><div><h2>%s</h2><b>%s:5555</b><br><span class="%s">%s</span></div>'%(html.escape(r['model']),html.escape(r['ip']),cls,html.escape(r['state'])))
 if already:print('<b class="ok">Bereits hinzugefügt</b></div></div>')
 else:
  name=html.escape(r['model'],quote=True);ip=html.escape(r['ip'],quote=True);token=html.escape(csrf(c),quote=True)
  print('<form method="post" action="config.cgi"><input type="hidden" name="csrf" value="%s"><input type="hidden" name="form_action" value="add_device"><input type="hidden" name="ip" value="%s"><input type="hidden" name="port" value="5555"><div class="row"><input name="name" maxlength="80" value="%s"><button>Hinzufügen</button></div></form></div>'%(token,ip,name))
print('<footer><small>Fire TV Control · Marco Düthorn · 2026 · v0.3.0</small></footer></div></body></html>')
