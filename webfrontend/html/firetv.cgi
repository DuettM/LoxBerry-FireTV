#!/usr/bin/env python3
import json
print("Content-Type: application/json; charset=utf-8\n")
print(json.dumps({"ok":True,"plugin":"Fire TV Control","version":"0.1.0"}))
