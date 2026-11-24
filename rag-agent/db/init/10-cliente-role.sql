-- =============================================================
-- Migración: Agregar rol 'cliente' al CHECK constraint de users
-- =============================================================

DO $$
DECLARE
    cname text;
BEGIN
    SELECT conname INTO cname
    FROM pg_constraint
    WHERE conrelid = 'users'::regclass
    AND contype = 'c'
    AND pg_get_constraintdef(oid) LIKE '%role%';

    IF cname IS NOT NULL THEN
        EXECUTE 'ALTER TABLE users DROP CONSTRAINT ' || cname;
    END IF;
END $$;

ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('admin', 'user', 'cliente'));

COMMENT ON COLUMN users.role IS 'admin | user | cliente';
