# PRD: Edge Listing Monitor

**Projekt:** Agent monitorujący zmiany w listingach Microsoft Edge na App Store i Google Play
**Wersja PRD:** 1.0
**Data:** 17 maja 2026
**Środowisko buildu:** Google Antigravity (agentic IDE)
**Autor:** przygotowane dla sesji szkoleniowej z klientem nietechnicznym

---

## 1. Po co to robimy (one-liner)

Chcemy mieć **automatycznego asystenta, który codziennie sprawdza stronę aplikacji Microsoft Edge w App Store i Google Play i pisze do nas, gdy coś się zmienia** — np. zmieniono opis, podmieniono screen, dodano event promocyjny albo wyszła nowa wersja.

Zamiast samemu wchodzić co dzień do dwóch sklepów i porównywać "co było wczoraj a co dziś", robi to za nas skrypt, który chodzi sam.

Projekt ma dwa cele:
1. **Produktowy:** mieć działające narzędzie do monitorowania konkurencji/produktu.
2. **Edukacyjny:** nauczyć się i pokazać klientowi, jak Google Antigravity (agentic IDE) pozwala nietechnicznej osobie zbudować realny projekt automatyzacji, w którym agent pisze kod, a my tylko go reviewujemy.

---

## 2. Co dokładnie chcemy łapać (i co to znaczy)

Aplikacja w sklepie składa się z kilku **warstw informacji**. Klient musi rozumieć tę różnicę, bo każda warstwa ma inne źródło danych i inny poziom trudności.

### Warstwa A: Listing metadata (łatwe, must-have w MVP)
Standardowe pola opisu aplikacji — podzielone na **tekstowe** i **wizualne**:

**Tekstowe:**
- **Tytuł** i **podtytuł** (np. "Microsoft Edge: AI Browser")
- **Opis** (długi tekst marketingowy)
- **"What's New" / Release notes** (notki o ostatniej wersji)
- **Wersja** (np. 130.0.2849.68) i **data ostatniego update'u**
- **Kategoria, cena, ocena, liczba ocen**

**Wizualne (kompletna lista — wszystko monitorujemy):**

