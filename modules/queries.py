import sqlite3
from typing import Any
from werkzeug.security import generate_password_hash
import modules

DB_FILENAME = "database.db"
START_TIMESTAMP_CALCULATION = "day * 60 * 24 + hour * 60 + minute "
END_TIMESTAMP_CALCULATION = START_TIMESTAMP_CALCULATION + "+ duration"
PERFORMANCE_ORDER_BY = "ORDER BY day, hour, minute, duration, stage_ID"
PERFORMANCE_SELECT_STATEMENT = f"""
    -- Rinomina colonne con come comune per renderle distinguibili da Python
    SELECT *, 
    A.name AS artist_name, 
    S.name AS stage_name, 
    P.ID AS performance_ID, 
    A.ID AS artist_ID, 
    U.ID AS organizer_ID,
    U.first_name AS organizer_first_name,
    U.last_name AS organizer_last_name
    FROM performance P 
    INNER JOIN artist A ON P.artist_ID = A.ID
    INNER JOIN stage S ON P.stage_ID = S.ID
    INNER JOIN user U ON U.ID = P.user_ID
"""


def __do_execute(query: str, params: tuple[Any, ...] | list[Any, ...] = ()) -> None:
    conn = sqlite3.connect(DB_FILENAME)
    conn.execute("PRAGMA foreign_keys = 1")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    cursor.close()
    conn.commit()
    conn.close()

def __do_fetchone(query: str, params: tuple[Any, ...] | list[Any, ...] = ()) -> sqlite3.Row | None:
    conn = sqlite3.connect(DB_FILENAME)
    conn.execute("PRAGMA foreign_keys = 1")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return result

def __do_fetchall(query: str, params: tuple[Any, ...] | list[Any, ...] = ()) -> list[sqlite3.Row] | None:
    conn = sqlite3.connect(DB_FILENAME)
    conn.execute("PRAGMA foreign_keys = 1")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    return result

def get_user_by_email(email: str) -> sqlite3.Row | None:
    sql = "SELECT * FROM user WHERE email = ?"
    return __do_fetchone(sql, (email,))

def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    sql = "SELECT * FROM user WHERE id = ?"
    return __do_fetchone(sql, (user_id,))

def create_new_user(first_name: str, last_name: str, email: str, password: str, is_organizer: bool):
    sql = "INSERT INTO user(first_name, last_name, email, pw_hash, is_organizer) VALUES (?, ?, ?, ?, ?)"
    __do_execute(sql, (first_name, last_name, email, generate_password_hash(password), int(is_organizer)))

def get_performances(
        exclude_user_id: int | None = None,
        filter_user_id: int | None = None,
        filter_published_status: bool | None = None,
        performance_id: int | None = None,
        stage_id: int | None = None,
        day: modules.values.Days | None = None,
        genre: str | None = None
) -> list[sqlite3.Row]:
    sql = f"""
    {PERFORMANCE_SELECT_STATEMENT}
    -- Condizione fittizia sempre vera per concatenare facilmente le condizioni facoltative
    WHERE 1
    -- Includi performance solo di uno specifico utente se filter_user_id è specificato
    {"AND P.user_id = ?" if filter_user_id is not None else ""} 
    -- Escludi performance di uno specifico utente se exclude_user_id è specificato
    {"AND P.user_id != ?" if exclude_user_id is not None else ""}
    -- Filtra solo per pubblicate o non se published_only è specificato
    {f"AND P.is_published = ?" if filter_published_status is not None else ""}
    -- Filtra solo per un ID performance se performance_id è specificato
    {f"AND P.ID = ?" if performance_id is not None else ""}
    --- Filtra per ID palco se stage_id è specificato
    {f"AND P.stage_ID = ?" if stage_id is not None else ""}
    --- Filtra per giorno se day è specificato
    {f"AND P.day = ?" if day is not None else ""}
    -- Filtra per genere se è specificato
    {f"AND P.genre = ?" if genre is not None else ""}
    {PERFORMANCE_ORDER_BY}
"""
    params = []
    if exclude_user_id is not None:
        params.append(exclude_user_id)
    if filter_user_id is not None:
        params.append(filter_user_id)
    if filter_published_status is not None:
        params.append(filter_published_status)
    if performance_id is not None:
        params.append(performance_id)
    if stage_id is not None:
        params.append(stage_id)
    if day is not None:
        params.append(day)
    if genre is not None:
        params.append(genre)

    return __do_fetchall(sql, params)

def get_performance(performance_id: int) -> sqlite3.Row:
    return sel[0] if (sel := get_performances(performance_id=performance_id)) else None

def get_pictures_from_performance(performance_id: int) -> list[sqlite3.Row] | None:
    sql = """
    SELECT *, AP.ID AS picture_ID, A.ID as artist_ID
    FROM artist_picture AP 
    JOIN performance P ON AP.artist_ID = P.artist_ID 
    JOIN artist A on AP.artist_ID = A.ID
    WHERE P.ID = ?"""
    return __do_fetchall(sql, (performance_id,))

