# Kolorowe pianino – zasady tworzenia stron z piosenkami

Ten dokument opisuje format stron z książeczki „Naklejasz i grasz”, w której dziecko gra na
pianinie (keyboardzie, dzwonkach) bez znajomości nut: zamiast pięciolinii są **kolorowe klocki**
w kolorach naklejek na klawiszach, a **szerokość klocka mówi, jak długo trzymać klawisz**.

Zasady odczytałem ze zdjęć w tym katalogu:

| Zdjęcie | Co pokazuje |
|---|---|
| `instrukcja.jpeg` | strona „Naklejasz i grasz”: jak znaleźć środkowe C i jak nakleić naklejki |
| `keyboard.jpeg` | zabawkowy keyboard (37 klawiszy) z naklejonymi naklejkami |
| `lulajże jezuniu.jpeg`, `anioł pasterzom mówił.jpeg`, `gdy się chrystus rodzi.jpeg`, `mizerna cicha.jpeg` | cztery rozkładówki z piosenkami |

Na końcu (punkty 6–7) opisuję generator, który z prostego pliku tekstowego robi nowe rozkładówki
w tym samym stylu, gotowe do druku.

---

## 1. Naklejki i klawisze

Naklejki przykleja się na **10 kolejnych białych klawiszy, zaczynając od środkowego C**:

| Nuta | Naklejka | Kolor w generatorze |
|---|---|---|
| **C** (środkowe C) | czerwona | `#E3262B` |
| **D** | niebieska | `#2A6BC1` |
| **E** | różowa (magenta) | `#E4357F` |
| **F** | zielona | `#5DAE35` |
| **G** | pomarańczowa | `#F07B26` |
| **A** | fioletowa | `#65297B` |
| **H** | żółta | `#F5D23A` |
| **c** | czerwona **w białe kropki** | jak C + kropki |
| **d** | niebieska **w białe kropki** | jak D + kropki |
| **e** | różowa **w białe kropki** | jak E + kropki |

- Nazwy są polskie: **H**, a nie B. Wielkie litery to oktawa od środkowego C, małe (c, d, e) –
  następna oktawa. Kolory się powtarzają, a **kropki oznaczają „te same kolory, ale wyżej”**.
- **Środkowe C** to biały klawisz tuż na lewo od grupy dwóch czarnych klawiszy, mniej więcej
  w połowie klawiatury. Na zabawkowych keyboardach leży zwykle bardziej po lewej. Na keyboardzie
  ze zdjęcia (pierwszy klawisz to F) czerwona naklejka jest na 5. białym klawiszu.
