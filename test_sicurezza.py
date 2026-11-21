#!/usr/bin/env python3
"""Test di sicurezza del Mod Manager (18/11/2026, dopo la perdita di 96 mod del 17/11).

Lavorano SOLO in cartelle temporanee: tutte le cartelle di server.py vengono sostituite prima di
ogni test. Per tenerle fuori da /tmp (RAM) lancia con TMPDIR=<cartella su disco>.

    TMPDIR=/percorso/scratch python3 -m unittest test_sicurezza -v
"""

import hashlib
import http.client
import json
import os
import shutil
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path

os.environ["MOD_MANAGER_NO_LAUNCH"] = "1"  # mai avviare gioco o OBS dai test

import server  # noqa: E402

MAPPA = "FS25_Mappa.zip"

CARTELLE = ("ARCHIVE_DIR", "ACTIVE_GAME_DIR", "WINE_GAME_ROOT", "ROOT_PROJECT",
            "LINK_BACKUP_DIR", "PRESETS_FILE", "GAME_LAUNCHER", "DB_PATH", "PROFILI_FILE", "MODHUB_CACHE",
            "BACKUP_DISCO")

RUN_SH = """#!/bin/bash
SET_MOD="mods"
case "$1" in
    pizzeria) SET_MOD="mods-pizzeria"; shift ;;
    flat)     SET_MOD="mods"; shift ;;
esac
"""


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Base(unittest.TestCase):
    def setUp(self):
        self._orig = {k: getattr(server, k) for k in CARTELLE}
        self.tmp = Path(tempfile.mkdtemp(prefix="mm-test-"))
        root = self.tmp / "fs25"
        server.ROOT_PROJECT = root
        server.ARCHIVE_DIR = root / "mods"
        server.ACTIVE_GAME_DIR = self.tmp / "gioco" / "mods"
        server.WINE_GAME_ROOT = self.tmp / "wine" / "FarmingSimulator2025"
        server.LINK_BACKUP_DIR = self.tmp / "link_salvati"
        server.PRESETS_FILE = self.tmp / "presets.json"
        server.GAME_LAUNCHER = self.tmp / "gioco" / "run.sh"
        server.PROFILI_FILE = self.tmp / "profili.json"
        server.MODHUB_CACHE = self.tmp / "modhub_cache.json"
        server.BACKUP_DISCO = self.tmp / "EROSBACKUP"
        self._gioco_aperto = server.gioco_aperto
        server.gioco_aperto = lambda: False
        server.DB_PATH = self.tmp / "nessun.db"
        for k in CARTELLE:  # difesa: nessun percorso vero
            self.assertTrue(str(getattr(server, k)).startswith(str(self.tmp)), k)
        server.ARCHIVE_DIR.mkdir(parents=True)
        self.archivio = {}
        for n in ("FS25_A.zip", "FS25_B.zip", "FS25_C.zip"):
            p = server.ARCHIVE_DIR / n
            p.write_bytes(os.urandom(2048))
            self.archivio[n] = sha(p)
        # una mappa vera (zip con modDesc.xml)
        mappa = server.ARCHIVE_DIR / "FS25_Mappa.zip"
        with zipfile.ZipFile(mappa, "w") as zf:
            zf.writestr("modDesc.xml", '<modDesc><title><en>Mod</en></title><maps>'
                        '<map id="Mappa_Prova"><title><it>Mappa di prova</it><en>Test map</en></title></map>'
                        '</maps></modDesc>')
        self.archivio[mappa.name] = sha(mappa)
        server._MAPPE_CACHE.clear()

    def tearDown(self):
        for k, v in self._orig.items():
            setattr(server, k, v)
        server.gioco_aperto = self._gioco_aperto
        shutil.rmtree(self.tmp)  # solo la cartella temporanea del test

    def assertArchivioIntatto(self):
        for n, h in self.archivio.items():
            p = server.ARCHIVE_DIR / n
            self.assertFalse(p.is_symlink(), f"{n} è diventato un link")
            self.assertTrue(p.is_file(), f"{n} sparito")
            self.assertEqual(sha(p), h, f"{n} cambiato")


