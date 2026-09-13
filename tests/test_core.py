#!/usr/bin/env python3
"""Tests für die Kernlogik von Fire TV Control.

Aufruf im Wurzelverzeichnis des Repos:
    python3 -m unittest discover -s tests -v

Die Tests kommen ohne Fire TV, ohne adb und ohne MQTT-Broker aus.
"""
import importlib.util
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


core = _load('firetv_core', 'bin/firetv.py')


class Bildschirmerkennung(unittest.TestCase):
    """Ein Fire TV Stick bleibt wach, wenn der Fernseher ausgeschaltet wird.
    mWakefulness allein taugt deshalb nicht als Anzeige."""

    STICK_WACH_TV_AUS = "mWakefulness=Awake\nmHoldingDisplaySuspendBlocker=false\nDisplay Power: state=OFF"
    STICK_WACH_TV_AN = "mWakefulness=Awake\nmHoldingDisplaySuspendBlocker=true\nDisplay Power: state=ON"
    STICK_SCHLAEFT = "mWakefulness=Asleep\nmHoldingDisplaySuspendBlocker=false\nDisplay Power: state=OFF"

    def test_display_power_erkennt_ausgeschalteten_fernseher(self):
        self.assertFalse(core.screen_from_power(self.STICK_WACH_TV_AUS, 'display'))
        self.assertTrue(core.screen_from_power(self.STICK_WACH_TV_AN, 'display'))

    def test_wakefulness_meldet_hier_falsch_an(self):
        self.assertTrue(core.screen_from_power(self.STICK_WACH_TV_AUS, 'wakefulness'))

    def test_automatik_bevorzugt_display_power(self):
        self.assertFalse(core.screen_from_power(self.STICK_WACH_TV_AUS, 'auto'))
        self.assertTrue(core.screen_from_power(self.STICK_WACH_TV_AN, 'auto'))

    def test_automatik_faellt_zurueck_wenn_zeile_fehlt(self):
        self.assertTrue(core.screen_from_power("mWakefulness=Awake", 'auto'))
        self.assertFalse(core.screen_from_power("mWakefulness=Asleep", 'auto'))

    def test_schlafender_stick_ist_immer_aus(self):
        for m in ('auto', 'display', 'suspendblocker', 'display_or_blocker', 'wakefulness'):
            self.assertFalse(core.screen_from_power(self.STICK_SCHLAEFT, m), m)

    def test_unbekanntes_verfahren_faellt_auf_automatik_zurueck(self):
        self.assertFalse(core.screen_from_power(self.STICK_WACH_TV_AUS, 'quatsch'))

    def test_fehlende_zeilen_ergeben_none(self):
        v = core.screen_values("irgendwas anderes")
        self.assertEqual(v, {'wakefulness': None, 'display': None, 'suspendblocker': None})


class Adressen(unittest.TestCase):
    def setUp(self):
        self.cfg = {'security': {'private_adb_only': True}}

    def test_private_ip_wird_akzeptiert(self):
        self.assertEqual(core.validate_adb_target(self.cfg, '192.168.1.50', 5555), ('192.168.1.50', 5555))

    def test_oeffentliche_ip_wird_blockiert(self):
        with self.assertRaises(ValueError):
            core.validate_adb_target(self.cfg, '8.8.8.8', 5555)

    def test_hostname_wird_aufgeloest(self):
        ip, port = core.validate_adb_target(self.cfg, 'localhost', 5555)
        self.assertEqual(ip, '127.0.0.1')

    def test_unsinn_wird_abgelehnt(self):
        for v in ('nicht existent!', '', '999.999.999.999'):
            with self.assertRaises(ValueError):
                core.validate_adb_target(self.cfg, v, 5555)

    def test_port_wird_geprueft(self):
        for p in (0, -1, 70000):
            with self.assertRaises(ValueError):
                core.validate_adb_target(self.cfg, '192.168.1.50', p)


class Geraetesuche(unittest.TestCase):
    CFG = {'devices': [
        {'id': 'wz', 'name': 'Wohnzimmer TV', 'ip': '192.168.1.50'},
        {'name': 'Schlafzimmer', 'ip': '192.168.1.51'},
    ]}

    def test_treffer_ueber_id(self):
        self.assertEqual(core.find_device(self.CFG, 'wz')['ip'], '192.168.1.50')

    def test_treffer_ueber_ip(self):
        self.assertEqual(core.find_device(self.CFG, '192.168.1.51')['name'], 'Schlafzimmer')

    def test_treffer_ueber_namen_als_slug(self):
        self.assertEqual(core.find_device(self.CFG, 'schlafzimmer')['ip'], '192.168.1.51')

    def test_unbekanntes_geraet(self):
        with self.assertRaises(Exception):
            core.find_device(self.CFG, 'gibtsnicht')


class Slug(unittest.TestCase):
    def test_umwandlung(self):
        self.assertEqual(core.slug('Wohnzimmer TV'), 'wohnzimmer-tv')
        self.assertEqual(core.slug('  Küche!!  '), 'k-che')

    def test_leerer_wert_ergibt_fallback(self):
        self.assertTrue(core.slug(''))


