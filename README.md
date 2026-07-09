# Radar Lavoro

**Web app personale per cercare, filtrare e gestire offerte di lavoro**

Radar Lavoro è una web app locale sviluppata in **Python** e **Flask**.  
L'app aiuta a cercare offerte di lavoro tramite API Jooble, filtrare gli annunci meno pertinenti, ordinare i risultati per compatibilità e gestire le candidature tramite un piccolo CRM personale.

Il progetto è pensato per un solo utente: nessun account, nessun login, nessun cloud. Tutti i dati restano salvati localmente.

---

## Obiettivo del progetto

Il progetto nasce da un'esigenza concreta: rendere più semplice e ordinata la ricerca di opportunità lavorative coerenti con un profilo junior in comunicazione digitale, social media, giornalismo, digital marketing, remoto/ibrido e categorie protette L.68/99.

Radar Lavoro permette di:

- raccogliere offerte da una fonte esterna;
- evitare duplicati;
- filtrare annunci poco pertinenti;
- assegnare un punteggio di compatibilità;
- salvare note e stati candidatura;
- tenere traccia delle opportunità più interessanti.

---

## Funzionalità principali

### Ricerca offerte

- Integrazione con API Jooble.
- Ricerca per città e parole chiave.
- Configurazione locale della API key.
- Salvataggio degli annunci in database SQLite.

### Filtri e ranking

- Filtri per distanza, modalità, esperienza, contratto, orario e stipendio.
- Priorità per opportunità remote/ibride.
- Attenzione alle offerte compatibili con categorie protette L.68/99.
- Punteggio di compatibilità da 0 a 100.
- Rimozione automatica dei duplicati.

### CRM candidature

Ogni annuncio può essere gestito con uno stato candidatura e note personali.

Stati disponibili:

- **Nuovo** — offerta appena trovata;
- **Visto** — offerta letta;
- **Salvato** — offerta interessante da riprendere;
- **CV preparato** — documenti pronti;
- **Candidatura inviata** — candidatura mandata;
- **Colloquio** — colloquio fissato o in corso;
- **Scartato** — offerta non adatta;
- **Assunto** — esito positivo.

---

## Architettura logica

```text
Radar Lavoro
│
├── Flask App
│   ├── Dashboard
│   ├── Ricerca offerte
│   ├── Filtri avanzati
│   └── CRM candidature
│
├── API Jooble
│   └── Recupero annunci
│
├── Ranking Engine
│   ├── Compatibilità profilo
│   ├── Filtri keyword
│   └── Deduplicazione
│
└── SQLite
    ├── Offerte
    ├── Stati candidatura
    └── Note personali
```

---

## Tecnologie utilizzate

- **Python**
- **Flask**
- **SQLite**
- **HTML/CSS**
- **API Jooble**

---

## Installazione

Clonare il repository:

```bash
git clone https://github.com/andrea-bartiromo/radar_lavoro_repo.git
cd radar_lavoro_repo
```

Installare le dipendenze:

```bash
pip install -r requirements.txt
```

---

## Avvio

```bash
python app.py
```

Poi aprire nel browser:

```text
http://127.0.0.1:5000
```

---

## Primo utilizzo

1. Vai nella sezione **Ricerca**.
2. Inserisci la città.
3. Incolla la tua API key Jooble dalle impostazioni dell'app.
4. Controlla le parole chiave precompilate.
5. Usa i **Filtri avanzati** per raffinare la ricerca.
6. Torna alla **Dashboard** e premi **Cerca ora**.

---

## Privacy e sicurezza

Il database locale `radar_lavoro.db` viene creato sul computer dell'utente e non deve essere caricato nel repository.

La API key Jooble va inserita dalle impostazioni dell'app e non deve mai essere salvata direttamente nel codice.

---

## Cosa resta volutamente fuori

Questa versione rimane essenziale e personale:

- nessun account o login;
- nessuna gestione multiutente;
- nessun deploy cloud;
- nessuna API key nel codice;
- nessun caricamento del database locale su GitHub.

---

## Possibili sviluppi futuri

- Aggiungere screenshot della dashboard.
- Migliorare il sistema di ranking.
- Aggiungere esportazione CSV delle candidature.
- Aggiungere grafici sulle candidature inviate.
- Integrare altre fonti di annunci.
- Creare una modalità demo senza API key.

---

## Autore

**Andrea Bartiromo**  
GitHub: [andrea-bartiromo](https://github.com/andrea-bartiromo)
