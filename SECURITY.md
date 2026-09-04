# Security Policy

## Unterstützte Version

Sicherheitskorrekturen werden grundsätzlich für den jeweils aktuellen veröffentlichten Stand gepflegt. Ältere Versionen sollten aktualisiert werden, sobald eine neuere stabile Version verfügbar ist.

## Sicherheitsmodell

Dieses Plugin steuert Fire-TV-Geräte über Netzwerk-ADB und kann MQTT-Befehle aus dem lokalen LoxBerry-Umfeld empfangen. Beide Schnittstellen sind leistungsfähig und sollten nur in vertrauenswürdigen Netzen betrieben werden.

Wichtige Schutzmaßnahmen im Plugin:

- geschützte Weboberflächen unter LoxBerry `htmlauth`
- schaltende Web/API-Aktionen nur per POST
- CSRF- und Same-Site-Prüfungen
- keine Shell-Interpolation für Backend-Aufrufe
- MQTT-Befehls-Whitelist
- `reboot` und freie Texteingabe standardmäßig gesperrt
- optionale zusätzliche MQTT-Befehlstoken-Prüfung
- Begrenzung von MQTT-Payload- und Eingabelängen
- Validierung von Geräte-IDs, Paketnamen, IP-Adressen und ADB-Ports
- ADB-Ziele standardmäßig nur in lokalen/privaten Netzen
- restriktive Dateirechte für Konfiguration und Logs
- SHA-256- und Ed25519-Prüfung für den vorgesehenen signierten Updatepfad

## Netzwerkempfehlungen

ADB TCP 5555 sollte in der Firewall ausschließlich vom LoxBerry zu den konfigurierten Fire TVs freigegeben werden. ADB darf nicht direkt aus dem Internet erreichbar sein.

MQTT sollte nur über den vertrauenswürdigen LoxBerry-Broker bzw. einen entsprechend abgesicherten Broker genutzt werden. Broker-Authentifizierung und ACLs sollten verwendet werden, wenn sie verfügbar sind. Ein optionaler Plugin-Befehlstoken ist eine zusätzliche Schutzschicht, ersetzt aber keine Broker- und Netzwerksicherheit.

## ADB-Autorisierung

Beim ersten Verbindungsaufbau muss die ADB-Autorisierung am Fire TV bestätigt werden. Das Plugin versucht nicht, diese Gerätefreigabe zu umgehen.

## Sicherheitslücke melden

Bitte keine Schwachstellen, Zugangsdaten, Tokens, privaten Schlüssel, Session-Cookies, personenbezogene Daten oder funktionsfähige Exploit-Details in einem öffentlichen Issue veröffentlichen.

Wenn GitHub Private Vulnerability Reporting / Security Advisories für das Repository verfügbar ist, diesen Weg bevorzugen. Alternativ den Repository-Inhaber privat über GitHub kontaktieren.

Eine Meldung sollte möglichst enthalten:

- betroffene Plugin-Version
- Auswirkung
- reproduzierbare Schritte
- erwartetes und tatsächliches Verhalten
- bereinigte Logs ohne Zugangsdaten oder Tokens

## Verantwortungsvolles Testen

Nur Systeme, Geräte und Accounts testen, die dir gehören oder für deren Test du ausdrücklich autorisiert bist. Keine Zugangskontrollen umgehen, keine Daten exfiltrieren und keine DoS-/Lasttests gegen fremde Systeme durchführen.

## Zugangsdaten und Schlüssel

Werden Passwörter, Tokens, Cookies oder private Signierschlüssel versehentlich veröffentlicht, gelten sie als kompromittiert und müssen umgehend rotiert bzw. widerrufen werden. Das nachträgliche Löschen aus Git allein reicht nicht aus.

## Release-Baseline

Vor einem öffentlichen Release sollten mindestens Syntax-/Build-Prüfungen, Secret-Scanning, Lizenz-/Abhängigkeitsprüfung und der LoxBerry-Sicherheitscheck durchgeführt werden. Der signierte Releasepfad darf nur verwendet werden, wenn ZIP, SHA-256 und Signatur vollständig zusammenpassen.
