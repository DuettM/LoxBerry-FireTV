# LoxBerry Fire TV Control

LoxBerry-Plugin zur Abfrage und Steuerung eines oder mehrerer Amazon Fire TV / Fire TV Stick Geräte per Netzwerk-ADB.

## Funktionen

- mehrere Fire-TV-Geräte
- Online-/ADB-/Bildschirmstatus
- aktuell aktive App
- Fernbedienung: Navigation, Home, Zurück, Menü, Medien, Lautstärke
- Wake / Standby / Reboot
- Apps per Package-ID oder Preset starten
- MQTT über den LoxBerry MQTT Gateway/Broker
- Status-Polling und Watchdog
- Weboberfläche und JSON-API

## Fire TV vorbereiten

Auf jedem Fire TV die Entwickleroptionen öffnen und **ADB-Debugging** aktivieren. Beim ersten Zugriff die Verbindung vom LoxBerry auf dem Fire TV bestätigen.

## MQTT

Basistopic standardmäßig `firetv`.

Status:
- `firetv/<id>/online`
- `firetv/<id>/authorized`
- `firetv/<id>/awake`
- `firetv/<id>/app`
- `firetv/<id>/state`

Steuerung:
- `firetv/<id>/set`

Payload-Beispiele:
- `home`
- `back`
- `standby`
- `wakeup`
- `playpause`
- `volumeup`
- `app:netflix`
- `app:com.example.package`

## Installation

Die Installationsdatei ist `LoxBerry-FireTV-0.1.0.zip`. Autoupdate ist in v0.1.0 vorerst deaktiviert, bis das Binärarchiv als GitHub-Release veröffentlicht ist.
