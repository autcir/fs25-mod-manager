#!/usr/bin/env python3
"""
Mod Manager FS25: server locale (solo 127.0.0.1).
Serve la dashboard, cerca mod nel database KingMods locale, prepara un salvataggio nuovo
e attiva le mod nel gioco con link simbolici.

Regole di sicurezza (dal 18/11/2026, dopo la perdita di 96 mod del 17/11):
- non cancella mai file veri: toglie solo link simbolici nella cartella mod del gioco;
- prima di togliere i link ne salva l'elenco in data/link_salvati/ (si possono rimettere);
- si ferma se la cartella del gioco coincide con l'archivio delle mod;
- un salvataggio esistente non si cancella mai: si sposta in BACKUP_SAVEGAMES e solo dopo
  conferma esplicita dall'interfaccia (campo "conferma_sovrascrittura" = numero dello slot);
- "rimetti i link di prima" rimette solo link verso file che esistono e non tocca file veri.
"""

import sys
import os
import json
import sqlite3
import subprocess
import mimetypes
import urllib.parse
import zipfile
import xml.etree.ElementTree as ET
import re
from xml.sax.saxutils import escape as xml_escape
from datetime import datetime
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import config

BASE_DIR = Path(__file__).resolve().parent
# Tutti i percorsi vengono da config.py (variabili FS25_* o ~/.config/fs25-mod-manager/config.json).
ROOT_PROJECT = config.library_dir()          # contiene mods/ (archivio), BACKUP_MODS/, mods-bck/
ARCHIVE_DIR = ROOT_PROJECT / "mods"
ACTIVE_GAME_DIR = config.game_mods_dir()     # la cartella da cui il gioco legge le mod
# La partita nuova si scrive solo qui: è il profilo che il gioco (Proton) legge davvero.
WINE_GAME_ROOT = config.profile_dir()
GAME_LAUNCHER = config.launcher()            # None = nessun lanciatore configurato
DB_PATH = config.kingmods_db()
NICKNAME = config.nickname()
FARM_NAME = config.farm_name()
PRESETS_FILE = BASE_DIR / "data" / "presets.json"
LINK_BACKUP_DIR = BASE_DIR / "data" / "link_salvati"
SAVEGAME_BACKUP_NAME = "BACKUP_SAVEGAMES"
DIFFICULTIES = {"EASY", "NORMAL", "HARD"}
MAX_SLOT = 20
_MOD_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.+()&'-]*\.zip$")


class RichiestaNonValida(ValueError):
    """Dati sbagliati dall'interfaccia: risposta 400."""


class SlotOccupato(Exception):
    """Lo slot esiste già e manca la conferma esplicita: risposta 409."""

    def __init__(self, slot, posti):
        super().__init__(f"lo slot {slot} esiste già")
        self.slot = slot
        self.posti = posti


def nome_mod_valido(nome):
    """Solo nomi di file .zip semplici: niente cartelle, niente '..', niente percorsi assoluti."""
    return (isinstance(nome, str) and len(nome) <= 200 and "/" not in nome and "\\" not in nome
            and ".." not in nome and _MOD_NAME_RE.match(nome) is not None)

DEFAULT_PRESETS = {
    "italia_mediterranea": {
        "name": "🇮🇹 Sopravvivenza Italia Mediterranea",
        "map": "FS25_Mediterranean_Italy.zip",
        "description": "Pacchetto storico italiano da 0€: Fiat 480, Fiatagri 110-90, Alpego, Dondi, produzioni piccole e realismo.",
        "mods": [
            "FS25_Mediterranean_Italy.zip",
            "FS25_Fiat_480.zip",
            "FS25_Fiatagri_110_90.zip",
            "FS25_Fiatagri_160180_90.zip",
            "FS25_fiatagriSeriesPack.zip",
            "FS25_fiatSeries180_90JT.zip",
            "FS25_lamborghiniMachVRT.zip",
            "FS25_DucatoFiat19tdi.zip",
            "FS25_DucatoFiatPickupTruck.zip",
            "FS25_Fiat682_N4.zip",
            "FS25_Fiat190_48_TurboStar.zip",
            "FS25_Alpego_JetM.zip",
            "FS25_Dondi800Series.zip",
            "FS25_DoubleWeightFiat.zip",
            "FS25_Trincia_Fiat_Hesston.zip",
            "FS25_two_wheel_trailer.zip",
            "FS25_Flatbed_Trailer.zip",
            "FS25_UniaGrudziadzUPlows.zip",
            "FS25_UsedEquipmentYards.zip",
            "FS25_orchardsAndGreenhouses_crossplay.zip",
            "FS25_smallFarmProduction.zip",
            "FS25_Raisinproductionpack.zip",
            "FS25_FloorWeightStation.zip",
            "FS25_additionalFieldInfo.zip",
            "FS25_interactiveControl.zip",
            "FS25_RealisticFirstPerson.zip",
            "FS25_GPSPlus.zip",
            "FS25_AutoDrive.zip",
            "FS25_Courseplay.zip",
            "FS25_AnimalFoodCalculator.zip",
            "FS25_AutomaticWater_Animals_Greenhouses.zip"
        ]
    },
    "tutte_le_mod": {
        "name": "📦 Tutte le Mod (Archivio Completo)",
        "map": "",
        "description": "Tutte le 240 mod attivate nel gioco contemporaneamente.",
        "mods": []
    }
}


def load_presets():
    if PRESETS_FILE.exists():
        try:
            with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_PRESETS


def save_presets(data):
    PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_active_game_mods():
    if not ACTIVE_GAME_DIR.is_dir():
        return []
    active = []
    for f in ACTIVE_GAME_DIR.glob("*.zip"):
        active.append(f.name)
    return sorted(active)


def _stessa_cartella_o_dentro(a, b):
    a, b = a.resolve(), b.resolve()
    return a == b or b in a.parents or a in b.parents


def salva_elenco_link(cartella):
    """Scrive l'elenco dei link simbolici attuali (nome -> destinazione) prima di toglierli."""
    links = {}
    for f in cartella.iterdir():
        if f.is_symlink():
            links[f.name] = os.readlink(f)
    if not links:
        return None
    LINK_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    out = LINK_BACKUP_DIR / f"link_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    out.write_text(json.dumps({"cartella": str(cartella), "link": links}, indent=1, ensure_ascii=False),
                   encoding="utf-8")
    return out


