#!/usr/bin/env python3
"""
Kolorowe pianino – generator stron z „kolorowymi nutami”.

Czyta pliki piosenek (piosenki/*.txt) i tworzy strony HTML (strony/*.html)
w stylu książeczki „Naklejasz i grasz”:
  lewa strona  – tytuł, słowa wszystkich zwrotek, ilustracja, legenda,
  prawa strona – melodia jako kolorowe klocki nawleczone na sznurek.

Zasady formatu opisuje plik ZASADY.md w katalogu głównym projektu.

Użycie:
  python generator/kolorowe_pianino.py                     # wszystkie piosenki
  python generator/kolorowe_pianino.py piosenki/05-sto-lat.txt
  python generator/kolorowe_pianino.py --sprawdz piosenki/05-sto-lat.txt
  python generator/kolorowe_pianino.py --pdf               # dodatkowo PDF książeczki do druku (Edge/Chrome)

Wymaga tylko Pythona 3.9+ (bez dodatkowych bibliotek).
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import math
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SONGS_DIR = ROOT / "piosenki"
OUT_DIR = ROOT / "strony"

# --------------------------------------------------------------------------
# Paleta i klawiatura
# --------------------------------------------------------------------------

# Kolory naklejek (odczytane ze zdjęć książeczki i rozjaśnione do druku).
COLORS = {
    "C": "#E3262B",  # czerwony
    "D": "#2A6BC1",  # niebieski
    "E": "#E4357F",  # różowy
    "F": "#5DAE35",  # zielony
    "G": "#F07B26",  # pomarańczowy
    "A": "#65297B",  # fioletowy
    "H": "#F5D23A",  # żółty
}
COLOR_WORDS = {
    "C": "czerwony", "D": "niebieski", "E": "różowy", "F": "zielony",
    "G": "pomarańczowy", "A": "fioletowy", "H": "żółty",
}
CORD = "#2F2C2C"
BLACK_KEY = "#1D1B1B"
TITLE_LEFT = "#7A1F2E"
TITLE_RIGHT = "#3A3838"
TEXT = "#2B2929"
TEXT_SOFT = "#77706B"
GREEN = "#7DBA3F"
GREEN_DARK = "#4E8F2A"

# Klawisze z naklejkami z książeczki: od środkowego C do e (10 białych klawiszy).
WHITE = ["C", "D", "E", "F", "G", "A", "H", "c", "d", "e"]
# Dodatkowe naklejki dla melodii, które nie mieszczą się w C–e: dwie w paski na lewo od czerwonej
# (A, i H, – te same kolory niżej) i cztery w kropki na prawo od różowej w kropki (f, g, a, h).
LOWER, UPPER = ["A,", "H,"], ["f", "g", "a", "h"]
ALL_WHITE = LOWER + WHITE + UPPER

# półton od środkowego C -> (biały klawisz z naklejką, stopień w pionie, czarny klawisz?)
# Czarny klawisz zapisujemy kolorem białego klawisza po LEWEJ + czarna belka.
KEYS = {
    -3: ("A,", -2, False), -2: ("A,", -1.5, True), -1: ("H,", -1, False),
    0: ("C", 0, False), 1: ("C", 0.5, True), 2: ("D", 1, False), 3: ("D", 1.5, True),
    4: ("E", 2, False), 5: ("F", 3, False), 6: ("F", 3.5, True), 7: ("G", 4, False),
    8: ("G", 4.5, True), 9: ("A", 5, False), 10: ("A", 5.5, True), 11: ("H", 6, False),
    12: ("c", 7, False), 13: ("c", 7.5, True), 14: ("d", 8, False), 15: ("d", 8.5, True),
    16: ("e", 9, False), 17: ("f", 10, False), 18: ("f", 10.5, True), 19: ("g", 11, False),
    20: ("g", 11.5, True), 21: ("a", 12, False), 22: ("a", 12.5, True), 23: ("h", 13, False),
}
LOW, HIGH = -3, 23            # wszystkie naklejki: A,–h
CORE_LOW, CORE_HIGH = 0, 16   # naklejki z książeczki: C–e
BASE_SEMI = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "H": 11, "B": 10}


def color_of(key: str) -> str:
    return COLORS[key[0].upper()]


def dotted(key: str) -> bool:
    return key[0].islower()


def striped(key: str) -> bool:
    return key.endswith(",")


def key_words(key: str) -> str:
    """Opis naklejki słowami, np. „zielony w kropki”, „żółty w paski”."""
    return COLOR_WORDS[key[0].upper()] + (" w kropki" if dotted(key) else " w paski" if striped(key) else "")

# --------------------------------------------------------------------------
# Geometria strony (viewBox 1000 x 707 ~ A4 / A5 poziomo)
# --------------------------------------------------------------------------

PAGE_W, PAGE_H = 1000, 707

BLOCK_H = 74            # wysokość klocka
QUARTER_W = 46          # szerokość ćwierćnuty
GAP = 6                 # przerwa między klockami (widać w niej sznurek)
UNIT = QUARTER_W + GAP  # „długość” jednej ćwierćnuty na sznurku
STEP = 0.14 * BLOCK_H   # przesunięcie w pionie na jeden biały klawisz
CORD_W = 0.27 * BLOCK_H
CORD_EXT = 10           # o ile sznurek wystaje za pierwszy/ostatni klocek
SHARP_OVER = 0.29       # o ile belka czarnego klawisza wystaje nad klocek (x BLOCK_H)
REPEAT_SPACE = 66       # miejsce na znak powtórki za rzędem
MEL_X0, MEL_X1 = 90, 930
MEL_Y0, MEL_Y1 = 150, 672
MIN_ROW_GAP, MAX_ROW_GAP = 40, 80
K_MAX = 1.7             # najwyższe powiększenie klocków, gdy melodia jest krótka
DEFAULT_TEMPO = 100     # ćwierćnut na minutę przy odtwarzaniu

FONT = "Montserrat, 'Segoe UI', Arial, sans-serif"
EMOJI_FONT = "'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif"


# --------------------------------------------------------------------------
# Model danych i parser
# --------------------------------------------------------------------------

class SongError(Exception):
    pass


@dataclass
class Note:
    semi: int | None  # None = pauza (sam sznurek)
    dur: float        # długość w ćwierćnutach
    src: str


@dataclass
class Row:
    items: list       # Note albo "|" (kreska taktowa)
    repeat: bool = False

    @property
    def notes(self) -> list[Note]:
        return [it for it in self.items if isinstance(it, Note)]


@dataclass
class Syl:
    sid: int            # numer sylaby na stronie ze słowami (atrybut data-s)
    text: str
    ext: int = 0        # o ile nut dłużej śpiewa się sylabę (znak „_” w słowach)
    first: bool = True  # pierwsza sylaba wyrazu


@dataclass
class Line:
    text: str                                   # wers do wyświetlenia (bez znaków „_”)
    note: bool = False                          # uwaga kursywą – nie jest śpiewana
    parts: list = field(default_factory=list)   # kawałki wersu: str albo Syl
    lid: int = -1                               # numer wersu na stronie
    st: int = -1                                # numer zwrotki
    ref: tuple | None = None                    # skrócony refren „…”: (zwrotka, wers), od którego się śpiewa

    @property
    def syls(self) -> list[Syl]:
        return [p for p in self.parts if isinstance(p, Syl)]


@dataclass
class Song:
    path: Path
    slug: str
    title: str
    subtitle: str = ""
    meter: str = ""
    transpose: int = 0
    illustration: str = ""
    theme: str = ""
    tempo: int = DEFAULT_TEMPO
    stanzas: list = field(default_factory=list)  # [[Line, ...], ...]
    rows: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    seq: list = field(default_factory=list)      # odtwarzanie: [półton | None, długość, nr klocka, nr sylaby]
    line_at: dict = field(default_factory=dict)  # nr wersu -> indeks w seq, od którego się go śpiewa
    sung: list = field(default_factory=list)     # do --sprawdz: (przejście, rząd, [nr sylaby, ...])

    def all_notes(self) -> list[Note]:
        return [n for r in self.rows for n in r.notes if n.semi is not None]

    def key_of(self, n: Note):
        return KEYS[n.semi + self.transpose]


def norm(s: str) -> str:
    s = s.strip().lower().replace("ł", "l")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


NOTE_RE = re.compile(r"^([A-Ha-h])([#b]?)([,']*)(16|1|2|4|8)?(\.)?$")
PAUSE_RE = re.compile(r"^-(16|1|2|4|8)?(\.)?$")
REPEAT_TOKENS = {"↻", "x2", "(x2)", "×2", "powtorz"}
META_KEYS = {
    "tytul": "title", "podtytul": "subtitle", "autor": "subtitle", "metrum": "meter",
    "transpozycja": "transpose", "ilustracja": "illustration", "kolor": "theme",
    "tempo": "tempo", "zapis": "notation",
}
# Zapis numerkowy (książeczki z ponumerowanymi klawiszami): 4 = środkowe C, 5 = D … 12 = d, 13 = e.
NUMBER_RE = re.compile(r"^(\d{1,2})([#b]?)(?::(16|1|2|4|8)(\.)?)?$")
NUMBER_OF_C = 4
WHITE_STEPS = [0, 2, 4, 5, 7, 9, 11]
INLINE_COMMENT_RE = re.compile(r"\s+#(\s.*)?$")


def parse_duration(num: str | None, dot: str | None, where: str) -> float:
    n = int(num) if num else 4
    if n == 16:
        raise SongError(f"{where}: szesnastki nie pasują do formatu książeczki – uprość rytm")
    d = 4 / n
    if dot:
        d *= 1.5
    return d


def parse_melody_line(line: str, where: str, numbered: bool = False) -> Row:
    line = line.replace(":|", " ↻ ").replace("|", " | ")
    row = Row(items=[])
    for tok in line.split():
        here = f"{where}, „{tok}”"
        if tok == "|":
            row.items.append("|")
            continue
        if tok == "↻" or norm(tok) in REPEAT_TOKENS:
            row.repeat = True
            continue
        m = PAUSE_RE.match(tok)
        if m:
            row.items.append(Note(None, parse_duration(m[1], m[2], here), tok))
            continue
        if numbered:
            m = NUMBER_RE.match(tok)
            if not m:
                raise SongError(f"{here}: w zapisie numerkowym nuta to numer klawisza, np. 7, 11:8, 9:2.")
            num, acc, dnum, dot = m.groups()
            octave, step = divmod(int(num) - NUMBER_OF_C, 7)
            semi = WHITE_STEPS[step] + 12 * octave + {"#": 1, "b": -1, "": 0}[acc]
            row.items.append(Note(semi, parse_duration(dnum, dot, here), tok))
            continue
        m = NOTE_RE.match(tok)
        if not m:
            raise SongError(f"{here}: nie rozumiem tego zapisu nuty")
        letter, acc, octs, num, dot = m.groups()
        semi = BASE_SEMI[letter.upper()] + (12 if letter.islower() else 0)
        semi += {"#": 1, "b": -1, "": 0}[acc]
        semi += 12 * octs.count("'") - 12 * octs.count(",")
        row.items.append(Note(semi, parse_duration(num, dot, here), tok))
    if not row.notes:
        raise SongError(f"{where}: pusty rząd melodii")
    return row


def parse_song(path: Path) -> Song:
    meta: dict[str, str] = {}
    section = None
    lyric_lines: list[str] = []
    melody_lines: list[tuple[int, str]] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.rstrip()
        s = line.strip()
        if s.startswith("#"):
            continue
        m = re.match(r"^\[(.+)\]$", s)
        if m:
            section = norm(m[1])
            if section not in ("slowa", "melodia"):
                raise SongError(f"{path.name}, wiersz {lineno}: nieznana sekcja [{m[1]}]")
            continue
        if section is None:
            if not s:
                continue
            key, sep, val = INLINE_COMMENT_RE.sub("", s).partition(":")
            if not sep or norm(key) not in META_KEYS:
                raise SongError(f"{path.name}, wiersz {lineno}: nieznane pole „{key}”")
            meta[META_KEYS[norm(key)]] = val.strip()
        elif section == "slowa":
            lyric_lines.append(line)
        elif s:
            melody_lines.append((lineno, INLINE_COMMENT_RE.sub("", s)))

    notation = norm(meta.get("notation", "litery"))
    if notation not in ("litery", "numery", "numerki"):
        raise SongError(f"{path.name}: „zapis:” może mieć wartość „litery” albo „numery”")
    rows = [parse_melody_line(s, f"{path.name}, wiersz {n}", numbered=notation != "litery")
            for n, s in melody_lines]

    if "title" not in meta:
        raise SongError(f"{path.name}: brak pola „tytuł:”")
    if not rows:
        raise SongError(f"{path.name}: brak sekcji [melodia]")

    stanzas, cur = [], []
    for line in lyric_lines + [""]:
        if line.strip():
            t = line.strip()
            if t.startswith(">"):
                note = t[1:].strip()
                cur.append(Line(note, True, [note]))
            else:
                cur.append(lyric_line(t))
        elif cur:
            stanzas.append(cur)
            cur = []
    number_lyrics(stanzas)

    try:
        transpose = int(meta.get("transpose", "0").replace("+", "") or 0)
    except ValueError:
        raise SongError(f"{path.name}: „transpozycja” musi być liczbą półtonów, np. +2 albo -5")

    try:
        tempo = int(meta.get("tempo", DEFAULT_TEMPO))
    except ValueError:
        raise SongError(f"{path.name}: „tempo” to liczba ćwierćnut na minutę, np. 100")
    if not 30 <= tempo <= 240:
        raise SongError(f"{path.name}: tempo {tempo} jest poza zakresem 30–240")

    song = Song(
        path=path, slug=path.stem, title=meta["title"], subtitle=meta.get("subtitle", ""),
        meter=meta.get("meter", ""), transpose=transpose,
        illustration=meta.get("illustration", ""), theme=meta.get("theme", ""), tempo=tempo,
        stanzas=stanzas, rows=rows,
    )
    validate(song)
    align_lyrics(song)
    return song


# --------------------------------------------------------------------------
# Sylaby i dopasowanie słów do nut
# --------------------------------------------------------------------------

VOWELS = set("aąeęioóuy")
DIGRAPHS = {"ch", "cz", "dz", "dź", "dż", "rz", "sz"}
LIQUIDS = {"r", "rz", "l", "ł"}                    # nie-dłu-go, o-gło-sza, przy-gry-waj
SIBILANTS = {"s", "ś", "z", "sz"}                  # chu-stecz-ka, pa-ste-rze
STOPS = {"p", "t", "k"}
SONORANTS = {"m", "n", "ń", "j", "l", "ł", "r"}
LETTERS_RE = re.compile(r"[^\W\d_]+")


def word_cuts(w: str) -> list[int]:
    """Miejsca podziału wyrazu na sylaby: tyle sylab, ile samogłosek („i” przed samogłoską tylko
    zmiękcza: nie-bo, dzie-ci). Ze spółgłosek między samogłoskami ostatnia idzie do następnej
    sylaby (ko-tek, moc-no, gwiazd-ko), razem z poprzedzającą ją spółgłoską, jeśli razem mogą
    zaczynać wyraz (nie-dłu-go, chu-stecz-ka). Dwuznaki (cz, sz, rz, ch, dz, dź, dż) są jedną głoską.
    Podział służy tylko do podświetlania sylab, więc wystarczy, że wygląda naturalnie."""
    lw = w.lower()
    nuc = [i for i, c in enumerate(lw)
           if c in VOWELS and not (c == "i" and i + 1 < len(lw) and lw[i + 1] in VOWELS)]
    cuts = []
    for a, b in zip(nuc, nuc[1:]):
        units, p = [], a + 1
        while p < b:
            if lw[p] == "i" and p == b - 1 and units:  # zmiękczenie zostaje przy spółgłosce
                break
            n = 2 if lw[p:p + 2] in DIGRAPHS else 1
            units.append((p, lw[p:p + n]))
            p += n
        k = len(units) - 1                      # od której głoski zaczyna się następna sylaba
        if k >= 1 and units[k][1] in LIQUIDS and units[k - 1][1] not in SONORANTS:
            k -= 1                              # spółgłoska + r/l/ł: dł, gr, prz
        if k >= 1 and units[k][1] in STOPS and units[k - 1][1] in SIBILANTS:
            k -= 1                              # s + p/t/k: st, sk, szk
        cuts.append(units[k][0] if units else a + 1)
    return cuts


def lyric_line(raw: str) -> Line:
    """Wers piosenki podzielony na sylaby. „_” po sylabie = sylaba trwa o jedną nutę dłużej."""
    chars, ext_at = [], {}
    for ch in raw:
        if ch == "_":
            ext_at[len(chars) - 1] = ext_at.get(len(chars) - 1, 0) + 1
        else:
            chars.append(ch)
    text = "".join(chars)
    spans, pending = [], None  # pending: wyraz bez samogłoski („w”, „z”) – śpiewa się z następną sylabą
    for m in LETTERS_RE.finditer(text):
        w = m.group()
        if not any(c in VOWELS for c in w.lower()):
            pending = m.start() if pending is None else pending
            continue
        bounds = [0] + word_cuts(w) + [len(w)]
        for k, (x, y) in enumerate(zip(bounds, bounds[1:])):
            start = m.start() + x
            if k == 0 and pending is not None:
                start, pending = pending, None
            spans.append((start, m.start() + y, Syl(-1, text[start:m.start() + y], 0, k == 0)))
    for pos, n in ext_at.items():  # „_” należy do sylaby, która kończy się przed nim
        owner = [s for a, _, s in spans if a <= pos]
        if owner:
            owner[-1].ext += n
    parts, pos = [], 0
    for a, b, s in spans:
        if a > pos:
            parts.append(text[pos:a])
        parts.append(s)
        pos = b
    if pos < len(text):
        parts.append(text[pos:])
    return Line(text, False, parts)


def plain_words(s: str) -> str:
    return " ".join(LETTERS_RE.findall(norm(s)))


def number_lyrics(stanzas: list) -> None:
    """Numeruje wersy i sylaby; skrócony refren („Chrystus się rodzi…”) wskazuje pełny tekst."""
    sid = lid = 0
    for si, st in enumerate(stanzas):
        for ln in st:
            ln.lid, ln.st, lid = lid, si, lid + 1
            for s in ln.syls:
                s.sid, sid = sid, sid + 1
            if ln.note or not re.search(r"(…|\.\.\.)\W*$", ln.text):
                continue
            short = plain_words(ln.text)
            ln.ref = next(((sj, lj) for sj, st2 in enumerate(stanzas[:si]) for lj, ln2 in enumerate(st2)
                           if not ln2.note and short and plain_words(ln2.text).startswith(short)), None)


def align_lyrics(song: Song) -> None:
    """Przypisuje sylaby słów do nut i układa całe odtwarzanie (song.seq): melodia gra tyle razy,
    ile trzeba na wszystkie zwrotki.

    Zwrotki łączą się w „przejścia” melodii: przejście ma tyle sylab, ile melodia ma nut
    (z powtórkami ↻), albo tyle, ile bez powtórek – wtedy powtórzony rząd śpiewa się z tymi samymi
    słowami. Gdy wszystkie słowa razem są kilka razy krótsze od melodii, śpiewa się je od nowa."""
    row_notes, block_no = [], 0
    for row in song.rows:
        out = []
        for nt in row.notes:
            if nt.semi is None:
                out.append((None, nt.dur, -1))
            else:
                out.append((nt.semi + song.transpose, nt.dur, block_no))
                block_no += 1
        row_notes.append(out)
    plays = [ri for ri, row in enumerate(song.rows) for _ in range(2 if row.repeat else 1)]
    sung = [sum(1 for n in r if n[0] is not None) for r in row_notes]
    k_full, k_once = sum(sung[ri] for ri in plays), sum(sung)

    def units(st):  # sylaby zwrotki po kolei, każda tyle razy, na ile nut przypada: (sylaba, wers)
        out = []
        for ln in st:
            if ln.note:
                continue
            src = [ln]
            if ln.ref:
                src = [x for x in song.stanzas[ln.ref[0]][ln.ref[1]:] if not x.note and not x.ref]
            out += [(s.sid, ln.lid) for x in src for s in x.syls for _ in range(1 + s.ext)]
        return out

    groups = [u for u in map(units, song.stanzas) if u]
    total = sum(map(len, groups))
    passes, acc, ok = [], [], True
    for g in groups:
        acc += g
        if len(acc) == k_full:
            passes.append((acc, False))
            acc = []
        elif len(acc) == k_once:
            passes.append((acc, True))
            acc = []
        elif len(acc) > k_full:
            ok = False
    if acc or not ok:
        stream = [u for g in groups for u in g]
        if total and k_full % total == 0:
            passes = [(stream * (k_full // total), False)]
        else:
            passes = [(stream[i:i + k_full], False) for i in range(0, len(stream), k_full)]
            song.warnings.append(
                f"słowa nie pasują do nut: zwrotki mają {', '.join(str(len(g)) for g in groups)} sylab, "
                f"a melodia {k_full} nut" + (f" (bez powtórek ↻: {k_once})" if k_once != k_full else "") +
                " – sylabę śpiewaną na kilku nutach oznacz „_” (np. „le_ży”); sprawdź podział w opisie poniżej")
    if not passes:
        passes = [([], False)]

    song.seq, song.line_at, song.sung = [], {}, []
    for pn, (us, reuse) in enumerate(passes, 1):
        cur, first_at = 0, {}
        for ri in plays:
            c = first_at[ri] if reuse and ri in first_at else cur
            first_at.setdefault(ri, c)
            sids = []
            for semi, dur, blk in row_notes[ri]:
                sid = -1
                if semi is not None and c < len(us):
                    sid, lid = us[c]
                    c += 1
                    song.line_at.setdefault(lid, len(song.seq))
                    sids.append(sid)
                song.seq.append([semi, dur, blk, sid])
            song.sung.append((pn, ri, sids))
            cur = max(cur, c)


def fmt_q(x: float) -> str:
    return f"{x:g}"


def transpositions(song: Song):
    """Przesunięcia (w półtonach), przy których melodia mieści się w naklejkach A,–h:
    [(czarne klawisze, dodatkowe naklejki, |przesunięcie|, przesunięcie)]. Najpierw te, które
    zostają w naklejkach z książeczki (C–e), potem z najmniejszą liczbą czarnych klawiszy."""
    semis = [n.semi for n in song.all_notes()]
    out = []
    for t in range(-24, 25):
        moved = [s + t for s in semis]
        if min(moved) >= LOW and max(moved) <= HIGH:
            blacks = sum(1 for s in moved if KEYS[s][2])
            extra = len({KEYS[s][0] for s in moved if not CORE_LOW <= s <= CORE_HIGH})
            out.append((blacks, extra, abs(t), t))
    return sorted(out, key=lambda o: (o[1] > 0, o[0], o[1], o[2]))


def fmt_transposition(opt) -> str:
    blacks, extra, _, t = opt
    return f"{t:+d}/{blacks}" + (f" (dodatkowe naklejki: {extra})" if extra else "")


def extra_keys(song: Song) -> list[str]:
    """Dodatkowe naklejki (poza C–e), których potrzebuje melodia, od lewej do prawej."""
    used = {song.key_of(n)[0] for n in song.all_notes()}
    return [k for k in ALL_WHITE if k in used and k not in WHITE]


def validate(song: Song) -> None:
    bad = [n for n in song.all_notes() if not LOW <= n.semi + song.transpose <= HIGH]
    if bad:
        opts = transpositions(song)
        hint = ""
        if opts:
            best = ", ".join(fmt_transposition(o) for o in opts[:4])
            hint = f" Propozycje pola „transpozycja:” (półtony/czarne klawisze): {best}."
        else:
            hint = " Melodia ma większą rozpiętość niż A,–h – wybierz fragment albo inną piosenkę."
        raise SongError(
            f"{song.path.name}: nuty {' '.join('„' + n.src + '”' for n in bad[:6])} wychodzą poza "
            f"klawisze z naklejkami (A,–h).{hint}")

    if extra_keys(song):
        blacks = sum(1 for n in song.all_notes() if song.key_of(n)[2])
        core = [o for o in transpositions(song) if not o[1] and o[0] <= blacks]
        if core:
            song.warnings.append(
                f"melodia potrzebuje dodatkowych naklejek ({', '.join(extra_keys(song))}), a z „transpozycja: "
                f"{core[0][3]:+d}” mieści się w C–e (czarnych klawiszy: {core[0][0]})")

    if not song.stanzas:
        song.warnings.append("brak słów w sekcji [słowa]")
    if len(song.rows) > 5:
        song.warnings.append(f"{len(song.rows)} rzędów melodii – w książeczce są 3–4, rozważ łączenie fraz")
    for i, row in enumerate(song.rows, 1):
        total = sum(n.dur for n in row.notes)
        if total > 18:  # ok. 16 ćwierćnut i miejsce na pauzy
            song.warnings.append(f"rząd {i} ma {fmt_q(total)} ćwierćnut – klocki zostaną zmniejszone")

    m = re.match(r"^(\d+)\s*/\s*(\d+)$", song.meter)
    if song.meter and not m:
        song.warnings.append(f"nie rozumiem metrum „{song.meter}”")
    if not m:
        return
    bar_len = int(m[1]) * 4 / int(m[2])
    segs, cur, sound = [], 0.0, False
    for row in song.rows:
        for it in row.items:
            if it == "|":
                segs.append((cur, sound))
                cur, sound = 0.0, False
            else:
                cur += it.dur
                sound = sound or it.semi is not None
        if row.repeat:  # znak powtórki zamyka takt
            segs.append((cur, sound))
            cur, sound = 0.0, False
    segs.append((cur, sound))
    segs = [s for s, snd in segs if snd]  # takt z samą pauzą („| - |”) to oddech poza metrum
    if len(segs) < 2:
        return
    for i, s in enumerate(segs):
        edge = i in (0, len(segs) - 1)  # przedtakt / ostatni takt mogą być niepełne
        if (edge and s > bar_len + 1e-9) or (not edge and abs(s - bar_len) > 1e-9):
            song.warnings.append(
                f"takt {i + 1} ma {fmt_q(s)} ćwierćnut zamiast {fmt_q(bar_len)} (metrum {song.meter})")


# --------------------------------------------------------------------------
# Pomocnicze funkcje SVG
# --------------------------------------------------------------------------

def esc(s) -> str:
    return html.escape(str(s), quote=True)


def f1(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".")


def uid_of(slug: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", norm(slug)).strip("-") or "p"


def mix(c1: str, c2: str, t: float) -> str:
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def text_width(s: str, size: float, bold: bool = False) -> float:
    """Przybliżona szerokość tekstu w kroju Montserrat (dokładne dopasowanie robi JS)."""
    w = 0.0
    for ch in s:
        if ch == " ":
            w += 0.28
        elif ch in ".,;:!'’|()„”\"":
            w += 0.27
        elif ch in "–-":
            w += 0.42
        elif ch in "mwMW":
            w += 0.86
        elif ch in "ijlIt":
            w += 0.3
        elif ch.isupper():
            w += 0.72
        else:
            w += 0.58
    return w * size * (1.06 if bold else 1.0)


def text_el(x, y, s, size, *, fill=TEXT, weight=400, anchor="start", italic=False,
            maxw=None, group=None, spacing=None, inner=None, extra="") -> str:
    attrs = [f'x="{f1(x)}"', f'y="{f1(y)}"', f'font-size="{f1(size)}"', f'fill="{fill}"']
    if weight != 400:
        attrs.append(f'font-weight="{weight}"')
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if italic:
        attrs.append('font-style="italic"')
    if spacing:
        attrs.append(f'letter-spacing="{spacing}"')
    if maxw:
        attrs.append(f'data-maxw="{f1(maxw)}" data-fs="{f1(size)}"')
    if group:
        attrs.append(f'data-group="{group}"')
    if extra:
        attrs.append(extra)
    return f'<text {" ".join(attrs)}>{esc(s) if inner is None else inner}</text>'


def music_icon(x: float, y: float, s: float, uid: str) -> str:
    """Zielona nutka ♫ w lewym górnym rogu strony."""
    g = f"{uid}-ng"
    return (
        f'<defs><linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{GREEN}"/><stop offset="1" stop-color="{GREEN_DARK}"/>'
        f'</linearGradient></defs>'
        f'<g fill="url(#{g})">'
        f'<ellipse cx="{f1(x + .17 * s)}" cy="{f1(y + .84 * s)}" rx="{f1(.19 * s)}" ry="{f1(.14 * s)}" '
        f'transform="rotate(-22 {f1(x + .17 * s)} {f1(y + .84 * s)})"/>'
        f'<ellipse cx="{f1(x + .7 * s)}" cy="{f1(y + .74 * s)}" rx="{f1(.19 * s)}" ry="{f1(.14 * s)}" '
        f'transform="rotate(-22 {f1(x + .7 * s)} {f1(y + .74 * s)})"/>'
        f'<rect x="{f1(x + .3 * s)}" y="{f1(y + .14 * s)}" width="{f1(.07 * s)}" height="{f1(.7 * s)}" rx="{f1(.03 * s)}"/>'
        f'<rect x="{f1(x + .83 * s)}" y="{f1(y + .04 * s)}" width="{f1(.07 * s)}" height="{f1(.7 * s)}" rx="{f1(.03 * s)}"/>'
        f'<path d="M{f1(x + .3 * s)} {f1(y + .14 * s)} L{f1(x + .9 * s)} {f1(y + .02 * s)} '
        f'L{f1(x + .9 * s)} {f1(y + .18 * s)} L{f1(x + .3 * s)} {f1(y + .3 * s)} Z"/>'
        f'</g>'
    )


def repeat_icon(cx: float, cy: float, r: float, color: str = CORD) -> str:
    """Okrągła strzałka „powtórz”."""
    sw = r * 0.32
    a0, a1 = math.radians(-40), math.radians(245)
    p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0))
    p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
    d = (-math.sin(a1), math.cos(a1))           # kierunek ruchu na końcu łuku
    nrm = (-d[1], d[0])
    tip = (p1[0] + d[0] * r * .62, p1[1] + d[1] * r * .62)
    b1 = (p1[0] + nrm[0] * r * .52 - d[0] * r * .05, p1[1] + nrm[1] * r * .52 - d[1] * r * .05)
    b2 = (p1[0] - nrm[0] * r * .52 - d[0] * r * .05, p1[1] - nrm[1] * r * .52 - d[1] * r * .05)
    return (
        f'<path d="M{f1(p0[0])} {f1(p0[1])} A{f1(r)} {f1(r)} 0 1 1 {f1(p1[0])} {f1(p1[1])}" '
        f'fill="none" stroke="{color}" stroke-width="{f1(sw)}" stroke-linecap="round"/>'
        f'<path d="M{f1(tip[0])} {f1(tip[1])} L{f1(b1[0])} {f1(b1[1])} L{f1(b2[0])} {f1(b2[1])} Z" '
        f'fill="{color}" stroke="{color}" stroke-width="{f1(sw * .35)}" stroke-linejoin="round"/>'
    )


def block_svg(x, y, w, h, key, sharp, dur, k=1.0) -> str:
    """Jeden klocek-naklejka: kolor = klawisz, kropki = wyższa oktawa, paski = niższa,
    belka = czarny klawisz."""
    out = [f'<rect x="{f1(x)}" y="{f1(y)}" width="{f1(w)}" height="{f1(h)}" rx="{f1(2 * k)}" fill="{color_of(key)}"/>']
    if dotted(key):
        cols = max(1, round(dur * 2))
        r = 0.07 * h
        for c in range(cols):
            cx = x + w * (c + 0.5) / cols
            for fy in (0.2, 0.5, 0.8):
                out.append(f'<circle cx="{f1(cx)}" cy="{f1(y + h * fy)}" r="{f1(r)}" fill="#fff"/>')
    if striped(key):
        sh = 0.11 * h
        inset = min(0.16 * QUARTER_W * k, 0.18 * w)
        for fy in (0.3, 0.7):
            out.append(f'<rect x="{f1(x + inset)}" y="{f1(y + h * fy - sh / 2)}" width="{f1(w - 2 * inset)}" '
                       f'height="{f1(sh)}" rx="{f1(sh / 2)}" fill="#fff"/>')
    if sharp:
        bw = min(0.46 * QUARTER_W * k, w * 0.75)
        bh = 0.58 * h
        inset = min(0.07 * QUARTER_W * k, (w - bw) / 2)
        bx = x + w - bw - inset
        by = y - SHARP_OVER * h
        out.append(f'<rect x="{f1(bx)}" y="{f1(by)}" width="{f1(bw)}" height="{f1(bh)}" '
                   f'rx="{f1(bw * .16)}" fill="{BLACK_KEY}"/>')
    return "".join(out)


def mini_keyboard(x: float, y: float, highlight_semi: int | None = None, kw: float = 15, kh: float = 52,
                  lo: int = CORE_LOW, hi: int = CORE_HIGH, marks=()) -> tuple[str, float]:
    """Mała klawiatura z naklejkami od półtonu lo do hi (do legendy): zaznacza czarny klawisz
    highlight_semi albo naklejki marks (pełny kolor, kropki/paski)."""
    whites = [s for s in range(lo, hi + 1) if not KEYS[s][2]]
    out = []
    for i, semi in enumerate(whites):
        kx, name = x + i * kw, KEYS[semi][0]
        out.append(f'<rect x="{f1(kx)}" y="{f1(y)}" width="{f1(kw)}" height="{f1(kh)}" '
                   f'fill="#fff" stroke="#c9c4c0" stroke-width="1"/>')
        sx, sy, sw, sh = kx + kw * .18, y + kh * .66, kw * .64, kh * .27
        if name in marks:
            out.append(block_svg(sx, sy - kh * .05, sw, sh + kh * .05, name, False, 0.5, sw / QUARTER_W))
        else:
            out.append(f'<rect x="{f1(sx)}" y="{f1(sy)}" width="{f1(sw)}" height="{f1(sh)}" '
                       f'fill="{color_of(name)}" opacity=".35"/>')
    for i, semi in enumerate(whites[:-1]):
        if KEYS.get(semi + 1, ("", 0, False))[2]:
            bx = x + (i + 1) * kw - kw * .3
            fill = BLACK_KEY if semi + 1 == highlight_semi else "#d8d4d1"
            out.append(f'<rect x="{f1(bx)}" y="{f1(y)}" width="{f1(kw * .6)}" height="{f1(kh * .58)}" fill="{fill}"/>')
    return "".join(out), len(whites) * kw


# --------------------------------------------------------------------------
# Prawa strona – melodia
# --------------------------------------------------------------------------

def bar_sound(row: Row) -> list[bool]:
    """Dla każdej nuty rzędu: czy w jej takcie coś brzmi (takt z samą pauzą rysuje się jako przerwa)."""
    out, bar = [], []
    for it in row.items + ["|"]:
        if it == "|":
            out += [any(n.semi is not None for n in bar)] * len(bar)
            bar = []
        else:
            bar.append(it)
    return out


def render_melody_page(song: Song, uid: str) -> str:
    parts = [music_icon(78, 50, 50, uid + "-m")]
    parts.append(text_el(PAGE_W / 2, 103, song.title.upper(), 30, fill=TITLE_RIGHT, weight=700,
                         anchor="middle", maxw=640, spacing="0.5"))

    rows = []
    for row in song.rows:
        notes = row.notes
        steps = [song.key_of(n)[1] for n in notes if n.semi is not None]
        rows.append(dict(
            notes=notes, repeat=row.repeat, merge=bar_sound(row),
            total=sum(n.dur for n in notes),
            smin=min(steps), smax=max(steps),
            sharp=any(song.key_of(n)[2] for n in notes if n.semi is not None),
        ))

    def content_w(r):
        return 2 * CORD_EXT + r["total"] * UNIT - GAP + (REPEAT_SPACE if r["repeat"] else 0)

    heights = [(r["smax"] - r["smin"]) * STEP + BLOCK_H + (SHARP_OVER * BLOCK_H if r["sharp"] else 0)
               for r in rows]
    n = len(rows)
    avail_w, avail_h = MEL_X1 - MEL_X0, MEL_Y1 - MEL_Y0
    widest = max(content_w(r) for r in rows)
    # Klocki rosną (do K_MAX), aż najdłuższy rząd wypełni szerokość strony – albo skończy się wysokość.
    k = min(K_MAX, avail_w / widest, (avail_h - (n - 1) * MIN_ROW_GAP) / sum(heights))
    used = k * sum(heights)
    gap = 0 if n == 1 else min(MAX_ROW_GAP * k, (avail_h - used) / (n - 1))
    y = MEL_Y0 + (avail_h - used - gap * (n - 1)) * 0.45
    x0 = MEL_X0 + (avail_w - widest * k) / 2  # cała melodia wyśrodkowana, rzędy wyrównane do lewej

    bh = BLOCK_H * k
    block_no = 0
    for r, h in zip(rows, heights):
        top = y + (SHARP_OVER * bh if r["sharp"] else 0)
        x = x0 + CORD_EXT * k
        blocks, pts = [], []
        for i, nt in enumerate(r["notes"]):
            if nt.semi is not None:
                # Pauza w takcie z nutami poszerza klocek przed nią (książeczka nie ma pauz), a przy ▶ jest
                # ciszą. Takt z samą pauzą zostaje przerwą na sznurku – widać, że trzeba poczekać.
                held = nt.dur
                for nx, in_bar in zip(r["notes"][i + 1:], r["merge"][i + 1:]):
                    if nx.semi is not None or not in_bar:
                        break
                    held += nx.dur
                w = (held * UNIT - GAP) * k
                key, step, sharp = song.key_of(nt)
                by = top + (r["smax"] - step) * STEP * k
                blocks.append(f'<g class="blk" data-n="{block_no}">'
                              f'{block_svg(x, by, w, bh, key, sharp, held, k)}</g>')
                block_no += 1
                pts.append((x + w / 2, by + bh / 2))
            x += nt.dur * UNIT * k
        x_end = x - GAP * k
        cord = [(x0, pts[0][1])] + pts + [(x_end + CORD_EXT * k, pts[-1][1])]
        parts.append(
            f'<polyline points="{" ".join(f"{f1(px)},{f1(py)}" for px, py in cord)}" fill="none" '
            f'stroke="{CORD}" stroke-width="{f1(CORD_W * k)}" stroke-linecap="round" stroke-linejoin="round"/>')
        parts.extend(blocks)
        if r["repeat"]:
            ri = 0.3 * bh
            parts.append(repeat_icon(x_end + CORD_EXT * k + 18 * k + ri, pts[-1][1], ri))
        y += h * k + gap

    if round(k * 100) < 80:
        song.warnings.append(f"klocki zmniejszone do {k:.0%} – rozważ podział długich rzędów")
    if widest * k < 0.7 * avail_w:
        song.warnings.append(f"melodia zajmuje tylko {widest * k / avail_w:.0%} szerokości strony – "
                             "połącz krótkie rzędy w dłuższe (do ok. 16 ćwierćnut)")
    return svg_page(uid + "-mel", "".join(parts))


def count_in(song: Song) -> int:
    """Ile uderzeń odliczyć przed graniem samemu: jeden takt ćwierćnut (co najmniej 3 uderzenia).
    W szybkiej piosence odtwarzacz odlicza je co półnutę (BEAT_MIN w PLAY_JS)."""
    m = re.match(r"^(\d+)\s*/\s*(\d+)$", song.meter)
    beats = int(m[1]) * 4 / int(m[2]) if m else 4
    if beats != int(beats) or not 2 <= beats <= 6:
        return 4
    return int(beats) * (2 if beats < 3 else 1)


# --------------------------------------------------------------------------
# Lewa strona – słowa
# --------------------------------------------------------------------------

def stanza_h(st, lh):
    return len(st) * lh


def layout_lyrics(song: Song, top: float, bottom_left: float, bottom_right: float):
    """Dobiera wielkość czcionki i liczbę kolumn tak, żeby słowa zmieściły się na stronie."""
    stanzas = song.stanzas or [[Line("")]]
    for fs in range(21, 14, -1):
        lh, sg = fs * 1.45, fs * 1.45 * 0.8
        widest = max(text_width(ln.text, fs * (0.85 if ln.note else 1)) for st in stanzas for ln in st)
        hs = [stanza_h(st, lh) for st in stanzas]
        total = sum(hs) + sg * (len(hs) - 1)
        if total <= bottom_left - top and widest <= 440:
            return dict(fs=fs, lh=lh, sg=sg, cols=[stanzas], xs=[100], colw=440)
        # dwie kolumny – podział między zwrotkami albo (dla jednej zwrotki) w połowie
        candidates = []
        if len(stanzas) > 1:
            for i in range(1, len(stanzas)):
                candidates.append((stanzas[:i], stanzas[i:]))
        else:
            st = stanzas[0]
            mid = (len(st) + 1) // 2
            candidates.append(([st[:mid]], [st[mid:]]))
        best = None
        for c1, c2 in candidates:
            h1 = sum(stanza_h(s, lh) for s in c1) + sg * (len(c1) - 1)
            h2 = sum(stanza_h(s, lh) for s in c2) + sg * (len(c2) - 1)
            if h1 <= bottom_left - top and h2 <= bottom_right - top:
                score = max(h1, h2)
                if best is None or score < best[0]:
                    best = (score, c1, c2)
        if best and widest <= 400:
            return dict(fs=fs, lh=lh, sg=sg, cols=[best[1], best[2]], xs=[100, 540], colw=400)
    song.warnings.append("słowa są bardzo długie – mogą nie zmieścić się na stronie")
    half = (len(stanzas) + 1) // 2
    fs = 15
    return dict(fs=fs, lh=fs * 1.45, sg=fs * 1.16, cols=[stanzas[:half], stanzas[half:]], xs=[100, 540], colw=400)


def illustration_svg(song: Song, uid: str, cx: float, cy: float, r: float) -> str:
    spec = song.illustration.strip()
    if not spec:
        return ""
    theme_key = theme_key_of(song)
    main = COLORS[theme_key]
    high_key = max(song.all_notes(), key=lambda n: n.semi)
    second = color_of(song.key_of(high_key)[0])
    if second == main:
        second = COLORS["D"] if main != COLORS["D"] else COLORS["E"]
    p1, p2, p3 = mix(main, "#FFFFFF", .55), mix(main, "#FFFFFF", .8), mix(second, "#FFFFFF", .7)
    seed = sum(map(ord, song.slug)) % 97
    defs = (
        f'<defs>'
        f'<filter id="{uid}-wc" x="-30%" y="-30%" width="160%" height="160%">'
        f'<feTurbulence type="fractalNoise" baseFrequency="0.016" numOctaves="3" seed="{seed}" result="n"/>'
        f'<feDisplacementMap in="SourceGraphic" in2="n" scale="{f1(r * .3)}" xChannelSelector="R" yChannelSelector="G" result="d"/>'
        f'<feGaussianBlur in="d" stdDeviation="{f1(r * .025)}"/>'
        f'</filter>'
        f'<radialGradient id="{uid}-rg" cx="45%" cy="40%" r="62%">'
        f'<stop offset="0" stop-color="#FFFFFF"/><stop offset=".55" stop-color="{p2}"/>'
        f'<stop offset="1" stop-color="{p1}"/></radialGradient>'
        f'</defs>'
    )
    wash = (
        f'<g filter="url(#{uid}-wc)">'
        f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="{f1(r)}" fill="url(#{uid}-rg)"/>'
        f'<circle cx="{f1(cx + r * .45)}" cy="{f1(cy - r * .42)}" r="{f1(r * .42)}" fill="{p3}" opacity=".55"/>'
        f'<circle cx="{f1(cx - r * .5)}" cy="{f1(cy + r * .5)}" r="{f1(r * .32)}" fill="{p3}" opacity=".45"/>'
        f'</g>'
    )
    img = image_data_uri(song, spec)
    if img:
        content = (f'<image href="{img}" x="{f1(cx - r)}" y="{f1(cy - r)}" width="{f1(2 * r)}" '
                   f'height="{f1(2 * r)}" preserveAspectRatio="xMidYMid meet"/>')
        return defs + content
    emojis = spec.split()
    content = [f'<text x="{f1(cx)}" y="{f1(cy + r * .06)}" font-size="{f1(r * 1.05)}" text-anchor="middle" '
               f'dominant-baseline="central" font-family="{EMOJI_FONT}">{esc(emojis[0])}</text>']
    spots = [(.66, -.6, .4), (-.68, .58, .34)]
    for e, (dx, dy, sz) in zip(emojis[1:], spots):
        content.append(f'<text x="{f1(cx + dx * r)}" y="{f1(cy + dy * r)}" font-size="{f1(r * sz)}" '
                       f'text-anchor="middle" dominant-baseline="central" font-family="{EMOJI_FONT}">{esc(e)}</text>')
    return defs + wash + "".join(content)


def image_data_uri(song: Song, spec: str) -> str:
    if not re.search(r"\.(png|jpe?g|gif|svg|webp)$", spec, re.I):
        return ""
    for base in (song.path.parent, ROOT):
        p = (base / spec).resolve()
        if p.is_file():
            mime = mimetypes.guess_type(p.name)[0] or "image/png"
            return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"
    song.warnings.append(f"nie znaleziono pliku ilustracji „{spec}”")
    return ""


def theme_key_of(song: Song) -> str:
    t = norm(song.theme)
    for key, word in COLOR_WORDS.items():
        if t and norm(word) == t:
            return key
    if t.upper() in COLORS:
        return t.upper()
    return song.key_of(song.all_notes()[0])[0][0].upper()


def legend_svg(song: Song, right: float, cy: float) -> tuple[str, float]:
    """Legenda symboli użytych w piosence (czarne klawisze, dodatkowe naklejki, powtórka) –
    wyrównana do prawej."""
    items = []
    semis = [n.semi + song.transpose for n in song.all_notes()]
    lo, hi = min(CORE_LOW, min(semis)), max(CORE_HIGH, max(semis))
    if KEYS[lo][2]:
        lo -= 1  # klawiatura zaczyna się od białego klawisza
    kw = min(15, 170 / sum(1 for s in range(lo, hi + 1) if not KEYS[s][2]))
    bw, bh = 30, 46
    extras = extra_keys(song)
    if extras:
        part, x = [], 0
        for key in extras:
            part.append(block_svg(x, cy - bh / 2 + 7, bw, bh, key, False, 1.0, bw / QUARTER_W))
            x += bw + 6
        part.append(text_el(x + 7, cy + 14, "=", 28, fill=TEXT, weight=500))
        kb, kbw = mini_keyboard(x + 34, cy - 22, kw=kw, lo=lo, hi=hi, marks=extras)
        part.append(kb)
        items.append(("".join(part), x + 34 + kbw))
    sharps = sorted({s for s in semis if KEYS[s][2]})
    for semi in sharps[:2]:
        key = KEYS[semi][0]
        part = [block_svg(0, cy - bh / 2 + 7, bw, bh, key, True, 1.0, bw / QUARTER_W)]
        part.append(text_el(bw + 13, cy + 14, "=", 28, fill=TEXT, weight=500))
        kb, kbw = mini_keyboard(bw + 40, cy - 22, semi, kw=kw, lo=lo, hi=hi)
        part.append(kb)
        items.append(("".join(part), bw + 40 + kbw))
    if any(r.repeat for r in song.rows):
        part = repeat_icon(18, cy + 2, 16) + text_el(46, cy + 10, "Powtórz", 21, fill=TEXT, weight=500)
        items.append((part, 46 + text_width("Powtórz", 21)))
    if not items:
        return "", 0
    total = sum(w for _, w in items) + 34 * (len(items) - 1)
    x = right - total
    out = []
    for svg, w in items:
        out.append(f'<g transform="translate({f1(x)} 0)">{svg}</g>')
        x += w + 34
    return "".join(out), total


def page_badge(x: float, y: float, num: int) -> str:
    """Zielona „drabinka” z numerem strony (jak w książeczce)."""
    return (
        f'<g fill="{GREEN}">'
        f'<rect x="{f1(x - 15)}" y="{f1(y - 25)}" width="8" height="50" rx="4"/>'
        f'<rect x="{f1(x + 7)}" y="{f1(y - 25)}" width="8" height="50" rx="4"/>'
        f'<rect x="{f1(x - 19)}" y="{f1(y - 14)}" width="38" height="7" rx="3.5"/>'
        f'<rect x="{f1(x - 19)}" y="{f1(y + 8)}" width="38" height="7" rx="3.5"/>'
        f'</g>'
        f'<circle cx="{f1(x)}" cy="{f1(y)}" r="10" fill="#fff"/>'
        + text_el(x, y + 5, str(num), 13, fill=TEXT, weight=700, anchor="middle")
    )


def lyric_el(song: Song, ln: Line, x: float, y: float, fs: float, maxw: float) -> str:
    """Wers słów; każda sylaba w osobnym <tspan data-s>, żeby odtwarzacz mógł ją podświetlić."""
    inner = "".join(f'<tspan data-s="{p.sid}">{esc(p.text)}</tspan>' if isinstance(p, Syl) else esc(p)
                    for p in ln.parts)
    extra = f'class="lyr" data-st="{ln.st}"'
    if ln.lid in song.line_at:
        extra += f' data-at="{song.line_at[ln.lid]}"'
    return text_el(x, y, ln.text, fs * (0.85 if ln.note else 1), fill=TEXT_SOFT if ln.note else TEXT,
                   italic=ln.note, maxw=maxw, group="lyr", inner=inner, extra=extra)


def render_lyrics_page(song: Song, uid: str, page_no: int | None) -> str:
    parts = [music_icon(88, 50, 52, uid + "-l")]
    parts.append(text_el(540, 105, song.title.upper(), 31, fill=TITLE_LEFT, weight=700,
                         anchor="middle", maxw=720, spacing="0.5"))
    top = 190
    if song.subtitle:
        parts.append(text_el(540, 137, song.subtitle, 18, fill="#6B4A50", anchor="middle", maxw=640))
        top = 205

    legend, legend_w = legend_svg(song, 935, 652)
    bottom = 665
    lay = layout_lyrics(song, top, bottom, 600 if legend else bottom)
    fs, lh, sg = lay["fs"], lay["lh"], lay["sg"]
    col_bottoms = []
    for col, x in zip(lay["cols"], lay["xs"]):
        y = top + fs
        for si, st in enumerate(col):
            if si:
                y += sg
            for ln in st:
                parts.append(lyric_el(song, ln, x, y, fs, lay["colw"]))
                y += lh
        col_bottoms.append(y - lh + fs * 0.4)

    # Ilustracja: w jednej kolumnie – po prawej; w dwóch – pod krótszą kolumną.
    if len(lay["cols"]) == 1:
        area = (570, top - 15, 935, (600 if legend else 650))
    else:
        free1 = bottom - col_bottoms[0]
        free2 = (600 if legend else bottom) - col_bottoms[1]
        if free1 >= free2:
            area = (100, col_bottoms[0] + 15, 500, bottom)
        else:
            area = (540, col_bottoms[1] + 15, 935, 600 if legend else bottom)
    ax0, ay0, ax1, ay1 = area
    r = min((ax1 - ax0) / 2 - 12, (ay1 - ay0) / 2 - 10, 170)
    if r >= 55:
        parts.append(illustration_svg(song, uid, (ax0 + ax1) / 2, (ay0 + ay1) / 2, r))

    parts.append(legend)
    if page_no:
        parts.append(page_badge(78, 655, page_no))
    return svg_page(uid + "-lyr", "".join(parts))


# --------------------------------------------------------------------------
# Strona „Jak grać?”
# --------------------------------------------------------------------------

def render_howto_page() -> str:
    uid = "jak-grac"
    p = [music_icon(78, 46, 50, uid)]
    title = "JAK GRAĆ?"
    cycle = ["C", "G", "D", "F", "E", "A", "H", "C", "D"]
    letters = []
    x = 500 - text_width(title, 44, True) / 2
    for ch, key in zip(title, cycle):
        fill = COLORS[key] if ch != " " else "none"
        letters.append(f'<tspan fill="{fill}">{esc(ch)}</tspan>')
    p.append(f'<text x="500" y="100" font-size="44" font-weight="800" text-anchor="middle" '
             f'letter-spacing="1.5">{"".join(letters)}</text>')

    # Klawiatura z naklejkami: z książeczki (C–e) i dodatkowymi po bokach (bledsze podpisy)
    names = ["G,"] + ALL_WHITE + ["c'"]
    kw, kh = 46, 140
    kx0 = 500 - len(names) * kw / 2
    ky = 124
    for i, nm in enumerate(names):
        x = kx0 + i * kw
        p.append(f'<rect x="{f1(x)}" y="{ky}" width="{kw}" height="{kh}" rx="3" fill="#fff" stroke="#bdb7b2" stroke-width="1.5"/>')
        if nm in ALL_WHITE:
            sw, sh = 28, 40
            p.append(block_svg(x + (kw - sw) / 2, ky + kh - sh - 12, sw, sh, nm, False, 1.0, sw / QUARTER_W))
            p.append(text_el(x + kw / 2, ky + kh + 29, nm.rstrip(","), 23,
                             fill=COLORS["C"] if nm == "C" else TEXT if nm in WHITE else TEXT_SOFT,
                             weight=700 if nm in WHITE else 500, anchor="middle"))
    for i, nm in enumerate(names[:-1]):
        if nm[0].upper() in "CDFGA":
            x = kx0 + (i + 1) * kw - 14
            p.append(f'<rect x="{f1(x)}" y="{ky}" width="28" height="86" rx="2" fill="{BLACK_KEY}"/>')
    p.append(text_el(500, ky + kh + 58, "Czerwona naklejka to środkowe C – biały klawisz tuż na lewo "
                     "od dwóch czarnych.", 16.5, fill=TEXT_SOFT, anchor="middle", maxw=860))
    p.append(text_el(500, ky + kh + 80, "Naklejki w paski (na lewo od czerwonej) i ostatnie cztery w kropki "
                     "są potrzebne tylko w kilku piosenkach.", 14.5, fill=TEXT_SOFT, anchor="middle",
                     italic=True, maxw=860))

    # Karty z legendą: nagłówek u góry, rysunek w środku, opis na dole
    cards = []
    cw, ch_ = 280, 156
    gx0, gy0, gdx, gdy = 60, 360, 300, 168
    bw, bh, bk = 28, 42, 28 / QUARTER_W

    def card(col, row, heading, body, draw):
        x, y = gx0 + col * gdx, gy0 + row * gdy
        s = [f'<rect x="{x}" y="{y}" width="{cw}" height="{ch_}" rx="14" fill="#F7F4EF" stroke="#ECE6DC"/>']
        s.append(text_el(x + 16, y + 29, heading, 18, fill=TEXT, weight=700, maxw=cw - 30))
        for i, line in enumerate(body):
            s.append(text_el(x + 16, y + ch_ - 31 + i * 19, line, 14.5, fill=TEXT_SOFT, maxw=cw - 30))
        s.append(draw(x, y + 46))  # y = górna krawędź pola rysunku (wys. ~58)
        cards.append("".join(s))

    def kolory(x, y):
        return "".join(block_svg(x + 18 + i * 36, y + 4, bw, bh, key, False, 1, bk)
                       for i, key in enumerate(["C", "D", "E", "F", "G", "A", "H"]))
    card(0, 0, "Kolor = klawisz", ["Naciśnij klawisz z naklejką", "w tym samym kolorze."], kolory)

    def kropki(x, y):
        return "".join(block_svg(x + 18 + i * 38 + (i // 2) * 12, y + 4, bw, bh, key, False, 1, bk)
                       for i, key in enumerate(["C", "c", "D", "d", "H,", "H"]))
    card(1, 0, "Kropki wyżej, paski niżej", ["Kropki – klawisz dalej w prawo,", "paski – na lewo od czerwonej."],
         kropki)

    def dlugosc(x, y):
        out, xx = [], x + 18
        for d in (0.5, 1, 2, 4):
            w = d * 26 - 4
            out.append(block_svg(xx, y + 4, w, bh, "F", False, d, bk))
            xx += w + 10
        return "".join(out)
    card(2, 0, "Szerokość = jak długo", ["Wąski – krótko, szeroki – trzymaj", "klawisz dłużej."], dlugosc)

    def kontur(x, y):
        pts = [(x + 40, y + 46), (x + 92, y + 36), (x + 144, y + 26), (x + 196, y + 16)]
        line = [(x + 18, pts[0][1])] + pts + [(x + 218, pts[-1][1])]
        out = [f'<polyline points="{" ".join(f"{f1(a)},{f1(b)}" for a, b in line)}" fill="none" '
               f'stroke="{CORD}" stroke-width="{f1(CORD_W * bk)}" stroke-linecap="round" stroke-linejoin="round"/>']
        for (px, py), key in zip(pts, ["C", "D", "E", "F"]):
            out.append(block_svg(px - bw / 2, py - bh / 2 + 2, bw, bh - 4, key, False, 1, bk))
        return "".join(out)
    card(0, 1, "Klocek wyżej = dźwięk wyżej", ["Sznurek pokazuje, czy melodia", "idzie w górę, czy w dół."], kontur)

    def czarny(x, y):
        out = [block_svg(x + 22, y + 12, bw, bh, "c", True, 1, bk)]
        out.append(text_el(x + 62, y + 44, "=", 26, fill=TEXT, weight=500))
        kb, _ = mini_keyboard(x + 88, y + 4, 13, kw=15, kh=50)
        out.append(kb)
        return "".join(out)
    card(1, 1, "Czarna belka", ["Zagraj czarny klawisz tuż na", "prawo od tego koloru."], czarny)

    def powtorz(x, y):
        out = [f'<polyline points="{f1(x + 14)},{f1(y + 25)} {f1(x + 150)},{f1(y + 25)}" fill="none" stroke="{CORD}" '
               f'stroke-width="{f1(CORD_W * bk)}" stroke-linecap="round"/>']
        for i, key in enumerate(["G", "E", "C"]):
            out.append(block_svg(x + 24 + i * 40, y + 4, bw, bh, key, False, 1, bk))
        out.append(repeat_icon(x + 184, y + 25, 16))
        return "".join(out)
    card(2, 1, "Powtórka", ["Zagraj ten rząd drugi raz", "(z kolejnym wersem)."], powtorz)

    p.extend(cards)
    return svg_page(uid, "".join(p))


# --------------------------------------------------------------------------
# Składanie HTML
# --------------------------------------------------------------------------

def svg_page(pid: str, inner: str) -> str:
    return (f'<svg data-page="{pid}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {PAGE_W} {PAGE_H}" '
            f'font-family="{esc(FONT)}" role="img"><rect width="{PAGE_W}" height="{PAGE_H}" fill="#fff"/>{inner}</svg>')


CSS = """
*{box-sizing:border-box}
body{margin:0;background:#ECE6DC;font-family:Montserrat,'Segoe UI',Arial,sans-serif;color:#2B2929}
a,button{touch-action:manipulation;-webkit-tap-highlight-color:transparent}
.ico{font-family:'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji',sans-serif;font-weight:400;
  font-style:normal;line-height:1}
.bar{display:flex;gap:12px;align-items:center;justify-content:center;flex-wrap:wrap;padding:16px}
.bar a{display:inline-flex;align-items:center;gap:10px;min-height:56px;padding:0 24px 0 18px;
  font:700 18px Montserrat,'Segoe UI',Arial,sans-serif;color:#2B2929;background:#fff;border:2px solid #D8D0C4;
  border-radius:999px;text-decoration:none;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,.08);
  transition:transform .08s ease-out}
