#!/usr/bin/env python3
import cgi,json,os,subprocess
ROOT=os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME') or '/opt/loxberry'
FOLDER='firetv';CFG=os.path.join(ROOT,'config','plugins',FOLDER,'config.json');BIN=os.path.join(ROOT,'bin','plugins',FOLDER)
print('Content-Type: application/json; charset=utf-8\n')
try:
 c=json.load(open(CFG,encoding='utf-8'));f=cgi.FieldStorage();dev=f.getfirst('device');action=f.getfirst('action','status');value=f.getfirst('value')
 if not dev:
  print(json.dumps({'ok':True,'devices':c.get('devices',[])},ensure_ascii=False));raise SystemExit
 cmd=[os.path.join(BIN,'firetv.py'),'--config',CFG,'--device',dev,'--action',action]
 if value is not None:cmd+=['--value',value]
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=15);print(p.stdout.strip())
except SystemExit:pass
except Exception as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False))
