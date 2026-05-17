# HANDOVER — Edge Listing Monitor (kontynuacja w Claude Code)

> **Jak użyć:** skopiuj cały ten plik jako pierwszy prompt do Claude Code w folderze projektu. Claude Code zrozumie cały kontekst, stan obecny i co dalej. Nie musisz nic dopisywać.

---

## Context — co budujemy i po co

Buduję **Edge Listing Monitor** — Python skrypt który automatycznie monitoruje listing aplikacji w App Store i Google Play, wykrywa zmiany (tekst + grafika), opisuje je przez AI i alertuje na różnych kanałach.

**Cel produktowy:** klient (nietechniczny, marketing/biznes) ma dostawać alert gdy Microsoft Edge zmieni cokolwiek na swojej stronie w sklepach (opis, screen, ikonę, release notes).

**Cel edukacyjny:** to ma być projekt szkoleniowy — pokazuję klientowi jak Google Antigravity / Claude Code pozwala nietechnicznej osobie zbudować realny tool. Warsztat 2h z klientem zaplanowany na jutro.

**Stack:** Python 3.11, GitHub Actions cron co 6h, Gemini 2.5 Flash Vision do AI opisów, Google Chat / email / Telegram do alertów, GitHub Pages do hostingu dashboardu HTML.

---

## Current state — co już jest gotowe

Folder projektu `edge-listing-monitor/` zawiera kompletny działający MVP. Struktura:

```
edge-listing-monitor/
├── README.md                    # instrukcja dla klienta (PL)
├── config.yaml                  # lista monitorowanych apek + ustawienia
├── monitor.py                   # główny skrypt (~450 linii, 8 sekcji)
├── requirements.txt             # zależności pip
├── .env.example                 # szablon kluczy API
├── .gitignore
├── templates/
│   └── dashboard.html           # Jinja2 template, Tailwind CSS
└── .github/workflows/
    └── monitor.yml              # cron + auto-deploy GitHub Pages
```

**monitor.py** ma 8 sekcji logicznych:
1. Pobieranie danych ze sklepów (`fetch_ios_metadata`, `fetch_android_metadata`)
2. Storage (snapshoty JSON + obrazki na dysku)
3. Detekcja zmian tekstowych i wizualnych (trójstopniowy filtr URL → SHA256 → pHash)
4. Gemini Vision — opis zmian wizualnych
5. Wzbogacenie zmian o AI opisy
6. Generowanie HTML dashboard
7. Alerty — Google Chat webhook + email przez Resend (Telegram TODO)
8. Main loop

**Co już działa (sprawdzone konceptualnie, nieprzetestowane lokalnie):**
- Fetch iTunes Lookup API dla Edge (`com.microsoft.msedgemobi`)
- Fetch Google Play scraper dla Edge (`com.microsoft.emmx`)
- Porównanie snapshotów JSON
- Trójstopniowy filtr obrazków
- Generowanie side-by-side PNG przez Pillow
- HTML dashboard generowany z Jinja2 template
- GitHub Actions workflow z auto-commitem i deploy na Pages

---

## Decisions already made (nie rozkminiaj na nowo)

- **Język:** Python (nie Node) — czytelność dla nietechnicznego klienta
- **AI Vision:** Gemini 2.5 Flash (free tier 1500 req/dobę), nie Claude — bo spójne z Google ekosystemem (Antigravity to Google)
- **Storage:** pliki JSON w repo + git history (Simon Willison "git scraping" pattern), bez bazy danych
- **Hosting dashboardu:** GitHub Pages (nie Vercel) — prostsze, w tym samym repo
- **Threshold pHash:** 5 (standard, ignoruje rekompresję, łapie realne zmiany)
- **Kanały alertów:** Google Chat (jeśli klient ma Workspace) + email przez Resend, Telegram jako fallback dla osób bez Workspace
- **Scope MVP:** tylko Microsoft Edge iOS + Android, lokalizacja `us`. Inne apki/lokalizacje przez config.yaml.
- **Cron:** co 6h w GitHub Actions

---

## Known issues / gaps to verify

**Priorytet wysoki (sprawdź pierwsze):**

1. **Biblioteka Gemini — nazwa pakietu może być nieaktualna.** W `requirements.txt` mam `google-genai>=0.3.0`. Google przenosił to z `google-generativeai`. Jeśli `pip install -r requirements.txt` rzuci błąd na tej linijce — sprawdź na PyPI która jest aktualna, popraw `requirements.txt` i import w sekcji 4 `monitor.py` (`from google import genai` może wymagać zmiany na `import google.generativeai as genai` + refaktor wywołania `client.models.generate_content`).

