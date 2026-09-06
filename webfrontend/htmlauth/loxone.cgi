#!/usr/bin/env python3
import html,json,os,re,sys
from urllib.parse import parse_qs

def root():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);m=os.sep+'webfrontend'+os.sep
 if m in p:return p.split(m,1)[0]
 r=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME')
 if r:return r
 raise RuntimeError('LoxBerry Basisverzeichnis konnte nicht ermittelt werden')
def folder():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);parts=p.split(os.sep);return parts[parts.index('plugins')+1] if 'plugins' in parts else 'firetv'
FOLDER=folder();BASE=root();CFG=os.path.join(BASE,'config','plugins',FOLDER,'config.json')
def version():
 base=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__).split(os.sep+'webfrontend'+os.sep,1)[0]
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
def slug(s):
 s=re.sub(r'[^a-z0-9]+','-',str(s).strip().lower()).strip('-');return s or 'firetv'

try:C=json.load(open(CFG,encoding='utf-8'))
except Exception as e:
 print('Status: 500 Internal Server Error\r\nContent-Type: text/html; charset=utf-8\r\n\r\n<h1>Fire TV Control</h1><p>%s</p>'%html.escape(str(e)));sys.exit(0)

Q={k:(v[-1] if v else '') for k,v in parse_qs(os.environ.get('QUERY_STRING',''),keep_blank_values=True).items()}
M=C.get('mqtt',{})
BASETOPIC=str(M.get('base_topic','firetv') or 'firetv').strip('/')
TOKEN=str(M.get('command_token','') or '') if M.get('command_token_required',False) else ''
ALLOWED=set(str(x).lower() for x in M.get('allowed_actions',[]))
if M.get('allow_reboot',False):ALLOWED.add('reboot')
if M.get('allow_text',False):ALLOWED.add('text')
UDPPORT='11884'
DEVICES=[d for d in C.get('devices',[]) if d.get('enabled',True)] or [{'name':'Fire TV','id':'firetv','ip':''}]

# Aktion, Beschriftung, optionaler Wert
CMDS=[('tvon','TV einschalten (CEC)',None),('tvoff','TV ausschalten (CEC)',None),
      ('wakeup','Aufwecken',None),('standby','Standby',None),
      ('home','Home',None),('back','Zurück',None),('menu','Menü',None),
      ('up','Hoch',None),('down','Runter',None),('left','Links',None),('right','Rechts',None),('ok','OK',None),
      ('playpause','Play/Pause',None),('stop','Stopp',None),('next','Weiter',None),('previous','Zurück (Titel)',None),
      ('volumeup','Lauter',None),('volumedown','Leiser',None),('mute','Stumm',None),
      ('app','App starten (Netflix)','com.netflix.ninja')]

def payload(act,val):
 """Ohne Token reicht die Kurzform, mit Token muss es JSON sein."""
 if TOKEN:
  o={'action':act}
  if val:o['value']=val
  o['token']=TOKEN
  return json.dumps(o,ensure_ascii=False,separators=(',',':'))
 return act+(':'+val if val else '')

def xa(s):return html.escape(str(s),quote=True)

def build_xml():
 host=os.environ.get('HTTP_HOST','loxberry').split(':')[0]
 addr='/dev/udp/%s/%s'%(host,UDPPORT)
 out=['<?xml version="1.0" encoding="UTF-8"?>']
 out.append('<VirtualOut Title="Fire TV Control (MQTT)" Comment="LoxBerry Fire TV Control %s - sendet ueber das MQTT-Gateway. Port ggf. an den LoxBerry-Eingangsport der Plugin-Einstellungen anpassen." Address="%s" CmdInit="" CmdSep="" CloseAfterSend="true">'%(xa(version()),xa(addr)))
 multi=len(DEVICES)>1
 for d in DEVICES:
  ident=slug(d.get('id') or d.get('name') or d.get('ip'))
  pre=('%s - '%(d.get('name') or ident)) if multi else ''
  for act,label,val in CMDS:
   if act not in ALLOWED:continue
   cmd='publish %s/%s/set %s'%(BASETOPIC,ident,payload(act,val))
   out.append('  <VirtualOutCmd Title="%s" Comment="%s" Analog="false" Repeat="0" RepeatRate="0" CmdOnMethod="GET" CmdOn="%s" CmdOnPost="" CmdOnHTTP="" CmdOffMethod="GET" CmdOff="" CmdOffPost="" CmdOffHTTP=""/>'%(xa(pre+label),xa('%s auf %s'%(act,ident)),xa(cmd)))
 out.append('</VirtualOut>')
 return '\n'.join(out)+'\n'

if Q.get('download')=='vq':
 x=build_xml().encode('utf-8')
 sys.stdout.buffer.write(('Content-Type: application/xml; charset=utf-8\r\nContent-Disposition: attachment; filename="VQ_FireTV_MQTT.xml"\r\nContent-Length: %d\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\n\r\n'%len(x)).encode('ascii'))
 sys.stdout.buffer.write(x);sys.stdout.buffer.flush();sys.exit(0)

