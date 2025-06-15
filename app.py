import logging
import os
import re
import pyotp
from flask import Flask, render_template, request, url_for, redirect, session, abort, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from modules import *

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config["SECRET_KEY"] = "stringa super segreta"

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id: str):
    # Carica utente
    user_sel = queries.get_user_by_id(int(user_id))
    if user_sel is None:
        return None
    # Carica biglietto (se presente)
    ticket_sel = queries.get_ticket_of_user(int(user_id))
    if ticket_sel is None:
        ticket = None
    else:
        # Istanzia biglietto
        ticket = user_classes.Ticket(
            id=ticket_sel["ID"],
            first_day=ticket_sel["first_day"],
            duration=ticket_sel["duration"]
        )

    # Istanzia utente
    user = user_classes.User(
        id = user_sel["ID"],
        email = user_sel["email"],
        first_name = user_sel["first_name"],
        last_name = user_sel["last_name"],
        is_organizer = bool(user_sel["is_organizer"]),
        ticket=ticket
    )
    return user

@app.route("/")
def site_root_page():
    return render_template(
        "home.html"
    )

@app.route("/accesso")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("site_root_page"))

    return render_template(
        "login.html",
    )


@app.route("/es_accesso", methods=["POST"])
def do_login():
    err = None # Inizializza variabile errore
    data = request.form.to_dict() # Carica dati form

    # Imposta stringhe vuote se i campi mancano
    email = data.get("email", "")
    password = data.get("password", "")

    # Controlla se i campi sono stringhe vuote
    if "" in (email, password):
        err = errors.LoginErrorCodes.EMPTY_FIELDS
    else:
        # Prova ad accedere
        # Carica utente in base alla mail
        if (user_sel := queries.get_user_by_email(email)) is None:
            # Imposta errore se l'utente non è stato trovato
            err = errors.LoginErrorCodes.USER_NOT_FOUND
        else:
            pw_hash = queries.get_user_pw_hash_from_email(email)
            # Controlla che la password corrisponda
            if check_password_hash(pw_hash, password):
                login_user(load_user(user_sel["ID"]))
            else:
                # Se la password non corrisponde, imposta errore
                err = errors.LoginErrorCodes.WRONG_PASSWORD

    if err is not None:
        flash(errors.get_login_error_message(err), "error")
        return redirect(url_for("login_page"))
    else:
        return redirect(url_for("site_root_page"))


@app.route("/registrazione")
def registration_page():
    if current_user.is_authenticated:
        return redirect(url_for("site_root_page"))

    return render_template(
        "register.html"
    )


@app.route("/es_registrazione", methods=["POST"])
def do_register():
    err = None  # Inizializza variabile errore
    data = request.form.to_dict()

    valid_otp = pyotp.TOTP(values.OTP_KEY).now()

    #Regex per controllare la mail. Non è perfetto, ma un regex che segue esattamente lo standard è estremamente complesso
    EMAIL_REGEX = r"[\w_+.]+@[a-zA-Z\-]+\.[a-zA-Z-\.]+"
    # Regex per contollare l'OTP, supporta XXX-XXX, XXXXXX, XXX XXX
    OTP_REGEX = r"[\d]{3}[ -]?[\d]{3}"

    # Imposta stringhe vuote se i campi mancano
    first_name = data.get("first-name", "")
    last_name = data.get("last-name", "")
    email = data.get("email", "")
    password = data.get("password", "")
    otp = data.get("otp", "")

    # Controlla se i campi sono stringhe vuote
    if "" in (email, password, first_name, last_name):
        err = errors.RegistrationErrorCodes.EMPTY_FIELDS
    # Controlla email
    elif not re.match(EMAIL_REGEX, email):
        err = errors.RegistrationErrorCodes.INVALID_EMAIL
    # Controlla password
    elif len(password) < 8:
        err = errors.RegistrationErrorCodes.INVALID_PASSWORD
    # Controlla OTP
    elif otp and not re.match(OTP_REGEX, otp):
        err = errors.RegistrationErrorCodes.INVALID_OTP
    elif otp and re.sub("[ -]", "", otp) != valid_otp:
        err = errors.RegistrationErrorCodes.WRONG_OTP
    else:
        # Imposta valore in base all'OTP
        is_organizer = True if otp else False
        # Prova a registrare l'utente
        # Seleziona utente in base alla mail per verificare se esiste già
        if queries.get_user_by_email(email) is None:
            queries.create_new_user(first_name, last_name, email, password, bool(is_organizer))
        else:
            err = errors.RegistrationErrorCodes.EMAIL_EXISTS

    if err is not None:
        flash(errors.get_registration_error_message(err), "error")
        return redirect(url_for("registration_page"))
    else:
        flash(success.get_registration_success_message(success.RegistrationSuccess.SUCCESS), "success")
        return redirect(url_for("site_root_page"))

