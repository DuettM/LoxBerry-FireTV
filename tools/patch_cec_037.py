#!/usr/bin/env python3
from pathlib import Path


def replace_once(path, old, new):
    p=Path(path); s=p.read_text(encoding='utf-8')
    if old not in s:
        raise SystemExit(f'Pattern not found in {path}: {old[:100]!r}')
    p.write_text(s.replace(old,new,1),encoding='utf-8')

# Version
replace_once('plugin.cfg','VERSION=0.3.6','VERSION=0.3.7')

# Core CEC handling
p=Path('bin/firetv.py'); s=p.read_text(encoding='utf-8')
old='''    def tv_on(self):\n        self.key("wakeup");time.sleep(0.35);self.key("home")\n        return {"ok":True,"action":"tvon","method":"firetv-one-touch-play","note":"Fire TV Gerätesteuerung/HDMI-CEC muss aktiviert sein."}\n    def tv_off(self):\n        self.key("sleep")\n        return {"ok":True,"action":"tvoff","method":"firetv-standby-cec","note":"CEC-Standby hängt von Fire TV und TV-Gerätesteuerung ab."}\n'''
new='''    def _cec_sequence(self,name,steps):\n        debug_log(self.cfg,"info",f"CEC {name} für {self.device.get('name',self.target)} gestartet")\n        done=[]\n        for key,delay in steps:\n            if delay: time.sleep(delay)\n            self.key(key);done.append(key)\n            debug_log(self.cfg,"debug",f"CEC {name}: ADB keyevent {key} gesendet")\n        return done\n    def tv_on(self):\n        method=str(self.device.get("cec_on_method","home") or "home").lower()\n        methods={\n            "home":[("home",0)],\n            "home_repeat":[("home",0),("home",0.8)],\n            "wakeup_home":[("wakeup",0),("home",0.8)],\n            "power_home":[("power",0),("home",1.0)],\n            "auto":[("home",0),("wakeup",1.0),("home",0.6),("home",0.8)],\n        }\n        if method not in methods: method="home"\n        steps=self._cec_sequence("TV EIN/"+method,methods[method])\n        return {"ok":True,"action":"tvon","method":method,"steps":steps,"note":"ADB-Keyevents können je nach Fire-TV-Modell anders als die physische Fernbedienung auf HDMI-CEC wirken."}\n    def tv_off(self):\n        method=str(self.device.get("cec_off_method","sleep") or "sleep").lower()\n        if method not in ("sleep","power"):method="sleep"\n        steps=self._cec_sequence("TV AUS/"+method,[(method,0)])\n        return {"ok":True,"action":"tvoff","method":method,"steps":steps,"note":"CEC-Standby hängt von Fire TV und TV-Gerätesteuerung ab."}\n    def cec_diagnostics(self):\n        checks={}\n        commands={\n            "hdmi_control_enabled":("settings","get","global","hdmi_control_enabled"),\n            "cec_control_enabled":("settings","get","global","cec_control_enabled"),\n            "hdmi_cec_enabled":("settings","get","global","hdmi_cec_enabled"),\n            "amazon_equipment_control":("settings","get","secure","equipment_control_enabled"),\n            "model":("getprop","ro.product.model"),\n            "device":("getprop","ro.product.device"),\n            "fireos_build":("getprop","ro.build.version.incremental"),\n        }\n        for name,cmd in commands.items():\n            try:checks[name]=self.shell(*cmd).strip()\n            except Exception as e:checks[name]="error: "+str(e)\n        debug_log(self.cfg,"info",f"CEC Diagnose {self.device.get('name',self.target)}: {json.dumps(checks,ensure_ascii=False)}")\n        return {"ok":True,"action":"cecdiag","on_method":self.device.get("cec_on_method","home"),"off_method":self.device.get("cec_off_method","sleep"),"checks":checks}\n'''
if old not in s: raise SystemExit('tv_on block not found')
s=s.replace(old,new,1)
s=s.replace('''        if a=="status":return self.status()\n''','''        if a=="status":return self.status()\n        if a in ("cecdiag","cec_diagnostics"):return self.cec_diagnostics()\n''',1)
p.write_text(s,encoding='utf-8')

