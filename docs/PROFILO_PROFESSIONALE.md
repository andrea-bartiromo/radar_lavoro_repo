# Profilo professionale

Il Profilo professionale e la scheda personale strutturata di Andrea dentro Radar Lavoro.

Non e un CV caricato nel repository e non contiene documenti personali: salva solo dati testuali locali nel database SQLite.

## Obiettivo

Il profilo serve come base comune per:

- ranking offerte;
- CV Manager;
- archivio documenti;
- concorsi pubblici;
- Radar AI;
- motore di apprendimento.

## Sezioni della scheda

La pagina `/profilo` e organizzata in sezioni distinte:

1. Identita professionale
2. Formazione
3. Esperienze
4. Certificazioni
5. Competenze
6. Competenze tecniche
7. Ruoli obiettivo
8. Preferenze territoriali
9. Categorie protette
10. Note interne

Ogni lista viene salvata come JSON nella tabella `profile`, partendo da textarea con una voce per riga.

## Dati iniziali

Il seed iniziale include:

- titolo professionale completo;
- percorso formativo;
- esperienze giornalismo/social media;
- certificazioni;
- competenze comunicazione/marketing/contenuti;
- competenze tecniche;
- ruoli obiettivo;
- preferenze territoriali;
- informazioni L.68/99.

## Database

I dati restano nella tabella `profile`, per mantenere l'app monoutente e compatibile con il database esistente.

Campi principali:

- `professional_full_name`
- `professional_headline`
- `education_items`
- `experiences`
- `certifications`
- `skills`
- `technical_skills`
- `target_roles`
- `territorial_preferences`
- `protected_categories`
- `availability`
- `profile_notes`
- `profile_updated_at`
- `profile_schema_version`

Campi legacy mantenuti per compatibilita:

- `education`
- `location_preference`
- `protected_category_notes`
- `strong_preferences`
- `soft_preferences`

## Compatibilita

Le nuove colonne vengono aggiunte con `ensure_column`.

La funzione `seed_professional_profile()` arricchisce i dati esistenti senza cancellare modifiche manuali gia presenti. Il campo `profile_schema_version` evita di riapplicare lo stesso arricchimento a ogni avvio. I campi legacy vengono mantenuti sincronizzati con le nuove liste dove serve.

## Uso futuro

`profile_keywords()` restituisce parole chiave derivate da:

- ruoli obiettivo;
- competenze;
- competenze tecniche;
- certificazioni;
- formazione;
- esperienze;
- preferenze territoriali;
- categorie protette;
- preferenze forti e leggere.

Questa funzione e il punto di aggancio per ranking, CV Manager e Radar AI.