class TestAttivaMod(Base):
    def test_cartella_gioco_uguale_archivio_si_ferma(self):
        """Il caso del 17/11: la cartella del gioco è l'archivio."""
        server.ACTIVE_GAME_DIR = server.ARCHIVE_DIR
        with self.assertRaises(RuntimeError):
            server.apply_mods_to_game(["FS25_A.zip"])
        self.assertArchivioIntatto()

    def test_cartella_gioco_link_all_archivio_si_ferma(self):
        server.ACTIVE_GAME_DIR.parent.mkdir(parents=True)
        server.ACTIVE_GAME_DIR.symlink_to(server.ARCHIVE_DIR)
        with self.assertRaises(RuntimeError):
            server.apply_mods_to_game(["FS25_A.zip", "FS25_B.zip"])
        self.assertArchivioIntatto()

    def test_cartella_gioco_dentro_archivio_si_ferma(self):
        server.ACTIVE_GAME_DIR = server.ARCHIVE_DIR / "sotto"
        with self.assertRaises(RuntimeError):
            server.apply_mods_to_game(["FS25_A.zip"])
        self.assertArchivioIntatto()

    def test_file_veri_nel_gioco_non_si_cancellano(self):
        g = server.ACTIVE_GAME_DIR
        g.mkdir(parents=True)
        vero = g / "FS25_Vero.zip"
        vero.write_bytes(b"mod vera")
        (g / "FS25_B.zip").symlink_to(server.ARCHIVE_DIR / "FS25_B.zip")
        enabled, missing, det = server.apply_mods_to_game(["FS25_A.zip"])
        self.assertEqual(enabled, ["FS25_A.zip"])
        self.assertEqual(vero.read_bytes(), b"mod vera")
        self.assertIn("FS25_Vero.zip", det["file_veri_lasciati"])
        self.assertFalse((g / "FS25_B.zip").exists(), "il vecchio link doveva essere tolto")
        self.assertTrue((g / "FS25_A.zip").is_symlink())
        # elenco dei link tolti salvato
        salvato = json.loads(Path(det["elenco_link_salvato"]).read_text())
        self.assertIn("FS25_B.zip", salvato["link"])
        self.assertArchivioIntatto()

    def test_file_vero_con_stesso_nome_resta(self):
        g = server.ACTIVE_GAME_DIR
        g.mkdir(parents=True)
        (g / "FS25_A.zip").write_bytes(b"copia locale")
        enabled, _, _ = server.apply_mods_to_game(["FS25_A.zip"])
        self.assertIn("FS25_A.zip", enabled)
        self.assertFalse((g / "FS25_A.zip").is_symlink())
        self.assertEqual((g / "FS25_A.zip").read_bytes(), b"copia locale")

    def test_nomi_con_percorso_rifiutati(self):
        fuori = self.tmp / "fuori"
        fuori.mkdir()
        link_fuori = fuori / "x.zip"
        link_fuori.symlink_to(server.ARCHIVE_DIR / "FS25_C.zip")
        cattivi = ["../fuori/x.zip", "/etc/passwd", "..\\x.zip", "FS25_A.zip/../../x.zip", 7, None]
        enabled, missing, det = server.apply_mods_to_game(cattivi + ["FS25_A.zip"])
        self.assertEqual(enabled, ["FS25_A.zip"])
        self.assertTrue(link_fuori.is_symlink(), "un link fuori dalla cartella del gioco è stato toccato")
        self.assertEqual(len(det["nomi_rifiutati"]), len(cattivi))
        self.assertArchivioIntatto()

    def test_mods_non_lista(self):
        with self.assertRaises(server.RichiestaNonValida):
            server.apply_mods_to_game("FS25_A.zip")


