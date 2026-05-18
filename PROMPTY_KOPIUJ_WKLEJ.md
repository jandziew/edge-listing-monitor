# Prompty — kopiuj i wklejaj

> Biblioteka gotowych promptów do użycia w Gemini i Antigravity. Otwórz na drugim monitorze podczas budowy — bierzesz odpowiedni i wklejasz, nie wymyślasz od zera.
>
> **Konwencja:** `[TEKST W KWADRATOWYCH NAWIASACH]` to miejsca do uzupełnienia własną treścią.

---

## A. GEMINI — sesja od pomysłu do PRD

### A1. Start sesji z Gemini (zawsze pierwszy)

```
Pomóż mi zaprojektować małe narzędzie biznesowe, które chcę zbudować używając
agentowego IDE (Antigravity). Jestem nietechnicznym pracownikiem [SWOJA ROLA, np. marketingu].

Pomysł w jednym zdaniu: chciałbym codziennie wiedzieć, czy [TWÓJ POMYSŁ — np. "Microsoft
zmienił coś w opisie aplikacji Edge w App Store"].

Twoja rola: zadaj mi 5-10 pytań które pomogą doprecyzować zakres tego MVP, tak żebym
mógł potem wkleić wynik jako prompt do Antigravity. Zadawaj pytania pojedynczo,
czekaj na moją odpowiedź, dopiero potem następne. Nie pisz jeszcze żadnego kodu —
najpierw chcę mieć jasny opis zakresu.
```

---

### A2. Gdy Gemini zaczyna rozdmuchiwać zakres

```
Stop — zaczynasz proponować za dużo. Skupmy się tylko na minimalnym MVP które
realnie zadziała w ciągu jednej sesji 2-3h budowy. Wyrzucamy:
[lista featurów które chcesz wyciąć]

Wróćmy do pytań ale tylko o rzeczy które są w tym minimalnym scope.
```

---

### A3. Gdy chcesz podpowiedź technologiczną

```
Polecasz Python czy Node.js dla tego projektu? Pamiętaj że ja jestem nietechniczny,
więc kryterium jest „czytelność kodu" i „łatwość gdy coś trzeba naprawić ręcznie",
nie „performance". Wybierz jedną opcję i krótko uzasadnij.
```

---

### A4. Finalizacja — wygeneruj PRD (po 10-15 min rozmowy)

```
OK, mamy wystarczająco info. Napisz mi teraz PRD (Product Requirements Document)
w Markdownie, ze strukturą:

1. Cel (1 akapit)
2. Użytkownik i scenariusz użycia (1 akapit)
3. Funkcjonalności w MVP (lista 3-7 punktów, każdy max 1 zdanie)
4. Co jest poza zakresem MVP (lista, żeby agent nie próbował tego budować)
5. Źródła danych i ich format (lista konkretnych URL/API)
6. Sposób alertowania (kanały, format wiadomości)
7. Stack technologiczny (zaproponuj: Python, najprostsze biblioteki)
8. Gdzie hostować (Cloudflare Pages + Access jako default)
9. Bezpieczeństwo (jakie klucze API potrzebne, gdzie je trzymać — .env, .gitignore)
10. Plan na pierwsze 2 godziny pracy w Antigravity (lista konkretnych zadań do agenta,
    w kolejności od najprostszego)

Pisz po polsku, prosto, bez żargonu engineerowego. Wynik wkleję jako pierwszy prompt
do Antigravity, więc ma być self-contained i precyzyjny.
```

---

### A5. Sanity check PRD (po wygenerowaniu)

```
Krytyczny review tego PRD. Powiedz mi:
- Czy jest coś nierealistycznego dla osoby nietechnicznej w 2h?
- Czy zakres MVP jest naprawdę minimalny? Co byś jeszcze wyciął?
- Czy są ukryte założenia o moim środowisku (jakie mam konta, dostępy)?
- Jakie są największe ryzyka że to nie zadziała za pierwszym razem?

Nie przepisuj PRD — tylko krytykuj.
```

---

## B. ANTIGRAVITY — sesja od PRD do działającego MVP

### B1. Pierwszy prompt — wbij PRD

```
Cześć. Jestem nietechnicznym użytkownikiem ([SWOJA ROLA]). Chcę zbudować z Twoją pomocą
mały tool według poniższego PRD. Twoja rola:

1. Najpierw przeczytaj PRD i powiedz mi po polsku co dokładnie zamierzasz zrobić,
   w jakich krokach (lista 5-10 punktów). NIE PISZ jeszcze kodu.
2. Gdy ja zaakceptuję plan, zaczniesz od pierwszego kroku.
3. Po każdym ukończonym kroku zatrzymaj się, pokaż mi co zrobiłeś, poczekaj na moją
   akceptację zanim ruszysz dalej.
4. Pisz komentarze w kodzie po polsku — chcę móc kiedyś sam to czytać.
5. Jeśli czegoś nie jesteś pewien — pytaj zamiast zgadywać.
6. Trzymaj się tego co jest w PRD. Jeśli chcesz dodać coś co nie jest w PRD —
   najpierw zapytaj „dorzucam X, OK?".

Oto PRD:

---

[TU WKLEJASZ CAŁY PRD WYGENEROWANY PRZEZ GEMINI]
```

