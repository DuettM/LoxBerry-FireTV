#!/usr/bin/env python3
import json
print("Content-Type: application/json; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nPermissions-Policy: camera=(), microphone=(), geolocation=()\r\n\r\n",end="")
print(json.dumps({"ok":True,"service":"firetv"},separators=(",",":")))
