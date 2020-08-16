/* Enable Foreign Keys.  This needs to be executed for each database
connection as it feaults to disabled. */

PRAGMA foreign_keys = ON;

/* Create a Version table, giving the version number of this database
instance. Insert the version number */

CREATE TABLE Version (
       version INTEGER NOT NULL
);
INSERT INTO Version (version) VALUES (1); /* This version */


/* Create Settings table. */

CREATE TABLE Settings (
       key TEXT PRIMARY KEY,
       value TEXT
);
