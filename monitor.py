"""
Edge Listing Monitor — główny skrypt.

Co robi:
1. Czyta listę aplikacji z config.yaml
2. Dla każdej apki pobiera aktualne metadane z App Store (iTunes API) i Google Play
3. Porównuje z poprzednim snapshotem (przechowywanym w folderze snapshots/)
4. Wykrywa zmiany tekstowe (opis, wersja, release notes) i wizualne (screeny, ikona)
5. Dla zmian wizualnych używa pHash + Gemini Vision do opisu
6. Generuje lokalny HTML dashboard (output/dashboard.html)
7. Opcjonalnie wysyła alerty na Google Chat i/lub email

Uruchomienie lokalne:
    pip install -r requirements.txt
    python monitor.py

Uruchomienie w GitHub Actions: zobacz .github/workflows/monitor.yml
"""

import os
import json
import hashlib
import datetime
from pathlib import Path
from io import BytesIO

import re
import difflib
import yaml
import requests
from PIL import Image
import imagehash
from deepdiff import DeepDiff
from jinja2 import Template
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Wspólny user-agent dla scrapingu — bez tego App Store / niektóre serwery zwracają pusto
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                  "Version/17.0 Safari/605.1.15",
    "Accept-Language": "en-US,en;q=0.9",
}

# Załaduj zmienne środowiskowe z pliku .env (lokalnie) lub z GitHub Secrets (w Actions)
load_dotenv()

# Ścieżki — wszystko relative do głównego folderu projektu
ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.yaml"
SNAPSHOTS_DIR = ROOT / "snapshots"
ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR = ROOT / "output"
HISTORY_DIR = ROOT / "history"

# Upewnij się, że foldery istnieją
SNAPSHOTS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
HISTORY_DIR.mkdir(exist_ok=True)

ALERTS_HISTORY_PATH = HISTORY_DIR / "alerts.jsonl"


# ============================================================
# SEKCJA 1: Pobieranie danych ze sklepów
# ============================================================

def fetch_ios_metadata(bundle_id: str, country: str = "us") -> dict:
    """Pobiera metadane apki z iTunes Lookup API (Apple) + In-App Events i screenshoty
    scrapowane ze strony apps.apple.com (lookup API ich nie zwraca dla wielu apek)."""
    url = f"https://itunes.apple.com/lookup?bundleId={bundle_id}&country={country}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    if data.get("resultCount", 0) == 0:
        raise ValueError(f"Nie znaleziono apki o bundle_id={bundle_id} w kraju {country}")

    app = data["results"][0]
    track_view_url = app.get("trackViewUrl")

    # iTunes lookup czasami zwraca puste screenshotUrls (np. dla Edge). Doczepiamy ze scrapingu.
    scraped = _fetch_ios_storefront_extras(track_view_url) if track_view_url else {}

    return {
        "platform": "ios",
        "country": country,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "name": app.get("trackName"),
        "version": app.get("version"),
        "release_date": app.get("currentVersionReleaseDate"),
        "description": app.get("description", "").strip(),
        "release_notes": app.get("releaseNotes", "").strip(),
        "seller_name": app.get("sellerName"),
        "price": app.get("price"),
        "category": app.get("primaryGenreName"),
        "rating_average": app.get("averageUserRating"),
        "rating_count": app.get("userRatingCount"),
        "size_bytes": int(app.get("fileSizeBytes", 0)),
        "images": {
            "icon": [app.get("artworkUrl512")] if app.get("artworkUrl512") else [],
            "screenshots_iphone": app.get("screenshotUrls", []) or scraped.get("screenshots_iphone", []),
            "screenshots_ipad": app.get("ipadScreenshotUrls", []) or scraped.get("screenshots_ipad", []),
        },
        "in_app_events": scraped.get("in_app_events", []),
        "store_url": track_view_url,
    }


