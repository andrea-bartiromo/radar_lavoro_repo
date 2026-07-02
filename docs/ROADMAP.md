# Roadmap Radar Lavoro

## Obiettivo personale

Radar Lavoro deve diventare un assistente personale per la ricerca di lavoro:
non solo un elenco di annunci, ma uno strumento capace di trovare, filtrare,
ordinare e spiegare le opportunità più adatte al profilo di Andrea.

## Fase 1 - Core Engine

Obiettivo: rendere il motore interno stabile, leggibile e modulare.

Attività principali:

- completare il refactoring di `app.py`;
- collegare realmente `SourceManager`;
- spostare la logica SQL nei repository;
- usare `matching_service` e `ranking_service` come motori ufficiali;
- introdurre diagnostica della ricerca;
- rendere affidabile il filtro geografico.

## Fase 2 - Multi fonte

Obiettivo: non dipendere solo da Jooble.

Fonti previste:

- Jooble;
- Remotive;
- EURES;
- ClicLavoro;
- InPA;
- altre fonti utilizzabili in modo conforme.

Ogni fonte dovrà restituire annunci in formato normalizzato.

## Fase 3 - Archivio candidature

Obiettivo: trasformare Radar in un piccolo CRM personale.

Stati previsti:

- nuovo;
- già visto;
- preferito;
- candidatura inviata;
- colloquio;
- scartato;
- assunto.

## Fase 4 - Radar AI

Obiettivo: spiegare il motivo del ranking.

Radar dovrà mostrare:

- perché un annuncio è consigliato;
- quali requisiti sono coperti;
- quali competenze mancano;
- quanto conviene candidarsi;
- come migliorare il profilo.

## Principio guida

Qualità delle opportunità prima della quantità degli annunci.
