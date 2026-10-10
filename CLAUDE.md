# Kolorowe pianino

Strony z piosenkami dla dzieci w formacie książeczki „Naklejasz i grasz”: kolorowe klocki
(kolor = naklejka na klawiszu, szerokość = długość dźwięku) i słowa obok. Wszystkie zasady
formatu są w [ZASADY.md](ZASADY.md). Zdjęcia `*.jpeg` w katalogu głównym to oryginały, na
których te zasady się opierają.

## Nowa piosenka na życzenie

1. Wybierz piosenkę znaną dzieciom. Może to być tekst tradycyjny, z domeny publicznej
   albo współczesny — projekt służy wyłącznie do użytku prywatnego, więc nie trzeba
   ograniczać się do utworów wolnych od praw autorskich.
2. Sprawdź melodię w zapisie nutowym, nie z pamięci. Szukaj zapisu w sieci (np.
   mamalisa.com: na stronie piosenki obrazek z `images/scores/` otwórz w przeglądarce);
   dla współczesnych piosenek korzystaj ze znalezionych transkrypcji i własnego słuchu.
3. Zapisz `piosenki/NN-krotka-nazwa.txt` z kolejnym numerem (format: ZASADY.md §6).
   W komentarzu `#` podaj źródło melodii.
4. Uruchom `python generator/kolorowe_pianino.py --sprawdz piosenki/NN-krotka-nazwa.txt`.
   Wynik musi być bez uwag, w zakresie C–e i z jak najmniejszą liczbą czarnych klawiszy
   (skorzystaj z podpowiedzi transpozycji). Gdy melodia nie mieści się w C–e, użyj dodatkowych
   naklejek A, H, (w paski) i f g a h (w kropki) zamiast przenosić frazy o oktawę (ZASADY.md §1, §4). Sprawdź też część „słowa do nut”: każda sylaba ma
   trafić na swoją nutę. Sylabę śpiewaną na kilku nutach oznacz w słowach `_` (ZASADY.md §6).
   Ustaw `tempo:` jak przy śpiewie i zostaw oddech na końcu wersów: długą nutę albo pauzę `-`
   (ZASADY.md §4, punkty 6–7). Bez tego następny wers wchodzi od razu.
5. Uruchom `python generator/kolorowe_pianino.py --pdf`. Przebuduje to HTML wszystkich
   piosenek i PDF książeczki (`strony/pdf/ksiazeczka.pdf`; pojedyncze piosenki nie mają PDF-ów).
6. Obejrzyj wynik przed oddaniem, na zrzucie ekranu z Edge w trybie headless:
   `msedge --headless=new --hide-scrollbars --window-size=1752,700 --screenshot=<plik.png> file:///C:/Code/kolorowe-pianino/strony/NN-krotka-nazwa.html`
   (w PowerShell przez `Start-Process ... -Wait`).

W kroku 6 sprawdź też, czy melodia wypełnia szerokość strony; jeśli nie, połącz krótkie rzędy
(`--sprawdz` ostrzega). Odtwarzanie ▶ sprawdzisz przez `.claude/launch.json` (serwer „strony”)
w przeglądarce w aplikacji. Po każdej zmianie odtwarzacza (PLAY_JS) uruchom
`node testy/synchronizacja.mjs`: mierzy w Edge/Chrome w tle, czy podświetlenie klocka zgadza się
z dźwiękiem, m.in. przy opóźnionym starcie dźwięku, słuchawkach Bluetooth i szybkim klikaniu.
Sprawdza też, czy z klockiem zapala się właściwa sylaba słów i czy tryb 🔇 („graj sam”) gra bez
dźwięku, z odliczaniem i w tempie.

## Import z innych książeczek (`import/`)

Zdjęcia w `import/` pochodzą z książeczki z numerowanymi klawiszami (4 = środkowe C, opis
w ZASADY.md §6.1). Są tam współczesne piosenki z podanymi kompozytorami — przepisuj ich słowa
i melodie na użytek domowy według `import/SZABLON-numerki.txt`. Dla piosenek z zapisem
numerkowym (`zapis: numery`) działa on tak samo jak literowy.

Katalogu `strony/` nie edytuj ręcznie, bo to wynik generatora. Zmiany wyglądu wprowadzaj
w `generator/kolorowe_pianino.py`.

## Publikacja

Push na `main` ze zmianami w `strony/` publikuje ten katalog na GitHub Pages
(`.github/workflows/pages.yml`): https://mswietlicki.github.io/kolorowe-pianino/