def _fetch_ios_storefront_extras(track_view_url: str) -> dict:
    """Scrapuje stronę apps.apple.com — wyciąga In-App Events i fallback screenshoty.

    Zwraca dict z kluczami: in_app_events (list), screenshots_iphone, screenshots_ipad.
    Wszystko opcjonalne — przy błędzie zwraca puste listy.
    """
    try:
        r = requests.get(track_view_url, headers=HTTP_HEADERS, timeout=30)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        print(f"[WARN] Scraping apps.apple.com padł: {e}")
        return {}

    out = {"in_app_events": [], "screenshots_iphone": [], "screenshots_ipad": []}

    # Apple embeduje wszystkie dane w jednym JSON: <script type="application/json">
    m = re.search(r'<script type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return out
    try:
        page_data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return out

    try:
        item = page_data["data"][0]["data"]
    except (KeyError, IndexError, TypeError):
        return out

    # --- In-App Events ---
    events_shelf = (item.get("shelfMapping") or {}).get("appEvents") or {}
    for evt_item in events_shelf.get("items", []):
        page = (evt_item.get("clickAction") or {}).get("pageData") or {}
        ev = page.get("appEvent") or {}
        if not ev:
            continue
        out["in_app_events"].append({
            "id": ev.get("appEventId"),
            "title": ev.get("title"),
            "subtitle": ev.get("subtitle"),
            "detail": ev.get("detail"),
            "start_date": ev.get("startDate"),
            "end_date": ev.get("endDate"),
            "badge": ev.get("appEventBadgeKind"),
        })

    # --- Screenshots fallback ---
    # Apple trzyma URL-template w shelfMapping.product_media_phone_/_pad_.items[].screenshot.template
    # Template ma placeholdery {w}x{h}{c}.{f} — podstawiamy oryginalne wymiary i format jpeg.
    for shelf_key, out_key in (
        ("product_media_phone_", "screenshots_iphone"),
        ("product_media_pad_", "screenshots_ipad"),
    ):
        shelf = (item.get("shelfMapping") or {}).get(shelf_key) or {}
        urls = []
        for sh_item in shelf.get("items", []):
            art = sh_item.get("screenshot") or {}
            tpl = art.get("template")
            w = art.get("width")
            h = art.get("height")
            crop = art.get("crop") or "bb"
            fmt = "jpg"
            if tpl and w and h:
                urls.append(tpl.format(w=w, h=h, c=crop, f=fmt))
        if urls:
            out[out_key] = urls

    return out


def fetch_microsoft_release_notes(channel: str = "stable") -> dict:
    """Scrapuje oficjalny changelog Edge mobile z learn.microsoft.com.

    channel: 'stable' lub 'beta'. Zwraca dict z listą wersji (każda: wersja, data, sekcje).
    """
    url = f"https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-mobile-{channel}-channel"
    try:
        r = requests.get(url, headers=HTTP_HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"[WARN] Microsoft release notes fetch padł: {e}")
        return {"channel": channel, "url": url, "versions": [], "error": str(e)}

    soup = BeautifulSoup(r.text, "lxml")
    main = soup.find("main") or soup

    versions = []
    current = None
    # Iterujemy po nagłówkach w kolejności DOM — h2 = wersja, h3 = sekcja (np. "Bug fixes")
    for tag in main.find_all(["h2", "h3"]):
        text = tag.get_text(strip=True)
        if not text or text.lower() == "in this article":
            continue

        # Wersja: "Version 148.0.3967.55 (Android and iOS): May 11, 2026"
        ver_match = re.match(r"Version\s+([\d.]+)\s*\(([^)]+)\)[:\s]*(.+)", text)
        if tag.name == "h2" and ver_match:
            if current:
                versions.append(current)
            current = {
                "version": ver_match.group(1),
                "platforms": [p.strip() for p in ver_match.group(2).split("and")],
                "date": ver_match.group(3).strip(),
                "sections": [],
            }
            continue

        if tag.name == "h3" and current is not None:
            # Zbieramy treść do następnego nagłówka
            body_parts = []
            for sib in tag.find_next_siblings():
                if sib.name in ("h2", "h3"):
                    break
                body_parts.append(sib.get_text("\n", strip=True))
            current["sections"].append({
                "heading": text,
                "body": "\n".join(p for p in body_parts if p).strip(),
            })

    if current:
        versions.append(current)

    return {
        "channel": channel,
        "url": url,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "versions": versions[:20],  # ograniczamy żeby snapshot nie puchł
    }


def fetch_android_metadata(package_name: str, country: str = "us") -> dict:
    """Pobiera metadane apki z Google Play przez google-play-scraper."""
    from google_play_scraper import app as gp_app

    app = gp_app(package_name, lang="en", country=country)

    return {
        "platform": "android",
        "country": country,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "name": app.get("title"),
        "version": app.get("version"),
        "release_date": app.get("updated"),  # unix timestamp
        "description": (app.get("description") or "").strip(),
        "release_notes": (app.get("recentChanges") or "").strip(),
        "seller_name": app.get("developer"),
        "price": app.get("price"),
        "category": app.get("genre"),
        "rating_average": app.get("score"),
        "rating_count": app.get("ratings"),
        "size_bytes": 0,  # Google Play scraper nie zawsze zwraca
        "images": {
            "icon": [app.get("icon")] if app.get("icon") else [],
            "screenshots": app.get("screenshots", []),
            "feature_graphic": [app.get("headerImage")] if app.get("headerImage") else [],
            "video": [app.get("video")] if app.get("video") else [],
        },
        "store_url": app.get("url"),
    }


# ============================================================
# SEKCJA 2: Storage — zapis i odczyt snapshotów
# ============================================================

def snapshot_path(app_slug: str, platform: str) -> Path:
    """Ścieżka do pliku JSON ze snapshotem."""
    return SNAPSHOTS_DIR / f"{app_slug}_{platform}.json"


def load_previous_snapshot(app_slug: str, platform: str) -> dict | None:
    """Wczytuje poprzedni snapshot z dysku. Zwraca None jeśli to pierwszy run."""
    path = snapshot_path(app_slug, platform)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_snapshot(app_slug: str, platform: str, snapshot: dict) -> None:
    """Zapisuje snapshot do pliku JSON."""
    path = snapshot_path(app_slug, platform)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)


def append_alert_to_history(alert: dict) -> None:
    """Dopisuje wpis do history/alerts.jsonl (JSON Lines — jedna linijka = jeden alert).

    Format append-only — git pamięta pełną historię, plik rośnie liniowo ale wolno
    (kilka KB / alert). Czytane wstecz przez load_alert_history().
    """
    with open(ALERTS_HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert, ensure_ascii=False) + "\n")


def load_alert_history(limit: int = 50) -> list[dict]:
    """Wczytuje ostatnie N alertów (najnowsze na górze)."""
    if not ALERTS_HISTORY_PATH.exists():
        return []
    lines = ALERTS_HISTORY_PATH.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    out.reverse()  # najnowsze na górze
    return out


def asset_path(app_slug: str, platform: str, image_type: str, index: int) -> Path:
    """Ścieżka do zapisanego pliku obrazka."""
    folder = ASSETS_DIR / app_slug / platform
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{image_type}_{index}.png"


