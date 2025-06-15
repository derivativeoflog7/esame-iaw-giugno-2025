from enum import IntEnum

class Days(IntEnum):
    FRIDAY = 0
    SATURDAY = 1
    SUNDAY = 2

__DayNames = {
    Days.FRIDAY: "Venerdì",
    Days.SATURDAY: "Sabato",
    Days.SUNDAY: "Domenica"
}

def get_day_name(day: Days) -> str:
    return __DayNames.get(day, None)

def get_all_days() -> dict[Days, str]:
    return __DayNames

MAX_TICKETS_PER_DAY = 200
FILES_RELOAD_WARNING = "Attenzione: è necessario riselezionare i file"
OTP_KEY = "SULFOXIDEOTP"