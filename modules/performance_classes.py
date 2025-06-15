import sqlite3

import modules

class ArtistPicture:
    _id: int
    _filename: str

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def id(self) -> int:
        return self._id

    def __init__(self, id, filename):
        self._id = id
        self._filename = filename

class Artist:
    _id: int
    _name: str
    _main_picture: ArtistPicture
    _background_picture: ArtistPicture
    _other_pictures: dict[int: ArtistPicture]

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def main_picture(self) -> ArtistPicture:
        return self._main_picture

    @property
    def background_picture(self) -> ArtistPicture:
        return self._background_picture

    @property
    def other_pictures(self) -> dict[int, ArtistPicture]:
        return self._other_pictures

    @property
    def all_pictures(self) -> dict[int, ArtistPicture]:
        # Unione di dizionari
        return ({self._main_picture.id: self._main_picture} |
                {self._background_picture.id: self._background_picture} |
                self._other_pictures)

    @property
    def pictures_count(self) -> int:
        return len(self.all_pictures)

    def __init__(
            self,
            id: int,
            name: str,
            main_picture: ArtistPicture,
            background_picture: ArtistPicture,
            other_pictures: dict[int: ArtistPicture],
    ):
        self._id = id
        self._name = name
        self._main_picture = main_picture
        self._background_picture = background_picture
        self._other_pictures = other_pictures


class Stage:
    _id: int
    _name: str

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def __init__(self, id, name):
        self._id = id
        self._name = name

class Organizer:
    _id: int
    _first_name: str
    _last_name: str

    @property
    def id(self) -> int:
        return self._id

    @property
    def first_name(self) -> str:
        return self._first_name

    @property
    def last_name(self) -> str:
        return self._last_name

    def __init__(
            self,
            id,
            first_name,
            last_name
    ):
        self._id = id
        self._first_name = first_name
        self._last_name = last_name

class Performance:
    _id: int
    _artist: Artist
    _stage: Stage
    _organizer: Organizer
    _description: str
    _day: modules.values.Days
    _hour: int
    _minute: int
    _duration: int
    _genre: str
    _overlaps: dict[int: 'Performance'] | None
    _is_published: bool

    @property
    def id(self) -> int:
        return self._id

    @property
    def artist(self) -> Artist:
        return self._artist

    @property
    def organizer(self) -> Organizer:
        return self._organizer

    @property
    def description(self) -> str:
        return self._description

    @property
    def day(self) -> modules.values.Days:
        return self._day

    @property
    def hour(self) -> int:
        return self._hour

    @property
    def minute(self) -> int:
        return self._minute

    @property
    def duration(self) -> int:
        return self._duration

    @property
    def stage(self) -> Stage:
        return self._stage

    @property
    def genre(self) -> str:
        return self._genre

    @property
    def overlaps(self) -> list[int: 'Performance'] | None:
        return self._overlaps

    @property
    def is_published(self) -> bool:
        return self._is_published

    @property
    def is_overlapping(self):
        return None if self._overlaps is None else bool(self._overlaps)

    @property
    def time_string(self) -> str:
        return f"{self._hour:02d}:{self._minute:02d}"

    def __init__(
            self,
            id: int,
            artist: Artist,
            stage: Stage,
            organizer: Organizer,
            description: str,
            day: modules.values.Days,
            hour: int,
            minute: int,
            duration: int,
            genre: str,
            is_published: bool,
            overlaps: dict[int: 'Performance'] | None
    ):
        self._id = id
        self._artist = artist
        self._stage = stage
        self._organizer = organizer
        self._description = description
        self._day = day
        self._hour = hour
        self._minute = minute
        self._duration = duration
        self._genre = genre
        self._is_published = is_published
        self._overlaps = overlaps

def __internal_performance_instance_from_selections(performance_selection: sqlite3.Row, pictures_selection: list[sqlite3.Row], overlaps: dict[int: Performance] | None) -> Performance:
    # Dividi immagini
    main_picture = None
    background_picture = None
    other_pictures = {}
    for pic_row in pictures_selection:
        if pic_row["is_main_picture"]:
            main_picture = ArtistPicture(id=pic_row["ID"], filename=pic_row["FILENAME"])
        if pic_row["is_background_picture"]:
            background_picture = ArtistPicture(id=pic_row["ID"], filename=pic_row["FILENAME"])
        if pic_row["is_other_picture"]:
            other_pictures[pic_row["ID"]] = ArtistPicture(id=pic_row["ID"], filename=pic_row["FILENAME"])

    assert None not in (main_picture, background_picture)

    # Costruisci e restituisci classi
    return Performance(
        id=performance_selection["ID"],
        description=performance_selection["description"],
        day=performance_selection["day"],
        hour=performance_selection["hour"],
        minute=performance_selection["minute"],
        duration=performance_selection["duration"],
        genre=performance_selection["genre"],
        is_published=performance_selection["is_published"],
        overlaps=overlaps,
        artist=Artist(
            id=performance_selection["artist_id"],
            name=performance_selection["artist_name"],
            main_picture=main_picture,
            background_picture=background_picture,
            other_pictures=other_pictures,
        ),
        stage=Stage(
            id=performance_selection["stage_id"],
            name=performance_selection["stage_name"]
        ),
        organizer=Organizer(
            id=performance_selection["organizer_ID"],
            first_name=performance_selection["organizer_first_name"],
            last_name=performance_selection["organizer_last_name"]
        )
    )


