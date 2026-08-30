#!/usr/bin/env python3
import argparse,json,os,signal,socket,struct,sys,time,fcntl,importlib.util,random
RUN=True
def stop(*_):
 global RUN;RUN=False
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
def enc_len(n):
 o=b''
 while True:
  d=n%128;n//=128
  if n:d|=128
  o+=bytes([d])
  if not n:return o
def mstr(v):
 b=str(v).encode();return struct.pack('!H',len(b))+b
def recv_exact(s,n):
 b=b''
 while len(b)<n:
  x=s.recv(n-len(b))
  if not x:raise ConnectionError('MQTT Verbindung geschlossen')
  b+=x
 return b
def recv_packet(s):
 f=recv_exact(s,1)[0];mul=1;rem=0
 for _ in range(4):
  d=recv_exact(s,1)[0];rem+=(d&127)*mul
  if not d&128:break
  mul*=128
 return f,recv_exact(s,rem) if rem else b''
class Client:
 def __init__(self,c):self.c=c;self.s=None;self.pid=1
 def connect(self):
  cid='lb-firetv-rx-%04x'%random.randint(0,65535);flags=2;pl=mstr(cid)
  if self.c.get('username'):
   flags|=0x80;pl+=mstr(self.c['username'])
   if self.c.get('password') is not None:flags|=0x40;pl+=mstr(self.c.get('password',''))
  vh=mstr('MQTT')+bytes([4,flags])+struct.pack('!H',30);self.s=socket.create_connection((self.c.get('host','127.0.0.1'),int(self.c.get('port',1883))),timeout=10);self.s.settimeout(5);self.s.sendall(bytes([0x10])+enc_len(len(vh)+len(pl))+vh+pl);h,b=recv_packet(self.s)
  if h>>4!=2 or len(b)<2 or b[1]!=0:raise RuntimeError('MQTT Login fehlgeschlagen')
 def subscribe(self,t):
  self.pid=(self.pid%65535)+1;body=struct.pack('!H',self.pid)+mstr(t)+bytes([0]);self.s.sendall(bytes([0x82])+enc_len(len(body))+body);recv_packet(self.s)
 def publish(self,t,p,retain=False):
  body=mstr(t)+str(p).encode();self.s.sendall(bytes([0x31 if retain else 0x30])+enc_len(len(body))+body)
 def ping(self):self.s.sendall(b'\xc0\x00')
def load_core(p):
 spec=importlib.util.spec_from_file_location('firetv_core',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def payload(raw):
 t=raw.decode('utf-8','replace').strip()
 try:
  o=json.loads(t)
  if isinstance(o,dict):return str(o.get('action',o.get('cmd',''))),o.get('value',o.get('package'))
 except Exception:pass
 if ':' in t:return tuple(x.strip() for x in t.split(':',1))
 return t,None
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--core',required=True);a=ap.parse_args();lock=open(os.path.join(os.path.dirname(a.config),'mqtt_listener.lock'),'w')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:return 0
 core=load_core(a.core);backoff=2
 while RUN:
  try:
   cfg=json.load(open(a.config,encoding='utf-8'));cfg['_config_path']=a.config
   if not cfg.get('mqtt',{}).get('enabled',True) or not cfg.get('mqtt',{}).get('listen_enabled',True):time.sleep(10);continue
   c=Client(core.mqtt_connection_config(cfg));c.connect();base=core.base_topic(cfg);c.subscribe(base+'/+/set');c.subscribe(base+'/+/command');c.publish(base+'/availability','online',True);mtime=os.path.getmtime(a.config);mm=core.mqtt_source_mtime(cfg);last=time.time();backoff=2
   while RUN:
    if os.path.getmtime(a.config)!=mtime or core.mqtt_source_mtime(cfg)!=mm:raise RuntimeError('Konfiguration geändert')
    try:h,b=recv_packet(c.s)
    except socket.timeout:
     if time.time()-last>20:c.ping();last=time.time()
     continue
    if h>>4!=3 or len(b)<2:continue
    n=struct.unpack('!H',b[:2])[0];topic=b[2:2+n].decode();pos=2+n
    if ((h>>1)&3):pos+=2
    rel=topic[len(base)+1:].split('/') if topic.startswith(base+'/') else []
    if len(rel)!=2 or rel[1] not in ('set','command'):continue
    action,value=payload(b[pos:]);action={'1':'tvon','true':'tvon','on':'tvon','0':'tvoff','false':'tvoff','off':'tvoff','pause':'playpause','play':'playpause'}.get(action.lower(),action.lower());d=core.find_device(cfg,rel[0]);r=core.FireTV(cfg,d).command(action,value);core.mqtt_event(cfg,'event',{'device':rel[0],'action':action,'result':r},False)
    try:core.publish_status(cfg,core.FireTV(cfg,d).status())
    except Exception:pass
  except Exception as e:
   try:core.debug_log(cfg,'warning',f'MQTT reconnect: {e}')
   except Exception:pass
   time.sleep(backoff);backoff=min(60,backoff*2)
 return 0
if __name__=='__main__':sys.exit(main())