.bar .ico{font-size:26px}
.bar a:hover{background:#F7F4EF}
.bar a:active{transform:scale(.95)}
.bar a:focus-visible{outline:3px solid #2A6BC1;outline-offset:2px}
.bar.top{justify-content:flex-start;max-width:1720px;min-height:120px;margin:0 auto}
.spread{display:flex;justify-content:center;margin:0 auto 28px;max-width:1720px;padding:0 16px}
.spread.song{padding-top:120px}
.bar.top+.spread.song{padding-top:0}
.page{flex:1 1 0;max-width:860px;min-width:0;background:#fff;box-shadow:0 2px 14px rgba(0,0,0,.12)}
.page+.page{border-left:1px solid #EEE9E2}
.page svg{display:block;width:100%;height:auto}
.spread.single .page{flex:0 1 860px}
.page{position:relative;container-type:inline-size}
.player{position:absolute;right:0;bottom:calc(100% + 16px);display:flex;align-items:center;gap:14px;z-index:2}
.player button{display:grid;place-items:center;padding:0;border-radius:50%;cursor:pointer;
  font:32px/1 'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji',sans-serif;
  box-shadow:0 3px 10px rgba(0,0,0,.18);transition:transform .08s ease-out}
.player button:active{transform:scale(.92)}
.player .play{width:88px;height:88px;border:0;background:#5DAE35;color:#fff}
.player .play:hover{background:#4E9A2C}
.player .play.on{background:#E3262B}
.player .play svg{width:46%;height:46%;fill:currentColor}
.player .play .count{font:800 40px/1 Montserrat,'Segoe UI',Arial,sans-serif}
.player .opt{width:68px;height:68px;background:#fff;border:3px solid #E5DED3;color:#2B2929}
.player .opt[aria-pressed="true"]{background:#FFF4D6;border-color:#F5D23A}
.player button:focus-visible{outline:3px solid #2A6BC1;outline-offset:3px}
.blk{transition:transform .05s ease-out,filter .05s ease-out;transform-box:fill-box;transform-origin:center}
.blk.on{transform:translateY(-10%) scale(1.14);filter:drop-shadow(0 5px 5px rgba(0,0,0,.35))}
.syl-hl{opacity:0;pointer-events:none}
.syl-hl.on{opacity:1}
.lyrics text.lyr{transition:opacity .3s}
.lyrics svg.sing text.lyr:not(.cur){opacity:.35}
.lyrics text[data-at]{cursor:pointer}
.hero{text-align:center;padding:28px 16px 4px}
.hero h1{margin:0 0 10px;font-size:clamp(36px,7vw,60px);font-weight:800;letter-spacing:1px;line-height:1.1}
.hero .lead{max-width:640px;margin:0 auto;color:#6B6460;font-size:17px;line-height:1.45}
.levels{max-width:1240px;margin:0 auto 56px;padding:0 16px}
.level h2{display:flex;align-items:center;gap:12px;margin:30px 4px 14px;font-size:clamp(21px,3.2vw,27px)}
.level h2 .ico{font-size:.95em;letter-spacing:-2px}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(clamp(140px,30vw,210px),1fr));gap:16px}
.tile{position:relative;display:flex;flex-direction:column;background:#fff;border-radius:24px;overflow:hidden;
  text-decoration:none;color:#2B2929;box-shadow:0 2px 10px rgba(0,0,0,.1);border-bottom:8px solid var(--c);
  transition:transform .12s ease-out,box-shadow .12s ease-out}
.tile:hover{transform:translateY(-3px);box-shadow:0 8px 20px rgba(0,0,0,.14)}
.tile:active{transform:scale(.96)}
.tile:focus-visible{outline:4px solid #2A6BC1;outline-offset:3px}
.tile .pic{position:relative;display:grid;place-items:center;aspect-ratio:3/2;
  background:radial-gradient(circle at 46% 46%,#fff 0 20%,var(--t) 60%,var(--t2) 100%)}
.tile .pic b{font-size:clamp(52px,9vw,76px)}
.tile .pic i{position:absolute;right:12%;top:10%;font-size:clamp(22px,3.6vw,30px)}
.tile .lvl{position:absolute;left:10px;top:10px;font-size:15px;letter-spacing:-3px}
.tile .name{flex:1;display:flex;align-items:center;justify-content:center;padding:12px 12px 8px;
  text-align:center;font-weight:700;font-size:clamp(15px,2.1vw,18px);line-height:1.25}
.tile .mel{display:block;padding:0 14px 14px}
.tile .mel svg{display:block;width:100%;height:clamp(34px,4.8vw,50px)}
@media (max-width:900px){.spread{flex-direction:column;align-items:center}.page{width:100%}
  .page+.page{border-left:0;margin-top:12px}
  .spread.song{padding-top:0}.spread.song .melody{margin-top:120px}
  .player{right:50%;transform:translateX(50%)}
  .bar.top{justify-content:center;min-height:0}}
@media (max-width:520px){
  .bar a{min-height:52px;padding:0 18px 0 14px;font-size:16px}
  .bar .ico{font-size:22px}
  .hero .lead{font-size:15px}
  .player .play{width:76px;height:76px}
  .player .opt{width:60px;height:60px;font-size:28px}
  .spread.song .melody{margin-top:108px}
  .tiles{gap:12px}.tile{border-radius:20px}}
@media print{
  @page{size:A4 landscape;margin:0}
  body{background:#fff}
  .bar,.hero,.levels,.player,.syl-hl{display:none}
  .lyrics svg text.lyr{opacity:1!important}
  .spread{display:block;max-width:none;margin:0;padding:0!important}
  .page{max-width:none;width:297mm;height:210mm;box-shadow:none;border:0!important;margin:0!important;
    overflow:hidden;break-after:page;page-break-after:always}
  .spread:last-of-type .page:last-child{break-after:auto;page-break-after:auto}
  .page svg{width:297mm;height:210mm}
}
"""

# Dopasowanie tekstów po wczytaniu czcionki: tytuły osobno, słowa jedną wspólną skalą.
FIT_JS = """
(function(){
  function fit(){
    var changes = [];
    document.querySelectorAll('svg[data-page]').forEach(function(svg){
      var group = [], ratio = 1;
      svg.querySelectorAll('text[data-maxw]').forEach(function(t){
        var max = +t.getAttribute('data-maxw'), base = +t.getAttribute('data-fs'), w = t.getComputedTextLength();
        if(t.hasAttribute('data-group')){ group.push(t); if(w > max) ratio = Math.min(ratio, max / w); }
        else if(w > max){ changes.push([t, base * max / w]); }
      });
      if(ratio < 1) group.forEach(function(t){ changes.push([t, +t.getAttribute('data-fs') * ratio]); });
    });
    changes.forEach(function(c){ c[0].setAttribute('font-size', c[1].toFixed(2)); });
  }
  if(document.fonts && document.fonts.ready){ document.fonts.ready.then(fit); } else { window.addEventListener('load', fit); }
})();
"""

# Odtwarzacz: proste „pianino” z Web Audio, podświetla grany klocek i śpiewaną sylabę w słowach.
# Dane: atrybut data-play strony. Przycisk 🔇 = dziecko gra samo: odliczanie i animacja w tempie, bez dźwięku.
# Podświetlenie liczymy z zegara audio (z poprawką na opóźnienie głośnika), a granie startuje dopiero,
# gdy ten zegar naprawdę ruszy – przy pierwszym kliknięciu urządzenie dźwiękowe startuje z opóźnieniem.
PLAY_JS = """
(function(){
  var ctx = null, master = null, current = null;
  var LEAD = 0.2;          // zapas przed pierwszą nutą (s) – klatki animacji zdążą się ustabilizować
  var AHEAD = 1.5;         // nuty planujemy na bieżąco, najwyżej tyle sekund do przodu
  var CLOCK_WAIT = 1500;   // najdłużej czekamy na start zegara audio (ms), potem gramy bez dźwięku
  var BEAT_MIN = 0.375;    // krótszych ćwierćnut (tempo > 160) nie odliczamy – liczymy co półnutę
  var SMOOTH = 0.3;        // wygładzanie zegara audio (s) – na telefonach jego odczyt skacze o kilkadziesiąt ms
  var SNAP = 0.1;          // większy skok to prawdziwa zmiana opóźnienia (np. słuchawki) – przyjmujemy od razu
  var ICON_PLAY = '<svg viewBox="0 0 24 24"><path d="M7 4.5v15l12.5-7.5z"/></svg>';
  var ICON_STOP = '<svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';
  function audio(){
    if(!ctx){
      var AC = window.AudioContext || window.webkitAudioContext;
      if(!AC) return null;
      ctx = new AC(); master = ctx.createGain(); master.gain.value = 0.5;
      var comp = ctx.createDynamicsCompressor(); master.connect(comp); comp.connect(ctx.destination);
    }
    return ctx;
  }
  function tone(bus, t, semi, len){
    var f = 261.6256 * Math.pow(2, semi / 12), g = ctx.createGain(), hold = Math.max(0.06, len - 0.035);
    g.connect(bus);
    [[1, 'triangle', 0.6], [2, 'sine', 0.2], [3, 'sine', 0.07]].forEach(function(h){
      var o = ctx.createOscillator(), og = ctx.createGain();
      o.type = h[1]; o.frequency.value = f * h[0]; og.gain.value = h[2];
      o.connect(og); og.connect(g); o.start(t); o.stop(t + hold + 0.3);
    });
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(1, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.25, t + hold);
    g.gain.exponentialRampToValueAtTime(0.0001, t + hold + 0.22);
  }
  // Czas zegara audio, który właśnie słychać z głośnika (uwzględnia opóźnienie wyjścia, np. Bluetooth).
  function heardTime(){
    if(ctx.getOutputTimestamp){
      var ts = ctx.getOutputTimestamp();
      if(ts && ts.contextTime > 0 && ts.performanceTime > 0){
        return ts.contextTime + Math.max(0, performance.now() - ts.performanceTime) / 1000;
      }
    }
    return ctx.currentTime - (ctx.outputLatency || ctx.baseLatency || 0);
  }
  // Czeka, aż zegar audio zacznie płynąć; done(true) gdy płynie, done(false) gdy nie ruszył w CLOCK_WAIT.
  function waitForClock(s, done){
    var c0 = ctx.currentTime, t0 = performance.now();
    (function check(){
      if(current !== s) return;
      if(ctx.state === 'running' && ctx.currentTime - c0 >= 0.03) return done(true);
      if(performance.now() - t0 > CLOCK_WAIT) return done(false);
      setTimeout(check, 10);
    })();
  }
  function pressed(page, sel){
    var b = page.querySelector(sel);
    return !!b && b.getAttribute('aria-pressed') === 'true';
  }
  function setButton(page, on, count){
    var b = page.querySelector('.play');
    b.classList.toggle('on', on);
    b.innerHTML = count ? '<span class="count">' + count + '</span>' : on ? ICON_STOP : ICON_PLAY;
    b.setAttribute('aria-label', on ? 'Zatrzymaj' : 'Zagraj melodię');
    b.title = on ? 'Zatrzymaj' : 'Zagraj';
  }
  // Słowa na lewej stronie: śpiewana sylaba dostaje tło w kolorze klocka, pozostałe zwrotki bledną.
  function lyricsOf(page){
    var spread = page.closest('.spread'), svg = spread && spread.querySelector('.lyrics svg');
    if(!svg || !svg.querySelector('tspan[data-s]')) return null;
    var L = {svg: svg, syl: {}, on: null, st: null, hl: svg.querySelector('.syl-hl')};
    if(!L.hl){
      var first = svg.querySelector('text.lyr');
      L.hl = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      L.hl.setAttribute('class', 'syl-hl');
      first.parentNode.insertBefore(L.hl, first);
    }
    svg.querySelectorAll('tspan[data-s]').forEach(function(t){ L.syl[t.getAttribute('data-s')] = t; });
    svg.classList.add('sing');
    return L;
  }
  function stanza(L, st){
    if(st == null || st === L.st) return;
    L.st = st;
    L.svg.querySelectorAll('text.lyr').forEach(function(t){ t.classList.toggle('cur', t.getAttribute('data-st') === st); });
  }
  function bright(c){  // jasna naklejka (żółta) – na niej ciemny tekst
    var n = parseInt(c.slice(1), 16);
    return ((n >> 16) * 299 + (n >> 8 & 255) * 587 + (n & 255) * 114) / 1000 > 160;
  }
  function sing(L, sid, block){
    if(L.on){ L.on.classList.remove('on'); L.on.style.fill = ''; L.on = null; }
    var t = sid >= 0 && L.syl[sid];
    if(!t || !block){ L.hl.classList.remove('on'); return; }
    var line = t.parentNode, fs = parseFloat(line.getAttribute('font-size')), r = t.getBBox();
    var color = block.querySelector('rect').getAttribute('fill');
    L.hl.setAttribute('x', r.x - fs * .16); L.hl.setAttribute('width', r.width + fs * .32);
    L.hl.setAttribute('y', r.y - fs * .04); L.hl.setAttribute('height', r.height + fs * .08);
    L.hl.setAttribute('rx', fs * .28); L.hl.setAttribute('fill', color);
    L.hl.classList.add('on');
    t.classList.add('on'); t.style.fill = bright(color) ? '#2B2929' : '#fff';
    L.on = t;
    stanza(L, line.getAttribute('data-st'));
  }
  function clearLyrics(L){
    if(!L) return;
    sing(L, -1, null);
    L.svg.classList.remove('sing');
    L.svg.querySelectorAll('text.lyr.cur').forEach(function(t){ t.classList.remove('cur'); });
  }
  function hop(el){  // podskok klocka przy odliczaniu
    if(el && el.animate) el.animate([{transform: 'none'}, {transform: 'translateY(-8%) scale(1.08)'},
                                     {transform: 'none'}], {duration: 200, easing: 'ease-out'});
  }
  function stop(){
    if(!current) return;
    var s = current; current = null;
    cancelAnimationFrame(s.raf);
    clearInterval(s.timer);
    if(s.bus){
      s.bus.gain.setTargetAtTime(0, ctx.currentTime, 0.015);
      setTimeout(function(){ s.bus.disconnect(); }, 300);
    }
    s.page.querySelectorAll('.blk.on').forEach(function(b){ b.classList.remove('on'); });
    clearLyrics(s.lyrics);
    setButton(s.page, false);
  }
  function toggle(page){
    if(current && current.page === page) stop(); else play(page, 0);
  }
  // Gra od nuty nr `from` (0 = od początku; kliknięty wers słów = od tego wersu).
  function play(page, from){
    stop();
    var data = JSON.parse(page.getAttribute('data-play'));
    var q = 60 / data.tempo * (pressed(page, '.slow') ? 1.6 : 1), rel = 0, events = [];
    data.seq.slice(from).forEach(function(ev){
      var len = ev[1] * q;
      events.push([rel, rel + len, ev[2], ev[0], ev[3]]);
      rel += len;
    });
    var s = {page: page, from: from, events: events, end: rel, q: q, count: 0, beat: q, bus: null, raf: 0, timer: 0,
             next: 0, clock: null, lyrics: lyricsOf(page)};
    current = s;
    setButton(page, true);  // przycisk reaguje od razu, granie rusza razem z dźwiękiem
    if(pressed(page, '.mute')){  // dziecko gra samo: odliczanie, potem sama animacja w tempie, bez dźwięku
      s.count = data.count || 4;
      if(q < BEAT_MIN && s.count % 2 === 0) s.beat = 2 * q;  // szybka piosenka: liczymy co półnutę
      startSilent(s);
      return;
    }
    if(!audio()){ startSilent(s); return; }
    var resumed = ctx.state === 'running' ? Promise.resolve() : ctx.resume();
    Promise.resolve(resumed).catch(function(){}).then(function(){
      waitForClock(s, function(ok){
        if(current !== s) return;  // w międzyczasie kliknięto stop albo inną piosenkę
        if(ok) startAudio(s); else startSilent(s);
      });
    });
  }
  function startAudio(s){
    s.bus = ctx.createGain();
    s.bus.connect(master);
    s.t0 = ctx.currentTime + LEAD;
    // Zegar strony + przesunięcie do zegara audio, które zmieniamy powoli. Na telefonach (Android) odczyt
    // zegara audio skacze w obie strony, a surowy cofał się przez granicę nut – klocki mrugały.
    var off = null, at = 0;
    s.clock = function(){
      var wall = performance.now() / 1000, raw = heardTime() - wall;
      if(off === null || Math.abs(raw - off) > SNAP) off = raw;
      else off += (raw - off) * Math.min(1, (wall - at) / SMOOTH);
      at = wall;
      return wall + off - s.t0;
    };
    schedule(s);
    s.timer = setInterval(function(){ schedule(s); }, 50);
    animate(s);
  }
  // Planuje tylko najbliższe nuty – kliknięcie nie blokuje strony i żadna nuta nie trafia „w przeszłość”.
  function schedule(s){
    if(current !== s) return;
    var horizon = ctx.currentTime + AHEAD;
    while(s.next < s.events.length && s.t0 + s.events[s.next][0] < horizon){
      var e = s.events[s.next++];
      if(e[3] !== null) tone(s.bus, Math.max(s.t0 + e[0], ctx.currentTime), e[3], e[1] - e[0]);
    }
    if(s.next >= s.events.length) clearInterval(s.timer);
  }
  // Bez dźwięku (granie samemu albo brak urządzenia audio): animacja na zegarze strony, po odliczeniu s.count uderzeń.
  function startSilent(s){
    var w0 = performance.now() / 1000 + LEAD + s.count * s.beat;
    s.clock = function(){ return performance.now() / 1000 - w0; };
    animate(s);
  }
  function animate(s){
    var blocks = {}, lit = -1, block = null, shown = 0, first = null, last = -Infinity, events = s.events, L = s.lyrics, i;
    s.page.querySelectorAll('.blk').forEach(function(b){ blocks[b.getAttribute('data-n')] = b; });
    for(i = 0; i < events.length && !first; i++) first = blocks[events[i][2]];
    for(i = 0; L && i < events.length; i++){  // od razu widać, którą zwrotkę się śpiewa
      if(L.syl[events[i][4]]){ stanza(L, L.syl[events[i][4]].parentNode.getAttribute('data-st')); break; }
    }
    (function frame(){
      if(current !== s) return;
      var now = last = Math.max(last, s.clock()), idx = -1;  // czas nie cofa się: poprzedni klocek nie wraca
      if(s.count && now < 0){  // odliczanie: liczba na przycisku, pierwszy klocek podskakuje w takt
        var left = Math.ceil(-now / s.beat);
        if(left <= s.count && left !== shown){ shown = left; setButton(s.page, true, left); hop(first); }
      } else if(shown){
        shown = 0; setButton(s.page, true);
      }
      for(var i = 0; i < events.length; i++){
        if(now >= events[i][0] && now < events[i][1]){ idx = i; break; }
      }
      if(idx !== lit){
        if(block) block.classList.remove('on');
        block = idx < 0 ? null : blocks[events[idx][2]] || null;
        if(block) block.classList.add('on');
        if(L) sing(L, idx < 0 ? -1 : events[idx][4], block);
        lit = idx;
      }
      if(now > s.end + 0.05){ stop(); return; }
      s.raf = requestAnimationFrame(frame);
    })();
  }
  document.querySelectorAll('.melody .play').forEach(function(b){ b.innerHTML = ICON_PLAY; });
  document.addEventListener('click', function(e){
    var el = e.target.closest && e.target.closest('.player button, .lyrics text[data-at]');
    if(!el) return;
    if(!el.closest('.player')){  // kliknięty wers słów – graj od niego
      var mel = el.closest('.spread').querySelector('.melody');
      if(mel) play(mel, +el.getAttribute('data-at'));
      return;
    }
    var page = el.closest('.melody');
    if(el.classList.contains('opt')){  // 🐢 / 🔇: przełącz i zacznij od nowa, jeśli właśnie gra
      el.setAttribute('aria-pressed', el.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
      if(current && current.page === page) play(page, current.from);
    } else {
      toggle(page);
    }
  });
  document.addEventListener('keydown', function(e){
    var pages = document.querySelectorAll('.melody');
    if(e.code === 'Space' && pages.length === 1 && !/^(INPUT|TEXTAREA|BUTTON)$/.test(e.target.tagName)){
      e.preventDefault(); toggle(pages[0]);
    }
  });
})();
"""


def html_doc(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,400;0,500;0,700;0,800;1,400&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
{body}
<script>{FIT_JS}</script>
<script>{PLAY_JS}</script>
</body>
</html>
"""


def toolbar(*links: tuple[str, str, str], top: bool = False) -> str:
    """Pasek dużych przycisków (ikona, napis, adres). Do druku służy PDF książeczki (--pdf).
    top=True: pasek nad rozkładówką jednej piosenki – po prawej, nad melodią, stoi w nim odtwarzacz."""
    a = "".join(f'<a href="{esc(h)}"><span class="ico" aria-hidden="true">{i}</span>{esc(t)}</a>'
                for i, t, h in links)
    return f'<div class="bar{" top" if top else ""}">{a}</div>'


def spread_html(song: Song, page_no: int | None) -> str:
    uid = uid_of(song.slug)
    left = render_lyrics_page(song, uid, page_no)
    right = render_melody_page(song, uid)
    # seq: [półton od środkowego C | None, długość w ćwierćnutach, nr klocka (data-n) | -1, nr sylaby (data-s) | -1]
    data = json.dumps({"tempo": song.tempo, "count": count_in(song), "seq": song.seq}, separators=(",", ":"))
    player = ('<div class="player">'
              '<button class="opt slow" type="button" aria-pressed="false" title="Wolniej" '
              'aria-label="Wolniej">🐢</button>'
              '<button class="opt mute" type="button" aria-pressed="false" title="Graj sam – bez dźwięku" '
              'aria-label="Graj sam, bez dźwięku">🔇</button>'
              '<button class="play" type="button" title="Zagraj" aria-label="Zagraj melodię">▶</button>'
              '</div>')
    return (f'<div class="spread song"><div class="page lyrics">{left}</div>'
            f'<div class="page melody" data-play="{esc(data)}">{player}{right}</div></div>')


# --------------------------------------------------------------------------
# Spis piosenek: od najłatwiejszej do najtrudniejszej
# --------------------------------------------------------------------------

# Poziomy w spisie: (ocena trudności poniżej, gwiazdki, nagłówek). Ocenę liczy difficulty().
LEVELS = [(12.0, "⭐", "Na dobry początek"), (14.2, "⭐⭐", "Trochę trudniejsze"),
          (math.inf, "⭐⭐⭐", "Dla wprawnych")]


def played_notes(song: Song) -> list[Note]:
    """Dźwięki melodii w kolejności grania (rząd z ↻ dwa razy), bez pauz."""
    return [n for r in song.rows for n in r.notes * (2 if r.repeat else 1) if n.semi is not None]


def difficulty(song: Song) -> float:
    """Ocena trudności melodii dla dziecka, które gra z naklejek – im więcej, tym trudniej.
    Liczą się: liczba dźwięków (dziesięć to 1 punkt), liczba różnych klawiszy, czarne klawisze
    (najmocniej), dodatkowe naklejki spoza C–e, skoki o 3 białe klawisze i więcej oraz bardzo
    krótkie nuty w szybkim tempie."""
    notes = played_notes(song)
    semis = [n.semi + song.transpose for n in notes]
    black = [s for s in semis if KEYS[s][2]]
    steps = [KEYS[s][1] for s in semis]
    jumps = sum(1 for a, b in zip(steps, steps[1:]) if abs(a - b) >= 3)
    fastest = min(n.dur for n in notes) * 60 / song.tempo  # najkrótsza nuta w sekundach
    return (len(semis) / 10 + 0.8 * len(set(semis)) + 3.5 * len(set(black)) + 0.3 * len(black)
            + 1.0 * len(extra_keys(song)) + 0.25 * jumps + 4 * max(0.0, 0.45 - fastest))


def level_of(song: Song) -> int:
    score = difficulty(song)
    return next(i for i, (limit, _, _) in enumerate(LEVELS) if score < limit)


def melody_preview(song: Song, quarters: float = 8) -> str:
    """Początek melodii (ok. dwóch taktów, do pierwszej przerwy) jako małe klocki na sznurku – do kafelka."""
    row = song.rows[0]
    items, total = [], 0.0  # [nuta, długość klocka]
    for nt, sound in zip(row.notes, bar_sound(row)):
        if total >= quarters or (items and not sound):  # takt z samą pauzą = przerwa na sznurku
            break
        total += nt.dur
        if nt.semi is not None:
            items.append([nt, nt.dur])
        elif items:
            items[-1][1] += nt.dur  # pauza w takcie z nutami poszerza klocek przed nią (jak na stronie)
    keys = [song.key_of(nt) for nt, _ in items]
    smin, smax = min(k[1] for k in keys), max(k[1] for k in keys)
    top = SHARP_OVER * BLOCK_H if any(k[2] for k in keys) else 0
    step_h = 0.7 * STEP  # spłaszczone w pionie, żeby kafelki miały podobne miniatury
    x = CORD_W / 2 + CORD_EXT
    blocks, pts = [], []
    for nt, held in items:
        key, step, sharp = song.key_of(nt)
        w, y = held * UNIT - GAP, top + (smax - step) * step_h
        blocks.append(block_svg(x, y, w, BLOCK_H, key, sharp, held))
        pts.append((x + w / 2, y + BLOCK_H / 2))
        x += held * UNIT
    width = x - GAP + CORD_EXT + CORD_W / 2
    cord = [(CORD_W / 2, pts[0][1])] + pts + [(width - CORD_W / 2, pts[-1][1])]
    return (f'<svg viewBox="0 0 {f1(width)} {f1(top + (smax - smin) * step_h + BLOCK_H)}" aria-hidden="true">'
            f'<polyline points="{" ".join(f"{f1(px)},{f1(py)}" for px, py in cord)}" fill="none" '
            f'stroke="{CORD}" stroke-width="{f1(CORD_W)}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'{"".join(blocks)}</svg>')


def song_tile(song: Song) -> str:
    """Kafelek piosenki: duża ilustracja w kolorze piosenki, tytuł i początek melodii w klockach."""
    c = COLORS[theme_key_of(song)]
    spec = song.illustration.strip()
    is_image = re.search(r"\.(png|jpe?g|gif|svg|webp)$", spec, re.I)
    emojis = spec.split() if spec and not is_image else ["🎵"]
    stars = LEVELS[level_of(song)][1]
    pic = (f'<span class="lvl ico">{stars}</span><b class="ico">{esc(emojis[0])}</b>'
           + (f'<i class="ico">{esc(emojis[1])}</i>' if len(emojis) > 1 else ""))
    return (f'<a class="tile" href="{esc(song.slug)}.html" style="--c:{c};--t:{mix(c, "#FFFFFF", .8)};'
            f'--t2:{mix(c, "#FFFFFF", .6)}"><span class="pic" aria-hidden="true">{pic}</span>'
            f'<span class="name">{esc(song.title)}</span><span class="mel">{melody_preview(song)}</span></a>')


def rainbow(text: str) -> str:
    """Napis w kolorach naklejek (bez żółtej – słabo ją widać na jasnym tle)."""
    cycle = ["C", "G", "D", "F", "E", "A"]
    out, i = [], 0
    for ch in text:
        if ch == " ":
            out.append(" ")
            continue
        out.append(f'<span style="color:{COLORS[cycle[i % len(cycle)]]}">{esc(ch)}</span>')
        i += 1
    return "".join(out)


def index_html(all_songs: list[Song]) -> str:
    """Spis piosenek: kafelki w trzech poziomach, w każdym od najłatwiejszej."""
    groups: dict[int, list[Song]] = {}
    for s in sorted(all_songs, key=difficulty):  # przy równej ocenie zostaje kolejność plików
        groups.setdefault(level_of(s), []).append(s)
    levels = "".join(
        f'<section class="level"><h2><span class="ico" aria-hidden="true">{LEVELS[i][1]}</span>'
        f'{esc(LEVELS[i][2])}</h2><div class="tiles">{"".join(song_tile(s) for s in groups[i])}</div></section>'
        for i in sorted(groups))
    return (
        f'<header class="hero"><h1 aria-label="Kolorowe pianino">{rainbow("Kolorowe pianino")}</h1>'
        '<p class="lead">Piosenki do grania z kolorowymi naklejkami, od najłatwiejszej do najtrudniejszej. '
        'Każda piosenka to rozkładówka: słowa po lewej, kolorowe klocki po prawej.</p></header>'
        '<nav class="bar"><a href="jak-grac.html"><span class="ico" aria-hidden="true">❓</span>Jak grać?</a>'
        '<a href="pdf/ksiazeczka.pdf"><span class="ico" aria-hidden="true">📖</span>Cała książeczka (do druku)</a>'
        f'</nav><main class="levels">{levels}</main>'
    )


def build(songs: list[Song], all_songs: list[Song]) -> list[Path]:
    OUT_DIR.mkdir(exist_ok=True)
    numbers = {s.slug: 2 + 2 * i for i, s in enumerate(all_songs)}
    written = []
    for song in songs:
        body = toolbar(("🏠", "Piosenki", "index.html"), ("❓", "Jak grać?", "jak-grac.html"), top=True) + \
            spread_html(song, numbers.get(song.slug))
        out = OUT_DIR / f"{song.slug}.html"
        out.write_text(html_doc(f"{song.title} – Kolorowe pianino", body), encoding="utf-8")
        written.append(out)

    howto = f'<div class="spread single"><div class="page">{render_howto_page()}</div></div>'
    (OUT_DIR / "jak-grac.html").write_text(
        html_doc("Jak grać? – Kolorowe pianino", toolbar(("🏠", "Piosenki", "index.html")) + howto),
        encoding="utf-8")

    book = howto + "".join(spread_html(s, numbers[s.slug]) for s in all_songs)
    (OUT_DIR / "ksiazeczka.html").write_text(
        html_doc("Kolorowe pianino – książeczka", toolbar(("🏠", "Piosenki", "index.html")) + book),
        encoding="utf-8")

    (OUT_DIR / "index.html").write_text(html_doc("Kolorowe pianino", index_html(all_songs)), encoding="utf-8")
    return written



# --------------------------------------------------------------------------
# PDF przez przeglądarkę w trybie headless (Edge / Chrome / Chromium)
# --------------------------------------------------------------------------

def find_browser() -> str | None:
    candidates = [
        os.environ.get("KOLOROWE_PIANINO_BROWSER", ""),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for name in ("msedge", "google-chrome", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    return next((c for c in candidates if c and Path(c).is_file()), None)


def to_pdf(browser: str, html_path: Path, pdf_path: Path) -> bool:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()
    profile = tempfile.mkdtemp(prefix="kolorowe-pianino-")
    cmd = [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
           "--print-to-pdf-no-header", f"--user-data-dir={profile}", "--virtual-time-budget=8000",
           f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"BŁĄD: nie udało się utworzyć {pdf_path.name}: {e}", file=sys.stderr)
        return False
    # Edge/Chrome potrafi zakończyć proces startowy, zanim drugi proces zapisze PDF – czekamy na plik.
    size, stable = -1, 0
    for _ in range(120):
        if pdf_path.is_file():
            now = pdf_path.stat().st_size
            stable = stable + 1 if now == size and now > 0 else 0
            size = now
            if stable >= 2:
                break
        time.sleep(0.25)
    shutil.rmtree(profile, ignore_errors=True)  # profil bywa jeszcze chwilę zajęty – to nie błąd
    if not pdf_path.is_file():
        print(f"BŁĄD: przeglądarka nie utworzyła {pdf_path.name}", file=sys.stderr)
        return False
    return True

# --------------------------------------------------------------------------
# Raport tekstowy (--sprawdz)
# --------------------------------------------------------------------------

DUR_WORDS = {0.5: "ósemka", 0.75: "ósemka z kropką", 1: "ćwierćnuta", 1.5: "ćwierćnuta z kropką",
             2: "półnuta", 3: "półnuta z kropką", 4: "cała nuta"}


def describe(song: Song) -> str:
    lines = [f"„{song.title}” ({song.path.name})"]
    semis = [n.semi + song.transpose for n in song.all_notes()]
    def name(semi):
        key, _, sharp = KEYS[semi]
        return key + ("#" if sharp else "")
    lines.append(f"  zakres: {name(min(semis))}–{name(max(semis))}, "
                 f"czarne klawisze: {sum(1 for s in semis if KEYS[s][2])}, transpozycja: {song.transpose:+d}")
    extras = extra_keys(song)
    if extras:
        lines.append("  dodatkowe naklejki spoza C–e: " + ", ".join(f"{k} ({key_words(k)})" for k in extras))
    q = 60 / song.tempo
    secs = sum(n.dur for r in song.rows for n in r.notes * (2 if r.repeat else 1)) * q
    q_s = f"{q:.2f}".replace(".", ",")
    lines.append(f"  tempo: {song.tempo} ćw./min (ćwierćnuta {q_s} s), melodia raz: {secs:.0f} s")
    _, stars, group = LEVELS[level_of(song)]
    lines.append(f"  trudność: {difficulty(song):.1f}".replace(".", ",") + f" – w spisie {stars} „{group}”")
    for i, row in enumerate(song.rows, 1):
        words = []
        for n, sound in zip(row.notes, bar_sound(row)):
            if n.semi is None:
                how = " – poszerza klocek" if sound and words else "" if sound else " – przerwa na sznurku"
                words.append(f"(pauza {fmt_q(n.dur)}{how})")
                continue
            key, _, sharp = song.key_of(n)
            w = key_words(key) + (" +czarna belka" if sharp else "")
            size = {0.5: "wąski", 0.75: "wąski+", 1: "zwykły", 1.5: "szerszy", 2: "szeroki",
                    3: "b. szeroki", 4: "najszerszy"}.get(n.dur, fmt_q(n.dur))
            words.append(f"{w} [{size}]")
        total = sum(n.dur for n in row.notes)
        lines.append(f"  rząd {i} ({fmt_q(total)} ćw.{' ↻' if row.repeat else ''}): " + ", ".join(words))
    syls = {x.sid: x for st in song.stanzas for ln in st for x in ln.syls}
    if syls:
        lines.append("  słowa do nut (przejście melodii.rząd: sylaby, „_” = ta sama sylaba na kolejnej nucie):")
        seen = set()
        for pn, ri, sids in song.sung:
            again = " ↻" if (pn, ri) in seen else ""
            seen.add((pn, ri))
            words, prev = [], None
            for sid in sids:
                x = syls[sid]
                if sid == prev:
                    words.append("_")
                else:
                    sep = " " if x.first else "" if words[-1:] == ["_"] else "-"
                    words.append((sep if words else "") + x.text.strip())
                prev = sid
            lines.append(f"    {pn}.{ri + 1}{again}: {''.join(words) or '(bez słów)'}")
    opts = transpositions(song)
    if opts:
        lines.append("  możliwe transpozycje względem zapisu (półtony / czarne klawisze, najpierw w C–e): " +
                     ", ".join(fmt_transposition(o) for o in opts[:8]))
    for w in song.warnings:
        lines.append(f"  UWAGA: {w}")
    return "\n".join(lines)


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Generator stron „Kolorowe pianino”.")
    ap.add_argument("pliki", nargs="*", help="pliki piosenek (domyślnie wszystkie z katalogu piosenki/)")
    ap.add_argument("--sprawdz", action="store_true", help="tylko sprawdź i opisz piosenki, nie generuj stron")
    ap.add_argument("--pdf", action="store_true",
                    help="utwórz też strony/pdf/ksiazeczka.pdf do druku (wymaga Edge/Chrome)")
    args = ap.parse_args(argv)

    all_paths = sorted(SONGS_DIR.glob("*.txt"))
    chosen = [Path(p).resolve() for p in args.pliki] if args.pliki else all_paths

    errors = 0
    parsed: dict[Path, Song] = {}
    for p in sorted(set(all_paths) | set(chosen)):
        try:
            parsed[p] = parse_song(p)
        except SongError as e:
            errors += 1
            print(f"BŁĄD: {e}", file=sys.stderr)
        except OSError as e:
            errors += 1
            print(f"BŁĄD: nie mogę otworzyć {p}: {e}", file=sys.stderr)

    songs = [parsed[p] for p in chosen if p in parsed]
    if args.sprawdz:
        for s in songs:
            render_melody_page(s, uid_of(s.slug))  # zbiera ostrzeżenia o układzie strony
            print(describe(s))
        return 1 if errors else 0

    all_songs = [parsed[p] for p in all_paths if p in parsed]
    for s in songs:
        if s not in all_songs:
            all_songs.append(s)
    written = build(songs, all_songs)
    for s, out in zip(songs, written):
        status = "" if not s.warnings else "  – " + "; ".join(s.warnings)
        print(f"OK  {out.relative_to(ROOT)}{status}")
    print(f"     {(OUT_DIR / 'index.html').relative_to(ROOT)}, ksiazeczka.html, jak-grac.html")
    if args.pdf:
        browser = find_browser()
        if not browser:
            print("BŁĄD: nie znaleziono Edge/Chrome – ustaw KOLOROWE_PIANINO_BROWSER albo drukuj z przeglądarki",
                  file=sys.stderr)
            return 1
        pdf = OUT_DIR / "pdf" / "ksiazeczka.pdf"  # tylko cała książeczka – spis linkuje prosto do niej
        if to_pdf(browser, OUT_DIR / "ksiazeczka.html", pdf):
            print(f"PDF {pdf.relative_to(ROOT)}")
        else:
            errors += 1
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
