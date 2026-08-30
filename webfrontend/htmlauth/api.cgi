#!/usr/bin/env python3
import cgi,hashlib,hmac,json,os,re,subprocess,sys

def root():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__)
 marker=os.sep+'webfrontend'+os.sep
 if marker in p:return p.split(marker,1)[0]
 r=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME')
 if r:return r
 raise RuntimeError('LoxBerry Basisverzeichnis konnte nicht ermittelt werden')
def folder():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);parts=p.split(os.sep)
 return parts[parts.index('plugins')+1] if 'plugins' in parts and parts.index('plugins')+1 < len(parts) else 'firetv'
FOLDER=folder();CFG=os.path.join(root(),'config','plugins',FOLDER,'config.json');BIN=os.path.join(root(),'bin','plugins',FOLDER)

def out(o,code=200):
 print('Status: %d\r\nContent-Type: application/json; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\n\r\n'%code,end='');print(json.dumps(o,ensure_ascii=False));raise SystemExit

def csrf(c):
 seed=(os.environ.get('HTTP_COOKIE','')+'|'+os.environ.get('HTTP_USER_AGENT','')).encode();key=str(c.get('web_secret','')).encode();return hmac.new(key,seed,hashlib.sha256).hexdigest()
def require_csrf(c):
 sent=os.environ.get('HTTP_X_FIRETV_CSRF','')
 if not sent or not hmac.compare_digest(sent,csrf(c)):out({'ok':False,'error':'CSRF-Prüfung fehlgeschlagen.'},403)
def same_site():
 if os.environ.get('HTTP_SEC_FETCH_SITE','').lower()=='cross-site':out({'ok':False,'error':'Cross-Site-Anfrage blockiert.'},403)
 host=os.environ.get('HTTP_HOST','').lower()
 for k in ('HTTP_ORIGIN','HTTP_REFERER'):
  v=os.environ.get(k,'').lower()
  if v and host:
   m=re.match(r'^https?://([^/]+)',v)
   if m and m.group(1)!=host:out({'ok':False,'error':'Cross-Site-Anfrage blockiert.'},403)
try:c=json.load(open(CFG,encoding='utf-8'))
except Exception as e:out({'ok':False,'error':'Konfiguration konnte nicht gelesen werden: '+str(e)},500)
f=cgi.FieldStorage();dev=(f.getfirst('device') or '').strip();action=(f.getfirst('action') or 'status').strip().lower();value=f.getfirst('value')
read_actions={'status','apps'};write_actions={'home','back','up','down','left','right','ok','enter','menu','playpause','stop','next','previous','rewind','fastforward','mute','volumeup','volumedown','wakeup','standby','on','wake','reboot','app','launch','text'}
if action not in read_actions|write_actions:out({'ok':False,'error':'Ungültiger Befehl.'},400)
if not dev:
 if action!='status':out({'ok':False,'error':'Gerät fehlt.'},400)
 out({'ok':True,'devices':c.get('devices',[])})
if len(dev)>128 or re.search(r'[\r\n\x00]',dev):out({'ok':False,'error':'Geräte-ID ungültig.'},400)
if action in write_actions:
 same_site()
 if os.environ.get('REQUEST_METHOD','GET').upper()!='POST':out({'ok':False,'error':'Schaltbefehle sind nur per POST erlaubt.'},405)
 require_csrf(c)
if value is not None and (len(value)>512 or '\x00' in value):out({'ok':False,'error':'Wert ungültig.'},400)
cmd=[os.path.join(BIN,'firetv.py'),'--config',CFG,'--device',dev,'--action',action]
if value is not None:cmd+=['--value',value]
try:
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=20,check=False)
 raw=(p.stdout or '').strip().splitlines()
 if not raw:out({'ok':False,'error':'Backend lieferte keine Antwort.'},502)
 try:r=json.loads(raw[-1])
 except Exception:r={'ok':False,'error':'Backend lieferte ungültige JSON-Antwort.'}
 out(r,200 if p.returncode==0 else 502)
except subprocess.TimeoutExpired:out({'ok':False,'error':'Backend-Zeitüberschreitung.'},504)
except Exception as e:out({'ok':False,'error':str(e)},500)
