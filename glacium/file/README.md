

# Framework Conventions

Diese Konventionen gelten für das gesamte Framework.

Ziel ist **Vorhersagbarkeit**:

* Man weiß, wo etwas liegt
* Man erkennt, was Interface ist
* Man erkennt, was Implementierung ist
* Man erkennt, was Test / Fake ist

Kein implizites Wissen. Keine Magie.

---

## 1. Grundprinzip

Das Framework folgt strikt diesem Muster:

* Interface (ABC)
* Fake (für Tests)
* Implementation (echtes Backend)

Jede dieser Rollen hat einen festen, eindeutigen Ort im Projektbaum.

---

## 2. Dateistruktur (verbindlich)

Jede funktionale Domäne (z.B. `convert`, `store`, `parse`, `meta`) folgt **derselben Struktur**.

### Grundlayout

<domain>/

* api.py
  Interfaces (ABCs) und kleine, geteilte Datentypen
* select.py
  Registry / Selector / Wiring (optional)
* impl/
  Konkrete Implementierungen
* test/
  Tests und Fakes

Innerhalb der Unterordner:

* impl/

  * *.py (reale Backends, Formate, Adapter)
* test/

  * fake.py (Fakes / Test-Doubles)

---

### Beispiele

convert/

* api.py
* select.py
* impl/

  * drop.py
  * converg.py
* test/

  * fake.py

store/

* api.py
* impl/

  * hdf5.py
* test/

  * fake.py

---

### Regeln

* `api.py` ist der „Header“ (C++-Gedanke)
* Implementierungen importieren `api.py`, niemals umgekehrt
* Fakes liegen immer unter `test/fake.py`
* Keine Implementierungslogik in `api.py`

---

## 3. Interfaces (ABCs)

### Regeln

* Interfaces werden **immer** mit `abc.ABC` definiert
* Keine `Protocol`s für Kernarchitektur
* Interface-Klassen haben **keinen** Suffix wie `IF` oder `Interface`
* Der Kontext ergibt sich aus:

  * dem Modulpfad (z.B. `convert.api.Converter`)
  * der Basisklasse (`ABC`)

### Beispiel

python:

* Klasse: `Converter`
* Datei: `convert/api.py`
* Implementierung: `convert/impl/drop.py`

---

## 4. Implementierungen

### Regeln

* Implementierungen liegen **immer** unter `impl/`
* Klassenname beschreibt Backend oder Format
* Implementierungen dürfen externe Libraries verwenden
  (z.B. `h5py`, `pandas`, `numpy`)
* Keine Auswahl- oder Wiring-Logik in Implementierungen

### Beispiel

* Interface: `Converter`
* Implementierung: `DropConfigConverter`
* Datei: `convert/impl/drop.py`

---

## 5. Fakes / Test-Doubles

### Regeln

* Fakes implementieren **dasselbe Interface**
* Keine Patches interner Attribute
* Keine Mock-Framework-Magie
* Fakes sind einfache, explizite Klassen
* Fakes liegen immer unter `test/fake.py`

### Beispiel

* Interface: `Store`
* Fake: `FakeStore`
* Datei: `store/test/fake.py`

---

## 6. Naming-Konventionen

### Klassen

* Interface:
  `Converter`, `Store`, `Parser`, `Source`

* Implementierung:
  `Hdf5Store`, `FsSource`, `DropConfigConverter`

* Fake:
  `FakeStore`, `FakeConverter`

Nicht erlaubt:

* `ConverterIF`
* `H5Interface`
* `ParserProtocol`

---

## 7. Methodenstil

### Regeln

* Methoden haben **ein Wort**
* Verben, keine Sätze
* Keine implizite Arbeit

Beispiele:

* `group`
* `attr`
* `feed`
* `read`
* `write`
* `parse`
* `select`
* `convert`

Nicht erlaubt:

* `get_converted_data`
* `load_and_parse_file`

---

## 8. Verantwortlichkeiten (hart getrennt)

Eine Datei darf **nur eine** dieser Rollen haben:

* IO (Filesystem, HDF5, Netzwerk)
* Parsing / Konvertierung
* Auswahl / Registry / Wiring

Wenn eine Datei mehr als eine Rolle erfüllt → **splitten**.

---

## 9. Meta-Daten (Single Source of Truth)

* `FileMeta` existiert **genau einmal**
* Liegt in `meta/api.py`
* Wird überall importiert
* Keine lokalen Varianten oder „leicht angepasste“ Kopien

---

## 10. Content-first APIs

Parser und Converter arbeiten **nicht primär mit Pfaden**.

Bevorzugt:

* `convert(content: bytes | str, meta: FileMeta)`

Filesystem- oder HDF5-Zugriff passiert in **separaten Adaptern**.

Vorteile:

* Konvertierung aus HDF5
* Konvertierung aus Filesystem
* Konvertierung aus Tests (Strings / Bytes)

---

## 11. Storage- und HDF5-Regeln

* Raw-Dateien werden **verlustfrei** gespeichert

* Speicherung als `uint8` Dataset

* Jedes Raw-Dataset enthält Provenance-Attribute:

  * `source_name`
  * `source_path` (wenn bekannt)
  * `source_size`
  * optional: `sha256`, `mtime_ns`

* Konvertierte Daten liegen **getrennt** von Raw-Daten
  (z.B. `/raw` vs `/conv`)

---

## 12. Selector / Wiring

* Auswahl-Logik lebt **nur** in `select.py`
* Keine implizite Registrierung beim Import
* Immer explizite Builder-Funktionen

Beispiel (konzeptionell):

* `build_default_selector()`

Wenn man fragt „wo wird entschieden, was benutzt wird?“
→ Antwort ist immer: `select.py`

---

## 13. Dateigröße & Pflege

* Ziel: < 300 Zeilen pro Datei
* Wenn eine Datei:

  * IO + Parsing + Wiring enthält → splitten
* Wenige, klar benannte Dateien sind besser als große Sammeldateien

---

## 14. Leitmotiv

* Struktur statt Cleverness
* Explizit statt Magie
* Interfaces klein, Implementierungen austauschbar
* Wenn man raten muss, wo etwas liegt, ist die Struktur falsch

