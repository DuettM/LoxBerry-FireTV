#!/usr/bin/env python3
"""Tests der Weboberfläche.

Jede Seite wird in einer nachgebauten LoxBerry-Installation als CGI
ausgeführt. Geprüft wird vor allem, dass die Seiten sich nicht
auseinanderentwickeln – genau daran krankte das Plugin bisher:
das Security Center hatte als einzige Seite keine Navigation für
Mobilgeräte, und die Versionsanzeige lieferte je Datei einen anderen
fest einprogrammierten Wert.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEITEN = ['dashboard.cgi', 'discover.cgi', 'config.cgi', 'security.cgi', 'loxone.cgi', 'debug.cgi']
API = 'api.cgi'
VERSION_TEST = '9.9.9'


class Installation:
    """Minimale LoxBerry-Struktur in einem temporären Verzeichnis."""

    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix='firetv-test-')
        for p in ('config/plugins/firetv', 'log/plugins/firetv', 'data/system',
                  'bin/plugins/firetv', 'webfrontend/htmlauth/plugins/firetv',
                  'config/system'):
            os.makedirs(os.path.join(self.dir, p), exist_ok=True)

        shutil.copy(os.path.join(ROOT, 'config/config.default.json'),
                    os.path.join(self.dir, 'config/plugins/firetv/config.json'))
        for f in os.listdir(os.path.join(ROOT, 'bin')):
            if f.endswith('.py'):
                shutil.copy(os.path.join(ROOT, 'bin', f), os.path.join(self.dir, 'bin/plugins/firetv', f))
        for f in SEITEN + [API]:
            shutil.copy(os.path.join(ROOT, 'webfrontend/htmlauth', f),
                        os.path.join(self.dir, 'webfrontend/htmlauth/plugins/firetv', f))

        with open(os.path.join(self.dir, 'data/system/plugindatabase.json'), 'w', encoding='utf-8') as f:
            json.dump({'plugins': [{'name': 'firetv', 'folder': 'firetv', 'version': VERSION_TEST, 'loglevel': 6}]}, f)
        with open(os.path.join(self.dir, 'config/system/general.json'), 'w', encoding='utf-8') as f:
            json.dump({'Mqtt': {'Brokerhost': '127.0.0.1', 'Brokerport': 11883}}, f)

        c = self.config()
        c['web_secret'] = 's' * 64
        c['web_api_key'] = 'k' * 22
        c['devices'] = [{'id': 'wz', 'name': 'Wohnzimmer', 'ip': '192.168.1.50', 'port': 5555, 'enabled': True}]
        self.write(c)

    def config(self):
        with open(os.path.join(self.dir, 'config/plugins/firetv/config.json'), encoding='utf-8') as f:
            return json.load(f)

    def write(self, c):
        with open(os.path.join(self.dir, 'config/plugins/firetv/config.json'), 'w', encoding='utf-8') as f:
            json.dump(c, f)

    def get(self, seite, query='', timeout=60):
        pfad = os.path.join(self.dir, 'webfrontend/htmlauth/plugins/firetv', seite)
        env = dict(os.environ, LBHOMEDIR=self.dir, SCRIPT_FILENAME=pfad,
                   REQUEST_METHOD='GET', QUERY_STRING=query, HTTP_HOST='loxberry',
                   PATH='/nonexistent:' + os.environ.get('PATH', ''))
        r = subprocess.run(['python3', pfad], capture_output=True, text=True, env=env, timeout=timeout)
        return r.stdout + r.stderr

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


LB = None


def setUpModule():
    global LB
    LB = Installation()


def tearDownModule():
    LB.cleanup()


class JedeSeite(unittest.TestCase):
    """Diese Prüfungen laufen über alle Seiten - eine Seite darf nicht ausscheren."""

    def seiten(self):
        for s in SEITEN:
            with self.subTest(seite=s):
                yield s, LB.get(s)

    def test_keine_ausnahme(self):
        for s, h in self.seiten():
            self.assertNotIn('Traceback', h, '%s wirft eine Ausnahme' % s)

    def test_liefert_html(self):
        for s, h in self.seiten():
            self.assertIn('Content-Type: text/html', h, s)
            self.assertIn('</html>', h, s)

    def test_navigation_enthaelt_alle_seiten(self):
        for s, h in self.seiten():
            for ziel in SEITEN:
                self.assertIn('href="%s"' % ziel, h,
                              '%s verlinkt %s nicht - von dort führt kein Weg zurück' % (s, ziel))

    def test_mobile_navigation_vorhanden(self):
        for s, h in self.seiten():
            m = re.search(r'<div class="mobile">(.*?)</div>', h, re.S)
            self.assertIsNotNone(m, '%s hat keine Navigation für Mobilgeräte' % s)
            self.assertEqual(len(re.findall(r'<a[ >]', m.group(1))), len(SEITEN),
                             '%s zeigt nicht alle Reiter' % s)

    def test_aktuelle_seite_ist_markiert_nicht_entfernt(self):
        for s, h in self.seiten():
            m = re.search(r'<div class="mobile">(.*?)</div>', h, re.S)
            self.assertIn('href="%s"' % s, m.group(1), '%s blendet sich selbst aus' % s)
            self.assertRegex(m.group(1), r'class="active" href="%s"' % re.escape(s),
                             '%s markiert den aktuellen Reiter nicht' % s)

    def test_kein_roher_programmcode_im_html(self):
        """Ein Ausdruck in einem einfachen String statt in einem f-String
        landet wörtlich im HTML - genau das ist beim Umbau passiert."""
        for s, h in self.seiten():
            self.assertNotIn('webui.', h, '%s gibt Programmcode als Text aus' % s)
            self.assertNotRegex(h, r"\{[a-z_]+\.[A-Z_]+\}", '%s enthält einen nicht ersetzten Platzhalter' % s)

    def test_navigation_ist_formatiert(self):
        """Ohne diese Regeln steht die Navigation unformatiert als Linkliste da
        und die Leiste für Mobilgeräte erscheint auch am Desktop."""
        for s, h in self.seiten():
            style = re.search(r'<style>(.*?)</style>', h, re.S)
            self.assertIsNotNone(style, '%s hat keinen Style-Block' % s)
            css = style.group(1)
            self.assertIn('.nav a{', css, '%s formatiert die Seitenleiste nicht' % s)
            self.assertIn('.mobile a.active', css, '%s hebt den aktuellen Reiter nicht hervor' % s)
            self.assertIn('.mobile{display:none}', css,
                          '%s blendet die Mobilleiste am Desktop nicht aus' % s)

    def test_version_kommt_aus_der_plugindatenbank(self):
        for s, h in self.seiten():
            self.assertIn(VERSION_TEST, h,
                          '%s zeigt eine fest einprogrammierte statt der installierten Version' % s)

    def test_sicherheitskopfzeilen(self):
        for s, h in self.seiten():
            self.assertIn('Cache-Control: no-store', h, s)
            self.assertIn('X-Content-Type-Options: nosniff', h, s)
            self.assertIn('frame-ancestors', h, s)

    def test_geheimnisse_stehen_nicht_ungefragt_im_html(self):
        for s, h in self.seiten():
            self.assertNotIn('s' * 64, h, '%s gibt das Web-Secret aus' % s)


class Formularpruefungen(unittest.TestCase):
    """Werte, die im Auswahlfeld stehen, müssen sich auch speichern lassen.
    Beim Ausschaltverfahren war das eine Zeit lang nicht so."""

    def post(self, seite, felder):
        c = LB.config()
        import hashlib, hmac
        tok = hmac.new(str(c.get('web_secret', '')).encode(), b'|', hashlib.sha256).hexdigest()
        felder = dict(felder, csrf=tok)
        body = '&'.join('%s=%s' % (k, v) for k, v in felder.items())
        pfad = os.path.join(LB.dir, 'webfrontend/htmlauth/plugins/firetv', seite)
        env = dict(os.environ, LBHOMEDIR=LB.dir, SCRIPT_FILENAME=pfad, REQUEST_METHOD='POST',
                   CONTENT_LENGTH=str(len(body)), HTTP_SEC_FETCH_SITE='same-origin', HTTP_HOST='loxberry',
                   PATH='/nonexistent:' + os.environ.get('PATH', ''))
        r = subprocess.run(['python3', pfad], input=body, capture_output=True, text=True, env=env, timeout=60)
        return r.stdout

    def auswahlwerte(self, html_text, name):
        m = re.search(r'name="%s"[^>]*>(.*?)</select>' % name, html_text, re.S)
        return re.findall(r'value="([^"]+)"', m.group(1)) if m else []

    def test_alle_ausschaltmethoden_sind_speicherbar(self):
        h = LB.get('config.cgi')
        werte = self.auswahlwerte(h, 'cec_off_method')
        self.assertTrue(werte, 'Auswahlfeld für die Ausschaltmethode fehlt')
        for w in werte:
            with self.subTest(methode=w):
                out = self.post('config.cgi', {'form_action': 'save_device_cec', 'id': 'wz',
                                               'cec_on_method': 'home', 'cec_on_delay': '0.8',
                                               'cec_off_method': w})
                self.assertNotIn('Ungültige TV-AUS-Methode', out,
                                 '%s steht zur Auswahl, wird aber abgelehnt' % w)

    def test_alle_einschaltmethoden_sind_speicherbar(self):
        h = LB.get('config.cgi')
        for w in self.auswahlwerte(h, 'cec_on_method'):
            with self.subTest(methode=w):
                out = self.post('config.cgi', {'form_action': 'save_device_cec', 'id': 'wz',
                                               'cec_on_method': w, 'cec_on_delay': '0.8',
                                               'cec_off_method': 'sleep'})
                self.assertNotIn('Ungültige TV-EIN-Methode', out, w)

    def test_alle_erkennungsverfahren_sind_speicherbar(self):
        h = LB.get('config.cgi')
        for w in self.auswahlwerte(h, 'screen_detect'):
            with self.subTest(verfahren=w):
                out = self.post('config.cgi', {'form_action': 'save_general', 'poll_interval': '30',
                                               'adb_timeout': '8', 'screen_poll_interval': '5',
                                               'screen_detect': w, 'base_topic': 'firetv'})
                self.assertNotIn('Unbekanntes Erkennungsverfahren', out, w)

    def test_post_ohne_gueltiges_token_wird_abgewiesen(self):
        pfad = os.path.join(LB.dir, 'webfrontend/htmlauth/plugins/firetv/config.cgi')
        body = 'form_action=save_device_cec&id=wz&csrf=falsch'
        env = dict(os.environ, LBHOMEDIR=LB.dir, SCRIPT_FILENAME=pfad, REQUEST_METHOD='POST',
                   CONTENT_LENGTH=str(len(body)), HTTP_SEC_FETCH_SITE='same-origin', HTTP_HOST='loxberry')
        r = subprocess.run(['python3', pfad], input=body, capture_output=True, text=True, env=env, timeout=60)
        self.assertIn('Sicherheitsprüfung fehlgeschlagen', r.stdout)


class LoxoneVorlage(unittest.TestCase):
    def test_vorlage_ist_gueltiges_xml(self):
        import xml.dom.minidom as minidom
        h = LB.get('loxone.cgi', 'download=vq')
        # text=True wandelt \r\n in \n um, deshalb auf beides prüfen
        h = h.replace('\r\n', '\n')
        xml = h.split('\n\n', 1)[1] if '\n\n' in h else h
        d = minidom.parseString(xml)
        self.assertEqual(d.documentElement.tagName, 'VirtualOut')
        self.assertTrue(d.getElementsByTagName('VirtualOutCmd'))

    def test_befehle_nutzen_das_richtige_topic(self):
        h = LB.get('loxone.cgi', 'download=vq')
        self.assertIn('publish firetv/wz/set tvon', h)

    def test_nur_freigegebene_aktionen_sind_enthalten(self):
        c = LB.config()
        erlaubt = set(c['mqtt']['allowed_actions'])
        h = LB.get('loxone.cgi', 'download=vq')
        for aktion in re.findall(r'publish firetv/wz/set ([a-z]+)', h):
            self.assertIn(aktion, erlaubt, '%s steht nicht in der Whitelist' % aktion)


class Api(unittest.TestCase):
    """api.cgi ist die Schnittstelle für Loxone und Skripte."""

    def ruf(self, methode='GET', query='', body='', extra=None):
        pfad = os.path.join(LB.dir, 'webfrontend/htmlauth/plugins/firetv', API)
        env = dict(os.environ, LBHOMEDIR=LB.dir, SCRIPT_FILENAME=pfad, REQUEST_METHOD=methode,
                   QUERY_STRING=query, HTTP_HOST='loxberry', HTTP_SEC_FETCH_SITE='same-origin',
                   PATH='/nonexistent:' + os.environ.get('PATH', ''))
        if methode == 'POST':
            env['CONTENT_LENGTH'] = str(len(body))
        env.update(extra or {})
        r = subprocess.run(['python3', pfad], input=body if methode == 'POST' else None,
                           capture_output=True, text=True, env=env, timeout=60)
        return r.stdout

    def json_teil(self, out):
        return json.loads(out.split('\n\n', 1)[1] if '\n\n' in out.replace('\r\n', '\n') else out)

    def test_status_eines_geraets_per_get(self):
        """GET-Parameter wurden früher stillschweigend verworfen."""
        d = self.json_teil(self.ruf(query='action=status&device=wz').replace('\r\n', '\n'))
        self.assertNotIn('devices', d, 'device= wurde ignoriert und die ganze Liste geliefert')

    def test_status_ohne_geraet_listet_geraete(self):
        d = self.json_teil(self.ruf(query='action=status').replace('\r\n', '\n'))
        self.assertTrue(d['ok'])
        self.assertEqual(d['devices'][0]['id'], 'wz')

    def test_schaltbefehl_per_get_wird_abgelehnt(self):
        out = self.ruf(query='action=tvon&device=wz')
        self.assertIn('nur per POST', out)

    def test_schaltbefehl_ohne_nachweis_wird_abgelehnt(self):
        out = self.ruf('POST', body='action=tvon&device=wz')
        self.assertIn('CSRF', out)

    def test_api_key_ersetzt_den_csrf_token(self):
        """Ein Miniserver kann den cookiegebundenen CSRF-Token nicht bilden."""
        out = self.ruf('POST', body='action=tvon&device=wz&apikey=' + 'k' * 22)
        self.assertNotIn('CSRF', out)

    def test_falscher_api_key_wird_abgelehnt(self):
        out = self.ruf('POST', body='action=tvon&device=wz&apikey=falsch')
        self.assertIn('CSRF', out)

    def test_api_key_taucht_nicht_in_der_statusantwort_auf(self):
        out = self.ruf(query='action=status')
        self.assertNotIn('k' * 22, out)


if __name__ == '__main__':
    unittest.main(verbosity=2)
