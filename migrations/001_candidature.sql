-- Radar Lavoro - Migrazione Fase 1: CRM candidature
-- Eseguire una sola volta sul database locale radar_lavoro.db.
-- I comandi sono idempotenti nelle versioni recenti di SQLite grazie a IF NOT EXISTS dove supportato.

ALTER TABLE jobs ADD COLUMN application_status TEXT DEFAULT 'nuovo';
ALTER TABLE jobs ADD COLUMN personal_notes TEXT DEFAULT '';
ALTER TABLE jobs ADD COLUMN applied_at TEXT DEFAULT '';
ALTER TABLE jobs ADD COLUMN last_status_at TEXT DEFAULT '';

UPDATE jobs
   SET application_status = COALESCE(NULLIF(application_status, ''), status, 'nuovo')
 WHERE application_status IS NULL OR application_status = '';
