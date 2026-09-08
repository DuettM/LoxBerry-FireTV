#!/usr/bin/env python3
import argparse,ipaddress,json,os,re,shlex,socket,struct,subprocess,sys,time

KEYS={"home":3,"back":4,"up":19,"down":20,"left":21,"right":22,"ok":23,"enter":66,"menu":82,"playpause":85,"stop":86,"next":87,"previous":88,"rewind":89,"fastforward":90,"mute":164,"volumeup":24,"volumedown":25,"wakeup":224,"sleep":223,"power":26}
APP_PRESETS={"prime":"com.amazon.firebat","primevideo":"com.amazon.firebat","netflix":"com.netflix.ninja","youtube":"com.amazon.firetv.youtube","disney":"com.disney.disneyplus","disneyplus":"com.disney.disneyplus","spotify":"com.spotify.tv.android"}

def load_json(path):
    with open(path,encoding="utf-8") as f:return json.load(f)
def plugin_root():
    root=os.environ.get("LBHOMEDIR") or os.environ.get("LBHOME")
    if not root:raise RuntimeError("LBHOMEDIR/LBHOME ist nicht gesetzt")
    return root
def general_json():return os.path.join(plugin_root(),"config","system","general.json")
SCREEN_METHODS=[("auto","Automatisch (bevorzugt Display Power)"),
                ("display","Display Power: state=ON"),
                ("suspendblocker","mHoldingDisplaySuspendBlocker=true"),
                ("display_or_blocker","Display Power oder Suspend Blocker"),
                ("wakefulness","mWakefulness=Awake")]
def screen_values(power):
    """Die drei Rohwerte aus dumpsys power. None = Zeile nicht vorhanden."""
    w=True if re.search(r"mWakefulness\s*=\s*Awake",power,re.I) else (False if re.search(r"mWakefulness\s*=",power,re.I) else None)
    m=re.search(r"Display Power:\s*state\s*=\s*(\w+)",power,re.I);d=(m.group(1).upper()=="ON") if m else None
    m=re.search(r"mHoldingDisplaySuspendBlocker\s*=\s*(\w+)",power,re.I);b=(m.group(1).lower()=="true") if m else None
    return {"wakefulness":w,"display":d,"suspendblocker":b}
def screen_from_power(power,method="auto"):
    v=screen_values(power);method=str(method or "auto").lower()
    if method in ("wakefulness","display","suspendblocker"):return bool(v[method])
    if method=="display_or_blocker":return bool(v["display"]) or bool(v["suspendblocker"])
    # auto: Display Power ist am aussagekraeftigsten, dann der Suspend Blocker,
    # Wakefulness nur als letzter Ausweg - ein Fire TV Stick bleibt oft wach,
    # obwohl der Fernseher laengst aus ist.
    for k in ("display","suspendblocker","wakefulness"):
        if v[k] is not None:return bool(v[k])
    return False
def base_topic(cfg):return str(cfg.get("mqtt",{}).get("base_topic","firetv") or "firetv").strip().strip("/")
def slug(s):
    s=re.sub(r"[^a-zA-Z0-9_-]+","-",str(s).strip().lower()).strip("-")
    return s or "device"
def mqtt_connection_config(cfg):
    try:
        g=load_json(general_json());m=g.get("Mqtt",{})
        return {"host":m.get("Brokerhost","127.0.0.1"),"port":int(m.get("Brokerport",1883)),"username":m.get("Brokeruser",""),"password":m.get("Brokerpass","")}
    except Exception:return {"host":"127.0.0.1","port":1883,"username":"","password":""}
def mqtt_source_mtime(cfg):
    try:return os.path.getmtime(general_json())
    except Exception:return 0
def log_path(cfg):
    cp=cfg.get("_config_path","");folder=os.path.basename(os.path.dirname(cp)) if cp else "firetv"
    return os.path.join(plugin_root(),"log","plugins",folder,"firetv.log")