- **Dostępny zakres to tylko C–e**: 10 białych klawiszy i 7 czarnych między nimi
  (C#, D#, F#, G#, A#, c#, d#). Klawisze bez naklejek nie są używane.
- Czarne klawisze nie mają naklejek. Zapisuje się je kolorem **białego klawisza po lewej**
  z doklejoną czarną belką (punkt 3).

## 2. Rozkładówka: dwie strony na piosenkę

Każda piosenka zajmuje dwie sąsiednie strony (książeczka jest w poziomie, ok. A5).

### Lewa strona – słowa

- W lewym górnym rogu **zielona nutka** (♪ albo ♫).
- **Tytuł WIELKIMI LITERAMI**, pogrubiony, bordowy, wyśrodkowany nad tekstem.
- Opcjonalnie pod tytułem mniejszym krojem **autor słów** (np. „Teofil Lenartowicz” przy
  „Mizerna cicha”).
- **Wszystkie zwrotki**, wersy jak w śpiewniku, z odstępem między zwrotkami. Prosty bezszeryfowy
  krój (podobny do Montserrat), ciemnoszary. Krótki tekst mieści się w jednej kolumnie, dłuższy
  w dwóch.
- **Powtarzany refren pisze się w całości tylko raz.** Dalej zostają pierwsze słowa i wielokropek,
  np. „Lulajże, Jezuniu…”.
- **Ilustracja** w delikatnym akwarelowym stylu, związana z treścią (Matka Boża z Dzieciątkiem,
  anioł z trąbką, szopka, stajenka w kole).
- **Legenda symboli**, jeśli prawa strona ich używa:
  - czarny klawisz: klocek z belką „=” mała klawiatura z zaznaczonym tym czarnym klawiszem,
  - **↻ Powtórz**: okrągła strzałka z podpisem.
- **Numer strony** w lewym dolnym rogu, na zielonej „drabince”. Lewe strony mają numery
  parzyste (4, 6, 8, 10…).

### Prawa strona – melodia

- Ta sama zielona nutka i **tytuł WIELKIMI LITERAMI** (ciemnoszary, wyśrodkowany).
- **Melodia jednej zwrotki.** Kolejne zwrotki śpiewa się na tę samą melodię.
- Najczęściej **3–4 rzędy** (spotyka się od 2 do 5). Rzędy są wyrównane do lewej i mają różną
  długość, bo każdy rząd to jedna fraza.
- **Na tej stronie nie ma słów, kresek taktowych, metrum, tempa ani pauz.**

## 3. Zapis melodii: „koraliki na sznurku”

Każdy dźwięk to prostokątny klocek. Klocki są nawleczone na gruby ciemny sznurek i czyta się je
od lewej do prawej, rząd po rzędzie.

| Cecha klocka | Znaczenie |
|---|---|
| **kolor** | który klawisz nacisnąć (kolor naklejki) |
| **białe kropki** | klawisz z kropkami, czyli wyższa oktawa (c, d, e) |
| **czarna belka** wystająca nad prawy górny róg | czarny klawisz **na prawo** od białego klawisza w tym kolorze (krzyżyk), np. czerwony w kropki + belka = c# |
| **szerokość** | jak długo trzymać klawisz |
| **położenie w pionie** | wyższy dźwięk leży wyżej; sznurek pokazuje, czy melodia idzie w górę, czy w dół |
| **↻ na końcu rzędu** | zagraj ten rząd jeszcze raz (z następnym wersem) |

### 3.1 Szerokość = długość dźwięku

Szerokość jest **proporcjonalna do długości dźwięku, razem z przerwą między klockami**, więc
czas płynie równo wzdłuż sznurka: półnuta jest tak szeroka jak dwie ćwierćnuty razem z przerwą
między nimi.

| Wartość | Długość (ćwierćnuta = 1) | Wygląd | Przykład z książeczki |
|---|---|---|---|
| ósemka | ½ | wąski pasek | „Lulajże”, rząd 1: wąskie zielony i różowy (F E) |
| ćwierćnuta | 1 | podstawowy klocek, stojący prostokąt (szerokość ≈ 0,63 wysokości) | większość klocków |
| ćwierćnuta z kropką | 1½ | trochę szerszy | „Lulajże”, rząd 2: szerszy pomarańczowy (G.) |
| półnuta | 2 | szeroki | „Lulajże”, koniec rzędu 1: szeroki pomarańczowy |
| półnuta z kropką | 3 | bardzo szeroki | „Mizerna cicha”, rząd 2: dwa długie różowe w kropki |
| cała nuta | 4 | najszerszy | „Gdy się Chrystus rodzi”: ostatnie czerwone C |

- Wszystkie klocki mają **tę samą wysokość**. Zmienia się tylko szerokość.
- Kropki tworzą siatkę: **3 rzędy, po 2 kolumny na każdą ćwierćnutę** (ósemka 1 kolumna,
  półnuta 4, półnuta z kropką 6).
- Książeczka nie używa szesnastek ani triol. Rytm trzeba uprościć do wartości z tabeli.

### 3.2 Wysokość w pionie

- Każdy biały klawisz wyżej podnosi klocek o ok. **1/7 jego wysokości**. Czarny klawisz leży
  w połowie między sąsiadami.
- Każdy rząd ma własną linię odniesienia: rysuje się go w swoim pasie strony i nie porównuje
  wysokości z innymi rzędami.

### 3.3 Sznurek

- Gruby (ok. ¼ wysokości klocka), prawie czarny, przechodzi **przez środki klocków**. Między
  sąsiednimi klockami biegnie prosty odcinek, skośny, gdy zmienia się wysokość.
- Na początku i na końcu rzędu wystaje za klocek i kończy się zaokrągloną kropką.
- Między klockami jest mała przerwa, w której widać sznurek. Dzięki temu dwa takie same
  dźwięki pod rząd to dwa osobne klocki, czyli dwa naciśnięcia.

### 3.4 Powtórka ↻

Jeśli rząd ma zabrzmieć **dwa razy pod rząd**, rysuje się go raz i stawia na końcu okrągłą
strzałkę. Przykład: w „Gdy się Chrystus rodzi” pierwszy rząd gra się dla „Gdy się Chrystus
rodzi…” i drugi raz dla „Ciemna noc w jasności…”. Jeśli powtórzenie **nie następuje od razu**,
rząd rysuje się ponownie (w „Lulajże” rzędy 2 i 4 są takie same i oba są narysowane).

### 3.5 Przykłady odczytu

**„Lulajże, Jezuniu”, rząd 1** („Lulajże, Jezuniu, moja Perełko”, 3/4, przeniesione z F-dur do C):

```
różowy różowy różowy | pomarańczowy, wąski zielony, wąski różowy, zielony | niebieski niebieski zielony | fioletowy, SZEROKI pomarańczowy
  E      E      E    |      G             F8           E8          F    |    D        D        F      |    A            G2
```

**„Anioł pasterzom mówił”, rząd 1**: `G G A A H A G` i skok w górę do `d d e e d c# d`.
c# to czerwony w kropki z czarną belką. Legenda na lewej stronie pokazuje, który to klawisz.

## 4. Jak dobierać i przygotowywać nowe piosenki

1. **Piosenki znane dzieciom**: ludowe, zabawy w kółku, kołysanki, kolędy, piosenki urodzinowe.
   Najlepiej tradycyjne albo takie, których autor słów zmarł ponad 70 lat temu (domena
   publiczna). Nie przepisuj tekstów współczesnych piosenek chronionych prawem autorskim.
2. **Melodię sprawdź w zapisie nutowym, nie z pamięci.** Dobre źródła:
   [Mama Lisa's World](https://www.mamalisa.com/?lang=Polish&t=el) (polskie piosenki dziecięce
   z nutami), polska Wikipedia (kolędy mają zapis w kodzie LilyPond, który da się przeczytać jako
   tekst przez `action=raw`) i [Wolne Lektury](https://wolnelektury.pl) (teksty kolęd i pieśni
   w domenie publicznej).
3. **Zakres C–e.** Melodia nie może mieć większej rozpiętości niż decyma. W razie potrzeby
   przenieś ją do innej tonacji tak, żeby **było jak najmniej czarnych klawiszy**: C-dur,
   G-dur bez dźwięku F#, F-dur bez B, a-moll. Książeczka też transponuje: „Lulajże” jest
   z F-dur przeniesione do C. Generator podpowiada transpozycje (`--sprawdz`).
4. **Czarne klawisze tylko wtedy, gdy bez nich melodia brzmi źle** (c# w „Anioł pasterzom”,
   gis w „Sto lat”). Każdy użyty czarny klawisz dostaje legendę na lewej stronie.
5. **Upraszczaj rytm**: bez szesnastek i triol. Pauzę zamień na dłuższą poprzednią nutę
   (książeczka nie ma pauz). Generator umie narysować pauzę jako odcinek samego sznurka,
   ale tego elementu nie ma w oryginale, więc używaj go oszczędnie.
6. **Rząd = fraza / wers.** Najwyżej ok. 16 ćwierćnut w rzędzie, 2–5 rzędów (najlepiej 3–4).
   Rzędy łam tam, gdzie kończy się wers tekstu. Generator powiększa klocki, aż najdłuższy rząd
   wypełni szerokość strony, i centruje całą melodię. Wiele krótkich rzędów (np. 4 × 8 ćwierćnut)
   nie wypełni jednak strony, bo wcześniej skończy się wysokość. Wtedy połącz je w dłuższe
   (2 × 16), tak jak w „Sto lat” i „Panie Janie”. `--sprawdz` ostrzega, gdy melodia zajmuje
   mniej niż 70% szerokości.
7. **Powtórka ↻** dla rzędu granego drugi raz od razu. Takie samo powtórzenie w innym
   miejscu rysuj ponownie.
8. **Słowa**: wszystkie zwrotki, poprawna interpunkcja i polskie znaki. Wskazówki do zabawy
   (np. „śpiewamy kanonem”, odliczanie godzin w „Starym niedźwiedziu”) dodaj kursywą pod tekstem.
9. **Ilustracja**: pogodna, związana z treścią (kotek, niedźwiedź, gwiazdka, tort).

## 5. Piosenki przygotowane w tym katalogu

| Plik | Piosenka | Zakres / czarne klawisze | Źródło melodii |
|---|---|---|---|
| `piosenki/01-wlazl-kotek.txt` | Wlazł kotek na płotek | C–G, 0 | zapis nutowy Mama Lisa |
| `piosenki/02-panie-janie.txt` | Panie Janie | D–e, 0 (przeniesione do G) | znana melodia „Frère Jacques” |
| `piosenki/03-stary-niedzwiedz.txt` | Stary niedźwiedź | C–d, 0 | zapis nutowy Mama Lisa |
| `piosenki/04-mrugaj-gwiazdko.txt` | Mrugaj, mrugaj, gwiazdko ma | C–A, 0 (z powtórką ↻) | znana melodia „Twinkle, Twinkle” |
| `piosenki/05-sto-lat.txt` | Sto lat | D–c, 1 (gis) | zapis nutowy Mama Lisa |
| `piosenki/06-mam-chusteczke.txt` | Mam chusteczkę haftowaną | C–A, 0 | nuty literowe z dwóch źródeł; rytm dobrany do sylab |
| `piosenki/07-czarny-baranie.txt` | Gdzieżeś ty bywał, czarny baranie? | C–c, 0 (przeniesione o −2) | zapis nutowy Mama Lisa (J. Roger) |
| `piosenki/08-krakowiaczek.txt` | Krakowiaczek jeden | C#–d, 8 (F#, C#) – trudniejsza | zapis nutowy Mama Lisa (Z. Gloger), rytm uproszczony |
| `piosenki/09-dzisiaj-w-betlejem.txt` | Dzisiaj w Betlejem | D–e, 0 | zapis LilyPond w Wikipedii |
| `piosenki/10-w-zlobie-lezy.txt` | W żłobie leży | D–e, 0 | zapis LilyPond w Wikipedii; tekst z Wolnych Lektur |

## 6. Format pliku piosenki (dla generatora)

Każda piosenka to jeden plik UTF-8 w katalogu `piosenki/`. Kolejność w książeczce wyznacza
nazwa pliku: `NN-krotka-nazwa.txt`.

```text
# Linie zaczynające się od # to komentarze (np. źródło melodii); „  # …” na końcu linii też.
tytuł: Wlazł kotek na płotek
podtytuł: piosenka ludowa         # opcjonalnie: autor słów / „melodia ludowa”
metrum: 3/4                       # opcjonalnie: generator sprawdzi długości taktów
ilustracja: 🐱 🌼                  # 1–3 emoji (pierwsze duże) albo ścieżka do obrazka .png/.jpg/.svg
kolor: pomarańczowy               # opcjonalnie: kolor akwarelowej plamy pod ilustracją
transpozycja: 0                   # opcjonalnie: przesunięcie melodii w półtonach (+2, -5…)
tempo: 120                        # opcjonalnie: ćwierćnut na minutę przy odtwarzaniu ▶ (domyślnie 100)
zapis: litery                     # opcjonalnie: „litery” (domyślnie) albo „numery” – patrz punkt 6.1

[słowa]
Wlazł kotek na płotek
i mruga.
Ładna to piosenka,
niedługa.

Nie długa, nie krótka,
lecz w sam raz.
> Linia zaczynająca się od „>” to uwaga (kursywa, mniejsza).

[melodia]
G E E | F D D | C8 E8 G2 |
G E E | F D D | C8 E8 C2 |
```

**Sekcja `[słowa]`**: pusta linia oddziela zwrotki.

**Sekcja `[melodia]`**: **jedna linia = jeden rząd klocków.** Nuty oddzielasz spacjami:

| Zapis | Znaczenie |
|---|---|
| `C D E F G A H` | klawisze od środkowego C (bez kropek) |
| `c d e` | klawisze z kropkami |
| `C#` `D#` `F#` `G#` `A#` `c#` `d#` | czarne klawisze (można też pisać bemolami: `Eb`, `B` = `A#`…) |
| brak liczby / `4` | ćwierćnuta (np. `G` albo `G4`) |
| `8` | ósemka (`E8`) |
| `4.` | ćwierćnuta z kropką (`G4.`) |
| `2`, `2.` | półnuta, półnuta z kropką |
| `1` | cała nuta |
| `-` `-8` `-2`… | pauza (odcinek samego sznurka; lepiej wydłużyć poprzednią nutę) |
| `\|` | kreska taktowa: nie jest rysowana, służy do kontroli metrum |
| `↻` albo `:\|` na końcu linii | znak powtórki rzędu |
| `G,` `A,` `H,` / `f` `g` `a` / `c'` | dźwięki poza naklejkami. Dozwolone tylko razem z `transpozycja:`, która przesunie je w zakres C–e |

Tę samą konwencję długości (`C8`, `G2.`) i nazw (`H`, małe litery = oktawa wyżej) stosuje
`--sprawdz`, który wypisuje melodię słowami („pomarańczowy [szeroki]…”). Tak łatwo porównać
wynik z zapisem nutowym.

### 6.1 Zapis numerkowy (książeczki z ponumerowanymi klawiszami)

Niektóre książeczki (np. zdjęcia w `import/`) pokazują nuty jako kolorowe owale **z numerem
klawisza** na pięciolinii i nie podają długości. Z pliku z `zapis: numery` generator przyjmuje
takie numery wprost:

| Numer | 1 | 2 | 3 | **4** | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Klawisz | G, | A, | H, | **C** (środkowe, czerwona) | D | E | F | G | A | H | c | d | e |

- Długość dopisuje się po dwukropku, bez dwukropka jest ćwierćnuta: `9:8` (ósemka), `9`, `9:4.`,
  `9:2`, `9:2.`, `9:1`.
- Czarny klawisz to `7#`. Czarny owal w takiej książeczce to najpewniej krzyżyk, ale sprawdź uchem.
- Numery 1–3 leżą poniżej naklejek, więc trzeba je przenieść polem `transpozycja:`.
- **Rytm trzeba dopisać samodzielnie.** Policz nuty w takcie (4 nuty w takcie na 4 to
  ćwierćnuty, 8 to ósemki, 2 to półnuty). Nuty narysowane ciasno, parami, to zwykle ósemki,
  a ostatnia nuta wersu jest zwykle długa. Potem odsłuchaj przyciskiem ▶ i poprawiaj, aż
  zgadza się ze śpiewem.
- Gotowy szablon z instrukcją i przykładem: [`import/SZABLON-numerki.txt`](import/SZABLON-numerki.txt).
- Przepisując piosenki z kupionej książeczki, pamiętaj, że współczesne piosenki są chronione
  prawem autorskim. Przepisane w ten sposób strony nadają się do użytku domowego, nie do
  publikowania ani rozdawania.

## 7. Generowanie i druk

Wymagany jest tylko Python 3.9+. PDF-y robi zainstalowany Edge albo Chrome.

```bash
python generator/kolorowe_pianino.py
```

Buduje wszystkie piosenki do katalogu `strony/`:

- `strony/NN-nazwa.html`: rozkładówka jednej piosenki,
- `strony/ksiazeczka.html`: strona „Jak grać?” i wszystkie piosenki po kolei,
- `strony/jak-grac.html`: legenda dla dziecka i rodzica (naklejki, kropki, szerokość, belka, ↻),
- `strony/index.html`: spis piosenek.

```bash
python generator/kolorowe_pianino.py --sprawdz piosenki/05-sto-lat.txt
```

Tylko sprawdza piosenkę: zakres, czarne klawisze, takty, możliwe transpozycje i opis melodii
słowami.

```bash
python generator/kolorowe_pianino.py --pdf
```

Dodatkowo tworzy PDF-y w `strony/pdf/`.

**Odtwarzanie:** na stronie z melodią jest zielony przycisk **▶** (albo spacja na stronie
pojedynczej piosenki). Gra melodię w tempie z pola `tempo:`, a grany klocek podskakuje, więc
dziecko widzi, gdzie jest. Rząd z ↻ gra dwa razy. Przycisk 🐢 zwalnia odtwarzanie do ok. 60%.
Przyciski nie drukują się. Do podglądu stron w przeglądarce wystarczy otworzyć plik HTML, bez
serwera.

**Druk:** każda strona trafia na osobną kartkę **A4 w poziomie**, więc klocki są duże i łatwe
do czytania. Z przeglądarki: przycisk „Drukuj”, orientacja pozioma, marginesy „brak”,
włączona grafika tła. Dla całej książeczki otwórz `ksiazeczka.html` albo `pdf/ksiazeczka.pdf`.

## 8. Lista kontrolna nowej strony

- [ ] Piosenka znana dzieciom, tekst tradycyjny albo z domeny publicznej
- [ ] Melodia sprawdzona z zapisem nutowym, rytm uproszczony (bez szesnastek, triol, pauz)
- [ ] Wszystkie dźwięki w zakresie C–e, jak najmniej czarnych klawiszy
- [ ] Rzędy = frazy, 2–5 rzędów, najwyżej ok. 16 ćwierćnut w rzędzie
- [ ] Bezpośrednie powtórzenie rzędu zapisane znakiem ↻
- [ ] Wszystkie zwrotki na lewej stronie, refren skrócony po pierwszym razie
- [ ] Legenda dla każdego użytego symbolu (czarny klawisz, ↻)
- [ ] Melodia wypełnia szerokość strony (bez ostrzeżenia `--sprawdz`)
- [ ] Melodia odsłuchana przyciskiem ▶ i zgodna ze śpiewem
- [ ] `--sprawdz` bez uwag; strona obejrzana w przeglądarce przed drukiem
