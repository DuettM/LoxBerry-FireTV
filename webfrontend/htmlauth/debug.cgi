#!/usr/bin/env python3
import html,json,os,re,subprocess

def root(): return os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME') or '/opt/loxberry'
def folder():
 p=os.path.abspath(os.environ.get('SCRIPT_FILENAME') or __file__);parts=p.split(os.sep);return parts[parts.index('plugins')+1] if 'plugins' in parts else 'firetv'
FOLDER=folder();CFG=os.path.join(root(),'config','plugins',FOLDER,'config.json');LOG=os.path.join(root(),'log','plugins',FOLDER,'firetv.log')
def redact(line,c):
 secrets=[str(c.get('web_secret',''))]
 for s in secrets:
  if len(s)>=4:line=line.replace(s,'[REDACTED]')
 line=re.sub(r'(?i)(authorization\s*:\s*(?:bearer|basic)\s+)[^\s,;]+',r'\1[REDACTED]',line)
 line=re.sub(r'(?i)((?:password|passwd|token|secret)\s*[=:]\s*)[^\s,;]+',r'\1[REDACTED]',line)
 return line
print('Content-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\n\r\n')
print('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire TV Debug</title></head><body><h1>Fire TV Control – Debug</h1><p><a href="index.cgi">Dashboard</a> · <a href="config.cgi">Konfiguration</a></p>')
try:c=json.load(open(CFG,encoding='utf-8'))
except Exception:c={}
for cmd,label in [(['adb','version'],'ADB'),(['python3','--version'],'Python')]:
 try:p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=5);print('<p><b>%s:</b> %s</p>'%(label,html.escape((p.stdout or '').strip())))
 except Exception as e:print('<p><b>%s:</b> %s</p>'%(label,html.escape(str(e))))
print('<p><b>Pluginordner:</b> %s</p>'%html.escape(FOLDER));print('<p><b>MQTT:</b> %s</p>'%('aktiv' if c.get('mqtt',{}).get('enabled',True) else 'deaktiviert'));print('<p><b>Watchdog:</b> %s</p>'%('aktiv' if c.get('watchdog',{}).get('enabled',True) else 'deaktiviert'))
print('<h2>Log (bereinigt)</h2><pre>')
try:
 lines=open(LOG,encoding='utf-8',errors='replace').read().splitlines()[-100:];print(html.escape('\n'.join(redact(x,c) for x in lines)))
except Exception as e:print(html.escape(str(e)))
print('</pre><footer>Düthorn Marco · 2026 · v0.2.0</footer></body></html>')