def download_image(url: str) -> bytes:
    """Pobiera plik obrazka z URL i zwraca jego bajty."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def save_image(data: bytes, path: Path) -> None:
    """Zapisuje bajty obrazka jako PNG na dysku."""
    # Konwertujemy do PNG dla spójności (Apple zwraca JPEG, Google PNG/WebP)
    img = Image.open(BytesIO(data))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(path, format="PNG", optimize=True)


# ============================================================
# SEKCJA 3: Detekcja zmian (tekst + obrazki)
# ============================================================

def detect_text_changes(current: dict, previous: dict) -> dict:
    """Wykrywa zmiany w polach tekstowych. Zwraca dict {pole: {old, new, diff?}}.

    Dla długich pól (description, release_notes) dodaje też 'diff' — listę linii
    z oznaczeniem czy są dodane / usunięte / kontekst, do ładnego renderu w dashboardzie.

    Świadomie POMIJAMY: rating_average, rating_count — tickają cały czas (każda nowa
    ocena = zmiana), generowałyby tylko szum w alertach. Jeśli ktoś chce monitorować
    ocenę — dodaj sobie do listy `fields` poniżej.
    """
    changes = {}
    fields = ["name", "version", "release_notes", "description",
              "price", "category"]
    diffable = {"description", "release_notes"}

    for field in fields:
        old_val = previous.get(field)
        new_val = current.get(field)
        if old_val != new_val:
            entry = {"old": old_val, "new": new_val}
            if field in diffable and isinstance(old_val, str) and isinstance(new_val, str):
                entry["diff"] = text_line_diff(old_val, new_val)
            changes[field] = entry

    return changes


def text_line_diff(old: str, new: str) -> list[dict]:
    """Line-by-line diff dwóch tekstów. Zwraca listę {'op': 'add'|'remove'|'context', 'text': str}.

    Używane do ładnego renderu w dashboardzie (kolorowanie dodanych/usuniętych linii).
    """
    old_lines = (old or "").splitlines() or [""]
    new_lines = (new or "").splitlines() or [""]
    sm = difflib.SequenceMatcher(None, old_lines, new_lines)
    result = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for line in old_lines[i1:i2]:
                result.append({"op": "context", "text": line})
        elif tag in ("replace", "delete"):
            for line in old_lines[i1:i2]:
                result.append({"op": "remove", "text": line})
            if tag == "replace":
                for line in new_lines[j1:j2]:
                    result.append({"op": "add", "text": line})
        elif tag == "insert":
            for line in new_lines[j1:j2]:
                result.append({"op": "add", "text": line})
    return result


def detect_iae_changes(current: list[dict], previous: list[dict]) -> list[dict]:
    """Wykrywa zmiany w In-App Events: dodane, usunięte, zmodyfikowane.

    Klucz: appEventId. Zwraca listę {'change_type': 'added'|'removed'|'modified', 'event': ...}.
    """
    current = current or []
    previous = previous or []
    cur_by_id = {e["id"]: e for e in current if e.get("id")}
    prev_by_id = {e["id"]: e for e in previous if e.get("id")}

    changes = []
    for eid, ev in cur_by_id.items():
        if eid not in prev_by_id:
            changes.append({"change_type": "added", "event": ev})
        else:
            old = prev_by_id[eid]
            if any(old.get(k) != ev.get(k) for k in ("title", "subtitle", "detail", "start_date", "end_date", "badge")):
                changes.append({"change_type": "modified", "event": ev, "previous": old})
    for eid, ev in prev_by_id.items():
        if eid not in cur_by_id:
            changes.append({"change_type": "removed", "event": ev})
    return changes


def detect_microsoft_release_changes(current: dict, previous: dict | None) -> dict | None:
    """Porównuje snapshoty release notes z learn.microsoft.com.

    Zwraca dict z listą NOWYCH wersji (te których nie było w poprzednim snapshocie),
    lub None gdy brak zmian.
    """
    if previous is None:
        return None
    cur_versions = current.get("versions", []) or []
    prev_versions = {v["version"] for v in (previous.get("versions") or [])}
    new_entries = [v for v in cur_versions if v.get("version") not in prev_versions]
    if not new_entries:
        return None
    return {"channel": current.get("channel"), "new_versions": new_entries}


def detect_visual_changes(
    current: dict,
    previous: dict,
    app_slug: str,
    platform: str,
    phash_threshold: int = 5,
) -> list[dict]:
    """
    Wykrywa zmiany w obrazkach używając trójstopniowego filtra:
    1. URL — jeśli identyczny, pomijamy
    2. SHA256 binarki — jeśli identyczny, to CDN reshuffle, pomijamy
    3. Perceptual hash — jeśli identyczny, to rekompresja, pomijamy

    Zwraca listę dict z opisem zmiany.
    """
    changes = []

    current_images = current.get("images", {})
    previous_images = previous.get("images", {})

    # Sprawdzamy wszystkie typy obrazków występujące w obecnym snapshocie
    for image_type, current_urls in current_images.items():
        previous_urls = previous_images.get(image_type, [])

        # Pomijamy video — hashowanie wideo nie ma sensu w MVP
        if image_type == "video":
            for i, url in enumerate(current_urls):
                old_url = previous_urls[i] if i < len(previous_urls) else None
                if url != old_url:
                    changes.append({
                        "image_type": image_type,
                        "index": i,
                        "change_type": "video_url_changed",
                        "new_url": url,
                        "old_url": old_url,
                    })
            continue

        for i, url in enumerate(current_urls):
            old_url = previous_urls[i] if i < len(previous_urls) else None

            # KROK 1: Porównanie URL
            if url == old_url:
                continue  # bez zmian

            # Pobieramy nowy obrazek
            try:
                new_data = download_image(url)
            except Exception as e:
                print(f"[WARN] Nie udało się pobrać {url}: {e}")
                continue

            old_path = asset_path(app_slug, platform, image_type, i)

            # Jeśli nie ma poprzedniego pliku (nowy obrazek dodany do listingu)
            if not old_path.exists():
                save_image(new_data, old_path)
                changes.append({
                    "image_type": image_type,
                    "index": i,
                    "change_type": "added",
                    "new_url": url,
                    "new_path": str(old_path.relative_to(ROOT)),
                })
                continue

            # KROK 2: SHA256
            old_data = old_path.read_bytes()
            old_sha = hashlib.sha256(old_data).hexdigest()
            new_sha = hashlib.sha256(new_data).hexdigest()
            if old_sha == new_sha:
                continue  # CDN reshuffle

            # KROK 3: Perceptual hash
            old_img = Image.open(old_path)
            new_img = Image.open(BytesIO(new_data))

            old_phash = imagehash.phash(old_img)
            new_phash = imagehash.phash(new_img)
            hash_distance = old_phash - new_phash

            if hash_distance < phash_threshold:
                # Tylko rekompresja, ignorujemy
                # ale aktualizujemy plik na dysku żeby przy następnym runie nie pobierać znowu
                save_image(new_data, old_path)
                continue

            # REALNA WIZUALNA ZMIANA
            # Zachowujemy stary plik jako "before", zapisujemy nowy
            before_path = old_path.with_name(f"{old_path.stem}_before.png")
            old_img.save(before_path, format="PNG")
            save_image(new_data, old_path)

            # Generujemy side-by-side
            sxs_path = generate_side_by_side(before_path, old_path, app_slug, platform, image_type, i)

            changes.append({
                "image_type": image_type,
                "index": i,
                "change_type": "changed",
                "new_url": url,
                "old_url": old_url,
                "before_path": str(before_path.relative_to(ROOT)),
                "after_path": str(old_path.relative_to(ROOT)),
                "side_by_side_path": str(sxs_path.relative_to(ROOT)),
                "phash_distance": hash_distance,
            })

    return changes


def generate_side_by_side(before_path: Path, after_path: Path,
                           app_slug: str, platform: str,
                           image_type: str, index: int) -> Path:
    """Generuje obrazek side-by-side (stary | nowy) z napisami."""
    before = Image.open(before_path).convert("RGB")
    after = Image.open(after_path).convert("RGB")

    # Skalujemy do tej samej wysokości
    target_height = 800
    before_w = int(before.width * (target_height / before.height))
    after_w = int(after.width * (target_height / after.height))
    before = before.resize((before_w, target_height), Image.LANCZOS)
    after = after.resize((after_w, target_height), Image.LANCZOS)

    # Tworzymy nowy obraz z przerwą między
    gap = 20
    canvas = Image.new("RGB", (before.width + after.width + gap, target_height), "white")
    canvas.paste(before, (0, 0))
    canvas.paste(after, (before.width + gap, 0))

    # Zapisz do folderu alertów
    alerts_dir = ASSETS_DIR / app_slug / platform / "_alerts"
    alerts_dir.mkdir(parents=True, exist_ok=True)
    out_path = alerts_dir / f"{image_type}_{index}_diff.png"
    canvas.save(out_path, format="PNG", optimize=True)

    return out_path


# ============================================================
# SEKCJA 4: Gemini Vision — AI opis zmiany
# ============================================================

def describe_visual_change_with_gemini(before_path: Path, after_path: Path) -> str | None:
    """
    Wysyła dwa obrazki do Gemini 2.5 Flash i prosi o opis różnicy po polsku.
    Zwraca tekst opisu lub None jeśli Gemini niedostępne.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        before_img = Image.open(before_path)
        after_img = Image.open(after_path)

        prompt = (
            "Porównaj te dwa screenshoty z App Store / Google Play dla tej samej aplikacji. "
            "Pierwszy obrazek to wersja STARA, drugi to NOWA. "
            "Opisz po polsku konkretnie co się zmieniło — tekst, kolory, ikony, layout, dodane/usunięte elementy. "
            "Maks 2-3 zdania. Jeśli nie widzisz istotnej różnicy, napisz 'Brak istotnej zmiany wizualnej'."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, before_img, after_img],
        )
        return response.text.strip()
    except Exception as e:
        print(f"[WARN] Gemini Vision nie zadziałał: {e}")
        return None


