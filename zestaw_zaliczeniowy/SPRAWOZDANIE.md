# Sprawozdanie

**Autor:** Kacper Jóźwik 14502

## Wprowadzenie

Zestaw zaliczeniowy łączy materiał z sześciu laboratoriów w jeden spójny pipeline analityczny zbudowany wokół wspólnego zbioru danych: `stanfordnlp/imdb` z Hugging Face.

## Lab 1 - Dekoratory

Zaimplementowano dwa dekoratory: `@retry(max_attempts, delay, backoff)`, ponawiający wywołanie funkcji przy wyjątku z exponential backoff, oraz `@cache_to_disk(cache_dir)`, zapisujący wynik funkcji do pliku JSON na dysku (klucz cache to hash MD5 z argumentów). Eksperyment na funkcji `flaky_fetch` o 50% szansie awarii, z pięcioma próbami ponawiania, dał 97/100 sukcesów wobec teoretycznych `1 − 0.5^5 ≈ 96,9%`, bardzo duza zgodnosc.

**Wniosek:** każda dodatkowa próba połowi prawdopodobieństwo całkowitej porażki, ale przyrost skuteczności maleje (N=1 → 50%, N=3 → 87,5%, N=5 → 96,9%), więc ustawianie bardzo dużej liczby prób się nie opłaca. Przy ponownym uruchomieniu eksperymentu liczba sukcesów rośnie, bo udane wyniki zapisane przez `@cache_to_disk` omijają losowanie - uczciwy pomiar jest możliwy tylko przy pustym cache. 


## Lab 2 - Współbieżność (multiprocessing vs threading)

Policzono prosty score sentymentu (lexicon-based) dla 5000 recenzji na trzy sposoby: sekwencyjnie, przez `ThreadPoolExecutor` i przez `multiprocessing.Pool`. Wyniki: sekwencyjnie 0,166 s, ThreadPool 0,228 s, multiprocessing 0,133 s.

**Wniosek:** zadanie to czyste liczenie, więc multiprocessing wygrywa - każdy z procesów ma własny interpreter i omija GIL, dzięki czemu praca faktycznie dzieli się na rdzenie. ThreadPool przegrywa nawet z wersją sekwencyjną, bo GIL pozwala tylko jednemu wątkowi naraz wykonywać kod Pythona, a dochodzi narzut na przełączanie wątków. Przewaga multiprocessingu jest skromna (okolo 20%), bo funkcja jest bardzo szybka, a uruchomienie procesów metodą spawn i serializacja danych mają swój koszt - multiprocessing opłaca się dopiero przy większej pracy na element. Dodatkowo na macOS funkcję trzeba było wynieść do osobnego, importowalnego modułu (`sentiment_module.py`), ponieważ procesy startują metodą spawn i importują funkcję po nazwie - funkcji z komórki notebooka (moduł `__main__`) nie da się zaimportować, co powodowało zawieszanie się `Pool`.


## Lab 3 - Testowanie (pytest)

Zaimplementowano klasę `Tokenizer` z trzema konfigurowalnymi opcjami (`lower`, `strip_html`, `min_length`) i metodami `tokenize` oraz `vocab`. Klasa i komplet testów (fixtures, `parametrize`, `xfail`) zapisywane są z poziomu notebooka do plików `tokenizer.py` i `test_tokenizer.py` w `_workspace/`, a pytest uruchamiany jest przez `subprocess`. Test oznaczony `@pytest.mark.xfail` (adres e-mail, którego prosty regex `\w+` nie obsłuży) celowo nie przechodzi - `XFAIL` jest tu oczekiwanym sukcesem.

**Wniosek:** profilowanie 100 recenzji dało 5053 unikalnych tokenów w całym zbiorze i średnio 153 unikalne tokeny na pojedynczą recenzję. Gdyby recenzje nie dzieliły słów, słownik liczyłby ok. `100 × 153 ≈ 15 300` tokenów - faktycznie ma 5053, czyli trzykrotnie mniej. Oznacza to, że recenzje masowo używają tych samych słów, więc rozmiar słownika rośnie wolniej niż liniowo wraz z liczbą tekstów. 


## Lab 4 - Bazy danych (schemat JSON vs klasyczny SQL)

