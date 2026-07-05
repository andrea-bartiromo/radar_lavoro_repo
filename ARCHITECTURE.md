# Architettura di Radar Lavoro

Radar Lavoro e una web app personale per cercare, valutare e gestire opportunita di lavoro. Resta un'app locale per un solo utente: niente login, niente cloud, niente multiutente.

## Principi guida

1. **Uso personale prima di tutto**
   L'app deve essere semplice da avviare sul PC dell'utente.

2. **Dati locali**
   Il database SQLite resta sul computer dell'utente. File sensibili, API key, CV e documenti personali non devono essere caricati nel repository.

3. **Modularita progressiva**
   `app.py` contiene ancora molta logica, ma ogni sprint sposta la logica riutilizzabile in moduli dedicati senza refactoring aggressivi.

4. **Sviluppo per sprint**
   Ogni sprint deve lasciare una versione funzionante: backend, database, interfaccia e documentazione evolvono insieme.

5. **Compatibilita retroattiva**
   Le modifiche al database devono preservare i dati esistenti. Le nuove colonne si aggiungono con migrazioni e `ensure_column`.

## Stato attuale

La versione corrente include:

- app Flask locale;
- ricerca offerte tramite Jooble;
- configurazione di citta, parole chiave, esclusioni e API key;
- filtri avanzati per distanza, modalita, esperienza, contratto, orario, stipendio e categorie protette;
- ranking di compatibilita 0-100;
- gestione offerte nuove/visti;
- CRM candidature con stato candidatura, note, date e offerte seguite;
- profilo professionale strutturato con formazione, esperienze, certificazioni, competenze, competenze tecniche, ruoli obiettivo, preferenze territoriali e categorie protette.
- CV Manager locale con metadati dei curriculum, categorie, stato attivo, CV predefinito e suggerimento iniziale per categoria.
- Archivio Documenti locale con metadati, categorie, tag, stato, percorsi file e collegamento opzionale ai CV.

## Struttura attuale del repository

```text
radar_lavoro_repo/
|-- app.py
|-- radar_candidates.py
|-- radar_cv.py
|-- radar_documents.py
|-- radar_profile.py
|-- requirements.txt
|-- README.md
|-- ROADMAP.md
|-- CHANGELOG.md
|-- ARCHITECTURE.md
|-- docs/
|   |-- SISTEMA_CANDIDATURE.md
|   |-- PROFILO_PROFESSIONALE.md
|   |-- CV_MANAGER.md
|   `-- DOCUMENT_ARCHIVE.md
|-- migrations/
|   |-- 001_candidature.sql
|   |-- 002_profilo_professionale.sql
|   |-- 003_cv_manager.sql
|   `-- 004_document_archive.sql
|-- templates/
|   |-- base.html
|   |-- cv.html
|   |-- dashboard.html
|   |-- documenti.html
|   |-- filtri.html
|   |-- impostazioni.html
|   `-- profilo.html
`-- static/
    `-- style.css
```

## Struttura obiettivo

```text
radar_lavoro_repo/
|-- app.py                         # entrypoint Flask minimale
|-- config.py                      # costanti applicative e configurazione
|-- db.py                          # connessione SQLite e migrazioni
|-- services/
|   |-- jooble_service.py
|   |-- ranking_service.py
|   |-- filter_service.py
|   |-- candidate_service.py
|   |-- profile_service.py
|   `-- contest_service.py
|-- repositories/
|   |-- job_repository.py
|   |-- profile_repository.py
|   `-- document_repository.py
|-- templates/
|-- static/
|-- migrations/
|-- docs/
|-- README.md
|-- ROADMAP.md
`-- CHANGELOG.md
```

## Moduli principali

### app.py

Responsabilita attuale:

- inizializzazione Flask;
- creazione e migrazione database;
- route principali;
- ricerca Jooble;
- ranking e filtri;
- rendering dashboard, impostazioni, filtri e profilo.

Obiettivo futuro: mantenere solo avvio app, registrazione route e wiring dei servizi.

### radar_candidates.py

Responsabilita:

- stati candidatura;
- etichette UI;
- arricchimento dei job con dati candidatura;
- divisione tra offerte nuove e offerte seguite;
- statistiche candidature;
- aggiornamento stato candidatura e note.

### radar_profile.py

Responsabilita:

- colonne e seed del profilo professionale;
- lettura e salvataggio della scheda personale;
- normalizzazione di liste scritte una voce per riga;
- compatibilita con i campi legacy del profilo;
- generazione di parole chiave per ranking, CV Manager e Radar AI.

Il profilo e strutturato in:

- identita professionale;
- formazione;
- esperienze;
- certificazioni;
- competenze;
- competenze tecniche;
- ruoli obiettivo;
- preferenze territoriali;
- categorie protette;
- note interne.

