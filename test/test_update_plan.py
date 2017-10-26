__author__ = "Alexander Elvers <aelvers AT inet.tu-berlin.de>"

import datetime
import pytest

from tutorplanner import update_plan
from tutorplanner.input import tutor, rooms
from tutorplanner.input.data import Data


def create_tutor(first_name, last_name):
    t = tutor.Tutor()
    t.first_name = first_name
    t.last_name = last_name
    return first_name, t


def create_room(room_name):
    return room_name, rooms.Room(room_name)


@pytest.fixture(autouse=True)
def fix(monkeypatch):
    monkeypatch.setattr(Data(), "_tutor_by_name", dict([
        create_tutor("Erika", "Mustermann"),
        create_tutor("Friedhelm", "von Arnim"),
    ]))

    monkeypatch.setattr(Data(), "_room_by_name", dict([
        create_room("MAR 0.001"),
    ]))



def test_search_room():
    assert update_plan.search_room("MAR 0.001").name == "MAR 0.001"
    assert update_plan.search_room("mar 0.001").name == "MAR 0.001"

    with pytest.raises(ValueError) as e:
        update_plan.search_room("MAR 0.002")
    assert e.match(r"room not found: MAR 0.002$")


def test_search_tutor():
    t = update_plan.search_tutor("Mustermann")
    assert (t.last_name, t.first_name) == ("Mustermann", "Erika")

    t = update_plan.search_tutor("mustermann")
    assert (t.last_name, t.first_name) == ("Mustermann", "Erika")

    t = update_plan.search_tutor("mUStERmanN")
    assert (t.last_name, t.first_name) == ("Mustermann", "Erika")

    with pytest.raises(ValueError) as e:
        update_plan.search_tutor("Erika")
    e.match(r"tutor not found: Erika$")


def test_search_date():
    assert update_plan.search_date(10, 19) == datetime.date(2016, 10, 19)
    assert update_plan.search_date(10, 22) is None


def test_parse_date():
    assert update_plan.parse_date("2016-10-17") == datetime.date(2016, 10, 17)
    assert update_plan.parse_date("10-17") == datetime.date(2016, 10, 17)

    with pytest.raises(ValueError) as e:
        update_plan.parse_date("17")
    assert e.match(r"invalid date format")

    with pytest.raises(ValueError) as e:
        update_plan.parse_date("-2016-10-17")
    assert e.match(r"invalid date format")

    with pytest.raises(ValueError) as e:
        update_plan.parse_date("2016-10-22")
    assert e.match(r"date not in settings")

    with pytest.raises(ValueError) as e:
        update_plan.parse_date("10-22")
    assert e.match(r"date not in settings")


def test_parse_task():
    # room required

    t, d, h, r = update_plan.parse_task("Mustermann 2016-10-17 11 MAR_0.001")
    assert (t.last_name, t.first_name) == ("Mustermann", "Erika")
    assert d == datetime.date(2016, 10, 17)
    assert h == 11
    assert r.name == "MAR 0.001"

    t, d, h, r = update_plan.parse_task("von_Arnim 2016-10-17 11 MAR_0.001")
    assert (t.last_name, t.first_name) == ("von Arnim", "Friedhelm")
    assert d == datetime.date(2016, 10, 17)
    assert h == 11
    assert r.name == "MAR 0.001"

    with pytest.raises(ValueError) as e:
        update_plan.parse_task("von Arnim 2016-10-17 11 MAR_0.001")
    assert e.match("expected TUTOR DATE HOUR ROOM")

    with pytest.raises(ValueError) as e:
        update_plan.parse_task("Mustermann 2016-10-17 11 MAR 0.001")
    assert e.match("expected TUTOR DATE HOUR ROOM")

    with pytest.raises(ValueError) as e:
        update_plan.parse_task("Mustermann 2016-10-17 11 MAR_0.001 foo")
    assert e.match("expected TUTOR DATE HOUR ROOM")

    # room not required

    t, d, h, r = update_plan.parse_task("Mustermann 2016-10-17 11 MAR_0.001", room_required=False)
    assert (t.last_name, t.first_name) == ("Mustermann", "Erika")
    assert d == datetime.date(2016, 10, 17)
    assert h == 11
    assert r.name == "MAR 0.001"

    t, d, h, r = update_plan.parse_task("Mustermann 2016-10-17 11", room_required=False)
    assert (t.last_name, t.first_name) == ("Mustermann", "Erika")
    assert d == datetime.date(2016, 10, 17)
    assert h == 11
    assert r is None