class Texteingabe(unittest.TestCase):
    """adb shell reicht die Argumente an die Shell des Fire TV weiter.
    Ohne Quoting wären ; und $(...) dort ausführbare Befehle."""

    class FakeTV(core.FireTV):
        def __init__(self, cfg):
            self.cfg = cfg
            self.device = {}
            self.ip = '192.168.1.50'
            self.port = 5555
            self.target = 'x'
            self.timeout = 5
            self._conn = {'ok': True}
            self.gesendet = []

        def shell(self, *args):
            self.gesendet.append(list(args))
            return ''

    def tv(self):
        return self.FakeTV({'security': {'private_adb_only': True}})

    def test_semikolon_wird_gequotet(self):
        t = self.tv()
        t.command('text', 'Film ab; reboot')
        arg = t.gesendet[0][2]
        self.assertTrue(arg.startswith("'") and arg.endswith("'"), arg)
        self.assertIn(';', arg)

    def test_kommandosubstitution_wird_gequotet(self):
        t = self.tv()
        t.command('text', '$(id)')
        self.assertTrue(t.gesendet[0][2].startswith("'"))

    def test_steuerzeichen_werden_abgelehnt(self):
        with self.assertRaises(ValueError):
            self.tv().command('text', 'abc\ndef')

    def test_zu_langer_text_wird_abgelehnt(self):
        with self.assertRaises(ValueError):
            self.tv().command('text', 'x' * 513)

    def test_unbekannte_taste_wird_abgelehnt(self):
        with self.assertRaises(ValueError):
            self.tv().key('rm -rf /')

    def test_ungueltiger_paketname_wird_abgelehnt(self):
        with self.assertRaises(ValueError):
            self.tv().launch('com.foo; rm -rf /')


class CecSequenzen(unittest.TestCase):
    def sequenz(self, device):
        schritte = []

        class T(Texteingabe.FakeTV):
            def _cec_sequence(self, label, steps):
                schritte.extend(steps)
                return [{'key': k} for k, _ in steps]

        t = T({})
        t.device = device
        return t, schritte

    def test_ausschalten_zweimal_sleep(self):
        t, s = self.sequenz({'cec_off_method': 'sleep_repeat', 'cec_off_delay': 0.5})
        t.tv_off()
        self.assertEqual([k for k, _ in s], ['sleep', 'sleep'])
        self.assertEqual(s[1][1], 0.5)

    def test_ausschalten_einmal_sleep(self):
        t, s = self.sequenz({'cec_off_method': 'sleep'})
        t.tv_off()
        self.assertEqual([k for k, _ in s], ['sleep'])

    def test_ausschalten_automatik(self):
        t, s = self.sequenz({'cec_off_method': 'auto'})
        t.tv_off()
        self.assertEqual([k for k, _ in s], ['sleep', 'sleep', 'power'])

    def test_unbekannte_methode_faellt_auf_standard_zurueck(self):
        t, s = self.sequenz({'cec_off_method': 'quatsch'})
        self.assertEqual(t.tv_off()['method'], 'sleep_repeat')

    def test_einschalten_home_zweimal(self):
        t, s = self.sequenz({'cec_on_method': 'home_repeat', 'cec_on_delay': 0.4})
        t.tv_on()
        self.assertEqual([k for k, _ in s], ['home', 'home'])

    def test_verzoegerung_wird_begrenzt(self):
        t, s = self.sequenz({'cec_on_method': 'home_repeat', 'cec_on_delay': 99})
        self.assertLessEqual(t.tv_on()['delay'], 5.0)


class MqttTopics(unittest.TestCase):
    def test_basistopic_aus_konfiguration(self):
        self.assertEqual(core.base_topic({'mqtt': {'base_topic': 'wohnung/firetv'}}), 'wohnung/firetv')

    def test_standard_basistopic(self):
        self.assertEqual(core.base_topic({}), 'firetv')


class StandardKonfiguration(unittest.TestCase):
    def test_ist_gueltiges_json(self):
        with open(os.path.join(ROOT, 'config/config.default.json'), encoding='utf-8') as f:
            c = json.load(f)
        self.assertIn('mqtt', c)
        self.assertIn('devices', c)

    def test_erkennungsverfahren_ist_gueltig(self):
        with open(os.path.join(ROOT, 'config/config.default.json'), encoding='utf-8') as f:
            c = json.load(f)
        gueltig = [k for k, _ in core.SCREEN_METHODS]
        self.assertIn(c.get('screen_detect', 'auto'), gueltig)

    def test_versionen_stimmen_ueberein(self):
        def ver(pfad):
            with open(os.path.join(ROOT, pfad), encoding='utf-8') as f:
                for line in f:
                    if line.startswith('VERSION='):
                        return line.split('=', 1)[1].strip()
        self.assertEqual(ver('plugin.cfg'), ver('release.cfg'),
                         'plugin.cfg und release.cfg nennen verschiedene Versionen')

    def test_archivurl_passt_zur_version(self):
        v = None
        url = ''
        with open(os.path.join(ROOT, 'release.cfg'), encoding='utf-8') as f:
            for line in f:
                if line.startswith('VERSION='):
                    v = line.split('=', 1)[1].strip()
                if line.startswith('ARCHIVEURL='):
                    url = line.strip()
        self.assertIn('/v%s/' % v, url)


if __name__ == '__main__':
    unittest.main(verbosity=2)
