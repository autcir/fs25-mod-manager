#!/usr/bin/env python3
"""Copia di sicurezza di tutte le mod FS25 sul disco EROSBACKUP.

Copia (mai sposta, mai cancella) i file veri di:
  - ~/Projects/fs25/mods            -> <dest>/archivio/
  - ~/Projects/fs25/BACKUP_MODS     -> <dest>/BACKUP_MODS/   (stessa struttura)
  - ogni set di run.sh (mods, mods-pizzeria, ...): solo i file veri, i link no -> <dest>/set/<cartella>/

Sulla destinazione non cancella niente: un file già copiato e uguale (stessa dimensione e data) si salta;
se è cambiato, la copia vecchia viene rinominata in <nome>.vecchio-<data> e poi si copia il nuovo.

    nice -n 19 ionice -c3 python3 backup_mods.py --dest /run/media/autcir/EROSBACKUP/fs25-mods
    python3 backup_mods.py --dest ... --prova      # dice cosa copierebbe, senza copiare
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import server  # noqa: E402  (stessi percorsi e stessi set del Mod Manager)


def sorgenti():
    """(origine, percorso relativo nella destinazione) per ogni file vero da copiare."""
    viste = set()
    if server.ARCHIVE_DIR.is_dir():
        for f in sorted(server.ARCHIVE_DIR.iterdir()):
            if f.is_file() and not f.is_symlink() and not f.name.startswith("."):
                yield f, Path("archivio") / f.name
    bm = server.ROOT_PROJECT / "BACKUP_MODS"
    if bm.is_dir():
        for f in sorted(bm.rglob("*")):
            if f.is_file() and not f.is_symlink() and "codice-" not in str(f.relative_to(bm)).split("/")[0]:
                yield f, Path("BACKUP_MODS") / f.relative_to(bm)
    for cartella in server.set_dal_launcher().values():
        if cartella in viste or not cartella.is_dir():
            continue
        viste.add(cartella)
        for f in sorted(cartella.rglob("*")):
            # solo file veri: i link puntano all'archivio, già copiato sopra
            rel = f.relative_to(cartella)
            if f.is_symlink() or any((cartella / p).is_symlink() for p in rel.parents if str(p) != "."):
                continue
            if f.is_file():
                yield f, Path("set") / cartella.name / f.relative_to(cartella)


def uguale(a, b):
    sa, sb = a.stat(), b.stat()
    return sa.st_size == sb.st_size and int(sa.st_mtime) == int(sb.st_mtime)


def copia(dest, prova=False):
    if not dest.parent.exists():
        raise SystemExit(f"Destinazione non raggiungibile: {dest.parent} (disco non montato?)")
    copiati, saltati, aggiornati, byte = 0, 0, 0, 0
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for src, rel in sorgenti():
        dst = dest / rel
        if dst.exists() and uguale(src, dst):
            saltati += 1
            continue
        if prova:
            print(("aggiorna " if dst.exists() else "copia    ") + str(rel))
            copiati += 1
            byte += src.stat().st_size
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            dst.rename(dst.with_name(f"{dst.name}.vecchio-{stamp}"))  # la copia vecchia resta
            aggiornati += 1
        tmp = dst.with_name(f".{dst.name}.parte")
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)
        copiati += 1
        byte += src.stat().st_size
    esito = {"quando": datetime.now().isoformat(timespec="seconds"), "copiati": copiati,
             "aggiornati": aggiornati, "gia_uguali": saltati, "byte_copiati": byte, "prova": prova}
    if not prova:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "ULTIMA_COPIA.json").write_text(json.dumps(esito, indent=1), encoding="utf-8")
        prop = dest / "PROPRIETARIO.md"
        if not prop.exists():
            prop.write_text(
                "# fs25-mods: copia di sicurezza delle mod FS25\n\n"
                "- Chi: Mod Manager FS25 (`~/Projects/fs25/MOD_MANAGER/backup_mods.py`), creata da fsLaya/Claude per Ciro.\n"
                f"- Creata: {datetime.now().date()}\n"
                "- Cosa: copia dei file veri di `~/Projects/fs25/mods`, `BACKUP_MODS` e dei set di `run.sh`.\n"
                "- Si toglie quando: mai da sola; solo se Ciro lo chiede.\n", encoding="utf-8")
    return esito


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--prova", action="store_true", help="mostra cosa copierebbe, senza copiare")
    a = ap.parse_args()
    print(json.dumps(copia(a.dest, a.prova), ensure_ascii=False))


if __name__ == "__main__":
    main()
