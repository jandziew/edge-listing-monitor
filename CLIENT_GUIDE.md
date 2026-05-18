# Build your own micro-tools in Antigravity — a guide for the non-technical

> A practical, step-by-step guide for someone with zero programming background to build a real, working business tool using Antigravity + Gemini. Worked example: **monitor for app listings of Microsoft Edge on the App Store and Google Play** — but the workflow applies to any micro-project (daily dashboard, scraper, small bot, automation).

---

## 0. What you'll learn

After working through this guide, you'll know:

1. **How to think** about agentic tools (Gemini, Antigravity, Claude Code) so they help you instead of frustrating you
2. **How to design your UI** using Google Stitch before writing any code (step 0 — saves 1-2 hours of iteration)
3. **How to talk to Gemini** to turn a vague idea into a usable spec (PRD)
4. **How to drive Antigravity** step-by-step through building the app — when to trust, when to stop
5. **How to handle secrets safely** — API keys, what never to commit, how not to blow your API budget
6. **Where to host the finished tool** — Cloudflare Pages, Apps Script Web App (Google-only), Cloud Run (hybrid)
7. **Which database to pick** — when JSON files are enough, when to use Sheets, when Firestore
8. **What's next** — iterating, when to call a human developer

---

## 1. Mindset — before you fire anything up

### Three rules that will save you 80% of the frustration

**Rule 1: The agent doesn't read minds.**
If you say "make it better," the agent will do something random that _it_ thinks is better. If you say "make the colors darker and the font bigger," you'll get exactly that.

> Golden rule: describe _what_ should happen and _how you'll know it worked_. Don't describe _how_ to do it technically — that's the agent's job.

**Rule 2: Small step → check → next step.**
Don't dump 10 changes into one prompt. Make 1 change, check that it works (open the result, click, look at the output), then move on. Because if you make 10 changes at once and something breaks, you have no idea which change broke it.

**Rule 3: The agent doesn't know what it doesn't know.**
If you ask "is this app popular?", the agent will answer by guessing. If you ask "search the web for how many downloads this app has," the agent will use a search tool. The difference is fundamental. **Always be explicit about where information should come from.**

### When to trust the agent vs. not

| Trust | Don't trust without verifying |
|-------|-------------------------------|
| Code syntax (Python, HTML, JS) | Whether working code does _what you wanted_ |
| Variable naming, code structure | Claims that "it's fixed now" — run it and see |
| Generating fake example data for tests | Real data values (links, prices, company names) — it can hallucinate |
| Explaining what a piece of code does | Assumptions about your environment (accounts, Workspace setup) |

### Two most common mistakes from non-technical users

1. **"Build me an app that does X"** → you get a giant blob all at once, half doesn't work, and you don't know where to start debugging.
   - **Instead:** break it into 5-10 smaller tasks and run them one at a time.

2. **Accepting everything the agent proposes without looking.**
   - **Instead:** after each step, open the generated file, read the comments, ask the agent "explain what's happening here in plain English, like you're explaining to a child."

---

## 2. The flow we'll follow

```
┌──────────────────────────────────────────────────────────────────┐
│  Step 0: Inspiration       Step 0.5: Stitch (UI)                 │
│  ─────────────────────     ─────────────────────                 │
│  • find references         • describe layout                     │
│  • screenshot what          • generate wireframe                 │
│    you like                 • screenshot → into PRD              │
│                                                                  │
│  Step 1: Gemini (chat)     Step 2: Antigravity                   │
│  ─────────────────────     ─────────────────────                 │
│  • describe features       • paste PRD + wireframe               │
│  • Gemini asks questions   • agent builds structure              │
│  • final spec (PRD.md)     • iterate, verify                     │
│                                                                  │
│  Step 3: Test locally      Step 4: Deploy                        │
│  ─────────────────────     ──────────────                        │
│  • run, check              • Cloudflare Pages + Access (default) │
│  • change, rerun           • OR Apps Script Web App (Google-only)│
│  • when working → push     • cron: GitHub Actions OR Apps Script │
└──────────────────────────────────────────────────────────────────┘
```

Each step has its own section below. Steps 0 and 0.5 (inspiration + wireframe) are optional but **strongly recommended** — they save 1-2 hours of iteration because the agent gets a visual anchor instead of word-only descriptions.

### What you need to start

Before step 1, sign up for these (all free):