def get_overlapping_performances(stage_id: int, day: int, hour: int, minute: int, duration: int, published_only: bool | None, ignore_id: int | None) -> list[sqlite3.Row] | None:
    start_timestamp = day * 60 * 24 + hour * 60 + minute
    end_timestamp = start_timestamp + duration

    sql = f"""
    { PERFORMANCE_SELECT_STATEMENT } 
    -- Negli schemi, [++++] rappresenta comparing_performance e |>----<| eventuali eventi sovrapposti
    -- Filtra solo performance con lo stesso stage
    WHERE stage_ID == ?
    -- Filtra se è presente un ID performance da ignorare
    {f"AND P.ID != ? --ignore_id" if ignore_id else ""}
    -- Filtra se richiesto solo eventi già pubblicati o non
    {f"AND is_published == ? --published_only" if published_only else ""}
    -- Trova eventi che si sovrappongono "da sinistra", ovvero che iniziano prima dell'evento corrente ma che finiscono dopo l'orario di inizio di questo
    -- |>----[+-<|+++++]
    -- |>----[+-+-+-]-<|
    AND (
            (
                {START_TIMESTAMP_CALCULATION} <
                ? --start_timestamp
            AND 
                {END_TIMESTAMP_CALCULATION} > 
                ? --start_timestamp
            )
    -- Trova eventi che si sovrappongono "da destra", ovvero che iniziano dopo dell'evento corrente ma prima che questo sia finito 
    -- (maggiore e uguale per coprire anche eventi con la stessa ora d'inizio)
    -- [++++|>+-+-]----<|
    -- [++++|>+-+-<|++++]
        OR (
                {START_TIMESTAMP_CALCULATION} >= 
                ? --start_timestamp
            AND 
                {START_TIMESTAMP_CALCULATION} < 
                ? --end_timestamp
            )
        )
    {PERFORMANCE_ORDER_BY}
    """

    # Costruzione della lista di params
    params = [stage_id]
    if ignore_id:
        params.append(ignore_id)
    if published_only:
        params.append(published_only)
    params += [start_timestamp, start_timestamp, start_timestamp, end_timestamp]

    return __do_fetchall(sql, params)

def update_performance(performance_id: int, stage_id: int, day: int, hour: int, minute: int, duration: int, description: str, genre: str) -> int:
    sql = """UPDATE performance
    SET stage_ID = ?, day = ?, hour = ?, minute = ?, duration = ?, description = ?, genre = ?
    WHERE ID = ?"""
    __do_execute(sql, (stage_id, day, hour, minute, duration, description, genre, performance_id))

def publish_performance(id: int) -> None:
    sql = "UPDATE performance SET is_published = 1 WHERE ID = ?"
    __do_execute(sql, (id,))

def get_all_stages() -> list[sqlite3.Row]:
    sql = "SELECT * FROM stage"
    return __do_fetchall(sql)

def create_artist(artist_name: str, main_picture_fname: str, background_picture_fname: str) -> int:
    """Returns the ID of the inserted artist"""
    conn = sqlite3.connect(DB_FILENAME)
    conn.execute("PRAGMA foreign_keys = 1")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = "BEGIN"
    cursor.execute(sql)
    try:
        sql = "INSERT INTO artist(name) VALUES (?) "
        cursor.execute(sql, (artist_name,))
        sql = "SELECT ID FROM artist WHERE name = ? "
        artist_id = int(cursor.execute(sql, (artist_name,)).fetchone()["ID"])
        sql = "INSERT INTO artist_picture(filename, artist_ID) VALUES (?, ?)"
        cursor.execute(sql, (main_picture_fname, artist_id))
        main_picture_id = cursor.lastrowid
        sql = "INSERT INTO artist_picture(filename, artist_ID) VALUES (?, ?)"
        cursor.execute(sql, (background_picture_fname, artist_id))
        background_picture_id = cursor.lastrowid
        sql = "UPDATE artist SET main_picture_ID = ?, background_picture_ID = ? WHERE ID = ?"
        cursor.execute(sql, (main_picture_id, background_picture_id, artist_id))
        sql = "COMMIT"
    except sqlite3.IntegrityError:
        sql = "ROLLBACK"
    finally:
        cursor.execute(sql)
        cursor.close()
        conn.commit()
        conn.close()
    return artist_id

