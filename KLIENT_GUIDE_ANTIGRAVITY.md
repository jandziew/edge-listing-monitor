# Buduj własne mikro-narzędzia w Antigravity — przewodnik dla nietechnicznego

> Praktyczny przewodnik krok po kroku jak osoba bez doświadczenia w programowaniu może zbudować realne, działające narzędzie biznesowe używając Antigravity + Gemini. Bazujemy na konkretnym przykładzie: **monitor listingu aplikacji Microsoft Edge w App Store i Google Play** — ale flow działa dla dowolnego „mikro-projektu" (codzienny dashboard, scraper, mały bot, automatyzacja).

---

## 0. Czego się tu nauczysz

Po przerobieniu tego przewodnika będziesz wiedział:

1. **Jak myśleć** o agentowych narzędziach (Gemini, Antigravity, Claude Code) tak, żeby Ci pomagały zamiast Cię frustrować
2. **Jak zaprojektować UI** przez Google Stitch zanim zaczniesz kodować (etap 0, oszczędza 1-2h iteracji)
3. **Jak rozmawiać z Gemini** żeby z mglistego pomysłu wyciągnąć użyteczną specyfikację (PRD)
4. **Jak prowadzić Antigravity** krok po kroku przez budowę aplikacji — gdzie zaufać, gdzie zatrzymać
5. **Jak bezpiecznie** trzymać klucze API, co nigdy nie commitować, jak nie spalić swojego budżetu na API
6. **Gdzie wystawić gotowe narzędzie** — Cloudflare Pages, Apps Script Web App (Google-only), Cloud Run (hybrid)
7. **Jaką wybrać bazę danych** — kiedy wystarczą pliki JSON, kiedy Sheets, kiedy Firestore
8. **Co dalej** — jak rozwijać narzędzie iteracyjnie, kiedy poprosić o pomoc człowieka

---

## 1. Mindset — zanim cokolwiek odpalisz

### Trzy zasady które oszczędzą Ci 80% frustracji

**Zasada 1: Agent nie czyta w myślach.**
Jeśli powiesz „zrób to lepiej", agent zrobi coś losowego co _jemu_ wydaje się lepsze. Jeśli powiesz „zrób tak, żeby kolory były ciemniejsze i font większy", dostaniesz dokładnie to.

> Złota zasada: opisuj _co_ ma się stać i _jak_ poznasz że się udało. Nie opisuj _jak_ to zrobić technicznie — to robota agenta.

**Zasada 2: Mały krok → sprawdź → kolejny krok.**
Nie wrzucaj 10 zmian w jednym promptcie. Wrzuć 1 zmianę, sprawdź czy działa (otwórz wynik, kliknij, zobacz output), dopiero potem kolejna. Bo jeśli zrobisz 10 zmian naraz i coś przestało działać, nie wiesz która z nich to popsuła.

**Zasada 3: Agent nie wie czego nie wie.**
Jeśli zapytasz „czy ta apka jest popularna?", agent odpowie zgadując. Jeśli zapytasz „znajdź w internecie ile pobrań ma ta apka", agent użyje narzędzia do wyszukiwania. Różnica jest fundamentalna. **Zawsze precyzuj skąd informacja ma pochodzić.**

### Czemu agentowi można ufać a czemu nie

| Można ufać | Nie ufaj bez sprawdzenia |
|------------|--------------------------|
| Składni kodu (Python, HTML, JS) | Czy działający kod _robi_ to co chciałeś |
| Wymyślaniu nazw zmiennych, struktury | Twierdzeniom „już naprawione" — uruchom i zobacz |
| Generowaniu wymyślonych przykładów do testów | Wartości danych (linki, ceny, nazwy firm) — może je zmyślić |
| Tłumaczeniu co robi kawałek kodu | Założeniom o Twoim środowisku (jakie masz konta, ile masz Workspace) |

### Dwa najczęstsze błędy nietechnicznych użytkowników

1. **„Zbuduj mi aplikację która robi X"** → dostaniesz wielki gulasz na raz, połowa nie działa, nie wiesz od czego zacząć debug.
   - **Zamiast:** rozbij na 5-10 mniejszych zadań i prowadź jedno po drugim.

2. **Akceptowanie wszystkiego co agent zaproponuje bez patrzenia.**
   - **Zamiast:** po każdym etapie otwórz wygenerowany plik, przeczytaj komentarze, zapytaj agenta „wytłumacz mi co tu się dzieje, po polsku, jakbyś tłumaczył dziecku".

---

## 2. Flow który będziemy realizować

```
┌──────────────────────────────────────────────────────────────────┐
│  Etap 0: Stitch (UI)           Etap 1: Gemini (chat)            │
│  ─────────────────────         ─────────────────────             │
│  • opisuję jak ma wyglądać     • opisuję funkcjonalność          │
│  • generuję wireframe          • Gemini stawia pytania           │
│  • screenshot → do PRD         • finalna spec (PRD.md)           │
│                                                                  │
│  Etap 2: Antigravity           Etap 3: Test lokalnie            │
│  ─────────────────────         ─────────────────────             │
│  • wklejam PRD + wireframe     • odpalam, sprawdzam              │
│  • agent buduje strukturę      • zmieniam, znów odpalam          │
│  • iteruję, weryfikuję         • gdy działa → push               │
│                                                                  │
│  Etap 4: Deploy                                                  │
│  ──────────────                                                  │
│  • Cloudflare Pages + Access (general default)                   │
│  • LUB Apps Script Web App (Google-only stack — sekcja 7b)       │
│  • cron — GitHub Actions LUB Apps Script triggers                │
└──────────────────────────────────────────────────────────────────┘
```

Każdy etap = osobna sekcja niżej. Etap 0 (Stitch) jest opcjonalny ale bardzo polecany — wireframe oszczędza 1-2h iteracji w Antigravity bo agent dostaje wizualną kotwicę zamiast tylko opis słowny.

