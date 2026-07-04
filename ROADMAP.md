# Roadmap Radar Lavoro

Questo file e la traccia ufficiale dello sviluppo dell'applicazione. Serve a non perdere piu decisioni importanti anche se una chat viene cancellata.

## Stato attuale

Radar Lavoro e una web app locale in Flask pensata per un solo utente. La versione attuale consente di:

- configurare citta, parole chiave e API key Jooble;
- cercare offerte tramite Jooble;
- salvare gli annunci in SQLite;
- distinguere annunci nuovi e gia visti;
- filtrare per distanza, modalita di lavoro, esperienza, contratto, orario, stipendio e categorie protette;
- ordinare le offerte con un punteggio di compatibilita personalizzato;
- dare priorita a offerte remote, junior, coerenti con comunicazione/digital marketing e L.68/99.
- gestire candidature con stati, note, date e offerte seguite;
- salvare un profilo professionale strutturato con formazione, esperienze, certificazioni, competenze, ruoli obiettivo e preferenze territoriali.
- gestire un archivio locale di CV con categorie, versioni, percorso file, stato attivo e CV predefinito.
- gestire un archivio locale di documenti con categorie, tag, stati, percorsi file e collegamento opzionale ai CV.

## Versione 1.1 - Stabilizzazione personale

Obiettivo: rendere l'app comoda e affidabile per l'uso quotidiano sul PC.

- [x] Aggiungere gestione candidatura: salvata, candidatura inviata, colloquio, scartata.
- [x] Aggiungere note personali per ogni annuncio.
- [ ] Aggiungere filtro in dashboard per stato candidatura.
- [ ] Aggiungere pulsante per archiviare o scartare offerte non interessanti.
- [ ] Migliorare messaggi di errore quando Jooble non risponde.
- [ ] Aggiungere pagina di riepilogo con statistiche base.

## Versione 1.2 - Profilo personale

Obiettivo: usare meglio il profilo di Andrea per ordinare le offerte.

- [x] Creare pagina Profilo.
- [x] Salvare competenze, titolo di studio, preferenze territoriali e disponibilita.
- [x] Migliorare la UX del Profilo con scheda personale, accordion, badge e modalita visualizzazione/modifica.
- [ ] Personalizzare le parole chiave partendo dal profilo.
- [x] Separare preferenze forti da preferenze leggere.
- [ ] Migliorare il punteggio di compatibilita con spiegazioni piu chiare.

## Versione 1.3 - Categorie protette e concorsi

Obiettivo: rendere Radar Lavoro particolarmente utile per offerte L.68/99 e opportunita pubbliche.

- [ ] Rafforzare il riconoscimento di offerte L.68/99.
- [ ] Aggiungere tag dedicati a invalidita civile, collocamento mirato, art. 1 L.68/99.
- [ ] Aggiungere sezione Concorsi pubblici.
- [ ] Monitorare parole chiave come operatore amministrativo, comunicazione, ufficio stampa, categorie protette.
- [ ] Preparare scheda riepilogo per ogni bando o concorso.

## Versione 2.0 - Radar intelligente

Obiettivo: trasformare l'app da aggregatore a assistente personale.

- [ ] Collegare piu fonti oltre Jooble.
- [x] Creare CV Manager locale con metadati, categorie, percorso file e predefinito.
- [x] Preparare una prima funzione `find_best_cv()` con regole semplici per categoria.
- [x] Creare Archivio Documenti locale con metadati, categorie, tag, stato e percorsi file.
- [ ] Aggiungere suggerimenti sul CV per ogni offerta.
- [ ] Preparare bozza lettera di presentazione.
- [ ] Evidenziare requisiti mancanti e punti forti.
- [ ] Imparare dalle azioni dell'utente: offerte ignorate, aperte, salvate, candidate.
- [ ] Notificare solo opportunita veramente rilevanti.

## Regole di sviluppo

- Ogni cambiamento importante va registrato in `CHANGELOG.md`.
- Le decisioni di prodotto vanno scritte in questo file.
- Il README deve spiegare sempre come installare e usare la versione corrente.
- Il database locale non va caricato su GitHub.
- Le API key non vanno mai salvate nel repository.