class TestSalvataggi(Base):
    def _slot_vero(self, radice, n=1):
        d = radice / f"savegame{n}"
        d.mkdir(parents=True)
        (d / "careerSavegame.xml").write_text("<partita vera/>")
        (d / "vehicles.xml").write_text("<trattori/>")
        return d

    def test_slot_occupato_senza_conferma_non_tocca_niente(self):
        d = self._slot_vero(server.WINE_GAME_ROOT)
        with self.assertRaises(server.SlotOccupato) as ctx:
            server.create_savegame_career(slot=1, mod_list=["FS25_A.zip"], mappa=MAPPA)
        self.assertEqual(len(ctx.exception.posti), 1)
        self.assertEqual((d / "careerSavegame.xml").read_text(), "<partita vera/>")
        self.assertFalse(server.ACTIVE_GAME_DIR.exists(), "le mod non andavano toccate")

    def test_conferma_sbagliata_non_basta(self):
        self._slot_vero(server.WINE_GAME_ROOT)
        for conferma in (True, "si", 2, "1 "):
            with self.assertRaises(server.SlotOccupato):
                server.create_savegame_career(slot=1, conferma_sovrascrittura=conferma, mappa=MAPPA)

    def test_con_conferma_sposta_in_backup_senza_perdere_niente(self):
        self._slot_vero(server.WINE_GAME_ROOT)
        res = server.create_savegame_career(slot=1, mod_list=["FS25_A.zip"], conferma_sovrascrittura=1,
                                            mappa=MAPPA)
        self.assertEqual(len(res["backups"]), 1)
        for b in res["backups"]:
            b = Path(b)
            self.assertEqual(b.parent.name, server.SAVEGAME_BACKUP_NAME)
            self.assertEqual((b / "careerSavegame.xml").read_text(), "<partita vera/>")
            self.assertEqual((b / "vehicles.xml").read_text(), "<trattori/>")
        nuovo = server.WINE_GAME_ROOT / "savegame1" / "careerSavegame.xml"
        self.assertIn("<initialMoney>0</initialMoney>", nuovo.read_text())
        self.assertArchivioIntatto()

    def test_slot_libero_non_chiede_conferma(self):
        server.WINE_GAME_ROOT.mkdir(parents=True)
        res = server.create_savegame_career(slot=3, savegame_name='Prova <&> "x"', mappa=MAPPA)
        self.assertEqual(res["backups"], [])
        xml = (server.WINE_GAME_ROOT / "savegame3" / "careerSavegame.xml").read_text()
        self.assertIn("Prova &lt;&amp;&gt;", xml)

    def test_valori_non_validi(self):
        for kw in ({"slot": 0}, {"slot": 99}, {"difficulty": "IMPOSSIBILE"},
                   {"mod_list": ["../x.zip"]}, {"mappa": "FS25_A.zip"}, {"mappa": "../FS25_Mappa.zip"},
                   {"mappa": "FS25_Assente.zip"}):
            server.WINE_GAME_ROOT.mkdir(parents=True, exist_ok=True)
            kw.setdefault("mappa", MAPPA)
            with self.assertRaises(server.RichiestaNonValida, msg=str(kw)):
                server.create_savegame_career(**kw)

    def test_cartella_gioco_uguale_archivio_non_tocca_salvataggio(self):
        d = self._slot_vero(server.WINE_GAME_ROOT)
        server.ACTIVE_GAME_DIR = server.ARCHIVE_DIR
        with self.assertRaises(RuntimeError):
            server.create_savegame_career(slot=1, conferma_sovrascrittura=1, mappa=MAPPA)
        self.assertEqual((d / "careerSavegame.xml").read_text(), "<partita vera/>")
        self.assertArchivioIntatto()


class TestMappe(Base):
    def test_trova_solo_le_mappe(self):
        mappe = server.trova_mappe()
        self.assertEqual(list(mappe), [MAPPA])
        self.assertEqual(mappe[MAPPA]["map_id"], "FS25_Mappa.Mappa_Prova")
        self.assertEqual(mappe[MAPPA]["titolo"], "Mappa di prova")

    def test_partita_con_mappa_scelta(self):
        server.WINE_GAME_ROOT.mkdir(parents=True)
        res = server.create_savegame_career(slot=4, mappa=MAPPA, mod_list=["FS25_A.zip"])
        xml = (server.WINE_GAME_ROOT / "savegame4" / "careerSavegame.xml").read_text()
        self.assertIn("<mapId>FS25_Mappa.Mappa_Prova</mapId>", xml)
        self.assertIn('modName="FS25_Mappa" title="FS25_Mappa" version="1.0.0.0" required="true"', xml)
        self.assertIn('modName="FS25_A" title="FS25_A" version="1.0.0.0" required="false"', xml)
        self.assertTrue((server.ACTIVE_GAME_DIR / MAPPA).is_symlink(), "la mappa deve essere attiva")
        self.assertEqual(res["mappa"]["file"], MAPPA)

    def test_profilo_wine_mancante_non_crea_niente(self):
        with self.assertRaises(RuntimeError):
            server.create_savegame_career(slot=1, mappa=MAPPA)
        self.assertFalse(server.WINE_GAME_ROOT.exists())

    def test_non_scrive_in_documents(self):
        src = Path(server.__file__).read_text(encoding="utf-8")
        self.assertNotIn("/home/autcir/Documents/My Games", src)


