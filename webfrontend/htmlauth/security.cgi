#!/usr/bin/env python3
import hashlib,hmac,html,ipaddress,json,os,re,secrets,stat,tempfile,sys
from urllib.parse import parse_qs
SAFE_ACTIONS=['tvon','tvoff','home','back','up','down','left','right','ok','menu','playpause','volumeup','volumedown','mute','app']
def root():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);m=os.sep+'webfrontend'+os.sep
 if m in p:return p.split(m,1)[0]
 r=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME')
 if r:return r
 raise RuntimeError('LoxBerry Basisverzeichnis konnte nicht ermittelt werden')
def folder():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);parts=p.split(os.sep);return parts[parts.index('plugins')+1] if 'plugins' in parts else 'firetv'
def form():
 data={}
 if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
  try:n=min(max(int(os.environ.get('CONTENT_LENGTH','0') or 0),0),65536)
  except ValueError:n=0
  raw=sys.stdin.buffer.read(n) if n else b''
  for k,v in parse_qs(raw.decode('utf-8','replace'),keep_blank_values=True).items():data[k]=v[-1] if v else ''
 return data
FOLDER=folder();CFG=os.path.join(root(),'config','plugins',FOLDER,'config.json')
def load():return json.load(open(CFG,encoding='utf-8'))
def save(c):
 fd,tmp=tempfile.mkstemp(prefix='.config-',dir=os.path.dirname(CFG),text=True)
 with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(c,f,ensure_ascii=False,indent=2);f.write('\n')
 os.chmod(tmp,0o600);os.replace(tmp,CFG)
def version():
 try:
  base=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__).split(os.sep+'webfrontend'+os.sep,1)[0]
  for line in open(os.path.join(base,'plugin.cfg'),encoding='utf-8'):
   if line.startswith('VERSION='):return line.split('=',1)[1].strip()
 except Exception:pass
 return '0.3.12'
def token(c):return hmac.new(str(c.get('web_secret','')).encode(),(os.environ.get('HTTP_COOKIE','')+'|'+os.environ.get('HTTP_USER_AGENT','')).encode(),hashlib.sha256).hexdigest()
def same_site():
 if os.environ.get('HTTP_SEC_FETCH_SITE','').lower()=='cross-site':return False
 host=os.environ.get('HTTP_HOST','').lower()
 for k in ('HTTP_ORIGIN','HTTP_REFERER'):
  v=os.environ.get(k,'').lower();m=re.match(r'^https?://([^/]+)',v) if v and host else None
  if m and m.group(1)!=host:return False
 return True
def private_ip(v):
 try:
  a=ipaddress.ip_address(str(v));return a.is_private or a.is_loopback or a.is_link_local
 except Exception:return False
c=load();f=form();msg='';err=''
if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
 try:
  if not same_site() or not hmac.compare_digest(f.get('csrf',''),token(c)):raise ValueError('Sicherheitsprüfung fehlgeschlagen.')
  m=c.setdefault('mqtt',{});m['allow_reboot']=bool(f.get('allow_reboot'));m['allow_text']=bool(f.get('allow_text'));m['allowed_actions']=[a for a in SAFE_ACTIONS if f.get('allow_'+a)];m['command_token_required']=bool(f.get('command_token_required'))
  if f.get('rotate_token') or not m.get('command_token'):m['command_token']=secrets.token_urlsafe(32)
  s=c.setdefault('security',{});s['discovery_post_only']=True;s['private_adb_only']=bool(f.get('private_adb_only'))
  save(c);msg='Sicherheitseinstellungen gespeichert.'
 except Exception as e:err=str(e)
