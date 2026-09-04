# LoxBerry Fire TV Control

LoxBerry-Plugin zur Abfrage und Steuerung eines oder mehrerer Amazon Fire TV / Fire TV Stick Geräte per Netzwerk-ADB.

Aktueller Entwicklungsstand: **v0.3.10**.

> Unabhängiges Community-Projekt. Nicht mit Amazon, Fire TV, LoxBerry oder Loxone verbunden oder von diesen unterstützt.

## Funktionen

- mehrere Fire-TV-Geräte mit Name, IP-Adresse und ADB-Port
- automatische Fire-TV-Suche im lokalen Netzwerk
- ADB-Autorisierungsstatus und gezieltes erneutes Verbinden
- Online-, Bildschirm-/Awake- und App-Status
- Fernbedienung: Navigation, OK, Home, Zurück, Menü und Mediensteuerung
- Lautstärke und Mute
- konfigurierbares TV-Einschalten über HDMI-CEC-orientierte ADB-Keyevents
- TV-EIN-Methoden: Home 1×, Home 2×, Wakeup + Home, Power + Home oder Automatik
- einstellbare Verzögerung zwischen CEC-Keyevents
- TV-AUS über Sleep/Standby oder Power-Keyevent
- Apps per Preset oder Android-Package-ID starten
- MQTT über den zentralen LoxBerry MQTT Broker
- MQTT-Befehls-Whitelist und Security Center
- optionaler MQTT-Befehlstoken für zusätzliche Absicherung
- Status-Polling, LoxBerry-Daemon und Watchdog
- JSON-API und Debug-/Log-Seite
- nativer LoxBerry-Webrahmen mit `LoxBerry::Web::lbheader()` / `lbfooter()`
- updatefeste Benutzerkonfiguration mit Backup/Restore und Default-Merge
- sichere Update-Prüfung mit SHA-256 und Ed25519 für signierte Releases

## Neu in v0.3.10

- Dashboard-Powerbuttons verwenden jetzt die konfigurierten Aktionen `tvon` und `tvoff`
- „Einschalten“ respektiert dadurch z. B. wirklich **Home 2×** samt Verzögerung
- „Ausschalten/Standby“ respektiert die pro Gerät gewählte AUS-Methode
- expliziter MQTT-Anzeigestatus `firetv/<id>/display` mit `ON` / `OFF`
- ADB-Ziele werden validiert und standardmäßig auf lokale/private Netze begrenzt
- zusätzliche Eingabevalidierung für Geräte-IDs, Paketnamen und Texteingaben
- MQTT-Listener gegen ungültige/übergroße Befehle weiter gehärtet
- fehlende MQTT-Quelländerungsprüfung (`mqtt_source_mtime`) ergänzt
- Security-Härtungen an Web/API und Konfiguration erweitert

## Voraussetzungen

- LoxBerry **3.0.0 oder neuer**
- Netzwerkverbindung zwischen LoxBerry und Fire TV
- ADB-Debugging auf dem Fire TV aktiviert
- HDMI-CEC bzw. Gerätesteuerung am Fire TV und Fernseher aktiviert, wenn der TV mitgeschaltet werden soll

Das Plugin installiert die benötigte ADB-Abhängigkeit über die LoxBerry-Paketverwaltung (`dpkg/apt`).

## Fire TV vorbereiten

Auf jedem Fire TV die Entwickleroptionen öffnen und **ADB-Debugging** aktivieren. Falls die Entwickleroptionen nicht sichtbar sind, unter **Einstellungen → Mein Fire TV → Info** das Gerät auswählen und die OK-Taste mehrfach drücken, bis die Entwickleroptionen freigeschaltet sind.

Beim ersten ADB-Zugriff vom LoxBerry erscheint auf dem Fire TV eine Autorisierungsabfrage. Diese bestätigen und nach Möglichkeit „Immer zulassen“ aktivieren.

Der übliche ADB-Port ist TCP **5555**. Dieser Port sollte in der Firewall ausschließlich vom LoxBerry zu den jeweiligen Fire TVs erreichbar sein.

## TV über HDMI-CEC ein- und ausschalten

Fire-TV-Modelle und Fernseher reagieren unterschiedlich auf ADB-Keyevents und HDMI-CEC. Deshalb ist die Methode pro Gerät einstellbar.

Wenn der Fernseher durch zweimaliges Drücken von Home auf der Fire-TV-Fernbedienung zuverlässig eingeschaltet wird, im Plugin **Home 2×** wählen. Der Dashboard-Button „Einschalten“ verwendet ab v0.3.10 exakt diese Geräteeinstellung.

