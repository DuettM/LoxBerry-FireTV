#!/usr/bin/env python3
import json, os, subprocess, sys, time
if len(sys.argv)<2: raise SystemExit(2)
cfgp=sys.argv[1]
with open(cfgp,encoding="utf-8") as f: cfg=json.load(f)
if not cfg.get("watchdog",{}).get("enabled",True): raise SystemExit(0)
root=os.environ.get("LBHOMEDIR") or os.environ.get("LBHOME")
if not root: raise SystemExit("LBHOMEDIR/LBHOME ist nicht gesetzt")
folder=os.path.basename(os.path.dirname(cfgp))
binp=os.path.join(root,"bin","plugins",folder)
logp=os.path.join(root,"log","plugins",folder,"watchdog.log")
os.makedirs(os.path.dirname(logp),exist_ok=True)
def log(s):
    with open(logp,"a",encoding="utf-8") as f:f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {s}\n")
try:
    out=subprocess.run(["pgrep","-f",f"{binp}/mqtt_listener.py.*{cfgp}"],stdout=subprocess.PIPE,text=True).stdout.strip()
    if not out:
        subprocess.Popen([os.path.join(binp,"mqtt_listener.py"),"--config",cfgp,"--core",os.path.join(binp,"firetv.py")],
                         stdout=open(os.path.join(root,"log","plugins",folder,"mqtt-daemon.log"),"a"),
                         stderr=subprocess.STDOUT,start_new_session=True)
        log("[WARN] MQTT Listener neu gestartet")
except Exception as e:
    log("[ERROR] "+str(e))