# Config UI / persistence
p=Path('webfrontend/htmlauth/config.cgi'); s=p.read_text(encoding='utf-8')
s=s.replace("return '0.3.5'","return '0.3.7'",1)
s=s.replace("c.setdefault('devices',[]).append({'id':ident,'name':name,'ip':ip,'port':port,'enabled':True});save(c);notice='Gerät hinzugefügt.'",
'''c.setdefault('devices',[]).append({'id':ident,'name':name,'ip':ip,'port':port,'enabled':True,'cec_on_method':'home','cec_off_method':'sleep'});save(c);notice='Gerät hinzugefügt.' ''',1)
needle="""  elif act=='delete':\n   ident=f.get('id','') or ''\n   c['devices']=[d for d in c.get('devices',[]) if str(d.get('id',''))!=ident];save(c);notice='Gerät gelöscht.'\n"""
insert="""  elif act=='save_device_cec':\n   ident=f.get('id','') or '';onm=f.get('cec_on_method','home');offm=f.get('cec_off_method','sleep')\n   if onm not in ('home','home_repeat','wakeup_home','power_home','auto'):raise ValueError('Ungültige TV-EIN-Methode.')\n   if offm not in ('sleep','power'):raise ValueError('Ungültige TV-AUS-Methode.')\n   found=False\n   for d in c.get('devices',[]):\n    if str(d.get('id',''))==ident:d['cec_on_method']=onm;d['cec_off_method']=offm;found=True;break\n   if not found:raise ValueError('Gerät nicht gefunden.')\n   save(c);notice='CEC-Einstellungen gespeichert.'\n  elif act=='delete':\n   ident=f.get('id','') or ''\n   c['devices']=[d for d in c.get('devices',[]) if str(d.get('id',''))!=ident];save(c);notice='Gerät gelöscht.'\n"""
if needle not in s: raise SystemExit('delete block not found')
s=s.replace(needle,insert,1)
s=s.replace('.field input{width:100%;height:38px;', '.field input,.field select{width:100%;height:38px;',1)
old_line=""" ident=html.escape(str(d.get('id','')),quote=True);print('<div class=\"device\"><div><b>%s</b><br><span class=\"muted\">%s:%s · %s</span></div><form method=\"post\">%s<input type=\"hidden\" name=\"form_action\" value=\"delete\"><input type=\"hidden\" name=\"id\" value=\"%s\"><button class=\"btn red\">Löschen</button></form></div>'%(html.escape(str(d.get('name',''))),html.escape(str(d.get('ip',''))),d.get('port',5555),html.escape(str(d.get('id',''))),h,ident))\n"""
new_line=""" ident=html.escape(str(d.get('id','')),quote=True);onm=str(d.get('cec_on_method','home'));offm=str(d.get('cec_off_method','sleep'))\n opts=[('home','Home'),('home_repeat','Home zweimal'),('wakeup_home','Wakeup + Home'),('power_home','Power + Home'),('auto','Automatik')];onopts=''.join('<option value=\"%s\" %s>%s</option>'%(v,'selected' if onm==v else '',t) for v,t in opts);offopts=''.join('<option value=\"%s\" %s>%s</option>'%(v,'selected' if offm==v else '',t) for v,t in [('sleep','Sleep / Standby'),('power','Power-Taste')])\n print('<div class=\"device\"><div><b>%s</b><br><span class=\"muted\">%s:%s · %s</span><form method=\"post\" style=\"margin-top:8px\">%s<input type=\"hidden\" name=\"form_action\" value=\"save_device_cec\"><input type=\"hidden\" name=\"id\" value=\"%s\"><label class=\"muted\">TV EIN über </label><select name=\"cec_on_method\">%s</select> <label class=\"muted\">TV AUS über </label><select name=\"cec_off_method\">%s</select> <button class=\"btn green\">CEC speichern</button></form></div><form method=\"post\">%s<input type=\"hidden\" name=\"form_action\" value=\"delete\"><input type=\"hidden\" name=\"id\" value=\"%s\"><button class=\"btn red\">Löschen</button></form></div>'%(html.escape(str(d.get('name',''))),html.escape(str(d.get('ip',''))),d.get('port',5555),html.escape(str(d.get('id',''))),h,ident,onopts,offopts,h,ident))\n"""
if old_line not in s: raise SystemExit('device render line not found')
s=s.replace(old_line,new_line,1)
p.write_text(s,encoding='utf-8')

# Changelog
p=Path('CHANGELOG.md'); s=p.read_text(encoding='utf-8')
entry='''# Changelog\n\n## 0.3.7\n- HDMI-CEC/TV-Einschalten pro Fire TV konfigurierbar gemacht\n- Neue TV-EIN-Methoden: Home, Home zweimal, Wakeup + Home, Power + Home und Automatik\n- TV-AUS-Methode pro Gerät zwischen Sleep/Standby und Power wählbar\n- CEC-Aktionen werden mit Methode und gesendeten ADB-Keyevents geloggt\n- Neue CEC-Diagnoseaktion `cecdiag` liest verfügbare HDMI-/CEC-Einstellungen und Fire-TV-Geräteinformationen aus\n- Neue Geräte verwenden standardmäßig `Home`, da diese Methode bei physischer Fire-TV-Fernbedienung typischerweise One-Touch-Play auslöst\n\n'''
if not s.startswith('# Changelog\n'): raise SystemExit('bad changelog')
s=entry+s[len('# Changelog\n\n'):]
p.write_text(s,encoding='utf-8')

# README short note
p=Path('README.md'); s=p.read_text(encoding='utf-8')
marker='- Wake / Standby / Reboot\n'
if marker in s and 'CEC-Einschaltmethode' not in s:
    s=s.replace(marker,marker+'- pro Gerät wählbare CEC-Einschaltmethode (Home, Wakeup + Home, Power + Home, Automatik)\n',1)
p.write_text(s,encoding='utf-8')

print('CEC v0.3.7 patch applied')
