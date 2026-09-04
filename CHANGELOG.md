# Changelog

## 0.3.10
- Dashboard-Powerbuttons korrigiert: `Einschalten` verwendet jetzt `tvon`, `Ausschalten/Standby` verwendet `tvoff`
- Gerätespezifische TV-EIN-Methode wird dadurch auch im Dashboard respektiert, z. B. `Home 2×` mit einstellbarer Verzögerung
- Gerätespezifische TV-AUS-Methode wird auch im Dashboard verwendet
- MQTT-Core um fehlende Quelländerungsprüfung `mqtt_source_mtime()` ergänzt, damit der Listener bei Änderungen am LoxBerry-MQTT-Setup sauber neu verbindet
- ADB-Ziele werden validiert; standardmäßig sind nur lokale/private Ziele erlaubt
- ADB-Portvalidierung ergänzt
- Paketnamen, Geräte-IDs und Texteingaben weiter eingeschränkt und validiert
- MQTT-Befehlstoken als optionale zusätzliche Absicherung vorbereitet/ergänzt, ohne bestehende Installationen standardmäßig zu brechen
- Security-Härtungen für Web/API und Konfiguration erweitert
- README, Lizenz-, Security- und rechtliche Hinweise aktualisiert

## 0.3.9
- Neues MQTT-Statustopic `firetv/<id>/display`
- `display` liefert lesbar `ON` bzw. `OFF`
- Bestehendes `awake` mit `1` / `0` bleibt für vorhandene Automationen unverändert erhalten

## 0.3.8
- ADB-Verbindungsstatus robuster ausgewertet (`device`, `unauthorized`, `offline`, `disconnected`)
- Gezieltes ADB-Reconnect pro Fire TV ergänzt, ohne globalen `adb kill-server`
- Verständliche Hinweise ergänzt, wenn die Autorisierungsabfrage am Fire TV bestätigt werden muss
- Einstellbare Verzögerung für TV-EIN-Sequenzen ergänzt
- `Home 2×`, `Wakeup + Home`, `Power + Home` und Automatik verwenden die konfigurierbare Verzögerung
- Gerätesuche zeigt ADB-Autorisierungs- und Offline-Status deutlicher an

## 0.3.7
- HDMI-CEC/TV-Einschalten pro Fire TV konfigurierbar gemacht
- Neue TV-EIN-Methoden: Home, Home zweimal, Wakeup + Home, Power + Home und Automatik
- TV-AUS-Methode pro Gerät zwischen Sleep/Standby und Power wählbar
- CEC-Aktionen werden mit Methode und gesendeten ADB-Keyevents geloggt
- Neue CEC-Diagnoseaktion `cecdiag` liest verfügbare HDMI-/CEC-Einstellungen und Fire-TV-Geräteinformationen aus
- Neue Geräte verwenden standardmäßig `Home`, da diese Methode bei physischer Fire-TV-Fernbedienung typischerweise One-Touch-Play auslöst

## 0.3.6
- Ed25519-Vertrauensschlüssel für sichere Updates rotiert
- Neuer öffentlicher Update-Schlüssel im Plugin und Secure-Updater hinterlegt
- Secure-Updater auf Version 0.3.6 aktualisiert
- Einmaliges manuelles Update auf 0.3.6 erforderlich, weil der bisherige private Signierschlüssel nicht mehr verfügbar ist
- Ab 0.3.6 können zukünftige Releases wieder mit der neuen Vertrauenskette signiert und geprüft werden

## 0.3.5
- Einstieg auf nativen LoxBerry-Webrahmen mit `LoxBerry::Web::lbheader()` und `lbfooter()` umgestellt
- Echte LoxBerry-Navigationssymbole erscheinen wieder im oberen Seitenbereich wie bei nativen LoxBerry-Plugins
- Eigenen nachgebauten Zurück-Button aus dem Fire-TV-Menü entfernt
- Bestehendes Fire-TV-Dashboard nach `dashboard.cgi` ausgelagert und in den nativen LoxBerry-Rahmen eingebettet
- Einstellungen, Gerätesuche, Security Center und Debug für Same-Origin-Einbettung freigegeben
- Frame-Schutz von `DENY`/`frame-ancestors 'none'` auf `SAMEORIGIN`/`frame-ancestors 'self'` korrigiert
- Installer und Upgrader um `dashboard.cgi` ergänzt
- CI- und Paket-Workflow an Perl-`index.cgi` plus Python-`dashboard.cgi` angepasst

## 0.3.4
- Zurück-zum-LoxBerry-Eintrag im selbstgebauten Menü zunächst auf kompaktes Home-Icon reduziert
- Mobile Navigation ebenfalls auf Icon-Variante umgestellt

## 0.3.3
- Feste linke LoxBerry-Navigation auf Dashboard, Einstellungen, Gerätesuche, Security Center und Debug vereinheitlicht
- „Zurück zu LoxBerry“ ist auf Desktop und Mobilansicht überall erreichbar
- Debug-Seite vollständig erneuert und in das LoxBerry-Design integriert
- Debug-Seite zeigt ADB-, Python-, MQTT-, Watchdog- und Pluginstatus
- Aktuell in LoxBerry gesetzter Plugin-Loglevel wird auf der Debug-Seite angezeigt
- Geschützter Button zum Leeren des Fire-TV-Logs ergänzt
- LoxBerry-Loglevel-Auswahl über `CUSTOM_LOGLEVELS=true` in der Pluginverwaltung aktiviert
- Gerätesuche auf Netzen größer als /24 korrigiert: gescannt wird das /24 des tatsächlichen LoxBerry-Interfaces

## 0.3.2
- Update-Sicherung der Benutzerkonfiguration auf robusten `/tmp`-Pfad umgestellt
- Bestehende `config.json` wird vor Updates als gültiges JSON geprüft und gesichert
- Konfiguration wird nach dem Update wiederhergestellt, bevor Migrationen laufen
- Neue Standardwerte werden nur ergänzt; vorhandene Geräte und Einstellungen bleiben unverändert
- Default-Konfiguration wird nur noch angelegt, wenn wirklich keine Benutzerkonfiguration vorhanden ist
- „Zurück zu LoxBerry“-Link für Desktop und Mobilansicht ergänzt

## 0.3.1
- Dashboard und Hauptseiten im hellen LoxBerry-Stil überarbeitet
- LoxBerry-Grün, weiße Karten, kompakte Navigation und responsive Darstellung ergänzt
- Dashboard mit Systemkacheln und übersichtlicheren Gerätekarten neu gestaltet
- Einstellungen, Gerätesuche und Security Center optisch vereinheitlicht
- Versionsanzeige im Dashboard wird dynamisch aus `plugin.cfg` gelesen
- Fest eingetragene Dashboard-Version `0.2.6` entfernt

## 0.3.0
- Security Center mit sichtbarer Sicherheitsbewertung hinzugefügt
- MQTT-Befehle werden über eine konfigurierbare Whitelist begrenzt
- Riskante MQTT-Aktionen `reboot` und `text` sind standardmäßig gesperrt
- Übergroße MQTT-Payloads und nicht freigegebene Aktionen werden blockiert
- Geblockte MQTT-Aktionen werden über ein Security-Event gemeldet
- Fire-TV-Netzwerksuche ist nur noch per POST mit CSRF-Schutz möglich
- Content-Security-Policy, Frame-Schutz und Permissions-Policy für sensible Seiten ergänzt
- Config-Migration auf Version 3 erhält bestehende Einstellungen und ergänzt sichere Defaults
- Konfigurations- und Logrechte sowie Ownership bei Installation/Upgrade weiter gehärtet

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
