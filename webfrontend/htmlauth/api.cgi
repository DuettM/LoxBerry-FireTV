#!/usr/bin/env python3
import hashlib,hmac,json,os,re,subprocess,sys
from urllib.parse import parse_qs
import importlib.util as _il, os as _os, sys as _sys
def _load_webui():
    p = _os.path.abspath(_os.environ.get('SCRIPT_FILENAME') or __file__)
    m = _os.sep + 'webfrontend' + _os.sep
    base = p.split(m, 1)[0] if m in p else (_os.environ.get('LBHOMEDIR') or _os.environ.get('LBHOME') or '')
    parts = p.split(_os.sep)
    fld = parts[parts.index('plugins') + 1] if 'plugins' in parts else 'firetv'
    mp = _os.path.join(base, 'bin', 'plugins', fld, 'webui.py')
    s = _il.spec_from_file_location('firetv_webui', mp)
    mod = _il.module_from_spec(s); s.loader.exec_module(mod); return mod
webui = _load_webui()
csrf=webui.csrf
folder=webui.folder
request_data=webui.post_data
root=webui.root
same_site=webui.same_site

FOLDER=folder();CFG=os.path.join(root(),'config','plugins',FOLDER,'config.json');BIN=os.path.join(root(),'bin','plugins',FOLDER)

def out(o,code=200):
 print('Status: %d\r\nContent-Type: application/json; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src \'none\'; frame-ancestors \'none\'; base-uri \'none\'\r\n\r\n'%code,end='');print(json.dumps(o,ensure_ascii=False));raise SystemExit

def require_csrf(c):
 sent=os.environ.get('HTTP_X_FIRETV_CSRF','')
 if not sent or not hmac.compare_digest(sent,csrf(c)):out({'ok':False,'error':'CSRF-Prüfung fehlgeschlagen.'},403)
try:c=json.load(open(CFG,encoding='utf-8'))
except Exception as e:out({'ok':False,'error':'Konfiguration konnte nicht gelesen werden: '+str(e)},500)
def params():
 """POST-Daten für Befehle, bei GET die Query-Parameter. Schaltbefehle bleiben
 auf POST beschränkt, GET dient nur der Statusabfrage."""
 if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':return request_data()
 from urllib.parse import parse_qs
 return {k:(v[-1] if v else '') for k,v in parse_qs(os.environ.get('QUERY_STRING',''),keep_blank_values=True).items()}
f=params();dev=(f.get('device') or '').strip();action=(f.get('action') or 'status').strip().lower();value=f.get('value')
read_actions={'status','apps'}
write_actions={'home','back','up','down','left','right','ok','enter','menu','playpause','stop','next','previous','rewind','fastforward','mute','volumeup','volumedown','wakeup','standby','on','wake','off','tvon','tvoff','tv_on','tv_off','reboot','app','launch','text'}
if action not in read_actions|write_actions:out({'ok':False,'error':'Ungültiger Befehl.'},400)
if not dev:
 if action!='status':out({'ok':False,'error':'Gerät fehlt.'},400)
 out({'ok':True,'devices':c.get('devices',[])})
if len(dev)>128 or re.search(r'[\r\n\x00/]',dev):out({'ok':False,'error':'Geräte-ID ungültig.'},400)
def api_key_ok(c,f):
 """Alternative zum Browser-CSRF-Token: fester API-Key für Loxone/Skripte.
 Der CSRF-Token hängt am Session-Cookie und ist von einem Miniserver nicht erzeugbar."""
 k=str(c.get('web_api_key','') or '');sent=os.environ.get('HTTP_X_FIRETV_KEY','') or str(f.get('apikey','') or '')
 return bool(k) and bool(sent) and hmac.compare_digest(k,sent)
if action in write_actions:
 if os.environ.get('REQUEST_METHOD','GET').upper()!='POST':out({'ok':False,'error':'Schaltbefehle sind nur per POST erlaubt.'},405)
 if not api_key_ok(c,f):
  same_site()
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
