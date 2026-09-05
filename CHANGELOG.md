# Changelog

## 0.3.12
- Mobile Navigation im Security Center ergänzt, damit Übersicht, Suche, Einstellungen, Sicherheit und Debug auch auf schmalen Displays erreichbar bleiben
- Aktiver Navigationspunkt bleibt sichtbar und wird grün hervorgehoben
- Versionsanzeige im Security Center auf die aktuelle Plugin-Version vereinheitlicht
- Darstellung auf kleinen Displays verbessert

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