---

### B2. Zatrzymaj agenta gdy od razu zaczyna kodować

```
Stop. Najpierw chcę plan, dopiero potem kod. Wróć i pokaż mi listę 5-10 kroków
w kolejności, ze szacunkiem czasu na każdy. Po mojej akceptacji zaczniesz pierwszy.
```

---

### B3. Akceptacja planu (zwykle pierwszy „klik")

```
Plan OK. Zacznij krok 1. Po skończeniu pokaż mi:
- jakie pliki stworzyłeś / zmodyfikowałeś
- co dokładnie robi nowy kod (2-3 zdania po polsku)
- jak mogę to przetestować lokalnie
```

---

### B4. Po pierwszym kroku — weryfikacja

```
Pokaż mi w swoich słowach, co masz teraz w projekcie. Wymień każdy plik i jednym
zdaniem opisz jego rolę. Po polsku.
```

---

### B5. Dodawanie kolejnej funkcji (mała, focused zmiana)

```
Chcę dodać następujący feature: [KONKRETNY OPIS FEATURU, np. "alert na Telegram gdy
wykryjemy zmianę wersji aplikacji"].

Wymagania:
- Zmień tylko niezbędne pliki, nie refaktoruj reszty
- Po implementacji pokaż mi diff (tylko zmienione linie)
- Wytłumacz mi po polsku co dodałeś, w 3-4 zdaniach
- Jeśli to wymaga nowych kluczy API / sekretów — powiedz mi gdzie je wziąć i gdzie wkleić

Nie zaczynaj kodować dopóki nie potwierdzę zakresu.
```

---

### B6. Gdy skrypt się sypie

```
Uruchomiłem `[komenda którą uruchomiłeś, np. python monitor.py]` i dostałem ten błąd:

```
[TU WKLEJASZ PEŁEN STACK TRACE Z TERMINALA, OD POCZĄTKU DO KOŃCA]
```

Co robiłem przed: [krótko opisz kontekst, np. "po dodaniu feature X"].
Spodziewałem się: [co miało się stać].
Faktycznie się stało: [co widzisz].

Zdiagnozuj co poszło nie tak. Najpierw wytłumacz mi po polsku problem (2-3 zdania),
dopiero potem napraw.
```

---

### B7. Gdy nie rozumiesz kodu który agent napisał

```
Wytłumacz mi po polsku, jakbyś tłumaczył 10-letniemu dziecku, co robi ten kawałek kodu:

```
[WKLEJASZ KOD KTÓRY CIĘ MARTWI]
```

Po wyjaśnieniu powiedz: czy to standardowe rozwiązanie, czy zrobiłeś coś nietypowego?
Jeśli nietypowe — czemu?
```

---

### B8. Gdy agent kombinuje za bardzo

```
To rozwiązanie wydaje mi się przekombinowane jak na MVP. Zaproponuj prostsze, nawet
jeśli będzie miało mniej featureów lub mniej elegancko obsługiwało skrajne przypadki.

Pamiętaj: to ma być działający MVP które ja nietechniczny będę umiał czytać i modyfikować,
nie production-grade aplikacja.

Wymień 2-3 prostsze podejścia i wytłumacz trade-offy, ale jeszcze nic nie kodu.
```

---

### B9. Przed pierwszym commitem do GitHub

```
Zanim cokolwiek commitujemy do GitHuba, sprawdź:
1. Czy istnieje plik `.gitignore` i czy zawiera `.env`, `*.key`, `secrets/`
2. Czy w żadnym pliku w repo nie ma zahardkodowanych kluczy API ani haseł
   (przeskanuj wszystkie pliki, szczególnie `monitor.py` i `config.yaml`)
3. Czy istnieje `.env.example` (szablon) ale NIE ma `.env` na liście trackowanych plików

Pokaż mi wynik tej kontroli. Dopiero gdy potwierdzimy bezpieczeństwo, zrobimy commit.
```

---

### B10. Konfiguracja GitHub Actions (cron)

```
Skonfiguruj GitHub Actions tak, żeby:
1. Uruchamiał `[TWÓJ GŁÓWNY SKRYPT, np. python monitor.py]` co [CZĘSTOTLIWOŚĆ, np. 6 godzin]
2. Po uruchomieniu commitował wygenerowane pliki (`output/`, `snapshots/`) z powrotem do repo
3. Klucze API brał z GitHub Secrets (nie z .env który jest gitignored)
4. Pozwalał też na ręczne uruchomienie przyciskiem w UI GitHuba (workflow_dispatch)

Po wygenerowaniu .github/workflows/monitor.yml napisz mi instrukcję krok po kroku
(po polsku) jak dodać sekret w GitHub UI — gdzie kliknąć, co wpisać.
```