def apply_mods_to_game(mod_list):
    """Attiva le mod scelte con link simbolici. Non cancella mai file veri.

    Ritorna (attivate, mancanti, dettagli) dove dettagli ha: file_veri_lasciati, nomi_rifiutati,
    elenco_link_salvato.
    """
    if not isinstance(mod_list, list):
        raise RichiestaNonValida("'mods' deve essere una lista di nomi .zip")
    # 18/11/2026: il 17/11 alle 18:01 la cartella del gioco puntava all'archivio e questa funzione ha
    # cancellato 96 zip veri lasciando link a se stessi. Regola: mai toccare l'archivio, mai cancellare file veri.
    if _stessa_cartella_o_dentro(ACTIVE_GAME_DIR, ARCHIVE_DIR):
        raise RuntimeError("cartella mod del gioco = archivio (o una dentro l'altra): mi fermo, non tocco niente")
    ACTIVE_GAME_DIR.mkdir(parents=True, exist_ok=True)

    rifiutati = sorted({m for m in mod_list if not nome_mod_valido(m)}, key=str)
    richieste = {m for m in mod_list if nome_mod_valido(m)}

    # Elenco dei link attuali salvato prima di toglierli: si possono rimettere a mano.
    elenco = salva_elenco_link(ACTIVE_GAME_DIR)

    # Rimuovi solo i vecchi symlink (mai file veri)
    for f in list(ACTIVE_GAME_DIR.iterdir()):
        try:
            if f.is_symlink():
                f.unlink()
        except Exception as e:
            print(f"Errore rimozione link {f.name}: {e}")

    enabled = []
    missing = []
    for m in sorted(richieste):
        src = ARCHIVE_DIR / m
        if not src.is_file():
            bck = sorted(p for p in ROOT_PROJECT.glob(f"BACKUP_MODS/**/{m}")
                         if p.is_file() and "_DOPPIONI_QUARANTENA" not in p.parts)
            if bck:
                src = bck[0]

        dst = ACTIVE_GAME_DIR / m
        if not src.is_file() or src.resolve() == dst.absolute():
            missing.append(m)
            continue
        try:
            if dst.exists() and not dst.is_symlink():
                enabled.append(m)  # file vero già nel gioco: lo lascio
                continue
            if dst.is_symlink():
                dst.unlink()
            dst.symlink_to(src.resolve())
            enabled.append(m)
        except Exception as e:
            print(f"Errore symlink {m}: {e}")
            missing.append(m)

    # File veri non scelti: restano nel gioco (non li cancelliamo). Li diciamo all'interfaccia.
    veri_lasciati = sorted(f.name for f in ACTIVE_GAME_DIR.glob("*.zip")
                           if not f.is_symlink() and f.name not in richieste)
    dettagli = {
        "file_veri_lasciati": veri_lasciati,
        "nomi_rifiutati": rifiutati,
        "elenco_link_salvato": str(elenco) if elenco else None,
    }
    return enabled, missing, dettagli


def _sposta_in_backup(cartella_slot, timestamp):
    """Sposta (non copia e cancella) uno slot esistente in <radice>/BACKUP_SAVEGAMES/."""
    dest_parent = cartella_slot.parent / SAVEGAME_BACKUP_NAME
    dest_parent.mkdir(parents=True, exist_ok=True)
    dest = dest_parent / f"{cartella_slot.name}_{timestamp}"
    n = 1
    while dest.exists():
        dest = dest_parent / f"{cartella_slot.name}_{timestamp}_{n}"
        n += 1
    os.rename(cartella_slot, dest)  # stessa cartella madre = stesso disco: spostamento atomico
    return dest


def slot_occupati(slot):
    posti = []
    d = WINE_GAME_ROOT / f"savegame{slot}"
    if d.exists() or d.is_symlink():
        posti.append(str(d))
    return posti


# ---------------------------------------------------------------- mappe
_MAPPE_CACHE = {}
_LINK_FILE_RE = re.compile(r"^link_\d{8}_\d{6}_\d{6}\.json$")
MAPPA_PREDEFINITA = "FS25_Mediterranean_Italy.zip"


def _testo_l10n(el):
    """<title><it>..</it><en>..</en></title> oppure testo semplice."""
    if el is None:
        return ""
    for lingua in ("it", "en"):
        x = el.find(lingua)
        if x is not None and (x.text or "").strip():
            return x.text.strip()
    for x in el:
        if (x.text or "").strip():
            return x.text.strip()
    return (el.text or "").strip()


def leggi_mappa(zip_path):
    """Se lo zip è una mappa ritorna {file, map_id, titolo}; altrimenti None. Legge soltanto."""
    try:
        st = zip_path.stat()
    except OSError:
        return None
    chiave = (str(zip_path), st.st_mtime_ns, st.st_size)
    if chiave in _MAPPE_CACHE:
        return _MAPPE_CACHE[chiave]
    risultato = None
    try:
        with zipfile.ZipFile(zip_path) as zf:
            info = zf.getinfo("modDesc.xml")
            if info.file_size <= 2_000_000:
                root = ET.fromstring(zf.read(info))
                m = root.find("maps/map")
                if m is not None and m.get("id"):
                    stem = zip_path.name[:-4]
                    titolo = _testo_l10n(m.find("title")) or _testo_l10n(root.find("title")) or stem
                    if titolo.startswith("$l10n_"):
                        titolo = _testo_l10n(root.find("title")) or stem
                    risultato = {"file": zip_path.name, "map_id": f"{stem}.{m.get('id')}", "titolo": titolo}
    except (KeyError, zipfile.BadZipFile, ET.ParseError, OSError, RuntimeError):
        risultato = None
    _MAPPE_CACHE[chiave] = risultato
    return risultato


def trova_mappe():
    """Mappe disponibili nell'archivio e in BACKUP_MODS (prima copia per nome di file)."""
    mappe = {}
    candidati = sorted(ARCHIVE_DIR.glob("*.zip")) + sorted(
        p for p in ROOT_PROJECT.glob("BACKUP_MODS/**/*.zip") if "_DOPPIONI_QUARANTENA" not in p.parts)
    for z in candidati:
        if z.name in mappe or not nome_mod_valido(z.name) or not z.is_file():
            continue
        info = leggi_mappa(z)
        if info:
            mappe[z.name] = info
    return mappe


# ---------------------------------------------------------------- link salvati
def elenco_link_salvati():
    if not LINK_BACKUP_DIR.is_dir():
        return []
    out = []
    for f in sorted(LINK_BACKUP_DIR.glob("link_*.json"), reverse=True):
        if not _LINK_FILE_RE.match(f.name):
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            out.append({"file": f.name, "cartella": d.get("cartella"), "quanti": len(d.get("link", {}))})
        except (OSError, ValueError):
            continue
    return out