### radar_cv.py

Responsabilita:

- schema e compatibilita della tabella `cv_documents`;
- categorie CV iniziali;
- lettura, salvataggio, eliminazione e scelta del CV predefinito;
- normalizzazione di formato, categoria e stato attivo;
- suggerimento iniziale del CV migliore tramite `find_best_cv()`.

Il modulo salva solo metadati e percorsi locali. I file CV non vengono copiati,
caricati o salvati nel database.

### radar_documents.py

Responsabilita:

- schema e compatibilita della tabella `document_archive`;
- categorie, formati e stati dei documenti;
- lettura, salvataggio, archiviazione ed eliminazione dei record;
- normalizzazione di tag, formato, categoria e stato;
- statistiche sintetiche per la pagina Archivio Documenti.

Il modulo salva solo metadati e percorsi locali. I file personali non vengono
copiati, caricati o salvati nel database.

### templates/

Responsabilita:

- `base.html`: layout, navigazione, sidebar;
- `dashboard.html`: elenco offerte, punteggi, CRM candidature;
- `cv.html`: archivio CV, form metadati, stato attivo, predefinito e suggerimento automatico;
- `documenti.html`: archivio documenti, form metadati, tag, stato e collegamento CV;
- `impostazioni.html`: configurazione ricerca;
- `filtri.html`: filtri avanzati e priorita;
- `profilo.html`: scheda professionale strutturata.

### static/style.css

Responsabilita:

- design system visivo;
- layout dashboard;
- card offerte;
- form impostazioni, filtri, profilo, CV Manager e Archivio Documenti;
- componenti CRM candidature.

## Flusso dati attuale

1. L'utente configura citta, parole chiave e API key.
2. L'utente preme `Cerca ora`.
3. L'app interroga Jooble per ogni parola chiave.
4. Ogni annuncio viene filtrato per pertinenza, distanza, modalita, esperienza, contratto, orario e preferenze.
5. Gli annunci gia presenti vengono ignorati.
6. Ogni nuovo annuncio riceve un punteggio di compatibilita.
7. Gli annunci vengono salvati in SQLite.
8. La dashboard mostra nuovi annunci e candidature/offerte seguite.
9. L'utente aggiorna stato candidatura e note.
10. Il profilo professionale alimenta parole chiave e ranking.
11. Il CV Manager mantiene i curriculum locali e prepara il suggerimento del CV piu adatto.
12. L'Archivio Documenti mantiene metadati e percorsi locali dei documenti utili a candidature e concorsi.

## Convenzioni codice

- Lingua UI: italiano.
- Nomi variabili backend: preferibilmente inglese tecnico, salvo funzioni gia esistenti in italiano.
- Route Flask: mantenere nomi brevi e leggibili.
- Ogni nuova funzione riutilizzabile va in un modulo dedicato.
- Evitare dipendenze esterne non necessarie.

## Convenzioni database

- SQLite locale.
- Nuove colonne tramite `ensure_column` e migrazione SQL in `migrations/`.
- Mai committare `radar_lavoro.db`.
- Mai committare API key, CV o documenti personali.
- Ogni tabella deve avere campi testuali semplici e facilmente esportabili.

## Roadmap architetturale

### Fase 1 - CRM candidature

- Stati candidatura.
- Note personali.
- Data candidatura.
- Ultimo aggiornamento.
- Statistiche base.

### Fase 2 - Profilo professionale

- Profilo unico Andrea.
- Titolo professionale.
- Formazione.
- Esperienze.
- Certificazioni.
- Competenze.
- Competenze tecniche.
- Ruoli obiettivo.
- Preferenze territoriali.
- Categorie protette.
- Parametri usati dal ranking.

### Fase 3 - CV e documenti

- Archivio CV con metadati e percorsi locali.
- Categorie CV e stato attivo/predefinito.
- Prima funzione di suggerimento CV per categoria.
- Archivio Documenti con metadati, tag, stati e percorsi locali.
- Suggerimento CV per offerta da integrare nella dashboard.
- Checklist candidatura.

### Fase 4 - Concorsi pubblici

- Schede bando.
- Scadenze.
- Requisiti.
- Stato domanda.
- Priorita L.68/99 e PA.

### Fase 5 - Radar AI

- Spiegazione compatibilita.
- Requisiti mancanti.
- Suggerimenti CV.
- Priorita dinamiche basate sulle azioni dell'utente.

## Regola fondamentale

Ogni sviluppo deve aumentare l'utilita pratica dell'app per la ricerca concreta del lavoro. Se una funzionalita non aiuta Andrea a trovare, valutare, preparare o tracciare opportunita, va rimandata.
