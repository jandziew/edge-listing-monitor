# Edge Listing Monitor

Script that monitors app pages on the App Store and Google Play, detects changes (text and visuals), describes them with AI, and sends alerts.

**Default target:** Microsoft Edge (iOS + Android).
**Easy to add more apps:** edit `config.yaml`.

> 📘 **New here?** Read [`CLIENT_GUIDE.md`](./CLIENT_GUIDE.md) — a step-by-step guide on how to build something like this yourself in Antigravity (for non-technical users). [`PROMPTS_COPY_PASTE.md`](./PROMPTS_COPY_PASTE.md) holds the prompt library.

---

## Quick start (locally, 5 minutes)

### 1. Install Python 3.11+
- macOS: `brew install python@3.11`
- Windows: download from [python.org](https://python.org)

### 2. Clone/copy this folder, enter it
```bash
cd edge-listing-monitor
```

### 3. (Optional but recommended) Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate     # macOS/Linux
# venv\Scripts\activate      # Windows
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure API keys (optional to start)
```bash
cp .env.example .env
# Open .env in an editor and paste GEMINI_API_KEY (free: https://aistudio.google.com/app/apikey)
```

If you skip this step, the script will work but without AI descriptions of changes — just text and images.

### 6. Run
```bash
python monitor.py
```

**First run** downloads all current metadata and images as a "baseline" — no alerts.
**Second and subsequent runs** compare with the baseline and report changes.

### 7. View the dashboard
```bash
open output/dashboard.html      # macOS
start output/dashboard.html     # Windows
```

---

## Folder structure

```
edge-listing-monitor/
├── config.yaml              # list of monitored apps + settings
├── monitor.py               # main script
├── requirements.txt         # Python libraries
├── .env                     # API keys (DO NOT commit!)
├── .env.example             # template
├── templates/
│   └── dashboard.html       # HTML dashboard template (Tailwind + Alpine.js)
├── snapshots/               # saved JSON snapshots (auto)
├── assets/                  # downloaded images (auto)
├── history/
│   └── alerts.jsonl         # append-only alert log (auto)
├── output/
│   └── dashboard.html       # generated dashboard (auto)
└── .github/workflows/
    └── monitor.yml          # GitHub Actions config (cron)
```

---

## Adding new apps

Open `config.yaml` and append a block:

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

  # NEW APP:
  - name: "Google Chrome"
    slug: "google-chrome"
    ios:
      bundle_id: "com.google.chrome.ios"
      country: "us"
    android:
      package_name: "com.android.chrome"
      country: "us"
```

**How to find bundle_id (iOS):**
1. Open the app page on https://apps.apple.com in a browser
2. Copy the ID number from the URL (e.g. `id1288723196`)
3. Visit `https://itunes.apple.com/lookup?id=1288723196` and find the `bundleId` field

**How to find package_name (Android):**
- The Google Play app page URL ends with e.g. `?id=com.android.chrome` — that's the package_name.

---

## Running in the cloud (GitHub Actions, free)

### 1. Push the project to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
gh repo create edge-listing-monitor --public --source=. --push
```

### 2. Add secrets in GitHub
In the repo: **Settings → Secrets and variables → Actions → New repository secret**

Add:
- `GEMINI_API_KEY` — Gemini key
- `GOOGLE_CHAT_WEBHOOK_URL` — (optional) Google Chat Space webhook URL
- `RESEND_API_KEY` — (optional) Resend key for email
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` — (optional) Telegram alerts

### 3. Enable the workflow
The workflow `.github/workflows/monitor.yml` runs automatically every 6h.

You can also trigger it manually: **Actions → Monitor App Listings → Run workflow**.

### 4. Enable GitHub Pages (so the dashboard is publicly available)
In the repo: **Settings → Pages → Source: `gh-pages` branch**.

After the first run, the dashboard will live at: `https://your-username.github.io/edge-listing-monitor/`.

**Note:** GitHub Pages on a private repo requires a paid GitHub plan ($4/mo). For corporate clients who can't go public, see [`CLIENT_GUIDE.md`](./CLIENT_GUIDE.md) section 9 for **Cloudflare Pages + Access** (free, with email-OTP gating) or section 10 for the **Google-only stack** (Apps Script Web App with @company.com restriction).

---

## Alerts

### Google Chat
1. In Google Chat: open a Space → arrow next to the name → **Apps & integrations → Add webhooks**.
2. Copy the webhook URL.
3. Paste into `.env` as `GOOGLE_CHAT_WEBHOOK_URL`.
4. In `config.yaml` change `alerts.google_chat.enabled` to `true`.

**Requires Google Workspace** — free Gmail accounts don't have Spaces with webhooks.

### Email (via Resend)
1. Sign up at [resend.com](https://resend.com) (3000 emails/mo free).
2. Generate an API key.
3. Paste into `.env` as `RESEND_API_KEY`.
4. In `config.yaml`:
   ```yaml
   alerts:
     email:
       enabled: true
       recipients:
         - "your-email@example.com"
   ```

### Telegram (simplest fallback, no Workspace needed)
1. In Telegram search for **@BotFather**, hit Start, send `/newbot`. Give the bot a name (e.g. "Edge Listing Bot") and a unique username ending in `bot` (e.g. `edge_listing_bot`). BotFather replies with a token like `123456:ABC-DEF...`.
2. Copy the token into `.env` as `TELEGRAM_BOT_TOKEN`.
3. Open the chat with your new bot in Telegram and send it **any message** (e.g. "hi"). This initializes the channel.
4. In a browser go to: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   Find `"chat":{"id":...}` in the response — that number is the **TELEGRAM_CHAT_ID** (positive for 1-on-1 chats, negative for groups). Paste into `.env`.
5. In `config.yaml` change `alerts.telegram.enabled` to `true`.

Telegram alerts include a summary of changes + a separate side-by-side image for each visual change.

---

## Common problems

**"ModuleNotFoundError: No module named 'X'"**
→ You didn't install requirements. Run: `pip install -r requirements.txt`

**"Nie znaleziono apki o bundle_id=..." (App not found)**
→ Check `bundle_id` in `config.yaml`. The app may not be available in the chosen `country`.

**"Gemini Vision failed"**
→ Check that `GEMINI_API_KEY` is correct. Without it the script works but without AI descriptions.

**Google Play scraper throws an error**
→ Google Play sometimes changes layout — the library breaks. Try `pip install --upgrade google-play-scraper`.

**First run shows nothing on the dashboard**
→ That's normal — first run is a baseline. Run again after e.g. a day to see a diff.

---

## Documentation

| File | What's in it |
|------|--------------|
| [`CLIENT_GUIDE.md`](./CLIENT_GUIDE.md) | How a non-technical user can build this in Antigravity, step by step. Flow: Stitch → Gemini → Antigravity → Cloudflare/Google-only deploy. Security, databases, video tutorial outline. |
| [`PROMPTS_COPY_PASTE.md`](./PROMPTS_COPY_PASTE.md) | Library of ready-to-use prompts for Stitch, Gemini, Antigravity, Apps Script. Organized into sections (G: Stitch, A: Gemini, B: Antigravity build, C: maintenance, D: debug, E: interventions, F: metaprompts, H: Google-only stack). |
| [`PRD_Edge_Listing_Monitor.md`](./PRD_Edge_Listing_Monitor.md) | Original Product Requirements Document used to build this project. Reference example of what a good PRD looks like. (Polish — translation pending.) |
| `PODRECZNIK_JD.md` | Internal handbook for the workshop facilitator (Polish, not for client use). |
