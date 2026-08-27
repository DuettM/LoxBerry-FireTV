#!/usr/bin/env python3
import cgi,html,json,os,re,tempfile
ROOT=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME') or '/opt/loxberry';FOLDER='firetv';CFG=os.path.join(ROOT,'config','plugins',FOLDER,'config.json')
def load():
 with open(CFG,encoding='utf-8') as f:return json.load(f)
def save(c):
 fd,tmp=tempfile.mkstemp(prefix='.config-',dir=os.path.dirname(CFG),text=True)
 with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(c,f,ensure_ascii=False,indent=2);f.write('\n')
 os.chmod(tmp,0o600);os.replace(tmp,CFG)
f=cgi.FieldStorage();c=load();notice=''
if os.environ.get('REQUEST_METHOD','GET')=='POST':
 act=f.getfirst('form_action','')
 if act=='save_general':
  c['poll_interval']=max(10,int(f.getfirst('poll_interval','30')));c.setdefault('mqtt',{})['enabled']=bool(f.getfirst('mqtt_enabled'));c['mqtt']['listen_enabled']=bool(f.getfirst('mqtt_listen'));c['mqtt']['base_topic']=(f.getfirst('base_topic','firetv').strip().strip('/') or 'firetv');c.setdefault('watchdog',{})['enabled']=bool(f.getfirst('watchdog_enabled'));save(c);notice='Einstellungen gespeichert.'
 elif act=='add_device':
  ip=f.getfirst('ip','').strip();name=f.getfirst('name','Fire TV').strip()
  if ip:
   ident=re.sub(r'[^a-zA-Z0-9_-]+','-',name.lower()).strip('-') or ip.replace('.','-');c.setdefault('devices',[]).append({'id':ident,'name':name,'ip':ip,'port':int(f.getfirst('port','5555')),'enabled':True});save(c);notice='Gerät hinzugefügt. ADB-Verbindung am Fire TV bestätigen.'
 elif act=='delete':
  ident=f.getfirst('id','');c['devices']=[d for d in c.get('devices',[]) if str(d.get('id',''))!=ident];save(c);notice='Gerät gelöscht.'
print('Content-Type: text/html; charset=utf-8\n')
print('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Konfiguration</title><style>body{font-family:system-ui;max-width:1000px;margin:auto;padding:20px}section{padding:16px;margin:14px 0;border:1px solid #ddd;border-radius:10px}input{padding:7px;margin:4px}button{padding:8px 12px;background:#ff9900;border:0;border-radius:6px}</style></head><body><h1>Fire TV Control – Konfiguration</h1><p><a href="index.cgi">Dashboard</a> · <a href="debug.cgi">Debug</a></p>')
if notice:print('<p><b>%s</b></p>'%html.escape(notice))
print('<section><h2>Allgemein</h2><form method="post"><input type="hidden" name="form_action" value="save_general"><label>Abfrageintervall <input type="number" min="10" name="poll_interval" value="%s"></label><br><label>MQTT Basistopic <input name="base_topic" value="%s"></label><br><label><input type="checkbox" name="mqtt_enabled" %s> MQTT aktiv</label><br><label><input type="checkbox" name="mqtt_listen" %s> Befehle empfangen</label><br><label><input type="checkbox" name="watchdog_enabled" %s> Watchdog aktiv</label><br><button>Speichern</button></form></section>'%(c.get('poll_interval',30),html.escape(c.get('mqtt',{}).get('base_topic','firetv'),quote=True),'checked' if c.get('mqtt',{}).get('enabled',True) else '','checked' if c.get('mqtt',{}).get('listen_enabled',True) else '','checked' if c.get('watchdog',{}).get('enabled',True) else ''))
print('<section><h2>Fire TV hinzufügen</h2><form method="post"><input type="hidden" name="form_action" value="add_device"><input name="name" placeholder="Wohnzimmer" required><input name="ip" placeholder="192.168.1.50" required><input name="port" type="number" value="5555"><button>Hinzufügen</button></form></section><section><h2>Geräte</h2>')
for d in c.get('devices',[]):
 print('<p><b>%s</b> · %s:%s · MQTT-ID <code>%s</code> <form method="post" style="display:inline"><input type="hidden" name="form_action" value="delete"><input type="hidden" name="id" value="%s"><button>Löschen</button></form></p>'%(html.escape(d.get('name','')),html.escape(d.get('ip','')),d.get('port',5555),html.escape(d.get('id','')),html.escape(d.get('id',''),quote=True)))
print('</section><footer>Düthorn Marco · 2026 · v0.1.0</footer></body></html>')