print("Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'self'\r\nX-Frame-Options: SAMEORIGIN\r\n\r\n",end='')
print('''<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Loxone – Fire TV Control</title><style>
:root{--g:#73b72b;--gs:#eaf5df;--l:#dde4e8}
*{box-sizing:border-box}body{margin:0;background:#f6f8f9;color:#29323a;font-family:Arial,Helvetica,sans-serif}
.root{max-width:1480px;margin:0 auto;padding:12px 12px 28px}
.head{display:flex;align-items:center;gap:14px;background:#fff;border:1px solid var(--l);border-radius:9px;padding:13px 16px;margin-bottom:12px}
.head h1{margin:0;color:#257c31;font-size:22px;flex:1}
.ver{font-size:12px;color:#687680;background:#f7f9fa;border:1px solid var(--l);padding:7px 10px;border-radius:6px}
.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:12px}
.nav{background:#fff;border:1px solid var(--l);border-radius:9px;padding:8px;height:max-content;position:sticky;top:8px}
.nav small{display:block;color:#8a959e;padding:8px 12px 4px;font-size:10px;text-transform:uppercase;letter-spacing:.07em}
.nav a{display:block;padding:11px 12px;border-radius:6px;color:#34404a;font-weight:600;text-decoration:none}
.nav a:hover{background:#f5f8f3}.nav a.active{background:var(--gs);color:#2d7d29}
.nav .sep{height:1px;background:#edf0f2;margin:7px 4px}
.card{background:#fff;border:1px solid var(--l);border-radius:9px;margin-bottom:12px}
.card h2{font-size:17px;margin:0;padding:13px 15px;border-bottom:1px solid #edf0f2}
.body{padding:15px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:8px 6px;border-bottom:1px solid #eef1f3;vertical-align:top}
th{font-size:11px;text-transform:uppercase;color:#87949e}
code{background:#f4f7f8;border:1px solid #e4eaed;border-radius:4px;padding:2px 5px;font-size:13px;word-break:break-all}
.btn{display:inline-block;background:var(--g);color:#fff;border:0;border-radius:6px;padding:11px 15px;font-weight:700;text-decoration:none}
.box{background:#fafbfb;border:1px solid #e6ebee;border-radius:7px;padding:12px;margin-bottom:12px}
ol{margin:6px 0 0 18px;padding:0}ol li{margin-bottom:5px}
.footer{text-align:center;color:#66727b;padding:14px;font-size:13px}
.mobile{display:none}
@media(max-width:900px){.layout{grid-template-columns:1fr}.nav{display:none}.mobile{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}.mobile a{background:#fff;border:1px solid var(--l);padding:9px 11px;border-radius:6px;text-decoration:none;color:#34404a}.mobile a.active{background:var(--g);border-color:var(--g);color:#fff;font-weight:700}table,thead,tbody,tr,td,th{display:block}thead{display:none}td{border:0;padding:3px 0}tr{border-bottom:1px solid #eef1f3;padding:8px 0}}
</style></head><body><div class="root">''')
print('<div class="head"><h1>Loxone-Anbindung</h1><span class="ver">v%s</span></div>'%html.escape(version()))
print('<div class="mobile"><a href="dashboard.cgi">\u2302 Übersicht</a><a href="config.cgi">\u2699 Einstellungen</a><a href="discover.cgi">\u2315 Suche</a><a href="security.cgi">\U0001f512 Sicherheit</a><a class="active" href="loxone.cgi">\u21c4 Loxone</a><a href="debug.cgi">\u25a4 Debug</a></div>')
print('<div class="layout"><nav class="nav"><small>Fire TV Control</small><a href="dashboard.cgi">\u2302 Übersicht</a><a href="discover.cgi">\u2315 Fire TVs suchen</a><div class="sep"></div><a href="config.cgi">\u2699 Einstellungen</a><a href="security.cgi">\U0001f512 Security Center</a><a class="active" href="loxone.cgi">\u21c4 Loxone</a><a href="debug.cgi">\u25a4 Debug-Log</a></nav><div class="content">')

blocked=[l for a,l,v in CMDS if a not in ALLOWED]