LOG_LEVELS={"emerg":0,"alert":1,"critical":2,"error":3,"warning":4,"notice":5,"info":6,"debug":7}
LOG_MAX_BYTES=1048576
_LOGLEVEL_CACHE={}
def plugin_loglevel(cfg):
    """LoxBerry-Loglevel des Plugins ermitteln (einmal je Prozess gecacht)."""
    cp=cfg.get("_config_path","")
    if cp in _LOGLEVEL_CACHE:return _LOGLEVEL_CACHE[cp]
    lvl=6
    try:
        folder=os.path.basename(os.path.dirname(cp)) if cp else "firetv"
        db=load_json(os.path.join(plugin_root(),"data","system","plugindatabase.json"))
        for p in db.get("plugins",[]):
            if str(p.get("folder",""))==folder or str(p.get("name",""))=="firetv":lvl=int(p.get("loglevel",6));break
    except Exception:pass
    _LOGLEVEL_CACHE[cp]=lvl;return lvl
def rotate_log(path):
    try:
        if os.path.getsize(path)>LOG_MAX_BYTES:
            os.replace(path,path+".1")
            try:os.chmod(path+".1",0o600)
            except Exception:pass
    except OSError:pass
def debug_log(cfg,level,msg):
    try:
        if LOG_LEVELS.get(str(level).lower(),6)>plugin_loglevel(cfg):return
        p=log_path(cfg);os.makedirs(os.path.dirname(p),exist_ok=True);rotate_log(p)
        with open(p,"a",encoding="utf-8") as f:f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{str(level).upper()}] {msg}\n")
        try:os.chmod(p,0o600)
        except Exception:pass
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
def _recv_exact(s,n):
    b=b""
    while len(b)<n:
        x=s.recv(n-len(b))
        if not x:raise ConnectionError("MQTT Verbindung geschlossen")
        b+=x
    return b
class MqttSession:
    """Eine MQTT-Verbindung für beliebig viele Publishes (statt einer Verbindung je Topic)."""
    def __init__(self,cfg):self.cfg=cfg;self.s=None;self.failed=False
    def _open(self):
        mc=mqtt_connection_config(self.cfg);cid=f"lb-firetv-pub-{os.getpid()}";flags=2;pl=_mstr(cid)
        if mc.get("username"):
            flags|=0x80;pl+=_mstr(mc["username"])
            if mc.get("password") is not None:flags|=0x40;pl+=_mstr(mc.get("password",""))
        vh=_mstr("MQTT")+bytes([4,flags])+struct.pack("!H",30)
        s=socket.create_connection((mc["host"],int(mc["port"])),timeout=4);s.settimeout(4)
        s.sendall(bytes([0x10])+_enc_len(len(vh)+len(pl))+vh+pl)
        h=_recv_exact(s,1)[0];rem=0;mul=1
        for _ in range(4):
            d=_recv_exact(s,1)[0];rem+=(d&127)*mul
            if not d&128:break
            mul*=128
        body=_recv_exact(s,rem) if rem else b""
        if h>>4!=2 or len(body)<2 or body[1]!=0:
            try:s.close()
            except Exception:pass
            raise RuntimeError(f"MQTT CONNACK abgelehnt (Code {body[1] if len(body)>1 else '?'})")
        self.s=s
    def publish(self,topic,payload,retain=False):
        if not self.cfg.get("mqtt",{}).get("enabled",True) or self.failed:return False
        try:
            if self.s is None:self._open()
            body=_mstr(topic)+str(payload).encode()
            self.s.sendall(bytes([0x31 if retain else 0x30])+_enc_len(len(body))+body);return True
        except Exception as e:
            self.failed=True;self.close()
            debug_log(self.cfg,"warning",f"MQTT publish fehlgeschlagen: {e}");return False
    def close(self):
        s,self.s=self.s,None
        if not s:return
        try:
            s.sendall(b"\xe0\x00");s.shutdown(socket.SHUT_WR)
        except Exception:pass
        try:s.close()
        except Exception:pass
    def __enter__(self):return self
    def __exit__(self,*_):self.close();return False
def mqtt_publish(cfg,topic,payload,retain=False):
    with MqttSession(cfg) as m:return m.publish(topic,payload,retain)
def mqtt_event(cfg,suffix,data,retain=False):
    payload=data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,separators=(",",":"))
    return mqtt_publish(cfg,base_topic(cfg)+"/"+suffix,payload,retain)

