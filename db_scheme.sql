BEGIN;

CREATE TABLE artist (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL COLLATE NOCASE,
    main_picture_ID INTEGER DEFAULT 0 REFERENCES artist_picture(ID) DEFERRABLE INITIALLY DEFERRED,
    background_picture_ID INTEGER DEFAULT 0 REFERENCES artist_picture(ID) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE artist_picture (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    FILENAME TEXT NOT NULL,
    artist_ID INTEGER NOT NULL REFERENCES artist(ID) ON DELETE CASCADE
);

CREATE TABLE user (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    pw_hash TEXT NOT NULL,
    is_organizer INTEGER NOT NULL CHECK(is_organizer IN (0, 1))
);

CREATE TABLE ticket (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    user_ID INTEGER UNIQUE NOT NULL REFERENCES user(ID),
    first_day INTEGER NOT NULL CHECK(first_day >= 0),
    duration INTEGER NOT NULL CHECK(duration > 0),  -- Controlla valore minimo
    -- Controlla validità durata in corrispondenza col giorno iniziale (controlla anche che il primo giorno rientri nel range)
    CONSTRAINT check_day_and_duration CHECK (
        first_day + duration < 4
    )
);

CREATE TABLE stage (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE performance (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    day INTEGER NOT NULL CHECK(day IN (0, 1, 2)),
    hour INTEGER NOT NULL CHECK(hour >= 0 AND hour< 24),
    minute INTEGER NOT NULL CHECK(minute >= 0 AND minute < 60),
    stage_ID INTEGER NOT NULL REFERENCES stage(ID),
    user_ID INTEGER NOT NULL REFERENCES user(ID),
    artist_ID INTEGER NOT NULL REFERENCES artist(ID),
    duration INTEGER NOT NULL CHECK(duration > 0),
    description TEXT NOT NULL,
    genre TEXT NOT NULL,
    is_published INTEGER NOT NULL DEFAULT 0 CHECK(is_published IN (0, 1))
);

CREATE TABLE ticket_properties (
    duration INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    price_cents INTEGER NOT NULL,
    css_class TEXT NOT NULL
);

COMMIT;

BEGIN;

INSERT INTO stage(name) VALUES ('Main Stage'), ('Side Stage'), ('Outside Stage');

INSERT INTO ticket_properties(duration, name, price_cents, css_class)
VALUES (1, 'Giornaliero', 5999, 'ticket-single'),
(2, 'Pass due giorni', 9999, 'ticket-double'),
(3, 'Full pass', 12999, 'ticket-triple');

COMMIT;

