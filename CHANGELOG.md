# Changelog

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
