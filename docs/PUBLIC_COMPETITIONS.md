# Concorsi Pubblici

Il modulo Concorsi Pubblici e lo Sprint 5 di Radar Lavoro. Serve a seguire
bandi, scadenze, stato della domanda e documenti collegati senza trasformare
l'app in un sistema cloud o multiutente.

## Obiettivo

La pagina `/concorsi` permette di registrare concorsi pubblici e opportunita
PA rilevanti per comunicazione, ufficio stampa, ruoli amministrativi,
categorie protette e profili digitali.

Il modulo prepara anche la base per:

- checklist candidatura;
- pacchetti documentali;
- priorita su scadenze;
- futuri suggerimenti Radar AI.

## Tabelle create

### `public_competitions`

Contiene i metadati del bando:

- titolo;
- ente;
- categoria;
- sede;
- link fonte;
- numero posti;
- tipo contratto;
- stato concorso;
- stato domanda;
- date principali;
- requisiti;
- documenti richiesti;
- note personali;
- stato archiviato;
- date tecniche di creazione e aggiornamento.

### `competition_documents`

Collega un concorso ai documenti salvati nell'Archivio Documenti:

- concorso;
- documento;
- uso del documento;
- documento richiesto/non richiesto;
- documento pronto/non pronto;
- note;
- date tecniche.

## Privacy

Radar Lavoro non copia bandi, CV, certificazioni o allegati dentro il
repository. I file personali restano nel computer dell'utente.

Nel database locale vengono salvati solo:

- metadati;
- percorsi locali gia presenti nell'Archivio Documenti;
- stati di avanzamento;
- note personali.

## Stati concorso

- Monitorato
- Aperto
- In scadenza
- Chiuso
- Prove
- Graduatoria
- Archiviato

## Stati domanda

- Da valutare
- In preparazione
- Domanda inviata
- Prove da seguire
- Idoneita/graduatoria
- Non idoneo
- Rinunciato

## Completezza domanda

La completezza viene calcolata in modo semplice:

- il modulo legge i documenti richiesti indicati nel concorso;
- controlla i documenti collegati come richiesti;
- conta quanti documenti richiesti sono segnati come pronti.

Questa logica e volutamente semplice. Lo Sprint Radar AI potra migliorare il
calcolo leggendo categorie, tag, requisiti e cronologia delle candidature.

## Integrazione con Archivio Documenti

Ogni concorso puo collegare documenti gia registrati in `/documenti`.
Il collegamento e leggero: non duplica file e non salva allegati nel database.

## Prossimi passi

- Collegare concorsi e profilo professionale per priorita automatiche.
- Creare checklist documentale per singolo bando.
- Evidenziare requisiti mancanti.
- Suggerire CV e documenti migliori tramite Radar AI.