class TestRimettiLink(Base):
    def _gioco_con_link(self, nomi):
        g = server.ACTIVE_GAME_DIR
        g.mkdir(parents=True, exist_ok=True)
        for n in nomi:
            (g / n).symlink_to(server.ARCHIVE_DIR / n)

    def test_rimette_i_link_di_prima(self):
        self._gioco_con_link(["FS25_A.zip", "FS25_B.zip"])
        _, _, det = server.apply_mods_to_game(["FS25_C.zip"])
        nome = Path(det["elenco_link_salvato"]).name
        res = server.rimetti_link(nome)
        self.assertEqual(sorted(res["rimessi"]), ["FS25_A.zip", "FS25_B.zip"])
        g = server.ACTIVE_GAME_DIR
        self.assertEqual(sorted(p.name for p in g.iterdir()), ["FS25_A.zip", "FS25_B.zip"])
        # anche il ritorno si può annullare: i link di prima (FS25_C) sono salvati
        salvato = json.loads(Path(res["elenco_link_salvato"]).read_text())
        self.assertEqual(list(salvato["link"]), ["FS25_C.zip"])
        self.assertArchivioIntatto()

    def test_file_veri_non_toccati_e_destinazioni_sparite_saltate(self):
        self._gioco_con_link(["FS25_A.zip"])
        _, _, det = server.apply_mods_to_game([])
        nome = Path(det["elenco_link_salvato"]).name
        g = server.ACTIVE_GAME_DIR
        (g / "FS25_A.zip").write_bytes(b"file vero")  # nel frattempo c'e' un file vero
        (g / "FS25_Altro.zip").write_bytes(b"altro vero")
        res = server.rimetti_link(nome)
        self.assertEqual(res["rimessi"], [])
        self.assertEqual((g / "FS25_A.zip").read_bytes(), b"file vero")
        self.assertEqual((g / "FS25_Altro.zip").read_bytes(), b"altro vero")
        self.assertEqual(res["saltati"][0]["nome"], "FS25_A.zip")

    def test_elenco_manomesso(self):
        server.ACTIVE_GAME_DIR.mkdir(parents=True)
        server.LINK_BACKUP_DIR.mkdir(parents=True)
        f = server.LINK_BACKUP_DIR / "link_20261118_120000_000000.json"
        fuori = self.tmp / "fuori.zip"
        fuori.write_bytes(b"x")
        f.write_text(json.dumps({"cartella": str(server.ACTIVE_GAME_DIR), "link": {
            "../evade.zip": str(fuori), "FS25_rel.zip": "relativo.zip", "FS25_Ok.zip": str(fuori)}}))
        res = server.rimetti_link(f.name)
        self.assertEqual(res["rimessi"], ["FS25_Ok.zip"])
        self.assertFalse((self.tmp / "gioco" / "evade.zip").exists())

    def test_nomi_file_non_validi(self):
        for nome in ("../x.json", "/etc/passwd", "link_x.json", None, 3):
            with self.assertRaises(server.RichiestaNonValida):
                server.rimetti_link(nome)

    def test_elenco_di_altra_cartella(self):
        server.ACTIVE_GAME_DIR.mkdir(parents=True)
        server.LINK_BACKUP_DIR.mkdir(parents=True)
        f = server.LINK_BACKUP_DIR / "link_20261118_120000_000001.json"
        f.write_text(json.dumps({"cartella": "/altra/cartella", "link": {}}))
        with self.assertRaises(server.RichiestaNonValida):
            server.rimetti_link(f.name)

    def test_archivio_protetto(self):
        server.LINK_BACKUP_DIR.mkdir(parents=True)
        f = server.LINK_BACKUP_DIR / "link_20261118_120000_000002.json"
        f.write_text(json.dumps({"cartella": str(server.ARCHIVE_DIR), "link": {"FS25_A.zip": "/x"}}))
        server.ACTIVE_GAME_DIR = server.ARCHIVE_DIR
        with self.assertRaises(RuntimeError):
            server.rimetti_link(f.name)
        self.assertArchivioIntatto()