- **Google account** (for Gemini, AI Studio, Stitch) — you probably already have one
- **Stitch** — go to [stitch.withgoogle.com](https://stitch.withgoogle.com), sign in with Google (350 wireframe generations / month free)
- **GitHub account** ([github.com/signup](https://github.com/signup)) — to store your code
- **Antigravity** — download from [antigravity.google.com](https://antigravity.google.com) or wherever your instructor points you
- **Cloudflare account** ([cloudflare.com/sign-up](https://cloudflare.com/sign-up)) — for deployment (skip if you go full Google-only — see section 7b)

No credit card needed for any of these (for small projects within free tier).

---

## 3. Step 0 — Find inspiration before you describe anything

### Why this comes first

If you start with "build me a dashboard" the agent will give you _a_ dashboard, but not _your_ dashboard. The single biggest predictor of how good your final product looks is **how clearly you can describe what you want it to look like**. And the easiest way to describe is to point.

### Where to find good UI references (15-20 minutes browsing)

| Source | What's there | Best for |
|--------|--------------|----------|
| **[Mobbin](https://mobbin.com)** | Screenshots from real mobile/web apps, categorized by feature | "Show me how Notion handles a sidebar with grouped sections" |
| **[Dribbble](https://dribbble.com)** | Designer portfolio shots, often aspirational | Visual inspiration, color palettes |
| **[Land-book](https://land-book.com)** | Landing page references | Marketing pages, hero sections |
| **[Refero.design](https://refero.design)** | Curated flows (signup, onboarding, settings) | When you're designing a specific flow |
| **Just open apps you use daily** | Linear, Notion, Stripe, Vercel — screenshot what you like | Real-world layouts that work |

### How to use references

1. Open 3-5 references in tabs
2. Take screenshots (Cmd+Shift+4 on Mac, Win+Shift+S on Windows) of specific parts you like
3. Write down in 1-2 sentences _why_ each one works for you ("I like how Linear's sidebar feels compact but readable" / "Notion's nested expandable sections are how I want my history view")
4. Keep these screenshots — you'll attach them to Stitch and Antigravity as visual anchors

> **Tip:** be specific. "I like Linear" is too vague. "I like Linear's left sidebar with grouped project sections and the way active items have a subtle background tint" — _that_ the agent can build.

---

## 4. Step 0.5 — Stitch: from idea to wireframe

### Why wireframe first

Most frustration with agentic tools comes from showing up at Gemini / Antigravity with a verbal description ("a dashboard with alerts and history") and getting something the _agent_ thinks is a dashboard with alerts. You had image X in your head, the agent built image Y, you waste hours on "no, not like that, move this here, change that color, add a section."

**A wireframe = one picture worth 500 words of prompt.**

You'll paste a screenshot of the wireframe into Gemini when generating the PRD and into Antigravity in the first prompt — the agent immediately understands layout, what's missing, where things go.

### How to use Stitch (5-10 minutes)

1. Open [stitch.withgoogle.com](https://stitch.withgoogle.com), sign in with Google
2. **New design** → describe in text. Example:

   > "Web dashboard for monitoring app listings in app stores (App Store, Google Play). Three sections stacked vertically: (1) Alerts — colored cards with recent changes, each showing detection date and release date, (2) Alert history — table with timestamps and alert type, (3) Current State per app — cards with app icon, version, screenshot gallery. Sticky header with name and last-updated timestamp. Right-side navigation sidebar with the list of monitored apps. Style: clean, Material Design, subtle blue accents, light mode."

3. Stitch generates a wireframe in 30 seconds. It looks like a real website, clickable.
4. Iterate: "add a date filter above the Alerts section", "change accent color to green", "add a dark mode toggle in the top-right"
5. When you're happy — **Export** → take a **full-page screenshot** (Cmd+Shift+4 on Mac, Win+Shift+S on Windows) or use the built-in export

### What now

You now have two artifacts:
- **Text description** (your Stitch prompt) — paste into Gemini when generating the PRD as "this is what the UI should look like"
- **Wireframe screenshot** — paste into Antigravity as the first attachment with your initial prompt ("build a dashboard that looks like this; here's the wireframe")

### Alternatives to Stitch (if for some reason you don't want it)

| Tool | Pro | Con |
|------|-----|-----|
| **Figma** (free tier) | Industry standard, huge template library | Learning curve, no AI, you draw it yourself |
| **Excalidraw** | Very simple, hand-drawn vibe (great in PRDs) | No AI, no real UI feel |
| **v0.dev** | Vercel's AI UI generator (generates real React code) | Output is code, not just visual — overkill if you want a quick mockup |
| **Skip step 0.5** | Faster to start coding | Agent flails blindly, more iterations |

For non-technical users: **Stitch** is simplest. Text → wireframe in 30 sec.

---

## 5. Step 1 — Gemini chat: from idea to PRD

### Why this step exists

Antigravity is brilliant, but it has a limit: **it builds well what you describe well, and it guesses poorly what you didn't tell it.**

Most frustration comes from someone typing "build a tool to monitor apps" — the agent invents 50 things, half of which aren't what you wanted, and you waste an hour on corrections.

The fix: **talk to Gemini first about the idea**, until you have a concrete specification (PRD = Product Requirements Document). Only then go to Antigravity with a clear document in hand.

It's like talking to an architect _before_ hiring a construction crew. The crew will build whatever you say — the question is whether you know what you want.

### How to talk to Gemini to extract a PRD

Open [gemini.google.com](https://gemini.google.com), pick the latest model (e.g. 2.5 Pro or Flash). Start with something like:

> **Your first prompt to Gemini:**
> ```
> Help me design a small business tool I want to build using an agentic IDE
> (Antigravity). I'm a non-technical [YOUR ROLE, e.g. marketing person].
>
> Idea in one sentence: I'd like to know daily whether [YOUR IDEA, 1-2 sentences].
>
> Your job: ask me 5-10 questions to nail down the scope of this MVP, so I can
> paste the result as a prompt into Antigravity. Ask one question at a time,
> wait for my answer, then the next. Don't write any code yet — first I want
> a clear scope description.
> ```

Gemini will ask things like:
- What exactly do you want to monitor? (data sources)
- How often? (daily, hourly)
- Where do you want alerts? (email, chat, dashboard)
- What counts as "a change"? (every change? only meaningful ones?)
- Who will use this? (just you? team? external client?)
- What's _out_ of scope? (deliberately excluded so the project doesn't bloat)

**Answer honestly and concretely.** If you don't know something, write "not sure, advise me" — Gemini will give a recommendation.

### When the PRD is ready

After 10-15 minutes of back-and-forth, ask:

> **Second prompt to Gemini (finalize):**
> ```
> OK, we have enough info. Now write a PRD (Product Requirements Document)
> in Markdown, with this structure:
>
> 1. Goal (1 paragraph)
> 2. User and use case (1 paragraph)
> 3. MVP functionality (list of 3-7 items, each max 1 sentence)
> 4. Out of scope for MVP (list, so the agent doesn't try to build it)
> 5. Data sources and their format (list of specific URLs/APIs)
> 6. Alerting (channels, message format)
> 7. Tech stack (recommend: Python, simplest libraries)
> 8. Where to host (simplest options for a non-technical person)
> 9. Security (which API keys needed, where to store them — .env, .gitignore)
> 10. Plan for the first 2 hours of work in Antigravity (concrete list of tasks
>     for the agent, in order, starting with simplest)
>
> Write in clear English, no engineering jargon. I'll paste the result as the
> first prompt into Antigravity, so it has to be self-contained and precise.
> ```

**Save the result** in a file called `PRD.md` on your computer. This is your "contract" with the agent — come back to it whenever the agent starts doing something unexpected and say "the PRD says X, let's stick with that."

### Red flags in Gemini's responses (signs you need to push back)

| What Gemini wrote | What it means | What to do |
|-------------------|---------------|-----------|
| "We could also add an AI insights dashboard, auto marketing suggestions, CRM integration..." | Scope creep | Say "let's focus only on MVP, drop those features" |
| "For this we'll need to set up a Postgres database on AWS RDS" | Over-engineering | Say "I want the simplest solution, for a non-technical user, ideally without a database" |
| "You can do this in Python, Node.js, Go, or Ruby" | No decision | Say "pick Python — it's the most readable for beginners" |
| "Anyone can do this in 5 minutes" | Naive estimate | Say "give me a realistic time estimate from a non-technical perspective" |

---

## 6. Step 2 — Antigravity: from PRD to a working MVP

### Setting up Antigravity (5 minutes)

1. Open Antigravity (desktop or browser, depending on version)
2. Create a **new project** / **new workspace** — name it after your idea (e.g. `edge-listing-monitor`)
3. Pick a folder on disk where the code will live (e.g. `~/Projects/edge-listing-monitor`)
4. **Important:** if Antigravity asks about preferred model, pick the latest Gemini Pro for planning, Flash for simple tasks

### First prompt — drop in the PRD + wireframe

Open the agent panel. Paste the full PRD you got from Gemini, **attach the screenshot of your Stitch wireframe** (drag it into the agent window or use the attach button), and prepend a short framing:

> **First prompt to Antigravity:**
> ```
> Hi. I'm a non-technical user ([YOUR ROLE]). I want to build a small tool with
> your help, following the PRD and wireframe below.
>
> Your role:
> 1. First, read the PRD, look at the wireframe, and tell me in plain English
>    what you're going to do, in steps (5-10 numbered items). DO NOT write code yet.
> 2. When I accept the plan, you start on step 1.
> 3. After each finished step, stop, show me what you did, wait for my approval
>    before moving on.
> 4. Write comments in the code in English — I want to be able to read it
>    someday on my own.
> 5. If you're not sure about something — ask instead of guessing.
> 6. Stick to what's in the PRD and wireframe. If you want to add something
>    that's not there — ask first.
>
> Attachment: wireframe.png (from Stitch)
>
> Here's the PRD:
>
> ---
>
> [PASTE THE FULL PRD HERE]
> ```

The agent should respond with **a plan, not code**. If it starts coding right away — interrupt and repeat: "stop, show me the plan first."

**Bonus:** when you get to generating the HTML dashboard, in one of the later prompts say "the dashboard should look like the attached wireframe — match the layout as closely as you can, you can simplify graphics if needed." The agent will start generating HTML/CSS that targets that layout.

### Iterating step by step — turning points

These are moments where the agent will stop and you have to make a conscious decision. Full list:

| Moment | What's happening | Your decision |
|--------|------------------|---------------|
| **Plan presented** | Agent showed 5-10 steps | Read it, maybe modify ("instead of step 3 let's do X"), then approve |
| **Library choices** | "I'll use `requests` for HTTP and `BeautifulSoup` for scraping" | Usually accept. If you see a weird name — ask "is this a popular library or something niche" |
| **File structure** | "I'll create monitor.py, config.yaml, requirements.txt" | Accept if nothing looks suspicious (e.g. agent wants to create 30 files — say "simplify, max 5-7 files") |
| **First run** | Script runs, does something | **Check yourself what happened** — open generated files, see if they make sense |
| **First error** | Something breaks | Copy the full error text, paste to agent: "script throws this error: [text]. What went wrong?" |
| **Commit to GitHub** | Agent suggests pushing code | **STOP. First check that there are no secrets in the code (API keys).** See section 7 |
| **Deploy** | Agent suggests publishing online | **STOP. First decide _where_ and _for whom_ — see section 8** |

### Good prompts for common situations (copy-paste into Antigravity)

**When you want an explanation:**
```
Explain in plain English, like you're explaining to a 10-year-old, what this
chunk of code does:
[paste the chunk]
```

**When you want to add a small feature:**
```
I want to add [concrete, small feature]. Show me the changes in 1-2 files,
explain in plain English what you're changing and why. Don't refactor anything
else while you're at it.
```

**When the script breaks:**
```
I ran [command] and got this error:

[paste the full error text, from beginning to end]

Analyze what happened, fix it, but first explain in plain English what was wrong.
```

**When you don't understand what the agent did:**
```
Stop. Explain step by step what you just changed in the project and why.
As if I'm completely new to this project.
```

**When the agent is over-engineering:**
```
This solution is too complex for our goal. Propose something simpler, even if
it has fewer features. We're building an MVP, not a production app.
```

### How long this step takes

Realistically: **2-4 hours for the first MVP** (like our listing monitor). Not 30 minutes. If someone tells you "you'll build an app with AI in an hour," either the app is trivial or that person has no production experience.

Break it into 2-3 sessions of an hour each. Take breaks between sessions — you come back fresher, catch bugs better.

---

## 7. Step 3 — Test locally: does it actually work?

### Rule: before you deploy, check it yourself

You can trust the agent that it wrote code that runs. You can't trust that the code does what _you_ wanted. The difference is fundamental.

**Your pre-deploy checklist:**

1. The script runs without errors (`python monitor.py` in the terminal)
2. Output files get created where they should (`output/`, `snapshots/`)
3. Open the dashboard / output and see **real data**, not placeholders like "TODO" or "example.com"
4. Make a **synthetic change** (e.g. manually edit one snapshot file) and run again — does the app detect the change?
5. If the app sends alerts — verify that an alert _actually_ arrives (to your email / Telegram / Slack)

If any step doesn't work — go back to the agent with specifics ("the dashboard shows 'undefined' instead of the app name — fix"), not vague "something's broken."

### When something's wrong and you don't know what

```
Something's off and I don't know what. Diagnose:

What I tried: [step by step what you did]
Expected: [what was supposed to happen]
Actually seeing: [what you see — error message, weird output, blank dashboard]

Full terminal output:
[paste everything from the console]

Contents of the file that worries me:
[file path and contents]

Ask me clarifying questions if something's missing, then start fixing.
```

The more specifics you paste, the better the diagnosis. The agent doesn't see your screen.

---

## 8. Security — six things you MUST know

This is the one section in this document you can't skip. API keys and secrets are like banking passwords — leaks mean someone else's costs charged to your card or your accounts getting stolen.

### 1. API keys live in a `.env` file, NEVER in code

The `.env` file (short for "environment variables") is a local file where you put values like:

```
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxx
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxx
```

**Why not in code:** you commit code to GitHub. If a key is in the code, anyone who opens your repo (and sometimes anyone on the internet, if the repo is public) has your key. Bots scan new GitHub commits in real time looking for keys.

### 2. The `.env` file MUST be in `.gitignore`

`.gitignore` is a list of files Git won't track. Your `.gitignore` should include:

```
.env
.env.local
*.key
secrets/
```

**Verify this before your first `git push`.** How? Open the project folder in terminal and type:
```bash
git status
```

If you see `.env` listed under "untracked files" — git is ignoring it (good). If you see `.env` as "new file to be committed" — **STOP, add `.env` to `.gitignore` and cancel the commit**.

### 3. Your API keys have budgets. Watch the limits.

Every API you use (Gemini, OpenAI, Resend, Twilio...) has some usage limit. Free tiers usually cover hobby projects, but a bug like "run the script 1000 times in a loop" can burn your monthly limit in 5 minutes.

**What to do:**
- **Set usage alerts** in each service's dashboard (e.g. Google AI Studio → Quotas → Email alert at 80%)
- **Never give a credit card number** to APIs you don't strictly need to (Gemini free tier doesn't require a card — that's good)
- **If you must give a card** (some services), set a **hard cap** — e.g. "no more than $5/mo" → exceeding it = service disabled, not billed more

### 4. APIs with destructive access are a different story

A Gemini API key = max damage is exhausting your limit (cents).
A key to an API that can access your company's database / send emails on behalf of the company / has CRM write access = **max damage is a catastrophe**.

If you have to use such an API, **this is not a project to do solo with Antigravity at high trust.** Invite a technical colleague to review the code before you run anything.

### 5. Private vs public repos

GitHub allows both.

- **Public:** code visible to the whole world. OK for hobby/educational projects if you handle secrets right (1+2). **Required** for free GitHub Pages.
- **Private:** only you (or collaborators you invite). Safer. **No free GitHub Pages** for private repos — needs paid plan ($4/mo).

For our case (listing monitor — the data is public, it's store pages anyone can see) **public is fine**. API keys are in `.env` which is gitignored.

For projects with company business data — always private.

### 6. API key leaked? Here's what to do in 60 seconds

1. Go to the service dashboard (e.g. Google AI Studio)
2. **Revoke the leaked key** (revoke / delete)
3. Generate a new one
4. Paste the new key into `.env` locally
5. If you used the key in a deployment (e.g. Vercel, Cloudflare) — update it there too
6. Check billing — did anyone use the key before you revoked it?

The faster you revoke, the better. Leaked Gemini keys are typically picked up by bots within 5-30 minutes of the bad commit.

---

## 9. Step 4 — Deploy: where to put the finished tool

### Requirements for deploying in a corporate environment

We're assuming you / your client works in a company and:
- doesn't have paid GitHub (so Pages on a private repo is out)
- IT won't easily let you sign up for AWS/Azure/GCP
- wants a **non-public dashboard** (basic auth is enough)
- doesn't want to pay

**Recommendation: Cloudflare Pages + Cloudflare Access.** Works for free, corporate clients usually get through (corporate IT doesn't block Cloudflare because it's standard network infrastructure).

### Setting up Cloudflare Pages + Access (20 minutes)

**Step 1: Cloudflare account** ([cloudflare.com/sign-up](https://cloudflare.com/sign-up))
Email + password. No card needed.

**Step 2: Connect your GitHub repo to Cloudflare Pages**
Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git → authorize GitHub → pick the repo. Cloudflare auto-deploys on every commit to `main`.

Build config (for our case — static output):
- Build command: (empty)
- Build output directory: `output`

**Step 3: First deploy**
After connecting, Cloudflare will deploy immediately. You get a URL like `https://your-project.pages.dev`. Open it, verify it works.

**Step 4: Enable Cloudflare Access (email-OTP password protection)**
Cloudflare Dashboard → Zero Trust → Access → Applications → Add an application → Self-hosted.
- Application name: `Edge Listing Monitor`
- Application domain: `your-project.pages.dev`
- Identity providers: pick **One-time PIN** (email OTP — built-in, no config needed)
- Policies → Add policy: "Allow" → Email → enter emails of people who should have access (you + client + team)

**Step 5: Test**
Open `https://your-project.pages.dev` in **incognito**. Cloudflare asks for an email → you enter it → get a code by email → paste it → enter the dashboard. Email-with-code per session (cached ~24h).

The client doesn't have to install anything, doesn't have to sign up anywhere new. They enter their corporate email, get a code, log in.

### Cron (GitHub Actions) — automatic runs in the background

Cloudflare Pages just serves the finished dashboard. We need a separate service that **runs our script every X hours**, generates a fresh dashboard, commits to the repo. Cloudflare deploys on every commit.

That's where **GitHub Actions** comes in — GitHub's built-in cron mechanism. Free, unlimited for public repos, 2000 minutes/month for private (each run costs ~30 sec).

Setup: the repo needs a `.github/workflows/monitor.yml` file with config. Antigravity will generate it — ask:

```
Set up GitHub Actions to run monitor.py every 6 hours, commit the output/ and
snapshots/ folders back to the repo. Pull API keys from GitHub Secrets. Show me
how to add a secret in the GitHub UI (instructions in plain English).
```

After landing the workflow in the repo: GitHub → Settings → Secrets and variables → Actions → New repository secret → add `GEMINI_API_KEY` (and any other keys). The workflow runs at the next scheduled hour (you can also trigger it manually from the UI: Actions → pick workflow → Run workflow).

### Alternative: Google Apps Script Web App (if corporate blocks Cloudflare)

If for some reason Cloudflare isn't an option (e.g. the company already uses another CDN and admin says no), you have a fallback: **Google Apps Script** as the HTML server, hosted for free in your Workspace.

Pros: everything in the client's company domain, access restricted to `"@company.com"`, zero billing, no credit cards.
Cons: you have to rewrite dashboard generation in Apps Script (instead of Python), or keep static HTML in Google Drive with Apps Script just proxying — extra code. Cold start a few seconds.

Realistically: **try Cloudflare first**. Apps Script only if corporate totally blocks Cloudflare.

---

## 10. Bonus: full Google-only stack (when corporate prefers everything in Workspace)

Some companies have a "Google-only ecosystem" policy — admin won't approve Cloudflare, GitHub, etc. There's a path that **wraps the entire app inside the client's Google Workspace**, with no external services, access restricted to the `@company.com` domain natively.

### Google-only architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Entire app contained in the client's Google Workspace          │
│                                                                 │
│  Stitch (UI)  →  Antigravity (code)  →  GitHub (repo)          │
│       ↓                                       ↓                 │
│  wireframe                            (you publish code, but    │
│                                        nothing runs from        │
│                                        GitHub itself)           │
│                                                                 │
│  Apps Script  ←  manually port code from GitHub (or write       │
│       ↓           directly in Apps Script Editor)               │
│                                                                 │
│       ├──→ Time trigger (cron — 1h / 6h / day, free, in UI)    │
│       ├──→ UrlFetchApp (scrape stores, APIs)                   │
│       ├──→ Google Sheets (as DB — alert history)               │
│       ├──→ Properties Service (API keys — stored safely)       │
│       └──→ HTML Service Web App (dashboard with DOMAIN restrict)│
│                                  ↓                              │
│                          Client opens the URL                   │
│                          (Google SSO @company.com)              │
└─────────────────────────────────────────────────────────────────┘
```

One tool (Apps Script) covers: cron + scraper + DB + secrets + hosting + auth. Everything clickable in the browser, client sees data directly in Google Sheets, dashboard at a `*.script.google.com` URL.

### Pros

- **No paid accounts, no credit cards** — everything free, even very active projects (~1000 invocations/day) fit in the free tier
- **Native SSO via Workspace** — `Execute as: me, Access: Anyone in company.com` = one checkbox, end of auth config
- **Client sees data directly in Sheets** — can edit, filter, build pivots without a developer
- **Corporate IT doesn't block it** — it's their own ecosystem
- **No dependency hell** — Apps Script has Sheets/Drive/Gmail/Calendar APIs built in, no library installs

### Cons / limitations

| Limitation | What it means in practice |
|------------|---------------------------|
| **Max 6 min runtime** (30 min on Workspace) | Your scraper has to fit — scraping 100 apps at 10s each won't finish |
| **JavaScript only** | Python is out, Python libraries are out. Most scrapes can be done in JS but not all |
| **No Playwright / headless browser** | JS-rendered sites (SPAs) — hard. Regular HTML / REST APIs — fine |
| **Cold start ~2-5 sec** | First visit to the dashboard after a quiet period is sluggish |
| **No native version control** | Apps Script Editor has "History" but it's not git. Workaround: keep code in a GitHub repo too (manual sync) |
| **No dev/prod environments** | You edit production directly. Workaround: copy the project as "dev" |

### When to choose Google-only over Cloudflare

**Google-only:** when the client says "IT won't let me register at Cloudflare", when the project has marginal needs (1-5 apps, simple dashboard, light scraper), when it matters that the client sees data in Sheets themselves.

**Cloudflare:** when you need Python (e.g. complex HTML parsing, ML libraries), when scraping will exceed 6 min, when you want a full CI/CD with proper code review (GitHub Actions), when you're building something that may scale.

### Hybrid (best of both worlds)

If scraping is heavy (Python, long runtime) but you want the frontend to stay in Google:

```
GitHub repo (Python code)  →  Cloud Run + Python container  →  Cloud Scheduler (cron)
                                       ↓
                              Firestore or Google Sheets (DB)
                                       ↓
                              Apps Script Web App (frontend, DOMAIN-restricted)
```

Heavy backend = Cloud Run (Python container, auto-deployed from GitHub via `gcloud run deploy --source .`, Antigravity will configure it). Light frontend = Apps Script (client sees it via SSO). Shared DB = Sheets (client clicks) or Firestore (if data is complex). Cost: usually $0/mo (Cloud Run has a generous free tier).

### When NOT to go full Google-only

If the project:
- will be sold as an external product (paying customers outside the company) → standard stack (Vercel/Cloudflare) is more flexible
- uses non-standard technologies (e.g. real-time WebSockets, video streaming) → Apps Script can't handle that
- has critical SLAs for business → Apps Script has known uptime limits, not suited for critical infra

---

## 11. Database — when do you need one and which to pick

Most micro-tools don't need a full database — JSON files in the repo are fine (like our monitor). But sometimes you want more: searchable history, data for charts, data the client edits themselves.

### Decision tree

```
Does the client want to EDIT data themselves (filter, add their own notes)?
   ├── YES   → Google Sheets as DB (Apps Script Sheets API)
   └── NO    → continue

Is the data complex nested JSON (e.g. snapshots with many levels)?
   ├── YES   → Firestore (NoSQL, free tier 50k reads/day)
   └── NO    → continue

Is the data simple relational records (customers → orders → products)?
   ├── YES   → Cloud SQL (Postgres, but this is $10+/mo)
   └── NO    → JSON files in the repo are enough
```

### Google Sheets as DB — when it's great

- **<10,000 rows** (slows down beyond)
- **Few writes** (max a few/min) — Sheets hates hundreds of writes/sec
- **Client wants to see data directly** — they open the sheet, sort, filter, build pivots
- **Flat structure** — columns and rows. Nested JSON needs flattening

In our case (Edge monitor) — alert history (currently `history/alerts.jsonl`) **could be in Sheets** instead of a JSONL file. The client would see a table, sort by date, filter per app. Plus a second sheet in the same file — list of apps to monitor (instead of `config.yaml`).

### Firestore — when it makes sense

- Data is **nested JSON** (like our `snapshots/microsoft-edge_ios.json` with nested images and IAE)
- You do **search** on specific fields (e.g. "show all alerts from March")
- You expect **many readers/writers** concurrently
- Free tier (50k reads / 20k writes / day) covers ~100 changes/day projects

### When to use no DB at all

If:
- Data is just "state snapshots" (like our JSON files)
- You don't need search / filtering (just latest state + git commit history)
- You don't want to introduce another layer to learn

Then **JSON files in the repo + git history** is the KISS solution (Keep It Simple Stupid). Working and understandable.

---

## 12. What's next — iterating and video tutorials

### How to iterate with the agent after the first MVP

Most common mistake: built an MVP, it works, "we're done." **MVP is just the start.** Realistic cycle:

```
MVP works
   ↓
You use it for a week, write down "what irritates me / what's missing"
   ↓
Pick the 1-2 biggest pain points
   ↓
Go back to Antigravity with a PRD for those 1-2 changes
   ↓
Agent adds them, you test, commit, deploy
   ↓
Use for another week
```

After 2-3 months of this cycle you have a tool tailored to you that nobody on the market sells. **You couldn't have bought this.**

### When to ask for human help

Some situations are out of scope for "agent + non-technical user":

| Situation | Why |
|-----------|-----|
| The app touches real customer data | Consequences of a mistake = catastrophe, GDPR, etc. |
| The app sends emails/messages as you/your company | Risk of losing reputation, getting your domain blocked |
| The app integrates with company systems (CRM, ERP) | Requires understanding of APIs and company security policies |
| The app will be sold as a product | Different level of code quality, compliance, support |
| The agent started doing things you don't understand and won't explain | Don't use what you don't understand |

In those cases, stop and ask a developer colleague for a 1-hour review before running anything.

### Outline of an educational video series — proposal (to record later)

If you want to record a series for others learning this:

**Episode 1 — "Mindset and flow" (8 min)**
- Why "build me an app" doesn't work
- Three rules (doesn't read minds / small step / doesn't know what it doesn't know)
- Flow demo (Stitch → Gemini → Antigravity → Deploy) on a whiteboard

**Episode 2 — "Stitch: from idea to wireframe" (7 min)**
- Live recording: describing layout, Stitch generates, iterating
- Why a wireframe saves 1-2h of agent iteration

**Episode 3 — "Gemini chat: from idea to PRD" (10 min)**
- Live recording of conversation with Gemini, how to extract a PRD, red flags

**Episode 4 — "Antigravity: setup and first prompt" (12 min)**
- Install, workspace, paste PRD + wireframe, accept plan
- Turning point demo: agent asks something, you decide

**Episode 5 — "Security: .env, .gitignore, API keys" (8 min)**
- What happens when a key leaks (revoke in 60 sec)
- Live `git status` and how to check what you're committing
- Setting alerts in Google AI Studio

**Episode 6 — "Deploy to Cloudflare Pages + Access" (12 min)**
- From zero: Cloudflare signup → connect GitHub → first deploy → configure Access
- Show client (different email) logging in via incognito

**Episode 7 — "Cron, alerts, iteration" (10 min)**
- GitHub Actions setup
- Telegram/Google Chat alerts
- Week of use → notes → next iteration in Antigravity

Total: ~70 minutes of material, chunked into digestible pieces.

---

## 13. Cheat sheet — the most important things on one page

**Philosophy:**
- Small step → check → next step
- Describe _what_ and _how you'll know it worked_, not _how_
- The agent doesn't know what it doesn't know
- A wireframe is one picture worth 500 words of prompt

**Flow:**
- Inspiration → Stitch (wireframe) → Gemini chat (PRD) → Antigravity (build) → test locally → push to GitHub → deploy

**Security:**
- `.env` in `.gitignore` — always
- API keys NEVER in code
- Hard caps on API budgets in service dashboards
- `git status` before every `git push`

**When things break:**
- Copy the full error text, paste to agent, describe what you did
- If the agent starts over-engineering — "I want the simplest, MVP not production"
- If you don't understand — "explain in plain English like you're explaining to a child"

**Deploy — decision tree:**
- **Cloudflare Pages + Access** (email OTP) — general default, works everywhere
- **Apps Script Web App** (Google-only stack) — when corporate won't allow Cloudflare, client has Workspace
- **Cloud Run + IAM** (hybrid) — when you need Python, long runtime, but dashboard has to be in Workspace
- **GitHub Pages** — only if repo is public and client is OK with that

**Database — decision tree:**
- **None (JSON in repo)** — when data is state snapshot, no search needed
- **Google Sheets** — when client wants to edit/filter, <10k rows, few writes
- **Firestore** — when JSON is complex, many writes, generous free tier
- **Cloud SQL / Postgres** — when truly relational data with real complexity ($10+/mo)

**Cron:**
- **GitHub Actions** — when code is in GitHub, scrape can take up to 6h, 2000 free min/mo
- **Apps Script time triggers** — when logic is in Apps Script, max 6 min run, 3 clicks in UI
- **Cloud Scheduler** — when backend is on Cloud Run, $0.10/job/mo (3 free)

**When to stop and call a developer:**
- Real company customer data
- CRM/ERP integrations
- App as a sold product
- Agent doing things you don't understand

---

*Good luck. The worst thing you can do is not start because you're afraid you don't know how — the agent is there to teach you while you work. The best thing: start with the simplest sensible MVP, hand it off (to yourself, your team), iterate.*
