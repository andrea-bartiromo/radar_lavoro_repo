# Profilo professionale

Questo sprint introduce il profilo professionale unico di Andrea dentro Radar Lavoro.

## Obiettivo

Il profilo serve a trasformare Radar Lavoro da semplice motore di ricerca a sistema personale capace di capire meglio:

- competenze reali;
- ruoli obiettivo;
- preferenze territoriali;
- disponibilita;
- categorie protette L.68/99;
- differenza tra preferenze forti e preferenze leggere.

## Scelte architetturali

La logica e stata inserita nel modulo `radar_profile.py`, seguendo il modello gia usato da `radar_candidates.py`.

Il modulo contiene:

- valori iniziali del profilo;
- colonne database necessarie;
- funzioni di migrazione tramite `ensure_column`;
- caricamento e salvataggio del profilo;
- normalizzazione delle liste scritte una voce per riga;
- funzione `profile_keywords`, utile per ranking, CV Manager e Radar AI.

## Database

I dati sono salvati nella tabella `profile`, perche l'app e ancora personale e monoutente.

Campi aggiunti:

- `professional_full_name`
- `professional_headline`
- `education`
- `location_preference`
- `availability`
- `protected_category_notes`
- `strong_preferences`
- `soft_preferences`
- `skills`
- `target_roles`
- `profile_notes`
- `profile_updated_at`

La migrazione SQL e disponibile in `migrations/002_profilo_professionale.sql`.

## UI

La pagina `templates/profilo.html` e pensata come scheda modificabile, non come semplice testo statico.

Sezioni previste:

1. identita professionale;
2. preferenze e disponibilita;
3. preferenze forti e leggere;
4. competenze e ruoli obiettivo;
5. note interne.

## Uso nei prossimi sprint

Il profilo professionale sara usato da:

- **CV Manager**: scelta del CV piu adatto e suggerimenti mirati;
- **Archivio documenti**: checklist candidatura;
- **Concorsi pubblici**: priorita PA, L.68/99 e profili amministrativi;
- **Radar AI**: spiegazione del match e requisiti mancanti;
- **Motore di apprendimento**: aggiustamento delle preferenze in base alle azioni dell'utente.

## Regola di prodotto

Le preferenze forti devono incidere piu delle preferenze leggere. Una preferenza forte puo diventare filtro o forte bonus; una preferenza leggera deve restare un aiuto al ranking, non un blocco automatico.