2. **Telegram support — brak.** W planie warsztatu jest jako "pierwsze ćwiczenie do dodania", ale jeśli klient nie ma Workspace, brak Google Chat → bez Telegrama klient nie ma alertów (poza emailem). **Dodaj funkcję `send_telegram_alert` w sekcji 7 monitor.py** (analogicznie do `send_google_chat_alert`). Powinna:
   - Czytać `TELEGRAM_BOT_TOKEN` i `TELEGRAM_CHAT_ID` z env
   - Wysyłać tekst przez `https://api.telegram.org/bot{TOKEN}/sendMessage` (markdown_v2)
   - Dla każdej zmiany wizualnej wysyłać też obrazek side-by-side przez `/sendPhoto` (multipart upload)
   - Dodaj `alerts.telegram.enabled` w `config.yaml`
   - Dodaj `TELEGRAM_BOT_TOKEN` i `TELEGRAM_CHAT_ID` w `.env.example`
   - Krótka instrukcja w README jak założyć bot przez `@BotFather` i jak znaleźć `chat_id` (POST do `/getUpdates` po wysłaniu wiadomości botowi).

3. **Pierwszy run lokalnie nie testowany.** Najprawdopodobniej zadziała, ale niektóre rzeczy do weryfikacji:
   - Czy `google-play-scraper` zwraca pole `headerImage` (używam jako feature_graphic) — mogło się zmienić
   - Czy `Image.open` poradzi sobie z WebP z Google Play (potrzebny Pillow z WebP support — domyślnie jest)
   - Czy `imagehash.phash` działa na obrazkach RGBA (przed konwersją do RGB)
   - Czy timezone w `datetime.datetime.now(datetime.timezone.utc).isoformat()` zwraca string bez problemu w JSON-ie

4. **Workflow GH Actions ma `permissions: contents: write` — sprawdź czy `peaceiris/actions-gh-pages@v3` nadal działa.** Możliwe że potrzebna jest aktualizacja na nowszą wersję lub natywne GitHub Pages deployment przez `actions/deploy-pages@v4`.

**Priorytet średni (po pierwszym testowym runie):**

5. **HTML dashboard — ścieżki obrazków.** Template używa `<img src="../{{ vc.side_by_side_path }}">` co zadziała lokalnie ale **nie zadziała na GitHub Pages** (publikujemy tylko folder `output/`, bez `assets/`). Trzeba albo:
   - Kopiować obrazki do `output/assets/` przed deployem
   - Lub publikować całe repo na Pages (Source: branch `main` zamiast `gh-pages`) i używać ścieżki względnej
   - Lub embedować obrazki jako base64 w HTML (gorsze ale samodzielne)

6. **Pierwszy run baseline = brak alertów.** To celowe, ale warto dodać flagę `--force-alerts` do testowania albo CLI argument do podmiany snapshotu.

7. **Brak error handlingu na poziomie main()** — jeśli jedna apka się wywali, leci dalej. To OK, ale warto logować błędy do `output/errors.json` żeby było widać w dashboardzie.

**Priorytet niski (nice-to-have):**

8. **Brak monitorowania Microsoft release notes z `learn.microsoft.com`** — w PRD jest, w kodzie nie. Sekcja `fetch_microsoft_release_notes(channel: str)` do dorzucenia.
9. **Brak In-App Events scraping** — celowo, do v2.
10. **Brak progress baru/lepszego loggingu** — dla nietechnicznego klienta `print()` jest OK, ale `rich` bibloteka by ładnie wyglądała.

---

## First tasks dla Ciebie (Claude Code) — w tej kolejności

### Task 1: Smoke test
Uruchom `pip install -r requirements.txt` w venv. Jeśli błąd na `google-genai` — napraw nazwę pakietu i import w `monitor.py`. Potem `python monitor.py` — sprawdź czy pierwszy run przechodzi bez crashy. Pokaż mi output i co się stworzyło w folderach `snapshots/`, `assets/`, `output/`.

### Task 2: Sztuczna zmiana — sprawdzenie czy detekcja działa
Po pierwszym pomyślnym runie:
1. Otwórz `snapshots/microsoft-edge_ios.json`, zmień pole `description` (np. usuń 1 zdanie), zapisz.
2. Zmień pole `version` na coś innego (np. dopisz "-test").
3. Wybierz pierwszy plik PNG z `assets/microsoft-edge/ios/`, podmień go na **inny obrazek** (możesz wziąć drugi screen z tej samej apki, byle był inny — albo wygenerować przez Pillow odwrócony kolorem).
4. Uruchom znów `python monitor.py`.
5. Pokaż mi output (powinno wykryć zmiany), zawartość `output/dashboard.html` (otwórz w przeglądarce żeby zobaczyć), i czy Gemini Vision zwróciło opis (wymaga `GEMINI_API_KEY` w `.env`).

### Task 3: Dodaj Telegram support
Implementuj `send_telegram_alert` jak opisane w "Known issues #2". Po dodaniu poinstruuj mnie jak założyć bota (BotFather) i podaj komendę do znalezienia chat_id. Dodaj test funkcji w main flow.

### Task 4: Napraw ścieżki obrazków w dashboardzie pod GitHub Pages
Wybierz jedną z 3 strategii z "Known issues #5" i zaimplementuj. Polecam opcję: **kopiować potrzebne pliki z assets/ do output/ przed render dashboardu** (najczystsze separation of concerns).