---

### B11. Setup deployu na Cloudflare Pages

```
Chcę wystawić generowany dashboard (folder `output/`) na Cloudflare Pages, z ochroną
hasłem przez Cloudflare Access (email OTP). Napisz mi:

1. Co dokładnie muszę zrobić w UI Cloudflare (krok po kroku, po polsku, jakbyś
   tłumaczył pierwszy raz w życiu)
2. Czy w naszym projekcie trzeba coś zmienić (np. dodać `wrangler.toml` lub coś
   podobnego — czy wystarczy że Cloudflare sam wykryje że to statyczny site)
3. Jakie pole „Build output directory" wpisać w konfiguracji Cloudflare Pages
4. Jak skonfigurować Cloudflare Access żeby tylko emaile z listy mogły wejść

Nie pisz jeszcze kodu — chcę najpierw zrozumieć plan.
```

---

### B12. Gdy agent zapomniał o czymś z PRD

```
Wracamy do PRD. W sekcji [X] mamy: „[CYTAT Z PRD]".

W obecnej wersji projektu tego nie widzę. Przeczytaj jeszcze raz cały PRD,
wymień mi co już zrobiliśmy i co jeszcze zostało. Po polsku, w formie checklisty.
```

---

## C. KONSERWACJA — gdy projekt już chodzi

### C1. Dodawanie nowej apki / encji do monitora

```
Dodaj do `config.yaml` nową apkę:
- Nazwa: [NAZWA, np. Google Chrome]
- iOS bundle_id: [BUNDLE_ID, np. com.google.chrome.ios]
- Google Play package_name: [PACKAGE_NAME, np. com.android.chrome]
- Kraj: [KOD KRAJU, np. us]

Po dodaniu uruchom `python monitor.py` żeby zrobić pierwszy baseline dla tej apki.
Pokaż mi w outputie czy się zaciągnęła poprawnie.
```

---

### C2. Zmiana częstotliwości cronu

```
Chcę zmienić cron z [STARA CZĘSTOTLIWOŚĆ, np. co 6h] na [NOWA CZĘSTOTLIWOŚĆ, np. co 1h].
Edytuj plik `.github/workflows/monitor.yml`. Po zmianie pokaż mi diff i wytłumacz
co zmienia konkretna składnia crona (po polsku).
```

---

### C3. Dodanie nowego kanału alertów

```
Chcę dodać alerty na [KANAŁ, np. Slack przez Incoming Webhook / Microsoft Teams / Discord].

Wymagania:
- Dodaj funkcję `send_[kanał]_alert(...)` analogicznie do istniejącej `send_telegram_alert`
- Dodaj flagę `alerts.[kanał].enabled` w `config.yaml`
- Dodaj zmienną sekretu w `.env.example` (np. SLACK_WEBHOOK_URL)
- Dodaj sekret do listy w GitHub Actions workflow
- W README sekcji „Alerty" dodaj instrukcję jak ten kanał skonfigurować

Po implementacji wypisz mi co dokładnie muszę zrobić poza kodem (np. gdzie założyć
webhook po stronie [KANAŁ]).
```

---

### C4. Audit security przed udostępnieniem klientowi

```
Zrób mi security review tego projektu zanim wyślę dostęp klientowi:

1. Czy są jakiekolwiek zahardkodowane klucze API / hasła w kodzie? (przeskanuj wszystkie pliki)
2. Czy `.gitignore` ignoruje wszystkie pliki które powinien (.env, *.key, secrets/, dane wrażliwe)?
3. Czy historia gita zawiera commit który kiedyś przypadkowo dodał sekret (sprawdź git log)?
4. Czy README mówi klientowi co MUSI ustawić u siebie a co już jest skonfigurowane?
5. Czy są jakieś endpointy/URLe które ja zostawiłem otwarte (np. testowe webhooks)?

Pisz po polsku, daj mi listę „do zrobienia przed wysłaniem" jeśli coś znajdziesz.
```

---

### C5. Gdy zewnętrzny serwis się zmienił (np. Google Play scraper przestał działać)

```
Skrypt rzuca błąd na fetch [KTÓREJ APKI / Z KTÓREGO ŹRÓDŁA]:

```
[STACK TRACE]
```

Prawdopodobnie [SERWIS, np. Google Play] zmienił HTML strony lub format API.
Twoja robota:

1. Sprawdź obecny stan strony / API (zrób live fetch i pokaż mi przykład response)
2. Porównaj z tym czego nasz kod się spodziewa
3. Zaproponuj minimalną poprawkę
4. Wytłumacz mi po polsku co się zmieniło po stronie [SERWIS] i jak to wpływa na nas

Nie modyfikuj kodu dopóki nie potwierdzę poprawki.
```