def rimetti_link(nome_file):
    """Rimette i link salvati in un file di data/link_salvati/. Non tocca mai file veri.

    Prima salva i link di adesso (così anche questo passo si può annullare)."""
    if not isinstance(nome_file, str) or not _LINK_FILE_RE.match(nome_file):
        raise RichiestaNonValida("nome del file salvato non valido")
    f = LINK_BACKUP_DIR / nome_file
    if not f.is_file():
        raise RichiestaNonValida("elenco salvato non trovato")
    try:
        dati = json.loads(f.read_text(encoding="utf-8"))
        link = dict(dati["link"])
    except (OSError, ValueError, KeyError, TypeError):
        raise RichiestaNonValida("elenco salvato illeggibile")
    if _stessa_cartella_o_dentro(ACTIVE_GAME_DIR, ARCHIVE_DIR):
        raise RuntimeError("cartella mod del gioco = archivio: mi fermo, non tocco niente")
    if Path(str(dati.get("cartella", ""))).resolve() != ACTIVE_GAME_DIR.resolve():
        raise RichiestaNonValida("l'elenco è di un'altra cartella del gioco")

    elenco_adesso = salva_elenco_link(ACTIVE_GAME_DIR)
    for x in list(ACTIVE_GAME_DIR.iterdir()):
        if x.is_symlink():
            x.unlink()

    rimessi, saltati = [], []
    gioco = ACTIVE_GAME_DIR.resolve()
    for nome, dest in sorted(link.items()):
        dst = ACTIVE_GAME_DIR / str(nome)
        target = Path(str(dest))
        if not nome_mod_valido(nome) or not target.is_absolute():
            saltati.append({"nome": str(nome), "motivo": "nome o destinazione non validi"})
            continue
        if not target.is_file() or target.resolve().parent == gioco:
            saltati.append({"nome": nome, "motivo": "il file di destinazione non c'è più"})
            continue
        if dst.exists() or dst.is_symlink():
            saltati.append({"nome": nome, "motivo": "c'è già un file vero con questo nome"})
            continue
        dst.symlink_to(target)
        rimessi.append(nome)
    return {"success": True, "rimessi": rimessi, "saltati": saltati,
            "elenco_link_salvato": str(elenco_adesso) if elenco_adesso else None}


def create_savegame_career(
    slot=1,
    savegame_name="Survival Italia Mediterranea",
    starting_money=0,
    starting_loan=0,
    difficulty="HARD",
    fruit_destruction=True,
    plowing_required=True,
    stones=True,
    weeds=True,
    lime=True,
    snow=True,
    dirt_interval=3,
    fuel_usage=2,
    days_per_period=1,
    time_scale=5.0,
    mod_list=None,
    conferma_sovrascrittura=None,
    mappa=MAPPA_PREDEFINITA,
    set_mod=None,
):
    if mod_list is None:
        mod_list = []
    if not isinstance(slot, int) or not 1 <= slot <= MAX_SLOT:
        raise RichiestaNonValida(f"slot deve essere un numero da 1 a {MAX_SLOT}")
    difficulty = str(difficulty).upper()
    if difficulty not in DIFFICULTIES:
        raise RichiestaNonValida("difficoltà: EASY, NORMAL o HARD")
    if not isinstance(mod_list, list) or not all(nome_mod_valido(m) for m in mod_list):
        raise RichiestaNonValida("'mods' deve contenere solo nomi di file .zip")
    if _stessa_cartella_o_dentro(ACTIVE_GAME_DIR, ARCHIVE_DIR):
        raise RuntimeError("cartella mod del gioco = archivio: mi fermo prima di toccare il salvataggio")

    if not WINE_GAME_ROOT.is_dir():
        raise RuntimeError(f"profilo del gioco non trovato: {WINE_GAME_ROOT}")
    # Set di mod (cartella di run.sh) in cui mettere le mod della partita nuova. Se manca, quello del Mod Manager.
    cartella_mod = cartella_set(set_mod) if set_mod else ACTIVE_GAME_DIR
    if not nome_mod_valido(mappa):
        raise RichiestaNonValida("mappa non valida")
    info_mappa = trova_mappe().get(mappa)
    if not info_mappa:
        raise RichiestaNonValida(f"mappa {mappa} non trovata nell'archivio")
    if mappa not in mod_list:
        mod_list = [mappa] + list(mod_list)

    savegame_dir = WINE_GAME_ROOT / f"savegame{slot}"
    backups = []

    # 1. Slot già usato: si sposta in BACKUP_SAVEGAMES, mai cancellato, e solo con conferma esplicita.
    posti = slot_occupati(slot)
    if posti:
        if str(conferma_sovrascrittura) != str(slot):
            raise SlotOccupato(slot, posti)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backups.append(str(_sposta_in_backup(savegame_dir, timestamp)))

    savegame_dir.mkdir(exist_ok=False)

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_fmt = datetime.now().strftime("%d/%m/%Y")

    # 2. Generate careerSavegame.xml
    mod_lines = []
    for m in mod_list:
        stem = m.replace(".zip", "")
        req = "true" if m == mappa else "false"
        mod_lines.append(f'    <mod modName="{stem}" title="{stem}" version="1.0.0.0" required="{req}" fileHash="00000000000000000000000000000000"/>')
    mods_xml = "\n".join(mod_lines)

    fruit_destr_str = "true" if fruit_destruction else "false"
    plow_str = "true" if plowing_required else "false"
    stones_str = "true" if stones else "false"
    weeds_str = "true" if weeds else "false"
    lime_str = "true" if lime else "false"
    snow_str = "true" if snow else "false"

    career_xml = f"""<?xml version="1.0" encoding="utf-8" standalone="no"?>
<careerSavegame revision="2" valid="true">
    <settings>
        <savegameName>{xml_escape(str(savegame_name))[:120]}</savegameName>
        <creationDate>{today_str}</creationDate>
        <mapId>{xml_escape(info_mappa["map_id"])}</mapId>
        <mapTitle>{xml_escape(info_mappa["titolo"])}</mapTitle>
        <saveDateFormatted>{today_fmt}</saveDateFormatted>
        <saveDate>{today_str}</saveDate>
        <initialMoney>{int(starting_money)}</initialMoney>
        <initialLoan>{int(starting_loan)}</initialLoan>
        <economicDifficulty>{difficulty}</economicDifficulty>
        <hasInitiallyOwnedFarmlands>true</hasInitiallyOwnedFarmlands>
        <loadDefaultFarm>true</loadDefaultFarm>
        <startWithGuidedTour>false</startWithGuidedTour>
        <trafficEnabled>true</trafficEnabled>
        <stopAndGoBraking>true</stopAndGoBraking>
        <trailerFillLimit>false</trailerFillLimit>
        <automaticMotorStartEnabled>true</automaticMotorStartEnabled>
        <growthMode>1</growthMode>
        <plannedDaysPerPeriod>{days_per_period}</plannedDaysPerPeriod>
        <fruitDestruction>{fruit_destr_str}</fruitDestruction>
        <plowingRequiredEnabled>{plow_str}</plowingRequiredEnabled>
        <stonesEnabled>{stones_str}</stonesEnabled>
        <weedsEnabled>{weeds_str}</weedsEnabled>
        <limeRequired>{lime_str}</limeRequired>
        <isSnowEnabled>{snow_str}</isSnowEnabled>
        <fuelUsage>{fuel_usage}</fuelUsage>
        <helperBuyFuel>false</helperBuyFuel>
        <helperBuySeeds>false</helperBuySeeds>
        <helperBuyFertilizer>false</helperBuyFertilizer>
        <helperSlurrySource>1</helperSlurrySource>
        <helperManureSource>1</helperManureSource>
        <dirtInterval>{dirt_interval}</dirtInterval>
        <timeScale>{float(time_scale):.6f}</timeScale>
        <autoSaveInterval>15</autoSaveInterval>
    </settings>
    <statistics>
        <money>{float(starting_money):.6f}</money>
        <playTime>0.000000</playTime>
    </statistics>
{mods_xml}
</careerSavegame>
"""
    (savegame_dir / "careerSavegame.xml").write_text(career_xml, encoding="utf-8")

    # 3. Generate farms.xml
    farms_xml = f"""<?xml version="1.0" encoding="utf-8" standalone="no"?>
<farms>
    <farm farmId="1" name="{xml_escape(FARM_NAME, {chr(34): '&quot;'})}" color="1" loan="{float(starting_loan):.6f}" money="{float(starting_money):.6f}">
        <players>
            <player id="1" lastNickname="{xml_escape(NICKNAME, {chr(34): '&quot;'})}" buyVehicle="true" sellVehicle="true" buyPlaceable="true" sellPlaceable="true" manageContracts="true" tradeAnimals="true" createFields="true" land="true" hireAssistant="true" resetVehicle="true" manageProductions="true" updateFarm="true" manageRights="true"/>
        </players>
    </farm>
</farms>
"""
    (savegame_dir / "farms.xml").write_text(farms_xml, encoding="utf-8")

    # 4. Generate environment.xml
    env_xml = f"""<?xml version="1.0" encoding="utf-8" standalone="no"?>
<environment>
    <dayTime>480.000000</dayTime>
    <currentDay>1</currentDay>
    <currentMonotonicDay>1</currentMonotonicDay>
    <realHourTimer>0.000000</realHourTimer>
    <daysPerPeriod>{days_per_period}</daysPerPeriod>
</environment>
"""
    (savegame_dir / "environment.xml").write_text(env_xml, encoding="utf-8")

    # 5. Mod della partita: si AGGIUNGONO link nel set scelto, non si toglie niente (il set può servire ad
    #    altri salvataggi: togliere link lì farebbe sparire oggetti). Poi l'abbinamento slot -> set è ricordato.
    enabled, missing = aggiungi_link(cartella_mod, mod_list)
    dettagli = {"file_veri_lasciati": []}
    if set_mod:
        salva_profilo(savegame_dir.name, set_mod)

    return {
        "success": True,
        "slot": slot,
        "savegame_name": savegame_name,
        "starting_money": starting_money,
        "starting_loan": starting_loan,
        "difficulty": difficulty,
        "mappa": info_mappa,
        "backup": backups[0] if backups else None,
        "backups": backups,
        "enabled_mods_count": len(enabled),
        "missing": missing,
        "file_veri_lasciati": dettagli["file_veri_lasciati"],
        "savegame_dir": str(savegame_dir),
        "set": cartella_mod.name,
    }