### Task 5: Init git repo + push do GitHuba (jeśli jeszcze nie zrobione)
```bash
git init
git add .
git commit -m "Initial commit: Edge Listing Monitor MVP"
gh repo create edge-listing-monitor --private --source=. --push
```
Pokaż mi URL repo. Potem instrukcja co ja mam dodać w UI GitHuba: 3 secrets, włączenie Pages, opcjonalnie pierwszy run workflowa.

---

## Environment setup (co Ty potrzebujesz w sesji)

**Folder projektu:** `~/Projects/edge-listing-monitor` (lub gdzie skopiowałem).

**Klucze API które wpisuję do `.env`:**
- `GEMINI_API_KEY` — z https://aistudio.google.com/app/apikey (darmowy, 30 sek)
- `GOOGLE_CHAT_WEBHOOK_URL` — z Space w Google Chat (opcjonalne, wymaga Workspace)
- `RESEND_API_KEY` — z https://resend.com (opcjonalne, free 3000/mies)
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` — z @BotFather + /getUpdates (opcjonalne, po Task 3)

**Python:** 3.11 (sprawdź `python3 --version`).

**Venv:** zawsze pracuj w `venv/` w katalogu projektu.

---

## Project conventions (żebyś nie wymyślał)

- **Komentarze i logi:** po polsku (klient nietechniczny, prowadzi go po polsku)
- **Funkcje:** docstring na początku, jasna nazwa, jeden poziom abstrakcji
- **Error handling:** `try/except` z `print("[ERR] ...")` i `print("[WARN] ...")` — żeby było widać w terminalu
- **Brak nadinżynierii:** kod ma być czytelny dla osoby która Pythona zna podstawowo, nie idiomatyczny zaawansowany
- **YAML config > Python config:** wszystko co użytkownik może chcieć zmienić bez ruszania kodu — do `config.yaml`
- **Snapshoty JSON:** `indent=2, ensure_ascii=False` — żeby były czytelne i obsługiwały polskie znaki

---

## Co masz w głowie ale nie w kodzie

**Architektura runtime:**
```
GitHub Actions cron (co 6h)
  → checkout repo
  → setup Python + cache pip
  → pip install -r requirements.txt
  → python monitor.py
     ├── load config.yaml
     ├── for each app, for each platform:
     │    ├── fetch metadata (iTunes API lub gp-scraper)
     │    ├── load previous snapshot z snapshots/
     │    ├── detect text changes (deepdiff-style)
     │    ├── detect visual changes (URL → SHA256 → pHash filter)
     │    ├── enrich with Gemini Vision descriptions
     │    ├── save new snapshot + new assets
     │    └── send alerts (Google Chat / email / Telegram)
     └── generate output/dashboard.html
  → git commit snapshots/, assets/, output/
  → git push
  → deploy output/ to gh-pages branch
```

**User journey klienta po deployu:**
- Co 6h dostaje (jeśli zmiany) — alert na Google Chat / email / Telegram
- W każdej chwili może otworzyć dashboard URL na GitHub Pages — widzi listę zmian
- Może edytować `config.yaml` w GitHubie (UI editor) → następny run obejmie nową apkę
- Może odpalić workflow ręcznie z UI Actions → Run workflow

---

## Co NIE rób

- Nie dodawaj bazy danych (SQLite/Postgres) — JSON+git wystarczy dla MVP i jest pedagogiczne
- Nie refaktoruj `monitor.py` na wiele modułów — celowo jest w 1 pliku żeby klient nietechniczny widział całość
- Nie dodawaj typingu zaawansowanego (Generics, Protocols) — `dict`/`list` wystarczą
- Nie używaj async — proste sekwencyjne wystarcza, klient czytelnie zrozumie
- Nie ulepszaj HTML dashboard pod kątem mobile responsive (Tailwind tu zrobi swoje)
- Nie commituj `.env` — jest w `.gitignore`, ale uważaj jeśli będziesz tworzył nowe pliki z sekretami
- Nie scrapuj In-App Events / Promotional Content — to v2

---

## Po wykonaniu wszystkich tasków powiedz mi:

1. Czy `python monitor.py` przechodzi bez crashy
2. Co jest w `output/dashboard.html` (screenshot lub opis)
3. Czy alerty działają (przetestowane na sztucznej zmianie)
4. URL do GitHub repo (jeśli pushed)
5. Co jeszcze warto poprawić zanim pokażę klientowi jutro

---

## Linki które mogą Ci się przydać

- iTunes Lookup API: https://itunes.apple.com/lookup?bundleId=com.microsoft.msedgemobi&country=us
- google-play-scraper docs: https://github.com/JoMingyu/google-play-scraper
- Gemini API quickstart: https://ai.google.dev/gemini-api/docs/quickstart
- Google Chat webhooks: https://developers.google.com/workspace/chat/quickstart/webhooks
- Telegram Bot API: https://core.telegram.org/bots/api#sendmessage
- Resend API: https://resend.com/docs/api-reference/emails/send-email
- GitHub Actions cron syntax: https://crontab.guru/

Powodzenia. Działaj — jak coś nie jest jasne, zapytaj zanim ruszysz w bok.
