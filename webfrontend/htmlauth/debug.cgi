#!/usr/bin/env python3
import html,json,os,subprocess
ROOT=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME') or '/opt/loxberry';FOLDER='firetv';CFG=os.path.join(ROOT,'config','plugins',FOLDER,'config.json');LOG=os.path.join(ROOT,'log','plugins',FOLDER,'firetv.log')
print('Content-Type: text/html; charset=utf-8\n')
print('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Debug</title></head><body><h1>Fire TV Control – Debug</h1><p><a href="index.cgi">Dashboard</a> · <a href="config.cgi">Konfiguration</a></p>')
try:
 c=json.load(open(CFG,encoding='utf-8'))
except Exception:c={}
for cmd,label in [(['adb','version'],'ADB'),(['python3','--version'],'Python')]:
 try:p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=5);print('<p><b>%s:</b> %s</p>'%(label,html.escape(p.stdout.strip())))
 except Exception as e:print('<p><b>%s:</b> %s</p>'%(label,html.escape(str(e))))
print('<p><b>MQTT:</b> %s</p>'%('aktiv' if c.get('mqtt',{}).get('enabled',True) else 'deaktiviert'))
print('<p><b>Watchdog:</b> %s</p>'%('aktiv' if c.get('watchdog',{}).get('enabled',True) else 'deaktiviert'))
print('<h2>Log</h2><pre>')
try:print(html.escape('\n'.join(open(LOG,encoding='utf-8',errors='replace').read().splitlines()[-100:])))
except Exception as e:print(html.escape(str(e)))
print('</pre><footer>Düthorn Marco · 2026 · v0.1.0</footer></body></html>')