def aggiungi_link(cartella, mod_list):
    """Aggiunge link alle mod scelte senza togliere niente. Ritorna (presenti_o_collegate, mancanti)."""
    if _stessa_cartella_o_dentro(cartella, ARCHIVE_DIR):
        raise RuntimeError("il set coincide con l'archivio: mi fermo")
    cartella.mkdir(parents=True, exist_ok=True)
    ok, mancanti = [], []
    for m in mod_list:
        if not nome_mod_valido(m):
            mancanti.append(str(m))
            continue
        nome = m[:-4]
        stato = _presente(cartella, nome)
        if stato in ("link", "file", "cartella"):
            ok.append(m)
            continue
        fonte = trova_fonte(nome, esclusa=cartella)
        if not fonte:
            mancanti.append(m)
            continue
        dst = cartella / m
        if dst.is_symlink():
            dst.unlink()  # link rotto della stessa mod
        dst.symlink_to(fonte.resolve())
        ok.append(m)
    return ok, mancanti


def query_kingmods(query, limit=20):
    if not DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT name, category, rating_stars, downloads, url, description, author "
            "FROM mods WHERE (name LIKE ? OR description LIKE ? OR brand LIKE ?) AND category != 'Unknown' "
            "ORDER BY downloads DESC LIMIT ?",
            (f"%{query}%", f"%{query}%", f"%{query}%", limit)
        )
        rows = cur.fetchall()
        results = []
        for r in rows:
            results.append({
                "name": r[0],
                "category": r[1],
                "rating": r[2],
                "downloads": r[3],
                "url": r[4],
                "description": r[5][:180] + "..." if r[5] else "",
                "author": r[6]
            })
        conn.close()
        return results
    except Exception as e:
        print("Errore DB KingMods:", e)
        return []


# ---------------------------------------------------------------- partite e set di mod
# Un "set" è una cartella di mod accanto al lanciatore (es. mods = una partita, mods-altra = un'altra).
# Fonte unica: i set si leggono da run.sh (riga SET_MOD="..." e righe `nome) SET_MOD="cartella"`), così il
# Mod Manager e i lanciatori usano gli stessi nomi e le stesse cartelle senza cambiare run.sh.
PROFILI_FILE = BASE_DIR / "data" / "profili.json"
BACKUP_DISCO = config.backup_dir()           # None = copia di sicurezza disattivata
BACKUP_SOTTOCARTELLA = "fs25-mods"
MODHUB_CACHE = BASE_DIR / "data" / "modhub_cache.json"
MODHUB_REFERER = "https://www.farming-simulator.com/"
_SET_NOME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_CDN_RE = re.compile(r'href="(https://cdn\d*\.giants-software\.com/modHub/storage/\d+/([A-Za-z0-9_.+()&\'-]+\.zip))"')


def game_dir():
    return GAME_LAUNCHER.parent