### Co Ci potrzebne na start

Przed pierwszym etapem załóż konta (wszystkie darmowe):

- **Konto Google** (do Gemini, AI Studio, Stitch) — pewnie już masz
- **Stitch** — wejdź na [stitch.withgoogle.com](https://stitch.withgoogle.com) i zaloguj kontem Google (350 generacji wireframów / m-c za darmo)
- **Konto GitHub** ([github.com/signup](https://github.com/signup)) — do trzymania kodu
- **Antigravity** — ściągnij z [antigravity.google.com](https://antigravity.google.com) lub miejsca które wskaże Ci osoba prowadząca
- **Konto Cloudflare** ([cloudflare.com/sign-up](https://cloudflare.com/sign-up)) — do deployu (lub pomijasz jeśli wybierzesz Google-only stack — sekcja 7b)

Karta kredytowa nie jest potrzebna do żadnego z tych setupów (przy małych projektach mieszczących się w free tier).

---

## 2b. Etap 0 — Stitch: od wyobrażenia do wireframe (opcjonalne, polecane)

### Po co najpierw rysować

Najczęstszy błąd: przychodzisz do Gemini / Antigravity z opisem słownym („dashboard z alertami i historią") i dostajesz coś co _agent_ uważa za dashboard z alertami. Ty miałeś w głowie obraz X, agent zbudował obraz Y, marnujesz godziny na „nie, nie tak miało być, przesuń tu, zmień kolor, dodaj sekcję".

**Wireframe = jeden obrazek wart 500 słów promptu.**

Wklejasz później screenshot wireframe'a do Gemini przy generowaniu PRD i do Antigravity przy pierwszym prompcie — agent ma natychmiast jasność co do układu, czego brakuje, gdzie co ma być.

### Jak używać Stitcha (5-10 min)

1. Otwórz [stitch.withgoogle.com](https://stitch.withgoogle.com), zaloguj kontem Google
2. **New design** → wpisz opis tekstem, np:

   > „Dashboard webowy dla monitorowania aplikacji w sklepach (App Store, Google Play). Trzy sekcje pod sobą: (1) Alerty — kolorowe karty z ostatnimi zmianami, każda z datą wykrycia i datą wydania, (2) Historia alertów — tabela z timestampami i typem alertu, (3) Current State per aplikacja — karty z ikoną apki, wersją, galerią screenshotów. Górą sticky header z nazwą i datą ostatniej aktualizacji. Po prawej sidebar nawigacyjny z listą monitorowanych aplikacji. Styl: clean, Material Design, lekko niebieskie akcenty, light mode."

3. Stitch wygeneruje wireframe w 30 sekund. Wygląda jak prawdziwa strona, klikalna.
4. Iteruj: „dodaj filtr po dacie nad sekcją Alerty", „zmień kolor accentów na zielony", „dodaj dark mode toggle w prawym górnym rogu"
5. Gdy zadowolony — **Export** → zrób **screenshot całej strony** (Cmd+Shift+4 na Mac, Win+Shift+S na Windows) lub użyj wbudowanego eksportu

### Co potem

Masz teraz dwa artefakty:
- **Opis tekstowy** (Twój prompt do Stitcha) — wklejasz do Gemini przy generowaniu PRD jako „tak ma wyglądać UI"
- **Screenshot wireframe** — wklejasz do Antigravity jako pierwszy załącznik z promptem („zbuduj dashboard wyglądający tak, oto wireframe")

### Alternatywy do Stitcha (jeśli z jakiegoś powodu nie chcesz)

| Tool | Plus | Minus |
|------|------|-------|
| **Figma** (free tier) | Standard branżowy, ogromna biblioteka templates | Krzywa uczenia, nie-AI, sam musisz rysować |
| **Excalidraw** | Bardzo proste, hand-drawn vibe (świetne na PRD) | Brak AI, brak realnego UI feel |
| **Pomijam etap 0** | Szybciej zacznę kodować | Agent kombinuje na ślepo, więcej iteracji |

Dla nietechnicznego: **Stitch** jest najprostszy. Tekst → wireframe w 30 sek.

---

## 3. Etap 1: Gemini chat — od pomysłu do PRD

### Po co w ogóle ten etap

Antigravity to genialne narzędzie, ale ma ograniczenie: **dobrze buduje to, co dobrze opiszesz, kiepsko zgaduje to, czego mu nie powiedziałeś.**

Większość frustracji bierze się z tego, że ludzie wrzucają prompt typu „zbuduj mi narzędzie do monitorowania aplikacji" — agent wymyśla 50 rzeczy, połowa to nie jest to co chciałeś, marnujesz godzinę na poprawki.

Rozwiązanie: **najpierw rozmawiamy z Gemini o pomyśle**, dopóki nie mamy konkretnej specyfikacji (PRD = Product Requirements Document). Dopiero potem idziemy do Antigravity z gotowym, jasnym dokumentem.

To trochę jak rozmowa z architektem PRZED zatrudnieniem ekipy budowlanej. Ekipa zbuduje co im powiesz — pytanie czy wiesz co chcesz.

### Jak rozmawiać z Gemini żeby wyciągnął z Ciebie PRD

Otwórz [gemini.google.com](https://gemini.google.com), wybierz najnowszy model (np. 2.5 Pro lub Flash). Zacznij od czegoś takiego:

> **Twój pierwszy prompt do Gemini:**
> ```
> Pomóż mi zaprojektować małe narzędzie biznesowe, które chcę zbudować używając
> agentowego IDE (Antigravity). Jestem nietechnicznym pracownikiem marketingu.
>
> Pomysł w jednym zdaniu: chciałbym codziennie wiedzieć, czy [opisz w 1-2 zdaniach].
>
> Twoja rola: zadaj mi 5-10 pytań które pomogą doprecyzować zakres tego MVP, tak żebym
> mógł potem wkleić wynik jako prompt do Antigravity. Zadawaj pytania pojedynczo, czekaj
> na moją odpowiedź, dopiero potem następne. Nie pisz jeszcze żadnego kodu — najpierw
> chcę mieć jasny opis zakresu.
> ```

Gemini zacznie pytać o rzeczy typu:
- Co dokładnie chcesz monitorować? (lista źródeł danych)
- Jak często sprawdzać? (codziennie, co godzinę)
- Gdzie chcesz dostawać alert? (email, chat, dashboard)
- Co jest „zmianą"? (każda zmiana? tylko istotne?)
- Kto będzie z tego korzystać? (tylko Ty? zespół? klient zewnętrzny?)
- Co _nie jest_ w zakresie? (świadomie wykluczamy żeby nie rozdmuchać)

**Odpowiadaj uczciwie i konkretnie.** Jeśli czegoś nie wiesz, napisz „nie wiem, doradź" — Gemini Ci doradzi.

### Kiedy wiedzieć że PRD jest gotowy

Po 10-15 minutach rozmowy poproś:

> **Drugi prompt do Gemini (finalizacja):**
> ```
> OK, mamy wystarczająco info. Napisz mi teraz PRD (Product Requirements Document)
> w Markdownie, ze strukturą:
>
> 1. Cel (1 akapit)
> 2. Użytkownik i scenariusz użycia (1 akapit)
> 3. Funkcjonalności w MVP (lista 3-7 punktów, każdy max 1 zdanie)
> 4. Co jest poza zakresem MVP (lista, żeby agent nie próbował tego budować)
> 5. Źródła danych i ich format (lista konkretnych URL/API)
> 6. Sposób alertowania (kanały, format wiadomości)
> 7. Stack technologiczny (zaproponuj: Python? Node? co najlepsze dla początkującego)
> 8. Gdzie hostować (najprostsze opcje dla nietechnicznego)
> 9. Bezpieczeństwo (jakie klucze API potrzebne, gdzie je trzymać)
> 10. Plan na pierwsze 2 godziny pracy w Antigravity (lista konkretnych zadań do agenta,
>     w kolejności)
>
> Pisz po polsku, prosto, bez żargonu engineerowego. Wynik wkleję jako pierwszy prompt
> do Antigravity, więc ma być self-contained i precyzyjny.
> ```

**Skopiuj wynik** i zapisz w pliku `PRD.md` na swoim komputerze. To jest twój „kontrakt" z agentem — wracaj do tego dokumentu zawsze gdy agent zacznie robić coś nieprzewidzianego i mówisz „w PRD mamy że X, trzymajmy się tego".

### Czerwone flagi w odpowiedzi Gemini (oznaki że trzeba doprecyzować)

| Co napisał Gemini | Co to znaczy | Co zrobić |
|-------------------|--------------|-----------|
| „Możemy też dodać dashboard z AI insights, automatyczne sugestie marketingowe, integrację z CRM..." | Rozwleka zakres | Powiedz „skupmy się tylko na MVP, te featurey usuń" |
| „W tym celu trzeba postawić bazę danych Postgres na AWS RDS" | Overkill technologii | Powiedz „chcę najprostsze rozwiązanie, dla nietechnicznego, najlepiej bez bazy danych" |
| „Możesz to zrobić w Pythonie, Node.js, Go lub Ruby" | Brak decyzji | Powiedz „wybierz Python — jest najczytelniejszy dla początkujących" |
| „Każdy może to zrobić w 5 minut" | Naiwna ocena | Powiedz „zrób realistyczny szacunek czasu z perspektywy nietechnicznego" |

---

## 4. Etap 2: Antigravity — od PRD do działającego MVP

### Setup Antigravity (5 minut)

1. Otwórz Antigravity (na desktopie albo w przeglądarce — zależy od wersji)
2. Stwórz **nowy projekt** / **nowy workspace** — nazwij go zgodnie z pomysłem (np. `edge-listing-monitor`)
3. Wybierz folder na dysku gdzie ma żyć kod (np. `~/Projects/edge-listing-monitor`)
4. **Ważne:** jeśli Antigravity pyta o preferowany model, wybierz najnowszy Gemini Pro do planowania, Flash do prostych zadań

### Pierwszy prompt — wbij PRD + wireframe

Otwórz panel agenta. Wklej cały PRD który dostałeś od Gemini, **załącz screenshot wireframe'a ze Stitcha** (przeciągnij do okna agenta lub użyj przycisku załącz), a na początek dopisz krótką ramę:

> **Pierwszy prompt do Antigravity:**
> ```
> Cześć. Jestem nietechnicznym użytkownikiem (marketing). Chcę zbudować z Twoją pomocą
> mały tool według poniższego PRD i wireframe'a.
>
> Twoja rola:
> 1. Najpierw przeczytaj PRD, obejrzyj wireframe i powiedz mi po polsku co dokładnie
>    zamierzasz zrobić, w jakich krokach (lista 5-10 punktów). NIE PISZ jeszcze kodu.
> 2. Gdy ja zaakceptuję plan, zaczniesz od pierwszego kroku.
> 3. Po każdym ukończonym kroku zatrzymaj się, pokaż mi co zrobiłeś, poczekaj na moją
>    akceptację zanim ruszysz dalej.
> 4. Pisz komentarze w kodzie po polsku — chcę móc kiedyś sam to czytać.
> 5. Jeśli czegoś nie jesteś pewien — pytaj zamiast zgadywać.
> 6. Trzymaj się tego co jest w PRD i wireframe. Jeśli chcesz dodać coś co tam nie jest —
>    najpierw zapytaj.
>
> Załącznik: wireframe.png (ze Stitcha)
>
> Oto PRD:
>
> ---
>
> [TU WKLEJASZ CAŁY PRD]
> ```

Agent powinien odpowiedzieć **planem działania, nie kodem**. Jeśli od razu zaczął kodować — przerwij i powtórz: „zatrzymaj się, najpierw pokaż plan".

**Bonus:** gdy generujesz dashboard HTML, w jednym z kolejnych promptów napisz „dashboard ma wyglądać tak jak na załączonym wireframie — odtwórz układ jak najwierniej, ale możesz uprościć grafiki." Agent zacznie generować HTML/CSS celowanie pod ten layout.

### Iteracja krok po kroku — turning points

To są momenty, w których agent się zatrzyma i musisz świadomie zdecydować. Pełna lista:

| Moment | Co dzieje się | Twoja decyzja |
|--------|---------------|---------------|
| **Plan działania** | Agent pokazał 5-10 kroków | Czytasz, ewentualnie modyfikujesz („zamiast kroku 3 zróbmy X"), akceptujesz |
| **Wybór bibliotek** | „Użyję `requests` do HTTP i `BeautifulSoup` do scrapowania" | Zwykle akceptujesz. Jeśli widzisz dziwną nazwę — zapytaj „czy to popularna biblioteka czy coś niszowego" |
| **Struktura plików** | „Stwórzę monitor.py, config.yaml, requirements.txt" | Akceptuj jeśli nie ma czegoś podejrzanego (np. agent chce stworzyć 30 plików — wtedy „uprość, chcę max 5-7 plików") |
| **Pierwsze uruchomienie** | Skrypt się odpala, coś robi | **Sprawdź sam co się stało** — otwórz wygenerowane pliki, zobacz czy mają sens |
| **Pierwszy błąd** | Coś się sypie | Skopiuj treść błędu, wklej do agenta: „skrypt rzuca błąd: [tekst]. Co poszło nie tak?" |
| **Commit do GitHub** | Agent proponuje wrzucenie kodu na GitHub | **STOP. Najpierw sprawdź czy w kodzie nie ma sekretów (kluczy API).** Patrz sekcja 6 |
| **Deploy** | Agent proponuje wystawienie online | **STOP. Najpierw zdecyduj _gdzie_ i _dla kogo_ — patrz sekcja 7** |

### Dobre prompty na typowe sytuacje (kopiuj-wklej do Antigravity)

**Gdy chcesz wyjaśnienie:**
```
Wytłumacz mi po polsku, jakbyś tłumaczył 10-letniemu dziecku, co robi ten kawałek kodu:
[wklejasz kawałek]
```

**Gdy chcesz dodać małą funkcję:**
```
Chcę dodać [konkretny, mały feature]. Pokaż mi zmiany w 1-2 plikach, wytłumacz po
polsku co zmieniasz i czemu. Nie rób refaktora przy okazji.
```

**Gdy skrypt się sypie:**
```
Uruchomiłem [komendę] i dostałem ten błąd:

[wklejasz pełną treść błędu, od początku do końca]

Przeanalizuj co się stało, napraw, ale najpierw wytłumacz mi po polsku co było nie tak.
```

**Gdy nie rozumiesz co agent zrobił:**
```
Zatrzymaj się. Wytłumacz mi krok po kroku, co właśnie zmieniłeś w projekcie i czemu.
Jakbym był zupełnie nowy do tego projektu.
```

**Gdy agent kombinuje za bardzo:**
```
To rozwiązanie jest zbyt skomplikowane jak na nasz cel. Zaproponuj prostsze, nawet
jeśli będzie miało mniej featureów. Chcemy MVP, nie produkcyjną aplikację.
```

### Czas trwania tego etapu

Realnie: **2-4 godziny dla pierwszego MVP** (np. naszego monitora listingu). Nie 30 minut. Jeśli ktoś Ci mówi „w godzinę zbudujesz aplikację z AI", to albo aplikacja jest trywialna albo person nie ma doświadczenia produkcyjnego.

Rozbij na 2-3 sesje po 1h. Między sesjami daj sobie odejść — wracasz świeższy, łapiesz błędy.

---

## 5. Etap 3: Test lokalnie — czy to naprawdę działa

### Reguła: zanim wystawisz, sprawdź sam

Agentowi możesz ufać że napisał działający kod. Nie możesz ufać że ten kod robi to czego _Ty_ chciałeś. Różnica jest fundamentalna.

**Twoja checklista przed jakimkolwiek deployem:**

1. Skrypt uruchamia się bez błędów (`python monitor.py` w terminalu)
2. Pliki wynikowe się tworzą tam, gdzie powinny (`output/`, `snapshots/`)
3. Otwierasz dashboard / output i widzisz **realne dane**, nie placeholdery typu „TODO" albo „example.com"
4. Robisz **sztuczną zmianę** (np. ręcznie edytujesz jeden plik snapshotu) i uruchamiasz znów — czy aplikacja wykrywa zmianę?
5. Jeśli aplikacja wysyła alerty — przetestuj że alert _faktycznie_ dochodzi (do Twojego maila / Telegrama / Slacka)

Jeśli któryś krok nie działa — wracasz do agenta z konkretem („dashboard pokazuje 'undefined' zamiast nazwy apki — napraw"), nie z mglistym „coś nie działa".

### Co zrobić gdy coś jest nie tak a nie wiesz co

```
Coś jest dziwne — uruchomiłem skrypt, [opisz co zrobiłeś krok po kroku],
spodziewałem się [co miało się stać], a zamiast tego widzę [co faktycznie się stało].

Pełen output z terminala:
[wklejasz wszystko z konsoli]

Zawartość pliku który mnie martwi:
[ścieżka do pliku i wklejona zawartość]

Zdiagnozuj i napraw.
```

Im więcej konkretów wkleisz, tym lepsza diagnoza. Agent nie widzi Twojego ekranu.

---

## 6. Bezpieczeństwo — sześć rzeczy o których MUSISZ wiedzieć

To jest jedyna sekcja w tym dokumencie której nie wolno przeskoczyć. Klucze API i sekrety to jak hasła do bankowości — ich wyciek = czyjeś koszty na Twojej karcie albo Twój kradzież.

### 1. Klucze API trzymamy w pliku `.env`, NIGDY w kodzie

Plik `.env` (od „environment variables") to lokalny plik gdzie wpisujesz wartości typu:

```
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxx
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxx
```

**Czemu nie w kodzie:** kod commitujesz do GitHuba. Jeśli klucz jest w kodzie, każdy kto otworzy Twoje repo (a czasem każdy w internecie, jeśli repo publiczne) ma Twój klucz. Boty na GitHubie skanują nowe commity w czasie rzeczywistym szukając kluczy.

### 2. Plik `.env` MUSI być w `.gitignore`

`.gitignore` to lista plików których Git nie ma śledzić. Twój `.gitignore` powinien zawierać:

```
.env
.env.local
*.key
secrets/
```

**Sprawdź to przed pierwszym `git push`.** Jak? Otwórz folder projektu w terminalu i wpisz:
```bash
git status
```

Jeśli widzisz `.env` na liście „untracked files" — git go ignoruje (dobrze). Jeśli widzisz `.env` jako „new file to be committed" — **STOP, dodaj `.env` do `.gitignore` i odwołaj commit**.

### 3. Twoje API kluczy mają budżety. Pilnuj limitów.

Każde API które używasz (Gemini, OpenAI, Resend, Twilio…) ma jakiś limit zużycia. Free tier zwykle wystarcza na hobbystyczne projekty, ale błąd w kodzie typu „uruchom skrypt 1000 razy w pętli" potrafi spalić Ci miesięczny limit w 5 minut.

**Co robić:**
- **Ustawiaj alerty zużycia** w panelu każdego serwisu (np. Google AI Studio → Quotas → Email alert at 80%)
- **Nigdy nie podawaj numeru karty kredytowej** w API których nie potrzebujesz koniecznie (Gemini free tier nie wymaga karty — i super)
- **Jeśli musisz podać kartę** (niektóre serwisy), ustaw **twardy budżet** (hard cap) — np. „nie więcej niż $5/mc" → przekroczenie = wyłączenie usługi, nie naliczanie więcej

### 4. API z destruktywnym dostępem traktuj inaczej

Klucz do API Gemini = max szkody to wyczerpanie Twojego limitu (kilka groszy).
Klucz do API które ma dostęp do bazy danych Twojej firmy / może wysyłać maile w imieniu firmy / ma uprawnienia do CRM = **max szkody to katastrofa**.

Jeśli musisz użyć takiego API, **to nie jest projekt do robienia z Antigravity z dużym zaufaniem.** Zaproś technicznego kolegę żeby przeszedł kod z Tobą zanim coś uruchomisz.

### 5. Repozytorium prywatne vs publiczne

GitHub pozwala na oba.

- **Publiczne:** kod widzi cały świat. OK dla projektów hobbystycznych, edukacyjnych, jeśli pilnujesz sekretów (sekcja 1+2). **Wymagane** dla darmowego GitHub Pages.
- **Prywatne:** tylko Ty (lub współpracownicy których zaprosisz). Bezpieczniejsze. **Nie ma darmowego GitHub Pages** dla prywatnych repo — musisz mieć płatny plan ($4/mc).

Dla naszego case'u (monitor listingu, dane są publiczne — to są strony sklepów które każdy widzi) **publiczne repo jest OK**. Klucze API i tak są w `.env` które gitignored.

Dla projektów z biznesowymi danymi — zawsze prywatne.

### 6. Wycieknął Ci klucz API? Co robić w 60 sekund

1. Wejdź na panel serwisu (np. Google AI Studio)
2. **Skasuj wyciekły klucz** (revoke / delete)
3. Wygeneruj nowy
4. Wklej nowy do `.env` lokalnie
5. Jeśli używałeś klucza w deployu (np. Vercel, Cloudflare) — zaktualizuj wartość tam też
6. Sprawdź billing — czy nikt nie wykorzystał klucza przed Twoim revoke

Im szybciej zrobisz revoke, tym lepiej. Wyciekły klucz Gemini przejmują boty zwykle w ciągu 5-30 minut od popełnienia commita.

---

## 7. Etap 4: Deploy — gdzie wystawić działające narzędzie

### Wymagania dla deployu w korpo środowisku

Zakładamy że Ty / Twój klient pracuje w firmie i:
- nie ma płatnego GitHub (więc Pages na private repo odpada)
- IT nie da się łatwo zarejestrować w nowym AWS/Azure/GCP
- chce mieć **niepubliczny dashboard** (basic auth wystarczy)
- nie chce płacić

**Rekomendacja: Cloudflare Pages + Cloudflare Access.** Działa za darmo, klient korpo zwykle przejdzie (IT firm nie blokuje Cloudflare bo to standardowa infrastruktura sieciowa).

### Setup Cloudflare Pages + Access (20 minut)

**Krok 1: Konto Cloudflare** ([cloudflare.com/sign-up](https://cloudflare.com/sign-up))
Email + hasło. Bez karty.

**Krok 2: Połącz repo GitHub z Cloudflare Pages**
Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git → autoryzuj GitHub → wybierz repo. Cloudflare automatycznie deployuje przy każdym commicie do `main`.

Konfiguracja build (dla naszego case'u — gdzie output statyczny):
- Build command: (puste)
- Build output directory: `output`

**Krok 3: Pierwszy deploy**
Po połączeniu Cloudflare od razu zrobi deploy. Dostaniesz URL typu `https://twoj-projekt.pages.dev`. Otwórz, sprawdź że działa.

**Krok 4: Włącz Cloudflare Access (zabezpieczenie hasłem mailowym)**
Cloudflare Dashboard → Zero Trust → Access → Applications → Add an application → Self-hosted.
- Application name: `Edge Listing Monitor`
- Application domain: `twoj-projekt.pages.dev`
- Identity providers: wybierz **One-time PIN** (email OTP — wbudowane, bez konfiguracji)
- Policies → Add policy: „Allow" → Email → wpisz emaile osób które mają mieć dostęp (Ty + klient + zespół)

**Krok 5: Test**
Otwórz `https://twoj-projekt.pages.dev` w **incognito**. Cloudflare poprosi o email → wpisujesz → dostajesz kod na maila → wklejasz → wchodzisz na dashboard. Email z kodem za każdym razem przy nowej sesji (cache na ~24h).

Klient nie musi nic instalować, nie musi zakładać nowych kont. Wpisuje swój firmowy email, dostaje kod na maila, wchodzi.

### Cron (GitHub Actions) — automatyczne uruchomienia w tle

Cloudflare Pages tylko serwuje gotowy dashboard. Musimy mieć osobny serwis który **uruchamia nasz skrypt co X godzin**, generuje nowy dashboard, commituje do repo. Cloudflare przy każdym commicie deployuje nowy.

Do tego używamy **GitHub Actions** — wbudowany w GitHub mechanizm cronowy. Za darmo, dla publicznych repo nielimitowany, dla prywatnych 2000 minut/miesiąc (każdy run nas kosztuje ~30 sekund).

Setup: w repo musi być plik `.github/workflows/monitor.yml` z konfiguracją. Antigravity wygeneruje to za Ciebie — poproś:

```
Skonfiguruj GitHub Actions tak, żeby uruchamiał monitor.py co 6 godzin, commitował
wynikowy folder output/ i snapshots/ z powrotem do repo. Klucze API ma brać z GitHub
Secrets. Pokaż mi jak dodać sekret w UI GitHuba (instrukcja po polsku).
```

Po wgraniu workflow do repo: w GitHubie → Settings → Secrets and variables → Actions → New repository secret → dodajesz `GEMINI_API_KEY` (i ewentualne inne klucze). Workflow uruchomi się przy następnym pełnym godzinie zgodnie z cronem (możesz też uruchomić ręcznie z UI: Actions → wybierz workflow → Run workflow).

### Alternatywa: Google Apps Script Web App (jeśli korpo blokuje Cloudflare)

Jeśli z jakiegoś powodu Cloudflare nie wchodzi (np. firma już używa innego CDN i admin nie chce), masz fallback: **Google Apps Script** jako serwer HTML, hostowany za darmo w infrastrukturze Google Workspace.

Plusy: wszystko w domenie firmy klienta, dostęp ograniczony do `"@firma.com"`, zero billing, zero kart kredytowych.
Minusy: trzeba przepisać generowanie dashboardu na Apps Script (zamiast Pythona) lub trzymać statyczny HTML w Google Drive i Apps Script tylko proxować — to dodatkowy kod. Cold start kilka sekund.

Realistycznie: **najpierw spróbuj Cloudflare**. Apps Script tylko jeśli korpo całkowicie blokuje opcję Cloudflare.

---

## 7b. Bonus: pełny Google-only stack (gdy korpo woli wszystko w Workspace)

Niektóre firmy mają politykę „tylko ekosystem Google" — admin nie zgodzi się na Cloudflare, GitHub itp. Wtedy istnieje ścieżka która **całość zamyka w Google Workspace klienta**, zero zewnętrznych usług, dostęp ograniczony do domeny `@firma.com` natywnie.

### Architektura Google-only

```
┌─────────────────────────────────────────────────────────────────┐
│  Cała aplikacja zamknięta w Google Workspace klienta            │
│                                                                 │
│  Stitch (UI)  →  Antigravity (kod)  →  GitHub (repo)           │
│       ↓                                       ↓                 │
│  wireframe                            (publikujesz kod, ale     │
│                                        nic z niego nie odpala   │
│                                        się w GitHubie)          │
│                                                                 │
│  Apps Script  ←  pobiera kod z GitHuba ręcznie (lub bezpośrednio│
│       ↓           pisany w Apps Script Editor)                  │
│                                                                 │
│       ├──→ Time trigger (cron — 1h / 6h / dzień, free, w UI)   │
│       ├──→ UrlFetchApp (scrapuje sklepy, API)                  │
│       ├──→ Google Sheets (jako baza danych — historia alertów) │
│       ├──→ Properties Service (klucze API — chowane bezpiecznie)│
│       └──→ HTML Service Web App (dashboard z DOMAIN restriction)│
│                                  ↓                              │
│                          Klient otwiera URL                     │
│                          (Google SSO @firma.com)                │
└─────────────────────────────────────────────────────────────────┘
```

Jeden tool (Apps Script) pokrywa: cron + scraper + bazę + secrets + hosting + auth. Wszystko klikalne w przeglądarce, klient widzi dane bezpośrednio w Google Sheets, dashboard pod URLem `*.script.google.com`.

### Plusy

- **Zero kont płatnych, zero kart kredytowych** — wszystko free, nawet bardzo aktywne projekty (~1000 wywołań/dobę) mieszczą się w darmowym limicie
- **Natywne SSO przez Workspace** — `Execute as: me, Access: Anyone in firma.com` = jeden checkbox, koniec konfiguracji auth
- **Klient sam widzi dane w Sheets** — możliwość edytowania, filtrowania, robienia własnych pivotów bez programisty
- **IT firmy nie blokuje** — to ich własny ekosystem
- **Brak dependency hell** — Apps Script ma Sheets/Drive/Gmail/Calendar API wbudowane, nie instalujesz bibliotek

### Minusy / ograniczenia

| Ograniczenie | Co to znaczy w praktyce |
|--------------|-------------------------|
| **Runtime max 6 min** (30 min na Workspace) | Twój scraper musi się mieścić — jeśli scrapujesz 100 apek po 10 sek każda, nie wyrobisz |
| **Tylko JavaScript** | Python out, biblioteki Pythona out. Większość scrape można zrobić w JS, ale nie wszystko |
| **Brak Playwright/headless browser** | Strony renderowane przez JS (np. SPA) — trudne. Zwykłe HTML / REST API — OK |
| **Cold start ~2-5 sek** | Pierwsza wizyta na dashboardzie po przerwie chwilkę chodzi |
| **Brak version control natywnego** | Edytor Apps Script ma „History" ale to nie git. Workaround: kod też trzymasz w GitHub repo (manual sync) |
| **Brak dev/prod environments** | Edytujesz produkcję bezpośrednio. Workaround: zrób kopię projektu jako „dev" |

### Kiedy wybrać Google-only zamiast Cloudflare

**Google-only:** gdy klient mówi „IT mi powie nie na rejestrację w Cloudflare", gdy klient ma marginalne wymagania (1-5 apek, prosty dashboard, mały scraper), gdy zależy na tym żeby klient widział dane w Sheets samodzielnie.

**Cloudflare:** gdy potrzebujesz Pythona (np. parsowanie skomplikowanego HTML, biblioteki ML), gdy scrape przekroczy 6 min, gdy chcesz mieć pełny CI/CD i proper code review (GitHub Actions), gdy budujesz coś co później może rosnąć.

### Hybrid (najlepsze z dwóch światów)

Jeśli scrape jest ciężki (Python, długi runtime), ale chcesz zostawić frontend w Google:

```
GitHub repo (kod Python)  →  Cloud Run + Python container  →  Cloud Scheduler (cron)
                                       ↓
                              Firestore lub Google Sheets (baza)
                                       ↓
                              Apps Script Web App (frontend, DOMAIN-restricted)
```

Backend ciężki = Cloud Run (Pythonowy kontener, automatycznie deployowany z GitHuba przez `gcloud run deploy --source .`, Antigravity Ci to skonfiguruje). Frontend lekki = Apps Script (klient widzi przez SSO). Baza wspólna = Sheets (klient klika) albo Firestore (jeśli dane skomplikowane). Koszt: zwykle $0/mies (Cloud Run ma hojny free tier).

### Kiedy w ogóle nie iść w Google-only

Jeśli projekt:
- ma być sprzedawany jako produkt zewnętrzny (kupują klienci spoza firmy) → standardowy stack (Vercel/Cloudflare) jest bardziej elastyczny
- używa nietypowych technologii (np. real-time WebSockets, video streaming) → Apps Script nie da rady
- ma kluczowe SLA dla biznesu → Apps Script ma znane ograniczenia uptime'u, nie nadaje się do critical infra

---

## 7c. Baza danych — kiedy potrzebna i jaką wybrać

Większość mikro-narzędzi nie potrzebuje pełnej bazy danych — wystarczą pliki JSON w repo (jak nasz monitor). Ale czasem chcesz coś więcej: historia z możliwością wyszukiwania, dane z których robisz wykresy, dane które klient sam edytuje.

### Decision tree

```
Czy klient chce sam EDYTOWAĆ dane (filtrować, dodawać własne notatki)?
   ├── TAK   → Google Sheets jako DB (Apps Script Sheets API)
   └── NIE   → idź dalej

Czy dane to skomplikowany JSON z zagnieżdżeniami (np. snapshoty z wieloma poziomami)?
   ├── TAK   → Firestore (NoSQL, free tier 50k reads/dobę)
   └── NIE   → idź dalej

Czy dane to proste rekordy z relacjami (klienci → zamówienia → produkty)?
   ├── TAK   → Cloud SQL (Postgres, ale to już $10+/mies)
   └── NIE   → JSON pliki w repo wystarczą
```

### Google Sheets jako DB — kiedy świetna

- **<10 000 wierszy** (potem zaczyna wolno działać)
- **Mało zapisów** (max kilka/min) — Sheets nie znosi setek zapisów na sekundę
- **Klient chce widzieć dane bezpośrednio** — wchodzi w arkusz, sortuje, filtruje, robi pivot table
- **Płaska struktura** — kolumny i wiersze. JSON-y zagnieżdżone trzeba flattenować

W naszym przypadku (Edge monitor) — historię alertów (dziś `history/alerts.jsonl`) **mogłaby być w Sheets** zamiast pliku JSONL. Klient by widział tabelę, sortował po dacie, filtrował per apka. Plus na drugim arkuszu w tym samym pliku — lista apek do monitorowania (zamiast `config.yaml`).

### Firestore — kiedy ma sens

- Dane to **JSON z poziomami** (np. nasz `snapshots/microsoft-edge_ios.json` z zagnieżdżonymi obrazami i IAE)
- Robisz **wyszukiwanie** po konkretnych polach (np. „pokaż wszystkie alerty z marca")
- Spodziewasz się **wielu czytelników/zapisów** jednocześnie
- Free tier (50k reads / 20k writes / dobę) wystarczy dla projektów ~100 zmian/dobę

### Kiedy NIE używać żadnej bazy

Jeśli:
- Dane to po prostu „snapshot stanu" (jak nasze JSON-y)
- Nie potrzebujesz wyszukiwania / filtrowania (tylko ostatni stan + historia commitów w git)
- Nie chcesz wprowadzać kolejnej warstwy do nauczenia

Wtedy **pliki JSON w repo + git history** to KISS-owe rozwiązanie (Keep It Simple Stupid). Robocze i zrozumiałe.

---

## 8. Co dalej — iteracje i serie filmików

### Jak iterować z agentem po pierwszym MVP

Najczęstszy błąd: zbudowałeś MVP, działa, „już skończone". **MVP to dopiero start.** Realnie cykl wygląda tak:

```
MVP działa
   ↓
Używasz przez tydzień, robisz notatki „co irytuje / czego brakuje"
   ↓
Wybierasz 1-2 największe bolączki
   ↓
Wracasz do Antigravity z PRD pod te 1-2 zmiany
   ↓
Agent dodaje, testujesz, commitujesz, deploy
   ↓
Używasz przez kolejny tydzień
```

Po 2-3 miesiącach takiego cyklu masz narzędzie szyte na miarę, którego nikt na rynku nie sprzedaje. **Tego nie mógłbyś kupić.**

### Kiedy poprosić o pomoc człowieka

Niektóre sytuacje są poza zakresem „agent + nietechniczny user":

| Sytuacja | Dlaczego |
|----------|----------|
| Aplikacja ma dotykać prawdziwych danych klientów Twojej firmy | Konsekwencje błędu = katastrofa, GDPR, etc. |
| Aplikacja ma wysyłać maile/wiadomości jako Ty/Twoja firma | Ryzyko utraty reputacji, zablokowania domeny |
| Aplikacja ma integrować się z systemem firmy (CRM, ERP) | Wymaga zrozumienia API i polityk bezpieczeństwa firmy |
| Aplikacja ma być sprzedawana jako produkt | Inny poziom jakości kodu, compliance, support |
| Agent zaczął robić rzeczy których nie rozumiesz a nie chce wytłumaczyć | Nie używaj tego co nie rozumiesz |

W takim przypadku zatrzymaj się i poproś kolegę-developera o godzinny review zanim cokolwiek uruchomisz.

### Outline serii filmików edukacyjnych — propozycja (do nagrania później)

Jeśli chcesz nagrać serię uczącą innych:

**Episode 1 — „Mindset i flow" (8 min)**
- Czemu „zbuduj mi aplikację" nie działa
- Trzy zasady (nie czyta w myślach / mały krok / nie wie czego nie wie)
- Pokaz flow Gemini → Antigravity → Deploy w wireframach

**Episode 2 — „Gemini chat: od pomysłu do PRD" (10 min)**
- Live screen recording: opisuję pomysł, Gemini pyta, ja odpowiadam
- Pokazuję jak wyciągnąć PRD na końcu
- Co zrobić gdy Gemini rozwleka zakres

**Episode 3 — „Antigravity setup i pierwszy prompt" (12 min)**
- Instalacja, nowy workspace
- Wklejam PRD, agent pokazuje plan
- Akceptuję, agent zaczyna budować
- Pokazuję turning point: agent pyta o coś, ja decyduję

**Episode 4 — „Bezpieczeństwo: klucze API, .env, .gitignore" (8 min)**
- Pokaz co się dzieje gdy klucz wycieka (revoke w 60 sekund)
- Pokaz `git status` i jak sprawdzić co commitujesz
- Pokaz alertu w panelu Google AI Studio

**Episode 5 — „Deploy do Cloudflare Pages + Access" (12 min)**
- Live od zera: rejestracja Cloudflare → połączenie z GitHub → pierwszy deploy → konfiguracja Access
- Pokazuję jak klient (z innym mailem) loguje się przez incognito

**Episode 6 — „Cron, alerty, iteracje" (10 min)**
- GitHub Actions setup
- Telegram/Google Chat alerty
- Tydzień użytkowania → notatki → kolejna iteracja w Antigravity

Razem: ~60 minut materiału, podzielonego na strawne kawałki.

---

## 9. Cheat sheet — najważniejsze rzeczy na 1 stronie

**Filozofia:**
- Mały krok → sprawdź → kolejny krok
- Opisuj _co_ i _jak poznasz że się udało_, nie _jak_
- Agent nie wie czego nie wie
- Wireframe = jeden obrazek wart 500 słów promptu

**Flow:**
- Stitch (wireframe) → Gemini chat (PRD) → Antigravity (build) → test lokalnie → push do GitHub → deploy

**Bezpieczeństwo:**
- `.env` w `.gitignore` — zawsze
- Klucze API NIGDY w kodzie
- Hard caps na budżetach w panelach API
- `git status` przed każdym `git push`

**Gdy się sypie:**
- Skopiuj pełen tekst błędu, wklej do agenta, opisz co robiłeś
- Jeśli agent zaczyna kombinować — „chcę najprostsze, MVP nie produkcja"
- Jeśli nie rozumiesz — „wytłumacz po polsku jakbyś tłumaczył dziecku"

**Deploy — decision tree:**
- **Cloudflare Pages + Access** (email OTP) — general default, działa wszędzie
- **Apps Script Web App** (Google-only stack) — gdy korpo nie puści Cloudflare, klient ma Workspace
- **Cloud Run + IAM** (hybrid) — gdy potrzebny Python, dłuższy runtime, ale dashboard ma być w Workspace
- **GitHub Pages** — tylko jeśli repo publiczne i klient OK z tym

**Baza danych — decision tree:**
- **Brak (JSON w repo)** — gdy dane to snapshot stanu, nie potrzebujesz search
- **Google Sheets** — gdy klient chce edytować/filtrować, <10k wierszy, mało zapisów
- **Firestore** — gdy JSON skomplikowany, dużo zapisów, free tier hojny
- **Cloud SQL / Postgres** — gdy relacyjne dane z prawdziwą złożonością ($10+/mies)

**Cron:**
- **GitHub Actions** — gdy kod w GitHub, scrape może trwać do 6h, 2000 min free/mies
- **Apps Script time triggers** — gdy logika w Apps Script, max 6 min run, w UI 3 kliknięcia
- **Cloud Scheduler** — gdy backend na Cloud Run, $0.10/job/m-c (3 free)

**Kiedy zatrzymać i zawołać developera:**
- Prawdziwe dane klientów firmy
- Integracje z CRM/ERP
- Aplikacja jako sprzedawany produkt
- Agent robi rzeczy których nie rozumiesz

---

*Powodzenia. Najgorsze co możesz zrobić to nie zacząć ze strachu że nie umiesz — agent jest po to żeby Cię nauczył w czasie pracy. Najlepsze: zacznij od najprostszego sensownego MVP, oddaj do użycia (sobie, zespołowi), iteruj.*
