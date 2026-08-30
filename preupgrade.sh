#!/bin/bash
set -u
PDIR="${3:-firetv}"
PCONFIG="${LBPCONFIG:?LBPCONFIG missing}/$PDIR"
BACKUP="${LBPDATA:?LBPDATA missing}/$PDIR/upgrade-config.json"
mkdir -p "$(dirname "$BACKUP")"
if [ -f "$PCONFIG/config.json" ]; then
  cp -p "$PCONFIG/config.json" "$BACKUP" || exit 1
  echo "<INFO> Fire TV Konfiguration für Update gesichert."
fi
exit 0
