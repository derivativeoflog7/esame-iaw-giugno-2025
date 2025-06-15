from enum import IntEnum, auto

class RegistrationSuccess(IntEnum):
    SUCCESS = auto()

__REGISTRATION_SUCCESS_MESSAGES = {
    RegistrationSuccess.SUCCESS: "Registrazione completata",
}

def get_registration_success_message(code: RegistrationSuccess):
    return None if code is None else __REGISTRATION_SUCCESS_MESSAGES.get(code, f"undefined {code}")

class PerformanceManagingSuccess(IntEnum):
    ADD_SUCCESS = auto()
    PERFORMANCE_EDIT_SUCCESS = auto()
    PICTURE_EDIT_SUCCESS = auto()
    DELETE_SUCCESS = auto()
    PUBLISH_SUCCESS = auto()

__PERFORMANCE_MANAGING_SUCCESS = {
    PerformanceManagingSuccess.ADD_SUCCESS: "Performance aggiunta",
    PerformanceManagingSuccess.PERFORMANCE_EDIT_SUCCESS: "Performance modificata",
    PerformanceManagingSuccess.PICTURE_EDIT_SUCCESS: "Immagini modificate",
    PerformanceManagingSuccess.DELETE_SUCCESS: "Performance eliminata",
    PerformanceManagingSuccess.PUBLISH_SUCCESS: "Performance pubblicata",
}

def get_performance_managing_success_message(code: PerformanceManagingSuccess):
    return None if code is None else __PERFORMANCE_MANAGING_SUCCESS.get(code, f"undefined {code}")