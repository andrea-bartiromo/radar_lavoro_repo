# Radar Lavoro - il tuo aggregatore personale

Radar Lavoro e una web app Flask locale, pensata per un solo utente: nessun account, nessun login, nessun cloud. Cerca offerte di lavoro tramite Jooble, filtra i risultati poco pertinenti, ordina gli annunci per compatibilita con il profilo di Andrea Bartiromo e ora include anche un piccolo CRM candidature.

Il progetto resta orientato a opportunita di comunicazione digitale, social media, giornalismo, digital marketing, posizioni junior, remoto/ibrido e categorie protette L.68/99.

## Installazione

```bash
pip install -r requirements.txt
```

## Avvio

```bash
python app.py
```

Poi apri **http://127.0.0.1:5000**.

Il database locale `radar_lavoro.db` viene creato sul tuo computer e non deve essere caricato nel repository. La API key Jooble va inserita dalle impostazioni dell'app, mai nel codice.

## Primo utilizzo

1. Vai in **Ricerca**.
2. Inserisci la tua citta.
3. Incolla la tua API key Jooble da **it.jooble.org/api/about**.
4. Controlla le parole chiave gia precompilate e modificale se serve.
5. Vai in **Filtri avanzati** per raffinare distanza, modalita, esperienza, contratto, orario, stipendio e priorita L.68/99.
6. Torna alla **Dashboard** e premi **Cerca ora**.

## Come funziona

- Ogni ricerca interroga Jooble con le parole chiave configurate e salva gli annunci pertinenti in SQLite.
- Gli annunci vengono filtrati e ordinati con un punteggio di compatibilita 0-100.
- Gli annunci gia presenti non vengono duplicati.
- Puoi segnare un annuncio come visto o usare **Segna tutti come visti** per svuotare la sezione dei nuovi.
- Le candidature e le note restano salvate solo nel database locale.

## CRM candidature

Ogni annuncio ha uno stato candidatura e un campo note personali direttamente nella dashboard.

Stati disponibili:

- **Nuovo**: offerta appena trovata.
- **Visto**: offerta letta, senza decisione.
- **Salvato**: offerta interessante da riprendere.
- **CV preparato**: documenti pronti per candidarsi.
- **Candidatura inviata**: candidatura mandata; l'app registra la data di invio.
- **Colloquio**: colloquio fissato o in corso.
- **Scartato**: offerta non adatta, senza eliminarla dal database.
- **Assunto**: esito positivo.

La dashboard mostra due sezioni principali:

- **Nuovi**: annunci ancora da valutare.
- **Candidature e offerte seguite**: annunci visti, salvati, candidati, in colloquio, scartati o conclusi.

In alto trovi anche le statistiche rapide: nuovi, salvati, candidature inviate e colloqui.

## Cosa resta volutamente fuori

Questa versione rimane essenziale e personale:

- nessun account o login;
- nessuna gestione multiutente;
- nessun deploy cloud;
- nessuna API key nel codice;
- nessun caricamento del database locale su GitHub.