# ============================================================
# SEKCJA 5: Wzbogacenie zmian o AI opisy
# ============================================================

def enrich_with_ai_descriptions(changes: list[dict], use_gemini: bool) -> list[dict]:
    """Dla każdej realnej zmiany wizualnej dodaje opis z Gemini Vision."""
    if not use_gemini:
        return changes

    for change in changes:
        if change.get("change_type") == "changed":
            before = ROOT / change["before_path"]
            after = ROOT / change["after_path"]
            description = describe_visual_change_with_gemini(before, after)
            change["ai_description"] = description or "(brak opisu AI)"

    return changes


# ============================================================
# SEKCJA 6: Generowanie HTML dashboard
# ============================================================

DASHBOARD_TEMPLATE_PATH = ROOT / "templates" / "dashboard.html"


def _copy_to_output_assets(src_rel_path: str) -> str | None:
    """
    Kopiuje plik z assets/ do output/assets/ żeby dashboard publikowany przez GitHub Pages
    (Pages dostaje tylko folder output/) mógł go zlinkować.
    Zwraca ścieżkę relatywną od output/ (do użycia jako href w HTML), np. 'assets/...'.
    """
    if not src_rel_path:
        return None
    src = ROOT / src_rel_path
    if not src.exists():
        return None
    dst = OUTPUT_DIR / src_rel_path  # zachowujemy ten sam układ folderów
    dst.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(src, dst)
    return src_rel_path  # ścieżka relatywna od output/ jest taka sama


