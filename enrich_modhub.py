#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arricchisce le mod con i dati pubblici del ModHub ufficiale.

Cerca ogni mod per nome/titolo, verifica che il nome file corrisponda e salva
nella cache: pagina ufficiale, valutazione, numero di voti, data di uscita,
piattaforme, categoria, autore e descrizione.

Il ModHub non pubblica il numero di download per singola mod: la dashboard
mostra i voti ufficiali, non un conteggio download inventato.

Uso:
    python3 enrich_modhub.py
    python3 enrich_modhub.py --limit 5
    python3 enrich_modhub.py --refresh
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODHUB_CACHE_FILE = DATA_DIR / "modhub_cache.json"
MODS_JSON = DATA_DIR / "mods.json"
MODHUB_BASE = "https://www.farming-simulator.com"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) ModManagerFS25/1.0"
DELAY = 0.35
_last_request = 0.0


class ModHubError(RuntimeError):
    pass


def polite_sleep(delay: float = DELAY):
    global _last_request
    wait = delay - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.monotonic()


def fetch(url: str, timeout: int = 30) -> str:
    polite_sleep()
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.8",
    })
    last_error = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read()
                return raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429 or 500 <= exc.code < 600:
                time.sleep(2 + attempt * 3)
                continue
            raise ModHubError(f"HTTP {exc.code} per {url}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            time.sleep(1 + attempt * 2)
    raise ModHubError(f"Impossibile scaricare {url}: {last_error}")


def strip_tags(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value or "", flags=re.I)
    value = re.sub(r"</(?:div|p|li|tr|h\d)>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value).replace("\xa0", " ")
    return value


def clean_lines(value: str) -> str:
    value = strip_tags(value)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in value.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def clean_inline(value: str) -> str:
    return re.sub(r"\s+", " ", clean_lines(value)).strip()


def norm(value: str) -> str:
    value = (value or "").lower()
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def parse_search_results(page: str) -> list[dict]:
    results = []
    chunks = page.split('<div class="mod-item">')[1:]
    for chunk in chunks:
        chunk = chunk[:5000]
        link = re.search(r'href="mod\.php\?mod_id=(\d+)&(?:amp;)?title=fs2025"', chunk)
        if not link:
            continue
        title = re.search(r"<h4>(.*?)</h4>", chunk, re.S)
        author = re.search(r"<span>By:\s*(.*?)</span>", chunk, re.S)
        rating = re.search(r'mod-item__rating-num">([^<]+)', chunk)
        results.append({
            "id": link.group(1),
            "title": clean_inline(title.group(1)) if title else "",
            "author": clean_inline(author.group(1)) if author else "",
            "rating": clean_inline(rating.group(1)) if rating else "",
        })
    return results


def parse_detail(page: str, mod_id: str) -> dict | None:
    def label(name: str):
        match = re.search(
            r"<b>" + re.escape(name) + r"</b></div>\s*<div class=\"table-cell\">(.*?)</div>",
            page, re.S,
        )
        return clean_inline(match.group(1)) if match else None

    title_match = re.search(r'<h2 class="column title-label">(.*?)</h2>', page, re.S)
    title = clean_inline(title_match.group(1)) if title_match else None
    filename = label("Filename")
    if not title or not filename:
        return None

    description = ""
    desc_match = re.search(r'<div class="top-line">(.*?)</div>', page, re.S)
    if desc_match:
        description = clean_lines(desc_match.group(1))
        description = description[:6000].strip()

    rating = None
    votes = None
    rating_match = re.search(r'mod-item__rating-num float-left">([^<]+)', page)
    if rating_match:
        rating_text = clean_inline(rating_match.group(1)).replace("\xa0", " ")
        number = re.search(r"([\d.,]+)\s*\(([\d.,]+)\)", rating_text)
        if number:
            try:
                rating = float(number.group(1).replace(",", "."))
                votes = int(number.group(2).replace(".", "").replace(",", ""))
            except ValueError:
                pass

    return {
        "id": str(mod_id),
        "url": f"{MODHUB_BASE}/mod.php?mod_id={mod_id}&title=fs2025&lang=en",
        "title": title,
        "filename": filename,
        "author": label("Author"),
        "manufacturer": label("Manufacturer"),
        "category": label("Category"),
        "size": label("Size"),
        "version": label("Version"),
        "released": label("Released"),
        "platform": label("Platform"),
        "rating": rating,
        "votes": votes,
        "description": description,
    }


def search(query: str) -> list[dict]:
    url = (f"{MODHUB_BASE}/mods.php?title=fs2025&lang=en&searchMod="
           + urllib.parse.quote(query))
    return parse_search_results(fetch(url))


def candidate_sort_key(candidate: dict, mod: dict):
    local_title = norm(mod.get("title"))
    cand_title = norm(candidate.get("title"))
    exact = 0 if cand_title == local_title else 1
    contains = 0 if local_title and (local_title in cand_title or cand_title in local_title) else 1
    return (exact, contains, candidate.get("title", "").lower())


def find_official(mod: dict, max_candidates: int = 3) -> dict | None:
    local_file = (mod.get("file") or "").lower()
    queries = []
    if len((mod.get("title") or "").strip()) >= 3:
        queries.append(mod["title"].strip())
    stem = re.sub(r"^fs25[_\-\s]*", "", Path(mod.get("file") or "").stem, flags=re.I)
    stem = stem.replace("_", " ").strip()
    if stem and all(norm(stem) != norm(q) for q in queries):
        queries.append(stem)

    checked = set()
    for query in queries:
        try:
            results = search(query)
        except ModHubError as exc:
            print(f"    avviso: {exc}", file=sys.stderr)
            continue
        results.sort(key=lambda c: candidate_sort_key(c, mod))
        for candidate in results[:max_candidates]:
            if candidate["id"] in checked:
                continue
            checked.add(candidate["id"])
            try:
                detail = parse_detail(
                    fetch(f"{MODHUB_BASE}/mod.php?mod_id={candidate['id']}&title=fs2025&lang=en"),
                    candidate["id"],
                )
            except ModHubError as exc:
                print(f"    avviso: {exc}", file=sys.stderr)
                continue
            if detail and detail["filename"].lower() == local_file:
                detail["description"] = detail.get("description") or ""
                return detail
    return None


def local_records() -> list[dict]:
    data = json.loads(MODS_JSON.read_text(encoding="utf-8"))
    mods = data.get("mods") or []
    by_file = {}
    for mod in mods:
        key = (mod.get("file") or "").lower()
        if not key:
            continue
        current = by_file.get(key)
        if current is None or (mod.get("source") == "attiva" and current.get("source") != "attiva"):
            by_file[key] = mod
    return sorted(by_file.values(), key=lambda m: (m.get("title") or "").lower())


def load_cache() -> dict:
    if not MODHUB_CACHE_FILE.exists():
        return {"version": 1, "entries": {}}
    try:
        data = json.loads(MODHUB_CACHE_FILE.read_text(encoding="utf-8"))
        data.setdefault("version", 1)
        data.setdefault("entries", {})
        return data
    except Exception:
        return {"version": 1, "entries": {}}


def save_cache(cache: dict):
    cache["updated_at"] = int(time.time())
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = MODHUB_CACHE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(MODHUB_CACHE_FILE)


def main():
    global DELAY
    parser = argparse.ArgumentParser(description="Arricchisce le mod con i dati ufficiali ModHub")
    parser.add_argument("--refresh", action="store_true", help="ricontrolla anche le mod già in cache")
    parser.add_argument("--limit", type=int, default=0, help="fermati dopo N mod (per prova)")
    parser.add_argument("--delay", type=float, default=DELAY, help="pausa tra richieste in secondi")
    args = parser.parse_args()
    DELAY = max(0.1, args.delay)

    if not MODS_JSON.exists():
        sys.exit("Manca data/mods.json: esegui prima ./aggiorna.sh")
    mods = local_records()
    cache = load_cache()
    entries = cache["entries"]

    todo = []
    for mod in mods:
        key = mod["file"].lower()
        cached = entries.get(key)
        fresh = (cached and not args.refresh
                 and cached.get("local_version") == mod.get("version")
                 and cached.get("local_size") == mod.get("size"))
        if not fresh:
            todo.append(mod)
    if args.limit:
        todo = todo[:args.limit]

    print(f"ModHub: {len(mods)} mod uniche, {len(todo)} da aggiornare.")
    matched = 0
    not_found = 0
    errors = 0
    for index, mod in enumerate(todo, 1):
        label = (mod.get("title") or mod.get("file"))[:48]
        try:
            official = find_official(mod)
        except ModHubError as exc:
            print(f"[{index}/{len(todo)}] {label}: errore ({exc})")
            errors += 1
            continue
        except Exception as exc:  # rete/parsing: non bloccare l'intera scansione
            print(f"[{index}/{len(todo)}] {label}: errore imprevisto ({exc})")
            errors += 1
            continue

        record = {
            "status": "matched" if official else "not_found",
            "checked_at": int(time.time()),
            "local_version": mod.get("version"),
            "local_size": mod.get("size"),
            "query": mod.get("title"),
        }
        if official:
            record["official"] = official
            matched += 1
            rating = official.get("rating")
            votes = official.get("votes")
            extra = f"★ {rating} ({votes} voti)" if rating is not None else "scheda trovata"
            print(f"[{index}/{len(todo)}] {label}: {extra}")
        else:
            not_found += 1
            print(f"[{index}/{len(todo)}] {label}: non trovata sul ModHub")
        entries[mod["file"].lower()] = record
        if index % 10 == 0:
            save_cache(cache)

    save_cache(cache)
    print(f"\nFatto: {matched} abbinate, {not_found} non trovate, {errors} errori.")
    print(f"Cache: {MODHUB_CACHE_FILE}")


if __name__ == "__main__":
    main()