@app.route("/esci")
@login_required
def do_logout():
    logout_user()
    return redirect(url_for("site_root_page"))

@app.route("/gestione")
@login_required
def manager_page():
    if not current_user.is_organizer:
        return abort(403)

    # Seleziona performance pubblicate e bozze dell'utente
    published = performance_classes.get_performance_instances(filter_published_status=True)
    drafts = performance_classes.get_performance_instances_with_overlaps(filter_user_id=current_user.id, filter_published_status=False)

    return render_template(
        "manager.html",
        drafts=drafts,
        published=published,
        day_names=values.get_all_days()
    )

@app.route("/gestione/aggiunta_performance")
@login_required
def add_performance_page():
    if not current_user.is_organizer:
        return abort(403)

    form_data = session.pop("add_performance_form_data", {}) # Recupera dati salvati se l'aggiunta è fallita
    return render_template(
        "add_performance.html",
        stages=performance_classes.get_all_stages_instances(),
        days=values.get_all_days(),
        form_data=form_data,
        int=int
    )

@app.route("/gestione/es_aggiunta_performance", methods=["POST"])
@login_required
def do_add_performance():
    if not current_user.is_organizer:
        return abort(403)

    err = None  # Inizializza variabile errore
    overlaps = None
    data = request.form.to_dict()

    # Imposta stringhe vuote/None se i campi mancano
    day = data.get("day", None)
    time = data.get("time", None)
    duration = data.get("duration", None)
    stage_id = data.get("stage", None)
    genre = data.get("genre", "")
    description = data.get("description", "")
    artist_name = data.get("artist-name", "")
    artist_main_picture = request.files.get("artist-main-picture", None)
    artist_background_picture = request.files.get("artist-background-picture", None)
    artist_other_pictures = request.files.getlist("artist-other-pictures")

    # Controlla se mancano dati
    if None in (day, time, duration, stage_id, artist_main_picture, artist_background_picture)\
        or "" in (genre, artist_name, description)\
            or "" in (artist_main_picture.filename, artist_background_picture.filename):
        err = errors.PerformanceManagingErrorCodes.MISSING_DATA
    else:
        try:
            # Controlla se i dati numerici sono validi
            day = int(day)
            hour, minute = time.split(":")
            hour = int(hour)
            minute = int(minute)
            duration = int(duration)
            stage_id = int(stage_id)

            # Ottieni tutti gli ID dei palchi presenti nel database
            stage_ids = set(performance_classes.get_all_stages_instances())

            # Controlla validità dei dati temporali e palco
            if day not in values.get_all_days().keys() or not (0 <= hour < 24) \
                or not (0 <= minute < 60) or stage_id not in stage_ids or duration < 1:
                raise ValueError

        except (ValueError, IndexError):
            err = errors.PerformanceManagingErrorCodes.INVALID_DATA
        
        else:
            # Controlla se ci sono sovrapposizioni con eventi pubblicati
            if overlaps := performance_classes.get_overlapping_performances(
                    stage_id=stage_id,
                    day=values.Days(day),
                    hour=hour,
                    minute=minute,
                    duration=duration,
                    published_only=True,
                    ignore_id=None
            ):
                err = errors.PerformanceManagingErrorCodes.OVERLAP_WITH_PUBLISHED
                overlaps_text_lines = [f"{p.artist.name} - {values.get_day_name(p.day)} {p.time_string} {p.duration}min" for p in overlaps.values()]
            # Controlla se il nome dell'artista è già utilizzato (case-insensitive a livello di db)
            elif queries.get_artist_by_name(artist_name):
                err = errors.PerformanceManagingErrorCodes.ARTIST_NAME_EXISTS
            else:
                # Ottieni prossimi ID delle immagini per aggiungerli al filename
                last_artist_picture_id = queries.get_last_artist_picture_rowid()
                main_picture_fname = f"{last_artist_picture_id + 1}_{secure_filename(artist_main_picture.filename)}"
                background_picture_fname = f"{last_artist_picture_id + 2}_{secure_filename(artist_background_picture.filename)}"
                # Salva immagini
                artist_main_picture.save(f"static/uploads/{main_picture_fname}")
                artist_background_picture.save(f"static/uploads/{background_picture_fname}")
                # Inserisci artista (la funzione restituisce l'ID dell'artista appena inserito)
                artist_id = queries.create_artist(
                    artist_name=artist_name,
                    main_picture_fname=main_picture_fname,
                    background_picture_fname=background_picture_fname
                )
                # Inserisci performance
                queries.create_performance(
                    stage_id=stage_id,
                    day=day,
                    hour=hour,
                    minute=minute,
                    duration=duration,
                    description=description,
                    genre=genre,
                    user_id=int(current_user.id),
                    artist_id=artist_id
                )
                # Salva e inserisci immagini extra
                for index, file in enumerate(artist_other_pictures):
                    if not file.filename == "":
                        fname = f"{last_artist_picture_id + index + 3}_{secure_filename(file.filename)}"
                        file.save(f"static/uploads/{fname}")
                        queries.create_picture(fname, artist_id)

    if err is not None:
        flash(f"{errors.get_performance_managing_error_message(err)}"
              f"\n{"\n".join(overlaps_text_lines) if overlaps else ""}", "error")
        flash(values.FILES_RELOAD_WARNING, "error")
        session["add_performance_form_data"] = data
        return redirect(url_for("add_performance_page"))
    else:
        flash(success.get_performance_managing_success_message(success.PerformanceManagingSuccess.ADD_SUCCESS), "success")
        return redirect(url_for("manager_page"))

