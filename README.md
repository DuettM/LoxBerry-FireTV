# LoxBerry Fire TV Control

LoxBerry-Plugin zur Abfrage und Steuerung eines oder mehrerer Amazon Fire TV / Fire TV Stick Geräte per Netzwerk-ADB.

Aktueller Entwicklungsstand: **v0.3.14**.

> Unabhängiges Community-Projekt. Nicht mit Amazon, Fire TV, LoxBerry oder Loxone verbunden oder von diesen unterstützt.

## Funktionen

- mehrere Fire-TV-Geräte mit Name, IP-Adresse und ADB-Port
- automatische Fire-TV-Suche im lokalen Netzwerk
- ADB-Autorisierungsstatus und gezieltes erneutes Verbinden
- Online-, Bildschirm-/Awake- und App-Status
- wählbares Verfahren zur Bildschirmerkennung mit Diagnose in der Oberfläche
- schnelle Bildschirmüberwachung: Änderungen werden im Sekundentakt über MQTT gemeldet
- Fernbedienung: Navigation, OK, Home, Zurück, Menü und Mediensteuerung
- Lautstärke und Mute
- konfigurierbares TV-Einschalten über HDMI-CEC-orientierte ADB-Keyevents
- TV-EIN-Methoden: Home 1×, Home 2×, Wakeup + Home, Power + Home oder Automatik
- einstellbare Verzögerung zwischen CEC-Keyevents
- TV-AUS-Methoden: Sleep 1×, Sleep 2×, Power 1×, Power 2× oder Automatik
- Apps per Preset oder Android-Package-ID starten
- MQTT über den zentralen LoxBerry MQTT Broker
- MQTT-Befehls-Whitelist und Security Center
- optionaler MQTT-Befehlstoken für zusätzliche Absicherung
- Status-Polling, LoxBerry-Daemon und Watchdog
- JSON-API und Debug-/Log-Seite
- Seite „Loxone" mit fertiger MQTT-Vorlage für virtuelle Ausgänge zum Download
- nativer LoxBerry-Webrahmen mit `LoxBerry::Web::lbheader()` / `lbfooter()`
- updatefeste Benutzerkonfiguration mit Backup/Restore und Default-Merge
- API-Key für Schaltbefehle aus Loxone/Skripten

## Neu in v0.3.14

**Sicherheit**
- Texteingabe wird vor der Übergabe an `adb shell` gequotet
- MQTT-Listener läuft auch nach einem Watchdog-Neustart als Benutzer `loxberry`
- Ed25519-Signaturprüfung entfernt, da sie nie im Updatepfad eingebunden war

**Loxone**
- Seite „Loxone" erzeugt eine fertige MQTT-Vorlage für virtuelle Ausgänge
- API-Key für Schaltbefehle aus Loxone oder Skripten
- `availability` geht per Last Will auf `offline`, wenn der Listener ausfällt

**Bildschirm**
- Erkennungsverfahren wählbar, mit Vergleichsdiagnose auf der Debug-Seite
- Änderungen werden im Sekundentakt gemeldet statt erst beim nächsten Poll

**Oberfläche**
- Navigation auf Mobilgeräten auf allen Seiten, aktueller Reiter farbig markiert
- Versionsanzeige zeigt die tatsächlich installierte Version
- Dashboard fragt alle Geräte parallel ab

**Wartung**
- gemeinsames Modul `bin/webui.py` statt sechsfach kopiertem Code
- Tests unter `tests/`, ausgeführt bei jedem Push und vor jedem Release

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

Wenn der Fernseher durch zweimaliges Drücken von Home auf der Fire-TV-Fernbedienung zuverlässig eingeschaltet wird, im Plugin **Home 2×** wählen. Der Dashboard-Button „Einschalten“ verwendet exakt diese Geräteeinstellung.

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

`LoxBerry-FireTV-0.3.11.zip`

Installation über die LoxBerry-Pluginverwaltung. Danach Fire TVs automatisch suchen oder manuell anlegen und die einmalige ADB-Autorisierung am Fire TV bestätigen.

Die Paketierung und Syntaxprüfung laufen automatisiert über GitHub Actions.

## Releases und Autoupdate

`release.cfg` zeigt auf das jeweils aktuelle Release. Das LoxBerry-Autoupdate lädt das dort hinterlegte ZIP über HTTPS von GitHub und installiert es.

Zu jedem Release wird zusätzlich eine `.sha256`-Datei veröffentlicht. Wer die Installationsdatei von Hand herunterlädt, kann sie damit prüfen:

```
sha256sum -c LoxBerry-FireTV-<version>.zip.sha256
```

Eine Signaturprüfung findet nicht statt. Die Integrität des Downloads beruht auf HTTPS und darauf, dass das Release aus dem offiziellen Repository stammt.

## Sicherheit

Wichtige Schutzmaßnahmen:

- LoxBerry-`htmlauth` für geschützte Weboberflächen
- POST/CSRF-/Same-Site-Schutz für schaltende Aktionen
- restriktive Rechte für Konfiguration und Logs
- MQTT-Befehls-Whitelist
- Reboot und freie Texteingabe standardmäßig gesperrt
- optionale MQTT-Befehlstoken-Prüfung
- ADB-Zielvalidierung und private/local-only Standard
- SHA-256-Prüfsumme zu jedem Release für die manuelle Kontrolle

ADB TCP 5555 und MQTT sollten nicht ungeschützt in fremde oder öffentliche Netze freigegeben werden.

Weitere Hinweise: [SECURITY.md](SECURITY.md), [LEGAL.md](LEGAL.md), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) und [LICENSE](LICENSE).

## Lizenz

Der originale Projektcode steht unter der **MIT License**. Drittsoftware und Systemabhängigkeiten behalten ihre jeweiligen eigenen Lizenzen. Siehe `LICENSE`, `LEGAL.md` und `THIRD_PARTY_NOTICES.md`.

## Autor

**Marco Düthorn**  
Kontakt: `duett86@web.de`

## Tests

```
python3 -m unittest discover -s tests -v
```

Die Tests kommen ohne Fire TV, ohne adb und ohne MQTT-Broker aus. Sie prüfen die
Kernlogik (Bildschirmerkennung, Adressprüfung, Quoting der Texteingabe,
CEC-Sequenzen) und führen jede Seite der Oberfläche in einer nachgebauten
LoxBerry-Installation aus. Dabei wird unter anderem verglichen, ob alle Seiten
dieselbe Navigation und dieselbe Versionsanzeige liefern und ob jeder Wert, der
in einem Auswahlfeld steht, sich auch speichern lässt.

Die Workflows `tests.yml` (bei jedem Push) und `release.yml` (beim Tag) führen
sie automatisch aus.
