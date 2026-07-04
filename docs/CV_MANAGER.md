# CV Manager

Il CV Manager e lo Sprint 3 di Radar Lavoro. Serve a mantenere un archivio
locale dei curriculum e a preparare la base per Radar AI.

## Obiettivo

La pagina `/cv` permette di registrare piu versioni del curriculum, distinguere
le categorie professionali e scegliere un CV predefinito. L'app non carica,
non copia e non salva i file CV nel database.

## Dati salvati

La tabella `cv_documents` salva solo metadati:

- nome;
- descrizione;
- versione;
- categoria;
- percorso file locale;
- formato;
- data creazione;
- data ultimo aggiornamento;
- stato attivo/non attivo;
- CV predefinito;
- note interne;
- checksum opzionale.

Il campo `file_path` contiene un percorso o un riferimento testuale al file.
Il file resta sul computer dell'utente e non deve essere committato.

## Categorie iniziali

- Corporate Communication
- Digital Marketing
- Giornalismo
- Comunicazione istituzionale
- Data Analyst
- Web Developer
- Generico

## Funzioni principali

Il modulo `radar_cv.py` espone:

- `ensure_cv_schema(conn, ensure_column)`: crea o aggiorna la tabella in modo compatibile.
- `load_cv(conn, cv_id=None)`: carica tutti i CV o un CV specifico.
- `save_cv(conn, form, cv_id=None)`: aggiunge o modifica un CV.
- `delete_cv(conn, cv_id)`: elimina il record dal manager senza cancellare il file.
- `set_default_cv(conn, cv_id)`: imposta un CV attivo come predefinito.
- `find_best_cv(conn, job_or_text=None)`: suggerisce il CV piu adatto con regole semplici.

## Suggerimento automatico

Per ora `find_best_cv()` usa parole chiave basilari:

- marketing, SEO, SEM, social media -> Digital Marketing;
- developer, HTML, CSS, JavaScript, Python, Laravel -> Web Developer;
- giornalista, redattore, redazione -> Giornalismo;
- pubblica amministrazione, ente pubblico, ufficio stampa -> Comunicazione istituzionale;
- data analyst, SQL, analytics, report -> Data Analyst;
- corporate communication, PR, media relation -> Corporate Communication.

Se nessuna regola trova un match, viene usato il CV predefinito. Se non esiste
un CV predefinito, viene scelto il primo CV attivo disponibile.

## Regole di sicurezza

- Non committare file CV personali.
- Non salvare documenti sensibili nel repository.
- Non salvare API key o dati privati nel codice.
- Il database `radar_lavoro.db` resta locale.

## Prossimi passi

- Collegare il suggerimento CV alle singole offerte in dashboard.
- Mostrare spiegazioni piu dettagliate del suggerimento.
- Integrare archivio documenti e lettere di presentazione.
- Far evolvere `find_best_cv()` nel futuro Sprint Radar AI.
