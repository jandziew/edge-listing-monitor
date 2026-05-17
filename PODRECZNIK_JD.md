# Podręcznik dla JD — projekt Edge Listing Monitor

**Cel:** żebyś świadomie prowadził klienta przez wszystko co używamy, bez zbędnego learningu. Tłumaczenia są napisane tak, żebyś mógł je powiedzieć klientowi (po polsku, prosto, bez żargonu).

---

## 1. Co tu jest na poziomie meta

Robimy skrypt który:
1. Pyta sklepy o aktualną stronę aplikacji
2. Zapisuje wynik na dysk
3. Porównuje z tym co zapisał wcześniej
4. Jeśli coś się różni → wysyła alert

**To wszystko.** Cała reszta (Antigravity, GitHub, Vercel, Gemini, Pillow) to **tylko narzędzia żeby to działało wygodnie**. Klient powinien zrozumieć tę esencję, zanim wejdziemy w narzędzia.

**Jak powiedzieć klientowi:**
> "Wyobraź sobie, że codziennie wchodzisz na stronę aplikacji w App Store, robisz screenshot całej strony, porównujesz z wczorajszym screenem i jak coś jest inaczej — piszesz do siebie maila. To dokładnie to, co robi nasz skrypt. Tyle że robi to za Ciebie co 6 godzin, automatycznie, w chmurze."

---

## 2. Warstwy które używamy (i dlaczego każda)

Tabela do mentalnego mapowania:

| Warstwa | Co to | Po co | Kto płaci |
|---|---|---|---|
| **Python** | Język programowania | Pisze logikę "pobierz, porównaj, wyślij" | Darmowy |
| **Antigravity** | Edytor kodu z AI | Tu agent pisze za nas Python | Darmowy (preview) |
| **iTunes Lookup API** | Strona Apple zwracająca dane apki w formacie JSON | Bierzemy stąd dane z App Store | Darmowy |
| **google-play-scraper** | Biblioteka Pythona | Bierzemy dane z Google Play (bo nie ma oficjalnego API) | Darmowy |
| **Gemini 2.5 Flash** | AI Google'a | Patrzy na 2 obrazki i opisuje co się zmieniło | Darmowy do 1500 zapytań/dobę |
| **Pillow + ImageHash** | Biblioteki Pythona do obrazków | Porównują "czy obrazek się naprawdę zmienił" | Darmowe |
| **GitHub** | Magazyn kodu w internecie | Tu mieszka projekt, działa cron, hostuje stronę | Darmowy do pewnego limitu |
| **GitHub Actions** | Robotnik który uruchamia nasz skrypt | Odpala monitor co 6h, sam | Darmowy do 2000 minut/mies |
| **GitHub Pages** | Hosting statycznych stron | Pokazuje dashboard pod adresem URL | Darmowy |
| **Google Chat** | Komunikator Google | Wysyła nam powiadomienia | Darmowy z Workspace |
| **Resend** | Serwis do wysyłki maili | Wysyła nam email z alertem | Darmowy do 3000 maili/mies |

**Co warto powiedzieć klientowi:**
> "Cały ten stos jest praktycznie darmowy. Płacisz dopiero jak skalujesz do dziesiątek aplikacji lub setek alertów dziennie."

---

## 3. Antigravity 101 (jak go używać świadomie)

### Co to jest
Antigravity to **edytor kodu od Google z wbudowaną AI**. W zwykłym edytorze (Visual Studio Code, Cursor) Ty piszesz kod a AI Ci pomaga. W Antigravity **agent sam pisze, sam testuje, sam uruchamia** — Ty tylko opisujesz co chcesz.

### Kluczowe pojęcia (po ludzku)

- **Workspace** = folder na Twoim dysku, w którym mieszka projekt. Wszystkie pliki, kod, dane. Otwierasz workspace = otwierasz cały projekt.
- **Agent** = pracownik AI. Dajesz mu zadanie, on wykonuje. Możesz mieć wielu agentów na raz pracujących nad różnymi częściami.
- **Artifact** = "dokument efektu pracy" — plik, plan, raport, screenshot — wszystko co agent wyprodukował. Możesz to przejrzeć i zaakceptować.
- **Prompt** = polecenie po polsku/angielsku które dajesz agentowi.

### Jak zacząć