class TestPartite(Base):
    """Profili per partita: il salvataggio dice quali mod servono, il set (da run.sh) le riceve come link."""

    def setUp(self):
        super().setUp()
        g = self.tmp / "gioco"
        g.mkdir(parents=True, exist_ok=True)
        server.GAME_LAUNCHER.write_text(RUN_SH)
        self.flat = g / "mods"
        self.pizz = g / "mods-pizzeria"
        self.flat.mkdir()
        self.pizz.mkdir()
        (self.flat / "FS25_Vero.zip").write_bytes(b"vero")           # file vero nel set
        (self.flat / "FS25_A.zip").symlink_to(server.ARCHIVE_DIR / "FS25_A.zip")
        (self.flat / "FS25_Rotto.zip").symlink_to(self.tmp / "non-esiste.zip")
        (self.flat / "FS25_C.zip").symlink_to(server.ARCHIVE_DIR / "FS25_C.zip")  # in più
        (self.flat / "FS25_Cartella").mkdir()                       # mod non zippata
        sg = server.WINE_GAME_ROOT / "savegame1"
        sg.mkdir(parents=True)
        mods = ["FS25_A", "FS25_B", "FS25_Vero", "FS25_Cartella", "FS25_Manca", "FS25_Rotto", "pdlc_x"]
        righe = "".join(f'<mod modName="{m}" title="T {m}" version="1.0" required="false"/>' for m in mods)
        (sg / "careerSavegame.xml").write_text(
            f"<careerSavegame><settings><savegameName>Flat</savegameName><mapTitle>Flat_Map</mapTitle>"
            f"<mapId>Flat_Map.Flat_Map</mapId><saveDate>2026-11-17</saveDate></settings>{righe}</careerSavegame>")
        server.MODHUB_CACHE.write_text(json.dumps({"entries": {"fs25_manca.zip": {
            "official": {"id": "123", "url": "https://www.farming-simulator.com/mod.php?mod_id=123&title=fs2025"}}}}))

    def test_set_letti_da_run_sh(self):
        sets = {v["cartella"]: v for v in server.elenco_set()}
        self.assertEqual(set(sets), {"mods", "mods-pizzeria"})
        self.assertEqual(sets["mods-pizzeria"]["comando"], "run.sh pizzeria")
        with self.assertRaises(server.RichiestaNonValida):
            server.cartella_set("../mods")
        with self.assertRaises(server.RichiestaNonValida):
            server.cartella_set("mods-sconosciuto")

    def test_piano_non_cambia_niente(self):
        prima = sorted((p.name, p.is_symlink()) for p in self.flat.iterdir())
        pl = server.piano_partita("savegame1", "mods")
        self.assertEqual(sorted(p.name for p in self.flat.iterdir()), [n for n, _ in prima])
        self.assertEqual({x["nome"] for x in pl["ok"]}, {"FS25_A", "FS25_Vero", "FS25_Cartella"})
        self.assertEqual({x["nome"] for x in pl["da_collegare"]}, {"FS25_B"})
        self.assertEqual([x["nome"] for x in pl["mancanti"]], ["FS25_Manca", "FS25_Rotto"])
        manca = pl["mancanti"][0]
        self.assertEqual(manca["mod_id"], "123")
        self.assertIn("searchMod=", manca["cerca"])
        self.assertEqual(pl["link_in_piu"], ["FS25_C.zip"])
        self.assertFalse(pl["pronto"])

    def test_applica_aggiunge_e_non_cancella_file_veri(self):
        with self.assertRaises(server.RichiestaNonValida):
            server.applica_partita("savegame1", "mods")             # senza conferma
        res = server.applica_partita("savegame1", "mods", conferma=True)
        self.assertEqual(res["collegati"], ["FS25_B"])
        # il link rotto di una mod che il salvataggio usa RESTA: così run.sh non parte (perderebbe gli oggetti)
        self.assertEqual(res["tolti"], [])
        self.assertTrue((self.flat / "FS25_Rotto.zip").is_symlink())
        self.assertEqual([m["nome"] for m in res["mancanti"]], ["FS25_Manca", "FS25_Rotto"])
        self.assertTrue((self.flat / "FS25_C.zip").is_symlink())      # in più ma resta (togli_altre=False)
        self.assertEqual((self.flat / "FS25_Vero.zip").read_bytes(), b"vero")
        self.assertTrue((self.flat / "FS25_Cartella").is_dir())
        self.assertTrue(Path(res["elenco_link_salvato"]).is_file())
        self.assertArchivioIntatto()

    def test_togli_altre_toglie_solo_link(self):
        (self.flat / "FS25_VeroInPiu.zip").write_bytes(b"x")
        server.applica_partita("savegame1", "mods", togli_altre=True, conferma=True)
        self.assertFalse((self.flat / "FS25_C.zip").exists())
        self.assertEqual((self.flat / "FS25_VeroInPiu.zip").read_bytes(), b"x")
        self.assertArchivioIntatto()

    def test_set_vuoto_usa_file_veri_di_altri_set(self):
        res = server.applica_partita("savegame1", "mods-pizzeria", conferma=True)
        self.assertIn("FS25_Vero", res["collegati"])
        self.assertEqual(os.readlink(self.pizz / "FS25_Vero.zip"), str((self.flat / "FS25_Vero.zip").resolve()))

    def test_partita_nuova_non_toglie_link_del_set(self):
        """Il caso Flat: una partita nuova nel set di un altro salvataggio non deve togliergli mod."""
        res = server.create_savegame_career(slot=5, mappa=MAPPA, mod_list=["FS25_B.zip"], set_mod="mods")
        self.assertTrue((self.flat / "FS25_A.zip").is_symlink())     # link di Flat ancora lì
        self.assertTrue((self.flat / "FS25_C.zip").is_symlink())
        self.assertTrue((self.flat / "FS25_B.zip").is_symlink())
        self.assertTrue((self.flat / MAPPA).is_symlink())
        self.assertEqual(server.leggi_profili()["savegame5"], "mods")
        self.assertEqual(res["set"], "mods")

    def test_argomento_del_launcher(self):
        self.assertEqual(server.argomento_launcher("mods"), "")
        self.assertEqual(server.argomento_launcher("mods-pizzeria"), "pizzeria")
        self.assertIsNone(server.argomento_launcher("mods-boh"))

    def test_gioco_aperto_blocca(self):
        server.gioco_aperto = lambda: True
        with self.assertRaises(server.RichiestaNonValida):
            server.applica_partita("savegame1", "mods", conferma=True)
        self.assertTrue((self.flat / "FS25_Rotto.zip").is_symlink())

    def test_profilo_e_protezione_di_attiva(self):
        server.salva_profilo("savegame1", "mods")
        self.assertEqual(server.mod_dei_salvataggi_del_set(self.flat) >= {"FS25_A.zip"}, True)
        with self.assertRaises(server.RichiestaNonValida):
            server.salva_profilo("savegame9", "mods")
        with self.assertRaises(server.RichiestaNonValida):
            server.salva_profilo("savegame1", "../x")

    def test_slot_non_validi(self):
        for slot in ("../savegame1", "savegame1/..", "x", None):
            with self.assertRaises(server.RichiestaNonValida):
                server.piano_partita(slot, "mods")