def create_performance(stage_id: int, day: int, hour: int, minute: int, duration: int, description: str, genre: str, user_id: int, artist_id: int) -> int:
    sql = """INSERT INTO performance(stage_ID, day, hour, minute, duration, description, genre, user_ID, artist_ID) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    __do_execute(sql, (stage_id, day, hour, minute, duration, description, genre, user_id, artist_id))

def delete_performance_and_artist(performance_id: int) -> set[str]:
    """Restituisce un insieme di filename delle immagini dell'artista eliminato (non si occupa dell'eliminazione)"""
    conn = sqlite3.connect(DB_FILENAME)
    conn.execute("PRAGMA foreign_keys = 1")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Ottieni e memorizza filename delle immagini dell'artista associato
    filenames = set()
    sql = "SELECT FILENAME FROM artist_picture AP JOIN artist A ON AP.artist_ID = A.ID JOIN performance P ON P.artist_ID = A.ID  WHERE P.ID = ?"
    for fn in cursor.execute(sql, (performance_id,)).fetchall():
        filenames.add(fn["FILENAME"])
    sql = "BEGIN"
    cursor.execute(sql)
    # Elimina performance
    sql = "DELETE FROM performance WHERE ID = ? RETURNING artist_ID"
    artist_id = cursor.execute(sql, (performance_id,)).fetchone()["artist_ID"]
    # Elimina artista, le immagini si eliminano automaticamente perché hanno CASCADE
    sql = "DELETE FROM artist WHERE ID = ?"
    cursor.execute(sql, (artist_id,))
    sql = "COMMIT"
    cursor.execute(sql)
    cursor.close()
    conn.commit()
    conn.close()
    return filenames

def get_artist_by_name(name: str) -> sqlite3.Row:
    sql = "SELECT * FROM artist WHERE name = ?"
    return __do_fetchone(sql, (name,))

def get_last_artist_picture_rowid() -> int:
    sql = "SELECT seq FROM sqlite_sequence WHERE name = ?"
    res = __do_fetchone(sql, ("artist_picture",))
    if res:
        return int(res["seq"])
    else:
        return 0

def create_picture(fname: str, artist_id: int) -> int:
    sql = "INSERT INTO artist_picture(filename, artist_ID) VALUES (?, ?)"
    __do_execute(sql, (fname, artist_id))

def delete_pictures(ids: set[int]) -> list[sqlite3.Row]:
    sql = f"DELETE FROM artist_picture WHERE ID IN ({",".join("?" for i in ids)}) RETURNING FILENAME"
    return __do_fetchall(sql, (tuple(i for i in ids)))

def get_number_of_sold_tickets_for_day(day: int) -> int:
    sql = f"""SELECT COUNT(*) AS count
    FROM ticket 
    WHERE first_day <= ? 
    AND first_day + duration > ?"""
    return __do_fetchone(sql, (day, day))["count"]

def get_ticket_statistics(first_day: int, duration: int) -> int:
    """Ottieni statistiche di un certo tipo di biglietto per una certa giornata"""
    sql = "SELECT COUNT(*) AS count FROM ticket WHERE first_day = ? AND duration = ?"
    return __do_fetchone(sql, (first_day, duration))["count"]

def get_ticket_of_user(user_id: int) -> sqlite3.Row | None:
    sql = "SELECT * FROM ticket WHERE user_id = ?"
    return __do_fetchone(sql, (user_id,))

def create_ticket_for_user(user_id: int, first_day: int, duration: int) -> int:
    """Restituisce l'ID del biglietto creato"""
    sql = "INSERT INTO ticket(user_ID, first_day, duration) VALUES (?, ?, ?) RETURNING ID"
    return __do_fetchone(sql, (user_id, first_day, duration))["ID"]

def get_artist_pictures(artist_id: int) -> list[sqlite3.Row]:
    """Restituisce anche colonne is_main_picture, is_background_picture, is_other_picture"""
    sql = f"""
    SELECT *, AP.ID AS picture_ID, 
    AP.ID = A.main_picture_ID AS is_main_picture, 
    AP.ID = A.background_picture_ID AS is_background_picture,
    AP.ID NOT IN (A.main_picture_ID, A.background_picture_ID) AS is_other_picture
    FROM artist_picture AP JOIN artist A ON A.ID = AP.artist_ID
    WHERE artist_ID = ?
    ORDER BY AP.ID
    """
    return __do_fetchall(sql, (artist_id,))

def get_user_pw_hash_from_email(email: str) -> str | None:
    sql = "SELECT pw_hash FROM user WHERE email = ?"
    return __do_fetchone(sql, (email,))["pw_hash"]

def update_artist(artist_id: int, name: str, main_picture_id: int, background_picture_id: int) -> None:
    sql = "UPDATE artist SET name = ?, main_picture_ID = ?, background_picture_ID = ? WHERE ID = ?"
    __do_execute(sql, (name, main_picture_id, background_picture_id, artist_id))

def get_all_tickets_properties() -> list[sqlite3.Row] | None:
    sql = "SELECT * FROM ticket_properties ORDER BY duration"
    return __do_fetchall(sql)

def get_ticket_properties(duration: int) -> sqlite3.Row | None:
    sql = "SELECT * FROM ticket_properties WHERE duration = ?"
    return __do_fetchone(sql, (duration,))