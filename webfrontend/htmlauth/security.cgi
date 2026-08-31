#!/usr/bin/env python3
import hashlib,hmac,html,json,os,re,tempfile,sys
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
 return '0.3.3'
def token(c):return hmac.new(str(c.get('web_secret','')).encode(),(os.environ.get('HTTP_COOKIE','')+'|'+os.environ.get('HTTP_USER_AGENT','')).encode(),hashlib.sha256).hexdigest()
def same_site():
 if os.environ.get('HTTP_SEC_FETCH_SITE','').lower()=='cross-site':return False
 host=os.environ.get('HTTP_HOST','').lower()
 for k in ('HTTP_ORIGIN','HTTP_REFERER'):
  v=os.environ.get(k,'').lower();m=re.match(r'^https?://([^/]+)',v) if v and host else None
  if m and m.group(1)!=host:return False
 return True
c=load();f=form();msg='';err=''
if os.environ.get('REQUEST_METHOD','GET').upper()=='POST':
 try:
  if not same_site() or not hmac.compare_digest(f.get('csrf',''),token(c)):raise ValueError('Sicherheitsprüfung fehlgeschlagen.')
  m=c.setdefault('mqtt',{});m['allow_reboot']=bool(f.get('allow_reboot'));m['allow_text']=bool(f.get('allow_text'));m['allowed_actions']=[a for a in SAFE_ACTIONS if f.get('allow_'+a)];c.setdefault('security',{})['discovery_post_only']=True;save(c);msg='Sicherheitseinstellungen gespeichert.'
 except Exception as e:err=str(e)