@app.route("/gestione/es_eliminazione_performance", methods=["POST"])
@login_required
def do_delete_performance():
    if not current_user.is_organizer:
        return abort(403)

    err = None  # Inizializza variabile errore
    data = request.form.to_dict()

    # Ottieni ID performance dall'input nascosto
    performance_id = data.get("performance-id", None)
    if performance_id:
        # Controlla validità dato numerico
        try:
            performance_id = int(performance_id)
        except ValueError:
            err = errors.PerformanceManagingErrorCodes.INVALID_PERFORMANCE_ID
        else:
            # Carica performance dal database
            performance = performance_classes.get_single_performance_instance(performance_id)

            # Controlla che la performance esista del database
            if performance is None:
                err = errors.PerformanceManagingErrorCodes.PERFORMANCE_ID_NOT_FOUND
            # Controlla che l'utente sia l'autore della performance
            elif int(performance.organizer.id) != int(current_user.id):
                err = errors.PerformanceManagingErrorCodes.OWNER_MISMATCH
            # Controlla che la performance non sia già stata pubblicata
            elif bool(performance.is_published):
                err = errors.PerformanceManagingErrorCodes.PERFORMANCE_ALREADY_PUBLISHED
            else:
                # Elimina performance e immagini
                filenames = queries.delete_performance_and_artist(performance_id)
                for fn in filenames:
                    os.remove(f"static/uploads/{fn}")
    else:
        err = errors.errors.PerformanceManagingErrorCodes.MISSING_PERFORMANCE_ID

    if err is not None:
        flash(errors.get_performance_managing_error_message(err), "error")
    else:
        flash(success.get_performance_managing_success_message(success.PerformanceManagingSuccess.DELETE_SUCCESS), "success")

    return redirect(url_for("manager_page"))

