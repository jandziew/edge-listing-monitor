# Edge Listing Monitor

Skrypt który monitoruje strony aplikacji w App Store i Google Play, wykrywa zmiany (tekst i grafika), opisuje je przez AI i alertuje.

**Domyślnie monitoruje:** Microsoft Edge (iOS + Android).
**Łatwo dodać kolejne apki:** edytuj `config.yaml`.

---

## Szybki start (lokalnie, 5 minut)

### 1. Zainstaluj Pythona 3.11+
- macOS: `brew install python@3.11`
- Windows: pobierz z [python.org](https://python.org)

### 2. Sklonuj/skopiuj ten folder, wejdź do niego
```bash
cd edge-listing-monitor
```

### 3. (Opcjonalnie ale rekomendowane) Stwórz wirtualne środowisko
```bash
python -m venv venv
source venv/bin/activate     # macOS/Linux
# venv\Scripts\activate      # Windows
```

### 4. Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### 5. Skonfiguruj klucze API (opcjonalne na start)
```bash
cp .env.example .env
# Otwórz .env w edytorze i wklej GEMINI_API_KEY (darmowy: https://aistudio.google.com/app/apikey)
```

Jeśli pominiesz ten krok, skrypt zadziała ale bez AI opisu zmian — tylko tekst i obrazki.

### 6. Uruchom
```bash
python monitor.py
```

**Pierwszy run** ściągnie wszystkie aktualne metadane i obrazki jako "baseline" — żadnych alertów.
**Drugie i kolejne runy** będą porównywać z baseline i raportować zmiany.

### 7. Zobacz dashboard
```bash
open output/dashboard.html      # macOS
start output/dashboard.html     # Windows
```

---

## Struktura folderów

```
edge-listing-monitor/
├── config.yaml              # lista monitorowanych apek + ustawienia
├── monitor.py               # główny skrypt
├── requirements.txt         # biblioteki Pythona
├── .env                     # klucze API (NIE commituj!)
├── .env.example             # szablon
├── templates/
│   └── dashboard.html       # template HTML dashboard
├── snapshots/               # zapisane snapshoty JSON (auto)
├── assets/                  # pobrane obrazki (auto)
├── output/
│   └── dashboard.html       # wygenerowany dashboard (auto)
└── .github/workflows/
    └── monitor.yml          # konfiguracja GitHub Actions (cron)
```

---

## Dodawanie nowych aplikacji

Otwórz `config.yaml` i dopisz blok:

```yaml
apps:
  - name: "Microsoft Edge"
    slug: "microsoft-edge"
    ios:
      bundle_id: "com.microsoft.msedge"
      country: "us"
    android:
      package_name: "com.microsoft.emmx"
      country: "us"

  # NOWA APKA:
  - name: "Google Chrome"
    slug: "google-chrome"
    ios:
      bundle_id: "com.google.chrome.ios"
      country: "us"
    android:
      package_name: "com.android.chrome"
      country: "us"
```

**Jak znaleźć bundle_id (iOS):**
1. Otwórz stronę apki na https://apps.apple.com w przeglądarce
2. Skopiuj numer ID z URL (np. `id1288723196`)
3. Wejdź na `https://itunes.apple.com/lookup?id=1288723196` i znajdź pole `bundleId`

**Jak znaleźć package_name (Android):**
- URL strony apki na Google Play kończy się np. `?id=com.android.chrome` — to jest package_name.

---

## Uruchomienie w chmurze (GitHub Actions, darmowe)

### 1. Wrzuć projekt na GitHub
```bash
git init
git add .
git commit -m "Initial commit"
gh repo create edge-listing-monitor --private --source=. --push
```

### 2. Dodaj sekrety w GitHub
W repo: **Settings → Secrets and variables → Actions → New repository secret**

Dodaj:
- `GEMINI_API_KEY` — klucz Gemini
- `GOOGLE_CHAT_WEBHOOK_URL` — (opcjonalnie) URL webhooka Google Chat Space
- `RESEND_API_KEY` — (opcjonalnie) klucz Resend do emaila
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` — (opcjonalnie) alerty na Telegram

### 3. Włącz workflow
Workflow `.github/workflows/monitor.yml` uruchomi się automatycznie co 6h.

Możesz też uruchomić ręcznie: **Actions → Monitor App Listings → Run workflow**.

### 4. Włącz GitHub Pages (żeby dashboard był publicznie dostępny)
W repo: **Settings → Pages → Source: gh-pages branch**.

Po pierwszym runie dashboard będzie pod: `https://twoj-username.github.io/edge-listing-monitor/dashboard.html`.

---

## Alerty

### Google Chat
1. W Google Chat: otwórz Space → strzałka obok nazwy → **Apps & integrations → Add webhooks**.
2. Skopiuj URL webhooka.
3. Wklej do `.env` jako `GOOGLE_CHAT_WEBHOOK_URL`.
4. W `config.yaml` zmień `alerts.google_chat.enabled` na `true`.

### Email (przez Resend)
1. Załóż konto na [resend.com](https://resend.com) (3000 maili/mies za darmo).
2. Wygeneruj API key.
3. Wklej do `.env` jako `RESEND_API_KEY`.
4. W `config.yaml`:
   ```yaml
   alerts:
     email:
       enabled: true
       recipients:
         - "twoj-email@example.com"
   ```

### Telegram (najprostszy fallback, nie wymaga Workspace)
1. W Telegramie wyszukaj **@BotFather**, kliknij Start, wyślij `/newbot`. Podaj nazwę bota (np. "Edge Listing Bot") i unikalny username kończący się na `bot` (np. `edge_listing_bot`). BotFather odpowie tokenem postaci `123456:ABC-DEF...`.
2. Skopiuj token do `.env` jako `TELEGRAM_BOT_TOKEN`.
3. Otwórz w Telegramie czat ze swoim nowym botem i wyślij mu **dowolną wiadomość** (np. "cześć"). To inicjalizuje kanał.
4. W przeglądarce wejdź na: `https://api.telegram.org/bot<TWOJ_TOKEN>/getUpdates`
   Znajdź w odpowiedzi `"chat":{"id":...}` — ta liczba to **TELEGRAM_CHAT_ID** (dla rozmów 1-na-1 dodatnia, dla grup ujemna). Wklej do `.env`.
5. W `config.yaml` zmień `alerts.telegram.enabled` na `true`.

Alert na Telegramie zawiera streszczenie zmian + dla każdej zmiany wizualnej osobny obrazek side-by-side.

---

## Częste problemy

**"ModuleNotFoundError: No module named 'X'"**
→ Nie zainstalowałeś wymagań. Uruchom: `pip install -r requirements.txt`

**"Nie znaleziono apki o bundle_id=..."**
→ Sprawdź bundle_id w `config.yaml`. Apka może nie być dostępna w wybranym kraju (`country`).

**"Gemini Vision nie zadziałał"**
→ Sprawdź czy `GEMINI_API_KEY` jest poprawny. Bez niego skrypt działa, ale bez opisów AI.

**Google Play scraper rzuca błąd**
→ Google Play czasami zmienia layout — biblioteka się psuje. Spróbuj `pip install --upgrade google-play-scraper`.

**Pierwszy run nie pokazuje nic na dashboardzie**
→ To normalne — pierwszy run to baseline. Uruchom drugi raz po np. dniu, żeby zobaczyć diff.