def set_dal_launcher():
    """{nome: cartella} letti da run.sh. 'predefinito' è il set usato da `run.sh` senza argomenti.

    Senza lanciatore configurato c'è un solo set: la cartella mod del gioco."""
    sets = {}
    if GAME_LAUNCHER is None:
        return {"predefinito": ACTIVE_GAME_DIR}
    try:
        testo = GAME_LAUNCHER.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return sets
    m = re.search(r'^SET_MOD="([^"/]+)"\s*$', testo, re.M)
    if m and _SET_NOME_RE.match(m.group(1)):
        sets["predefinito"] = game_dir() / m.group(1)
    for nome, cartella in re.findall(r'^\s*([A-Za-z0-9_-]+)\)\s*SET_MOD="([^"/]+)"', testo, re.M):
        if _SET_NOME_RE.match(cartella):
            sets[nome] = game_dir() / cartella
    return sets


def elenco_set():
    """Un elemento per cartella, con i nomi del lanciatore che la usano."""
    per_cartella = {}
    for nome, cartella in set_dal_launcher().items():
        voce = per_cartella.setdefault(cartella.name, {"cartella": cartella.name, "percorso": str(cartella),
                                                        "nomi": [], "esiste": cartella.is_dir()})
        voce["nomi"].append(nome)
    for v in per_cartella.values():
        nomi = [n for n in v["nomi"] if n != "predefinito"]
        v["comando"] = f"run.sh {nomi[0]}" if nomi else "run.sh"
    return sorted(per_cartella.values(), key=lambda v: v["cartella"])


def cartella_set(nome_cartella):
    """Solo cartelle che run.sh conosce. Mai l'archivio."""
    if not isinstance(nome_cartella, str) or not _SET_NOME_RE.match(nome_cartella):
        raise RichiestaNonValida("set non valido")
    for cartella in set_dal_launcher().values():
        if cartella.name == nome_cartella:
            if _stessa_cartella_o_dentro(cartella, ARCHIVE_DIR):
                raise RuntimeError("il set coincide con l'archivio: mi fermo")
            return cartella
    raise RichiestaNonValida(f"set {nome_cartella} non presente in run.sh")


def gioco_aperto():
    try:
        return subprocess.run(["pgrep", "-f", "FarmingSimulator2025Game.exe"], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=5).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def leggi_salvataggio(slot_dir):
    """Nome, mappa e mod di un savegameN (solo lettura)."""
    f = slot_dir / "careerSavegame.xml"
    if not f.is_file() or f.stat().st_size > 20_000_000:
        return None
    try:
        root = ET.parse(f).getroot()
    except (ET.ParseError, OSError):
        return None
    mods = []
    for m in root.findall("mod"):
        nome = m.get("modName") or ""
        if not nome or nome.startswith("pdlc_"):
            continue
        mods.append({"nome": nome, "titolo": m.get("title") or nome, "versione": m.get("version") or "",
                     "richiesta": (m.get("required") or "").lower() == "true"})
    return {
        "slot": slot_dir.name,
        "nome": (root.findtext("settings/savegameName") or "").strip(),
        "mappa": (root.findtext("settings/mapTitle") or "").strip(),
        "map_id": (root.findtext("settings/mapId") or "").strip(),
        "data": (root.findtext("settings/saveDate") or "").strip(),
        "mods": mods,
    }


def _slot_validi():
    if not WINE_GAME_ROOT.is_dir():
        return []
    return sorted((d for d in WINE_GAME_ROOT.iterdir()
                   if d.is_dir() and re.fullmatch(r"savegame\d+", d.name)),
                  key=lambda d: int(d.name[8:]))