class TestScaricaEBackup(Base):
    def test_scarica_valida_prima_di_andare_in_rete(self):
        for nome, mid in (("../x", "1"), ("FS25_A", "1"), ("FS25_Nuova", "abc"), ("FS25_Nuova", None)):
            with self.assertRaises(server.RichiestaNonValida):
                server.scarica_mod(nome, mid)
        self.assertArchivioIntatto()

    def test_backup_non_montato(self):
        self.assertFalse(server.stato_backup()["montato"])
        with self.assertRaises(server.RichiestaNonValida):
            server.avvia_backup()

    def test_copia_di_sicurezza_non_cancella(self):
        import backup_mods
        g = self.tmp / "gioco"
        g.mkdir(parents=True, exist_ok=True)
        server.GAME_LAUNCHER.write_text(RUN_SH)
        (g / "mods").mkdir()
        (g / "mods" / "FS25_SoloGioco.zip").write_bytes(b"solo qui")
        (g / "mods" / "FS25_A.zip").symlink_to(server.ARCHIVE_DIR / "FS25_A.zip")
        dest = self.tmp / "disco" / "fs25-mods"
        dest.parent.mkdir()
        e1 = backup_mods.copia(dest)
        self.assertEqual((dest / "set" / "mods" / "FS25_SoloGioco.zip").read_bytes(), b"solo qui")
        self.assertFalse((dest / "set" / "mods" / "FS25_A.zip").exists())  # i link non si copiano
        self.assertEqual(sha(dest / "archivio" / "FS25_A.zip"), self.archivio["FS25_A.zip"])
        (dest / "extra.txt").write_text("resta")
        e2 = backup_mods.copia(dest)
        self.assertEqual(e2["copiati"], 0)
        self.assertGreater(e1["copiati"], 0)
        (server.ARCHIVE_DIR / "FS25_A.zip").write_bytes(b"versione nuova")
        e3 = backup_mods.copia(dest)
        self.assertEqual(e3["aggiornati"], 1)
        vecchie = list((dest / "archivio").glob("FS25_A.zip.vecchio-*"))
        self.assertEqual(len(vecchie), 1)
        self.assertEqual(sha(vecchie[0]), self.archivio["FS25_A.zip"])
        self.assertEqual((dest / "extra.txt").read_text(), "resta")
        self.archivio["FS25_A.zip"] = sha(server.ARCHIVE_DIR / "FS25_A.zip")