| Asset | App Store (iOS) | Google Play (Android) |
|---|---|---|
| **Ikona aplikacji** | 1024×1024 | 512×512 |
| **Screenshoty telefon** | do 10, różne rozmiary (6.7", 6.5", 5.5") | do 8, min 320px |
| **Screenshoty tablet** | do 10 dla iPada (12.9", 11") | do 8 dla tableta |
| **Preview video** | do 3 wideo per device, max 30s | 1 wideo (link YouTube) |
| **Feature graphic** | brak | 1024×500 — duży obrazek nad ikoną na stronie listingu |
| **Promo graphic** | brak | 180×120 (deprecated ale czasem jeszcze używane) |
| **TV banner** | brak | tylko Android TV |

Zmiana którejkolwiek z tych rzeczy — **tekstowych lub wizualnych** — = alert. To jest **kluczowy wymóg klienta**: nie wystarczy "wykryć że coś się zmieniło", trzeba **pokazać co się zmieniło, wizualnie, w alercie**.

### Warstwa B: In-App Events / Promotional Content (trudniejsze, opcjonalne)
**In-App Events** to feature Apple od iOS 15 — czasowe karty wydarzeń (np. "AI weekend challenge", "Limited time offer") pojawiające się **przed opisem aplikacji**. Trwają do 31 dni.

**Promotional Content** to Google'owy odpowiednik (dawniej "LiveOps") — wprowadzony w 2022, trwa do 4 tygodni, też pokazywany na stronie listingu.

**Realnie:** Edge prawdopodobnie nie używa tych formatów (to bardziej narzędzie dla gier i appek z eventami). W tygodniu 1 weryfikujemy empirycznie czy w ogóle są, i wtedy decydujemy czy budujemy detektor.

### Warstwa C: Zewnętrzne źródła Microsoftu (bonus, łatwe)
Microsoft publikuje **oficjalny, publiczny changelog dla Edge mobile** na `learn.microsoft.com`:
- Stable Channel: https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-mobile-stable-channel
- Beta Channel: https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-mobile-beta-channel

To zazwyczaj **bardziej szczegółowe** niż "What's New" w sklepie. Dorzucamy jako trzecie źródło prawdy — daje pełniejszy obraz "co się dzieje w Edge'u".

---

## 3. Skąd bierzemy dane (techniczne źródła)

| Źródło | Co stąd | Jak technicznie | Trudność |
|---|---|---|---|
| **iTunes Lookup API** (Apple) | Listing metadata Edge iOS | Publiczne API, JSON, `https://itunes.apple.com/lookup?bundleId=com.microsoft.msedgemobi` | ⭐ trywialne |
| **Google Play HTML** | Listing metadata Edge Android | Biblioteka `google-play-scraper` (Python lub JS) | ⭐⭐⭐ średnie, fragile |
| **`apps.apple.com` HTML** | In-App Events (jeśli są) | Scraping + parsowanie JSON z `<script>` tagu | ⭐⭐⭐⭐ trudne |
| **Google Play HTML (Promotional Content)** | Promotional Content (jeśli są) | Scraping HTML | ⭐⭐⭐⭐ trudne |
| **learn.microsoft.com release notes** | Oficjalny changelog Edge mobile | Prosty fetch + diff Markdown | ⭐ trywialne |

**MVP** = iTunes API + google-play-scraper + Microsoft release notes.
**v2** = + In-App Events i Promotional Content (jeśli okaże się, że Edge ich używa).

---

## 4. Gotowe biblioteki, które wykorzystamy (a nie piszemy od zera)

Sporo tego problemu jest już rozwiązanego. Nie wymyślamy koła na nowo:

- **[facundoolano/app-store-scraper](https://github.com/facundoolano/app-store-scraper)** — Node, wrapper na iTunes API + scraping App Store. Maintained, ale wolno.
- **[facundoolano/google-play-scraper](https://github.com/facundoolano/google-play-scraper)** — Node. **UWAGA: autor nie rozwija aktywnie, parser psuje się przy zmianach layoutu Google.** Pull requesty od community.
- **[JoMingyu/google-play-scraper](https://github.com/JoMingyu/google-play-scraper)** — Python port, aktywniej utrzymywany.
- **[digitalmethodsinitiative/itunes-app-scraper](https://github.com/digitalmethodsinitiative/itunes-app-scraper)** — Python, akademickie, MIT.
- **[dgtlmoon/changedetection.io](https://github.com/dgtlmoon/changedetection.io)** — gotowe narzędzie do change detection dowolnej strony, self-hosted. Można rozważyć jako **całkowity skrót** zamiast pisania własnego skryptu.
- **Wzorzec Git scraping** ([Simon Willison](https://simonwillison.net/2020/Oct/9/git-scraping/)) — pattern, nie biblioteka: cron commituje snapshoty do repo, diff i historia za darmo. **Bardzo rekomendowane dla nietechnicznego klienta**.

---

## 5. Decision Tree: Lokalnie czy w chmurze?

To największa decyzja architektoniczna i zależy od preferencji klienta. Oto trzy ścieżki z konsekwencjami w codziennym życiu:

### Ścieżka A: GitHub Actions cron (REKOMENDOWANA)
**Co to znaczy w praktyce:**
- Skrypt mieszka w darmowym repo na GitHubie.
- GitHub uruchamia go automatycznie co 6h (lub jak ustawimy) **bez Twojej obecności**.
- Snapshoty commitowane do repo → historia zmian widoczna w UI GitHuba (diff zielono/czerwono).
- Alerty na Slacka/email/Discord przez webhook.

**Codzienne realia:**
- Laptop może być wyłączony. Internet nie jest potrzebny. Wszystko dzieje się "w chmurze GitHuba".
- Koszt: **0 zł** (mieścimy się w darmowym tierze GitHub Actions: 2000 minut/mies).
- Konfiguracja: jednorazowa, 2-4h pracy z agentem.
- Maintenance: gdy scraper Play Store się popsuje (~co 1-3 mies), trzeba poprosić agenta o naprawę.

**Wady:** trzeba mieć konto GitHub (proste, darmowe).

### Ścieżka B: Google Cloud Run Jobs / Cloud Scheduler
**Co to znaczy w praktyce:**
- Skrypt mieszka w kontenerze w Google Cloud.
- Cloud Scheduler odpala go cyklicznie.
- Storage w Cloud Storage lub Firestore.

**Codzienne realia:**
- Laptop może być wyłączony.
- Koszt: **~$0–5/mies** (mieścimy się prawie cały czas w free tier GCP).
- Konfiguracja: trudniejsza niż GitHub Actions, ale spójna z innymi narzędziami Google jeśli klient już ich używa.
- **Tematyczna spójność z Antigravity** (też produkt Google) — może być argumentem szkoleniowym.
- Maintenance: jak wyżej.

**Wady:** wymaga karty kredytowej w GCP, więcej "ruchomych części" do skonfigurowania.

### Ścieżka C: Lokalnie na laptopie / Raspberry Pi
**Co to znaczy w praktyce:**
- Skrypt uruchamiany przez systemowy cron (Mac/Linux) lub Task Scheduler (Windows).
- Plik SQLite lokalnie.

**Codzienne realia:**
- **Laptop musi być włączony w momencie uruchomienia skryptu.** Jeśli skrypt ma chodzić co 6h, a Ty pracujesz w godzinach 9-17 i wyłączasz wieczorem — przegapi uruchomienia.
- Koszt: 0 zł.
- Maintenance: codzienne, mentalne ("czy się włączył?").
- Raspberry Pi (~250 zł) rozwiązuje problem włączania — chodzi 24/7.

**Sensowne tylko gdy:** klient chce mieć kompletną kontrolę nad danymi i nie chce nic w chmurze.

### Rekomendacja
**Ścieżka A (GitHub Actions)** dla 90% przypadków. Najmniej tarcia, najwięcej wartości dla nietechnicznego klienta (widzi commity = "agent zrobił dziś tę pracę"). Jeśli klient jest mocno zinwestowany w Google Cloud — Ścieżka B.

---

## 6. Stack rekomendowany

Pod ścieżkę A (GitHub Actions), klient nietechniczny:

- **Język: Python.** Czytelniejszy diff niż JS, lepsze biblioteki naukowe (DeepDiff), ekosystem Pythona jest standardem dla skryptów automatyzacji. Antigravity świetnie radzi sobie z Pythonem.
- **Biblioteki:**
  - `requests` — fetch iTunes API, learn.microsoft.com i pobieranie binarek (screeny, ikony)
  - `google-play-scraper` (JoMingyu fork) — Play Store
  - `beautifulsoup4` + `lxml` — parsowanie HTML (release notes Microsoftu, ewentualnie IAE)
  - `deepdiff` — porównywanie struktur JSON (tekst)
  - `hashlib` — SHA256 plików (twardy hash, do detekcji "binarka się zmieniła")
  - **`imagehash` + `Pillow`** — *perceptual hashing* obrazków (pHash, dHash) — wykrywa "ten sam obrazek mimo rekompresji" vs "naprawdę inny obraz"
  - **`Pillow`** — generowanie side-by-side comparison ("przed/po")
  - **`google-genai`** — Gemini 2.5 Flash Vision API do AI opisu różnicy między obrazkami (darmowy tier ~1.5k req/dobę)
- **Storage:**
  - **Tekst (snapshots JSON):** pliki w repo + git history (Simon Willison pattern). Bez bazy danych.
  - **Grafiki (current state):** folder `assets/` w repo, **plik zastępowany przy zmianie** (nie historycznie) → git i tak pamięta delta w historii commitów, ale aktywne pliki nie puchną.
  - **Grafiki (przed/po do alertu):** generowane on-the-fly, hostowane w `assets/_alerts/` w repo z URL `https://raw.githubusercontent.com/...` — dla Google Chat i email wystarczy URL, nie trzeba uploadować pliku.
  - **Limity GitHuba:** repo darmowe do 5GB, plik do 100MB. Edge ma ~20MB wszystkich assetów → bezpiecznie na lata.
- **Alerty (dwa kanały równolegle):**
  - **Google Chat** — incoming webhook do Space, format Card v2, obsługuje obrazki przez URL (nie trzeba uploadować jak Slack). Setup w 5 min w Google Workspace.
  - **Email** — przez [Resend](https://resend.com) (3000 maili/mies free) albo [Mailgun] (100/dzień free). HTML email z embedded images.
  - Oba kanały dostają ten sam content, klient sam decyduje co czyta.
- **AI interpretacja:** Gemini 2.5 Flash z dwoma obrazkami w prompcie → tekst opisu różnicy. Trafia do treści alertu zamiast/oprócz załączonych obrazków.
- **Cron:** GitHub Actions `schedule` co 6h.

**Dlaczego nie Node?** Oryginalne biblioteki facundoolano są w JS i są dobre, ale dla klienta nietechnicznego Python jest czytelniejszy podczas reviewu kodu w Antigravity. To bardziej preferencja edukacyjna niż techniczna.

---

## 7. Jak to działa krok po kroku (user journey)

```
[Co 6h]
   ↓
[GitHub Actions odpala skrypt monitor.py]
   ↓
[1. Fetch z iTunes API → snapshot Edge iOS]
[2. Fetch z Google Play scraper → snapshot Edge Android]
[3. Fetch z learn.microsoft.com → release notes]
[4. (opcjonalnie) Scrape apps.apple.com → IAE]
   ↓
[Porównanie z poprzednim snapshotem (poprzedni commit w repo)]
   ↓
[Jeśli różnica → commit + alert na Slacka]
[Jeśli bez zmian → cicho]
   ↓
[Klient widzi:]
  - Slack message: "Edge iOS: zmieniono opis aplikacji + 2 nowe screeny"
  - Link do diffa w GitHubie (zielono/czerwono)
  - Link do nowej strony w sklepie
```

**Co klient zobaczy w praktyce każdego dnia:**
- Większość dni: **nic**. To dobre, znaczy że apka się nie zmieniła.
- 2-3 razy w miesiącu: powiadomienie na Slacku gdy Microsoft wypchnie update.
- W repo GitHub: codzienna historia "snapshot z dnia X", dostępna do przeglądania jak kalendarz.

---

## 7b. Wizualna detekcja zmian — pełny flow (kluczowy dla klienta)

Klient powiedział wprost: **chcemy łapać każdą zmianę graficzną — screeny, ikony, wszystko**. To wymaga zniuansowanego podejścia, bo "porównaj plik" naiwnie zwróci dużo fałszywych alertów.

### Czterostopniowy filtr zmian (z AI interpretacją)

```
[Krok 1: Porównaj URL]
   ↓ URL ten sam → brak zmiany, koniec
   ↓ URL inny → idź dalej

[Krok 2: Pobierz oba pliki, porównaj SHA256]
   ↓ Hash ten sam → URL się zmienił ale plik nie (CDN reshuffle) → ignorujemy
   ↓ Hash inny → idź dalej

[Krok 3: Porównaj perceptual hash (pHash)]
   ↓ Pliki różne ale pHash identyczny → tylko rekompresja/optymalizacja → log, bez alertu
   ↓ pHash różny → REALNA WIZUALNA ZMIANA → idź do AI

[Krok 4: Gemini 2.5 Flash Vision — opisz różnicę]
   ↓ Wyślij stary i nowy obraz do Gemini z promptem
     "Porównaj te dwa screenshoty z App Store dla tej samej apki.
      Opisz CO konkretnie się zmieniło (tekst, kolory, layout, elementy UI).
      Odpowiedź max 2-3 zdania, po polsku."
   ↓ Otrzymany opis → dorzucany do alertu jako "tekst zmiany"
```

### Czym jest perceptual hash (po ludzku)
Zwykły SHA256 mówi "czy bajty są identyczne" — jeden piksel inaczej = inny hash. Apple/Google regularnie rekompresują obrazki (np. przy zmianie kodeka WebP → AVIF) — dla użytkownika obraz wygląda tak samo, ale SHA256 jest inny. To byłby **fałszywy alert co tydzień**.

**Perceptual hash** mówi "czy obrazki wyglądają podobnie" — odporne na rekompresję, zmianę formatu, drobne kolorystyczne korekty. Dwa screeny tego samego ekranu dadzą identyczny pHash, mimo że pliki są różne.

### Jak wygląda alert do klienta
Google Chat message (i równolegle HTML email) po wykryciu realnej zmiany:

```
🔔 Microsoft Edge iOS — wykryto zmiany (17.05.2026, 14:23)

✏️ Tekst:
- Opis: zmieniono 3 zdania w sekcji "AI features" [link do diff w GitHubie]
- Wersja: 130.0.2849.68 → 131.0.2851.12

🖼️ Grafiki:
- Screenshot #2 (iPhone 6.7"): PODMIENIONY
  💬 AI: "Zmieniono nagłówek z 'Browse smarter' na 'Browse with Copilot',
       dodano fioletową ikonę AI w prawym górnym rogu, tło zmieniło się
       z gradientu niebieskiego na ciemnofioletowy."
  [obrazek side-by-side: stary | nowy]

- Screenshot #5 (iPhone 6.7"): PODMIENIONY
  💬 AI: "Zastąpiono screenshot głównego ekranu nową wersją z widocznym
       buttonem 'Ask Copilot' w pasku adresu."
  [obrazek side-by-side: stary | nowy]

- Ikona aplikacji: BEZ ZMIAN
- Preview video #1: BEZ ZMIAN

🔗 Zobacz stronę aplikacji: https://apps.apple.com/...
🔗 Pełny diff w GitHub: https://github.com/.../commit/abc123
```

Każdy "PODMIENIONY" obrazek ma:
1. **Tekst opisu** wygenerowany przez Gemini Vision — najszybsza droga do zrozumienia "co się stało" bez patrzenia na obrazek.
2. **Side-by-side PNG** wygenerowany przez Pillow, hostowany w repo, link wstawiony do alertu.

Klient czyta sam tekst i już wie czego się spodziewać — obrazek otwiera tylko jeśli chce zobaczyć szczegóły. To rozwiązuje problem "muszę zobaczyć alert na telefonie ale obrazek za duży / za mały / niewyraźny".

### Co konkretnie robi skrypt z grafikami

Każdy run cron:
1. Pobiera listę URL wszystkich assetów wizualnych z iTunes API + Google Play scraper.
2. Dla każdego URL: czy się zmienił od poprzedniego snapshota?
3. Jeśli tak: pobierz binarkę → policz SHA256 → policz pHash.
4. Porównaj z plikiem `assets/edge_ios_screenshot_2.png` w repo.
5. Jeśli pHash różny → zastąp plik w repo (git commituje delta), wygeneruj side-by-side, wyślij do Slacka.

### Storage assetów — alternatywy gdyby repo puchło

Dla Edge (~20MB assetów) repo darmowe wystarczy na lata. Ale jeśli klient w przyszłości doda 20 apek (×400MB rocznie wzrostu):

| Storage | Free tier | Sens użycia |
|---|---|---|
| **GitHub repo** | 5GB | MVP, 1-5 apek |
| **Cloudflare R2** | 10GB + 0 egress | 5-50 apek, jeśli chcemy elastycznie |
| **Backblaze B2** | 10GB + 1GB egress/dzień | Alternatywa do R2 |
| **Supabase Storage** | 1GB | Jeśli już używamy Supabase do czegoś innego |

Decyzję podejmiemy gdy/jeśli klient zechce skalować ponad 5 apek.

### Czego NIE łapiemy (świadome ograniczenia v1)

- **Preview video** — pobieranie/porównywanie wideo jest 100× cięższe niż obrazka. Sygnalizujemy tylko zmianę URL (czyli "video zostało podmienione"), bez pHash. Klient sam wchodzi i ogląda.
- **Mikrokorekta kolorów** — pHash może to przepuścić jako "to samo". W praktyce nie chcemy alertu na "delikatnie ciemniejszy hue".
- **Screen w innej lokalizacji** — jeśli klient chce monitorować US i PL, każda lokalizacja ma osobny pHash i osobny alert.

---

## 8. Plan wdrożenia w Antigravity (krok po kroku, jako sesja szkoleniowa)

To jest **scenariusz pokazu klientowi**. Pokazujemy, jak nietechniczna osoba może to zbudować, delegując pracę agentom Antigravity.

### Sesja 1 (2h): Setup + MVP App Store
**Co robimy:**
1. Otwarcie Antigravity, utworzenie nowego workspace'u "edge-listing-monitor".
2. Promptujemy głównego agenta: *"Zbuduj mi skrypt Python, który ściąga metadane Microsoft Edge z iTunes Lookup API, zapisuje do pliku JSON, i porównuje z poprzednim zapisem."* — pokazujemy klientowi, jak agent **planuje, pisze, testuje**.
3. Agent generuje **Artifact: plan implementacji** (lista kroków, klient widzi że to nie magia).
4. Agent pisze kod, sam go uruchamia, pokazuje wynik.
5. Wspólnie reviewujemy — klient widzi że może powiedzieć "zmień X" i agent to zrobi.

**Co klient z tego ma:**
- Realizację, że agent sam testuje to, co napisał.
- Pierwszy działający skrypt (Edge iOS metadata snapshot).

### Sesja 2 (2h): Dorzucamy Google Play + release notes Microsoftu
**Co robimy:**
1. Drugi agent (w równoległej "subtask") — *"Dodaj do skryptu fetch z Google Play dla bundleId com.microsoft.emmx"*.
2. Trzeci agent — *"Dodaj parser release notes z learn.microsoft.com/.../mobile-stable-channel"*.
3. Pokazujemy **multi-agent orchestration** — kluczowy USP Antigravity.

**Co klient z tego ma:**
- Zrozumienie, że można "delegować do trzech pomocników na raz".
- Działający skrypt łapie zmiany w 3 źródłach.

### Sesja 3 (2h): Wizualna detekcja zmian — najbardziej "wow" sesja
**Co robimy:**
1. Promptujemy: *"Rozbuduj skrypt o pełną detekcję zmian graficznych: pobieraj wszystkie ikony, screeny, feature graphics. Porównuj je trójstopniowym filtrem (URL → SHA256 → perceptual hash). Generuj side-by-side comparison PNG przy wykryciu zmiany."*
2. Agent dodaje `Pillow` i `imagehash`, refaktoruje strukturę storage (folder `assets/`).
3. **Live demo:** sztucznie podmieniamy plik PNG w `assets/`, odpalamy skrypt, widzimy alert z obrazkiem przed/po.
4. Pokazujemy klientowi **różnicę między SHA256 a pHash** — promptujemy agenta żeby pokazał ten sam screen w dwóch formatach (JPG, WebP) i zobaczył jak pHash daje to samo, a SHA inne.

**Co klient z tego ma:**
- Najbardziej "magiczny" moment szkolenia — widzi obrazek "przed/po" wygenerowany automatycznie.
- Zrozumienie, że "AI nie magiczne" — pHash to konkretna technika z 2010 roku, agent po prostu wiedział której biblioteki użyć.

### Sesja 4 (2h): GitHub Actions + alerty na Slacka
**Co robimy:**
1. Promptujemy: *"Skonfiguruj GitHub Actions, żeby uruchamiał ten skrypt co 6h i commitował zmiany (w tym podmienione obrazki) do repo. Wyślij alerty na Slacka z załączonymi obrazkami side-by-side."*
2. Agent generuje `.github/workflows/monitor.yml`, integruje Slack Files API (upload obrazków), instrukcje do dodania `SLACK_BOT_TOKEN` jako secret.
3. Push do GitHuba. **Live demo: agent odpala workflow, pokazuje action run + Slack message z obrazkami.**

**Co klient z tego ma:**
- Działający produkt w chmurze, monitoruje 24/7.
- Świadomość że to **kompletnie za darmo** i bez serwera.

### Sesja 5 (opcjonalna, 2h): In-App Events + Promotional Content
**Tylko jeśli weryfikacja w tygodniu 1 pokaże, że Edge faktycznie używa tych formatów.**

---

## 8b. Wersja warsztatowa (jeden 1.5-2h sprint z klientem)

Jeśli klient ma mało czasu i nie chcemy 4 osobnych sesji, **da się zbudować "minimum viable demo" w jednej sesji 1.5-2h**. To zupełnie inny scope niż pełna wersja powyżej — uproszczony, ale działający i imponujący.

### Co świadomie wycinamy żeby zmieścić w 2h
- ❌ Google Play scraper (najbardziej fragile — w warsztacie nie potrzebujemy)
- ❌ GitHub Actions (uruchamiamy ręcznie przyciskiem w Antigravity)
- ❌ Microsoft release notes
- ❌ Pełne 4 kanały alertów — wybieramy JEDEN
- ❌ Storage assetów w git (trzymamy w `/tmp` lokalnie)

### Co zostaje (i to wystarczy do "wow" effect)
- ✅ iTunes API → metadane + URL screenów Edge iOS
- ✅ Pobieranie obrazków, trójstopniowy filtr (URL → SHA256 → pHash)
- ✅ **AI opis różnicy przez Gemini Flash** — to jest serce demo
- ✅ Side-by-side PNG przez Pillow
- ✅ **Jedno** wyjście: lokalny HTML dashboard (`output.html` otwierany w przeglądarce)

### Scenariusz 2h warsztatu

**00:00 – 00:15: Setup**
- Otwieramy Antigravity, tworzymy workspace `edge-monitor`.
- Pokazujemy klientowi UI Antigravity, czym są "agents" i "Artifacts".
- Wklejamy do agenta wstępny brief: *"Buduję skrypt Python, który monitoruje stronę aplikacji Microsoft Edge w App Store i alertuje mnie gdy się zmienia"*. **Agent generuje plan implementacji jako Artifact** — pokazujemy klientowi, że to czytelny dokument, nie magia.

**00:15 – 00:45: Pobieranie danych**
- Promptujemy: *"Napisz skrypt który pobiera metadane Microsoft Edge z iTunes Lookup API (`bundleId=com.microsoft.msedgemobi`) i zapisuje do `snapshot.json`. Pobierz też wszystkie screeny i ikonę do folderu `assets/`."*
- Agent pisze, uruchamia, pokazuje że plik jest.
- **Pierwszy "wow moment":** klient widzi że bez kodowania ma na dysku JSON i 10 PNG-ów ze sklepu.

**00:45 – 01:15: Detekcja zmian + AI**
- Promptujemy: *"Dodaj funkcję która porównuje aktualny snapshot z poprzednim. Dla obrazków użyj URL → SHA256 → pHash filtr. Dla każdej zmiany wizualnej wywołaj Gemini 2.5 Flash Vision z pytaniem 'co się zmieniło między tymi screenshotami'."*
- Agent dodaje `imagehash`, `Pillow`, `google-genai`. Pyta o API key Gemini — generujemy w [Google AI Studio](https://aistudio.google.com) (30 sec, free).
- **Demonstracja:** sztucznie podmieniamy jeden screen w `assets/` (np. odwracamy w Photoshopie/Pillow). Uruchamiamy skrypt. **AI mówi "drugi obrazek to lustrzane odbicie pierwszego".**
- To jest **najmocniejszy moment szkolenia** — klient widzi że AI naprawdę "rozumie" co jest na ekranie.

**01:15 – 01:45: Output — lokalny HTML dashboard**
- Promptujemy: *"Wygeneruj plik `output.html` ze stylizowaną listą wykrytych zmian. Każda zmiana ma tytuł, AI opis, i embedded obrazek side-by-side. Otwórz plik w przeglądarce."*
- Agent generuje HTML z Tailwind CDN, side-by-side przez `<img>` tagi.
- **Drugi "wow moment":** dashboard otwarty w Chrome, klient widzi zmianę z tekstem AI i obrazkami. **Wygląda jak produkt SaaS, nie skrypt.**

**01:45 – 02:00: Wrap-up i co dalej**
- Pokazujemy git history w Antigravity — *"Patrz, tu są wszystkie zmiany które agent zrobił, możesz wycofać każdą"*.
- Mówimy: *"To MVP. Żeby to chodziło samo co 6h, dorzucamy GitHub Actions (5 min). Żeby alert leciał na Google Chat / mail, dorzucamy webhook (10 min). Żeby monitorować też Androida, dorzucamy bibliotekę (15 min)."*
- Klient zostaje z **działającym skryptem na laptopie i jasną wizją jak go rozszerzyć**.

### Co klient zabiera ze sobą po warsztacie
1. **Działający lokalny skrypt** który uruchomi sam (komenda `python monitor.py`).
2. **Plik `output.html`** który może otworzyć i pokazać szefowi.
3. **Roadmapa rozszerzeń** (Google Chat / Android / GitHub Actions / Microsoft release notes).
4. **Praktyczne zrozumienie Antigravity** — wie jak prompować, jak reviewować Artifacts, jak uruchamiać agenta.

### Czego potrzebujemy przed warsztatem
- Klient: laptop z zainstalowanym Antigravity, konto Google (do API key Gemini).
- Ty: gotowy brief do wklejenia (skopiowany z tego PRD), backup plan jeśli coś nie zadziała (np. Edge nie ma zmian — wtedy sztuczna podmiana obrazka jako demo).

### Backup plan na wypadek "nic się nie zmieniło"
W realu Edge może nie zmienić nic w dniu warsztatu. Mamy 3 plany B:
1. **Sztuczna podmiana** — przed warsztatem zapisujemy aktualny screen jako "stary", potem skrypt widzi "nowy" z sklepu (nawet jeśli identyczny, można ręcznie podmienić plik).
2. **Druga apka** — odpalamy też na np. Chrome / TikTok — coś gdzie częściej są zmiany.
3. **Mockowane dane** — agent generuje fake snapshot z modyfikacjami, pokazujemy że flow działa.

---

## 9. Pułapki techniczne (i jak je obejść)

Klient nietechniczny powinien o nich wiedzieć, żeby nie był zaskoczony.

| Pułapka | Co się stanie | Jak omijamy |
|---|---|---|
| **Google Play scraper się psuje** | Po zmianie layoutu Google nasz parser przestaje działać, alerty znikają. | Monitoring: jeśli scraper rzuca błąd 3x z rzędu → alert "scraper się popsuł, popraw". Plan B: poproś agenta o naprawę / aktualizację biblioteki. |
| **Rate limiting Apple (~20/min)** | Przy 1 apce nieproblem. Przy >50 apkach trzeba spowalniać. | Dla Edge'a — niepotrzebne. Skala MVP nie zbliża się do limitu. |
| **Rate limiting Google Play** | Od kilkudziesięciu requestów dziennie Google może czasowo zablokować IP. | Dla 1 apki / 6h = ~4 requesty/dobę = bezpieczne. GitHub Actions ma dynamiczne IP więc rzadziej oberwie. |
| **Lokalizacje** | Edge ma listing w 30+ krajach. Każdy może mieć inny opis/screeny. | MVP: tylko US i PL. Decyzja klienta czy więcej. |
| **Screenshoty — fałszywe zmiany (CDN reshuffle)** | Apple czasem zmienia URL bez zmiany pliku (przeniesienie między serwerami CDN). Sam URL nie wystarczy. | Trójstopniowy filtr: URL → SHA256 → pHash (sekcja 7b). |
| **Rekompresja grafik** | Apple/Google przepuszczają obrazki przez nowy kodek (WebP→AVIF) → SHA inne, ale obraz wygląda tak samo → fałszywy alert co tydzień. | pHash ignoruje rekompresję, tylko realna zmiana wizualna triggerują alert. |
| **Storage assetów puchnie** | Trzymanie historycznych wersji wszystkich obrazków → repo rośnie szybko. | Trzymamy tylko *current* w `assets/`, historyczne wersje są w git history (delta storage). Repo zostaje płaskie. |
| **Google Chat: tylko URL do obrazka, nie upload** | Google Chat Card v2 obsługuje `<img src="...">` ale nie upload pliku w webhooku. | Hostujemy side-by-side PNG w repo (`assets/_alerts/`), URL `raw.githubusercontent.com/...` w karcie. |
| **Gemini Free tier: 1.5k req/dobę** | Przy ~10 zmianach × 10 obrazków × 4 runy/dobę = 400 calls. Bezpieczne. Ale gdy klient skaluje do 20 apek — przekroczy. | Cache: jeśli ten sam pHash był już opisany w przeszłości, reuse opisu. Albo upgrade na płatny Gemini ($0.075/1M tokens — grosze). |
| **Gemini halucynuje opis obrazka** | Model może opisać coś czego nie ma. | W prompcie wprost: *"Jeśli nie widzisz różnicy lub jest minimalna, napisz 'brak istotnej zmiany'"*. Plus klient i tak widzi obrazek side-by-side. |
| **Email: HTML w outlooku łamie się** | Outlook ma archaiczny rendering HTML — embedded CSS często ignorowany. | Używamy [Resend](https://resend.com) z gotowymi templates, testowanych w Outlook/Gmail/Apple Mail. |
| **Preview video — niemożliwe do hashowania** | Hashowanie video jest 100× droższe niż obrazka. | Sygnalizujemy tylko zmianę URL ("video podmienione"), bez porównania zawartości. |
| **Whitespace / kolejność w opisie** | Apple/Google czasem normalizują formatowanie — wykryjemy "zmianę", a tak naprawdę żadnej nie było. | Przed porównaniem: trim, normalize whitespace, sortuj listy gdzie kolejność nieistotna. |
| **GitHub Actions: 2000 min/mies free** | Przy uruchomieniu co 6h skrypt zajmuje ~2 min = 240 min/mies. Bezpiecznie. | Monitoring zużycia w settings GitHuba. |
| **Sekrety (Slack webhook URL)** | Nie wkleimy do kodu, bo publiczne repo. | GitHub Secrets — szyfrowane env vars dla Actions. |

---

## 10. Alternatywy (jeśli klient nie chce budować)

Klient powinien znać opcje. Może po sesji pokazu stwierdzi: *"OK, fajnie wiem jak to działa, ale w produkcji weźmy gotowca."*

| Rozwiązanie | Co daje | Cena | Kiedy ma sens |
|---|---|---|---|
| **[AppFollow](https://appfollow.io)** Free | 2 apki + 1000 keywords, alerty na zmiany listingu | 0 zł | Idealne dla Edge alone — robi dokładnie to co budujemy, bez budowania |
| **AppFollow Standard** | Więcej apek, więcej kanałów alertów | od $29/mies | Gdy chcemy monitorować całą branżę (>2 apki) |
| **[42matters](https://42matters.com)** API | Changelog history, API dla developera | tier-based | Gdy potrzebujemy historycznych danych i pełnego API |
| **[changedetection.io](https://github.com/dgtlmoon/changedetection.io)** | Self-hosted change detection dowolnej strony | 0 zł (self-host) lub $9/mies SaaS | Gdy chcemy "uniwersalnie" monitorować apki + inne strony |
| **[Sensor Tower](https://sensortower.com)** | Enterprise ASO platform | ~$25k/rok | Tylko dla dużych firm marketingowych |
| **Nasz własny skrypt** | Pełna kontrola, edukacja, darmowy, customizowalny | 0 zł + 8-16h naszej pracy | Gdy uczymy się Antigravity i chcemy customizacji |

**Uczciwie:** jeśli celem jest TYLKO monitorowanie Edge i nic poza tym — **AppFollow free tier jest najlepszy**. Budujemy własne, bo (a) uczymy się Antigravity, (b) klient prawdopodobnie będzie chciał poszerzać zakres (więcej apek, dodatkowe źródła Microsoftu, własna logika alertów).

---

## 11. Co klient dostanie na koniec (deliverables)

Po wszystkich sesjach klient ma:
1. **Repo na GitHubie** z całym kodem (publiczne lub prywatne — do decyzji).
2. **Działający workflow** uruchamiający się co 6h.
3. **Slack channel z alertami** o zmianach w Edge.
4. **Historia commit-snapshotów** = wbudowana "baza" zmian od dnia zero, z UI GitHub do przeglądania.
5. **Dokumentację Markdown** (auto-generowaną przez Antigravity) — jak to wszystko działa.
6. **Świadomość techniczną** — wie do czego służy Antigravity, jak prompować agenta, jak reviewować jego pracę.

---

## 12. Co jeszcze nie jest jasne / decyzje do podjęcia z klientem

Te rzeczy musisz potwierdzić z klientem **przed sesją 1**:

1. **Google Chat Space** — który Space dostaje alerty? Czy klient ma Workspace? Tworzymy nowy dedykowany Space "Edge Monitor" czy wrzucamy do istniejącego?
1b. **Email** — na jakie maile? Czy klient ma listę odbiorców (cc-marketing-team@), czy tylko sam dostaje?
2. **Repo publiczne czy prywatne?** Publiczne = free GitHub Actions na darmowym tierze (3000 min/mies vs 2000). Prywatne = bezpieczniej.
3. **Lokalizacje** — tylko US? Tylko PL? US + PL? Wszystkie 30+?
4. **Częstotliwość** — co 6h? Co 12h? Codziennie? (każda zmiana wpływa na zużycie GH Actions minutes)
5. **Czy interesują nas też zmiany w rankingach** (pozycja w kategorii, liczba ocen)? Czy tylko "twarde" zmiany w listingu?
6. **Co z wersjami Edge poza Stable** — chcemy też monitorować Edge Beta / Canary?
7. **Threshold "co już jest zmianą"** — czy literówka w opisie to alert? Czy tylko zmiany >X znaków? (do dyskusji)
8. **Czy klient chce sam móc dodawać apki w przyszłości?** Jeśli tak — trzeba zaprojektować config (lista app IDs w pliku YAML).
9. **Threshold dla pHash** — jak bardzo "różny" obraz to już zmiana? pHash zwraca liczbę 0–64 (Hamming distance). Domyślnie próg ~5 (drobne korekty pomijamy, realne podmiany łapiemy). Klient może chcieć ostrożniej (3) lub luźniej (8).
10. **Czy alertujemy o każdej zmianie ikony?** Ikona zmienia się bardzo rzadko (raz w roku?), ale alert powinien być wtedy "głośniejszy" — może osobny kolor / emoji / @mention?
11. **Side-by-side: pozioma czy pionowa orientacja?** iPhone screen jest pionowy → side-by-side w poziomie zajmuje dużo miejsca. Pionowa układanka (stary nad nowym) lepiej na mobile Slacku.
12. **Czy klient chce w alercie też tekstowy opis tego co się zmieniło w obrazku?** Można dorzucić Claude vision do agenta — *"opisz różnicę między tymi screenami"* — i wkleić do alertu jako bonus. Koszt: ~$0.01 per zmiana.

---

## 13. Risk & mitigation summary (TL;DR)

- **Najbardziej ryzykowne:** scraper Google Play (przewidywalna degradacja co kilka miesięcy).
- **Najmniej ryzykowne:** iTunes API + learn.microsoft.com (oficjalne, stabilne źródła).
- **Najtrudniejsze do zrealizowania:** In-App Events (jeśli okaże się, że Edge ich używa).
- **Najłatwiejsze do przepoczatkowania:** GitHub Actions setup + alerty.
- **Mitigation w 1 zdaniu:** jeśli scraper się psuje, klient dostaje alert "scraper down", a agent w Antigravity to naprawia w 30 min.

---

## 14. Następny krok

Po przeczytaniu PRD i odpowiedzi na pytania z sekcji 12:
1. Stworzyć konto GitHub + Slack webhook (klient).
2. Otworzyć Antigravity i rozpocząć Sesję 1.
3. Iść po kolei przez sekcję 8.

---

## Źródła i referencje

- [iTunes Search API: Lookup Examples](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/LookupExamples.html)
- [Overview of In-App Events – Apple Developer](https://developer.apple.com/help/app-store-connect/offer-in-app-events/overview-of-in-app-events/)
- [Google Play Promotional Content – Google Play Console](https://play.google.com/console/about/programs/promotionalcontent/)
- [Microsoft Edge mobile release notes (Stable)](https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-mobile-stable-channel)
- [Microsoft Edge mobile release notes (Beta)](https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-mobile-beta-channel)
- [facundoolano/app-store-scraper (Node)](https://github.com/facundoolano/app-store-scraper)
- [facundoolano/google-play-scraper (Node, maintenance mode)](https://github.com/facundoolano/google-play-scraper)
- [JoMingyu/google-play-scraper (Python)](https://github.com/JoMingyu/google-play-scraper)
- [digitalmethodsinitiative/itunes-app-scraper (Python)](https://github.com/digitalmethodsinitiative/itunes-app-scraper)
- [dgtlmoon/changedetection.io (universal change detection)](https://github.com/dgtlmoon/changedetection.io)
- [Git scraping pattern – Simon Willison](https://simonwillison.net/2020/Oct/9/git-scraping/)
- [AppFollow pricing & free tier (ASO tools overview)](https://appdrift.co/blog/15-best-app-store-optimization-tools)
- [AppFollow data collection (Bright Data case study)](https://brightdata.com/blog/brightdata-in-practice/appfollow-app-store-optimization-insights)
- [42matters App Market Data APIs](https://42matters.com/app-market-data)
- [Google Antigravity – Developers Blog](https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/)
- [Getting Started with Google Antigravity (Codelabs)](https://codelabs.developers.google.com/getting-started-google-antigravity)
- [Guide to In-App Events & Promotional Content – Radaso](https://radaso.com/blog/guide-to-launching-in-app-events-and-promotional-content-on-the-app-store-and-google-play)
- [imagehash – perceptual hashing dla Pythona](https://github.com/JohannesBuchner/imagehash)
- [Pillow – Python imaging library (PIL fork)](https://pillow.readthedocs.io/)
- [Gemini 2.5 Flash – Vision API docs](https://ai.google.dev/gemini-api/docs/vision)
- [Google AI Studio – generowanie API key (free)](https://aistudio.google.com)
- [Google Chat incoming webhooks](https://developers.google.com/workspace/chat/quickstart/webhooks)
- [Google Chat Card v2 reference](https://developers.google.com/workspace/chat/api/guides/message-formats/cards)
- [Resend – transactional email API](https://resend.com)