@app.route("/gestione/es_pubblicazione_performance", methods=["POST"])
@login_required
def do_publish_performance():
    if not current_user.is_organizer:
        return abort(403)

    err = None  # Inizializza variabile errore
    data = request.form.to_dict()

    # Ottieni ID performance nell'input nascosto
    performance_id = data.get("performance-id", None)
    if performance_id:
        # Controlla validità dato numerico
        try:
            performance_id = int(performance_id)
        except ValueError:
            err = errors.PerformanceManagingErrorCodes.INVALID_PERFORMANCE_ID
        else:
            # Seleziona performance dal database
            performance = performance_classes.get_single_performance_instance(performance_id, find_overlaps=True)

            # Controlla che la performance esista nel database
            if performance is None:
                err = errors.PerformanceManagingErrorCodes.PERFORMANCE_ID_NOT_FOUND
            # Controlla che l'utente sia l'autore della performance
            elif int(performance.organizer.id) != int(current_user.id):
                err = errors.PerformanceManagingErrorCodes.OWNER_MISMATCH
            # Controlla che la performance non sia già stata pubblicata
            elif bool(performance.is_published):
                err = errors.PerformanceManagingErrorCodes.PERFORMANCE_ALREADY_PUBLISHED
            # Controlla che la performance non si sovrapponi
            elif performance.is_overlapping:
                overlaps_text_lines = [f"{p.artist.name} - {values.get_day_name(p.day)} {p.time_string} {p.duration}min" for p in performance.overlaps.values()]
                err = errors.PerformanceManagingErrorCodes.OVERLAP_WITH_PUBLISHED
            else:
                queries.publish_performance(performance_id)
    else:
        err = errors.PerformanceManagingErrorCodes.MISSING_PERFORMANCE_ID

    if err is not None:
        flash(f"{errors.get_performance_managing_error_message(err)}"
              f"\n{"\n".join(overlaps_text_lines) if performance.is_overlapping else ""}", "error")
    else:
        flash(success.get_performance_managing_success_message(success.PerformanceManagingSuccess.PUBLISH_SUCCESS), "success")

    return redirect(url_for("manager_page"))

@app.route("/gestione/modifica_performance/<int:performance_id>")
@login_required
def edit_performance_page(performance_id: int):
    if not current_user.is_organizer:
        abort(403)

    err = None  # Inizializza variabile errore
    form_data = session.pop("edit_performance_form_data", None)

    # Ottieni ID performance
    if performance_id:
        # Controlla validità dato numerico
        try:
            performance_id = int(performance_id)
        except ValueError:
            err = errors.PerformanceManagingErrorCodes.INVALID_PERFORMANCE_ID
        else:
            # Carica performance dal database
            performance = performance_classes.get_single_performance_instance(performance_id, find_overlaps=True)

            # Controlla che la performance esista del database
            if performance is None:
                err = errors.PerformanceManagingErrorCodes.PERFORMANCE_ID_NOT_FOUND
            # Controlla che l'utente sia l'autore della performance
            elif int(performance.organizer.id) != int(current_user.id):
                err = errors.PerformanceManagingErrorCodes.OWNER_MISMATCH
            # Controlla che la performance non sia già stata pubblicata
            elif bool(performance.is_published):
                err = errors.PerformanceManagingErrorCodes.PERFORMANCE_ALREADY_PUBLISHED
            else:
                # Se non c'è nessun form_data salvato (quindi non si sta arrivando da una modifica fallita), prepara i dati dal db per mostrarli nel form
                if form_data is None:
                    data = {
                        "day": performance.day,
                        "time": performance.time_string,
                        "duration": performance.duration,
                        "stage": performance.stage.id,
                        "genre": performance.genre,
                        "description": performance.description,
                        "artist-name": performance.artist.name,
                        "artist-main-picture-id": performance.artist.main_picture.id,
                        "artist-background-picture-id": performance.artist.background_picture.id,
                    }
                else:
                    data = form_data

    else:
        err = errors.PerformanceManagingErrorCodes.MISSING_PERFORMANCE_ID

    if err is not None:
        flash(errors.get_performance_managing_error_message(err), "error")
        return redirect(url_for("manager_page"))
    else:
        return render_template(
            "edit_performance.html",
            data=data,
            days=values.get_all_days(),
            stages=performance_classes.get_all_stages_instances(),
            performance=performance,
            int=int
        )

