from flask_login import UserMixin
import modules.values

class Ticket:
    _id: int
    _first_day: modules.values.Days
    _duration: int

    @property
    def id(self):
        return self._id

    @property
    def first_day(self):
        return self._first_day

    @property
    def duration(self):
        return self._duration

    def __init__(self, id: int, first_day: modules.values.Days, duration: int):
        self._id = id
        self._first_day = first_day
        self._duration = duration


class User(UserMixin):
    _id: int
    _email: str
    _first_name: str
    _last_name: str
    _is_organizer: bool
    _ticket: Ticket | None

    @property
    def id(self) -> str:
        return str(self._id)

    @property
    def email(self) -> str:
        return self._email

    @property
    def first_name(self) -> str:
        return self._first_name

    @property
    def last_name(self) -> str:
        return self._last_name

    @property
    def is_organizer(self) -> bool:
        return self._is_organizer

    @property
    def ticket(self) -> Ticket | None:
        return self._ticket

    @ticket.setter
    def ticket(self, ticket):
        self._ticket = ticket

    def __init__(
        self,
        id: int,
        email: str,
        first_name: str,
        last_name: str,
        is_organizer: bool,
        ticket: Ticket | None
    ):
        self._id = id
        self._email = email
        self._first_name = first_name
        self._last_name = last_name
        self._is_organizer = is_organizer
        self._ticket = ticket
