#!/usr/bin/env python3
"""Gemeinsame Bausteine der Weboberfläche.

Liegt bewusst unter bin/ und nicht im Webverzeichnis: Apache liefert hier
nichts aus. Die CGI-Skripte laden das Modul über bootstrap() weiter unten.

Bis 0.3.13 stand dieser Code in jeder der sechs CGI-Dateien noch einmal.
Genau daran lag es, dass das Security Center als einzige Seite keine
Navigation für Mobilgeräte hatte und dass eine Prüfung der TV-AUS-Methode
an einer Stelle erweitert wurde und an der anderen nicht.
"""
import hashlib
import hmac
import html
import json
import os
import re
import sys

VERSION_FALLBACK = '0.3.14'

# ---------------------------------------------------------------- Pfade

def script_path():
    return os.path.abspath(os.environ.get('SCRIPT_FILENAME') or sys.argv[0] or __file__)


def root():
    """Basisverzeichnis des LoxBerry."""
    p = script_path()
    m = os.sep + 'webfrontend' + os.sep
    if m in p:
        return p.split(m, 1)[0]
    r = os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME')
    if r:
        return r
    raise RuntimeError('LoxBerry Basisverzeichnis konnte nicht ermittelt werden')


def folder():
    """Ordnername des Plugins, z. B. firetv."""
    parts = script_path().split(os.sep)
    return parts[parts.index('plugins') + 1] if 'plugins' in parts else 'firetv'


def config_path(base=None, fld=None):
    return os.path.join(base or root(), 'config', 'plugins', fld or folder(), 'config.json')


def bin_path(base=None, fld=None):
    return os.path.join(base or root(), 'bin', 'plugins', fld or folder())


def log_path(base=None, fld=None):
    return os.path.join(base or root(), 'log', 'plugins', fld or folder(), 'firetv.log')


def version(fld=None):
    """Installierte Version. LoxBerry legt plugin.cfg nicht mit ab, deshalb
    zuerst die Plugindatenbank; plugin.cfg nur beim Betrieb aus dem Quellordner."""
    fld = fld or folder()
    base = script_path().split(os.sep + 'webfrontend' + os.sep, 1)[0]
    lb = os.environ.get('LBHOMEDIR') or os.environ.get('LBHOME') or base
    try:
        with open(os.path.join(lb, 'data', 'system', 'plugindatabase.json'), encoding='utf-8') as f:
            for p in json.load(f).get('plugins', []):
                if str(p.get('folder', '')) == fld or str(p.get('name', '')) == 'firetv':
                    v = str(p.get('version', '') or '').strip()
                    if v:
                        return v
    except Exception:
        pass
    try:
        with open(os.path.join(base, 'plugin.cfg'), encoding='utf-8') as f:
            for line in f:
                if line.startswith('VERSION='):
                    return line.split('=', 1)[1].strip()
    except Exception:
        pass
    return VERSION_FALLBACK


def slug(s):
    s = re.sub(r'[^a-z0-9]+', '-', str(s).strip().lower()).strip('-')
    return s or 'firetv'


# ------------------------------------------------------------ Konfiguration

def load_config(path=None):
    with open(path or config_path(), encoding='utf-8') as f:
        return json.load(f)


# ------------------------------------------------------------ Sicherheit

def post_data():
    from urllib.parse import parse_qs
    if os.environ.get('REQUEST_METHOD', 'GET').upper() != 'POST':
        return {}
    try:
        n = int(os.environ.get('CONTENT_LENGTH') or 0)
    except ValueError:
        return {}
    if n <= 0 or n > 262144:
        return {}
    raw = sys.stdin.read(n)
    return {k: (v[-1] if v else '') for k, v in parse_qs(raw, keep_blank_values=True).items()}


def csrf(c):
    return hmac.new(str(c.get('web_secret', '')).encode(),
                    (os.environ.get('HTTP_COOKIE', '') + '|' + os.environ.get('HTTP_USER_AGENT', '')).encode(),
                    hashlib.sha256).hexdigest()


def same_site():
    sf = os.environ.get('HTTP_SEC_FETCH_SITE', '')
    if sf and sf not in ('same-origin', 'same-site', 'none'):
        return False
    host = os.environ.get('HTTP_HOST', '')
    for env in ('HTTP_ORIGIN', 'HTTP_REFERER'):
        v = os.environ.get(env, '')
        if v and host and host not in v:
            return False
    return True