def resolve_host(value):
    """Hostnamen zu einer IP auflösen; IP-Adressen werden unverändert zurückgegeben."""
    v=str(value).strip()
    try:return str(ipaddress.ip_address(v))
    except ValueError:pass
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,253}",v):raise ValueError("Ungültige Fire-TV-Adresse")
    try:infos=socket.getaddrinfo(v,None,type=socket.SOCK_STREAM)
    except OSError:raise ValueError(f"Hostname konnte nicht aufgelöst werden: {v}")
    for fam in (socket.AF_INET,socket.AF_INET6):
        for i in infos:
            if i[0]==fam:return i[4][0]
    raise ValueError(f"Hostname konnte nicht aufgelöst werden: {v}")
def validate_adb_target(cfg,ip,port):
    try:addr=ipaddress.ip_address(resolve_host(ip))
    except ValueError as e:raise ValueError(str(e) if "aufgelöst" in str(e) or "Ungültige Fire-TV-Adresse" in str(e) else "Ungültige Fire-TV-IP-Adresse")
    if addr.is_multicast or addr.is_unspecified:raise ValueError("Unsichere Fire-TV-IP-Adresse")
    if cfg.get("security",{}).get("private_adb_only",True) and not (addr.is_private or addr.is_loopback or addr.is_link_local):
        raise ValueError("ADB-Ziel außerhalb des privaten Netzes blockiert")
    try:p=int(port)
    except Exception:raise ValueError("Ungültiger ADB-Port")
    if p<1 or p>65535:raise ValueError("Ungültiger ADB-Port")
    return str(addr),p

