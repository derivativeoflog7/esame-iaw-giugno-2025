import modules

class TicketProperties:
    _duration: int
    _name: str
    _price_cents: int
    _css_class: str
    _single_ticket_base_price_cents: int

    @property
    def duration(self) -> int:
        return self._duration

    @property
    def name(self) -> str:
        return self._name

    @property
    def css_class(self) -> str:
        return self._css_class

    def __price_string_gen(self, price: int) -> str:
        price = str(price)
        return f"€{price[:-2]},{price[-2:]}"

    @property
    def base_price_string(self) -> str:
        return self.__price_string_gen(self._single_ticket_base_price_cents * self._duration)

    @property
    def price_string(self) -> str:
        return self.__price_string_gen(self._price_cents)

    def __init__(self, duration: int, name: str, price_cents: int, css_class: str, single_ticket_base_price_cents: int) -> None:
        self._duration = duration
        self._name = name
        self._price_cents = price_cents
        self._css_class = css_class
        self._single_ticket_base_price_cents = single_ticket_base_price_cents

def get_all_tickets_properties_instances() -> dict[int: TicketProperties]:
    sel = modules.queries.get_all_tickets_properties()
    return {
        row["duration"]: TicketProperties(
            duration=row["duration"],
            price_cents=row["price_cents"],
            name=row["name"],
            css_class=row["css_class"],
            single_ticket_base_price_cents=sel[0]["price_cents"]
        )
        for row in sel
    }

def get_ticket_properties_instance(duration: int) -> TicketProperties:
    sel = modules.queries.get_ticket_properties(duration)
    return TicketProperties(
        duration=sel["duration"],
        name=sel["name"],
        price_cents=sel["price_cents"],
        css_class=sel["css_class"],
        single_ticket_base_price_cents=sel["price_cents"]
    )