def check_post(c, f):
    """Wirft ValueError, wenn Herkunft oder CSRF-Token nicht stimmen."""
    if not same_site() or not hmac.compare_digest(str(f.get('csrf', '')), csrf(c)):
        raise ValueError('Sicherheitsprüfung fehlgeschlagen.')


def csrf_field(c):
    return '<input type="hidden" name="csrf" value="%s">' % html.escape(csrf(c), quote=True)


# ------------------------------------------------------------ Navigation

PAGES = [
    ('dashboard.cgi', '\u2302 Übersicht', '\u2302 Übersicht'),
    ('discover.cgi', '\u2315 Suche', '\u2315 Fire TVs suchen'),
    ('config.cgi', '\u2699 Einstellungen', '\u2699 Einstellungen'),
    ('security.cgi', '\U0001f512 Sicherheit', '\U0001f512 Security Center'),
    ('loxone.cgi', '\u21c4 Loxone', '\u21c4 Loxone'),
    ('debug.cgi', '\u25a4 Debug', '\u25a4 Debug-Log'),
]


def mobile_nav(current):
    """Leiste für schmale Bildschirme. Enthält immer alle Seiten – die aktuelle
    wird markiert, nicht weggelassen."""
    out = []
    for href, kurz, _ in PAGES:
        cls = ' class="active"' if href == current else ''
        out.append('<a%s href="%s">%s</a>' % (cls, href, kurz))
    return '<div class="mobile">%s</div>' % ''.join(out)


def sidebar(current):
    out = ['<nav class="nav"><small>Fire TV Control</small>']
    for i, (href, _, lang) in enumerate(PAGES):
        if i == 2:
            out.append('<div class="sep"></div>')
        cls = ' class="active"' if href == current else ''
        out.append('<a%s href="%s">%s</a>' % (cls, href, lang))
    out.append('</nav>')
    return ''.join(out)


NAV_CSS = """
.nav{background:#fff;border:1px solid #dde4e8;border-radius:9px;padding:8px;height:max-content;position:sticky;top:8px}
.nav small{display:block;color:#8a959e;padding:8px 12px 4px;font-size:10px;text-transform:uppercase;letter-spacing:.07em}
.nav a{display:block;padding:11px 12px;border-radius:6px;color:#34404a;font-weight:600;text-decoration:none}
.nav a:hover{background:#f5f8f3}
.nav a.active{background:#eaf5df;color:#2d7d29}
.nav .sep{height:1px;background:#edf0f2;margin:7px 4px}
.mobile{display:none}
@media(max-width:900px){
 .nav{display:none}
 .mobile{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
 .mobile a{background:#fff;border:1px solid #dde4e8;padding:9px 11px;border-radius:6px;text-decoration:none;color:#34404a}
 .mobile a.active{background:#73b72b;border-color:#73b72b;color:#fff;font-weight:700}
}
"""


def headers(csp="default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'self'"):
    return ("Content-Type: text/html; charset=utf-8\r\n"
            "Cache-Control: no-store\r\n"
            "X-Content-Type-Options: nosniff\r\n"
            "Referrer-Policy: no-referrer\r\n"
            "Content-Security-Policy: %s\r\n"
            "X-Frame-Options: SAMEORIGIN\r\n\r\n" % csp)


def fail(msg, status='500 Internal Server Error'):
    print('Status: %s\r\nContent-Type: text/html; charset=utf-8\r\n\r\n<h1>Fire TV Control</h1><p>%s</p>'
          % (status, html.escape(str(msg))))
    sys.exit(0)


# ------------------------------------------------------------ Bootstrap

BOOTSTRAP = '''
import importlib.util as _il, os as _os, sys as _sys
def _load_webui():
    p = _os.path.abspath(_os.environ.get('SCRIPT_FILENAME') or __file__)
    m = _os.sep + 'webfrontend' + _os.sep
    base = p.split(m, 1)[0] if m in p else (_os.environ.get('LBHOMEDIR') or _os.environ.get('LBHOME') or '')
    parts = p.split(_os.sep)
    fld = parts[parts.index('plugins') + 1] if 'plugins' in parts else 'firetv'
    mp = _os.path.join(base, 'bin', 'plugins', fld, 'webui.py')
    s = _il.spec_from_file_location('firetv_webui', mp)
    mod = _il.module_from_spec(s); s.loader.exec_module(mod); return mod
webui = _load_webui()
'''
