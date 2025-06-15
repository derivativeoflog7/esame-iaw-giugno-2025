from enum import IntEnum, auto

class LoginErrorCodes(IntEnum):
    EMPTY_FIELDS = auto()
    USER_NOT_FOUND = auto()
    WRONG_PASSWORD = auto()

__LOGIN_ERROR_MESSAGES = {
    LoginErrorCodes.EMPTY_FIELDS: "Compila tutti i campi",
    LoginErrorCodes.WRONG_PASSWORD: "Password errata",
    LoginErrorCodes.USER_NOT_FOUND: "Utente non trovato",
}

def get_login_error_message(code: LoginErrorCodes):
    return None if code is None else __LOGIN_ERROR_MESSAGES.get(code, f"undefined {code}")

class RegistrationErrorCodes(IntEnum):
    EMPTY_FIELDS = auto()
    EMAIL_EXISTS = auto()
    INVALID_EMAIL = auto()
    INVALID_PASSWORD = auto()
    INVALID_OTP = auto()
    WRONG_OTP = auto()

__REGISTER_ERROR_MESSAGES = {
    RegistrationErrorCodes.EMPTY_FIELDS: "Compila tutti i campi",
    RegistrationErrorCodes.EMAIL_EXISTS: "Email già registrata",
    RegistrationErrorCodes.INVALID_EMAIL: "Email non valida",
    RegistrationErrorCodes.INVALID_PASSWORD: "Password non valida",
    RegistrationErrorCodes.INVALID_OTP: "OTP non valido",
    RegistrationErrorCodes.WRONG_OTP: "OTP errato",
}

def get_registration_error_message(code: RegistrationErrorCodes):
    return None if code is None else __REGISTER_ERROR_MESSAGES.get(code, f"undefined {code}")

class PerformanceManagingErrorCodes(IntEnum):
    PERFORMANCE_ID_NOT_FOUND = auto()
    MISSING_PERFORMANCE_ID = auto()
    PERFORMANCE_ALREADY_PUBLISHED = auto()
    MISSING_DATA = auto()
    INVALID_DATA = auto()
    ARTIST_NAME_EXISTS = auto()
    OVERLAP_WITH_PUBLISHED = auto()
    INVALID_PERFORMANCE_ID = auto()
    OWNER_MISMATCH = auto()

__PERFORMANCE_MANAGING_ERROR_MESSAGES = {
    PerformanceManagingErrorCodes.PERFORMANCE_ID_NOT_FOUND: "Performance non trovata",
    PerformanceManagingErrorCodes.MISSING_PERFORMANCE_ID: "ID non specificato",
    PerformanceManagingErrorCodes.PERFORMANCE_ALREADY_PUBLISHED: "Performance già pubblicata",
    PerformanceManagingErrorCodes.MISSING_DATA: "Dati mancanti",
    PerformanceManagingErrorCodes.INVALID_DATA: "Dati non validi",
    PerformanceManagingErrorCodes.ARTIST_NAME_EXISTS: "Nome artista già esistente",
    PerformanceManagingErrorCodes.OVERLAP_WITH_PUBLISHED: "Sovrapposizione con performance pubblicata/e",
    PerformanceManagingErrorCodes.INVALID_PERFORMANCE_ID: "ID non valido",
    PerformanceManagingErrorCodes.OWNER_MISMATCH: "Non sei l'autore della performance",
}

def get_performance_managing_error_message(code: PerformanceManagingErrorCodes):
    return None if code is None else __PERFORMANCE_MANAGING_ERROR_MESSAGES.get(code, f"undefined {code}")

class TicketBuyingErrorCodes(IntEnum):
    INVALID_DATA = auto()
    DAY_UNAVAILABLE = auto()
    MISSING_DATA = auto()
    ALREADY_BOUGHT = auto()

__TICKET_BUYING_ERROR_MESSAGES = {
    TicketBuyingErrorCodes.INVALID_DATA: "Dati non validi",
    TicketBuyingErrorCodes.DAY_UNAVAILABLE: "Biglietti esauriti per la giornata",
    TicketBuyingErrorCodes.MISSING_DATA: "Dati mancanti",
    TicketBuyingErrorCodes.ALREADY_BOUGHT: "Hai già acquistato un biglietto",
}

def get_ticket_buying_error_message(code: TicketBuyingErrorCodes):
    return None if code is None else __TICKET_BUYING_ERROR_MESSAGES.get(code, f"undefined {code}")