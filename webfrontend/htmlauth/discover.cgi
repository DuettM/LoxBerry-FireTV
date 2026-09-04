#!/usr/bin/env python3
import hashlib,hmac,html,ipaddress,json,os,re,socket,subprocess,sys,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import parse_qs

def root():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);m=os.sep+'webfrontend'+os.sep
 if m in p:return p.split(m,1)[0]
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
  for line in open(os.path.join(base,'plugin.cfg'),encoding='utf-8'):
   if line.startswith('VERSION='):return line.split('=',1)[1].strip()
 except Exception:pass
 return '0.3.8'
def local_net():
 try:
  out=subprocess.check_output(['ip','-o','-4','addr','show','scope','global'],text=True,timeout=3)
  for line in out.splitlines():
   parts=line.split();cidr=parts[parts.index('inet')+1] if 'inet' in parts else ''
   if not cidr:continue
   iface=ipaddress.ip_interface(cidr);net=iface.network
   if net.is_loopback:continue
   if net.prefixlen<24:net=ipaddress.ip_network(f'{iface.ip}/24',strict=False)
   return net
 except Exception:pass
 return None
def open5555(ip):
 try:
  with socket.create_connection((str(ip),5555),timeout=.18):return str(ip)
 except OSError:return None
def adb_state(serial):
 try:
  p=subprocess.run(['adb','devices'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=4);txt=p.stdout or ''
  for line in txt.splitlines():
   if line.startswith(serial+'\t'):return line.split('\t',1)[1].strip().lower()
 except Exception:pass
 return 'disconnected'
def adb_info(ip):
 serial=f'{ip}:5555';state='disconnected';model='Fire TV';authorized=False
 try:
  subprocess.run(['adb','connect',serial],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=4);state=adb_state(serial)
  if state=='device':
   p=subprocess.run(['adb','-s',serial,'shell','getprop','ro.product.model'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=4);txt=(p.stdout or '').strip()
   if txt:model=txt
   authorized=True;label='ADB autorisiert'
  elif state=='unauthorized':label='Bestätigung am Fire TV erforderlich'
  elif state=='offline':label='ADB offline'
  else:label='ADB nicht verbunden'
 except Exception:label='ADB-Status konnte nicht geprüft werden'
 return {'ip':ip,'model':model,'authorized':authorized,'state':state,'label':label}
def reconnect(ip):
 serial=f'{ip}:5555'
 try:subprocess.run(['adb','disconnect',serial],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=4)
 except Exception:pass
 time.sleep(.35)
 try:p=subprocess.run(['adb','connect',serial],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=5);out=(p.stdout or '').strip()
 except Exception as e:return False,'ADB-Verbindung fehlgeschlagen: '+str(e)
 time.sleep(.35);state=adb_state(serial)
 if state=='device':return True,'ADB autorisiert und verbunden.'
 if state=='unauthorized':return True,'ADB-Verbindung neu angefordert. Bitte die Abfrage am Fire TV bestätigen.'
 if state=='offline':return False,'Fire TV ist per ADB offline.'
 return False,'ADB-Verbindung nicht möglich: '+out
FOLDER=folder();CFG=os.path.join(root(),'config','plugins',FOLDER,'config.json');c=json.load(open(CFG,encoding='utf-8'));f=post_data();scan=False;err='';notice='';results=[];net=local_net();known={str(d.get('ip','')) for d in c.get('devices',[])}
if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
 if not same_site() or not f.get('csrf') or not hmac.compare_digest(f.get('csrf',''),csrf(c)):err='Sicherheitsprüfung fehlgeschlagen.'
 elif f.get('action')=='scan':scan=True
 elif f.get('action')=='reconnect':
  ip=(f.get('ip') or '').strip()
  try:ipaddress.ip_address(ip)
  except ValueError:err='Ungültige IP-Adresse.'
  else:
   ok,msg=reconnect(ip);notice=msg if ok else '';err='' if ok else msg;scan=True
 else:err='Unbekannte Aktion.'
if scan and net:
 hosts=list(net.hosts())[:254];found=[]
 with ThreadPoolExecutor(max_workers=64) as ex:
  for fut in as_completed([ex.submit(open5555,h) for h in hosts]):
   ip=fut.result()
   if ip:found.append(ip)
 for ip in sorted(found,key=lambda x:tuple(int(p) for p in x.split('.'))):results.append(adb_info(ip))
print("Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'self'\r\nX-Frame-Options: SAMEORIGIN\r\n\r\n",end='')
CSS='''<style>:root{--g:#73b72b;--gs:#eaf5df;--t:#29323a;--m:#71808d;--l:#dde4e8;--bg:#f6f8f9}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--t);font-family:Arial,Helvetica,sans-serif}.root{max-width:1480px;margin:auto;padding:12px}.head{display:flex;align-items:center;gap:14px;background:#fff;border:1px solid var(--l);border-radius:9px;padding:13px 16px;margin-bottom:12px}.logo{width:58px;height:58px;border-radius:8px;background:linear-gradient(145deg,#86ca42,#5ba21d);display:grid;place-items:center;color:#fff;font-size:29px}.title{flex:1}.title h1{margin:0;color:#257c31;font-size:24px}.title p{margin:4px 0 0;color:#56616b}.ver{font-size:12px;color:#687680}.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:12px}.nav{background:#fff;border:1px solid var(--l);border-radius:9px;padding:8px;height:max-content;position:sticky;top:8px}.nav small{display:block;color:#8a959e;padding:8px 12px 4px;font-size:10px;text-transform:uppercase}.nav a{display:block;padding:11px 12px;border-radius:6px;color:#34404a;font-weight:600;text-decoration:none}.nav a:hover{background:#f5f8f3}.nav a.active{background:var(--gs);color:#2d7d29}.sep{height:1px;background:#edf0f2;margin:7px 4px}.card{background:#fff;border:1px solid var(--l);border-radius:9px;margin-bottom:12px}.card h2{font-size:17px;margin:0;padding:13px 15px;border-bottom:1px solid #edf0f2}.body{padding:15px}.row{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center}.btn{border:1px solid #cdd6dc;background:#fff;border-radius:6px;padding:9px 12px;cursor:pointer;font-weight:600}.green{background:var(--g);border-color:var(--g);color:#fff}.orange{border-color:#e7ca99;color:#a56b0b;background:#fffaf1}.muted{color:var(--m);font-size:12px}.status{display:inline-block;padding:3px 8px;border-radius:5px;font-size:12px;font-weight:bold}.ok{background:#eff8eb;border:1px solid #cbe1c1;color:#23802a}.warn{background:#fff7e8;border:1px solid #f0d39c;color:#a66b0c}.bad{background:#fff0f0;border:1px solid #efc0c0;color:#a52828}.notice{padding:10px 12px;border-radius:6px;margin-bottom:12px}.add{display:flex;gap:7px;align-items:center;flex-wrap:wrap}.add input{height:38px;border:1px solid #cbd4da;border-radius:6px;padding:0 10px}.result{padding:12px 0;border-bottom:1px solid #edf0f2}.actions{display:flex;gap:7px;align-items:center;flex-wrap:wrap}.footer{text-align:center;color:#66727b;padding:16px;font-size:13px}.mobile{display:none}@media(max-width:850px){.layout{grid-template-columns:1fr}.nav{display:none}.mobile{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}.mobile a{background:#fff;border:1px solid var(--l);padding:8px;border-radius:6px;text-decoration:none;color:#34404a}.row{grid-template-columns:1fr}}</style>'''
V=html.escape(version());print(f'<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Suche</title>{CSS}</head><body><div class="root"><div class="head"><div class="logo">⌕</div><div class="title"><h1>Fire TVs suchen</h1><p>ADB-Geräte im lokalen Netzwerk automatisch finden und autorisieren</p></div><div class="ver">Version {V}</div></div><div class="mobile"><a href="dashboard.cgi">⌂ Übersicht</a><a href="config.cgi">⚙ Einstellungen</a><a href="security.cgi">🔒 Sicherheit</a><a href="debug.cgi">▤ Debug</a></div><div class="layout"><nav class="nav"><small>Fire TV Control</small><a href="dashboard.cgi">⌂ Übersicht</a><a class="active" href="discover.cgi">⌕ Fire TVs suchen</a><div class="sep"></div><a href="config.cgi">⚙ Einstellungen</a><a href="security.cgi">🔒 Security Center</a><a href="debug.cgi">▤ Debug-Log</a></nav><main>')
if notice:print('<div class="notice ok">%s</div>'%html.escape(notice))
if err:print('<div class="notice bad">%s</div>'%html.escape(err))
if not net:print('<section class="card"><div class="body">Lokales IPv4-Netz konnte nicht ermittelt werden.</div></section>')
else:print('<section class="card"><h2>Netzwerksuche</h2><div class="body"><div class="row"><div><b>Erkanntes Netz: %s</b><br><span class="muted">Scan auf TCP 5555, maximal 254 Hosts.</span></div><form method="post"><input type="hidden" name="csrf" value="%s"><input type="hidden" name="action" value="scan"><button class="btn green">⌕ Suche starten</button></form></div></div></section>'%(html.escape(str(net)),html.escape(csrf(c),quote=True)))
if scan and net and not results:print('<section class="card"><div class="body">Kein Fire TV mit offenem ADB-Port 5555 gefunden.</div></section>')
if results:
 print('<section class="card"><h2>Gefundene Geräte</h2><div class="body">')
 for r in results:
  already=r['ip'] in known;cls='ok' if r['authorized'] else ('warn' if r['state']=='unauthorized' else 'bad');print('<div class="result"><div class="row"><div><b>%s</b><br>%s:5555<br><span class="status %s">%s</span></div><div class="actions">'%(html.escape(r['model']),html.escape(r['ip']),cls,html.escape(r['label'])))
  if not r['authorized']:
   print('<form method="post"><input type="hidden" name="csrf" value="%s"><input type="hidden" name="action" value="reconnect"><input type="hidden" name="ip" value="%s"><button class="btn orange">↻ ADB neu verbinden</button></form>'%(html.escape(csrf(c),quote=True),html.escape(r['ip'],quote=True)))
  if already:print('<span class="status ok">Bereits hinzugefügt</span>')
  else:print('<form class="add" method="post" action="config.cgi"><input type="hidden" name="csrf" value="%s"><input type="hidden" name="form_action" value="add_device"><input type="hidden" name="ip" value="%s"><input type="hidden" name="port" value="5555"><input name="name" maxlength="80" value="%s"><button class="btn green">Hinzufügen</button></form>'%(html.escape(csrf(c),quote=True),html.escape(r['ip'],quote=True),html.escape(r['model'],quote=True)))
  print('</div></div></div>')
 print('</div></section>')
print(f'</main></div><div class="footer">Fire TV Control · Marco Düthorn · 2026 · v{V}</div></div></body></html>')
