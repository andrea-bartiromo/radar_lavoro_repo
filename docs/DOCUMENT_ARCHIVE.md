# Archivio Documenti

L'Archivio Documenti e lo Sprint 4 di Radar Lavoro. Serve a mantenere una
traccia locale dei documenti utili per candidature, concorsi pubblici, CV
Manager e futuri suggerimenti Radar AI.

## Obiettivo

La pagina `/documenti` permette di registrare documenti collegati alla ricerca
di lavoro senza caricare file dentro l'applicazione. Radar Lavoro salva solo
metadati e percorsi locali.

## Dati salvati

La tabella `document_archive` contiene:

- titolo;
- descrizione;
- categoria;
- percorso file locale;
- formato;
- checksum opzionale;
- tag;
- eventuale CV collegato;
- stato;
- attivo/non attivo;
- scadenza opzionale;
- data creazione;
- data ultimo aggiornamento;
- note interne.

Il file vero resta sul computer dell'utente. Il database non contiene il
contenuto dei documenti.

## Categorie iniziali

- CV
- Lettera di presentazione
- Certificazione
- Categorie protette
- Portfolio
- Documento amministrativo
- Bando o concorso
- Altro

## Stati disponibili

- Pronto
- Bozza
- Da aggiornare
- Archiviato

## Funzioni principali

Il modulo `radar_documents.py` espone:

- `ensure_document_schema(conn, ensure_column)`: crea o aggiorna la tabella.
- `load_documents(conn, document_id=None)`: carica l'archivio o un documento specifico.
- `save_document(conn, form, document_id=None)`: aggiunge o modifica un documento.
- `delete_document(conn, document_id)`: elimina il record senza cancellare il file locale.
- `archive_document(conn, document_id)`: archivia un documento senza eliminarlo.
- `document_stats(documents)`: calcola statistiche sintetiche per la pagina.

## Integrazione con CV Manager

Ogni documento puo essere collegato a un CV tramite `related_cv_id`. Il
collegamento e volutamente leggero: serve per preparare checklist candidatura,
pacchetti documentali e suggerimenti futuri.

## Regole di sicurezza

- Non committare documenti personali.
- Non salvare file nel database.
- Non salvare API key o dati sensibili nel codice.
- Il database `radar_lavoro.db` resta locale.

## Prossimi passi

- Collegare documenti e candidature specifiche.
- Preparare checklist per candidatura.
- Creare pacchetti documentali per concorsi pubblici.
- Usare tag e categorie nel futuro Radar AI.