Te same 2000 recenzji załadowano do SQLite na dwa sposoby: klasycznie (osobne kolumny) oraz w stylu pseudo-NoSQL (jedna kolumna `doc` z całym dokumentem JSON, w tym zagnieżdżonym `stats` i listą `tags`). Napisano cztery zapytania analityczne z `json_extract(doc, '$.ścieżka')`. Schemat JSON był o ~9% większy.

**Wniosek:** dla problemu analityka - agregacje na wymiarach, lepszy jest klasyczny schemat relacyjny. Schemat JSON jest większy, bo każdy wiersz powtarza nazwy pól jako tekst, oraz wolniejszy, bo `json_extract` musi parsować dokument przy każdym wierszu. Napotkany został konkretny problem z ograniczeniem: zapytanie o średni `word_count` per klasa początkowo zwracało `(None, 2000)`, bo SQLite nie potrafił pogrupować po aliasie, gdy w grę wchodziła funkcja `AVG` na polu wyłuskanym przez `json_extract` - trzeba było powtórzyć całe wyrażenie `json_extract` w `GROUP BY`. W klasycznym SQL `word_count` jest osobną kolumną i `AVG(...) GROUP BY` działa od razu. 


## Lab 5 - PySpark (window functions)

Na DataFrame z 2000 recenzji (Spark 4.1.2 uruchomiony lokalnie) zastosowano funkcje okienne: ranking recenzji w obrębie klasy po długości (`row_number`), top 3 najdłuższe per klasa, różnicę długości od średniej klasowej, średnią kroczącą w oknie 50 wierszy (`rowsBetween(-49, 0)`) oraz wykres liniowy z dwiema liniami (pos/neg). Statystyki potwierdziły zbliżone średnie długości: pozytywne ~237 słów, negatywne ~230.

**Wniosek:** window functions liczą agregaty (ranking, średnia, średnia krocząca) bez zwijania wierszy, w odróżnieniu od `groupBy` - dzięki temu w jednym wierszu jest i wartość indywidualnej recenzji, i kontekst całej klasy (np. `diff_from_avg` pokazał recenzję odstającą o +433 słowa od średniej klasowej). `partitionBy("label")` izoluje obliczenia w obrębie klasy (rankingi obu klas zaczynają się od 1), a `rowsBetween(-49, 0)` tworzy okno przesuwne dla średniej kroczącej. Wykres pokazał, że po wygładzeniu obie klasy krążą wokół ~230 słów, a linie się przeplatają - długość recenzji nie różnicuje sentymentu. Początkowe gwałtowne wahania linii to artefakt niepełnego okna (dla pierwszych poniżej 50 wierszy partycji średnia liczona jest z mniej niż 50 elementów).

---

## Lab 6 - Data Quality (kontrakt danych)

Zaimplementowano prosty framework jakości danych: klasę `DataContract` z metodą `add_rule(name, check, severity)` oraz `DataValidator`, która iteruje po regułach i zwraca raport `{rule_name: {passed, severity, details}}`. Każda reguła to funkcja zwracająca krotkę `(passed, details)`, dzięki czemu walidator nie musi nic wiedzieć o konkretnej regule. Zdefiniowano sześć reguł plus bonus, wynik zapisano do `_workspace/data_quality_report.json` z timestampem. 

**Wniosek:** kluczowy jest podział na severity. Reguły `error` (brak nulli, etykiety w {0,1}, balans klas) to twarde warunki - ich złamanie przerywa pipeline (fail fast). Reguły `warning` (długość, duplikaty, HTML) to sygnały jakości do posprzątania, ale nie blokery. Bonus `no_html_tags` pokazał to namacalnie: 59% recenzji zawiera HTML (`<br />`), a mimo to walidacja nie zawiodła, bo reguła ma severity `warning` - raport o problemie informuje, ale go nie blokuje. Gdyby ta reguła była `error`, pipeline zatrzymałby się na pierwszym tagu i nie zapisałby raportu. Sednem Data Quality jest właśnie to, że nie każdy problem z danymi jest równie krytyczny.


## Wnioski końcowe

Paca uwypukliła realne pułapki środowiskowe: konieczność wynoszenia funkcji do importowalnego modułu przy multiprocessing na macOS (spawn), podwajanie backslashy w regexach zapisywanych do plików jako string, oraz wymóg uruchamiania notebooka od góry do dołu, ponieważ importy i zmienne (`WORKDIR`, `functools`, `re`) żyją w pamięci kernela i muszą być załadowane w odpowiedniej kolejności.