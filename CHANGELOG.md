# Changelog

## [0.3.12]

### Sicherheit
- Texteingabe (`text`) wird vor der Übergabe an `adb shell` gequotet. Vorher konnten Zeichen wie `;`, `|` oder `$(...)` als Shell-Befehl auf dem Fire TV ausgeführt werden.
- `key()` akzeptiert nur noch bekannte Keycodes statt beliebiger Strings.
- Der Watchdog startet den MQTT-Listener wieder als Benutzer `loxberry`; bisher lief er nach einem Neustart durch den Cron als root.
- MQTT-Pakete werden auf 64 KB begrenzt (vorher bis 256 MB Puffer je Paket).
- Debug-Log maskiert zusätzlich API-Key, MQTT-Befehlstoken und die Broker-Zugangsdaten aus `general.json`.

### Neu
- Neue Seite „Loxone": erzeugt eine fertige Vorlage für virtuelle Ausgänge (`VQ_FireTV_MQTT.xml`), die über das MQTT-Gateway des LoxBerry sendet. Enthält für jedes Gerät alle freigegebenen Befehle mit dem richtigen Topic, berücksichtigt die Befehls-Whitelist und den Befehlstoken. Dazu eine Tabelle zum Kopieren und die Liste der Status-Topics für die Rückmeldung an den Miniserver.
- Schnelle Bildschirmüberwachung: der MQTT-Listener fragt in einem einstellbaren Takt (Standard 5 Sekunden, 0 schaltet ab) nur den Bildschirmzustand ab und meldet jede Änderung sofort über `awake` und `display`. Dafür genügt ein einziger adb-Aufruf je Gerät. Nicht erreichbare Geräte werden eine Minute lang übersprungen, damit sie den Takt nicht ausbremsen.
- Das Verfahren zur Bildschirmerkennung ist wählbar (Einstellungen → Bildschirmerkennung): Display Power, Display-Suspend-Blocker, beides kombiniert, Wakefulness oder automatisch. „Automatisch" wertet jetzt bevorzugt `Display Power` aus und fällt nur zurück, wenn die Zeile fehlt – bisher galt der Bildschirm schon als an, sobald `mWakefulness=Awake` war. Ein Fire TV Stick bleibt aber wach, wenn der Fernseher per Fernbedienung ausgeschaltet wird, weshalb der Zustand dauerhaft „an" blieb.
- Bildschirm-Diagnose auf der Debug-Seite: zeigt pro Gerät die Rohwerte aus `dumpsys power` (Wakefulness, Display Power, Suspend Blocker) samt aktueller Erkennung. Zusätzlich wird jedes Erkennungsverfahren mit seinem Ergebnis aufgelistet, sodass sich ohne SSH ablesen lässt, welches beim eigenen Gerät auf das Abschalten reagiert.
- API-Key für `api.cgi` (Header `X-FireTV-Key` oder POST-Feld `apikey`) als Alternative zum browsergebundenen CSRF-Token, damit Schaltbefehle vom Loxone Miniserver nutzbar sind. Verwaltung im Security Center.

### Entfernt
- Die Ed25519-Signaturprüfung (`bin/secure_update.py`, `bin/update_public_key.hex`, `SIGURL` in `release.cfg`) ist entfallen. Sie war an keiner Stelle in den Updatepfad eingebunden: das LoxBerry-Autoupdate lädt das ZIP aus `release.cfg` und installiert es ohne Prüfung. Ein Schutzmerkmal, das in der Dokumentation steht, aber nichts prüft, ist irreführend.
- Zu jedem Release wird weiterhin eine `.sha256`-Datei veröffentlicht, mit der ein manueller Download kontrolliert werden kann. Die Integrität des Downloads beruht auf HTTPS und dem Zugriffsschutz des Repositories.

### Behoben
- Hostnamen werden jetzt aufgelöst und danach validiert. Bisher ließen sich Geräte mit Hostnamen anlegen, die das Backend anschließend immer ablehnte.
- Statusabfrage startet nicht mehr für jedes Shell-Kommando ein neues `adb connect`/`get-state`; der Verbindungszustand wird je Aufruf gecacht.
- `publish_status()` nutzt eine MQTT-Verbindung statt sechs; CONNACK-Returncode wird ausgewertet und DISCONNECT sauber geflusht.
- Awake-Erkennung wertet `state=ON` nicht mehr kontextfrei aus (Falsch-Positive).
- Die Kachel „Bildschirm" im Dashboard zeigte bei jedem Fehler „Standby", weil `status()` das Feld `awake` bei nicht erreichbarem Gerät gar nicht erst setzt. Unbekannter Status wird jetzt als „—" dargestellt, zusammen mit der tatsächlichen Fehlerursache. Das Zeitlimit der Statusabfrage im Dashboard steigt von 12 auf 25 Sekunden.
- Cron-Poll läuft unter `flock`, überlappende Durchläufe entfallen.
- Netzwerksuche prüft gefundene Geräte parallel statt seriell.
- Die Menüleiste auf Mobilgeräten zeigt auf jeder Seite alle fünf Reiter; die aktuelle Seite verschwindet nicht mehr, sondern ist grün hinterlegt.
- Das Security Center hatte als einzige Seite gar keine Menüleiste auf Mobilgeräten – von dort führte kein Weg zurück.
- Versionsanzeige liest die installierte Version aus der LoxBerry-Plugindatenbank; bisher wurde immer ein fest einprogrammierter, veralteter Wert angezeigt.
- Ausgewählte Schalter im Security Center bleiben sichtbar markiert (grün bzw. rot bei riskanten Freigaben), Speichern-Button bleibt am unteren Rand stehen.
- `firetv.log` und `watchdog.log` rotieren bei 1 MB; `debug_log()` beachtet den LoxBerry-Loglevel.


## 0.3.11
- Ed25519-Vertrauenskette für künftige Releases erneuert
- Neuer öffentlicher Update-Schlüssel im Secure-Updater hinterlegt
- Einmaliges manuelles Update auf v0.3.11 erforderlich, wenn eine bestehende Installation noch den vorherigen öffentlichen Schlüssel verwendet
- Release-Paketierung um `THIRD_PARTY_NOTICES.md` ergänzt
- Funktionsstand von v0.3.10 einschließlich korrigierter `tvon`-/`tvoff`-Powerbuttons übernommen
- Ab v0.3.11 können folgende Releases wieder über die neue signierte Update-Vertrauenskette geprüft werden

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