@app.route("/gestione/es_modifica_performance", methods=["POST"])
@login_required
def do_edit_performance():
    if not current_user.is_organizer:
        return abort(403)

    data = request.form.to_dict()
    err = None  # Inizializza variabile errore
    overlaps = None

    # Ottieni ID performance dall'input nascosto
    if data.get("performance-id", None) is not None:
        try:
            # Controlla validità dato numerico
            performance_id = int(data["performance-id"])
        except ValueError:
            err = errors.PerformanceManagingErrorCodes.INVALID_PERFORMANCE_ID
        else:
            # Carica performance dal database
            performance = performance_classes.get_single_performance_instance(performance_id)

            # Controlla che la performance esista nel database
            if performance is None:
                err = errors.PerformanceManagingErrorCodes.PERFORMANCE_ID_NOT_FOUND
            elif performance.organizer.id != int(current_user.id):
                err = errors.PerformanceManagingErrorCodes.OWNER_MISMATCH
            # Controlla che l'utente sia l'autore della performance
            elif performance.is_published:
                err = errors.PerformanceManagingErrorCodes.PERFORMANCE_ALREADY_PUBLISHED
            else:
                # Imposta stringhe vuote/None se i campi mancano
                day = data.get("day", None)
                time = data.get("time", None)
                duration = data.get("duration", None)
                stage_id = data.get("stage", None)
                genre = data.get("genre", "")
                description = data.get("description", "")
                artist_name = data.get("artist-name", "")
                artist_main_picture_id = data.get("artist-main-picture-id", None)
                artist_background_picture_id = data.get("artist-background-picture-id", None)

                # Controlla se mancano dati
                if None in (day, time, duration, stage_id, artist_background_picture_id, artist_main_picture_id)\
                    or "" in (genre, artist_name, description):
                    err = errors.PerformanceManagingErrorCodes.MISSING_DATA
                else:
                    try:
                        # Controlla se i dati numerici sono validi
                        day = int(day)
                        hour, minute = time.split(":")
                        hour = int(hour)
                        minute = int(minute)
                        duration = int(duration)
                        stage_id = int(stage_id)
                        artist_background_picture_id = int(artist_background_picture_id)
                        artist_main_picture_id = int(artist_main_picture_id)

                        # Ottieni tutti gli ID dei palchi presenti nel database
                        stage_ids = set(stage.id for stage in performance_classes.get_all_stages_instances().values())
                        # Controlla validità dei dati temporali e palco e immagini
                        if day not in values.get_all_days().keys() or not (0 <= hour < 24) \
                                or not (0 <= minute < 60) or stage_id not in stage_ids \
                                or artist_main_picture_id not in set(performance.artist.all_pictures)\
                                or artist_background_picture_id not in set(performance.artist.all_pictures):
                            raise ValueError

                    except (ValueError, IndexError):
                        err = errors.PerformanceManagingErrorCodes.INVALID_DATA

                    else:
                        # Controlla sovrapposizione con performance pubblicate
                        if  overlaps := performance_classes.get_overlapping_performances(
                                stage_id=stage_id,
                                day=values.Days(day),
                                hour=hour,
                                minute=minute,
                                duration=duration,
                                published_only=True,
                                ignore_id=performance_id
                        ):
                            overlaps_text_lines = [f"{p.artist.name} - {values.get_day_name(p.day)} {p.time_string} {p.duration}min" for p in overlaps.values()]
                            err = errors.PerformanceManagingErrorCodes.OVERLAP_WITH_PUBLISHED
                        # Se il nome dell'artista è stato modificato, controlla che non esista già nel database
                        elif (artist_name != performance.artist.name
                              and queries.get_artist_by_name(artist_name)):
                            err = errors.PerformanceManagingErrorCodes.ARTIST_NAME_EXISTS
                        else:
                            queries.update_performance(
                                performance_id=performance_id,
                                stage_id=stage_id,
                                day=day,
                                hour=hour,
                                minute=minute,
                                duration=duration,
                                description=description,
                                genre=genre
                            )
                            queries.update_artist(
                                artist_id=performance.artist.id,
                                name=artist_name,
                                main_picture_id=artist_main_picture_id,
                                background_picture_id=artist_background_picture_id
                            )

    else:
        err = errors.PerformanceManagingErrorCodes.MISSING_PERFORMANCE_ID

    if err is not None:
        flash(f"{errors.get_performance_managing_error_message(err)}"
              f"\n{"\n".join(overlaps_text_lines) if overlaps else ""}", "error")
        # Rimanda al gestore in caso di ID non valido/assente/non esistente/di un altro gestore
        if err in {
            errors.PerformanceManagingErrorCodes.INVALID_PERFORMANCE_ID,
            errors.PerformanceManagingErrorCodes.PERFORMANCE_ID_NOT_FOUND,
            errors.PerformanceManagingErrorCodes.MISSING_PERFORMANCE_ID,
            errors.PerformanceManagingErrorCodes.OWNER_MISMATCH,
            errors.PerformanceManagingErrorCodes.PERFORMANCE_ALREADY_PUBLISHED,
        }:
            return redirect(url_for("manager_page"))
        else:
            # Altrimenti ricarica pagina preservando più dati possibili
            session["edit_performance_form_data"] = data
            return redirect(url_for("edit_performance_page", performance_id=performance_id))
    else:
        flash(success.get_performance_managing_success_message(success.PerformanceManagingSuccess.PERFORMANCE_EDIT_SUCCESS), "success")
        return redirect(url_for("manager_page"))


