# Kolorowe pianino

Strony z piosenkami dla dzieci w formacie książeczki „Naklejasz i grasz”: kolorowe klocki
(kolor = naklejka na klawiszu, szerokość = długość dźwięku) i słowa obok. Wszystkie zasady
formatu są w [ZASADY.md](ZASADY.md). Zdjęcia `*.jpeg` w katalogu głównym to oryginały, na
których te zasady się opierają.

## Nowa piosenka na życzenie

1. Wybierz piosenkę znaną dzieciom, z tekstem tradycyjnym albo z domeny publicznej
   (ZASADY.md §4). Jeśli użytkownik chce piosenki z tekstem chronionym prawem autorskim,
   powiedz to i zaproponuj tradycyjną alternatywę.
2. Sprawdź melodię w zapisie nutowym, nie z pamięci (np. mamalisa.com: na stronie piosenki
   obrazek z `images/scores/` otwórz w przeglądarce).
3. Zapisz `piosenki/NN-krotka-nazwa.txt` z kolejnym numerem (format: ZASADY.md §6).
   W komentarzu `#` podaj źródło melodii.
4. Uruchom `python generator/kolorowe_pianino.py --sprawdz piosenki/NN-krotka-nazwa.txt`.
   Wynik musi być bez uwag, w zakresie C–e i z jak najmniejszą liczbą czarnych klawiszy
   (skorzystaj z podpowiedzi transpozycji).
5. Uruchom `python generator/kolorowe_pianino.py --pdf`. Przebuduje to HTML i PDF wszystkich
   piosenek oraz książeczki.
6. Obejrzyj wynik przed oddaniem, na zrzucie ekranu z Edge w trybie headless:
   `msedge --headless=new --hide-scrollbars --window-size=1752,700 --screenshot=<plik.png> file:///C:/Code/kolorowe-pianino/strony/NN-krotka-nazwa.html`
   (w PowerShell przez `Start-Process ... -Wait`).

W kroku 6 sprawdź też, czy melodia wypełnia szerokość strony; jeśli nie, połącz krótkie rzędy
(`--sprawdz` ostrzega). Odtwarzanie ▶ sprawdzisz przez `.claude/launch.json` (serwer „strony”)
w przeglądarce w aplikacji. Po każdej zmianie odtwarzacza (PLAY_JS) uruchom
`node testy/synchronizacja.mjs`: mierzy w Edge/Chrome w tle, czy podświetlenie klocka zgadza się
z dźwiękiem, m.in. przy opóźnionym starcie dźwięku, słuchawkach Bluetooth i szybkim klikaniu.

## Import z innych książeczek (`import/`)

Zdjęcia w `import/` pochodzą z książeczki z numerowanymi klawiszami (4 = środkowe C, opis
w ZASADY.md §6.1). Są tam wyłącznie współczesne piosenki z podanymi kompozytorami, chronione
prawem autorskim. Nie przepisuj ich słów ani melodii. Użytkownik może przepisać je sam do
użytku domowego według `import/SZABLON-numerki.txt`. Dla piosenek tradycyjnych zapis
numerkowy (`zapis: numery`) działa tak samo jak literowy.

Katalogu `strony/` nie edytuj ręcznie, bo to wynik generatora. Zmiany wyglądu wprowadzaj
w `generator/kolorowe_pianino.py`.