def generate_html_dashboard(
    all_changes: list[dict],
    all_current_states: list[dict] | None = None,
    ms_release_snapshots: list[dict] | None = None,
    ms_release_alerts: list[dict] | None = None,
    alert_history: list[dict] | None = None,
) -> Path:
    """Generuje plik output/dashboard.html.

    Sekcje:
      - Top: alerty (jeśli są zmiany)
      - Current State per app: ikonka, screenshoty, IAE, opis, wersja
      - Microsoft release notes: najnowsze wpisy z learn.microsoft.com

    Kopiuje obrazki referencjonowane w HTML do output/assets/.
    """
    all_current_states = all_current_states or []
    ms_release_snapshots = ms_release_snapshots or []
    ms_release_alerts = ms_release_alerts or []

    # 1) Kopiuj obrazki diffów do output/assets/
    for app_change in all_changes:
        for vc in app_change.get("visual_changes", []):
            for key in ("side_by_side_path", "before_path", "after_path", "new_path"):
                rel = vc.get(key)
                if rel:
                    copied = _copy_to_output_assets(rel)
                    if copied:
                        vc[key] = copied

    # 2) Kopiuj obrazki current state (ikona + screenshoty) do output/assets/
    for state in all_current_states:
        if state.get("icon_path"):
            copied = _copy_to_output_assets(state["icon_path"])
            if copied:
                state["icon_path"] = copied
        new_screenshots = []
        for p in state.get("screenshots", []):
            copied = _copy_to_output_assets(p)
            new_screenshots.append(copied or p)
        state["screenshots"] = new_screenshots

    with open(DASHBOARD_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = Template(f.read())

    html = template.render(
        all_changes=all_changes,
        all_current_states=all_current_states,
        ms_release_snapshots=ms_release_snapshots,
        ms_release_alerts=ms_release_alerts,
        alert_history=alert_history or [],
        generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    out_path = OUTPUT_DIR / "dashboard.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    # index.html duplikat — Pages domyślnie serwuje index.html
    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")

    return out_path


# ============================================================
# SEKCJA 7: Alerty (Google Chat i email)
# ============================================================

DASHBOARD_BASE_URL = os.getenv("DASHBOARD_BASE_URL", "https://jandziew.github.io/edge-listing-monitor")

# Image URLs muszą być DOSTĘPNE w momencie wysłania karty. GitHub Pages buduje się
# 15-30s po commit/push, więc gdyby karta linkowała do *.github.io/..., obrazek byłby
# 404 na pierwszym Cards V2 send (Google Chat cache'uje 404).
# raw.githubusercontent.com serwuje pliki w sekundach od pusha — niezawodne.
IMAGE_BASE_URL = os.getenv(
    "IMAGE_BASE_URL",
    "https://raw.githubusercontent.com/jandziew/edge-listing-monitor/main",
)


def _abs_url(rel_path: str | None) -> str | None:
    """Konwertuje relatywną ścieżkę (assets/...) na publiczny URL obrazka.
    Używamy raw.githubusercontent.com (instant po push), nie GitHub Pages
    (cold build 15-30s, race condition z momentem wysłania karty).
    """
    if not rel_path:
        return None
    return f"{IMAGE_BASE_URL.rstrip('/')}/{rel_path.lstrip('/')}"


def send_google_chat_alert(app_name: str, platform: str, text_changes: dict, visual_changes: list[dict],
                            iae_changes: list[dict] | None = None,
                            is_new_release: bool = False,
                            store_url: str | None = None,
                            app_icon_url: str | None = None) -> None:
    """Wysyła kartę Cards V2 do Google Chat Space przez incoming webhook.

    Format Cards V2 (zamiast plain text):
    - Header z nazwą apki + platformą + ikoną
    - Sekcje per typ zmiany (new release, text, visual, IAE)
    - Obrazki side-by-side (publiczny URL z GitHub Pages)
    - Fixed footer z przyciskami: View in store, Open dashboard

    Wymaga GOOGLE_CHAT_WEBHOOK_URL w env. Opcjonalnie DASHBOARD_BASE_URL
    (default: jandziew.github.io/edge-listing-monitor).
    """
    webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
    if not webhook_url:
        print("[INFO] GOOGLE_CHAT_WEBHOOK_URL not set, skipping Google Chat alert")
        return

    iae_changes = iae_changes or []
    sections = []

    # === SEKCJA: New release ===
    if is_new_release:
        new_v = (text_changes.get("version") or {}).get("new", "?")
        old_v = (text_changes.get("version") or {}).get("old", "?")
        sections.append({
            "header": "🚀 New release",
            "widgets": [{
                "decoratedText": {
                    "topLabel": "Version bump",
                    "text": f"<b>v{new_v}</b>",
                    "bottomLabel": f"Previous: v{old_v}",
                    "wrapText": True,
                }
            }],
        })

    # === SEKCJA: Text changes ===
    if text_changes:
        widgets = []
        for field, change in text_changes.items():
            if field == "version" and is_new_release:
                continue  # już pokazane wyżej
            old_val = str(change.get("old", ""))[:80]
            new_val = str(change.get("new", ""))[:80]
            widgets.append({
                "decoratedText": {
                    "topLabel": field,
                    "text": f"<font color=\"#16a34a\">{_html_escape(new_val)}</font>",
                    "bottomLabel": f"Was: {_html_escape(old_val)}" if old_val else "(new)",
                    "wrapText": True,
                }
            })
        if widgets:
            sections.append({
                "header": "Text changes",
                "collapsible": True,
                "uncollapsibleWidgetsCount": 3,
                "widgets": widgets,
            })

    # === SEKCJA: Visual changes ===
    if visual_changes:
        widgets = []
        for vc in visual_changes[:5]:  # max 5 żeby karta się nie rozdęła
            label = f"{vc['image_type']} #{vc['index']}"
            if vc["change_type"] == "changed":
                desc = vc.get("ai_description") or "Visual change detected."
                widgets.append({
                    "decoratedText": {
                        "topLabel": label,
                        "text": f"<b>Changed</b> — {_html_escape(desc[:200])}",
                        "wrapText": True,
                    }
                })
                # Dorzucamy side-by-side image (jeśli dostępny publicznie)
                sxs_url = _abs_url(vc.get("side_by_side_path"))
                if sxs_url:
                    widgets.append({"image": {"imageUrl": sxs_url, "altText": "Before vs after"}})
            elif vc["change_type"] == "added":
                widgets.append({
                    "decoratedText": {
                        "topLabel": label,
                        "text": "<b>Added</b> — new asset detected.",
                        "wrapText": True,
                    }
                })
                new_url = _abs_url(vc.get("new_path"))
                if new_url:
                    widgets.append({"image": {"imageUrl": new_url, "altText": "New asset"}})
            else:
                widgets.append({
                    "decoratedText": {
                        "topLabel": label,
                        "text": f"<b>{_html_escape(vc['change_type'])}</b>",
                        "wrapText": True,
                    }
                })
        if len(visual_changes) > 5:
            widgets.append({"textParagraph": {"text": f"<i>… and {len(visual_changes) - 5} more visual changes (see dashboard)</i>"}})
        sections.append({
            "header": "Visual changes",
            "collapsible": False,
            "widgets": widgets,
        })

    # === SEKCJA: In-App Events ===
    if iae_changes:
        widgets = []
        for ic in iae_changes:
            ev = ic.get("event") or {}
            change_label = ic["change_type"].upper()
            widgets.append({
                "decoratedText": {
                    "topLabel": f"In-App Event · {change_label}",
                    "text": f"<b>{_html_escape(ev.get('title') or '(no title)')}</b>",
                    "bottomLabel": _html_escape((ev.get("detail") or "")[:120]),
                    "wrapText": True,
                }
            })
        sections.append({"header": "In-App Events", "widgets": widgets})

    # Fallback gdy brak żadnych zmian (defensive — nie powinno się zdarzyć)
    if not sections:
        sections.append({"widgets": [{"textParagraph": {"text": "<i>Change detected but no details available.</i>"}}]})

    # === Header karty ===
    subtitle = f"{platform.upper()}"
    if is_new_release:
        subtitle = f"{platform.upper()} · 🚀 NEW RELEASE"
    elif visual_changes or text_changes or iae_changes:
        change_summary = []
        if text_changes: change_summary.append(f"{len(text_changes)} text")
        if visual_changes: change_summary.append(f"{len(visual_changes)} visual")
        if iae_changes: change_summary.append(f"{len(iae_changes)} IAE")
        subtitle = f"{platform.upper()} · {' · '.join(change_summary)}"

    header = {
        "title": app_name,
        "subtitle": subtitle,
    }
    if app_icon_url:
        header["imageUrl"] = app_icon_url
        header["imageType"] = "SQUARE"  # ikony apek są kwadratowe (lub CIRCLE)

    # === Przyciski jako buttonList na końcu (pewniejsze niż fixedFooter
    #     który nie zawsze renderuje się w webhookach) ===
    buttons = []
    if store_url:
        buttons.append({
            "text": "View in store",
            "onClick": {"openLink": {"url": store_url}},
            "color": {"red": 0.1, "green": 0.46, "blue": 0.82},
        })
    buttons.append({
        "text": "Open dashboard",
        "onClick": {"openLink": {"url": DASHBOARD_BASE_URL}},
    })
    sections.append({
        "widgets": [{"buttonList": {"buttons": buttons}}],
    })

    card = {
        "header": header,
        "sections": sections,
    }

    message = {
        "cardsV2": [{
            "cardId": f"alert-{app_name.lower().replace(' ', '-')}-{platform}",
            "card": card,
        }]
    }

    try:
        r = requests.post(webhook_url, json=message, timeout=15)
        r.raise_for_status()
        print(f"[OK] Sent Google Chat Cards V2 alert for {app_name} {platform}")
    except Exception as e:
        print(f"[ERR] Google Chat alert failed: {e}")
        # Fallback do plain text żeby user dostał chociaż coś
        try:
            fallback_text = f"*{app_name} ({platform.upper()})* — change detected. Dashboard: {DASHBOARD_BASE_URL}"
            requests.post(webhook_url, json={"text": fallback_text}, timeout=10).raise_for_status()
            print("[OK] Sent fallback plain-text Google Chat alert")
        except Exception as e2:
            print(f"[ERR] Plain-text fallback also failed: {e2}")


def _html_escape(text: str) -> str:
    """Escape znaków HTML dla Cards V2 (Google używa ograniczonego HTML w textParagraph/decoratedText)."""
    if not text:
        return ""
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _escape_telegram_md(text: str) -> str:
    """Escape znaków zarezerwowanych w Telegram MarkdownV2."""
    if text is None:
        return ""
    # https://core.telegram.org/bots/api#markdownv2-style
    specials = r"_*[]()~`>#+-=|{}.!\\"
    out = []
    for ch in str(text):
        if ch in specials:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def send_telegram_alert(app_name: str, platform: str, text_changes: dict, visual_changes: list[dict],
                          iae_changes: list[dict] | None = None,
                          is_new_release: bool = False) -> None:
    """
    Wysyła wiadomość na Telegram przez Bot API.
    Wymaga TELEGRAM_BOT_TOKEN i TELEGRAM_CHAT_ID w env.

    Jak założyć bota:
    1. Otwórz @BotFather w Telegramie, wyślij /newbot, podaj nazwę.
       Dostaniesz token w stylu '123456:ABC-DEF...' — to TELEGRAM_BOT_TOKEN.
    2. Wyślij dowolną wiadomość do swojego nowego bota.
    3. Otwórz https://api.telegram.org/bot<TOKEN>/getUpdates w przeglądarce.
       Znajdź "chat":{"id":...} — to TELEGRAM_CHAT_ID (może być ujemny dla grup).
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[INFO] TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID nie ustawione, pomijam Telegram")
        return

    # Header wiadomości
    if is_new_release:
        new_v = (text_changes.get("version") or {}).get("new", "?")
        header = f"🚀 *NEW RELEASE* \\- {_escape_telegram_md(app_name)} \\({platform.upper()}\\) v{_escape_telegram_md(new_v)}"
    else:
        header = f"*{_escape_telegram_md(app_name)} \\({platform.upper()}\\)* — wykryto zmiany"
    lines = [header]

    if text_changes:
        lines.append("")
        lines.append("*Tekst:*")
        for field, _change in text_changes.items():
            lines.append(f"• {_escape_telegram_md(field)}: zmieniono")

    if visual_changes:
        lines.append("")
        lines.append("*Grafika:*")
        for vc in visual_changes:
            label = f"{vc['image_type']} \\#{vc['index']}"
            if vc["change_type"] == "changed":
                desc = vc.get("ai_description", "")
                lines.append(f"• {_escape_telegram_md(label)}: {_escape_telegram_md(desc)}")
            elif vc["change_type"] == "added":
                lines.append(f"• {_escape_telegram_md(label)}: DODANY")
            else:
                lines.append(f"• {_escape_telegram_md(label)}: {_escape_telegram_md(vc['change_type'])}")

    if iae_changes:
        lines.append("")
        lines.append("*In\\-App Events:*")
        for ic in iae_changes:
            ev = ic.get("event", {})
            lines.append(f"• \\[{_escape_telegram_md(ic['change_type'].upper())}\\] {_escape_telegram_md(ev.get('title','(brak tytułu)'))}")

    text = "\n".join(lines)

    # Wyślij wiadomość tekstową
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "MarkdownV2"},
            timeout=15,
        )
        r.raise_for_status()
        print(f"[OK] Wysłano Telegram dla {app_name} {platform}")
    except Exception as e:
        print(f"[ERR] Telegram sendMessage nie poszedł: {e}")
        # Fallback bez markdown — jakby escape się sypnął
        try:
            plain = text.replace("\\", "")
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": plain},
                timeout=15,
            ).raise_for_status()
            print("[OK] Telegram (fallback bez markdown)")
        except Exception as e2:
            print(f"[ERR] Telegram fallback też padł: {e2}")
            return

    # Dla zmian wizualnych wyślij obrazek side-by-side
    for vc in visual_changes:
        sxs = vc.get("side_by_side_path")
        if not sxs:
            continue
        sxs_path = ROOT / sxs
        if not sxs_path.exists():
            continue
        try:
            with open(sxs_path, "rb") as photo:
                caption = f"{vc['image_type']} #{vc['index']} — {vc.get('ai_description','')}"
                requests.post(
                    f"https://api.telegram.org/bot{token}/sendPhoto",
                    data={"chat_id": chat_id, "caption": caption[:1024]},
                    files={"photo": photo},
                    timeout=30,
                ).raise_for_status()
        except Exception as e:
            print(f"[WARN] Telegram sendPhoto dla {vc['image_type']}#{vc['index']} padł: {e}")


def send_email_alert(app_name: str, platform: str, text_changes: dict, visual_changes: list[dict],
                      recipients: list[str],
                      iae_changes: list[dict] | None = None,
                      is_new_release: bool = False) -> None:
    """Wysyła email przez Resend API."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("[INFO] RESEND_API_KEY nie ustawiony, pomijam email")
        return
    if not recipients:
        print("[INFO] Brak odbiorców email, pomijam")
        return

    # Prosty HTML body
    if is_new_release:
        new_v = (text_changes.get("version") or {}).get("new", "?")
        html_body = f"<h2>🚀 NEW RELEASE — {app_name} ({platform.upper()}) v{new_v}</h2>"
        subject_prefix = f"🚀 NEW RELEASE v{new_v} — "
    else:
        html_body = f"<h2>{app_name} ({platform.upper()}) — wykryto zmiany</h2>"
        subject_prefix = ""

    if text_changes:
        html_body += "<h3>Tekst:</h3><ul>"
        for field, change in text_changes.items():
            html_body += f"<li><b>{field}</b>: zmieniono</li>"
        html_body += "</ul>"
    if visual_changes:
        html_body += "<h3>Grafika:</h3><ul>"
        for vc in visual_changes:
            desc = vc.get("ai_description", "")
            html_body += f"<li><b>{vc['image_type']} #{vc['index']}</b>: {vc['change_type']} — {desc}</li>"
        html_body += "</ul>"
    if iae_changes:
        html_body += "<h3>In-App Events:</h3><ul>"
        for ic in iae_changes:
            ev = ic.get("event", {})
            html_body += f"<li><b>[{ic['change_type'].upper()}]</b> {ev.get('title','(brak tytułu)')} — {ev.get('detail','')}</li>"
        html_body += "</ul>"

    payload = {
        "from": "Edge Monitor <onboarding@resend.dev>",
        "to": recipients,
        "subject": f"{subject_prefix}[{app_name}/{platform}] Zmiany w listingu",
        "html": html_body,
    }

    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        r.raise_for_status()
        print(f"[OK] Wysłano email dla {app_name} {platform}")
    except Exception as e:
        print(f"[ERR] Email nie poszedł: {e}")


# ============================================================
# SEKCJA 8: Main — uruchomienie całości
# ============================================================

def _download_all_current_images(app_slug: str, platform: str, current: dict) -> dict:
    """Pobiera i zapisuje wszystkie aktualne obrazki listingu. Zwraca mapping
    image_type → lista lokalnych ścieżek (relative do ROOT) — do użycia w dashboardzie.
    """
    local_paths: dict[str, list[str]] = {}
    for image_type, urls in (current.get("images") or {}).items():
        if image_type == "video":
            continue
        local_paths[image_type] = []
        for i, url in enumerate(urls):
            if not url:
                continue
            path = asset_path(app_slug, platform, image_type, i)
            if not path.exists():
                try:
                    data = download_image(url)
                    save_image(data, path)
                except Exception as e:
                    print(f"[WARN] Nie udało się pobrać {url}: {e}")
                    continue
            local_paths[image_type].append(str(path.relative_to(ROOT)))
    return local_paths


def _build_current_state(app_name: str, app_slug: str, platform: str,
                          current: dict, local_image_paths: dict) -> dict:
    """Buduje 'kartę' apki na dashboard — to co aktualnie jest w sklepie."""
    return {
        "app_name": app_name,
        "app_slug": app_slug,
        "platform": platform,
        "store_url": current.get("store_url"),
        "version": current.get("version"),
        "release_date": current.get("release_date"),
        "description": current.get("description", ""),
        "release_notes": current.get("release_notes", ""),
        "rating_average": current.get("rating_average"),
        "rating_count": current.get("rating_count"),
        "in_app_events": current.get("in_app_events", []),
        "icon_path": (local_image_paths.get("icon") or [None])[0],
        "screenshots": [
            p for key, paths in local_image_paths.items()
            if key.startswith("screenshots") or key == "feature_graphic"
            for p in paths
        ],
    }


def process_app_platform(app_config: dict, platform: str, settings: dict) -> dict:
    """Przetwarza jedną apkę na jednej platformie.

    Zwraca dict z:
      - current_state: zawsze (do wyświetlenia w sekcji 'Current State' dashboardu)
      - changes: None jeśli brak zmian, w przeciwnym razie szczegóły
    """
    app_slug = app_config["slug"]
    app_name = app_config["name"]

    print(f"\n=== {app_name} / {platform.upper()} ===")

    # Fetch
    try:
        if platform == "ios":
            current = fetch_ios_metadata(
                app_config["ios"]["bundle_id"],
                app_config["ios"].get("country", "us"),
            )
        elif platform == "android":
            current = fetch_android_metadata(
                app_config["android"]["package_name"],
                app_config["android"].get("country", "us"),
            )
        else:
            return {"current_state": None, "changes": None}
    except Exception as e:
        print(f"[ERR] Fetch failed: {e}")
        return {"current_state": None, "changes": None}

    # Previous snapshot
    previous = load_previous_snapshot(app_slug, platform)

    if previous is None:
        # Pierwszy run — baseline, bez alertu, ale wciąż pokazujemy aktualny stan
        print("[INFO] Pierwszy run — zapisuję baseline bez alertów")
        save_snapshot(app_slug, platform, current)
        local_paths = _download_all_current_images(app_slug, platform, current)
        return {
            "current_state": _build_current_state(app_name, app_slug, platform, current, local_paths),
            "changes": None,
        }

    # Detekcja zmian
    text_changes = detect_text_changes(current, previous)
    visual_changes = detect_visual_changes(
        current, previous, app_slug, platform,
        phash_threshold=settings.get("phash_threshold", 5),
    )
    iae_changes = detect_iae_changes(current.get("in_app_events", []),
                                      previous.get("in_app_events", []))

    # Czy to nowy release? (wersja się zmieniła)
    is_new_release = "version" in text_changes

    # Upewniamy się że mamy też wszystkie aktualne obrazki na dysku (do dashboardu)
    local_paths = _download_all_current_images(app_slug, platform, current)

    current_state = _build_current_state(app_name, app_slug, platform, current, local_paths)

    if not text_changes and not visual_changes and not iae_changes:
        print("[OK] Brak zmian")
        return {"current_state": current_state, "changes": None}

    # Wzbogacamy o AI
    visual_changes = enrich_with_ai_descriptions(
        visual_changes,
        use_gemini=settings.get("use_gemini_vision", True),
    )

    # Zapisujemy nowy snapshot
    save_snapshot(app_slug, platform, current)

    # Alerty
    alerts_cfg = settings.get("alerts", {})
    if alerts_cfg.get("google_chat", {}).get("enabled"):
        icon_url = (current.get("images") or {}).get("icon", [None])[0]
        send_google_chat_alert(app_name, platform, text_changes, visual_changes,
                                iae_changes=iae_changes, is_new_release=is_new_release,
                                store_url=current.get("store_url"),
                                app_icon_url=icon_url)
    if alerts_cfg.get("telegram", {}).get("enabled"):
        send_telegram_alert(app_name, platform, text_changes, visual_changes,
                             iae_changes=iae_changes, is_new_release=is_new_release)
    if alerts_cfg.get("email", {}).get("enabled"):
        send_email_alert(
            app_name, platform, text_changes, visual_changes,
            recipients=alerts_cfg["email"].get("recipients", []),
            iae_changes=iae_changes, is_new_release=is_new_release,
        )

    summary_parts = []
    if is_new_release:
        summary_parts.append("🚀 NEW RELEASE")
    summary_parts.append(f"{len(text_changes)} tekst, {len(visual_changes)} wizualnych, {len(iae_changes)} IAE")
    print(f"[OK] Wykryto zmiany: {' | '.join(summary_parts)}")

    detected_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    change_record = {
        "app_name": app_name,
        "app_slug": app_slug,
        "platform": platform,
        "store_url": current.get("store_url"),
        "is_new_release": is_new_release,
        "new_version": current.get("version") if is_new_release else None,
        "old_version": previous.get("version") if is_new_release else None,
        # release_date = kiedy NAPRAWDĘ apka się wydała (wg sklepu), nie kiedy my to złapaliśmy
        "store_release_date": current.get("release_date") if is_new_release else None,
        "text_changes": text_changes,
        "visual_changes": visual_changes,
        "iae_changes": iae_changes,
        "detected_at": detected_at,
    }

    # Historia — append zwięzłego wpisu (bez pełnych diffów obrazków, bez tekstów)
    append_alert_to_history({
        "detected_at": detected_at,
        "source": "app_store",
        "app_name": app_name,
        "app_slug": app_slug,
        "platform": platform,
        "store_url": current.get("store_url"),
        "is_new_release": is_new_release,
        "new_version": current.get("version") if is_new_release else None,
        "old_version": previous.get("version") if is_new_release else None,
        "store_release_date": current.get("release_date") if is_new_release else None,
        "n_text_changes": len(text_changes),
        "n_visual_changes": len(visual_changes),
        "n_iae_changes": len(iae_changes),
        "changed_fields": list(text_changes.keys()),
        "iae_titles": [(ic.get("event") or {}).get("title") for ic in iae_changes],
    })

    return {"current_state": current_state, "changes": change_record}


MS_RELEASE_SNAPSHOT = SNAPSHOTS_DIR / "microsoft_release_notes_{channel}.json"


def process_microsoft_release_notes(channels: list[str]) -> tuple[list[dict], list[dict]]:
    """Pobiera release notes dla każdego kanału, wykrywa nowe wersje.

    Zwraca (current_snapshots, change_alerts) — pierwsze do dashboardu, drugie do alertów.
    """
    current_snapshots = []
    change_alerts = []
    for channel in channels:
        print(f"\n=== Microsoft release notes / {channel} ===")
        current = fetch_microsoft_release_notes(channel)
        snap_path = Path(str(MS_RELEASE_SNAPSHOT).format(channel=channel))
        previous = None
        if snap_path.exists():
            previous = json.loads(snap_path.read_text(encoding="utf-8"))
        change = detect_microsoft_release_changes(current, previous)
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
        current_snapshots.append(current)
        if change:
            print(f"[OK] Nowe wersje na learn.microsoft.com: {[v['version'] for v in change['new_versions']]}")
            change_alerts.append(change)
            detected_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            for nv in change["new_versions"]:
                append_alert_to_history({
                    "detected_at": detected_at,
                    "source": "ms_release_notes",
                    "channel": channel,
                    "new_version": nv.get("version"),
                    "platforms": nv.get("platforms"),
                    "published_date": nv.get("date"),
                    "n_sections": len(nv.get("sections", [])),
                })
        elif previous is None:
            print("[INFO] Pierwszy run dla MS release notes — baseline")
        else:
            print("[OK] Brak nowych wersji")
    return current_snapshots, change_alerts


def main():
    # Wczytaj konfigurację
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    apps = config.get("apps", [])
    settings = config.get("settings", {})
    ms_channels = settings.get("microsoft_release_channels", ["stable"])

    print(f"Monitoruję {len(apps)} aplikacji...")

    all_current_states = []
    all_changes = []

    for app in apps:
        for platform in ("ios", "android"):
            if platform not in app:
                continue
            result = process_app_platform(app, platform, settings)
            if result.get("current_state"):
                all_current_states.append(result["current_state"])
            if result.get("changes"):
                all_changes.append(result["changes"])

    # Microsoft official release notes
    ms_snapshots, ms_release_alerts = process_microsoft_release_notes(ms_channels)

    # Cross-link: dla każdego app_change z is_new_release, szukamy wpisu o tej wersji
    # w MS snapshocie. Apple iTunes API potrafi zwracać wersję bez środkowych zer
    # (np. "148.3967.55" zamiast "148.0.3967.55"), więc dopuszczamy luźny match po
    # ostatnich 3 segmentach.
    ms_version_index = {}
    for snap in ms_snapshots:
        for v in snap.get("versions", []):
            ms_version_index[v["version"]] = {"channel": snap.get("channel"), **v}

    def _version_match(store_v: str, ms_v: str) -> bool:
        if not store_v or not ms_v:
            return False
        if store_v == ms_v:
            return True
        # iTunes Lookup często wycina środkowy "0" — Apple zwraca "148.3967.55"
        # zamiast pełnego "148.0.3967.55". Matchujemy po major + ostatnich 2 segmentach
        # (patch i build) — to są jedyne dwa numery które się realnie zmieniają.
        s_parts = store_v.split(".")
        m_parts = ms_v.split(".")
        return (len(s_parts) >= 3 and len(m_parts) >= 3
                and s_parts[0] == m_parts[0]
                and s_parts[-2:] == m_parts[-2:])

    for change in all_changes:
        if change.get("is_new_release"):
            sv = change.get("new_version")
            matched = ms_version_index.get(sv)
            if not matched:
                for mv, payload in ms_version_index.items():
                    if _version_match(sv, mv):
                        matched = payload
                        break
            if matched:
                change["ms_release_notes_match"] = matched

    # Generuj HTML dashboard
    if settings.get("generate_html_dashboard", True):
        history = load_alert_history(limit=100)
        dashboard_path = generate_html_dashboard(
            all_changes=all_changes,
            all_current_states=all_current_states,
            ms_release_snapshots=ms_snapshots,
            ms_release_alerts=ms_release_alerts,
            alert_history=history,
        )
        print(f"\n[OK] Dashboard: {dashboard_path}")

    print(f"\nGotowe. Wykryto zmiany w {len(all_changes)} listingach, "
          f"{len(ms_release_alerts)} nowych wpisów MS release notes.")


if __name__ == "__main__":
    main()