def get_overlapping_performances(
        stage_id: int,
        day: modules.values.Days,
        hour: int,
        minute: int,
        duration: int,
        published_only: bool,
        ignore_id: int | None,
):
    ret = {}

    overlaps_sel = modules.queries.get_overlapping_performances(
        stage_id=stage_id,
        day=day,
        hour=hour,
        minute=minute,
        duration=duration,
        published_only=published_only,
        ignore_id=ignore_id
    )
    # Istanzia performance sovrapposte
    for ov_row in overlaps_sel:
        pictures_sel = modules.queries.get_artist_pictures(ov_row["artist_ID"])
        ret[ov_row["performance_ID"]] = __internal_performance_instance_from_selections(
            performance_selection=ov_row,
            pictures_selection=pictures_sel,
            overlaps=None
        )

    return ret

def __internal_get_performance_instances(
        find_overlaps: bool = False,
        exclude_user_id: int | None = None,
        filter_user_id: int | None = None,
        filter_published_status: bool | None = None,
        performance_id: int | None = None,
        stage_id: int | None = None,
        day: modules.values.Days | None = None,
        genre: str | None = None
):
    ret: dict[int, Performance] = {}
    # Carica performance dal database
    performance_sel = modules.queries.get_performances(
        exclude_user_id=exclude_user_id,
        filter_user_id=filter_user_id,
        filter_published_status=filter_published_status,
        performance_id=performance_id,
        stage_id=stage_id,
        day=day,
        genre=genre,
    )
    for perf_row in performance_sel:
        # Trova sovrapposizioni se richiesto
        overlaps = get_overlapping_performances(
            stage_id=perf_row["stage_ID"],
            day=perf_row["day"],
            hour=perf_row["hour"],
            minute=perf_row["minute"],
            duration=perf_row["duration"],
            published_only=True,
            ignore_id=perf_row["performance_ID"]
        ) if find_overlaps else None

        # Costruisci dizionario
        pictures_sel = modules.queries.get_artist_pictures(perf_row["artist_ID"])
        ret[perf_row["ID"]] = __internal_performance_instance_from_selections(
            performance_selection=perf_row,
            pictures_selection=pictures_sel,
            overlaps=overlaps
        )

    # Restituisci dizionario
    return ret

def get_performance_instances(
        exclude_user_id: int | None = None,
        filter_user_id: int | None = None,
        filter_published_status: bool | None = None,
        stage_id: int | None = None,
        day: modules.values.Days | None = None,
        genre: str | None = None
) -> dict[int: Performance]:
    return __internal_get_performance_instances(
        find_overlaps=False,
        exclude_user_id=exclude_user_id,
        filter_user_id=filter_user_id,
        filter_published_status=filter_published_status,
        stage_id=stage_id,
        day=day,
        genre=genre,
    )

def get_performance_instances_with_overlaps(
        exclude_user_id: int | None = None,
        filter_user_id: int | None = None,
        filter_published_status: bool | None = None,
        stage_id: int | None = None,
        day: modules.values.Days | None = None,
        genre: str | None = None
) -> dict[int: Performance]:
    return __internal_get_performance_instances(
        find_overlaps=True,
        exclude_user_id=exclude_user_id,
        filter_user_id=filter_user_id,
        filter_published_status=filter_published_status,
        stage_id=stage_id,
        day=day,
        genre=genre,
    )

def get_single_performance_instance(performance_id, find_overlaps: bool = False) -> Performance:
    perf = __internal_get_performance_instances(
        performance_id=performance_id,
        find_overlaps=find_overlaps
    )
    return perf[performance_id] if perf else None

def get_all_stages_instances() -> dict[int: Stage]:
    stages_sel = modules.queries.get_all_stages()
    return {
        stage_row["ID"]: Stage(id=stage_row["ID"], name=stage_row["name"])
        for stage_row in stages_sel
    }