m=c.get('mqtt',{});s=c.get('security',{});allowed=set(m.get('allowed_actions',SAFE_ACTIONS));listen=bool(m.get('listen_enabled',True));danger=bool(m.get('allow_reboot')) or bool(m.get('allow_text'));tokreq=bool(m.get('command_token_required'));privateonly=bool(s.get('private_adb_only',True))
try:mode=stat.S_IMODE(os.stat(CFG).st_mode);perm_ok=mode==0o600
except Exception:mode=0;perm_ok=False
bad_devices=[str(d.get('ip','')) for d in c.get('devices',[]) if d.get('ip') and not private_ip(d.get('ip'))]
checks=[('Web-Secret',bool(c.get('web_secret')),'gesetzt','fehlt'),('Config-Rechte',perm_ok,'0600','%04o'%mode),('Private ADB-Ziele',privateonly and not bad_devices,'aktiv','prüfen'),('MQTT Token',tokreq,'aktiv','optional'),('Riskante Befehle',not danger,'gesperrt','freigegeben')]
score=100
if listen and not tokreq:score-=15
if danger:score-=25
if not c.get('web_secret'):score-=40
if not perm_ok:score-=20
if not privateonly:score-=15
if bad_devices:score-=25
score=max(0,score);level='Sehr gut' if score>=85 else ('Gut' if score>=70 else ('Verbesserbar' if score>=50 else 'Kritisch'))
print("Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'self'\r\nX-Frame-Options: SAMEORIGIN\r\nPermissions-Policy: camera=(), microphone=(), geolocation=()\r\n\r\n",end='')
CSS='''<style>:root{--g:#73b72b;--gs:#eaf5df;--t:#29323a;--m:#71808d;--l:#dde4e8;--bg:#f6f8f9}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--t);font-family:Arial,Helvetica,sans-serif}.root{max-width:1480px;margin:auto;padding:12px}.head,.card,.nav{background:#fff;border:1px solid var(--l);border-radius:9px}.head{display:flex;align-items:center;gap:14px;padding:13px 16px;margin-bottom:12px}.logo{width:58px;height:58px;border-radius:8px;background:#73b72b;display:grid;place-items:center;color:#fff;font-size:29px}.title{flex:1}.title h1{margin:0;color:#257c31;font-size:24px}.title p{margin:4px 0 0;color:#56616b}.ver{font-size:12px;color:#687680}.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:12px}.nav{padding:8px;height:max-content}.nav a{display:block;padding:11px 12px;border-radius:6px;color:#34404a;font-weight:600;text-decoration:none}.nav a:hover{background:#f5f8f3}.nav a.active{background:var(--gs);color:#2d7d29}.mobile{display:none}.mobile a{background:#fff;border:1px solid var(--l);padding:9px 11px;border-radius:6px;text-decoration:none;color:#34404a;font-weight:600}.mobile a.active{background:var(--gs);border-color:#bddd9f;color:#2d7d29}.card{margin-bottom:12px}.card h2{font-size:17px;margin:0;padding:13px 15px;border-bottom:1px solid #edf0f2}.body{padding:15px}.score{display:flex;gap:18px;align-items:center}.num{width:86px;height:86px;border-radius:50%;display:grid;place-items:center;background:#edf8e8;border:7px solid #bddd9f;font-size:22px;font-weight:bold;color:#2d7d29}.grid{display:grid;grid-template-columns:repeat(3,minmax(160px,1fr));gap:9px;margin-top:15px}.metric{border:1px solid #e3e8eb;background:#fafbfb;border-radius:7px;padding:11px}.metric small{display:block;color:var(--m);margin-bottom:4px}.good{color:#278c2b}.warn{color:#b87410}.bad{color:#cf3838}.actions{display:grid;grid-template-columns:repeat(3,minmax(170px,1fr));gap:8px}.actions label,.box{padding:9px;border:1px solid #e2e7ea;border-radius:6px;background:#fafbfb}.danger{margin-top:14px;padding:12px;border:1px solid #efc0c0;background:#fff5f5;border-radius:7px}.btn{background:var(--g);color:#fff;border:0;border-radius:6px;padding:9px 12px;cursor:pointer;font-weight:600}.token{width:100%;padding:8px;font-family:monospace}.notice{padding:10px 12px;border-radius:6px;margin-bottom:12px}.footer{text-align:center;color:#66727b;padding:16px;font-size:13px}@media(max-width:850px){.layout{grid-template-columns:1fr}.nav{display:none}.mobile{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px}.grid,.actions{grid-template-columns:1fr}}@media(max-width:520px){.head{align-items:flex-start;flex-wrap:wrap}.ver{margin-left:72px}.mobile a{flex:1 1 calc(50% - 7px);text-align:center}}</style>'''
V=html.escape(version());print(f'<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Security</title>{CSS}</head><body><div class="root"><div class="head"><div class="logo">🔒</div><div class="title"><h1>Security Center</h1><p>Hardening, MQTT-Berechtigungen und Selbsttests</p></div><div class="ver">Version {V}</div></div><div class="mobile"><a href="dashboard.cgi">⌂ Übersicht</a><a href="discover.cgi">⌕ Suche</a><a href="config.cgi">⚙ Einstellungen</a><a class="active" href="security.cgi">🔒 Sicherheit</a><a href="debug.cgi">▤ Debug</a></div><div class="layout"><nav class="nav"><a href="dashboard.cgi">⌂ Übersicht</a><a href="discover.cgi">⌕ Fire TVs suchen</a><a href="config.cgi">⚙ Einstellungen</a><a class="active" href="security.cgi">🔒 Security Center</a><a href="debug.cgi">▤ Debug-Log</a></nav><main>')
if msg:print('<div class="notice good">%s</div>'%html.escape(msg))
if err:print('<div class="notice bad">%s</div>'%html.escape(err))
cls='good' if score>=85 else 'warn' if score>=70 else 'bad';print('<section class="card"><h2>Sicherheitsbewertung</h2><div class="body"><div class="score"><div class="num">%d</div><div><h3 class="%s">%s</h3><p>Automatische lokale Prüfungen.</p></div></div><div class="grid">'%(score,cls,level))
for name,ok,good,bad in checks:print('<div class="metric"><small>%s</small><b class="%s">%s</b></div>'%(html.escape(name),'good' if ok else 'warn',html.escape(good if ok else bad)))
print('</div></div></section>')
print('<section class="card"><h2>Hardening</h2><div class="body"><form method="post"><input type="hidden" name="csrf" value="%s">'%html.escape(token(c),quote=True))
print('<div class="box"><label><input type="checkbox" name="private_adb_only" %s> ADB nur zu privaten/lokalen IP-Adressen erlauben</label></div>'%('checked' if privateonly else ''))
print('<div class="box" style="margin-top:8px"><label><input type="checkbox" name="command_token_required" %s> MQTT-Befehle zusätzlich mit Token absichern</label><p>Bei Aktivierung müssen Befehle als JSON gesendet werden, z. B. <code>{"action":"tvon","token":"..."}</code>.</p><input class="token" type="text" readonly value="%s"><p><label><input type="checkbox" name="rotate_token"> Neuen Token erzeugen</label></p></div>'%('checked' if tokreq else '',html.escape(str(m.get('command_token','')),quote=True)))
print('<h3>MQTT-Befehls-Whitelist</h3><div class="actions">')
for a in SAFE_ACTIONS:print('<label><input type="checkbox" name="allow_%s" %s> %s</label>'%(a,'checked' if a in allowed else '',html.escape(a)))
print('</div><div class="danger"><b>Erweiterte Freigaben</b><p><label><input type="checkbox" name="allow_reboot" %s> Reboot über MQTT erlauben</label></p><p><label><input type="checkbox" name="allow_text" %s> Texteingabe über MQTT erlauben</label></p></div><p><button class="btn">Speichern</button></p></form></div></section>'%('checked' if m.get('allow_reboot') else '','checked' if m.get('allow_text') else ''))
if bad_devices:print('<section class="card"><h2>Warnung</h2><div class="body bad">Nicht-private Geräte-IP(s): %s</div></section>'%html.escape(', '.join(bad_devices)))
print(f'<section class="card"><h2>Firewall</h2><div class="body">ADB TCP 5555 nur vom LoxBerry zu den Fire TVs freigeben. MQTT-Schreibrechte auf <code>{html.escape(str(m.get("base_topic","firetv")))}/+/set</code> und <code>/command</code> möglichst per Broker-ACL begrenzen.</div></section></main></div><div class="footer">Fire TV Control · Marco Düthorn · 2026 · v{V}</div></div></body></html>')
