# Changelog

## 0.2.9
- TV-Einschaltlogik über Fire-TV-Wakeup plus Home für HDMI-CEC/One-Touch-Play ergänzt
- TV-Ausschaltlogik über Fire-TV-Standby/CEC ergänzt
- MQTT `on/1/true` steuert jetzt den TV-Einschaltpfad, `off/0/false` den TV-Ausschaltpfad
- Lautstärke versucht zuerst Android Media-Session/System-Volume und fällt danach auf Keyevents zurück
- CEC-Einstellung wird soweit verfügbar im Gerätestatus mit ausgegeben
- Bestehender `awake` MQTT-Status bleibt für Loxone-Automationen verfügbar

## 0.2.8
- Automatische Fire-TV-Suche im lokalen IPv4-Netz hinzugefügt
- Scan prüft ADB auf TCP-Port 5555 und begrenzt sich auf maximal 254 Hosts
- Gefundene Geräte können direkt aus der Suche übernommen werden
- Bereits konfigurierte Geräte werden erkannt und markiert
- ADB-Autorisierungsstatus wird bei gefundenen Geräten angezeigt

## 0.2.7
- Konfiguration wird vor einem Plugin-Update gesichert und danach wiederhergestellt
- Upgrade-Pfad schützt `config.json` vor Überschreiben
- Modernes Fire-TV-Dashboard aus 0.2.6 bleibt erhalten
- Python-3.13-kompatible CGI-Verarbeitung aus 0.2.5 bleibt erhalten

## 0.2.6
- Dashboard optisch modernisiert
- Gerätekarten, Statusanzeige, D-Pad und Mobile-Ansicht verbessert

## 0.2.5
- Veraltetes Python-`cgi`-Modul entfernt
- Weboberfläche für aktuelle Python-Versionen kompatibel gemacht

## 0.2.4
- Postinstall-Pfade für `webfrontend/htmlauth` korrigiert

## 0.2.3
- Ursprüngliche LoxBerry-Plugin-Identität `Marco Düthorn / duett86@web.de` wiederhergestellt
- CGI-Pfade robust ermittelt, auch wenn `LBHOMEDIR` in der Webserver-Umgebung fehlt
- CGI-Dateirechte im Postinstall sauber gesetzt
- Fire-TV-Iconset vollständig im Paket enthalten
- ADB-Abhängigkeit weiterhin über `dpkg/apt`

## 0.2.2
- CI- und Paketierungsprüfungen verbessert
- Hardcodierte LoxBerry-Basisverzeichnis-Fallbacks entfernt

## 0.1.0
- Erste Version
- Mehrgeräte-Unterstützung
- Netzwerk-ADB
- Fire-TV-Statusabfrage
- Fernbedienungsbefehle
- App-Start
- LoxBerry-MQTT
- Watchdog
- Weboberfläche
