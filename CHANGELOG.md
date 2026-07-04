# Changelog Radar Lavoro

Tutte le modifiche importanti al progetto verranno annotate qui.

## Sprint - Profilo professionale

### Aggiunto

- Aggiunto `radar_profile.py` per gestire il profilo professionale unico.
- Aggiunta pagina `/profilo` con form per dati professionali, preferenze, competenze e ruoli obiettivo.
- Aggiunte preferenze forti e preferenze leggere.
- Aggiunta migrazione `migrations/002_profilo_professionale.sql`.
- Aggiunta documentazione `docs/PROFILO_PROFESSIONALE.md`.
- Attivata la voce Profilo nella navigazione laterale.

### Modificato

- `app.py` inizializza e salva i nuovi campi del profilo professionale.
- Il ranking puo usare le parole chiave del profilo professionale.
- Aggiunta la costante `PAROLE_TROPPO_GENERICHE` per rendere piu robusto il calcolo della pertinenza.

## Fase 1 - CRM candidature

### Aggiunto

- Integrato `radar_candidates.py` in `app.py` per stati candidatura, arricchimento annunci, split dashboard e aggiornamento candidature.
- Estesa la tabella `jobs` con `application_status`, `personal_notes`, `applied_at` e `last_status_at`, mantenendo compatibilita con il campo storico `status`.
- Aggiunta la route `POST /candidatura/<job_id>` per salvare stato candidatura e note personali.
- Aggiornate le azioni "segna visto" e "segna tutti come visti" per sincronizzare anche lo stato candidatura e la data ultimo aggiornamento.
- Aggiornata la dashboard con sezioni "Nuovi" e "Candidature e offerte seguite", statistiche rapide, tag stato, date candidatura, select stato e textarea note.
- Aggiunti stili CSS per form candidatura, note, select, tag stato e date.

### File modificati

- `app.py`
- `radar_candidates.py`
- `templates/dashboard.html`
- `static/style.css`
- `README.md`
- `ROADMAP.md`
- `CHANGELOG.md`

## Prima sessione di ripresa sviluppo

### Aggiunto

- Creato `ROADMAP.md` come traccia ufficiale dello sviluppo.
- Definito il percorso verso Radar Lavoro 1.1, con priorita alla gestione candidature.
- Aggiunto questo changelog per conservare lo storico delle decisioni.

### Decisioni di prodotto

- Radar Lavoro resta prima di tutto uno strumento personale locale, non una piattaforma pubblica.
- La prossima funzionalita da sviluppare e il CRM candidature: stati avanzati, note e tracciamento candidatura.
- Prima di aggiungere nuove fonti esterne conviene completare il flusso personale: ricerca, valutazione, salvataggio, candidatura, colloquio.

### Prossimo sviluppo tecnico

- Estendere la tabella `jobs` con campi per stato candidatura, note personali, data candidatura e ultimo aggiornamento.
- Aggiungere nella dashboard un selettore di stato e un campo note per ogni offerta.
- Aggiungere una vista dedicata alle candidature attive.
