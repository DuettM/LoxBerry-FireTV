# LoxBerry Fire TV Control

LoxBerry-Plugin zur Abfrage und Steuerung eines oder mehrerer Amazon Fire TV / Fire TV Stick Geräte per Netzwerk-ADB.

Aktueller Entwicklungsstand: **v0.3.5**.

## Funktionen

- mehrere Fire-TV-Geräte mit Name, IP/Hostname und ADB-Port
- Online-, ADB-Autorisierungs-, Bildschirm-/Awake- und App-Status
- Fernbedienung: Navigation, OK, Home, Zurück, Menü und Mediensteuerung
- Lautstärke, Mute, Wake/Standby und HDMI-CEC-orientierte TV-Ein-/Ausschaltlogik
- Apps per Preset oder Android-Package-ID starten
- automatische Fire-TV-Suche im lokalen /24-Netz auf ADB TCP 5555
- MQTT über den zentralen LoxBerry MQTT Broker/Gateway
- MQTT-Befehls-Whitelist und Security Center
- Status-Polling, LoxBerry-Daemon und Watchdog
- JSON-API und Debug-/Log-Seite
- LoxBerry-Loglevel über die Pluginverwaltung
- nativer LoxBerry-Seitenrahmen mit `LoxBerry::Web::lbheader()` / `lbfooter()`
- feste linke Plugin-Navigation innerhalb der Fire-TV-Oberfläche
- updatefeste Benutzerkonfiguration mit Backup/Restore und Default-Merge
- sichere Update-Prüfung mit SHA-256 und Ed25519 für veröffentlichte Releases

## Fire TV vorbereiten

Auf jedem Fire TV die Entwickleroptionen öffnen und **ADB-Debugging** aktivieren. Falls die Entwickleroptionen nicht sichtbar sind, unter **Einstellungen → Mein Fire TV → Info** das Gerät auswählen und die OK-Taste mehrfach drücken, bis die Entwickleroptionen freigeschaltet sind.

Beim ersten ADB-Zugriff vom LoxBerry erscheint auf dem Fire TV eine Autorisierungsabfrage. Diese bestätigen und nach Möglichkeit „Immer zulassen“ aktivieren.

Der übliche ADB-Port ist TCP **5555**. Für die Netzwerksicherheit sollte dieser Port nur vom LoxBerry zum jeweiligen Fire TV erreichbar sein.

## MQTT

Basistopic standardmäßig `firetv`, im Plugin änderbar.

Status:

- `firetv/<id>/online`
- `firetv/<id>/authorized`
- `firetv/<id>/awake`
- `firetv/<id>/app`
- `firetv/<id>/state`
- `firetv/availability`

Steuerung:

- `firetv/<id>/set`
- `firetv/<id>/command`

Beispiele:

- `on`, `1`, `true` → TV-/Fire-TV-Einschaltpfad
- `off`, `0`, `false` → Standby-/CEC-Ausschaltpfad
- `home`
- `back`
- `playpause`
- `volumeup`
- `volumedown`
- `mute`
- `app:netflix`
- `app:youtube`
- `app:com.example.package`

Riskante MQTT-Befehle wie Reboot oder freie Texteingabe sind standardmäßig gesperrt und müssen im Security Center ausdrücklich freigegeben werden.

## LoxBerry-Oberfläche

Ab v0.3.5 verwendet die Einstiegsseite den nativen LoxBerry-Webrahmen. Dadurch stehen oben dieselben LoxBerry-Navigationssymbole wie bei anderen nativen LoxBerry-Plugins zur Verfügung. Das Fire-TV-Dashboard selbst behält darunter seine feste linke Navigation für Übersicht, Gerätesuche, Einstellungen, Security Center und Debug-Log.

## Konfiguration bei Updates

Die vorhandene `config.json` wird vor einem Plugin-Update außerhalb des Plugin-Verzeichnisses gesichert, anschließend wiederhergestellt und nur um neu hinzugekommene Default-Felder ergänzt. Bestehende Geräte und Benutzerwerte werden dabei nicht absichtlich überschrieben.

## Installation

Die jeweils gebaute Installationsdatei heißt:

`LoxBerry-FireTV-<VERSION>.zip`

Für v0.3.5 entsprechend:

`LoxBerry-FireTV-0.3.5.zip`

Die Paketierung und Syntaxprüfung laufen automatisiert über GitHub Actions.

## Releases und Autoupdate

Das Repository unterscheidet zwischen aktuellem Entwicklungsstand und **signiert veröffentlichtem GitHub-Release**. `release.cfg` zeigt nur auf eine Version, wenn deren ZIP, SHA-256-Datei und Ed25519-Signatur tatsächlich als GitHub-Release veröffentlicht wurden. So wird verhindert, dass LoxBerry auf nicht vorhandene oder ungeprüfte Update-Dateien verweist.

## Sicherheit

- Web-Aktionen mit POST/CSRF-Schutz
- sensitive Konfiguration mit restriktiven Dateirechten
- MQTT-Whitelist
- dangerous actions standardmäßig gesperrt
- Same-Origin-Frame-Schutz für die Einbettung in den nativen LoxBerry-Rahmen
- SHA-256 + Ed25519 für den sicheren Release-Updatepfad

Weitere Hinweise stehen in `SECURITY.md`.