@app.route("/gestione/modifica_immagini/<int:performance_id>")
@login_required
def edit_pictures_page(performance_id: int):
    if not current_user.is_organizer:
        abort(403)

    err = None  # Inizializza variabile errore

    # Ottieni ID performance
    if performance_id:
        # Controlla validità dato numerico
        try:
            performance_id = int(performance_id)
        except ValueError:
            err = errors.PerformanceManagingErrorCodes.INVALID_PERFORMANCE_ID
        else:
            # Carica performance dal database
            performance = performance_classes.get_single_performance_instance(performance_id)
            # Controlla che la performance esista del database
            if performance is None:
                err = errors.PerformanceManagingErrorCodes.PERFORMANCE_ID_NOT_FOUND
            # Controlla che l'utente sia l'autore della performance
            elif performance.organizer.id != int(current_user.id):
                err = errors.PerformanceManagingErrorCodes.OWNER_MISMATCH
            # Controlla che la performance non sia già stata pubblicata
            elif performance.is_published:
                err = errors.PerformanceManagingErrorCodes.PERFORMANCE_ALREADY_PUBLISHED

    else:
        err = errors.PerformanceManagingErrorCodes.MISSING_PERFORMANCE_ID

    if err is not None:
        flash(errors.get_performance_managing_error_message(err), "error")
        return redirect(url_for("manager_page"))
    else:
        return render_template(
            "edit_pictures.html",
            performance=performance
        )