m=c.get('mqtt',{});allowed=set(m.get('allowed_actions',SAFE_ACTIONS));listen=bool(m.get('listen_enabled',True));danger=bool(m.get('allow_reboot')) or bool(m.get('allow_text'));score=100-(15 if listen else 0)-(25 if danger else 0)-(40 if not c.get('web_secret') else 0);level='Sehr gut' if score>=85 else ('Gut' if score>=70 else ('Verbesserbar' if score>=50 else 'Kritisch'))
print("Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'\r\nX-Frame-Options: DENY\r\n\r\n",end='')
CSS='''<style>:root{--g:#73b72b;--gs:#eaf5df;--t:#29323a;--m:#71808d;--l:#dde4e8;--bg:#f6f8f9}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--t);font-family:Arial,Helvetica,sans-serif}.root{max-width:1480px;margin:auto;padding:12px}.head{display:flex;align-items:center;gap:14px;background:#fff;border:1px solid var(--l);border-radius:9px;padding:13px 16px;margin-bottom:12px}.logo{width:58px;height:58px;border-radius:8px;background:linear-gradient(145deg,#86ca42,#5ba21d);display:grid;place-items:center;color:#fff;font-size:29px}.title{flex:1}.title h1{margin:0;color:#257c31;font-size:24px}.title p{margin:4px 0 0;color:#56616b}.ver{font-size:12px;color:#687680}.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:12px}.nav{background:#fff;border:1px solid var(--l);border-radius:9px;padding:8px;height:max-content;position:sticky;top:8px}.nav small{display:block;color:#8a959e;padding:8px 12px 4px;font-size:10px;text-transform:uppercase}.nav a{display:block;padding:11px 12px;border-radius:6px;color:#34404a;font-weight:600;text-decoration:none}.nav a:hover{background:#f5f8f3}.nav a.active{background:var(--gs);color:#2d7d29}.sep{height:1px;background:#edf0f2;margin:7px 4px}.card{background:#fff;border:1px solid var(--l);border-radius:9px;margin-bottom:12px}.card h2{font-size:17px;margin:0;padding:13px 15px;border-bottom:1px solid #edf0f2}.body{padding:15px}.score{display:flex;gap:18px;align-items:center}.num{width:86px;height:86px;border-radius:50%;display:grid;place-items:center;background:#edf8e8;border:7px solid #bddd9f;font-size:22px;font-weight:bold;color:#2d7d29}.grid{display:grid;grid-template-columns:repeat(4,minmax(140px,1fr));gap:9px;margin-top:15px}.metric{border:1px solid #e3e8eb;background:#fafbfb;border-radius:7px;padding:11px}.metric small{display:block;color:var(--m);margin-bottom:4px}.good{color:#278c2b}.warn{color:#b87410}.bad{color:#cf3838}.actions{display:grid;grid-template-columns:repeat(3,minmax(170px,1fr));gap:8px}.actions label{padding:9px;border:1px solid #e2e7ea;border-radius:6px;background:#fafbfb}.danger{margin-top:14px;padding:12px;border:1px solid #efc0c0;background:#fff5f5;border-radius:7px}.btn{border:1px solid #cdd6dc;background:var(--g);color:#fff;border-radius:6px;padding:9px 12px;cursor:pointer;font-weight:600}.notice{padding:10px 12px;border-radius:6px;margin-bottom:12px}.footer{text-align:center;color:#66727b;padding:16px;font-size:13px}.mobile{display:none}@media(max-width:850px){.layout{grid-template-columns:1fr}.nav{display:none}.mobile{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}.mobile a{background:#fff;border:1px solid var(--l);padding:8px;border-radius:6px;text-decoration:none;color:#34404a}.grid{grid-template-columns:repeat(2,1fr)}.actions{grid-template-columns:1fr}}</style>'''
V=html.escape(version());print(f'<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Security</title>{CSS}</head><body><div class="root"><div class="head"><div class="logo">🔒</div><div class="title"><h1>Security Center</h1><p>Sicherheitsstatus und MQTT-Berechtigungen</p></div><div class="ver">Version {V}</div></div><div class="mobile"><a href="index.cgi">⌂ Übersicht</a><a href="config.cgi">⚙ Einstellungen</a><a href="discover.cgi">⌕ Suche</a><a href="debug.cgi">▤ Debug</a><a href="/admin/index.cgi">← LoxBerry</a></div><div class="layout"><nav class="nav"><small>Fire TV Control</small><a href="index.cgi">⌂ Übersicht</a><a href="discover.cgi">⌕ Fire TVs suchen</a><div class="sep"></div><a href="config.cgi">⚙ Einstellungen</a><a class="active" href="security.cgi">🔒 Security Center</a><a href="debug.cgi">▤ Debug-Log</a><div class="sep"></div><a href="/admin/index.cgi">← Zurück zu LoxBerry</a></nav><main>')
if msg:print('<div class="notice good">%s</div>'%html.escape(msg))
if err:print('<div class="notice bad">%s</div>'%html.escape(err))
cls='good' if score>=85 else 'warn' if score>=70 else 'bad';print('<section class="card"><h2>Sicherheitsbewertung</h2><div class="body"><div class="score"><div class="num">%d</div><div><h3 class="%s">%s</h3></div></div><div class="grid"><div class="metric"><small>Webschutz</small><b class="good">CSRF aktiv</b></div><div class="metric"><small>Gerätesuche</small><b class="good">POST + CSRF</b></div><div class="metric"><small>MQTT</small><b class="%s">%s</b></div><div class="metric"><small>Riskante Befehle</small><b class="%s">%s</b></div></div></div></section>'%(score,cls,level,'warn' if listen else 'good','Aktiv' if listen else 'Aus','bad' if danger else 'good','Freigegeben' if danger else 'Gesperrt'))
print('<section class="card"><h2>MQTT-Befehls-Whitelist</h2><div class="body"><form method="post"><input type="hidden" name="csrf" value="%s"><div class="actions">'%html.escape(token(c),quote=True))
for a in SAFE_ACTIONS:print('<label><input type="checkbox" name="allow_%s" %s> %s</label>'%(a,'checked' if a in allowed else '',html.escape(a)))
print('</div><div class="danger"><b>Erweiterte Freigaben</b><p><label><input type="checkbox" name="allow_reboot" %s> Reboot über MQTT erlauben</label></p><p><label><input type="checkbox" name="allow_text" %s> Texteingabe über MQTT erlauben</label></p></div><p><button class="btn">Speichern</button></p></form></div></section>'%('checked' if m.get('allow_reboot') else '','checked' if m.get('allow_text') else ''))
print(f'<section class="card"><h2>Netzwerk</h2><div class="body">ADB TCP 5555 sollte in der Firewall nur vom LoxBerry zu den Fire TVs freigegeben sein.</div></section></main></div><div class="footer">Fire TV Control · Marco Düthorn · 2026 · v{V}</div></div></body></html>')