Für das Ausschalten stehen **Sleep/Standby** und **Power-Taste** zur Verfügung. Welche Variante den Fernseher tatsächlich per CEC ausschaltet, hängt von Fire TV, Fernseher und deren CEC-Einstellungen ab.

## MQTT

Basistopic standardmäßig `firetv`, im Plugin änderbar.

Status:

- `firetv/<id>/online` → `1` / `0`
- `firetv/<id>/authorized` → `1` / `0`
- `firetv/<id>/awake` → `1` / `0`
- `firetv/<id>/display` → `ON` / `OFF`
- `firetv/<id>/app`
- `firetv/<id>/state` → vollständiger JSON-Status
- `firetv/availability`

Steuerung:

- `firetv/<id>/set`
- `firetv/<id>/command`

Beispiele:

- `on`, `1`, `true` → konfigurierte TV-EIN-Methode (`tvon`)
- `off`, `0`, `false` → konfigurierte TV-AUS-Methode (`tvoff`)
- `home`
- `back`
- `playpause`
- `volumeup`
- `volumedown`
- `mute`
- `app:netflix`
- `app:youtube`
- `app:com.example.package`

Riskante MQTT-Befehle wie Reboot oder freie Texteingabe sind standardmäßig gesperrt und müssen im Security Center ausdrücklich freigegeben werden. Für zusätzliche Absicherung kann ein MQTT-Befehlstoken verwendet werden. Broker-Zugangsdaten, ACLs und Netzsegmentierung bleiben trotzdem wichtig.

## Weboberfläche und API

Die Einstiegsseite verwendet den nativen LoxBerry-Webrahmen. Dashboard, Gerätesuche, Einstellungen, Security Center und Debug-Log sind in die Plugin-Oberfläche integriert.

Schaltende Web/API-Aktionen sind auf POST begrenzt und verwenden CSRF-/Same-Site-Prüfungen. Backend-Aufrufe erfolgen ohne Shell-Interpolation.

## Konfiguration bei Updates

Die vorhandene `config.json` wird vor einem Plugin-Update außerhalb des Plugin-Verzeichnisses gesichert, anschließend wiederhergestellt und nur um neu hinzugekommene Default-Felder ergänzt. Bestehende Geräte und Benutzerwerte werden dadurch erhalten.

## Installation

Die Installationsdatei für diese Version heißt:

`LoxBerry-FireTV-0.3.10.zip`

Installation über die LoxBerry-Pluginverwaltung. Danach Fire TVs automatisch suchen oder manuell anlegen und die einmalige ADB-Autorisierung am Fire TV bestätigen.

Die Paketierung und Syntaxprüfung laufen automatisiert über GitHub Actions.

## Releases und Autoupdate

Das Repository unterscheidet zwischen aktuellem Entwicklungsstand und **signiert veröffentlichtem GitHub-Release**. `release.cfg` wird erst auf eine neue Version umgestellt, wenn ZIP, SHA-256-Datei und Ed25519-Signatur vollständig als Release vorliegen. Dadurch verweist der LoxBerry-Autoupdater nicht auf unvollständige oder ungeprüfte Release-Dateien.

## Sicherheit

Wichtige Schutzmaßnahmen:

- LoxBerry-`htmlauth` für geschützte Weboberflächen
- POST/CSRF-/Same-Site-Schutz für schaltende Aktionen
- restriktive Rechte für Konfiguration und Logs
- MQTT-Befehls-Whitelist
- Reboot und freie Texteingabe standardmäßig gesperrt
- optionale MQTT-Befehlstoken-Prüfung
- ADB-Zielvalidierung und private/local-only Standard
- SHA-256 + Ed25519 für den sicheren Release-Updatepfad

ADB TCP 5555 und MQTT sollten nicht ungeschützt in fremde oder öffentliche Netze freigegeben werden.

Weitere Hinweise: [SECURITY.md](SECURITY.md), [LEGAL.md](LEGAL.md) und [LICENSE](LICENSE).

## Lizenz

Der originale Projektcode steht unter der **MIT License**. Drittsoftware und Systemabhängigkeiten behalten ihre jeweiligen eigenen Lizenzen. Siehe `LICENSE`, `LEGAL.md` und `THIRD_PARTY_NOTICES.md`.

## Autor

**Marco Düthorn**  
Kontakt: `duett86@web.de`
