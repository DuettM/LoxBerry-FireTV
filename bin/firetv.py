#!/usr/bin/env python3
import argparse, json, os, re, socket, struct, subprocess, sys, time, tempfile

KEYS={"home":3,"back":4,"up":19,"down":20,"left":21,"right":22,"ok":23,"enter":66,"menu":82,"playpause":85,"stop":86,"next":87,"previous":88,"rewind":89,"fastforward":90,"mute":164,"volumeup":24,"volumedown":25,"wakeup":224,"sleep":223,"power":26}
APP_PRESETS={"prime":"com.amazon.firebat","primevideo":"com.amazon.firebat","netflix":"com.netflix.ninja","youtube":"com.amazon.firetv.youtube","disney":"com.disney.disneyplus","disneyplus":"com.disney.disneyplus","spotify":"com.spotify.tv.android"}

def load_json(path):
    with open(path,encoding="utf-8") as f:return json.load(f)

def plugin_root():
    root=os.environ.get("LBHOMEDIR") or os.environ.get("LBHOME")
    if not root: raise RuntimeError("LBHOMEDIR/LBHOME ist nicht gesetzt")
    return root
def general_json(): return os.path.join(plugin_root(),"config","system","general.json")
def base_topic(cfg): return str(cfg.get("mqtt",{}).get("base_topic","firetv") or "firetv").strip().strip("/")
def slug(s):
    s=re.sub(r"[^a-zA-Z0-9_-]+","-",str(s).strip().lower()).strip("-")
    return s or "device"
def mqtt_source_mtime(cfg=None):
    try:return os.path.getmtime(general_json())
    except OSError:return 0

def mqtt_connection_config(cfg):
    try:
        g=load_json(general_json()); m=g.get("Mqtt",{})
        return {"host":m.get("Brokerhost","127.0.0.1"),"port":int(m.get("Brokerport",1883)),"username":m.get("Brokeruser",""),"password":m.get("Brokerpass","")}
    except Exception:return {"host":"127.0.0.1","port":1883,"username":"","password":""}

def log_path(cfg):
    cp=cfg.get("_config_path","")
    folder=os.path.basename(os.path.dirname(cp)) if cp else "firetv"
    return os.path.join(plugin_root(),"log","plugins",folder,"firetv.log")
def debug_log(cfg,level,msg):
    try:
        p=log_path(cfg); os.makedirs(os.path.dirname(p),exist_ok=True)
        with open(p,"a",encoding="utf-8") as f:f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{str(level).upper()}] {msg}\n")
    except Exception:pass

def _enc_len(n):
    out=b""
    while True:
        d=n%128;n//=128
        if n:d|=128
        out+=bytes([d])
        if not n:return out
def _mstr(v):
    b=str(v).encode();return struct.pack("!H",len(b))+b

def mqtt_publish(cfg,topic,payload,retain=False):
    if not cfg.get("mqtt",{}).get("enabled",True):return False
    mc=mqtt_connection_config(cfg);s=None
    try:
        cid=f"lb-firetv-pub-{os.getpid()}";flags=2;pl=_mstr(cid)
        if mc.get("username"):
            flags|=0x80;pl+=_mstr(mc["username"])
            if mc.get("password") is not None:flags|=0x40;pl+=_mstr(mc.get("password",""))
        vh=_mstr("MQTT")+bytes([4,flags])+struct.pack("!H",20)
        s=socket.create_connection((mc["host"],int(mc["port"])),timeout=4);s.sendall(bytes([0x10])+_enc_len(len(vh)+len(pl))+vh+pl);s.recv(4)
        body=_mstr(topic)+str(payload).encode();s.sendall(bytes([0x31 if retain else 0x30])+_enc_len(len(body))+body);s.sendall(b"\xe0\x00");return True
    except Exception as e:debug_log(cfg,"warning",f"MQTT publish fehlgeschlagen: {e}");return False
    finally:
        try:
            if s:s.close()
        except Exception:pass

