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

import yaml
import requests
from PIL import Image
import imagehash
from deepdiff import DeepDiff
from jinja2 import Template
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env (lokalnie) lub z GitHub Secrets (w Actions)
load_dotenv()

# Ścieżki — wszystko relative do głównego folderu projektu
ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.yaml"
SNAPSHOTS_DIR = ROOT / "snapshots"
ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR = ROOT / "output"

# Upewnij się, że foldery istnieją
SNAPSHOTS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# SEKCJA 1: Pobieranie danych ze sklepów
# ============================================================

def fetch_ios_metadata(bundle_id: str, country: str = "us") -> dict:
    """Pobiera metadane apki z iTunes Lookup API (Apple)."""
    url = f"https://itunes.apple.com/lookup?bundleId={bundle_id}&country={country}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    if data.get("resultCount", 0) == 0:
        raise ValueError(f"Nie znaleziono apki o bundle_id={bundle_id} w kraju {country}")

    app = data["results"][0]

    # Wybieramy tylko interesujące pola — żeby snapshot był czytelny
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
            "screenshots_iphone": app.get("screenshotUrls", []),
            "screenshots_ipad": app.get("ipadScreenshotUrls", []),
        },
        "store_url": app.get("trackViewUrl"),
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
    """Wykrywa zmiany w polach tekstowych. Zwraca dict {pole: (stara, nowa)}."""
    changes = {}
    fields = ["name", "version", "release_notes", "description",
              "rating_average", "rating_count", "price", "category"]

    for field in fields:
        old_val = previous.get(field)
        new_val = current.get(field)
        if old_val != new_val:
            changes[field] = {"old": old_val, "new": new_val}

    return changes


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


def generate_html_dashboard(all_changes: list[dict]) -> Path:
    """Generuje plik output/dashboard.html ze wszystkimi wykrytymi zmianami.

    Kopiuje też obrazki side-by-side / before / after do output/assets/, żeby
    GitHub Pages (publikujący tylko folder output/) mógł je serwować.
    """
    # Przepisujemy ścieżki obrazków na takie, które będą działać po deployu Pages.
    # Modyfikujemy in-place w dictach — to OK, bo all_changes nie jest dalej używane.
    for app_change in all_changes:
        for vc in app_change.get("visual_changes", []):
            for key in ("side_by_side_path", "before_path", "after_path", "new_path"):
                rel = vc.get(key)
                if rel:
                    copied = _copy_to_output_assets(rel)
                    if copied:
                        vc[key] = copied

    with open(DASHBOARD_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = Template(f.read())

    html = template.render(
        all_changes=all_changes,
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

def send_google_chat_alert(app_name: str, platform: str, text_changes: dict, visual_changes: list[dict]) -> None:
    """Wysyła wiadomość do Google Chat Space przez incoming webhook."""
    webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
    if not webhook_url:
        print("[INFO] GOOGLE_CHAT_WEBHOOK_URL nie ustawiony, pomijam alert na Google Chat")
        return

    text_lines = [f"*{app_name} ({platform.upper()})* — wykryto zmiany"]

    if text_changes:
        text_lines.append("\n*Tekst:*")
        for field, change in text_changes.items():
            text_lines.append(f"• {field}: zmieniono")

    if visual_changes:
        text_lines.append("\n*Grafika:*")
        for vc in visual_changes:
            if vc["change_type"] == "changed":
                desc = vc.get("ai_description", "")
                text_lines.append(f"• {vc['image_type']} #{vc['index']}: {desc}")
            elif vc["change_type"] == "added":
                text_lines.append(f"• {vc['image_type']} #{vc['index']}: DODANY")

    message = {"text": "\n".join(text_lines)}

    try:
        requests.post(webhook_url, json=message, timeout=10).raise_for_status()
        print(f"[OK] Wysłano alert na Google Chat dla {app_name} {platform}")
    except Exception as e:
        print(f"[ERR] Google Chat alert nie poszedł: {e}")


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


def send_telegram_alert(app_name: str, platform: str, text_changes: dict, visual_changes: list[dict]) -> None:
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
    lines = [f"*{_escape_telegram_md(app_name)} \\({platform.upper()}\\)* — wykryto zmiany"]

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
                      recipients: list[str]) -> None:
    """Wysyła email przez Resend API."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("[INFO] RESEND_API_KEY nie ustawiony, pomijam email")
        return
    if not recipients:
        print("[INFO] Brak odbiorców email, pomijam")
        return

    # Prosty HTML body
    html_body = f"<h2>{app_name} ({platform.upper()}) — wykryto zmiany</h2>"
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

    payload = {
        "from": "Edge Monitor <onboarding@resend.dev>",
        "to": recipients,
        "subject": f"[{app_name}/{platform}] Zmiany w listingu",
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

def process_app_platform(app_config: dict, platform: str, settings: dict) -> dict | None:
    """Przetwarza jedną apkę na jednej platformie. Zwraca dict ze zmianami lub None."""
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
            return None
    except Exception as e:
        print(f"[ERR] Fetch failed: {e}")
        return None

    # Previous snapshot
    previous = load_previous_snapshot(app_slug, platform)

    if previous is None:
        # Pierwszy run — baseline, bez alertu
        print("[INFO] Pierwszy run — zapisuję baseline bez alertów")
        save_snapshot(app_slug, platform, current)
        # Pobierz i zapisz wszystkie aktualne obrazki
        for image_type, urls in current.get("images", {}).items():
            if image_type == "video":
                continue
            for i, url in enumerate(urls):
                if not url:
                    continue
                try:
                    data = download_image(url)
                    save_image(data, asset_path(app_slug, platform, image_type, i))
                except Exception as e:
                    print(f"[WARN] Nie udało się pobrać {url}: {e}")
        return None

    # Detekcja zmian
    text_changes = detect_text_changes(current, previous)
    visual_changes = detect_visual_changes(
        current, previous, app_slug, platform,
        phash_threshold=settings.get("phash_threshold", 5),
    )

    if not text_changes and not visual_changes:
        print("[OK] Brak zmian")
        return None

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
        send_google_chat_alert(app_name, platform, text_changes, visual_changes)
    if alerts_cfg.get("telegram", {}).get("enabled"):
        send_telegram_alert(app_name, platform, text_changes, visual_changes)
    if alerts_cfg.get("email", {}).get("enabled"):
        send_email_alert(
            app_name, platform, text_changes, visual_changes,
            recipients=alerts_cfg["email"].get("recipients", []),
        )

    print(f"[OK] Wykryto {len(text_changes)} zmian tekstowych i {len(visual_changes)} wizualnych")

    return {
        "app_name": app_name,
        "app_slug": app_slug,
        "platform": platform,
        "store_url": current.get("store_url"),
        "text_changes": text_changes,
        "visual_changes": visual_changes,
        "detected_at": datetime.datetime.now().isoformat(),
    }


def main():
    # Wczytaj konfigurację
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    apps = config.get("apps", [])
    settings = config.get("settings", {})

    print(f"Monitoruję {len(apps)} aplikacji...")

    all_changes = []

    for app in apps:
        for platform in ("ios", "android"):
            if platform not in app:
                continue
            result = process_app_platform(app, platform, settings)
            if result:
                all_changes.append(result)

    # Generuj HTML dashboard
    if settings.get("generate_html_dashboard", True):
        dashboard_path = generate_html_dashboard(all_changes)
        print(f"\n[OK] Dashboard: {dashboard_path}")

    print(f"\nGotowe. Wykryto zmiany w {len(all_changes)} listingach.")


if __name__ == "__main__":
    main()