print('<div class="card"><h2>\u2460 Vorlage für virtuelle Ausgänge</h2><div class="body">')
print('<p>Die Vorlage enthält für jedes eingerichtete Fire TV einen Ausgangsbefehl je Funktion. Die Befehle gehen per UDP an das MQTT-Gateway, das sie an den Broker weiterreicht.</p>')
print('<p><a class="btn" href="loxone.cgi?download=vq">VQ_FireTV_MQTT.xml herunterladen</a></p>')
print('<div class="box"><b>So spielst du sie ein</b><ol>')
print('<li>Datei nach <code>Dokumente\\Loxone\\Loxone Config\\Templates\\VirtualOut</code> kopieren</li>')
print('<li>Loxone Config neu starten</li>')
print('<li>Peripherie → Virtuelle Ausgänge → Gerätevorlagen → „Fire TV Control (MQTT)" wählen</li>')
print('<li>Adresse prüfen: <code>%s</code></li>'%html.escape('/dev/udp/%s/%s'%(os.environ.get('HTTP_HOST','loxberry').split(':')[0],UDPPORT)))
print('</ol><p style="margin:8px 0 0">Der Port muss dem <b>LoxBerry-Eingangsport</b> aus den Einstellungen des MQTT-Gateway entsprechen – nicht dem Miniserver-UDP-Port. Standard ist %s.</p></div>'%UDPPORT)
if blocked:
 print('<div class="box"><b>Nicht enthalten:</b> %s.<br>Diese Aktionen stehen nicht in der Befehls-Whitelist. Im <a href="security.cgi">Security Center</a> freigeben, dann die Vorlage neu herunterladen.</div>'%html.escape(', '.join(blocked)))
if TOKEN:
 print('<div class="box">Der Befehlstoken ist aktiv, deshalb sind die Nutzlasten als JSON erzeugt und enthalten den Token im Klartext. Behandle die Datei entsprechend.</div>')
print('</div></div>')

print('<div class="card"><h2>\u2461 Befehle zum Kopieren</h2><div class="body">')
print('<div class="box"><b>Virtueller Ausgang</b><br>Adresse: <code>%s</code></div>'%html.escape('/dev/udp/%s/%s'%(os.environ.get('HTTP_HOST','loxberry').split(':')[0],UDPPORT)))
print('<p>Pro Funktion einen Ausgangsbefehl anlegen und den Text unten bei <b>Befehl bei EIN</b> eintragen. Haken bei „Als Digitalausgang verwenden" setzen.</p>')
for d in DEVICES:
 ident=slug(d.get('id') or d.get('name') or d.get('ip'))
 print('<h3 style="font-size:15px;margin:16px 0 6px">%s <span style="color:#87949e;font-weight:normal">(%s)</span></h3>'%(html.escape(str(d.get('name','Fire TV'))),html.escape(ident)))
 print('<table><thead><tr><th>Funktion</th><th>Befehl bei EIN</th></tr></thead><tbody>')
 for act,label,val in CMDS:
  if act not in ALLOWED:continue
  print('<tr><td>%s</td><td><code>publish %s/%s/set %s</code></td></tr>'%(html.escape(label),html.escape(BASETOPIC),html.escape(ident),html.escape(payload(act,val))))
 print('</tbody></table>')
print('</div></div>')

print('<div class="card"><h2>\u2462 Rückmeldungen in den Miniserver</h2><div class="body">')
print('<p>Das Plugin veröffentlicht den Status von sich aus. Damit die Werte im Miniserver ankommen, müssen die Topics im MQTT-Gateway abonniert sein (Einstellungen → Subscriptions, z.\u202fB. <code>%s/#</code>).</p>'%html.escape(BASETOPIC))
print('<table><thead><tr><th>Topic</th><th>Bedeutung</th></tr></thead><tbody>')
for d in DEVICES:
 ident=slug(d.get('id') or d.get('name') or d.get('ip'))
 for suf,desc in (('online','Fire TV erreichbar (1/0)'),('awake','Bildschirm an (1/0)'),('display','ON / OFF'),('app','laufende App'),('authorized','ADB autorisiert (1/0)')):
  print('<tr><td><code>%s/%s/%s</code></td><td>%s</td></tr>'%(html.escape(BASETOPIC),html.escape(ident),suf,html.escape(desc)))
print('<tr><td><code>%s/availability</code></td><td>Listener läuft</td></tr>'%html.escape(BASETOPIC))
print('<tr><td><code>%s/event</code></td><td>Ergebnis des letzten Befehls (JSON)</td></tr>'%html.escape(BASETOPIC))
print('<tr><td><code>%s/security</code></td><td>abgewiesener Befehl mit Begründung (JSON)</td></tr>'%html.escape(BASETOPIC))
print('</tbody></table>')
print('<div class="box" style="margin-top:12px"><b>Virtuelle Eingänge anlegen</b><ol>')
print('<li>Im MQTT-Gateway „Incoming Overview" öffnen und den Bereich „UDP Transmissions" aufklappen</li>')
print('<li>Dort steht neben jedem Wert die fertige Befehlserkennung</li>')
print('<li>In Loxone Config einen „Virtuellen UDP Eingang" auf dem Miniserver-UDP-Port des Gateway anlegen</li>')
print('<li>Pro Wert einen UDP-Eingangsbefehl anlegen und die Befehlserkennung einfügen</li>')
print('</ol><p style="margin:8px 0 0">Eine Vorlage kann das Plugin dafür nicht erzeugen – die Befehlserkennung hängt davon ab, wie dein Gateway konfiguriert ist. Das Gateway überträgt außerdem nur Änderungen.</p></div>')
print('</div></div>')

print('</div></div><div class="footer">Fire TV Control · v%s</div></div></body></html>'%html.escape(version()))