def mqtt_event(cfg,suffix,data,retain=False):
    payload=data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,separators=(",",":"))
    return mqtt_publish(cfg,base_topic(cfg)+"/"+suffix,payload,retain)

class FireTV:
    def __init__(self,cfg,device):
        self.cfg=cfg;self.device=device;self.ip=str(device.get("ip","")).strip();self.port=int(device.get("port",5555));self.target=f"{self.ip}:{self.port}";self.timeout=max(2,int(cfg.get("adb_timeout",8)))
    def _run(self,args):
        try:p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=self.timeout)
        except FileNotFoundError:raise RuntimeError("ADB ist nicht installiert")
        except subprocess.TimeoutExpired:raise RuntimeError("ADB Zeitüberschreitung")
        return p.returncode,(p.stdout or "").strip()
    def connect(self):
        rc,out=self._run(["adb","connect",self.target]);low=out.lower()
        if "unauthorized" in low:return {"ok":False,"authorized":False,"message":out}
        ok=("connected to" in low or "already connected" in low)
        return {"ok":ok,"authorized":ok,"message":out}
    def shell(self,*args):
        self.connect();rc,out=self._run(["adb","-s",self.target,"shell",*map(str,args)]);low=out.lower()
        if "unauthorized" in low:raise RuntimeError("ADB nicht autorisiert – Verbindung am Fire TV bestätigen")
        if "no devices" in low or "offline" in low or "not found" in low:raise RuntimeError(out)
        return out
    def key(self,key):
        k=str(key).lower();code=KEYS.get(k,k);self.shell("input","keyevent",str(code));return {"ok":True,"action":k}
    def volume(self,direction):
        d=str(direction).lower();adj={"volumeup":"raise","volumedown":"lower","mute":"toggle"}.get(d)
        if not adj:raise ValueError("Ungültige Lautstärkeaktion")
        attempts=[]
        for cmd in (("cmd","media_session","volume","--stream","3","--adj",adj),("media","volume","--stream","3","--adj",adj)):
            try:
                out=self.shell(*cmd); attempts.append(out)
                if "unknown" not in out.lower() and "error" not in out.lower():return {"ok":True,"action":d,"method":"media_session","output":out[-300:]}
            except Exception as e:attempts.append(str(e))
        self.key(d)
        return {"ok":True,"action":d,"method":"keyevent-fallback","note":"Bei HDMI-CEC/IR kann Fire TV ADB die Hardware-Lautstärketaste nicht auf jedem TV vollständig emulieren."}
    def tv_on(self):
        self.key("wakeup");time.sleep(0.35);self.key("home")
        return {"ok":True,"action":"tvon","method":"firetv-one-touch-play","note":"Fire TV Gerätesteuerung/HDMI-CEC muss aktiviert sein."}
    def tv_off(self):
        self.key("sleep")
        return {"ok":True,"action":"tvoff","method":"firetv-standby-cec","note":"CEC-Standby hängt von Fire TV und TV-Gerätesteuerung ab."}
    def launch(self,package):
        package=APP_PRESETS.get(str(package).lower(),package);out=self.shell("monkey","-p",str(package),"-c","android.intent.category.LAUNCHER","1");return {"ok":True,"package":package,"output":out[-500:]}
    def status(self):
        r={"name":self.device.get("name","Fire TV"),"ip":self.ip,"port":self.port,"id":slug(self.device.get("id") or self.device.get("name") or self.ip),"online":False,"authorized":False}
        c=self.connect();r["adb_message"]=c["message"];r["authorized"]=bool(c["authorized"])
        if not c["ok"]:return r
        try:
            r["online"]=self._run(["adb","-s",self.target,"get-state"])[1].strip()=="device";r["model"]=self.shell("getprop","ro.product.model").strip();r["manufacturer"]=self.shell("getprop","ro.product.manufacturer").strip();r["android"]=self.shell("getprop","ro.build.version.release").strip();r["build"]=self.shell("getprop","ro.build.version.incremental").strip();power=self.shell("dumpsys","power");r["awake"]=bool(re.search(r"mWakefulness=Awake|Display Power: state=ON|state=ON",power,re.I));win=self.shell("dumpsys","window","windows");m=re.search(r"mCurrentFocus=.*?\s([A-Za-z0-9._]+)/(?:[A-Za-z0-9._$]+)",win)
            if not m:
                act=self.shell("dumpsys","activity","activities");m=re.search(r"mResumedActivity:.*?\s([A-Za-z0-9._]+)/",act)
            r["app"]=m.group(1) if m else ""
            try:r["cec_setting"]=self.shell("settings","get","global","hdmi_control_enabled").strip()
            except Exception:r["cec_setting"]="unknown"
        except Exception as e:r["error"]=str(e)
        return r
    def list_apps(self):
        out=self.shell("pm","list","packages");return sorted({x.split(":",1)[1].strip() for x in out.splitlines() if x.startswith("package:")})
    def command(self,action,value=None):
        a=str(action).strip().lower()
        if a=="status":return self.status()
        if a in ("volumeup","volumedown","mute"):return self.volume(a)
        if a in KEYS:return self.key(a)
        if a=="standby":return self.key("sleep")
        if a in ("on","wake","tvon","tv_on"):return self.tv_on()
        if a in ("off","tvoff","tv_off"):return self.tv_off()
        if a=="reboot":self._run(["adb","-s",self.target,"reboot"]);return {"ok":True,"action":"reboot"}
        if a in ("app","launch"):
            if not value:raise ValueError("App/Package fehlt")
            return self.launch(value)
        if a=="text":
            if value is None:raise ValueError("Text fehlt")
            self.shell("input","text",str(value).replace(" ","%s"));return {"ok":True,"action":"text"}
        if a=="apps":return {"ok":True,"apps":self.list_apps()}
        raise ValueError("Unbekannter Befehl: "+a)

