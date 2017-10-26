__author__ = "Alexander Elvers <aelvers AT inet.tu-berlin.de>"

import datetime
import pytest
from tutorplanner.util import settings


@pytest.fixture(autouse=True)
def fix_settings(monkeypatch):
    monkeypatch.setattr(settings.settings, "_data", {
        "days": [
            datetime.date(2016, 10, 17),
            datetime.date(2016, 10, 18),
            datetime.date(2016, 10, 19),
            datetime.date(2016, 10, 20),
            datetime.date(2016, 10, 21),
            datetime.date(2016, 10, 24),
            datetime.date(2016, 10, 25),
            datetime.date(2016, 10, 26),
            datetime.date(2016, 10, 27),
            datetime.date(2016, 10, 28),
        ],
        "times": [10, 12, 14, 16],
        "forbidden_timeslots": {
            datetime.date(2016, 10, 17): [10, 12, 14, 16],
            datetime.date(2016, 10, 18): [12],
            datetime.date(2016, 10, 19): [14],
            datetime.date(2016, 10, 20): [16],
            datetime.date(2016, 10, 21): [14],
            datetime.date(2016, 10, 24): [16],
            datetime.date(2016, 10, 25): [12],
            datetime.date(2016, 10, 26): [14],
            datetime.date(2016, 10, 27): [16],
            datetime.date(2016, 10, 28): [14],
        },
    })