1. Pobierz Antigravity z [antigravity.google.com](https://antigravity.google.com) (lub odpowiedni URL).
2. Otwórz aplikację → **Open Workspace** → wybierz folder gdzie ma siedzieć projekt.
3. Wpisz pierwszy prompt do agenta — np. "Sklonuj repo X z GitHuba i wyjaśnij mi co tam jest".
4. Agent czyta, planuje, działa. Pokazuje Artifact z planem. Zatwierdzasz, jedzie dalej.

### Jak tłumaczyć klientowi

> "Pomyśl o Antigravity jak o juniorze developerze, który nie potrzebuje przerw, nie marudzi, i pisze kod 100× szybciej niż człowiek. Ty jesteś jego menedżerem — mówisz mu czego chcesz, on robi, Ty zatwierdzasz. Nie musisz znać Pythona ani SQL — wystarczy że umiesz powiedzieć 'chcę żeby ten skrypt wysyłał mi maila gdy zmieni się cena na stronie X'."

### Pułapki Antigravity o których warto wiedzieć

- **Agent czasem zmyśla nazwy bibliotek lub funkcji.** Jeśli coś nie działa — powiedz "uruchom skrypt i pokaż błąd" zamiast "popraw". On wtedy zobaczy konkretny błąd i go naprawi.
- **Agent czasem traci kontekst** w długich sesjach. Jeśli zaczyna powtarzać błędy — zacznij nowy chat, wklej istotne pliki.
- **Agent się spieszy** i bywa nadgorliwy. Jeśli robi za dużo — powiedz "tylko zrób X, nie ruszaj reszty".

### Praktyczna zasada

**Nie pisz "popraw kod".** Pisz "uruchom skrypt → pokaż mi output → na podstawie outputu popraw to co nie działa". Agent musi widzieć efekt swojego kodu żeby wiedzieć co naprawiać.

---

## 4. Git i GitHub 101 (dla nietechnicznego)

### Po co to w ogóle
Git to **system kontroli wersji**. Wyobraź sobie Word z funkcją "track changes" włączoną cały czas, dla każdego pliku w projekcie. Możesz w każdej chwili wrócić do dowolnego stanu projektu z dowolnego dnia.

GitHub to **hosting Gita w chmurze** — Twój projekt mieszka tam, jest dostępny zewsząd, możesz dać linka komuś innemu.

### 5 pojęć które musisz znać

| Pojęcie | Po ludzku | Analogia |
|---|---|---|
| **Repository (repo)** | Cały Twój projekt w Git | Folder z dokumentami |
| **Commit** | "Zapisz stan projektu w tym momencie z komentarzem co się zmieniło" | Save w Wordzie, ale z notką |
| **Push** | "Wyślij moje commity do GitHuba" | Upload do Dropboxa |
| **Pull** | "Pobierz najnowsze zmiany z GitHuba" | Sync w Dropboxie |
| **Branch** | Równoległa wersja projektu | "Wersja eksperymentalna" pliku Word |

### Najprostszy workflow w Antigravity

Antigravity ma wbudowanego Gita — większość rzeczy klikasz w UI:

1. **Zmieniłeś jakiś plik** → ikona Git w sidebarze pokazuje "1 change".
2. **Klikasz Git → wpisujesz commit message** (np. "Dodano detekcję ikony") → klikasz **Commit**.
3. **Klikasz Push** → zmiany lecą do GitHuba.

W terminalu (jeśli klient chce zobaczyć):
```bash
git add .                          # przygotuj wszystkie zmiany
git commit -m "Opis zmiany"        # zapisz z notką
git push                           # wyślij do GitHuba
```

### Jak założyć repo na GitHubie (raz, na początek projektu)

1. Załóż konto na [github.com](https://github.com).
2. W prawym górnym rogu **+** → **New repository**.
3. Wpisz nazwę (np. `edge-listing-monitor`), wybierz **Private** (prywatne, tylko Ty widzisz).
4. **Don't initialize** — żebyśmy mogli wrzucić istniejący projekt.
5. Skopiuj URL repo (np. `https://github.com/jd/edge-listing-monitor.git`).
6. W terminalu (lub w Antigravity terminal):
   ```bash
   cd ścieżka/do/projektu
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/jd/edge-listing-monitor.git
   git push -u origin main
   ```

### Jak tłumaczyć klientowi

> "GitHub to Twój sejf na kod plus magazyn dla automatyzacji. Każdy plik tu trafia, każda zmiana ma datę i autora, każdy stan można przywrócić. To darmowe do 5GB. I ważne: GitHub potrafi sam uruchamiać Twój skrypt regularnie — nie musisz mieć włączonego komputera."

### Pułapki Gita o których warto wiedzieć

- **Konflikty merge** — gdy 2 osoby zmienią ten sam plik. W solo-projekcie się nie zdarza.
- **`.gitignore`** — plik mówiący Gitowi co IGNOROWAĆ (np. klucze API, hasła). Bardzo ważny! W naszym projekcie ignorujemy `.env`.
- **Klucze API w repo = katastrofa.** Jeśli wkleisz `GEMINI_API_KEY` do kodu i commitujesz → cały świat ma Twój klucz → Google blokuje. Zawsze przez **GitHub Secrets** lub `.env` (który jest w `.gitignore`).

---

## 5. Python 101 (na poziomie potrzebnym do prowadzenia klienta)

### Co warto wiedzieć

- **Python** = język w którym napisany jest nasz skrypt. Czytelny, ekosystem 100k+ bibliotek.
- **pip** = manager paczek Pythona (jak App Store dla bibliotek). Komenda: `pip install <nazwa>`.
- **requirements.txt** = lista wszystkich bibliotek których używa Twój projekt + ich wersje. `pip install -r requirements.txt` instaluje wszystko z listy.
- **Wirtualne środowisko (venv)** = "izolowane Python tylko dla tego projektu". Zapobiega konfliktom między projektami. Tworzysz raz: `python -m venv venv`, aktywujesz przed pracą: `source venv/bin/activate` (Mac/Linux) lub `venv\Scripts\activate` (Windows).

### Komendy które usłyszysz/zobaczysz

```bash
python --version                # sprawdza zainstalowany Python
python -m venv venv             # tworzy wirtualne środowisko
source venv/bin/activate        # aktywuje je (Mac)
pip install -r requirements.txt # instaluje wszystkie zależności
python monitor.py               # uruchamia nasz skrypt
deactivate                      # wychodzi z venv
```

### Jak tłumaczyć klientowi

> "Python to język dla automatyzacji — Excel z makrami, ale 1000× potężniejszy. Większość 'AI tools' jakie używasz pod spodem to Python. Nie musisz go znać żeby z niego korzystać — Antigravity pisze go za Ciebie."

---

## 6. Vercel / GitHub Pages — gdzie hostować dashboard?

Dashboard to plik HTML — żeby klient mógł go otworzyć z dowolnego miejsca, musi być w internecie.

### Opcja A: GitHub Pages (REKOMENDOWANE)
- **Plus:** darmowe, część GitHuba, zero osobnej konfiguracji.
- **Minus:** statyczna (nie obsługuje formularzy/backendu — ale my tego nie potrzebujemy).
- **Jak włączyć:** w repo: Settings → Pages → Source: `gh-pages` branch. Po pierwszym runie workflowa dashboard pojawi się pod `https://twoj-username.github.io/edge-listing-monitor/dashboard.html`.

### Opcja B: Vercel
- **Plus:** lepszy dla bardziej zaawansowanych stron (Next.js, serverless functions, custom domain łatwiej).
- **Minus:** kolejne konto, kolejny dashboard do ogarniania.
- **Jak działa:** podłączasz Vercel do GitHuba, on przy każdym pushu sam deployuje stronę.
- **Kiedy ma sens dla naszego projektu:** gdy klient w przyszłości chce dorzucić interaktywny UI (formularz "dodaj apkę", konfigurator) — wtedy potrzebny jest backend.

### Jak tłumaczyć klientowi

> "Hosting to po prostu serwer w internecie pod jakimś URL-em. GitHub Pages = darmowy, prosty, dla statycznych stron. Vercel = ten sam serwer ale na sterydach, dla bardziej skomplikowanych aplikacji. My zaczynamy z GitHub Pages — 5 min konfiguracji."

---

## 7. Stawianie projektu w chmurze dla klienta (production setup)

**Scenariusz:** klient chce mieć ten skrypt działający automatycznie na firmę, niezależnie od Ciebie.

### Setup w 30 minut

1. **Klient zakłada konto GitHub** (jeśli nie ma) — może być na maila firmowego.
2. **Klient zakłada konto Google AI Studio** ([aistudio.google.com](https://aistudio.google.com)) — generuje Gemini API key. Darmowe.
3. **Ty pushujesz projekt** na repo klienta (lub klient klonuje z Twojego).
4. **Klient dodaje sekrety** w **Settings → Secrets → Actions**:
   - `GEMINI_API_KEY` — wkleja klucz z AI Studio.
   - `GOOGLE_CHAT_WEBHOOK_URL` — wkleja URL z Google Chat Space.
   - `RESEND_API_KEY` — wkleja klucz z Resend (jeśli chce maile).
5. **Klient włącza GitHub Pages** — Settings → Pages → Source: `gh-pages` branch.
6. **Ręcznie odpalamy workflow** — Actions → Monitor App Listings → Run workflow.

Workflow chodzi sam co 6h, klient dostaje alerty, dashboard żyje pod własnym URL-em.

### Co klient widzi codziennie

- **Email** (jeśli włączony) — w skrzynce gdy są zmiany.
- **Google Chat** (jeśli włączony) — powiadomienie w wybranym Space.
- **Dashboard URL** — zakładka w przeglądarce, otwiera kiedy chce.
- **GitHub repo** — historia commitów to historia zmian aplikacji.

### Co klient płaci

**Realnie:** 0 zł przy normalnym użyciu.
**Maksymalnie:** ~$5/mies jeśli przekroczy darmowe limity GitHub Actions (mało prawdopodobne dla 1-5 apek).

### Jak tłumaczyć klientowi

> "Po tych 30 minutach masz produkt który działa sam i będzie działać latami. Nikt nie musi włączać komputera, nikt nie musi pamiętać. Skrypt chodzi w chmurze GitHuba, używa darmowych usług Google, alerty lecą do Twojej skrzynki. Możesz to porzucić na 6 miesięcy i wrócić — będzie działać. Możesz też w każdej chwili dodać nową apkę albo zmienić co alertuje — wystarczy edytować plik `config.yaml`."

---

## 8. Architektura w 1 obrazku (do narysowania klientowi)

```
   ┌─────────────────────────────────────────────────┐
   │  KAŻDE 6H GitHub Actions odpala monitor.py     │
   └────────────────────┬────────────────────────────┘
                        │
        ┌───────────────┼─────────────────┐
        ▼               ▼                 ▼
   ┌─────────┐     ┌──────────┐    ┌────────────┐
   │ iTunes  │     │  Google  │    │ Microsoft  │
   │   API   │     │   Play   │    │ Learn docs │
   │ (Apple) │     │ scraper  │    │  (release  │
   │         │     │          │    │   notes)   │
   └─────────┘     └──────────┘    └────────────┘
        │               │                 │
        └───────────────┴─────────────────┘
                        │
                        ▼
        ┌─────────────────────────────────┐
        │   Porównanie z poprzednim       │
        │   snapshotem (folder snapshots/) │
        └─────────────────────────────────┘
                        │
                        ▼
        ┌─────────────────────────────────┐
        │   Dla obrazków: pHash + Gemini  │
        │   Vision → opis różnicy         │
        └─────────────────────────────────┘
                        │
        ┌───────────────┼─────────────────┐
        ▼               ▼                 ▼
   ┌─────────┐    ┌──────────┐     ┌──────────┐
   │  Google │    │   Email  │     │   HTML   │
   │  Chat   │    │ (Resend) │     │dashboard │
   │ webhook │    │          │     │(GH Pages)│
   └─────────┘    └──────────┘     └──────────┘
```

---

## 9. Plan szkolenia z klientem (warsztat 2h, krok po kroku)

### Co przygotować PRZED warsztatem
- Klient ma laptop z zainstalowanym Antigravity.
- Klient ma konto Google (do AI Studio + ewentualnie Workspace).
- Klient ma konto GitHub.
- Ty masz gotowy projekt na swoim GitHubie (już go masz po dzisiejszej pracy).
- Slack/Google Chat ze sobą żeby wysyłać linki w trakcie.

### Czas 0:00 – 0:15: Wprowadzenie (bez kodu)
- Powiedz analogię ze screenshot-codziennie.
- Pokaż żywy dashboard z Twojego repo (zrób to dziś wieczorem!).
- Powiedz **co konkretnie zbudujemy w te 2h** — żeby klient miał oczekiwania.

### Czas 0:15 – 0:30: Antigravity setup
- Klient otwiera Antigravity, tworzy workspace.
- Pierwszy prompt: "Sklonuj repo `[URL Twojego repo]` i wytłumacz mi co tam jest".
- Agent czyta, robi Artifact z opisem struktury. Klient widzi że to **nie jest magia**.

### Czas 0:30 – 1:00: Lokalne uruchomienie
- Klient kopiuje `.env.example` na `.env`, wkleja Gemini key.
- Agent uruchamia `pip install -r requirements.txt` w terminalu Antigravity.
- Agent uruchamia `python monitor.py`.
- Klient widzi że folder się zapełnia plikami JSON i obrazkami.
- Klient otwiera `output/dashboard.html` — pusty (pierwszy run).

### Czas 1:00 – 1:30: Drugi run + sztuczna zmiana (wow moment)
- **Backup plan dla braku realnej zmiany:** wracamy do folderu, ręcznie edytujemy plik snapshot (zmieniamy 1 słowo w opisie), uruchamiamy znów.
- Klient widzi alert + dashboard z diff.
- Jeszcze lepiej: ręcznie podmieniamy 1 obrazek w `assets/` na inny (np. lustro), uruchamiamy.
- **Gemini Vision opisuje co się zmieniło** — klient czyta i wpada w zachwyt.

### Czas 1:30 – 2:00: Deploy do chmury + Q&A
- Razem pushujemy do GitHuba klienta.
- Razem dodajemy GitHub Secret z Gemini key.
- Razem włączamy workflow.
- Pokazujemy klientowi gdzie znaleźć: dashboard URL, historię commitów, listę alertów.
- Q&A — odpowiadamy na pytania, pokazujemy jak dodać nową apkę w `config.yaml`.

### Po warsztacie
- Klient zostaje z **działającym produktem w chmurze**.
- Klient ma w głowie **co znaczą każde z 10 narzędzi** które używamy.
- Klient wie że **może sam dodawać apki edytując 1 plik**.

---

## 10. Co odpowiedzieć gdy klient zapyta...

### "Czy to bezpieczne?"
> "Tak. Klucze API mieszkają w GitHub Secrets — to szyfrowany sejf, nikt inny nie ma do niego dostępu. Repozytorium jest prywatne — tylko Ty je widzisz. Skrypt nie loguje się nigdzie pod Twoim hasłem — tylko czyta publiczne dane ze sklepów."

### "Co się stanie jak Apple zmieni API?"
> "Apple od ~15 lat ma to samo API, nie zmieni. Google Play scraper czasem się psuje gdy Google zmieni layout strony — wtedy w Antigravity prosimy agenta o naprawę, zajmuje 15 min. Mogę Ci pokazać proces gdy zaboli."

### "Czy mogę monitorować więcej niż Edge?"
> "Tak — edytujesz plik `config.yaml`, dopisujesz nazwę i ID apki, commitujesz. Workflow przy następnym runie obejmie nową apkę. Możesz mieć 1, 5, 50 apek — tylko więcej apek = więcej minut workflow = potencjalnie limit darmowy."

### "Co to kosztuje miesięcznie?"
> "Przy 1-5 apkach: 0 zł. Wszystkie usługi (GitHub, Gemini, Resend) mają darmowe tiery które wystarczą. Powyżej 20 apek może być potrzebny upgrade GitHub Actions ($4/mies) i ewentualnie Gemini paid (grosze)."

### "Czy moje screeny / dane są bezpieczne?"
> "Nie ściągamy żadnych Twoich danych — tylko publiczne strony sklepów. Te same dane widzi każdy odwiedzający App Store."

### "Mogę dać dostęp marketingowi do dashboardu?"
> "Tak — wystarczy podać im URL GitHub Pages. Lub dodać ich konta jako collaborators w GitHub repo (Settings → Collaborators)."

### "A jak chcę zmienić częstotliwość z 6h na 1h?"
> "Edytujesz 1 linijkę w pliku `.github/workflows/monitor.yml` — zmieniasz `0 */6 * * *` na `0 * * * *`. Commit. Działa."

---

## 11. Twoja ściąga (cheat sheet)

### Komendy które będziesz wpisywał w terminalu Antigravity

```bash
# Setup raz
git clone https://github.com/twój-user/edge-listing-monitor.git
cd edge-listing-monitor
python -m venv venv
source venv/bin/activate    # macOS
pip install -r requirements.txt
cp .env.example .env
# (otwierasz .env i wklejasz klucze)

# Codzienne uruchomienie
source venv/bin/activate
python monitor.py
open output/dashboard.html

# Wrzucenie zmian na GitHuba
git add .
git commit -m "Opis zmiany"
git push

# Pobranie najnowszych zmian z GitHuba (jeśli ktoś inny coś popchnął)
git pull
```

### Antigravity prompty które będą Ci potrzebne

```
# Eksploracja
"Wyjaśnij mi strukturę tego projektu. Co robi monitor.py?"

# Uruchomienie
"Uruchom monitor.py i pokaż mi output. Jeśli są błędy, napraw je."

# Modyfikacja
"Dodaj do config.yaml apkę Google Chrome — bundle_id 'com.google.chrome.ios' dla iOS, package_name 'com.android.chrome' dla Android."

# Debug
"Skrypt rzuca błąd '[treść błędu]'. Sprawdź co poszło nie tak i napraw."

# Deploy
"Skonfiguruj wszystko żeby ten projekt chodził w GitHub Actions co 6h. Wyjaśnij mi gdzie wkleić sekrety."
```

### Gdy coś się sypie

1. **Najpierw uruchom skrypt i przeczytaj błąd.** 80% błędów mówi co jest nie tak.
2. **Skopiuj cały błąd do Antigravity** i powiedz "uruchom, dostaję ten błąd, napraw".
3. **Sprawdź `.env`** — najczęstsze błędy to brak klucza Gemini lub literówka.
4. **Sprawdź czy `pip install -r requirements.txt` przeszło bez błędów.** Czasem warto zrobić `pip install --upgrade -r requirements.txt`.
5. **Ostateczność:** usuń folder `venv/`, stwórz od nowa.

---

## 12. Czego NIE mów klientowi (żeby go nie zniechęcić)

- "Google Play scraper się psuje co 2-3 miesiące i trzeba go ręcznie naprawiać." → Powiedz: "Czasami biblioteki się aktualizują i wtedy w Antigravity prosimy agenta o najnowszą wersję — 5 minut roboty."
- "Gemini czasem halucynuje." → Powiedz: "AI bywa kreatywne — jeśli zobaczysz dziwny opis, zawsze masz oryginalny obrazek do podglądu."
- "Apple może w teorii kiedyś zamknąć darmowe API." → To prawda dla każdego API. Nie warto straszyć.

---

## 13. Materiały do dorzucenia klientowi po warsztacie

Po warsztacie wyślij klientowi:
1. **README.md** projektu (już masz w repo).
2. **Link do dashboardu** (GitHub Pages URL).
3. **Krótki email** z 3 punktami: "co dostałeś, gdzie to mieszka, co możesz sam zrobić".
4. **Zaproszenie do GitHuba** jako collaborator (jeśli chce widzieć kod).

---

## 14. Twoja własna ścieżka nauki (1h tygodniowo)

Nie musisz uczyć się Pythona ani Gita do tego projektu. Ale jeśli chcesz **świadomie prowadzić więcej takich projektów**, polecam w tej kolejności:

1. **Tydzień 1:** [GitHub Skills](https://skills.github.com/) — interaktywne kursy na github. Dosłownie klikasz i robisz.
2. **Tydzień 2:** [Python Crash Course](https://realpython.com/python-basics/) — 30 min/dzień, do podstaw.
3. **Tydzień 3:** Bawienie się Antigravity na własnym projekcie (np. "automatycznie zapisuj mi linki z dzisiejszych wiadomości do Notion").
4. **Tydzień 4:** Deploy czegoś na Vercel (np. portfolio static page) — żeby zrozumieć hosting.

Po 4 tygodniach jesteś znacznie bardziej świadomym konsumentem tych narzędzi — wystarczy żeby świadomie prowadzić klientów.

---

## 15. Twoja roadmapa "co dodać klientowi po warsztacie" (do sprzedaży kolejnych godzin)

Po pierwszym warsztacie zostawiasz MVP. Każda z poniższych rzeczy = dodatkowa sesja:

1. **Microsoft Edge release notes** (15 min — fetch z `learn.microsoft.com`, dodatkowe źródło zmian).
2. **Monitoring konkurencji** (15 min — dorzucamy Chrome, Brave, Firefox do `config.yaml`).
3. **Tygodniowy raport email** (30 min — agreguje wszystkie zmiany z tygodnia w jeden mail).
4. **Dashboard na własnej domenie** (15 min — Vercel + custom domain).
5. **In-App Events scraping** (1h — jeśli okaże się że klient potrzebuje).
6. **Slack** (jeśli kiedyś przejdzie z Workspace) (15 min — dodajemy webhook Slack).
7. **Filtrowanie alertów** (30 min — np. "alertuj tylko gdy zmieni się screen, ignoruj zmiany ratingów").
8. **Wersjowanie dashboardu** (30 min — historyczny widok zmian w czasie, kalendarz).

To wszystko możesz wycenić jako dodatkowe godziny doradztwa, ale każde z osobna jest tanie i wartościowe dla klienta.
