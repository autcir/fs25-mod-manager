#!/usr/bin/env python3
"""
MOD MANAGER FS25 - Scanner archivio mod
=======================================
Legge le mod attive (mods/) e l'archivio (BACKUP_MODS/), estrae i metadati dai
modDesc.xml e dai file store, converte le icone in PNG e genera i dati per la
dashboard (data/mods.js + data/mods.json).

Solo libreria standard + ImageMagick (opzionale, per le icone DDS).
Nessun file delle mod viene modificato: la scansione è in sola lettura.

Uso:
    python3 MOD_MANAGER/scan_mods.py
    python3 MOD_MANAGER/scan_mods.py --no-icons   # scansione veloce
    python3 MOD_MANAGER/scan_mods.py --force      # ignora la cache
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import config

BASE_DIR = Path(__file__).resolve().parent
GAME_DIR = config.library_dir()  # FS25_LIBRARY_DIR: contiene mods/, BACKUP_MODS/, mods-bck/
MODS_DIR = GAME_DIR / "mods"
BACKUP_DIR = GAME_DIR / "BACKUP_MODS"
QUARANTINE_DIR = BACKUP_DIR / "_DOPPIONI_QUARANTENA"
DATA_DIR = BASE_DIR / "data"
ICON_DIR = BASE_DIR / "icons"
CACHE_FILE = DATA_DIR / "cache.json"
MODHUB_CACHE_FILE = DATA_DIR / "modhub_cache.json"

LANG_ORDER = ("it", "en", "de", "fr", "es", "pl")

BACKUP_FOLDERS = {
    "01_MAPPE": "Mappe",
    "02_TRATTORI_E_MEZZI": "Trattori e mezzi",
    "03_MIETITREBBIE_RACCOLTA": "Mietitrebbie e raccolta",
    "04_SEMINA_CULTURE_SPECIALI": "Semina e colture",
    "05_ATREZZI_SUOLO": "Lavorazione del suolo",
    "06_FALCI_FIENAGIONE": "Falci e fienagione",
    "07_RIMORCHI_ZAVORRE": "Rimorchi e zavorre",
    "08_ACQUA_LETAME": "Acqua, letame e stalle",
    "09_SILOS_BUNKER": "Silos e stoccaggio",
    "10_SCRIPT_MOD_UTILITY": "Script e utility",
    "11_URBANIZZAZIONE_TERRAFORMING": "Terraforming e strade",
    "12_CAPANNI_DECORAZIONE": "Costruzioni e decorazioni",
    "13_FILIERE_PRODUZIONI": "Produzioni",
    "14_STRUMENTI_VARIE": "Strumenti vari",
    "15_COPIE_MOD_ATTIVE": "Copie mod attive",
    "maps": "Mappe",
    "amap": "Mappe",
    "bmap": "Mappe",
}

# Categorie ampie usate per i filtri della dashboard
BROAD_CATEGORIES = [
    "Mappe",
    "Trattori e mezzi",
    "Mietitrebbie e raccolta",
    "Semina e colture",
    "Lavorazione del suolo",
    "Falci e fienagione",
    "Rimorchi e zavorre",
    "Acqua, letame e stalle",
    "Silos e stoccaggio",
    "Produzioni",
    "Costruzioni e decorazioni",
    "Terraforming e strade",
    "Script e utility",
    "Strumenti vari",
    "Copie mod attive",
    "Altro",
]

SHOP_TO_BROAD = {
    # veicoli
    "tractors": "Trattori e mezzi", "tractorss": "Trattori e mezzi",
    "tractorsm": "Trattori e mezzi", "tractorsl": "Trattori e mezzi",
    "cars": "Trattori e mezzi", "trucks": "Trattori e mezzi",
    "telehandlers": "Trattori e mezzi", "loaders": "Trattori e mezzi",
    "forklifts": "Trattori e mezzi", "drivables": "Trattori e mezzi",
    # raccolta
    "harvesters": "Mietitrebbie e raccolta", "cutters": "Mietitrebbie e raccolta",
    "cornheaders": "Mietitrebbie e raccolta", "forageharvesters": "Mietitrebbie e raccolta",
    "cottenharvesters": "Mietitrebbie e raccolta", "cottonharvesters": "Mietitrebbie e raccolta",
    "grapeharvesters": "Mietitrebbie e raccolta", "oliveharvesters": "Mietitrebbie e raccolta",
    "potatoharvesting": "Mietitrebbie e raccolta", "riceharvesters": "Mietitrebbie e raccolta",
    "sugarcaneharvesters": "Mietitrebbie e raccolta", "stonepickers": "Mietitrebbie e raccolta",
    "cuttertrailers": "Rimorchi e zavorre",
    # semina e cura
    "seeders": "Semina e colture", "planters": "Semina e colture",
    "potatoplanting": "Semina e colture", "riceplanters": "Semina e colture",
    "sprayers": "Semina e colture", "fertilizerspreaders": "Semina e colture",
    "weeders": "Semina e colture",
    # suolo
    "plows": "Lavorazione del suolo", "cultivators": "Lavorazione del suolo",
    "dischargers": "Lavorazione del suolo", "discharges": "Lavorazione del suolo",
    "discharrows": "Lavorazione del suolo", "harrows": "Lavorazione del suolo",
    "subsoilers": "Lavorazione del suolo", "rollers": "Lavorazione del suolo",
    "mulchers": "Lavorazione del suolo",
    # fienagione
    "mowers": "Falci e fienagione", "balers": "Falci e fienagione",
    "balerssquare": "Falci e fienagione", "wrappers": "Falci e fienagione",
    "tedders": "Falci e fienagione", "windrowers": "Falci e fienagione",
    "grasslandcare": "Falci e fienagione", "loaderwagons": "Falci e fienagione",
    "augerwagons": "Rimorchi e zavorre", "foragewagons": "Rimorchi e zavorre",
    # rimorchi
    "trailers": "Rimorchi e zavorre", "lowloaders": "Rimorchi e zavorre",
    "weights": "Rimorchi e zavorre", "woodtransport": "Rimorchi e zavorre",
    "animaltransport": "Rimorchi e zavorre",
    # acqua / letame / stalle
    "watertanks": "Acqua, letame e stalle", "fillabletanks": "Acqua, letame e stalle",
    "slurrytanks": "Acqua, letame e stalle", "manurespreaders": "Acqua, letame e stalle",
    "animalpens": "Acqua, letame e stalle", "animals": "Acqua, letame e stalle",
    "barrels": "Acqua, letame e stalle",
    # silos e stoccaggio
    "silos": "Silos e stoccaggio", "bunkersilos": "Silos e stoccaggio",
    "siloextensions": "Silos e stoccaggio", "storages": "Silos e stoccaggio",
    "pallets": "Silos e stoccaggio", "bigbags": "Silos e stoccaggio",
    "bigbagpallets": "Silos e stoccaggio", "seedtanks": "Silos e stoccaggio",
    # produzioni / economia
    "productionpoints": "Produzioni", "production": "Produzioni",
    "generators": "Produzioni", "sellingpoints": "Produzioni",
    # costruzioni
    "buildings": "Costruzioni e decorazioni", "sheds": "Costruzioni e decorazioni",
    "gardensheds": "Costruzioni e decorazioni", "farmhouses": "Costruzioni e decorazioni",
    "decorations": "Costruzioni e decorazioni", "decoration": "Costruzioni e decorazioni",
    "fences": "Costruzioni e decorazioni", "floodlighting": "Costruzioni e decorazioni",
    "constructiblebuildings": "Costruzioni e decorazioni",
    # terraforming / esterni
    "landscaping": "Terraforming e strade", "placeablemisc": "Terraforming e strade",
    # strumenti
    "chainsaws": "Strumenti vari", "handtools": "Strumenti vari",
    "handtoolsmisc": "Strumenti vari", "tools": "Strumenti vari",
    "misc": "Strumenti vari",
}

SCRIPT_KEYS = {
    "additionalfieldinfo", "autodrive", "courseplay", "courseplayplayerunload",
    "easydevcontrols", "fieldcreatorplus", "followme", "forestryhelper",
    "freeterraformingandpainting", "gpsplus", "greenhouseautomaticwatering",
    "hirepurchasing", "infodisplaysieextension", "increasedworkareasforpickups",
    "lumberjack", "mobileworkshop", "moveplaceablesadvanced", "perfectedge",
    "placeterraformpaintanywhere_kingmods", "powertools", "precisionfarming",
    "roadbuilder", "simpleinspector", "specialoffers", "storedeliveries",
    "th_defaulttypes", "togglesuperstrength", "universalautoload",
    "unlimitedcolorconfigurations",
}

CATEGORY_OVERRIDES = {
    "oldlogshedspack": "Costruzioni e decorazioni",
    "newhollandtx32": "Mietitrebbie e raccolta",
    "smallproduction": "Produzioni",
    "chickencoopeuropean": "Acqua, letame e stalle",
    "internationalih_70": "Trattori e mezzi",
    "foragepickup": "Mietitrebbie e raccolta",
    "landstal_pack": "Lavorazione del suolo",
    "mf11": "Semina e colture",
    "asm_cannabisdlcpack": "Produzioni",
    "handpushabletoolspack": "Strumenti vari",
    "wood_autoload": "Rimorchi e zavorre",
    "seeds_addon_crossplay": "Semina e colture",
    "handbalingtools": "Strumenti vari",
}


def category_tokens(value: str):
    return [t.lower() for t in re.split(r"[\s,;|/]+", value or "") if t]


def map_store_category(value: str, table: dict) -> str | None:
    for token in category_tokens(value):
        label = table.get(token)
        if label:
            return label
    return None

# Categorie dello shop FS25 -> etichette italiane
STORE_CATEGORIES = {
    "tractors": "Trattori",
    "tractorss": "Trattori piccoli",
    "tractorsm": "Trattori medi",
    "tractorsl": "Trattori grandi",
    "harvesters": "Mietitrebbie",
    "cutters": "Barre di taglio",
    "trailers": "Rimorchi",
    "cars": "Auto",
    "trucks": "Camion",
    "telehandlers": "Sollevatori telescopici",
    "loaders": "Pale",
    "forklifts": "Carrelli elevatori",
    "implements": "Attrezzi",
    "seeders": "Seminatrici",
    "planters": "Seminatrici",
    "sprayers": "Irroratrici",
    "fertilizerspreaders": "Spandiconcime",
    "manurespreaders": "Spandiletame",
    "mowers": "Falciatrici",
    "balers": "Presse",
    "wrappers": "Avvolgitori",
    "tedders": "Andanatori",
    "windrowers": "Andanatori",
    "plows": "Aratri",
    "cultivators": "Coltivatori",
    "harrows": "Erpici",
    "rollers": "Rulli",
    "weights": "Zavorre",
    "productionpoints": "Produzioni",
    "generators": "Generatori",
    "animalhusbandry": "Stalle",
    "silos": "Silos",
    "bunkersilos": "Silos",
    "decorations": "Decorazioni",
    "placeable": "Piazzabili",
    "sellingpoints": "Punti vendita",
    "greenhouses": "Serre",
    "forestry": "Forestale",
    "misc": "Vari",
    "tools": "Strumenti",
    "handtools": "Attrezzi a mano",
    "pallets": "Bancali",
    "bales": "Balle",
    "bigbags": "Big bag",
}

VEHICLE_CATS = {
    "tractors", "tractorss", "tractorsm", "tractorsl", "harvesters", "cars",
    "trucks", "telehandlers", "loaders", "forklifts", "drivables", "vehicles",
    "cottonharvesters", "forageharvesters", "grapeharvesters", "oliveharvesters",
    "riceharvesters", "sugarcaneharvesters",
}
TOOL_CATS = {
    "cutters", "trailers", "implements", "seeders", "planters", "sprayers",
    "fertilizerspreaders", "manurespreaders", "mowers", "balers", "wrappers",
    "tedders", "windrowers", "plows", "cultivators", "harrows", "rollers",
    "weights", "tools", "handtools", "forestry", "discharrows", "subsoilers",
    "mulchers", "weeders", "stonepickers", "potatoharvesting", "potatoplanting",
    "riceplanters", "cornheaders", "grasslandcare", "loaderwagons", "augerwagons",
    "cuttertrailers", "lowloaders", "woodtransport", "animaltransport",
    "chainsaws", "handtoolsmisc", "belts", "slurrytanks", "watertanks",
    "fillabletanks", "seedtanks",
}
PLACEABLE_CATS = {
    "productionpoints", "generators", "animalhusbandry", "silos",
    "bunkersilos", "decorations", "placeable", "sellingpoints", "greenhouses",
    "pallets", "bales", "bigbags", "misc", "buildings", "sheds", "gardensheds",
    "farmhouses", "decoration", "fences", "floodlighting", "landscaping",
    "storages", "siloextensions", "animalpens", "animals", "constructiblebuildings",
    "placeablemisc", "barrels",
}

TYPE_LABELS = {
    "mappa": "Mappa",
    "veicolo": "Veicolo",
    "attrezzo": "Attrezzo",
    "piazzabile": "Piazzabile",
    "script": "Script",
    "pacchetto": "Pacchetto",
    "altro": "Altro",
}

CATEGORY_COLORS = {
    "Mappe": "#6ea8fe",
    "Trattori e mezzi": "#f4a261",
    "Mietitrebbie e raccolta": "#e9c46a",
    "Semina e colture": "#a7c957",
    "Lavorazione del suolo": "#bc6c25",
    "Falci e fienagione": "#90be6d",
    "Rimorchi e zavorre": "#c77dff",
    "Acqua, letame e stalle": "#48cae4",
    "Silos e stoccaggio": "#8d99ae",
    "Produzioni": "#f28482",
    "Costruzioni e decorazioni": "#e5989b",
    "Terraforming e strade": "#b08968",
    "Script e utility": "#ffd166",
    "Strumenti vari": "#adb5bd",
    "Copie mod attive": "#7bdff2",
    "Altro": "#9aa0a6",
}

# Parole chiave per dedurre l'uso della mod / tag funzionali
TAG_RULES = [
    ("Autoload", r"autoload|auto.?load|caricamento automatico"),
    ("Guida assistita", r"\bgps\b|guidance|sterzata|linee guida"),
    ("Operaio AI", r"courseplay|autodrive|operaio|helper|ai worker"),
    ("Produzione", r"produc|production|filiere|trasform|ricett|recipe"),
    ("Silos", r"silo|bunker|insilato|silage"),
    ("Acqua", r"acqua|water|irrig|abbeveratoio"),
    ("Letame", r"letame|manure|slurry|purin"),
    ("Serre", r"serra|greenhouse|vivaio"),
    ("Bosco/Foresta", r"forest|legno|wood|tree|albero|chainsaw|sega"),
    ("Terraforming", r"terraform|terreno|paint|pittura|scavo"),
    ("Strade", r"road|strada|asfalt|parking|parcheggio"),
    ("Costruzioni", r"shed|capannone|edificio|building|house|casa|stalla"),
    ("Rimorchi", r"trailer|rimorch|carret"),
    ("Trattori", r"tractor|trattor"),
    ("Mietitrebbia", r"harvester|mietitrebbia|combine"),
    ("Fienagione", r"mower|falci|baler|pressa|fieno|hay|windrow|andana"),
    ("Semina", r"seeder|seminat|planter|semina"),
    ("Irrigazione", r"sprayer|irrorat|spray"),
    ("Soldi/Economia", r"money|denaro|econom|finance|mutuo|rate|prezzo"),
    ("Qualità della vita", r"quality of life|comod|utility|super strength|forza"),
    ("Multiplayer", r"multiplayer|crossplay"),
    ("Mappa", r"\bmap\b|mappa"),
    ("Cannabis", r"cannabis|weed|marijuana"),
    ("Animali", r"animal|bestiame|mucche|pecore|chicken|galline"),
]

CURATED: dict[str, dict] = {}
try:
    from curated import CURATED as _CURATED  # type: ignore
    CURATED = _CURATED
except Exception:
    CURATED = {}


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def clean_text(value: str, limit: int = 14000) -> str:
    if not value:
        return ""
    s = html.unescape(value)
    s = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(p|div|li|h[1-6]|tr)>", "\n", s)
    s = re.sub(r"(?i)<li[^>]*>", "• ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t\f\v]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = s.strip()
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0].rstrip() + "…"
    return s


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower() if "}" in tag else tag.lower()


def find_child(elem, name: str):
    if elem is None:
        return None
    for child in list(elem):
        if strip_ns(child.tag) == name.lower():
            return child
    return None


def iter_local(elem, name: str):
    if elem is None:
        return
    for node in elem.iter():
        if strip_ns(node.tag) == name.lower():
            yield node


def node_text(elem) -> str:
    if elem is None:
        return ""
    return clean_text("".join(elem.itertext()))


def localized(elem) -> str:
    """Estrae il testo localizzato (preferenza: italiano, inglese, ...)."""
    if elem is None:
        return ""
    children = list(elem)
    if not children:
        return clean_text(elem.text or "")
    # Figli con tag lingua
    by_lang = {}
    for child in children:
        by_lang[strip_ns(child.tag)] = child
    for lang in LANG_ORDER:
        if lang in by_lang:
            txt = node_text(by_lang[lang])
            if txt:
                return txt
    for child in children:
        txt = node_text(child)
        if txt:
            return txt
    return node_text(elem)


def safe_int(value) -> int | None:
    if value is None:
        return None
    m = re.search(r"-?\d[\d.,]*", str(value))
    if not m:
        return None
    raw = m.group(0).replace(".", "").replace(",", ".") if "," in m.group(0) else m.group(0)
    try:
        return int(float(raw))
    except ValueError:
        return None


def safe_float(value) -> float | None:
    if value is None:
        return None
    m = re.search(r"-?\d[\d.,]*", str(value))
    if not m:
        return None
    raw = m.group(0)
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def parse_xml(data: bytes):
    """Parse tollerante: restituisce (root, testo) oppure (None, testo)."""
    text = data.decode("utf-8-sig", errors="replace")
    text = text.replace("\x00", "")
    for candidate in (text, re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", text)):
        try:
            return ET.fromstring(candidate), candidate
        except ET.ParseError:
            continue
    return None, text


def parse_xml_file(zf: zipfile.ZipFile, name: str):
    try:
        return parse_xml(zf.read(name))
    except (KeyError, OSError, RuntimeError):
        return None, ""


def normalize_key(filename: str) -> str:
    stem = Path(filename).stem.lower()
    stem = re.sub(r"^fs25[_\-\s]*", "", stem)
    stem = re.sub(r"[_\-\s]*(crossplay|kingmods|fs25)$", "", stem)
    stem = re.sub(r"[_\-\s]+", "_", stem).strip("_")
    return stem


def human_size(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.1f} {unit}" if unit != "B" else f"{num} B"
        num /= 1024.0
    return f"{num:.1f} GB"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Estrazione metadati
# ---------------------------------------------------------------------------

def parse_l10n(root, text: str) -> dict[str, str]:
    out = {}
    if root is not None:
        l10n = find_child(root, "l10n")
        if l10n is not None:
            for item in list(l10n):
                name = item.attrib.get("name")
                if not name:
                    continue
                val = localized(item)
                if val:
                    out[name] = val
    # fallback regex per modDesc malformati
    if not out:
        for m in re.finditer(r'<text\s+name="([^"]+)"[^>]*>(.*?)</text>', text, re.S | re.I):
            val = clean_text(re.sub(r"<[^>]+>", " ", m.group(2)))
            if val:
                out[m.group(1)] = val
    return out


def resolve_l10n(value: str, l10n: dict[str, str]) -> str:
    if not value:
        return ""
    value = value.strip()
    if value.startswith("$l10n_"):
        return l10n.get(value[6:], value[6:].replace("_", " "))
    if value.startswith("$"):
        return l10n.get(value[1:], value[1:].replace("_", " "))
    return value


def pretty_store_name(value: str, ref: str) -> str:
    """Rende leggibili i nomi non tradotti (es. 'storeItem paperFactory')."""
    raw = (value or "").strip()
    if not raw or re.search(r"%[sd]", raw):
        raw = Path(ref).stem
        raw = re.sub(r"^multiPurchase", "", raw, flags=re.I)
    raw = re.sub(r"^\$?l10n_", "", raw, flags=re.I)
    raw = re.sub(r"^(storeItem|shopItem)[_\s]+", "", raw, flags=re.I)
    raw = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", raw)
    raw = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", raw)
    raw = re.sub(r"[_]+", " ", raw)
    raw = re.sub(r"^(?:Name|Fill Type|Buyable Handtool|Production Point|Sell Station)\s+", "", raw, flags=re.I)
    raw = re.sub(r"\s+", " ", raw).strip()
    if not raw:
        raw = Path(ref).stem
    words = [w[:1].upper() + w[1:] if w.islower() else w for w in raw.split()]
    return " ".join(words)


def get_moddesc(zf: zipfile.ZipFile):
    names = zf.namelist()
    candidates = [n for n in names if posixpath.basename(n).lower() == "moddesc.xml"]
    if not candidates:
        return None, ""
    # preferisci quello in radice, poi il più corto
    candidates.sort(key=lambda n: (n.count("/"), len(n)))
    return candidates[0], posixpath.dirname(candidates[0])


def parse_store_items(zf: zipfile.ZipFile, root, text: str, md_dir: str, l10n: dict[str, str]):
    refs = []
    if root is not None:
        for si in iter_local(root, "storeitem"):
            ref = si.attrib.get("xmlFilename") or si.attrib.get("filename")
            if ref:
                refs.append(ref)
    if not refs:
        refs = re.findall(r'<storeItem[^>]+(?:xmlFilename|filename)="([^"]+)"', text, re.I)

    items = []
    for ref in dict.fromkeys(refs):
        zip_path = posixpath.normpath(posixpath.join(md_dir, ref)).lstrip("/")
        if zip_path not in zf.namelist():
            continue
        sub_root, _ = parse_xml_file(zf, zip_path)
        if sub_root is None:
            continue
        store = find_child(sub_root, "storeData")
        if store is None:
            continue
        name_raw = node_text(find_child(store, "name"))
        name = pretty_store_name(resolve_l10n(name_raw, l10n), ref)
        cats = []
        for c in iter_local(store, "category"):
            val = (c.text or "").strip()
            if val and val not in cats:
                cats.append(val)
        price = safe_int(node_text(find_child(store, "price")))
        daily_upkeep = safe_int(node_text(find_child(store, "dailyUpkeep")))
        lifetime = safe_int(node_text(find_child(store, "lifetime")))
        finance_category = node_text(find_child(store, "financeCategory"))
        species = node_text(find_child(store, "species"))
        can_be_sold_raw = node_text(find_child(store, "canBeSold")).strip().lower()
        can_be_sold = True if can_be_sold_raw == "true" else False if can_be_sold_raw == "false" else None
        brand = resolve_l10n(node_text(find_child(store, "brand")), l10n)
        functions = []
        funcs = find_child(store, "functions")
        if funcs is not None:
            for f in list(funcs):
                val = resolve_l10n(node_text(f), l10n)
                if val:
                    functions.append(val)
        specs = find_child(store, "specs")
        power = max_speed = needed_power = weight = capacity = None
        working_width = None
        fill_types = []
        if specs is not None:
            def spec_value(tag):
                return node_text(find_child(specs, tag))

            power = safe_int(spec_value("power"))
            max_speed = safe_int(spec_value("maxspeed"))
            needed_power = safe_int(spec_value("neededpower"))
            working_width = safe_float(spec_value("workingwidth"))
            weight = safe_int(spec_value("weight"))
            capacity = safe_int(spec_value("capacity"))
            fill_raw = resolve_l10n(spec_value("filltypes"), l10n)
            fill_types = [x for x in re.split(r"[,;/\s]+", fill_raw) if x][:20]
        category_labels = []
        for cat in cats:
            label = map_store_category(cat, STORE_CATEGORIES) or cat.replace("_", " ").capitalize()
            if label not in category_labels:
                category_labels.append(label)
        items.append({
            "file": zip_path,
            "name": name or Path(ref).stem,
            "root_tag": strip_ns(sub_root.tag),
            "categories": cats,
            "category_labels": category_labels,
            "price": price,
            "daily_upkeep": daily_upkeep,
            "lifetime": lifetime,
            "can_be_sold": can_be_sold,
            "finance_category": finance_category,
            "species": species,
            "brand": brand,
            "functions": functions[:8],
            "power": power,
            "needed_power": needed_power,
            "maxSpeed": max_speed,
            "working_width": working_width,
            "weight": weight,
            "capacity": capacity,
            "fill_types": fill_types,
        })
    return items


def extract_icon(zf: zipfile.ZipFile, entry: dict, icon_name: str, icon_id: str,
                 icon_cache: dict[str, str], no_icons: bool) -> str | None:
    if no_icons:
        return None
    names = zf.namelist()
    lower_map = {n.lower(): n for n in names}
    candidate = None
    if icon_name:
        candidate = lower_map.get(icon_name.replace("\\", "/").lower())
    if not candidate:
        for key in ("icon.png", "icon.dds", "preview.png", "preview.dds",
                    "icon.jpg", "preview.jpg"):
            if key in lower_map:
                candidate = lower_map[key]
                break
    if not candidate:
        # ultima spiaggia: primo file icon_* o store_*
        for n in names:
            base = posixpath.basename(n).lower()
            if (base.startswith("icon_") or base.startswith("store_")) and base.endswith((".png", ".dds", ".jpg", ".jpeg")):
                candidate = n
                break
    if not candidate:
        return None
    if entry["sha256"] in icon_cache:
        return icon_cache[entry["sha256"]]
    try:
        blob = zf.read(candidate)
    except (KeyError, OSError, RuntimeError):
        return None
    if not blob:
        return None
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ICON_DIR / f"{icon_id}.png"
    tmp_path = None
    try:
        suffix = Path(candidate).suffix.lower() or ".img"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=str(ICON_DIR)) as tmp:
            tmp.write(blob)
            tmp_path = Path(tmp.name)
        if shutil.which("magick") or shutil.which("convert"):
            exe = "magick" if shutil.which("magick") else "convert"
            cmd = [exe, str(tmp_path), "-background", "none", "-gravity", "center",
                   "-thumbnail", "220x220", "-extent", "220x220", str(out_path)]
            proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            if proc.returncode != 0 or not out_path.exists():
                # secondo tentativo senza extent (alcune iconne hanno alpha problematica)
                cmd = [exe, str(tmp_path), "-thumbnail", "220x220", str(out_path)]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        elif suffix in (".png", ".jpg", ".jpeg"):
            shutil.copyfile(tmp_path, out_path)
        if out_path.exists() and out_path.stat().st_size > 0:
            rel = f"icons/{out_path.name}"
            icon_cache[entry["sha256"]] = rel
            return rel
    except Exception:
        pass
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
    return None


def item_type(item) -> str:
    if item.get("root_tag") == "placeable":
        return "piazzabile"
    cats = [t for c in item.get("categories", []) for t in category_tokens(c)]
    for cat in cats:
        if cat in VEHICLE_CATS:
            return "veicolo"
        if cat in TOOL_CATS:
            return "attrezzo"
        if cat in PLACEABLE_CATS:
            return "piazzabile"
    return "piazzabile"


def guess_type(store_items, has_map: bool, has_scripts: bool, lua_count: int,
               i3d_count: int, text: str, filename: str, key: str):
    if has_map:
        return "mappa"
    if key in SCRIPT_KEYS:
        return "script"
    if store_items:
        types = [item_type(item) for item in store_items]
        counts = {t: types.count(t) for t in set(types)}
        # Il primo oggetto è di solito quello principale (es. trattore nel pack)
        first = item_type(store_items[0])
        if len(store_items) >= 4 and len(counts) >= 3:
            return "pacchetto"
        if len(store_items) >= 3 and len(counts) >= 2 and max(counts.values()) / len(types) < 0.65:
            return "pacchetto"
        return first
    if has_scripts and i3d_count == 0:
        return "script"
    if lua_count > 0 and i3d_count == 0:
        return "script"
    low = (text + " " + filename).lower()
    if re.search(r"tractor|trattor|harvester|mietitrebbia", low):
        return "veicolo"
    if i3d_count > 0:
        return "piazzabile"
    if lua_count > 0 or "extraSourceFiles" in text:
        return "script"
    return "altro"


def broad_category(store_items, backup_folder: str, mod_type: str, text: str):
    if mod_type == "mappa":
        return "Mappe"
    if mod_type == "script":
        return "Script e utility"
    labels = []
    for item in store_items:
        for cat in item.get("categories", []):
            label = map_store_category(cat, SHOP_TO_BROAD)
            if label:
                labels.append(label)
                break
    if labels:
        counts = {}
        for label in labels:
            counts[label] = counts.get(label, 0) + 1
        best = max(counts.values())
        for label in labels:
            if counts[label] == best:
                return label
    if backup_folder in BACKUP_FOLDERS:
        return BACKUP_FOLDERS[backup_folder]
    low = text.lower()
    heuristic = [
        ("Produzioni", r"produc|production|filiere|trasform|ricett"),
        ("Acqua, letame e stalle", r"acqua|water|letame|manure|slurry|abbeveratoio"),
        ("Silos e stoccaggio", r"silo|bunker|insilato|storage|magazzino"),
        ("Costruzioni e decorazioni", r"shed|capannone|decor|house|casa|stalla|shelter"),
        ("Terraforming e strade", r"terraform|road|strada|paint"),
        ("Falci e fienagione", r"falci|mower|fieno|hay|baler|pressa"),
        ("Rimorchi e zavorre", r"trailer|rimorch|weight|zavorra"),
        ("Semina e colture", r"seeder|seminat|planter|coltura|sprayer|irrorat"),
        ("Lavorazione del suolo", r"plow|arat|cultivator|erpice|harrow|tiller|rullo"),
        ("Mietitrebbie e raccolta", r"harvester|mietitrebbia|combine|header"),
        ("Trattori e mezzi", r"tractor|trattor|truck|camion|telehandler|forklift"),
    ]
    for label, rx in heuristic:
        if re.search(rx, low):
            return label
    return "Altro"


def shop_category(store_items, mod_type: str) -> str:
    if mod_type == "mappa":
        return "Mappe"
    if mod_type == "script":
        return "Script"
    for item in store_items:
        for cat in item.get("categories", []):
            label = map_store_category(cat, STORE_CATEGORIES)
            if label:
                return label
    return ""


def make_tags(text: str, mod_type: str):
    tags = []
    low = text.lower()
    for label, rx in TAG_RULES:
        if re.search(rx, low):
            tags.append(label)
    if mod_type == "mappa" and "Mappa" not in tags:
        tags.insert(0, "Mappa")
    return tags[:8]


def short_description(desc: str) -> str:
    if not desc:
        return ""
    # taglia i changelog
    s = re.split(r"\n\s*(changelog|changes|novità|update log)\b", desc, flags=re.I)[0]
    s = s.strip()
    # primo paragrafo utile
    for block in re.split(r"\n\s*\n", s):
        block = block.strip()
        if len(block) >= 25 and not re.match(r"^(features|caratteristiche|keyboard|controls|comandi)\b", block, re.I):
            s = block
            break
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > 240:
        cut = s[:240]
        cut = cut.rsplit(" ", 1)[0]
        s = cut.rstrip(".,;:") + "…"
    return s


FALLBACK_PATTERNS = {
    "version": r"<version>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</version>",
    "author": r"<author>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</author>",
    "icon": r"<iconFilename>\s*(.*?)\s*</iconFilename>",
}


def fallback_field(text: str, key: str) -> str:
    m = re.search(FALLBACK_PATTERNS[key], text, re.S | re.I)
    return clean_text(m.group(1)) if m else ""


def scan_zip(path: Path, source: str, backup_folder: str, icon_cache: dict[str, str],
             no_icons: bool, prev: dict | None):
    resolved_path = path.resolve()
    try:
        rel = resolved_path.relative_to(GAME_DIR.resolve()).as_posix()
    except ValueError:
        rel = resolved_path.as_posix()
    stat = resolved_path.stat()
    entry = {
        "id": hashlib.sha1(rel.encode("utf-8")).hexdigest()[:10],
        "file": resolved_path.name,
        "stem": resolved_path.stem,
        "key": normalize_key(resolved_path.name),
        "source": source,
        "folder": backup_folder or "mods",
        "path": rel,
        "size": stat.st_size,
        "mtime": int(stat.st_mtime),
        "sha256": "",
        "title": path.stem,
        "version": "",
        "author": "",
        "desc": "",
        "desc_short": "",
        "icon": None,
        "has_moddesc": False,
        "moddesc_version": None,
        "multiplayer": None,
        "map": False,
        "deps": [],
        "store_items": [],
        "store_cats": [],
        "shop_category": "",
        "type": "altro",
        "category": "Altro",
        "tags": [],
        "l10n_count": 0,
        "tech": {},
        "health": [],
        "curated": None,
        "read_error": None,
    }

    # Cache: file invariato -> riusa i metadati (tranne campi globali).
    # Se in passato le icone erano disattivate, rileggi lo ZIP per estrarle.
    icon_ready = no_icons or bool(prev and prev.get("icon_checked"))
    if prev and icon_ready and prev.get("size") == stat.st_size and prev.get("mtime") == int(stat.st_mtime):
        cached = dict(prev)
        cached["path"] = rel
        cached["source"] = source
        cached["folder"] = backup_folder or "mods"
        cached["file"] = path.name
        cached["stem"] = path.stem
        cached["key"] = normalize_key(path.name)
        cached["health"] = []  # ricalcolata da base_health() a ogni scansione
        cached["curated"] = CURATED.get(cached["key"]) or CURATED.get(cached.get("title", "").lower())
        return cached

    try:
        zf = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as exc:
        entry["read_error"] = f"ZIP non valido: {exc}"
        entry["sha256"] = sha256_file(path)
        return entry

    with zf:
        names = zf.namelist()
        md_name, md_dir = get_moddesc(zf)
        text = ""
        root = None
        if md_name:
            entry["has_moddesc"] = True
            root, text = parse_xml_file(zf, md_name)

        l10n = parse_l10n(root, text) if text else {}

        title = version = author = desc = icon_name = ""
        if root is not None:
            title = localized(find_child(root, "title"))
            version = node_text(find_child(root, "version"))
            author = node_text(find_child(root, "author"))
            desc = localized(find_child(root, "description"))
            icon_name = node_text(find_child(root, "iconFilename"))
            entry["moddesc_version"] = safe_int(root.attrib.get("descVersion"))
            mp = find_child(root, "multiplayer")
            if mp is not None:
                entry["multiplayer"] = (mp.attrib.get("supported", "").lower() == "true")
            entry["map"] = find_child(root, "maps") is not None or bool(list(iter_local(root, "map")))
            deps = []
            dep_root = find_child(root, "dependencies")
            if dep_root is not None:
                for d in list(dep_root):
                    name = d.attrib.get("modName") or d.attrib.get("name") or node_text(d)
                    if name:
                        deps.append(name)
            entry["deps"] = deps
            entry["store_items"] = parse_store_items(zf, root, text, md_dir, l10n)
        else:
            # fallback regex
            version = fallback_field(text, "version")
            author = fallback_field(text, "author")
            icon_name = fallback_field(text, "icon")
            m = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
            if m:
                title = localized(ET.fromstring(f"<root>{m.group(1)}</root>")) if False else clean_text(re.sub(r"<[^>]+>", " ", m.group(1)))
            m = re.search(r"<description>(.*?)</description>", text, re.S | re.I)
            if m:
                desc = clean_text(re.sub(r"<[^>]+>", " ", m.group(1)))
            entry["map"] = "<maps>" in text.lower()

        title = title or path.stem
        desc = desc or ""
        entry.update({
            "title": title,
            "version": version,
            "author": author,
            "desc": desc,
            "desc_short": short_description(desc),
            "moddesc_version": entry["moddesc_version"],
            "multiplayer": entry["multiplayer"],
            "map": entry["map"],
            "deps": entry["deps"],
            "store_items": entry["store_items"],
        })

        # Statistiche tecniche
        exts = {}
        for name in names:
            ext = posixpath.splitext(name)[1].lower()
            if ext:
                exts[ext] = exts.get(ext, 0) + 1
        lua_count = exts.get(".lua", 0)
        xml_count = exts.get(".xml", 0)
        i3d_count = exts.get(".i3d", 0)
        has_scripts = (find_child(root, "extraSourceFiles") is not None) if root is not None else ("extraSourceFiles" in text)
        entry["tech"] = {
            "files": len([n for n in names if not n.endswith("/")]),
            "lua": lua_count,
            "xml": xml_count,
            "i3d": i3d_count,
            "dds": exts.get(".dds", 0),
            "sounds": sum(exts.get(e, 0) for e in (".ogg", ".wav", ".gls")),
            "uncompressed": sum(getattr(i, "file_size", 0) for i in zf.infolist()),
            "has_scripts": has_scripts,
            "has_l10n": bool(l10n),
        }
        entry["l10n_count"] = len(l10n)

        store_items = entry["store_items"]
        entry["store_cats"] = sorted({c for item in store_items for c in item.get("categories", [])})
        entry["type"] = guess_type(store_items, entry["map"], has_scripts, lua_count,
                                   i3d_count, f"{title} {desc}", path.name, entry["key"])
        entry["category"] = CATEGORY_OVERRIDES.get(entry["key"]) or broad_category(
            store_items, backup_folder, entry["type"], f"{title} {desc} {path.name}")
        entry["shop_category"] = shop_category(store_items, entry["type"])
        entry["tags"] = make_tags(f"{title} {desc} {' '.join(entry['store_cats'])}", entry["type"])

        entry["sha256"] = sha256_file(path)
        if not entry["icon"]:
            entry["icon"] = extract_icon(zf, entry, icon_name, entry["id"], icon_cache, no_icons)

    entry["icon_checked"] = True
    entry["curated"] = CURATED.get(entry["key"]) or CURATED.get(entry["title"].strip().lower())
    return entry


def base_health(entry: dict) -> list[dict]:
    """Controlli che dipendono solo dai metadata della singola mod.

    Vengono ricalcolati anche per le voci in cache, così gli avvisi non
    spariscono quando il file ZIP non è cambiato.
    """
    health = []
    if entry.get("read_error"):
        health.append({"level": "error", "code": "zip_non_valido",
                       "msg": entry["read_error"]})
    elif entry.get("has_moddesc", True) is False:
        health.append({"level": "error", "code": "moddesc_mancante",
                       "msg": "modDesc.xml non trovato nello ZIP."})
    if not entry.get("version"):
        health.append({"level": "warning", "code": "versione_mancante",
                       "msg": "Versione non dichiarata nel modDesc."})
    if len(entry.get("desc") or "") < 30:
        health.append({"level": "warning", "code": "descrizione_mancante",
                       "msg": "Descrizione assente o troppo breve."})
    if not entry.get("icon"):
        health.append({"level": "warning", "code": "icona_mancante",
                       "msg": "Nessuna icona/preview trovata nello ZIP."})
    if (entry.get("size") or 0) < 30000:
        health.append({"level": "warning", "code": "file_molto_piccolo",
                       "msg": f"File molto piccolo ({human_size(entry['size'])}): possibile download incompleto."})
    return health


# ---------------------------------------------------------------------------
# Scansione completa
# ---------------------------------------------------------------------------

def load_cache(force: bool) -> dict:
    if force or not CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return data.get("entries", {})
    except Exception:
        return {}


def load_modhub_cache() -> dict:
    """Record ufficiali ModHub, indicizzati per nome file locale."""
    if not MODHUB_CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(MODHUB_CACHE_FILE.read_text(encoding="utf-8"))
        return {str(k).lower(): v for k, v in (data.get("entries") or {}).items()}
    except Exception:
        return {}


def scan_all(no_icons: bool, force: bool, quiet: bool = False, extra_dirs: list[Path] | None = None):
    if not MODS_DIR.exists():
        sys.exit(f"Cartella non trovata: {MODS_DIR}")
    if not BACKUP_DIR.exists():
        sys.exit(f"Cartella non trovata: {BACKUP_DIR}")

    cache = load_cache(force)
    modhub = load_modhub_cache()
    new_cache = {}
    entries = []
    icon_cache: dict[str, str] = {}

    def with_official(entry):
        rec = modhub.get(entry["file"].lower()) or {}
        entry["official"] = rec.get("official") if rec.get("status") == "matched" else None
        entry["official_status"] = rec.get("status") or "unchecked"
        return entry

    # Mod attive
    for path in sorted(MODS_DIR.glob("*.zip"), key=lambda p: p.name.lower()):
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(GAME_DIR.resolve()).as_posix()
        except ValueError:
            rel = resolved.as_posix()
        prev = cache.get(rel)
        entry = with_official(scan_zip(resolved, "attiva", "", icon_cache, no_icons, prev))
        entry["health"] = base_health(entry)
        entries.append(entry)
        new_cache[rel] = {k: v for k, v in entry.items()
                          if k not in ("health", "curated", "official", "official_status")}

    # Archivio (la quarantena dei doppioni non fa parte dell'inventario attivo)
    for zip_path in sorted(BACKUP_DIR.rglob("*.zip"), key=lambda p: str(p).lower()):
        resolved = zip_path.resolve()
        if QUARANTINE_DIR.resolve() in resolved.parents:
            continue
        try:
            rel = resolved.relative_to(GAME_DIR.resolve()).as_posix()
        except ValueError:
            rel = resolved.as_posix()
        try:
            sub = resolved.parent.relative_to(BACKUP_DIR.resolve()).parts[0]
        except (ValueError, IndexError):
            sub = ""
        prev = cache.get(rel)
        entry = with_official(scan_zip(resolved, "backup", sub, icon_cache, no_icons, prev))
        entry["health"] = base_health(entry)
        entries.append(entry)
        new_cache[rel] = {k: v for k, v in entry.items()
                          if k not in ("health", "curated", "official", "official_status")}

    # Cartelle archivio aggiuntive (rilevamento automatico di mods-bck o cartelle passate via CLI)
    target_extra_dirs: list[Path] = []
    if extra_dirs:
        for ed in extra_dirs:
            p = Path(ed).resolve()
            if p.exists() and p not in target_extra_dirs and p != MODS_DIR.resolve() and p != BACKUP_DIR.resolve():
                target_extra_dirs.append(p)
    for auto_bck in [BASE_DIR / "mods-bck", GAME_DIR / "mods-bck"]:
        auto_p = auto_bck.resolve()
        if auto_p.exists() and auto_p not in target_extra_dirs and auto_p != MODS_DIR.resolve() and auto_p != BACKUP_DIR.resolve():
            target_extra_dirs.append(auto_p)

    for extra_dir in target_extra_dirs:
        for zip_path in sorted(extra_dir.rglob("*.zip"), key=lambda p: str(p).lower()):
            resolved = zip_path.resolve()
            if QUARANTINE_DIR.resolve() in resolved.parents:
                continue
            try:
                rel = resolved.relative_to(GAME_DIR.resolve()).as_posix()
            except ValueError:
                rel = resolved.as_posix()
            try:
                sub_parts = resolved.parent.relative_to(extra_dir).parts
                sub = f"{extra_dir.name}/{'/'.join(sub_parts)}" if sub_parts else extra_dir.name
            except (ValueError, IndexError):
                sub = extra_dir.name
            prev = cache.get(rel)
            entry = with_official(scan_zip(resolved, "backup", sub, icon_cache, no_icons, prev))
            entry["health"] = base_health(entry)
            entries.append(entry)
            new_cache[rel] = {k: v for k, v in entry.items()
                              if k not in ("health", "curated", "official", "official_status")}

    # ------------------------------------------------------------------
    # Gruppi duplicati / conflitti
    # ------------------------------------------------------------------
    by_hash: dict[str, list] = {}
    by_key: dict[str, list] = {}
    for e in entries:
        if e.get("sha256"):
            by_hash.setdefault(e["sha256"], []).append(e)
        by_key.setdefault(e["key"], []).append(e)

    for sha, group in by_hash.items():
        if len(group) > 1:
            ids = [e["id"] for e in group]
            for e in group:
                e["duplicate_group"] = sha[:12]
                e["copies"] = [i for i in ids if i != e["id"]]
                if not any(h["code"] == "duplicato_esatto" for h in e["health"]):
                    e["health"].append({
                        "level": "info", "code": "duplicato_esatto",
                        "msg": f"File identico presente {len(group)} volte (copia di sicurezza o doppione)."
                    })

    for key, group in by_key.items():
        if len(group) > 1:
            versions = {e.get("version") or "?" for e in group}
            hashes = {e.get("sha256") for e in group}
            conflict = len(versions) > 1 or len(hashes) > 1
            for e in group:
                e["same_key"] = [x["id"] for x in group if x["id"] != e["id"]]
                if conflict:
                    e["version_conflict"] = True
                    if not any(h["code"] == "conflitto_versione" for h in e["health"]):
                        e["health"].append({
                            "level": "warning", "code": "conflitto_versione",
                            "msg": f"Stessa mod in più versioni/contenuti: {', '.join(sorted(versions))}."
                        })
                else:
                    e["identical_copy"] = True

    # ------------------------------------------------------------------
    # Statistiche
    # ------------------------------------------------------------------
    def count(pred):
        return sum(1 for e in entries if pred(e))

    active = [e for e in entries if e["source"] == "attiva"]
    backup = [e for e in entries if e["source"] == "backup"]
    unique_keys = len(by_key)
    exact_dupes = sum(len(g) - 1 for g in by_hash.values() if len(g) > 1)
    duplicate_groups = sum(1 for g in by_hash.values() if len(g) > 1)
    conflicts = sum(1 for g in by_key.values()
                    if len(g) > 1 and (len({e.get("version") or "?" for e in g}) > 1 or len({e.get("sha256") for e in g}) > 1))
    issues = [e for e in entries if any(h["level"] in ("error", "warning") for h in e["health"])]
    errors = [e for e in entries if any(h["level"] == "error" for h in e["health"])]

    category_counts: dict[str, int] = {}
    for e in entries:
        category_counts[e["category"]] = category_counts.get(e["category"], 0) + 1

    type_counts: dict[str, int] = {}
    for e in entries:
        type_counts[e["type"]] = type_counts.get(e["type"], 0) + 1

    unique_map = {}
    for e in entries:
        prev = unique_map.get(e["key"])
        if prev is None or (e["source"] == "attiva" and prev["source"] != "attiva"):
            unique_map[e["key"]] = e
    unique_entries = list(unique_map.values())
    shop_items = sum(len(e.get("store_items") or []) for e in unique_entries)
    priced_items = sum(1 for e in unique_entries for item in (e.get("store_items") or [])
                       if item.get("price") is not None)
    official_matches = sum(1 for e in unique_entries if e.get("official"))
    official_votes = sum(int((e.get("official") or {}).get("votes") or 0) for e in unique_entries)

    stats = {
        "total_files": len(entries),
        "active": len(active),
        "backup": len(backup),
        "unique_mods": unique_keys,
        "exact_duplicate_files": exact_dupes,
        "duplicate_groups": duplicate_groups,
        "version_conflicts": conflicts,
        "issues": len(issues),
        "errors": len(errors),
        "size_active": sum(e["size"] for e in active),
        "size_backup": sum(e["size"] for e in backup),
        "size_total": sum(e["size"] for e in entries),
        "shop_items": shop_items,
        "priced_items": priced_items,
        "official_matches": official_matches,
        "official_votes": official_votes,
        "categories": dict(sorted(category_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "types": dict(sorted(type_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
    }

    meta = {
        "generated_at": int(time.time()),
        "generated_label": time.strftime("%d/%m/%Y %H:%M"),
        "game_version": (GAME_DIR / "VERSION").read_text(encoding="utf-8", errors="ignore").strip()
        if (GAME_DIR / "VERSION").exists() else "",
        "mods_dir": str(MODS_DIR),
        "backup_dir": str(BACKUP_DIR),
        "stats": stats,
        "category_colors": CATEGORY_COLORS,
        "type_labels": TYPE_LABELS,
    }

    if not entries or not MODS_DIR.is_dir():
        # Cartelle vuote o non montate: non sovrascrivo i dati e non tolgo le icone.
        print(f"Cartella {MODS_DIR} mancante o nessuna mod trovata: dati della dashboard lasciati com'erano.",
              file=sys.stderr)
        return {"meta": meta, "mods": []}

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ICON_DIR.mkdir(exist_ok=True)
    payload = {"meta": meta, "mods": entries}

    (DATA_DIR / "mods.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    js = "/* Generato da scan_mods.py - non modificare a mano */\nwindow.MODS_DATA = " + \
         json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (DATA_DIR / "mods.js").write_text(js, encoding="utf-8")
    CACHE_FILE.write_text(json.dumps({"version": 1, "entries": new_cache}, ensure_ascii=False),
                          encoding="utf-8")

    # Pulizia icone orfane
    valid_icons = {e["icon"].split("/")[-1] for e in entries if e.get("icon")}
    for p in ICON_DIR.glob("*.png"):
        if p.name not in valid_icons:
            try:
                p.unlink()
            except OSError:
                pass

    bck_count = sum(1 for e in entries if e.get("folder", "").startswith("mods-bck"))

    if not quiet:
        bck_info = f" (di cui {bck_count} in mods-bck)" if bck_count else ""
        print("\n" + "=" * 64)
        print("  MOD MANAGER FS25 - SCANSIONE COMPLETATA")
        print("=" * 64)
        print(f"  Mod attive ........ {stats['active']}")
        print(f"  Mod in archivio ... {stats['backup']}{bck_info}")
        print(f"  Mod uniche ........ {stats['unique_mods']}")
        print(f"  Duplicati esatti .. {stats['exact_duplicate_files']} file in {stats['duplicate_groups']} gruppi")
        print(f"  Conflitti versione  {stats['version_conflicts']}")
        print(f"  Criticità ......... {stats['issues']} (errori: {stats['errors']})")
        print(f"  Spazio totale ..... {human_size(stats['size_total'])}")
        print(f"  Dati .............. {DATA_DIR / 'mods.js'}")
        print(f"  Dashboard ......... {BASE_DIR / 'index.html'}")
        print("=" * 64 + "\n")
    return payload


def main():
    parser = argparse.ArgumentParser(description="Scanner mod FS25 per Mod Manager")
    parser.add_argument("--no-icons", action="store_true", help="salta estrazione/ conversione icone")
    parser.add_argument("--force", action="store_true", help="ignora la cache e rilegge tutto")
    parser.add_argument("--quiet", action="store_true", help="non stampare il riepilogo finale")
    parser.add_argument("--extra-dir", action="append", default=[], help="cartella aggiuntiva da scansionare")
    parser.add_argument("--fast", "--no-modhub", action="store_true", help="scansione rapida senza query esterne")
    args = parser.parse_args()
    scan_all(no_icons=args.no_icons, force=args.force, quiet=args.quiet,
             extra_dirs=[Path(d) for d in args.extra_dir])


if __name__ == "__main__":
    main()
