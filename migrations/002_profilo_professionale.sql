-- Sprint Profilo professionale
-- Migrazione compatibile con SQLite: aggiunge i campi alla tabella profile esistente.
-- L'app usa anche ensure_column per evitare errori se alcune colonne sono gia presenti.

ALTER TABLE profile ADD COLUMN professional_full_name TEXT DEFAULT '';
ALTER TABLE profile ADD COLUMN professional_headline TEXT DEFAULT '';
ALTER TABLE profile ADD COLUMN education TEXT DEFAULT '';
ALTER TABLE profile ADD COLUMN education_items TEXT DEFAULT '[]';
ALTER TABLE profile ADD COLUMN experiences TEXT DEFAULT '[]';
ALTER TABLE profile ADD COLUMN certifications TEXT DEFAULT '[]';
ALTER TABLE profile ADD COLUMN location_preference TEXT DEFAULT '';
ALTER TABLE profile ADD COLUMN territorial_preferences TEXT DEFAULT '[]';
ALTER TABLE profile ADD COLUMN availability TEXT DEFAULT '';
ALTER TABLE profile ADD COLUMN protected_category_notes TEXT DEFAULT '';
ALTER TABLE profile ADD COLUMN protected_categories TEXT DEFAULT '[]';
ALTER TABLE profile ADD COLUMN strong_preferences TEXT DEFAULT '[]';
ALTER TABLE profile ADD COLUMN soft_preferences TEXT DEFAULT '[]';
ALTER TABLE profile ADD COLUMN skills TEXT DEFAULT '[]';
ALTER TABLE profile ADD COLUMN technical_skills TEXT DEFAULT '[]';
ALTER TABLE profile ADD COLUMN target_roles TEXT DEFAULT '[]';
ALTER TABLE profile ADD COLUMN profile_notes TEXT DEFAULT '';
ALTER TABLE profile ADD COLUMN profile_updated_at TEXT DEFAULT '';
ALTER TABLE profile ADD COLUMN profile_schema_version TEXT DEFAULT '';