@app.route("/gestione/es_modifica_immagini", methods=["POST"])
@login_required
def do_edit_pictures():
    if not current_user.is_organizer:
        return abort(403)

    data = request.form.to_dict()
    err = None  # Inizializza variabile errore

    # Ottieni ID performance dall'input nascosto
    if data.get("performance-id") is not None:
        try:
            # Controlla validità dato numerico
            performance_id = int(data["performance-id"])
        except ValueError:
            err = errors.PerformanceManagingErrorCodes.INVALID_PERFORMANCE_ID
        else:
            # Carica performance dal database
            performance = performance_classes.get_single_performance_instance(performance_id)

            # Controlla che la performance esista del database
            if performance is None:
                err = errors.PerformanceManagingErrorCodes.PERFORMANCE_ID_NOT_FOUND
            elif performance.organizer.id != int(current_user.id):
                err = errors.PerformanceManagingErrorCodes.OWNER_MISMATCH
            # Controlla che l'utente sia l'autore della performance
            elif bool(performance.is_published):
                err = errors.PerformanceManagingErrorCodes.PERFORMANCE_ALREADY_PUBLISHED
            else:
                # Ottieni lista di checkbox spuntate
                remove_list = request.form.getlist("remove")
                try:
                    # Inserisci ID da rimuovere in un insieme
                    remove_ids = {int(i) for i in remove_list}

                    # Controlla che gli ID delle immagini siano effettivamente per l'artista in questione
                    # e che non siano incluse l'immagine principale o di sfondo
                    if remove_ids - set(performance.artist.other_pictures):
                        raise ValueError

                except ValueError:
                    err = errors.PerformanceManagingErrorCodes.INVALID_DATA
                else:
                    # Elimina immagini
                    files = queries.delete_pictures(remove_ids)
                    for file in files:
                        os.remove(f"static/uploads/{file["FILENAME"]}")

                    new_pictures = request.files.getlist("new-pictures")
                    last_artist_picture_id = queries.get_last_artist_picture_rowid()

                    # Aggiungi immagini
                    for index, file in enumerate(new_pictures):
                        if file.filename:
                            fname = f"{last_artist_picture_id + index + 1}_{secure_filename(file.filename)}"
                            file.save(f"static/uploads/{fname}")
                            queries.create_picture(fname, performance.artist.id)

    else:
        err = errors.PerformanceManagingErrorCodes.MISSING_PERFORMANCE_ID

    if err is not None:
        flash(errors.get_performance_managing_error_message(err), "error")
        # Rimanda al gestore in caso di ID non valido/assente/non esistente/di un altro gestore
        if err in {
            errors.PerformanceManagingErrorCodes.INVALID_PERFORMANCE_ID,
            errors.PerformanceManagingErrorCodes.PERFORMANCE_ID_NOT_FOUND,
            errors.PerformanceManagingErrorCodes.MISSING_PERFORMANCE_ID,
            errors.PerformanceManagingErrorCodes.OWNER_MISMATCH,
            errors.PerformanceManagingErrorCodes.PERFORMANCE_ALREADY_PUBLISHED,
        }:
            return redirect(url_for("manager_page"))
        else:
            # Altrimenti ricarica pagina
            return redirect(url_for("edit_pictures_page", performance_id=performance_id))
    else:
        flash(success.get_performance_managing_success_message(success.PerformanceManagingSuccess.PICTURE_EDIT_SUCCESS), "success")
        return redirect(url_for("manager_page"))

@app.route("/acquisto_biglietti")
@login_required
def buy_tickets_page():
    if current_user.is_organizer:
        return abort(403)

    day_names = values.get_all_days()
    # Carica proprietà biglietti
    tickets_properties = ticket_properties_class.get_all_tickets_properties_instances()
    if not current_user.ticket:
        # Costruisci dizionario indicante la disponibilità dei vari giorni
        days_availability = {
            d: queries.get_number_of_sold_tickets_for_day(d) < values.MAX_TICKETS_PER_DAY
            for d in day_names.keys()
        }

        # Calcola la disponibilità di giorni consecutivi per ogni giorno
        # Il dizionario è in formato first_day: consecutive_days_available
        # Quindi ad esempio 1: 2 vuol dire che sabato e sabato-domenica è disponibile
        consecutive_days_available = {}
        for i in day_names.keys():
            c = 0
            for j in tuple(day_names.keys())[i:]:
                if days_availability[j]:
                    c += 1
                else:
                    break
            consecutive_days_available[i] = c

        return render_template(
            "buy_tickets.html",
            day_names=day_names,
            consecutive_days_available=consecutive_days_available,
            tickets_properties=tickets_properties,
            max=max,
            list=list,
            len=len
        )
    else:
        return redirect(url_for("profile_page"))

@login_required
@app.route("/acquisto_biglietti/esegui_acquisto", methods=["POST"])
def do_buy_ticket():
    if current_user.is_organizer:
        return abort(403)

    data = request.form.to_dict()
    err = None  # Inizializza variabile errore

    # Ottieni dati dal form
    first_day = data.get("first-day", None)
    duration = data.get("duration", None)
    if None in (first_day, duration):
        err = errors.TicketBuyingErrorCodes.MISSING_DATA
    else:
        try:
            # Controlla validità dei dati numerici
            first_day = int(first_day)
            duration = int(duration)

            # Controlla validità intervallo giorni
            if first_day < 0 or duration < 1 or first_day + duration > len(values.Days):
                raise ValueError
        except ValueError:
            err = errors.TicketBuyingErrorCodes.INVALID_DATA
        else:
            # Controlla che l'utente non abbia già acquistato un biglietto
            if current_user.ticket is not None:
                err = errors.TicketBuyingErrorCodes.ALREADY_BOUGHT
            else:
                # Controlla che i giorni selezionati siano disponibili
                # Carica disponibilità dei singoli giorni
                days_availability = {
                    d: queries.get_number_of_sold_tickets_for_day(d) < values.MAX_TICKETS_PER_DAY
                    for d in values.get_all_days()
                }
                valid = True
                # Itera disponibilità nell'intervallo selezionato e controlla che tutti i giorni siano disponibili
                for i in range(first_day, first_day + duration):
                    if not days_availability[i]:
                        valid = False
                        break
                if not valid:
                    err = errors.TicketBuyingErrorCodes.DAY_UNAVAILABLE
                else:
                    t_id = queries.create_ticket_for_user(current_user.id, first_day, duration)
                    current_user.ticket = user_classes.Ticket(
                        id=t_id,
                        first_day=values.Days(first_day),
                        duration=duration
                    )


    if err is not None:
        flash(errors.get_ticket_buying_error_message(err), "error")

    return redirect(url_for("buy_tickets_page"))

