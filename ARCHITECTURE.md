# Architettura di Radar Lavoro

Radar Lavoro e una web app personale per la ricerca, valutazione e gestione delle opportunita di lavoro. Il progetto nasce come applicazione locale per un solo utente, senza login, senza cloud e senza funzionalita multiutente.

## Principi guida

1. **Uso personale prima di tutto**
   L'app deve essere semplice da avviare sul PC dell'utente. Non va progettata come piattaforma pubblica finche non sara una scelta esplicita.

2. **Dati locali**
   Il database SQLite resta sul computer dell'utente. File sensibili, API key, CV e documenti personali non devono essere caricati nel repository.

3. **Modularita progressiva**
   `app.py` contiene ancora molta logica. Ogni nuova fase deve spostare logica riutilizzabile in moduli separati, senza fare refactoring troppo aggressivi in un solo passaggio.

4. **Sviluppo per sprint**
   Ogni sprint deve produrre una versione funzionante: backend, database, interfaccia e documentazione devono evolvere insieme.

5. **Compatibilita retroattiva**
   Le modifiche al database devono preservare i dati gia presenti. Le nuove colonne si aggiungono con migrazioni e `ensure_column`.

## Stato attuale

La versione corrente include:

- app Flask locale;
- ricerca offerte tramite Jooble;
- configurazione di citta, parole chiave, esclusioni e API key;
- filtri avanzati per distanza, modalita, esperienza, contratto, orario, stipendio e categorie protette;
- ranking di compatibilita 0-100;
- gestione offerte nuove/visti;
- CRM candidature di base, con stato candidatura e note personali;
- documentazione iniziale di roadmap, changelog e migrazioni.

## Struttura attuale del repository

```text
radar_lavoro_repo/
├── app.py
├── radar_candidates.py
├── requirements.txt
├── README.md
├── ROADMAP.md
├── CHANGELOG.md
├── ARCHITECTURE.md
├── docs/
│   └── SISTEMA_CANDIDATURE.md
├── migrations/
│   └── 001_candidature.sql
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── filtri.html
│   └── impostazioni.html
└── static/
    └── style.css
```

## Struttura obiettivo

Nel tempo il progetto dovrebbe arrivare a questa organizzazione:

```text
radar_lavoro_repo/
├── app.py                         # entrypoint Flask minimale
├── config.py                      # costanti applicative e configurazione
├── db.py                          # connessione SQLite e migrazioni
├── services/
│   ├── jooble_service.py          # chiamate Jooble
│   ├── ranking_service.py         # compatibilita e motivazioni
│   ├── filter_service.py          # filtri e pertinenza
│   ├── candidate_service.py       # CRM candidature
│   ├── profile_service.py         # profilo professionale
│   └── contest_service.py         # concorsi pubblici
├── repositories/
│   ├── job_repository.py          # query offerte
│   ├── profile_repository.py      # query profilo
│   └── document_repository.py     # query documenti
├── templates/
├── static/
├── migrations/
├── docs/
├── README.md
├── ROADMAP.md
└── CHANGELOG.md
```

## Moduli principali

### app.py

Responsabilita attuale:

- inizializzazione Flask;
- creazione/migrazione database;
- route principali;
- ricerca Jooble;
- ranking e filtri;
- rendering dashboard, impostazioni e filtri.

Obiettivo futuro: mantenere solo avvio app, registrazione route e wiring dei servizi.

### radar_candidates.py

Responsabilita:

- stati candidatura;
- etichette UI;
- arricchimento dei job con dati candidatura;
- divisione tra offerte nuove e offerte seguite;
- statistiche candidature;
- aggiornamento stato candidatura e note.

Questo modulo rappresenta il modello da seguire per i prossimi servizi.

### templates/

Responsabilita:

- `base.html`: layout, navigazione, sidebar;
- `dashboard.html`: elenco offerte, punteggi, CRM candidature;
- `impostazioni.html`: configurazione ricerca;
- `filtri.html`: filtri avanzati e priorita.

### static/style.css

Responsabilita:

- design system visivo;
- layout dashboard;
- card offerte;
- form impostazioni e filtri;
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

## Convenzioni codice

- Lingua UI: italiano.
- Nomi variabili backend: preferibilmente inglese tecnico, salvo funzioni gia esistenti in italiano.
- Route Flask: mantenere nomi brevi e leggibili.
- Ogni nuova funzione riutilizzabile va in un modulo dedicato.
- Evitare dipendenze esterne non necessarie.
- Prima di aggiungere una libreria, valutare se basta la standard library.

## Convenzioni database

- SQLite locale.
- Nuove colonne tramite `ensure_column` e migrazione SQL in `migrations/`.
- Mai committare `radar_lavoro.db`.
- Mai committare API key o documenti personali.
- Ogni tabella deve avere campi testuali semplici e facilmente esportabili.

## Convenzioni UI

- Interfaccia sobria, leggibile, ispirata a registro/protocollo ma moderna.
- Ogni offerta deve mostrare rapidamente: compatibilita, titolo, azienda, localita, fonte, motivi e azioni.
- Evitare schermate troppo dense: le funzioni avanzate possono stare in sezioni dedicate.
- I pulsanti devono indicare chiaramente l'azione.

## Roadmap architetturale

### Fase 1 - CRM candidature

- Stati candidatura.
- Note personali.
- Data candidatura.
- Ultimo aggiornamento.
- Statistiche base.

### Fase 2 - Profilo professionale

- Profilo unico Andrea.
- Competenze.
- Preferenze.
- Titoli di studio.
- Disponibilita.
- Parametri usati dal ranking.

### Fase 3 - CV e documenti

- Archivio CV.
- Documenti personali locali.
- Suggerimento CV per offerta.
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