def leggi_profili():
    try:
        d = json.loads(PROFILI_FILE.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def salva_profilo(slot, cartella):
    cartella_set(cartella)
    if not re.fullmatch(r"savegame\d+", str(slot)) or not (WINE_GAME_ROOT / slot).is_dir():
        raise RichiestaNonValida("salvataggio non trovato")
    profili = leggi_profili()
    profili[slot] = cartella
    PROFILI_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = PROFILI_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(profili, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, PROFILI_FILE)
    return profili


def _presente(cartella, nome):
    """'link', 'file', 'cartella', 'rotto' o None."""
    z = cartella / f"{nome}.zip"
    if z.is_symlink():
        return "link" if z.is_file() else "rotto"
    if z.is_file():
        return "file"
    d = cartella / nome
    if d.is_dir():
        return "cartella"
    return None


def trova_fonte(nome, esclusa=None):
    """Una copia vera della mod: archivio, BACKUP_MODS, poi i file veri degli altri set."""
    zipname = f"{nome}.zip"
    if not nome_mod_valido(zipname):
        return None
    p = ARCHIVE_DIR / zipname
    if p.is_file() and not p.is_symlink():
        return p
    for p in sorted(ROOT_PROJECT.glob(f"BACKUP_MODS/**/{zipname}")):
        if p.is_file() and not p.is_symlink() and "_DOPPIONI_QUARANTENA" not in p.parts:
            return p
    for cartella in set_dal_launcher().values():
        if esclusa is not None and cartella.resolve() == esclusa.resolve():
            continue
        p = cartella / zipname
        if p.is_file() and not p.is_symlink():
            return p
    return None


def _modhub_cache():
    try:
        return json.loads(MODHUB_CACHE.read_text(encoding="utf-8")).get("entries", {})
    except (OSError, ValueError, AttributeError):
        return {}


def info_modhub(nome, titolo=""):
    e = _modhub_cache().get(f"{nome}.zip".lower(), {})
    off = e.get("official") or {}
    q = urllib.parse.quote(titolo or nome)
    return {
        "mod_id": off.get("id"),
        "pagina": off.get("url") or None,
        "cerca": f"https://www.farming-simulator.com/mods.php?title=fs2025&searchMod={q}",
    }


def suggerisci_set(info):
    """Il set che ha più mod del salvataggio (solo un suggerimento)."""
    migliore, punti = None, -1
    for v in elenco_set():
        cartella = Path(v["percorso"])
        if not cartella.is_dir():
            continue
        n = sum(1 for m in info["mods"] if _presente(cartella, m["nome"]) in ("link", "file", "cartella"))
        if n > punti:
            migliore, punti = v["cartella"], n
    return migliore


def elenco_partite():
    profili = leggi_profili()
    out = []
    for d in _slot_validi():
        info = leggi_salvataggio(d)
        if not info:
            continue
        scelto = profili.get(d.name)
        out.append({"slot": d.name, "nome": info["nome"], "mappa": info["mappa"], "data": info["data"],
                    "quante_mod": len(info["mods"]), "set": scelto, "set_suggerito": suggerisci_set(info),
                    "set_salvato": scelto is not None})
    return out


def piano_partita(slot, nome_cartella, togli_altre=False):
    """Cosa serve per giocare `slot` con il set `nome_cartella`. Non cambia niente."""
    if not isinstance(slot, str) or not re.fullmatch(r"savegame\d+", slot):
        raise RichiestaNonValida("salvataggio non valido")
    info = leggi_salvataggio(WINE_GAME_ROOT / slot)
    if not info:
        raise RichiestaNonValida("salvataggio non trovato o illeggibile")
    cartella = cartella_set(nome_cartella)
    servono = {m["nome"]: m for m in info["mods"]}
    ok, da_collegare, mancanti = [], [], []
    for nome, m in sorted(servono.items()):
        stato = _presente(cartella, nome) if cartella.is_dir() else None
        if stato in ("link", "file", "cartella"):
            ok.append({"nome": nome, "come": stato})
            continue
        fonte = trova_fonte(nome, esclusa=cartella)
        if fonte:
            da_collegare.append({"nome": nome, "fonte": str(fonte), "rotto": stato == "rotto"})
        else:
            mancanti.append({"nome": nome, "titolo": m["titolo"], "versione": m["versione"],
                             "richiesta": m["richiesta"], **info_modhub(nome, m["titolo"])})
    da_togliere, veri_in_piu, rotti = [], [], []
    if cartella.is_dir():
        for f in sorted(cartella.iterdir()):
            nome = f.name[:-4] if f.name.endswith(".zip") else f.name
            if nome in servono or f.name.endswith((".md", ".txt", ".json")):
                continue
            if f.is_symlink():
                (da_togliere if f.exists() else rotti).append(f.name)
            elif f.is_file() or f.is_dir():
                veri_in_piu.append(f.name)
    return {
        "slot": slot, "salvataggio": {k: info[k] for k in ("nome", "mappa", "map_id", "data")},
        "set": nome_cartella, "percorso_set": str(cartella),
        "ok": ok, "da_collegare": da_collegare, "mancanti": mancanti,
        "link_in_piu": da_togliere, "link_rotti": rotti, "file_veri_in_piu": veri_in_piu,
        "togli_altre": bool(togli_altre),
        "pronto": not mancanti,
    }


def applica_partita(slot, nome_cartella, togli_altre=False, conferma=False):
    """Mette nel set i link alle mod che il salvataggio usa. Toglie solo link (rotti sempre, quelli in più
    solo con togli_altre). Mai file veri: le mod restano nell'archivio."""
    piano = piano_partita(slot, nome_cartella, togli_altre)
    if conferma is not True:
        raise RichiestaNonValida("serve la conferma esplicita")
    if gioco_aperto():
        raise RichiestaNonValida("il gioco è aperto: chiudilo prima di cambiare le mod")
    cartella = Path(piano["percorso_set"])
    if _stessa_cartella_o_dentro(cartella, ARCHIVE_DIR):
        raise RuntimeError("il set coincide con l'archivio: mi fermo")
    cartella.mkdir(parents=True, exist_ok=True)
    elenco = salva_elenco_link(cartella)
    tolti = []
    for nome in piano["link_rotti"] + (piano["link_in_piu"] if togli_altre else []):
        f = cartella / nome
        if f.is_symlink():
            f.unlink()
            tolti.append(nome)
    collegati = []
    for voce in piano["da_collegare"]:
        dst = cartella / f"{voce['nome']}.zip"
        if dst.is_symlink():
            dst.unlink()  # link rotto della stessa mod
        if dst.exists():
            continue
        dst.symlink_to(Path(voce["fonte"]).resolve())
        collegati.append(voce["nome"])
    return {"success": True, "collegati": collegati, "tolti": tolti, "mancanti": piano["mancanti"],
            "elenco_link_salvato": str(elenco) if elenco else None}


def mod_dei_salvataggi_del_set(cartella):
    """Nomi .zip usati dai salvataggi collegati (in profili.json) a questa cartella."""
    profili = leggi_profili()
    nomi = set()
    for slot, nome_set in profili.items():
        if nome_set != cartella.name or not re.fullmatch(r"savegame\d+", slot):
            continue
        info = leggi_salvataggio(WINE_GAME_ROOT / slot)
        if info:
            nomi.update(f"{m['nome']}.zip" for m in info["mods"])
    return nomi


# ---------------------------------------------------------------- scaricare una mod dal ModHub
def scarica_mod(nome, mod_id):
    """Scarica <nome>.zip dalla pagina ModHub ufficiale nell'archivio. Mai sovrascrivere."""
    zipname = f"{nome}.zip"
    if not nome_mod_valido(zipname):
        raise RichiestaNonValida("nome della mod non valido")
    if not re.fullmatch(r"\d{1,9}", str(mod_id or "")):
        raise RichiestaNonValida("serve l'id ModHub (numero)")
    dst = ARCHIVE_DIR / zipname
    if dst.exists() or dst.is_symlink():
        raise RichiestaNonValida(f"{zipname} c'è già nell'archivio")
    import urllib.request
    ua = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) ModManagerFS25"}
    pagina = f"https://www.farming-simulator.com/mod.php?mod_id={mod_id}&title=fs2025"
    with urllib.request.urlopen(urllib.request.Request(pagina, headers=ua), timeout=30) as r:
        html = r.read(3_000_000).decode("utf-8", "replace")
    link = None
    for url, fname in _CDN_RE.findall(html):
        if fname == zipname:
            link = url
    if not link:
        raise RichiestaNonValida(f"nella pagina ModHub {mod_id} non c'è il file {zipname}")
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    parte = ARCHIVE_DIR / f".{zipname}.parte"
    req = urllib.request.Request(link, headers={**ua, "Referer": MODHUB_REFERER})
    try:
        with urllib.request.urlopen(req, timeout=60) as r, open(parte, "wb") as out:
            tot = 0
            while True:
                blocco = r.read(1 << 20)
                if not blocco:
                    break
                tot += len(blocco)
                if tot > 4_000_000_000:
                    raise RichiestaNonValida("file troppo grande")
                out.write(blocco)
        with zipfile.ZipFile(parte) as zf:
            zf.getinfo("modDesc.xml")
        if dst.exists():
            raise RichiestaNonValida(f"{zipname} è comparso nel frattempo: non sovrascrivo")
        os.rename(parte, dst)
    finally:
        if parte.exists():
            parte.unlink()  # solo il file parziale appena scaricato
    return {"success": True, "file": str(dst), "byte": dst.stat().st_size, "da": link}


