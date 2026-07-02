# Radar Lavoro — il tuo aggregatore personale

Versione semplificata, pensata per un solo utente: nessun account, nessun
login, nessuna complessità multi-utente. Cerca offerte di lavoro nella città
che scegli tu, con parole chiave già precompilate in base al tuo profilo
(comunicazione, social media, digital, giornalismo), e ti mostra solo le
novità con un'interfaccia pulita.

## Installazione

```bash
pip install -r requirements.txt
```

## Avvio

```bash
python app.py
```

Poi apri **http://127.0.0.1:5000**

## Primo utilizzo

1. Vai in **Impostazioni**
2. Inserisci la tua città
3. Incolla la tua API key Jooble (da **it.jooble.org/api/about** — dominio italiano, non jooble.org)
4. Le parole chiave sono già precompilate in base al tuo profilo — modificale liberamente
5. Salva, torna alla Dashboard, premi **"Cerca ora"**

## Come funziona

- Ogni volta che premi "Cerca ora", lo strumento interroga Jooble con tutte le tue parole chiave nella tua città
- Gli annunci già visti non vengono più mostrati come "nuovi" alle ricerche successive
- Puoi segnare un singolo annuncio come visto, oppure usare "Segna tutti come visti" per svuotare la lista dei nuovi
- Tutto resta salvato in un database locale (`radar_lavoro.db`) sul tuo computer

## Cosa è stato tolto rispetto alle versioni precedenti

Su richiesta esplicita, questa versione torna volutamente essenziale:
- Nessun account/login (l'avevamo aggiunto pensando a un uso multi-utente, non più necessario ora)
- Nessun valutatore di bandi PDF (era una funzionalità separata, aggiungibile in futuro se serve)
- Nessuna delle protezioni pensate per un lancio pubblico (CSRF, blocco brute-force, ecc.) — non servono per uno strumento che gira solo sul tuo computer, per te

Se in futuro vorrai di nuovo condividerlo con altre persone o metterlo online,
sappi che quelle funzionalità esistono già in una versione precedente e
possono essere reintegrate.
