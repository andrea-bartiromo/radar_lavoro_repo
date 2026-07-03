# Sistema candidature

Obiettivo: trasformare Radar Lavoro da semplice elenco di offerte a CRM personale per seguire ogni candidatura.

## Stati candidatura

Ogni offerta puo trovarsi in uno di questi stati:

| Stato tecnico | Etichetta UI | Significato |
| --- | --- | --- |
| `nuovo` | Nuovo | Offerta appena trovata e non ancora valutata |
| `visto` | Visto | Offerta letta ma senza decisione |
| `salvato` | Salvato | Offerta interessante da riprendere |
| `cv_preparato` | CV preparato | CV o documenti pronti per candidarsi |
| `candidatura_inviata` | Candidatura inviata | Candidatura effettivamente mandata |
| `colloquio` | Colloquio | Colloquio fissato o in corso |
| `scartato` | Scartato | Offerta non interessante o non adatta |
| `assunto` | Assunto | Esito positivo |

## Campi da aggiungere alla tabella jobs

```sql
ALTER TABLE jobs ADD COLUMN application_status TEXT DEFAULT 'nuovo';
ALTER TABLE jobs ADD COLUMN personal_notes TEXT DEFAULT '';
ALTER TABLE jobs ADD COLUMN applied_at TEXT DEFAULT '';
ALTER TABLE jobs ADD COLUMN last_status_at TEXT DEFAULT '';
```

Per compatibilita con la versione attuale, il campo `status` puo rimanere temporaneamente usato per distinguere nuovi/visti. La nuova logica deve usare `application_status`.

## Funzioni backend da aggiungere

```python
APPLICATION_STATUS_OPTIONS = {
    "nuovo": "Nuovo",
    "visto": "Visto",
    "salvato": "Salvato",
    "cv_preparato": "CV preparato",
    "candidatura_inviata": "Candidatura inviata",
    "colloquio": "Colloquio",
    "scartato": "Scartato",
    "assunto": "Assunto",
}
```

Nuova route Flask:

```python
@app.route("/candidatura/<int:job_id>", methods=["POST"])
def aggiorna_candidatura(job_id):
    profile = get_profile()
    new_status = request.form.get("application_status", "visto")
    notes = request.form.get("personal_notes", "").strip()
    if new_status not in APPLICATION_STATUS_OPTIONS:
        new_status = "visto"
    applied_at = datetime.now().isoformat(timespec="minutes") if new_status == "candidatura_inviata" else ""
    conn = get_db()
    conn.execute(
        """UPDATE jobs
           SET application_status=?, personal_notes=?, applied_at=COALESCE(NULLIF(applied_at, ''), ?),
               last_status_at=?, status=CASE WHEN status='nuovo' THEN 'visto' ELSE status END
           WHERE id=? AND search_location=?""",
        (new_status, notes, applied_at, datetime.now().isoformat(timespec="minutes"), job_id, profile["search_location"]),
    )
    conn.commit()
    conn.close()
    flash("Candidatura aggiornata.", "successo")
    return redirect(url_for("dashboard"))
```

## Modifiche alla dashboard

Ogni card offerta deve mostrare:

- selettore stato candidatura;
- campo note personali;
- eventuale data candidatura;
- pulsante `Salva candidatura`.

## Statistiche successive

Quando il sistema candidature sara stabile, la pagina Statistiche dovra mostrare:

- offerte nuove;
- offerte salvate;
- candidature inviate;
- colloqui ottenuti;
- offerte scartate;
- percentuale colloqui/candidature.

## Regole UX

- Lo stato `scartato` non elimina l'offerta: la nasconde o la sposta in basso.
- Lo stato `salvato` deve rendere l'offerta facile da ritrovare.
- Le note devono restare solo nel database locale.
- Nessun dato sensibile va caricato nel repository.
