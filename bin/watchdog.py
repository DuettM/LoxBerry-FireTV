#!/usr/bin/env python3
import json, os, shutil, subprocess, sys, time
if len(sys.argv)<2: raise SystemExit(2)
cfgp=sys.argv[1]
with open(cfgp,encoding="utf-8") as f: cfg=json.load(f)
if not cfg.get("watchdog",{}).get("enabled",True): raise SystemExit(0)
root=os.environ.get("LBHOMEDIR") or os.environ.get("LBHOME")
if not root: raise SystemExit("LBHOMEDIR/LBHOME ist nicht gesetzt")
folder=os.path.basename(os.path.dirname(cfgp))
binp=os.path.join(root,"bin","plugins",folder)
logdir=os.path.join(root,"log","plugins",folder)
logp=os.path.join(logdir,"watchdog.log")
daemonlog=os.path.join(logdir,"mqtt-daemon.log")
os.makedirs(logdir,exist_ok=True)
MAXLOG=1048576
def log(s):
    try:
        if os.path.getsize(logp)>MAXLOG: os.replace(logp,logp+".1")
    except OSError: pass
    with open(logp,"a",encoding="utf-8") as f: f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {s}\n")

def launch_cmd(inner):
    """Der Cron läuft als root, der Listener darf aber nur als loxberry laufen -
    sonst gehören Logdateien nach einem Watchdog-Neustart root."""
    if os.geteuid()!=0: return inner
    if shutil.which("runuser"): return ["runuser","-u","loxberry","--"]+inner
    if shutil.which("setpriv"): return ["setpriv","--reuid=loxberry","--regid=loxberry","--init-groups"]+inner
    return ["su","-s","/bin/sh","loxberry","-c"," ".join("'"+a.replace("'","'\\''")+"'" for a in inner)]

try:
    out=subprocess.run(["pgrep","-f",f"{binp}/mqtt_listener.py.*{cfgp}"],stdout=subprocess.PIPE,text=True).stdout.strip()
    if not out:
        inner=[os.path.join(binp,"mqtt_listener.py"),"--config",cfgp,"--core",os.path.join(binp,"firetv.py")]
        with open(daemonlog,"a") as lf:
            subprocess.Popen(launch_cmd(inner),stdout=lf,stderr=subprocess.STDOUT,start_new_session=True)
        try: os.chmod(daemonlog,0o600)
        except OSError: pass
        log("[WARN] MQTT Listener neu gestartet")
except Exception as e:
    log("[ERROR] "+str(e))
