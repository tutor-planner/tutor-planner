__author__ = ("Matthias Rost <mrost AT inet.tu-berlin.de>, "
              "Alexander Elvers <aelvers AT inet.tu-berlin.de>")

__all__ = ["Data"]

from collections import OrderedDict
from typing import Dict, List, Optional

from . import tutor
from . import rooms
from ..util import converter
from ..util.settings import settings


class SingletonMeta(type):
    """
    Singleton meta class

    Saves the instance when class is called.
    """
    def __init__(cls, *args, **kwargs):
        type.__init__(cls, *args, **kwargs)
        cls._instance = None

    def __call__(cls):
        if cls._instance is None:
            cls._instance = type.__call__(cls)
        return cls._instance


class Data(metaclass=SingletonMeta):
    """
    Singleton for keeping all data together.

    Because some data might not yet exist, it is loaded on access.
    """
    _tutor_by_name: Optional[Dict[str, tutor.Tutor]] = None
    _room_by_name: Optional[Dict[str, rooms.Room]] = None
    # first type, then name
    _room_by_type: Optional[Dict[str, Dict[str, rooms.Room]]] = None

    # tutor name -> day index -> hour -> availability value
    _availability: Optional[Dict[str, Dict[int, Dict[int, int]]]] = None
    # day index -> hour -> list of room names
    _bookings_tutorials: Optional[Dict[int, Dict[int, List[str]]]] = None
    # day index -> hour -> list of room names
    _bookings_pools: Optional[Dict[int, Dict[int, List[str]]]] = None
    _rooms_external: Optional[List[str]] = None

    @property
    def tutor_by_name(self) -> Dict[str, tutor.Tutor]:
        """
        tutors hashed by last name
        """
        if self._tutor_by_name is None:
            self._tutor_by_name = OrderedDict(sorted([(t.last_name, t) for t in tutor.load_tutors()],
                                                     key=lambda x: x[0]))
        return self._tutor_by_name

    @property
    def room_by_name(self) -> Dict[str, rooms.Room]:
        """
        room hashed by room name
        """
        if self._room_by_name is None:
            self._room_by_name = {r.name: r for r in rooms.import_rooms_from_csv(settings.paths.bookings())}
        return self._room_by_name

    @property
    def room_by_type(self) -> Dict[str, Dict[str, rooms.Room]]:
        """
        room hashed by room type and then by room name
        """
        if self._room_by_type is None:
            self._room_by_type = {}
            for room in self.room_by_name.values():
                self.room_by_type.setdefault(room.type, {})[room.name] = room
        return self._room_by_type

    @property
    def availability(self) -> Dict[str, Dict[int, Dict[int, int]]]:
        """
        tutor availability
        """
        if self._availability is None:
            self._availability = {}  # tutor, day index, hour
            # TODO: use datetime.date instead of day index
            for t in self.tutor_by_name.values():
                self._availability[t.last_name] = {}
                for day, day_availability in t.availability.items():
                    d = converter.date_to_day_index(day)
                    self._availability[t.last_name][d] = {}
                    for hour, availability in day_availability.items():
                        self._availability[t.last_name][d][hour] = availability if availability is not None else 0
                        # self.availability[t.last_name][d][hour+1] = availability if availability is not None else 0
        return self._availability

    @property
    def bookings_tutorials(self) -> Dict[int, Dict[int, List[str]]]:
        """
        bookings of tutorial rooms
        """
        if self._bookings_tutorials is None:
            self._bookings_tutorials = {}
            for day in settings.days():
                day_index = converter.date_to_day_index(day)
                self._bookings_tutorials[day_index] = {}
                for time in settings.times():
                    self._bookings_tutorials[day_index][time] = []
                for room in self.room_by_type["tutorial"].values():
                    times = room.get_booked_times(day)
                    for time in times:
                        self._bookings_tutorials.setdefault(day_index, {}).setdefault(time, []).append(room.name)
            self._bookings_tutorials = converter.to_single_hour_precision(self._bookings_tutorials)
        return self._bookings_tutorials

    @property
    def bookings_pools(self) -> Dict[int, Dict[int, List[str]]]:
        """
        bookings of exercise pools
        """
        if self._bookings_pools is None:
            self._bookings_pools = {}
            for day in settings.days():
                day_index = converter.date_to_day_index(day)
                self._bookings_pools[day_index] = {}
                for time in settings.times():
                    self._bookings_pools[day_index][time] = []
                for room in self.room_by_name.values():
                    if room.type.startswith("exercise"):
                        times = room.get_booked_times(day)
                        for time in times:
                            self._bookings_pools.setdefault(day_index, {}).setdefault(time, []).append(room.name)
            self._bookings_pools = converter.to_single_hour_precision(self._bookings_pools)
        return self._bookings_pools

    @property
    def rooms_external(self) -> List[str]:
        """
        list of room names
        """
        if self._rooms_external is None:
            self._rooms_external = []  # this is static
        return self._rooms_external

    def get_number_of_tutorial_rooms(self, day: int, hour: int) -> int:
        """
        Get the number of tutorial rooms at the time slot.
        """
        if day not in self.bookings_tutorials or hour not in self.bookings_tutorials[day]:
            return 0
        return len(self.bookings_tutorials[day][hour])

    def get_exercise_rooms(self) -> List[str]:
        """
        Get a list of public pool rooms that are shown to the students.
        """
        return list(self.room_by_type["exercise"].keys()) + list(self.room_by_type.get("exerciseMAR", {}).keys())