---

## D. DEBUG / „NIE WIEM CO SIĘ DZIEJE"

### D1. Generic „coś jest dziwne"

```
Coś jest nie tak a nie wiem co. Zdiagnozuj:

Co próbowałem: [KROK PO KROKU CO ROBIŁEŚ — np. "zmieniłem X w config.yaml,
uruchomiłem skrypt, dashboard nie pokazuje nowej apki"]

Czego się spodziewałem: [CO MIAŁO SIĘ STAĆ]

Co faktycznie widzę: [CO WIDZISZ — error message, dziwny output, pusty dashboard]

Output z terminala (cały, od momentu uruchomienia):
```
[WKLEJASZ TERMINAL OUTPUT]
```

Zawartość plików które mogą być powiązane:
- [NAZWA PLIKU]: [JEGO TREŚĆ ALBO WAŻNY FRAGMENT]

Zadaj mi pytania doprecyzowujące jeśli czegoś brakuje, dopiero potem zacznij naprawiać.
```

---

### D2. Gdy commit się sypie (pre-commit hook fail itp.)

```
Próbuję zrobić `git commit -m "..."` i dostaję ten błąd:

```
[BŁĄD Z TERMINALA]
```

Zdiagnozuj problem i napraw. Jeśli to pre-commit hook się czepia (np. formatter,
linter) — popraw kod żeby przeszedł, NIE proponuj `--no-verify` (omijanie hooków).
```

---

### D3. Gdy `git push` się sypie (konflikty)

```
Próbuję `git push` i dostaję błąd o konflikcie / rejection:

```
[BŁĄD Z TERMINALA]
```

Wytłumacz mi po polsku co się stało (dlaczego git nie chce wypchnąć moich zmian)
i przeprowadź mnie przez rozwiązanie krok po kroku. Pokazuj komendy do wpisania,
ale ja je sam wpisze — Ty nie wpisuj.
```

---

## E. SZYBKIE INTERVENTIONS — gdy agent źle zrozumiał

### E1. „Stop, zatrzymaj się"

```
Stop. Zatrzymaj wszystko, nie kontynuuj. Wytłumacz mi po polsku co właśnie robisz
i czemu, zanim podejmę decyzję czy idziemy dalej.
```

### E2. „Cofnij ostatnią zmianę"

```
Ostatnia zmiana którą zrobiłeś nie działa / nie podoba mi się. Cofnij ją:
przywróć stan z przed Twojej ostatniej edycji [NAZWA PLIKU]. Pokaż mi diff
żebym widział że faktycznie wróciliśmy do poprzedniego stanu.
```

### E3. „To nie to o co prosiłem"

```
Nie o to mi chodziło. Proszony byłeś o [POWTÓRZ ORYGINALNĄ PROŚBĘ].
Zamiast tego zrobiłeś [OPISZ CO ZROBIŁ NIE TAK].

Wytłumacz mi czemu uznałeś że to o co prosiłem to to co zrobiłeś. Możliwe że jak
sformułowałem prośbę było niejasne. Spróbujmy jeszcze raz, ja precyzuję:
[PRECYZJA].
```

### E4. „Nie spiesz się"

```
Spowolnij. Wydaje mi się że robisz za dużo naraz. Wróć do pojedynczego, najmniejszego
sensownego kroku. Po jego skończeniu pokaż mi co zrobiłeś, ja zaakceptuję, dopiero
wtedy idziemy dalej.
```

---

## F. METAPROMPTY — gdy potrzebujesz pomoc samego agenta z promptingiem

### F1. „Pomóż mi sformułować prośbę"

```
Chcę osiągnąć [OPIS CELU], ale nie wiem jak to opisać w prompcie żebyś mnie dobrze
zrozumiał. Pomóż mi sformułować prompt — zadaj mi 3-5 pytań doprecyzowujących i na
ich podstawie zaproponuj mi gotowy prompt który mogę użyć w naszej rozmowie.
```

### F2. „Naucz mnie czegoś przy okazji"

```
Przy okazji zrobienia tego co cię proszę, naucz mnie po polsku co to znaczy
[KONCEPT — np. "co to są dependencies w Pythonie", "co to jest cron", "co to jest API"].
Krótko, 3-5 zdań, jakbyś tłumaczył nietechnicznemu.
```

---

*Trzymaj ten plik otwarty na drugim monitorze podczas pracy. Z biegiem sesji
zaczniesz pamiętać większość promptów na pamięć. Po 10-15 godzinach pracy z Antigravity
ten cheat sheet stanie się zbędny — ale na start oszczędza ogromnie czasu.*
