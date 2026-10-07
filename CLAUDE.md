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

Katalogu `strony/` nie edytuj ręcznie, bo to wynik generatora. Zmiany wyglądu wprowadzaj
w `generator/kolorowe_pianino.py`.
