# Prompts — copy and paste

> Library of ready-to-use prompts for Gemini and Antigravity. Keep this open on a second monitor while building — pick the relevant one and paste, don't reinvent from scratch.
>
> **Convention:** `[TEXT IN SQUARE BRACKETS]` are spots for you to fill in with your own content.

---

## G. GOOGLE STITCH — wireframe before you code

> Stitch ([stitch.withgoogle.com](https://stitch.withgoogle.com)) generates a wireframe of the whole page from a text description. Free tier: 350 generations/mo. Output: clickable mockup, exportable screenshot. You'll paste the wireframe into Gemini (when generating the PRD) and into Antigravity (when building) — the agent gets a visual anchor.

### G1. First Stitch prompt — from idea to wireframe

```
[DESCRIBE THE APP IN ONE SENTENCE, e.g. "Web dashboard for monitoring changes
in app listings on App Store and Google Play"]

Page layout (top to bottom):
1. Sticky header: logo + app name on the left, last-update timestamp and
   dark/light toggle on the right
2. Left sidebar (sticky, ~250px wide): list of monitored apps, each with an
   active-alert count (colored dot)
3. Main content (rest of the width), three sections stacked:
   a) "Alerts" — colored cards with recent changes, each with detection date,
      release date (if different), type badge (NEW RELEASE / VISUAL / TEXT / IAE)
   b) "Alert history" — table: columns [Detected | Released | Source |
      What changed], sortable
   c) "Current State per app" — card with app icon, version, rating,
      horizontal screenshot gallery, collapsible "release notes" section
4. Footer: small links "Repo on GitHub" and "What is this tool"

Style: clean, Material Design 3, light background, blue accents (#1a73e8),
Inter font, generous whitespace. Inspiration: Linear, Notion, Stripe dashboards.

Generate the full-page wireframe (desktop, ~1440px wide).
```

### G2. Iterate — change part of the wireframe

```
In the current wireframe change:
- [CONCRETE CHANGE, e.g. "accent color to green (#10b981) instead of blue"]
- [SECOND CHANGE, e.g. "add filters above the History table: dropdown 'All /
   Only new releases / Only visual changes' + date range picker"]
- [THIRD CHANGE, e.g. "Alert cards should be narrower — 3 per row instead of 1"]

Leave the rest unchanged.
```

### G3. Mobile version — generate mobile variant

```
Generate the mobile version (390px wide) of the same dashboard. Rules:
- Sidebar becomes a sticky bottom navigation with 4 icons (Alerts, History,
  Apps, Settings)
- Alert cards stretch full width, stacked vertically
- History table → cards (each row as a separate card) since the table won't fit
- Screenshot gallery → carousel with dot indicators

Keep colors, font, style identical to desktop.
```

### G4. Export wireframe for further work

```
OK, this wireframe works for me. Generate:
1. List of all UI components on the page (each with a name and a 1-sentence
   description) — I'll pass this to Antigravity as context
2. List of all colors used (HEX) + fonts
3. Brief description of interactions (what happens when I click X, hover Y) —
   if the wireframe doesn't show, propose sensible defaults

Everything in plain English, in Markdown so I can attach it to the PRD.
```

---

## A. GEMINI — session from idea to PRD

### A1. Start the Gemini session (always first)

```
Help me design a small business tool I want to build using an agentic IDE
(Antigravity). I'm a non-technical [YOUR ROLE, e.g. marketing person].

Idea in one sentence: I'd like to know daily whether [YOUR IDEA, e.g.
"Microsoft has changed anything in the Edge app description on the App Store"].

Your job: ask me 5-10 questions to nail down the scope of this MVP, so I can
paste the result as a prompt into Antigravity. Ask one question at a time,
wait for my answer, then the next. Don't write any code yet — first I want
a clear scope description.
```

---

### A2. When Gemini starts inflating the scope

```
Stop — you're suggesting too much. Let's focus only on a minimal MVP that
realistically works within a single 2-3h build session. We're cutting:
[list of features you want to remove]

Back to questions, but only about things that are in this minimal scope.
```

---

### A3. When you want a tech recommendation

```
Do you recommend Python or Node.js for this project? Remember I'm non-technical,
so the criterion is "code readability" and "ease of manual fixes," not
"performance." Pick one and briefly justify.
```

---

### A4. Finalize — generate the PRD (after 10-15 min conversation)

```
OK, we have enough info. Now write a PRD (Product Requirements Document)
in Markdown, with this structure:

1. Goal (1 paragraph)
2. User and use case (1 paragraph)
3. MVP functionality (list of 3-7 items, each max 1 sentence)
4. Out of scope for MVP (list, so the agent doesn't try to build it)
5. Data sources and their format (list of specific URLs/APIs)
6. Alerting (channels, message format)
7. Tech stack (recommend Python, simplest libraries)
8. Where to host (Cloudflare Pages + Access as default)
9. Security (which API keys needed, where to store them — .env, .gitignore)
10. Plan for the first 2 hours of work in Antigravity (concrete list of tasks
    for the agent, in order, starting with simplest)

Write in clear English, no engineering jargon. I'll paste the result as the
first prompt into Antigravity, so it has to be self-contained and precise.
```

---

### A5. Sanity check the PRD (after generation)

```
Critical review of this PRD. Tell me:
- Is anything unrealistic for a non-technical person in 2h?
- Is the MVP scope truly minimal? What else would you cut?
- Are there hidden assumptions about my environment (what accounts, access)?
- What are the biggest risks that this won't work first try?

Don't rewrite the PRD — just critique.
```

---

## B. ANTIGRAVITY — session from PRD to working MVP

### B1. First prompt — drop in the PRD

```
Hi. I'm a non-technical user ([YOUR ROLE]). I want to build a small tool with
your help, following the PRD and wireframe below.

Your role:
1. First, read the PRD, look at the wireframe, and tell me in plain English
   what you're going to do, in steps (5-10 numbered items). DO NOT write code yet.
2. When I accept the plan, you start on step 1.
3. After each finished step, stop, show me what you did, wait for my approval
   before moving on.
4. Write comments in the code in English — I want to be able to read it
   someday on my own.
5. If you're not sure about something — ask instead of guessing.
6. Stick to what's in the PRD and wireframe. If you want to add something
   that's not there — first ask "I'm adding X, OK?".

Attachment: wireframe.png (from Stitch)

Here's the PRD:

---

[PASTE THE FULL PRD GENERATED BY GEMINI]
```

---

### B2. Stop the agent when it starts coding immediately

```
Stop. I want a plan first, code second. Go back and show me a list of 5-10
steps in order, with a time estimate for each. After my approval you'll start
step 1.
```

---

### B3. Accept the plan (usually the first "click")

```
Plan looks good. Start step 1. When done, show me:
- which files you created / modified
- what the new code does in 2-3 plain-English sentences
- how I can test it locally
```

---

### B4. After the first step — verification

```
Tell me in your own words what's in the project right now. List each file and
describe its role in one sentence. Plain English.
```

---

### B5. Adding a new feature (small, focused change)

```
I want to add this feature: [CONCRETE DESCRIPTION OF THE FEATURE, e.g.
"a Telegram alert when we detect a version change"].

Requirements:
- Modify only the necessary files, don't refactor the rest
- After implementation show me the diff (only changed lines)
- Explain in plain English what you added, in 3-4 sentences
- If it requires new API keys / secrets — tell me where to get them and
  where to paste them

Don't start coding until I confirm scope.
```

---

### B6. When the script breaks

```
I ran `[command you ran, e.g. python monitor.py]` and got this error:

```
[PASTE THE FULL STACK TRACE FROM THE TERMINAL, FROM BEGINNING TO END]
```

What I was doing before: [briefly describe context, e.g. "after adding feature X"].
Expected: [what was supposed to happen].
Actually saw: [what you see].

Diagnose what went wrong. First explain the problem in plain English
(2-3 sentences), then fix it.
```

---

### B7. When you don't understand code the agent wrote

```
Explain in plain English, like you're explaining to a 10-year-old, what this
chunk of code does:

```
[PASTE THE CODE THAT'S WORRYING YOU]
```

After explaining, tell me: is this a standard solution, or did you do something
unusual? If unusual — why?
```

---

### B8. When the agent is over-engineering

```
This solution feels over-engineered for an MVP. Propose something simpler,
even if it has fewer features or handles edge cases less gracefully.

Remember: this should be a working MVP that I, a non-technical user, can read
and modify, not a production-grade app.

List 2-3 simpler approaches with their trade-offs, but don't write code yet.
```

---

### B9. Before the first commit to GitHub

```
Before we commit anything to GitHub, check:
1. Does the project have a `.gitignore` file and does it contain `.env`,
   `*.key`, `secrets/`
2. Are there any hardcoded API keys or passwords in any file in the repo
   (scan all files, especially `monitor.py` and `config.yaml`)
3. Is there a `.env.example` (template) but `.env` itself is NOT in the
   tracked files list

Show me the result of this audit. Only when we confirm safety do we commit.
```

---

### B10. Configure GitHub Actions (cron)

```
Set up GitHub Actions to:
1. Run `[YOUR MAIN SCRIPT, e.g. python monitor.py]` every [FREQUENCY, e.g. 6 hours]
2. After running, commit generated files (`output/`, `snapshots/`) back to the repo
3. Pull API keys from GitHub Secrets (not from .env which is gitignored)
4. Also allow manual run via a button in the GitHub UI (workflow_dispatch)

After generating .github/workflows/monitor.yml, write me step-by-step
instructions (plain English) on how to add a secret in the GitHub UI —
where to click, what to type.
```

---

### B11. Set up deployment to Cloudflare Pages

```
I want to publish the generated dashboard (folder `output/`) to Cloudflare Pages,
with password protection via Cloudflare Access (email OTP). Tell me:

1. Exactly what I need to do in the Cloudflare UI (step by step, plain English,
   as if I'm doing this for the first time in my life)
2. Whether anything needs to change in our project (e.g. add `wrangler.toml`
   or something — or will Cloudflare auto-detect this is a static site)
3. What value to put in "Build output directory" in Cloudflare Pages config
4. How to configure Cloudflare Access so only emails from a list can enter

Don't write code yet — first I want to understand the plan.
```

---

### B12. When the agent forgot something from the PRD

```
Back to the PRD. Section [X] says: "[QUOTE FROM PRD]".

I don't see this in the current project. Re-read the full PRD, list what we've
already done and what's still left. Plain English, as a checklist.
```

---

## C. MAINTENANCE — when the project is already running

### C1. Adding a new app / entity to the monitor

```
Add to `config.yaml` a new app:
- Name: [NAME, e.g. Google Chrome]
- iOS bundle_id: [BUNDLE_ID, e.g. com.google.chrome.ios]
- Google Play package_name: [PACKAGE_NAME, e.g. com.android.chrome]
- Country: [COUNTRY CODE, e.g. us]

After adding, run `python monitor.py` to set the first baseline for this app.
Show me in the output whether it loaded correctly.
```

---

### C2. Changing cron frequency

```
I want to change the cron from [OLD FREQUENCY, e.g. every 6h] to [NEW FREQUENCY,
e.g. every 1h]. Edit `.github/workflows/monitor.yml`. After the change show me
the diff and explain in plain English what specific cron syntax means.
```

---

### C3. Adding a new alert channel

```
I want to add alerts on [CHANNEL, e.g. Slack via Incoming Webhook / Microsoft
Teams / Discord].

Requirements:
- Add a `send_[channel]_alert(...)` function analogous to the existing
  `send_telegram_alert`
- Add `alerts.[channel].enabled` flag in `config.yaml`
- Add secret variable to `.env.example` (e.g. SLACK_WEBHOOK_URL)
- Add the secret to the secrets list in the GitHub Actions workflow
- In README "Alerts" section, add instructions on how to set up this channel

After implementation, list what I have to do outside the code (e.g. where to
set up the webhook on the [CHANNEL] side).
```

---

### C4. Security audit before handing access to a client

```
Run me a security review of this project before I send access to a client:

1. Are there any hardcoded API keys / passwords in the code? (scan all files)
2. Does `.gitignore` ignore everything it should (.env, *.key, secrets/,
   sensitive data)?
3. Does git history contain a commit that accidentally added a secret at some
   point (check git log)?
4. Does the README tell the client what they MUST set up themselves vs. what's
   already configured?
5. Are there any endpoints/URLs I left open (e.g. test webhooks)?

In plain English, give me a "to-do before sending" list if you find anything.
```

---

### C5. When an external service has changed (e.g. Google Play scraper stopped working)

```
Script throws an error on fetch for [WHICH APP / FROM WHICH SOURCE]:

```
[STACK TRACE]
```

Probably [SERVICE, e.g. Google Play] changed the page HTML or API format.
Your job:

1. Check the current state of the page / API (do a live fetch and show me
   example response)
2. Compare with what our code expects
3. Propose a minimal fix
4. Explain in plain English what changed on [SERVICE] side and how it affects us

Don't modify code until I approve the fix.
```

---

## D. DEBUG — "I don't know what's going on"

### D1. Generic "something is weird"

```
Something is off and I don't know what. Diagnose:

What I tried: [STEP BY STEP WHAT YOU DID — e.g. "changed X in config.yaml,
ran the script, dashboard doesn't show the new app"]

Expected: [WHAT WAS SUPPOSED TO HAPPEN]

What I actually see: [WHAT YOU SEE — error message, weird output, empty dashboard]

Terminal output (full, from run start):
```
[PASTE TERMINAL OUTPUT]
```

Contents of files that may be related:
- [FILENAME]: [ITS CONTENTS OR IMPORTANT FRAGMENT]

Ask me clarifying questions if anything's missing, then start fixing.
```

---

### D2. When a commit fails (pre-commit hook fail etc.)

```
I'm trying to `git commit -m "..."` and got this error:

```
[ERROR FROM TERMINAL]
```

Diagnose and fix. If it's a pre-commit hook (e.g. formatter, linter) — fix
the code so it passes, DO NOT suggest `--no-verify` (bypassing hooks).
```

---

### D3. When `git push` fails (conflicts)

```
I tried `git push` and got a conflict / rejection error:

```
[ERROR FROM TERMINAL]
```

Explain in plain English what happened (why git won't push my changes) and
walk me through the resolution step by step. Show commands to type, but I'll
type them myself — don't type them.
```

---

## E. QUICK INTERVENTIONS — when the agent misunderstood

### E1. "Stop, halt"

```
Stop. Halt everything, don't continue. Explain in plain English what you're
doing and why, before I decide whether we proceed.
```

### E2. "Revert the last change"

```
The last change you made doesn't work / I don't like it. Revert it: restore
the state from before your last edit to [FILENAME]. Show me the diff so I can
see that we're really back at the previous state.
```

### E3. "That's not what I asked for"

```
That's not what I meant. You were asked to [REPEAT ORIGINAL REQUEST].
Instead you did [DESCRIBE WHAT WENT WRONG].

Explain why you thought what I asked for was what you did. Possibly my request
was unclear. Let's try again, I'm being more specific:
[PRECISION].
```

### E4. "Slow down"

```
Slow down. Feels like you're doing too much at once. Go back to the smallest
sensible single step. After finishing it, show me what you did, I'll approve,
then we go further.
```

---

## F. METAPROMPTS — when you need agent's help with prompting itself

### F1. "Help me phrase the request"

```
I want to achieve [GOAL DESCRIPTION], but I don't know how to describe it in
a prompt so you understand me well. Help me phrase the prompt — ask me 3-5
clarifying questions and based on them propose a ready-to-use prompt I can
use in our conversation.
```

### F2. "Teach me something along the way"

```
While doing what I'm asking, teach me in plain English what [CONCEPT —
e.g. "what dependencies in Python are", "what cron is", "what an API is"]
means. Short, 3-5 sentences, as if explaining to a non-technical person.
```

---

## H. GOOGLE-ONLY STACK — Apps Script + Sheets + Stitch

> When corporate won't allow Cloudflare/GitHub and everything must stay in Google Workspace. Apps Script covers: scraper, cron, DB (Sheets), secrets (Properties Service), hosting (Web App with DOMAIN restriction).

### H1. Decision: will my project fit in Apps Script?

```
I have an idea for a tool: [DESCRIPTION, 2-3 sentences].

Check if it fits in Apps Script given the constraints:
- max 6 min runtime (30 min on Workspace) per execution
- JavaScript only (Python out)
- no Playwright / headless browser (works only with regular HTML/REST API)
- DB can be Google Sheets (~10k rows max reasonable)
- frontend = HTML generated in Apps Script (one HTML file, static or generated)

Tell me:
1. Whether you CAN do this in Apps Script yes/no + 1-2 sentence justification
2. If no — what's the minimum tech that must be outside Apps Script (e.g.
   "scraper has to be on Cloud Run because it takes >6 min")
3. Hybrid stack you'd propose (e.g. "Cloud Run for scraper + Apps Script for
   dashboard and DB")
```

---

### H2. Set up a new Apps Script project

```
Create me an Apps Script project named [NAME, e.g. "Edge Listing Monitor"].
Walk me through step by step (plain English, as if explaining for the first time):

1. How to get to the Apps Script Editor (script.google.com vs through a specific Sheet)
2. What file structure to create (typically: Code.gs, Scraper.gs, Dashboard.gs,
   index.html, Properties.gs)
3. How to name these files consistently

Don't write content yet — first I want to understand the structure.
```

---

### H3. Scraper in Apps Script (instead of Python)

```
Write me an Apps Script scraper that:
1. Fetches [URL, e.g. "https://itunes.apple.com/lookup?bundleId=com.microsoft.msedge"]
   using UrlFetchApp
2. Parses the response (JSON or HTML — pick the right parser)
3. Extracts fields: [LIST OF FIELDS, e.g. "version, description, screenshotUrls"]
4. Returns a JS object

Important:
- Comments in plain English
- Handle errors when fetch fails (return null + log via Logger)
- If you use an HTML parser — use XmlService (built-in) or regex (simpler for
  simple cases)

Also show me how to run this function manually in the editor ("Run" button).
```

---

### H4. Google Sheets as DB — write/read

```
I want to use Google Sheets as a database in this project. Setup:
- Spreadsheet ID: [YOUR ID — pull from sheet URL]
- Sheet "alerts" — columns [Timestamp, App, Platform, Type, Old Value, New Value, Detected By]
- Sheet "apps" — list of monitored: [Name, Slug, iOS Bundle ID, Android Package, Enabled]

Write functions (comments in plain English):
1. appendAlert(alertObj) — appends a new alert to the end of the "alerts" sheet
2. getAllApps() — reads the "apps" sheet where Enabled=TRUE, returns list of objects
3. loadSnapshot(appSlug, platform) — reads the latest snapshot for an app from a
   dedicated sheet "snapshots_[appSlug]_[platform]" (one sheet per app × platform)
4. saveSnapshot(appSlug, platform, snapshotObj) — saves (overwrites the whole sheet)

Design with the assumption that the client will open this Sheet manually to browse
data — so the data should be readable, columns wide, dates in YYYY-MM-DD HH:MM format.
```

---

### H5. Secrets (Properties Service)

```
I don't want to keep the API key in code. Show me:
1. How to set a project property (Script Property) named GEMINI_API_KEY with
   value "AIzaSy..." — step by step in the Apps Script UI (where to click,
   what to type)
2. How to read this property in code
   (`PropertiesService.getScriptProperties().getProperty(...)`)
3. How to do this securely — are these properties encrypted, who has access,
   do they commit to the project if I share it with someone else

Explain in plain English, as if I'm using this tool for the first time.
```

---

### H6. Time-driven trigger (cron every X hours)

```
I want the function `runMonitor()` to run every [FREQUENCY, e.g. 6 hours]
automatically. Show me:

1. How to set up a time-driven trigger in the Apps Script UI (where to click:
   Triggers → Add trigger, what options for "hour timer" vs "day timer")
2. Whether it's better to do this programmatically (via `ScriptApp.newTrigger(...)`)
   or in the UI — compare pros/cons
3. How to check logs from previous runs (Executions tab)
4. What to do when a trigger exceeds the 6 min limit — will I get an email alert
```

---

### H7. Dashboard as HTML Service Web App with DOMAIN restriction

```
I want to publish the dashboard as an Apps Script Web App accessible only to my
company (@company.com domain). Requirements:

1. File index.html — generate static HTML (Tailwind via CDN) rendering data
   from the "alerts" sheet (read via Sheets API in `doGet()`)
2. `doGet()` function in Code.gs — reads data, renders HTML with
   `HtmlService.createTemplateFromFile('index')`
3. Deploy: walk me through step by step on doing Deploy → New Deployment → Web App:
   - Description: "Production v1"
   - Execute as: "Me"
   - Who has access: "Anyone in [company.com]"
4. I'll get a URL like `https://script.google.com/macros/s/.../exec` — can this
   URL be changed to something prettier?
5. How do clients log in (automatic Google SSO, or do they have to approve
   something on first entry)

Explain everything in plain English, step by step.
```

---

### H8. Hybrid: Cloud Run scraper + Apps Script frontend

```
My scraper is too heavy for Apps Script (Python, long runtime). Hybrid stack:
- Backend (scraper + cron): Cloud Run with Python
- DB: Google Sheets (client sees data themselves)
- Frontend: Apps Script Web App with DOMAIN restriction

Design the architecture:
1. Cloud Run service deployed via `gcloud run deploy --source .` from a Python folder
2. Cloud Scheduler trigger every 6h → POST to Cloud Run service URL
3. Cloud Run service: scrapes, saves result to Google Sheets (via Sheets API
   with service account)
4. Apps Script Web App: reads from Sheets, renders HTML

Secrets:
- In Cloud Run: environment variables (via `gcloud run deploy --set-env-vars`)
  or Secret Manager
- In Apps Script: Properties Service

Tell me:
1. How to configure a service account for Cloud Run so it has write access to Sheets
2. Whether Cloud Scheduler is free for our case (1 job, 4x daily)
3. How to debug when something breaks (where to check logs — Cloud Run Logs,
   Sheets edit history, Apps Script Executions)

Don't generate code yet — first I want to understand the whole architecture and
where what lives.
```

---

### H9. Migrating an existing Python project to Apps Script

```
I have a Python project I'd like to rewrite to Apps Script (where it makes sense).
Repo: [link to GitHub repo or paste the most important files].

Your job:
1. Analyze the project — list all external Python libraries I'm using
2. For each: does it have a native Apps Script equivalent (e.g. `requests`
   → `UrlFetchApp`), can it be worked around (e.g. `PIL` → send to Vision API),
   or it CAN'T sensibly be done (e.g. `playwright` → leave the scraper on Cloud Run)
3. Propose the minimum version of the project for Apps Script (what drops out,
   what stays)
4. Estimate migration effort (hours of work with the agent)

Don't start migrating — first I want to understand the scale and whether it's
even worth it.
```

---

*Keep this file open on a second monitor while working. As your session
progresses you'll start remembering most prompts by heart. After 10-15 hours
of work with Antigravity this cheat sheet becomes redundant — but at the start
it saves enormous time.*