@app.route("/performance/<int:performance_id>")
def performance_page(performance_id: int):
    performance = performance_classes.get_single_performance_instance(performance_id)
    # Non mostrare la performance se non esiste, o se non è pubblicata e l'utente non è l'autore (o l'utente non ha effettuato l'accesso)
    if performance and (performance.is_published or (current_user.is_authenticated and performance.organizer.id == int(current_user.id))):
        return render_template(
            "single_performance.html",
            day_names=values.get_all_days(),
            performance=performance,
            len=len
        )

    return redirect(url_for("site_root_page"))

@login_required
@app.route("/profilo")
def profile_page():
    day_names = values.get_all_days()
    if current_user.is_organizer:
        # Carica statistiche biglietti
        single_tickets_stats = {}
        double_tickets_stats = {}
        totals = {}

        # Carica statistiche per tutti e 3 i giorni
        for d in day_names:
            single_tickets_stats[d] = queries.get_ticket_statistics(d, 1)
            totals[d] = queries.get_number_of_sold_tickets_for_day(d)
        for d in tuple(day_names.keys())[:-1]:
            double_tickets_stats[d] = queries.get_ticket_statistics(d, 2)
        triple_ticket_stats = {0: queries.get_ticket_statistics(0, 3)}

        ticket_stats = {
            1: single_tickets_stats,
            2: double_tickets_stats,
            3: triple_ticket_stats,
        }

        return render_template(
            "profile.html",
            current_user=current_user,
            ticket_stats=ticket_stats,
            totals=totals,
            day_names=day_names,
            MAX_TICKETS_PER_DAY=values.MAX_TICKETS_PER_DAY,
        )

    elif current_user.ticket:
        return render_template(
            "profile.html",
            current_user=current_user,
            ticket=ticket_properties_class.get_ticket_properties_instance(current_user.ticket.duration),
            first_day=current_user.ticket.first_day,
            day_names=values.get_all_days(),
            list=list
        )

    else:
        return render_template(
            "profile.html",
            current_user=current_user,
            list=list
        )

@app.route("/ricerca_performance")
def search_performances_page():
    return render_template("search_performances.html")

@app.route("/performance")
def performances_list_page():
    # Carica performance pubblicate
    performances = performance_classes.get_performance_instances(filter_published_status=True)
    # Costruisci lista generi musicali ordinata
    genres = sorted(set(p.genre for p in performances.values()))
    stages = performance_classes.get_all_stages_instances()
    day_names = values.get_all_days()

    day = request.args.get('day', default=None, type=int)
    stage_id = request.args.get('stage', default=None, type=int)
    genre = request.args.get('genre', default=None, type=str)

    # Annulla filtri con valori non validi
    if day is not None and day not in day_names:
        day = None
    if stage_id is not None and stage_id not in stages:
        stage_id = None
    if genre is not None and genre not in genres:
        genre = None

    # Seleziona solo performance pubblicate e con i filtri richiesti
    performances = performance_classes.get_performance_instances(
        filter_published_status=True,
        day=day,
        stage_id=stage_id,
        genre=genre,
    )

    return render_template(
        "performances_list.html",
        performances=performances,
        day_names=day_names,
        stages=stages,
        genres=genres,
        filtered_day=day,
        filtered_stage=stage_id,
        filtered_genre=genre,
    )