class FireTV:
    def __init__(self,cfg,device):
        self.cfg=cfg;self.device=device;self.ip,self.port=validate_adb_target(cfg,device.get("ip",""),device.get("port",5555));self.target=f"{self.ip}:{self.port}";self.timeout=max(2,min(30,int(cfg.get("adb_timeout",8))));self._conn=None
    def _run(self,args):
        try:p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=self.timeout,check=False)
        except FileNotFoundError:raise RuntimeError("ADB ist nicht installiert")
        except subprocess.TimeoutExpired:raise RuntimeError("ADB Zeitüberschreitung")
        return p.returncode,(p.stdout or "").strip()
    def _state(self):
        rc,out=self._run(["adb","-s",self.target,"get-state"]);low=out.lower().strip()
        if "unauthorized" in low:return "unauthorized",out
        if "offline" in low:return "offline",out
        if low=="device":return "device",out
        _,devs=self._run(["adb","devices"])
        for line in devs.splitlines():
            if line.startswith(self.target+"\t"):return line.split("\t",1)[1].strip().lower(),devs
        return "disconnected",out or devs
    def connect(self,force=False):
        """Verbindungszustand ermitteln. Ergebnis wird je Instanz gecacht, damit ein
        status()-Aufruf nicht für jedes Shell-Kommando erneut adb connect/get-state startet."""
        if self._conn is not None and not force and self._conn.get("ok"):return self._conn
        _,out=self._run(["adb","connect",self.target]);state,detail=self._state();msg=(out+" | "+detail).strip(" |")
        self._conn={"ok":state=="device","authorized":state=="device","state":state,"message":msg}
        return self._conn
    def reconnect(self):
        self._conn=None
        try:self._run(["adb","disconnect",self.target])
        except Exception:pass
        time.sleep(.35);_,out=self._run(["adb","connect",self.target]);time.sleep(.35);state,detail=self._state();debug_log(self.cfg,"info",f"ADB reconnect {self.target}: {state}");msg=(out+" | "+detail).strip(" |")
        if state=="unauthorized":return {"ok":False,"authorized":False,"state":state,"message":"Bestätigung am Fire TV erforderlich","adb_output":msg}
        if state=="offline":return {"ok":False,"authorized":False,"state":state,"message":"ADB-Gerät ist offline","adb_output":msg}
        if state!="device":return {"ok":False,"authorized":False,"state":state,"message":"ADB-Verbindung konnte nicht hergestellt werden","adb_output":msg}
        return {"ok":True,"authorized":True,"state":"device","message":"ADB autorisiert und verbunden","adb_output":msg}
    def shell(self,*args):
        c=self.connect()
        if not c.get("authorized"):
            if c.get("state")=="unauthorized":raise RuntimeError("ADB nicht autorisiert – Verbindung am Fire TV bestätigen")
            raise RuntimeError(c.get("message") or "ADB nicht verbunden")
        rc,out=self._run(["adb","-s",self.target,"shell",*map(str,args)]);low=out.lower()
        if "unauthorized" in low:self._conn=None;raise RuntimeError("ADB nicht autorisiert – Verbindung am Fire TV bestätigen")
        if "no devices" in low or "offline" in low or "not found" in low:self._conn=None;raise RuntimeError(out)
        return out
    def key(self,key):
        k=str(key).lower();code=KEYS.get(k)
        if code is None:raise ValueError("Unbekannte Taste: "+k)
        self.shell("input","keyevent",str(code));return {"ok":True,"action":k}
    def volume(self,direction):
        d=str(direction).lower();adj={"volumeup":"raise","volumedown":"lower","mute":"toggle"}.get(d)
        if not adj:raise ValueError("Ungültige Lautstärkeaktion")
        for cmd in (("cmd","media_session","volume","--stream","3","--adj",adj),("media","volume","--stream","3","--adj",adj)):
            try:
                out=self.shell(*cmd)
                if "unknown" not in out.lower() and "error" not in out.lower():return {"ok":True,"action":d,"method":"media_session","output":out[-300:]}
            except Exception:pass
        self.key(d);return {"ok":True,"action":d,"method":"keyevent-fallback"}
    def _cec_sequence(self,name,steps):
        debug_log(self.cfg,"info",f"CEC {name} für {self.device.get('name',self.target)} gestartet");done=[]
        for key,delay in steps:
            if delay:time.sleep(delay)
            self.key(key);done.append(key)
        return done
    def tv_on(self):
        method=str(self.device.get("cec_on_method","home") or "home").lower()
        try:delay=float(self.device.get("cec_on_delay",0.8))
        except Exception:delay=.8
        delay=min(max(delay,.1),5.0);methods={"home":[("home",0)],"home_repeat":[("home",0),("home",delay)],"wakeup_home":[("wakeup",0),("home",delay)],"power_home":[("power",0),("home",delay)],"auto":[("wakeup",0),("home",delay),("home",delay)]}
        if method not in methods:method="home"
        steps=self._cec_sequence("TV EIN/"+method,methods[method]);return {"ok":True,"action":"tvon","method":method,"delay":delay,"steps":steps}
    def tv_off(self):
        method=str(self.device.get("cec_off_method","sleep") or "sleep").lower()
        try:delay=float(self.device.get("cec_on_delay",0.8))
        except Exception:delay=.8
        delay=min(max(delay,.1),5.0)
        methods={"sleep":[("sleep",0)],"sleep_repeat":[("sleep",0),("sleep",delay)],"power":[("power",0)]}
        if method not in methods:method="sleep"
        steps=self._cec_sequence("TV AUS/"+method,methods[method])
        return {"ok":True,"action":"tvoff","method":method,"delay":delay,"steps":steps}
    def cec_diagnostics(self):
        checks={}
        for name,cmd in {"hdmi_control_enabled":("settings","get","global","hdmi_control_enabled"),"cec_control_enabled":("settings","get","global","cec_control_enabled"),"hdmi_cec_enabled":("settings","get","global","hdmi_cec_enabled"),"amazon_equipment_control":("settings","get","secure","equipment_control_enabled"),"model":("getprop","ro.product.model"),"device":("getprop","ro.product.device"),"fireos_build":("getprop","ro.build.version.incremental")}.items():
            try:checks[name]=self.shell(*cmd).strip()
            except Exception as e:checks[name]="error: "+str(e)
        return {"ok":True,"action":"cecdiag","on_method":self.device.get("cec_on_method","home"),"on_delay":self.device.get("cec_on_delay",.8),"off_method":self.device.get("cec_off_method","sleep"),"checks":checks}
    def launch(self,package):
        package=APP_PRESETS.get(str(package).lower(),package);package=str(package).strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,200}",package):raise ValueError("Ungültiger Paketname")
        out=self.shell("monkey","-p",package,"-c","android.intent.category.LAUNCHER","1");return {"ok":True,"package":package,"output":out[-500:]}
    def status(self):
        r={"name":self.device.get("name","Fire TV"),"ip":self.ip,"port":self.port,"id":slug(self.device.get("id") or self.device.get("name") or self.ip),"online":False,"authorized":False}
        c=self.connect();r["adb_message"]=c["message"];r["adb_state"]=c.get("state");r["authorized"]=bool(c["authorized"])
        if not c["ok"]:return r
        try:
            r["online"]=True;r["model"]=self.shell("getprop","ro.product.model").strip();r["manufacturer"]=self.shell("getprop","ro.product.manufacturer").strip();r["android"]=self.shell("getprop","ro.build.version.release").strip();r["build"]=self.shell("getprop","ro.build.version.incremental").strip();power=self.shell("dumpsys","power");r["awake"]=screen_from_power(power,self.cfg.get("screen_detect","auto"));win=self.shell("dumpsys","window","windows");m=re.search(r"mCurrentFocus=.*?\s([A-Za-z0-9._]+)/(?:[A-Za-z0-9._$]+)",win)
            if not m:
                act=self.shell("dumpsys","activity","activities");m=re.search(r"mResumedActivity:.*?\s([A-Za-z0-9._]+)/",act)
            r["app"]=m.group(1) if m else ""
        except Exception as e:r["error"]=str(e)
        return r
    def screen(self):
        """Nur den Bildschirmzustand abfragen - ein einziger adb-Aufruf,
        deutlich schneller als der vollstaendige status()."""
        power=self.shell("dumpsys","power")
        return screen_from_power(power,self.cfg.get("screen_detect","auto"))
    def power_dump(self):
        """Rohdaten zur Bildschirmerkennung - fuer die Diagnose in der Oberflaeche."""
        power=self.shell("dumpsys","power")
        keys=("mWakefulness","Display Power","mHoldingDisplaySuspendBlocker","mHoldingWakeLockSuspendBlocker",
              "mScreenOn","mScreenBrightness","Dream","mDreaming","mIsPowered","mWakeLockSummary","mUserActivitySummary")
        hits=[l.strip() for l in power.splitlines() if any(k.lower() in l.lower() for k in keys)]
        cur=str(self.cfg.get("screen_detect","auto"))
        return {"ok":True,"action":"powerdump","method":cur,"awake":screen_from_power(power,cur),
                "values":screen_values(power),
                "methods":[{"id":k,"label":l,"awake":screen_from_power(power,k)} for k,l in SCREEN_METHODS],
                "lines":hits[:60]}
    def list_apps(self):
        out=self.shell("pm","list","packages");return sorted({x.split(":",1)[1].strip() for x in out.splitlines() if x.startswith("package:")})
    def command(self,action,value=None):
        a=str(action).strip().lower()
        if a=="status":return self.status()
        if a in ("reconnect","adb_reconnect"):return self.reconnect()
        if a in ("cecdiag","cec_diagnostics"):return self.cec_diagnostics()
        if a in ("powerdump","screendiag"):return self.power_dump()
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
            v=str(value)
            if len(v)>512 or any(ord(ch)<32 or ord(ch)==127 for ch in v):raise ValueError("Ungültiger Text")
            # adb shell übergibt die Argumente an die Shell des Fire TV. Der Text muss
            # deshalb zwingend gequotet werden, sonst sind ";", "|" oder "$(...)"
            # ausführbare Befehle auf dem Gerät.
            self.shell("input","text",shlex.quote(v.replace(" ","%s")));return {"ok":True,"action":"text"}
        if a=="apps":return {"ok":True,"apps":self.list_apps()}
        raise ValueError("Unbekannter Befehl: "+a)

def find_device(cfg,ident):
    ident=str(ident)
    if len(ident)>128 or re.search(r"[\r\n\x00/]",ident):raise KeyError("Ungültige Geräte-ID")
    for d in cfg.get("devices",[]):
        if ident in (str(d.get("id","")),slug(d.get("id","")),slug(d.get("name","")),str(d.get("ip",""))):return d
    raise KeyError("Fire TV nicht gefunden: "+ident)
def publish_status(cfg,st):
    b=base_topic(cfg)+"/"+st["id"];ret=bool(cfg.get("mqtt",{}).get("retain_state",True))
    with MqttSession(cfg) as m:
        m.publish(b+"/online","1" if st.get("online") else "0",ret)
        m.publish(b+"/authorized","1" if st.get("authorized") else "0",ret)
        m.publish(b+"/awake","1" if st.get("awake") else "0",ret)
        m.publish(b+"/display","ON" if st.get("awake") else "OFF",ret)
        m.publish(b+"/app",st.get("app",""),ret)
        m.publish(b+"/state",json.dumps(st,ensure_ascii=False,separators=(",",":")),ret)
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