# ---------------------------------------------------------------- copia di sicurezza delle mod
def stato_backup():
    if BACKUP_DISCO is None:
        return {"montato": False, "configurato": False, "disco": "", "destinazione": "", "ultima": None,
                "in_corso": False}
    dest = BACKUP_DISCO / BACKUP_SOTTOCARTELLA
    # disponibile se è un punto di montaggio (disco collegato) o se la destinazione esiste già
    montato = os.path.ismount(BACKUP_DISCO) or (BACKUP_DISCO.is_dir() and dest.is_dir())
    ultimo = None
    f = dest / "ULTIMA_COPIA.json"
    if montato and f.is_file():
        try:
            ultimo = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            ultimo = None
    return {"montato": montato, "configurato": True, "disco": str(BACKUP_DISCO), "destinazione": str(dest), "ultima": ultimo,
            "in_corso": _BACKUP_PROC is not None and _BACKUP_PROC.poll() is None}


_BACKUP_PROC = None


def avvia_backup():
    global _BACKUP_PROC
    st = stato_backup()
    if not st["montato"]:
        if not st["configurato"]:
            raise RichiestaNonValida("copia di sicurezza non configurata: imposta FS25_BACKUP_DIR")
        raise RichiestaNonValida(f"il disco di backup non è collegato ({BACKUP_DISCO}): collegalo e riprova")
    if st["in_corso"]:
        return {"success": True, "gia_in_corso": True}
    log = open(BASE_DIR / "data" / "backup_mods.log", "a", encoding="utf-8")
    _BACKUP_PROC = subprocess.Popen(
        ["nice", "-n", "19", "ionice", "-c3", sys.executable, str(BASE_DIR / "backup_mods.py"),
         "--dest", str(BACKUP_DISCO / BACKUP_SOTTOCARTELLA)],
        stdout=log, stderr=subprocess.STDOUT, cwd=str(BASE_DIR))
    return {"success": True, "avviato": True}


HOST_LOCALI = {"127.0.0.1", "localhost", "[::1]"}
MAX_BODY = 1_000_000


class ModManagerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    # ---- aiuti
    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _host_locale(self):
        """Contro il DNS rebinding: accetta solo richieste indirizzate a 127.0.0.1/localhost."""
        host = (self.headers.get("Host") or "").strip()
        nome = host.rsplit(":", 1)[0] if not host.startswith("[") else host.split("]")[0] + "]"
        return nome in HOST_LOCALI

    def _origine_locale(self):
        """Le scritture arrivano solo dalla dashboard stessa: niente siti esterni (CSRF)."""
        origin = self.headers.get("Origin")
        if origin is None:
            return True  # curl o script locali
        try:
            nome = urllib.parse.urlparse(origin).hostname or ""
        except ValueError:
            return False
        return nome in {"127.0.0.1", "localhost", "::1"}

    def _leggi_json(self):
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype != "application/json":
            raise RichiestaNonValida("serve Content-Type: application/json")
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            raise RichiestaNonValida("Content-Length non valido")
        if length < 0 or length > MAX_BODY:
            raise RichiestaNonValida("richiesta troppo grande")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            data = json.loads(raw or "{}")
        except json.JSONDecodeError:
            raise RichiestaNonValida("JSON non valido")
        if not isinstance(data, dict):
            raise RichiestaNonValida("serve un oggetto JSON")
        return data

    # ---- GET
    def do_GET(self):
        if not self._host_locale():
            self._json(403, {"success": False, "error": "solo richieste locali (127.0.0.1)"})
            return
        try:
            self._get()
        except RichiestaNonValida as e:
            self._json(400, {"success": False, "error": str(e)})
        except Exception as e:
            print("Errore GET:", e)
            self._json(500, {"success": False, "error": str(e)})

    def _get(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/status":
            presets = load_presets()
            active = get_active_game_mods()
            archive = [f.name for f in ARCHIVE_DIR.glob("*.zip")]
            self._json(200, {
                "active_mods": active,
                "active_count": len(active),
                "archive_count": len(archive),
                "presets": presets,
                "game_dir": str(ACTIVE_GAME_DIR),
                "has_launcher": GAME_LAUNCHER is not None and GAME_LAUNCHER.exists(),
                "has_kingmods_db": DB_PATH.exists(),
                "cartella_gioco_sicura": not _stessa_cartella_o_dentro(ACTIVE_GAME_DIR, ARCHIVE_DIR),
            })
            return

        if path == "/api/slot":
            try:
                slot = int(params.get("n", ["1"])[0])
            except ValueError:
                raise RichiestaNonValida("n deve essere un numero")
            self._json(200, {"slot": slot, "occupato_in": slot_occupati(slot)})
            return

        if path == "/api/set":
            self._json(200, {"set": elenco_set(), "launcher": str(GAME_LAUNCHER or "")})
            return

        if path == "/api/partite":
            self._json(200, {"partite": elenco_partite(), "set": elenco_set(), "gioco_aperto": gioco_aperto()})
            return

        if path == "/api/piano":
            self._json(200, piano_partita(params.get("slot", [""])[0], params.get("set", [""])[0],
                                          params.get("togli", ["0"])[0] == "1"))
            return

        if path == "/api/backup":
            self._json(200, stato_backup())
            return

        if path == "/api/maps":
            mappe = sorted(trova_mappe().values(), key=lambda m: m["titolo"].lower())
            self._json(200, {"mappe": mappe, "predefinita": MAPPA_PREDEFINITA})
            return

        if path == "/api/link_salvati":
            self._json(200, {"elenchi": elenco_link_salvati()})
            return

        if path == "/api/search_external":
            q = params.get("q", [""])[0][:100]
            try:
                limit = max(1, min(100, int(params.get("limit", [20])[0])))
            except ValueError:
                raise RichiestaNonValida("limit deve essere un numero")
            results = query_kingmods(q, limit) if q else []
            self._json(200, {"results": results, "count": len(results)})
            return

        if path == "/api/recommended":
            categories = {
                "mediterranean": {
                    "title": "🍇 Olio, vino e frutteti mediterranei",
                    "items": query_kingmods("wine", 4) + query_kingmods("olive", 4)
                },
                "italian_tractors": {
                    "title": "🚜 Trattori italiani e storici (Laverda, Antonio Carraro, Maschio)",
                    "items": query_kingmods("laverda", 3) + query_kingmods("antonio carraro", 3) + query_kingmods("maschio", 3)
                },
                "realism_economy": {
                    "title": "🧠 Realismo, suolo ed economia",
                    "items": query_kingmods("realistic soil", 3) + query_kingmods("water", 3)
                }
            }
            self._json(200, {"categories": categories})
            return

        if path.startswith("/data/link_salvati") or path.endswith((".py", ".csv", ".sh", ".bak")) or ".bak-" in path:
            self._json(404, {"success": False, "error": "non disponibile"})
            return

        super().do_GET()

    # ---- POST
    def do_POST(self):
        if not self._host_locale() or not self._origine_locale():
            self._json(403, {"success": False, "error": "solo richieste dalla dashboard locale"})
            return
        try:
            self._post()
        except RichiestaNonValida as e:
            self._json(400, {"success": False, "error": str(e)})
        except SlotOccupato as e:
            self._json(409, {
                "success": False,
                "error": f"Lo slot {e.slot} contiene già un salvataggio.",
                "slot": e.slot,
                "occupato_in": e.posti,
                "serve_conferma": True,
            })
        except Exception as e:
            print("Errore POST:", e)
            self._json(500, {"success": False, "error": str(e)})

    def _post(self):
        path = urllib.parse.urlparse(self.path).path

        if path == "/api/activate":
            data = self._leggi_json()
            mods_to_enable = data.get("mods", [])
            preset_key = data.get("preset")
            if preset_key:
                presets = load_presets()
                if preset_key in presets:
                    mods_to_enable = presets[preset_key]["mods"]
            if isinstance(mods_to_enable, list) and not data.get("forza"):
                servono = mod_dei_salvataggi_del_set(ACTIVE_GAME_DIR)
                tolte = sorted(servono - set(m for m in mods_to_enable if isinstance(m, str)))
                tolte = [m for m in tolte if (ACTIVE_GAME_DIR / m).is_symlink()]
                if tolte:
                    self._json(409, {"success": False, "serve_conferma": True, "mod_del_salvataggio_tolte": tolte,
                                     "error": f"{len(tolte)} mod usate da un salvataggio di questo set verrebbero tolte"})
                    return
            enabled, missing, dettagli = apply_mods_to_game(mods_to_enable)
            self._json(200, {
                "success": True,
                "enabled_count": len(enabled),
                "missing_count": len(missing),
                "enabled": enabled,
                "missing": missing,
                **dettagli,
            })
            return

        if path == "/api/profilo":
            data = self._leggi_json()
            self._json(200, {"success": True, "profili": salva_profilo(data.get("slot"), data.get("set"))})
            return

        if path == "/api/applica_partita":
            data = self._leggi_json()
            self._json(200, applica_partita(data.get("slot"), data.get("set"), bool(data.get("togli_altre")),
                                            data.get("conferma") is True))
            return

        if path == "/api/scarica_mod":
            data = self._leggi_json()
            self._json(200, scarica_mod(data.get("nome"), data.get("mod_id")))
            return

        if path == "/api/backup":
            self._leggi_json()
            self._json(200, avvia_backup())
            return

        if path == "/api/rimetti_link":
            data = self._leggi_json()
            self._json(200, rimetti_link(data.get("file")))
            return

        if path == "/api/create_game":
            data = self._leggi_json()
            try:
                slot = int(data.get("slot", 1))
                money = int(data.get("money", 0))
                loan = int(data.get("loan", 0))
                dirt = int(data.get("dirt_interval", 3))
                fuel = int(data.get("fuel_usage", 2))
                days = int(data.get("days_per_period", 1))
                tscale = float(data.get("time_scale", 5.0))
            except (TypeError, ValueError):
                raise RichiestaNonValida("numeri non validi nei campi della partita")

            res = create_savegame_career(
                slot=slot,
                savegame_name=data.get("name", "Survival Italia Mediterranea - Giorno 1"),
                starting_money=money,
                starting_loan=loan,
                difficulty=data.get("difficulty", "HARD"),
                fruit_destruction=bool(data.get("fruit_destruction", True)),
                plowing_required=bool(data.get("plowing_required", True)),
                stones=bool(data.get("stones", True)),
                weeds=bool(data.get("weeds", True)),
                lime=bool(data.get("lime", True)),
                snow=bool(data.get("snow", True)),
                dirt_interval=dirt,
                fuel_usage=fuel,
                days_per_period=days,
                time_scale=tscale,
                mod_list=data.get("mods", []),
                conferma_sovrascrittura=data.get("conferma_sovrascrittura"),
                mappa=data.get("map") or MAPPA_PREDEFINITA,
                set_mod=data.get("set") or None,
            )

            if data.get("launch_game", False):
                ok, err = avvia_gioco(res.get("set"))
                res["game_launched"] = ok
                if err:
                    res["launch_error"] = err

            if data.get("launch_obs", False):
                res["obs_launched"] = avvia_obs()

            self._json(200, res)
            return

        if path == "/api/launch_now":
            data = self._leggi_json()
            ok, err = avvia_gioco()
            obs_ok = avvia_obs() if data.get("launch_obs", False) else False
            self._json(200, {"success": ok, "obs": obs_ok, "error": err})
            return

        self._json(404, {"success": False, "error": "indirizzo sconosciuto"})


def argomento_launcher(cartella):
    """Il nome da passare a run.sh per usare quella cartella di mod ('' = run.sh senza argomenti)."""
    for v in elenco_set():
        if v["cartella"] == cartella:
            nomi = [n for n in v["nomi"] if n != "predefinito"]
            return "" if "predefinito" in v["nomi"] or not nomi else nomi[0]
    return None


def avvia_gioco(cartella_set_mod=None):
    if os.environ.get("MOD_MANAGER_NO_LAUNCH"):
        return False, "avvio disattivato (MOD_MANAGER_NO_LAUNCH)"
    if GAME_LAUNCHER is None:
        return False, "nessun lanciatore configurato (FS25_LAUNCHER): avvia il gioco da Steam"
    cmd = [str(GAME_LAUNCHER)]
    if cartella_set_mod:
        arg = argomento_launcher(cartella_set_mod)
        if arg is None:
            return False, f"run.sh non conosce il set {cartella_set_mod}"
        if arg:
            cmd.append(arg)
    try:
        subprocess.Popen(cmd, cwd=str(GAME_LAUNCHER.parent))
        return True, None
    except Exception as e:
        print("Errore avvio gioco:", e)
        return False, str(e)


def avvia_obs():
    if os.environ.get("MOD_MANAGER_NO_LAUNCH"):
        return False
    try:
        subprocess.Popen(["obs"])
        return True
    except Exception:
        return False


def run_server(port=8025, host="127.0.0.1"):
    ThreadingHTTPServer.allow_reuse_address = True
    httpd = ThreadingHTTPServer((host, port), ModManagerHandler)
    print(f"Mod Manager FS25 attivo su http://{host}:{port} (solo da questo PC)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArresto server.")
        httpd.server_close()


if __name__ == "__main__":
    port = 8025
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