class TestCodice(unittest.TestCase):
    def test_nessuna_cancellazione_ricorsiva_nel_server(self):
        for f in ("server.py", "backup_mods.py"):
            src = (Path(server.__file__).parent / f).read_text(encoding="utf-8")
            for vietato in ("rmtree", "os.remove(", "send2trash", "os.rmdir("):
                self.assertNotIn(vietato, src, f"{vietato} in {f}: cancellazioni vietate")


class TestHttp(Base):
    def setUp(self):
        super().setUp()
        self.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.ModManagerHandler)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        super().tearDown()

    def req(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        h = {"Content-Type": "application/json"}
        h.update(headers or {})
        c.request(method, path, body=json.dumps(body) if isinstance(body, dict) else body, headers=h)
        r = c.getresponse()
        data = r.read()
        c.close()
        try:
            return r.status, json.loads(data)
        except ValueError:
            return r.status, data

    def test_status(self):
        st, data = self.req("GET", "/api/status")
        self.assertEqual(st, 200)
        self.assertTrue(data["cartella_gioco_sicura"])

    def test_sito_esterno_bloccato(self):
        st, _ = self.req("POST", "/api/activate", {"mods": []}, {"Origin": "https://sito-cattivo.example"})
        self.assertEqual(st, 403)

    def test_host_esterno_bloccato(self):
        st, _ = self.req("GET", "/api/status", headers={"Host": "cattivo.example:8025"})
        self.assertEqual(st, 403)

    def test_testo_semplice_rifiutato(self):
        st, _ = self.req("POST", "/api/activate", '{"mods": []}', {"Content-Type": "text/plain"})
        self.assertEqual(st, 400)

    def test_json_rotto(self):
        st, data = self.req("POST", "/api/activate", "{non json")
        self.assertEqual(st, 400)
        self.assertFalse(data["success"])

    def test_slot_occupato_409(self):
        d = server.WINE_GAME_ROOT / "savegame1"
        d.mkdir(parents=True)
        (d / "careerSavegame.xml").write_text("<vera/>")
        st, data = self.req("POST", "/api/create_game", {"slot": 1, "mods": [], "launch_game": True, "map": MAPPA},
                            {"Origin": f"http://127.0.0.1:{self.port}"})
        self.assertEqual(st, 409)
        self.assertTrue(data["serve_conferma"])
        self.assertEqual((d / "careerSavegame.xml").read_text(), "<vera/>")

    def test_archivio_protetto_via_api(self):
        server.ACTIVE_GAME_DIR = server.ARCHIVE_DIR
        st, data = self.req("POST", "/api/activate", {"mods": ["FS25_A.zip"]})
        self.assertEqual(st, 500)
        self.assertIn("archivio", data["error"])
        self.assertArchivioIntatto()

    def test_api_mappe_e_link(self):
        st, data = self.req("GET", "/api/maps")
        self.assertEqual(st, 200)
        self.assertEqual([m["file"] for m in data["mappe"]], [MAPPA])
        st, data = self.req("GET", "/api/link_salvati")
        self.assertEqual((st, data["elenchi"]), (200, []))
        st, _ = self.req("POST", "/api/rimetti_link", {"file": "../x.json"})
        self.assertEqual(st, 400)

    def test_attiva_protegge_le_mod_del_salvataggio(self):
        g = server.ACTIVE_GAME_DIR
        g.mkdir(parents=True)
        server.GAME_LAUNCHER.write_text(RUN_SH)
        (g / "FS25_A.zip").symlink_to(server.ARCHIVE_DIR / "FS25_A.zip")
        sg = server.WINE_GAME_ROOT / "savegame1"
        sg.mkdir(parents=True)
        (sg / "careerSavegame.xml").write_text('<careerSavegame><mod modName="FS25_A"/></careerSavegame>')
        server.salva_profilo("savegame1", "mods")
        st, data = self.req("POST", "/api/activate", {"mods": ["FS25_B.zip"]})
        self.assertEqual(st, 409)
        self.assertEqual(data["mod_del_salvataggio_tolte"], ["FS25_A.zip"])
        self.assertTrue((g / "FS25_A.zip").is_symlink())
        st, _ = self.req("POST", "/api/activate", {"mods": ["FS25_B.zip"], "forza": True})
        self.assertEqual(st, 200)

    def test_api_partite(self):
        server.GAME_LAUNCHER.parent.mkdir(parents=True, exist_ok=True)
        server.GAME_LAUNCHER.write_text(RUN_SH)
        st, data = self.req("GET", "/api/partite")
        self.assertEqual(st, 200)
        self.assertEqual(len(data["set"]), 2)
        st, _ = self.req("GET", "/api/piano?slot=../x&set=mods")
        self.assertEqual(st, 400)
        st, data = self.req("GET", "/api/backup")
        self.assertFalse(data["montato"])

    def test_file_sorgente_non_serviti(self):
        st, _ = self.req("GET", "/server.py")
        self.assertEqual(st, 404)


class TestFileDiTerzi(unittest.TestCase):
    """Icone degli zip (file di terzi) e export CSV: nessun formato indovinato, nessuna formula."""

    def test_imagemagick_formato_esplicito(self):
        import scan_mods
        cmd = scan_mods.magick_cmd("magick", Path("/x/a.dds"), ".dds", Path("/x/o.png"))
        self.assertEqual(cmd[1], "dds:/x/a.dds")
        self.assertEqual(cmd[-1], "png:/x/o.png")
        for vietato in (".svg", ".mvg", ".txt", ".img", ""):
            with self.assertRaises(KeyError):
                scan_mods.magick_cmd("magick", Path("/x/a" + vietato), vietato, Path("/x/o.png"))
        self.assertTrue((scan_mods.MAGICK_POLICY_DIR / "policy.xml").is_file())
        self.assertEqual(scan_mods.magick_env()["MAGICK_CONFIGURE_PATH"], str(scan_mods.MAGICK_POLICY_DIR))

    def test_icona_svg_rifiutata(self):
        import scan_mods
        tmp = Path(tempfile.mkdtemp(prefix="mm-icone-"))
        vecchia = scan_mods.ICON_DIR
        try:
            scan_mods.ICON_DIR = tmp / "icons"
            z = tmp / "mod.zip"
            with zipfile.ZipFile(z, "w") as zf:
                zf.writestr("icon_x.svg", "<svg/>")
            with zipfile.ZipFile(z) as zf:
                self.assertIsNone(scan_mods.extract_icon(zf, {"sha256": "x"}, "icon_x.svg", "id1", {}, False))
            self.assertFalse((tmp / "icons" / "id1.png").exists())
        finally:
            scan_mods.ICON_DIR = vecchia
            shutil.rmtree(tmp, ignore_errors=True)

    @unittest.skipUnless(shutil.which("magick"), "ImageMagick non installato")
    def test_policy_blocca_mvg_e_text(self):
        import subprocess
        import scan_mods
        tmp = Path(tempfile.mkdtemp(prefix="mm-policy-"))
        try:
            (tmp / "x.mvg").write_text("push graphic-context\nviewbox 0 0 10 10\npop graphic-context\n")
            (tmp / "t.txt").write_text("ciao")
            for src in (f"mvg:{tmp / 'x.mvg'}", f"text:{tmp / 't.txt'}", f"@{tmp / 't.txt'}"):
                r = subprocess.run(["magick", src, f"png:{tmp / 'o.png'}"], env=scan_mods.magick_env(),
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
                self.assertNotEqual(r.returncode, 0, src)
                self.assertFalse((tmp / "o.png").exists(), src)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    @unittest.skipUnless(shutil.which("node"), "node non installato")
    def test_csv_niente_formule(self):
        import re
        import subprocess
        src = (Path(server.__file__).parent / "assets" / "app.js").read_text(encoding="utf-8")
        m = re.search(r"const escapeCell = value => \{.*?\n    \};", src, re.S)
        self.assertIsNotNone(m, "escapeCell non trovata in app.js")
        js = m.group(0) + """
const casi = ['=1+1', '+1', '-1', '@SUM(A1)', '\\tx', '\\nx', 'ok', 'a"b', 12];
console.log(JSON.stringify(casi.map(escapeCell)));"""
        out = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=30).stdout)
        self.assertEqual(out[:4], ['"\'=1+1"', '"\'+1"', '"\'-1"', '"\'@SUM(A1)"'])
        self.assertTrue(out[4].startswith('"\'\t') and out[5].startswith('"\'\n'))
        self.assertEqual(out[6:], ['"ok"', '"a""b"', '"12"'])


if __name__ == "__main__":
    unittest.main()