def find_device(cfg,ident):
    ident=str(ident)
    for d in cfg.get("devices",[]):
        if ident in (str(d.get("id","")),slug(d.get("id","")),slug(d.get("name","")),str(d.get("ip",""))):return d
    raise KeyError("Fire TV nicht gefunden: "+ident)

def publish_status(cfg,st):
    b=base_topic(cfg)+"/"+st["id"];ret=bool(cfg.get("mqtt",{}).get("retain_state",True));mqtt_publish(cfg,b+"/online","1" if st.get("online") else "0",ret);mqtt_publish(cfg,b+"/authorized","1" if st.get("authorized") else "0",ret);mqtt_publish(cfg,b+"/awake","1" if st.get("awake") else "0",ret);mqtt_publish(cfg,b+"/app",st.get("app",""),ret);mqtt_publish(cfg,b+"/state",json.dumps(st,ensure_ascii=False,separators=(",",":")),ret)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",required=True);ap.add_argument("--device");ap.add_argument("--action",default="status");ap.add_argument("--value");ap.add_argument("--poll-all",action="store_true");a=ap.parse_args();cfg=load_json(a.config);cfg["_config_path"]=a.config
    if a.poll_all:
        out=[]
        for d in cfg.get("devices",[]):
            if d.get("enabled",True):
                try:st=FireTV(cfg,d).status();publish_status(cfg,st);out.append(st)
                except Exception as e:out.append({"name":d.get("name"),"online":False,"error":str(e)})
        mqtt_event(cfg,"availability","online",True);print(json.dumps(out,ensure_ascii=False));return 0
    if not a.device:raise SystemExit("--device fehlt")
    d=find_device(cfg,a.device);r=FireTV(cfg,d).command(a.action,a.value)
    if a.action=="status" and isinstance(r,dict):publish_status(cfg,r)
    print(json.dumps(r,ensure_ascii=False));return 0
if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:print(json.dumps({"ok":False,"error":str(e)},ensure_ascii=False));sys.exit(1)
