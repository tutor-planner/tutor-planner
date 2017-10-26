__author__ = "Alexander Elvers <aelvers AT inet.tu-berlin.de>"

import datetime

import pytest

from tutorplanner.input import plan, tutor, rooms
from tutorplanner.util import converter
from tutorplanner.util.settings import TUTORIUM, UEBUNG_TEL, UEBUNG_MAR, KONTROLLE

# TODO: set settings in fixture: dates, times


def create_tutor(first_name, last_name, availability):
    t = tutor.Tutor()
    t.first_name = first_name
    t.last_name = last_name
    t.availability = availability
    return t


@pytest.fixture
def tutor_list(monkeypatch):
    ts = [
        create_tutor("A", "A", {
            datetime.date(2016, 10, 18): {10: 3, 12: None, 14: 0, 16: 2},
            datetime.date(2016, 10, 19): {10: 0, 12: 2, 14: None, 16: 2},
        }),
        create_tutor("B", "B", {
            datetime.date(2016, 10, 18): {10: 2, 12: None, 14: 1, 16: 0},
            datetime.date(2016, 10, 19): {10: 1, 12: 2, 14: None, 16: 3},
        }),
        create_tutor("C", "C", {
            datetime.date(2016, 10, 18): {10: 1, 12: None, 14: 1, 16: 2},
            datetime.date(2016, 10, 19): {10: 3, 12: 2, 14: None, 16: 0},
        }),
    ]
    monkeypatch.setattr(tutor, "load_tutors", lambda: ts)
    return ts


def create_room(name, room_type, booked):
    r = rooms.Room(name)
    r.type = room_type
    r.booked = booked
    return r


@pytest.fixture
def room_list(monkeypatch):
    rs = [
        create_room("MAR 0.001", "tutorial", {
            datetime.date(2016, 10, 18): {10, 12, 14, 16},
            datetime.date(2016, 10, 19): {10, 12, 16},
        }),
        create_room("MAR 0.003", "tutorial", {
            datetime.date(2016, 10, 18): {14, 16},
            datetime.date(2016, 10, 19): {10, 12},
        }),
        create_room("MAR 0.011", "tutorial", {
            datetime.date(2016, 10, 18): {12, 14},
            datetime.date(2016, 10, 19): {10, 12},
        }),
        create_room("TEL 106li", "exercise", {
            datetime.date(2016, 10, 18): {10, 12, 14, 16},
            datetime.date(2016, 10, 19): {10, 12, 14},
        }),
        create_room("TEL 106re", "exercise", {
            datetime.date(2016, 10, 18): {12, 14, 16},
            datetime.date(2016, 10, 19): {10, 12, 14, 16},
        }),
    ]
    monkeypatch.setattr(rooms, "import_rooms_from_csv", lambda *a: rs)
    return rs


def create_empty_plan(tutor_list):
    # TODO: use settings for days and times
    return {
        t.last_name: {
            UEBUNG_MAR: {day: {hour: "" for hour in range(10, 18)} for day in range(1, 11)},
            UEBUNG_TEL: {day: {hour: "" for hour in range(10, 18)} for day in range(1, 11)},
            TUTORIUM: {day: {hour: "" for hour in range(10, 18)} for day in range(1, 11)},
            KONTROLLE: {day: {hour: "" for hour in range(10, 18)} for day in range(1, 11)},
        } for t in tutor_list
    }


class TestPersonalPlan:
    def test_add_task__simple_case(self, tutor_list, room_list):
        p = plan.PersonalPlan()
        assert p.plan_by_tutor == {}
        assert p.plan_by_room == {}

        t0, t1, t2 = tutor_list
        r0, r1, r2, r3, r4 = room_list
        d0, d1 = datetime.date(2016, 10, 18), datetime.date(2016, 10, 19)

        # simple tests

        p.add_task(t0, d0, 10, r0)

        assert p.plan_by_tutor == {t0: {d0: {10: r0}}}
        assert p.plan_by_room == {r0: {d0: {10: {t0}}}}

        p.add_task(t0, d0, 16, r4)
        p.add_task(t0, d0, 17, r3)
        p.add_task(t0, d1, 12, r2)

        p.add_task(t1, d0, 14, r1)
        p.add_task(t1, d1, 16, r0)

        assert p.plan_by_tutor == {
            t0: {d0: {10: r0, 16: r4, 17: r3}, d1: {12: r2}},
            t1: {d0: {14: r1}, d1: {16: r0}},
        }
        assert p.plan_by_room == {
            r0: {d0: {10: {t0}}, d1: {16: {t1}}},
            r1: {d0: {14: {t1}}},
            r2: {d1: {12: {t0}}},
            r3: {d0: {17: {t0}}},
            r4: {d0: {16: {t0}}},
        }

    def test_add_task__double_tutor(self, tutor_list, room_list):
        p = plan.PersonalPlan()
        assert p.plan_by_tutor == {}
        assert p.plan_by_room == {}

        r0, r1, r2, r3, r4 = room_list
        d0, d1 = datetime.date(2016, 10, 18), datetime.date(2016, 10, 19)
        t0, t1, t2 = tutor_list

        # multiple tutors in exercise room

        p.add_task(t0, d0, 10, r3)
        p.add_task(t1, d0, 10, r3)
        p.add_task(t2, d0, 10, r3)

        assert p.plan_by_tutor == {
            t0: {d0: {10: r3}},
            t1: {d0: {10: r3}},
            t2: {d0: {10: r3}},
        }
        assert p.plan_by_room == {
            r3: {d0: {10: {t0, t1, t2}}},
        }

        # multiple tutors in tutorial room

        p.add_task(t0, d1, 12, r0)
        with pytest.raises(ValueError) as e:
            p.add_task(t1, d1, 12, r0)
        e.match(r"^MAR 0.001 has already a task at 2016-10-19 12$")

    def test_add_task__tutor_unavailable(self, tutor_list, room_list):
        p = plan.PersonalPlan()
        assert p.plan_by_tutor == {}
        assert p.plan_by_room == {}

        r0, r1, r2, r3, r4 = room_list
        d0, d1 = datetime.date(2016, 10, 18), datetime.date(2016, 10, 19)
        t0, t1, t2 = tutor_list

        # tutor has already a task

        p.add_task(t0, d0, 10, r0)
        p.add_task(t0, d0, 11, r0)

        with pytest.raises(ValueError) as e:
            p.add_task(t0, d0, 10, r1)
        e.match(r"^A A has already a task at 2016-10-18 10$")

        with pytest.raises(ValueError) as e:
            p.add_task(t0, d0, 11, r1)
        e.match(r"^A A has already a task at 2016-10-18 11$")

        # tutor unavailable

        with pytest.raises(ValueError) as e:
            p.add_task(t0, d0, 14, r1)
        e.match(r"^A A is unavailable at 2016-10-18 14$")

        with pytest.raises(ValueError) as e:
            p.add_task(t0, d0, 15, r1)
        e.match(r"^A A is unavailable at 2016-10-18 15$")

    def test_add_task__room_not_booked(self, tutor_list, room_list):
        p = plan.PersonalPlan()
        assert p.plan_by_tutor == {}
        assert p.plan_by_room == {}

        r0, r1, r2, r3, r4 = room_list
        d0, d1 = datetime.date(2016, 10, 18), datetime.date(2016, 10, 19)
        t0, t1, t2 = tutor_list

        # room not booked

        with pytest.raises(ValueError) as e:
            p.add_task(t0, d0, 10, r1)
        e.match(r"^MAR 0.003 is not booked at 2016-10-18 10$")

        with pytest.raises(ValueError) as e:
            p.add_task(t0, d0, 11, r1)
        e.match(r"^MAR 0.003 is not booked at 2016-10-18 11$")

    def test_remove_task(self, tutor_list, room_list):
        p = plan.PersonalPlan()

        r0, r1, r2, r3, r4 = room_list
        d0, d1 = datetime.date(2016, 10, 18), datetime.date(2016, 10, 19)
        t0, t1, t2 = tutor_list

        p.plan_by_tutor = {
            t0: {d0: {10: r3, 16: r4, 17: r3}},
            t1: {d0: {10: r3}},
            t2: {d0: {10: r3}},
        }
        p.plan_by_room = {
            r3: {d0: {10: {t0, t1, t2}, 17: {t0}}},
            r4: {d0: {16: {t0}}},
        }

        # simple remove

        p.remove_task(t0, d0, 10, r3)

        assert p.plan_by_tutor == {
            t0: {d0: {16: r4, 17: r3}},
            t1: {d0: {10: r3}},
            t2: {d0: {10: r3}},
        }
        assert p.plan_by_room == {
            r3: {d0: {10: {t1, t2}, 17: {t0}}},
            r4: {d0: {16: {t0}}},
        }

        p.remove_task(t1, d0, 10)

        assert p.plan_by_tutor == {
            t0: {d0: {16: r4, 17: r3}},
            t1: {d0: {}},  # remove does not delete dates
            t2: {d0: {10: r3}},
        }
        assert p.plan_by_room == {
            r3: {d0: {10: {t2}, 17: {t0}}},
            r4: {d0: {16: {t0}}},
        }

        p.remove_task(t0, d0, 17)

        assert p.plan_by_tutor == {
            t0: {d0: {16: r4}},
            t1: {d0: {}},
            t2: {d0: {10: r3}},
        }
        assert p.plan_by_room == {
            r3: {d0: {10: {t2}, 17: set()}},  # remove does not delete times in plan by room
            r4: {d0: {16: {t0}}},
        }

        # double remove

        with pytest.raises(ValueError) as e:
            p.remove_task(t0, d0, 17)
        e.match("^A A has no task at 2016-10-18 17$")

        # wrong room

        with pytest.raises(ValueError) as e:
            p.remove_task(t0, d0, 16, r1)
        e.match("^task of A A at 2016-10-18 16 is not in MAR 0.003$")

    def test_get_personal_plan__empty(self, tutor_list, room_list):
        p = plan.PersonalPlan()

        assert p.get_personal_plan() == create_empty_plan(tutor_list)

    def test_personal_plan(self, tutor_list, room_list):
        # test get_personal_plan
        p = plan.PersonalPlan()

        r0, r1, r2, r3, r4 = room_list
        d0, d1 = datetime.date(2016, 10, 18), datetime.date(2016, 10, 19)
        t0, t1, t2 = tutor_list

        tasks = [
            (t0, d0, 10, r3),
            (t0, d0, 16, r4),
            (t0, d0, 17, r3),
            (t1, d0, 10, r3),
            (t2, d0, 10, r3),
        ]

        p_out = create_empty_plan(tutor_list)

        for task in tasks:
            p.add_task(*task)
            p_out[task[0].last_name][plan.type_map[task[3].type]][converter.date_to_day_index(task[1])][task[2]] = task[3].name

        assert p.get_personal_plan() == p_out

        # test create_from_personal_plan
        p2 = plan.PersonalPlan.create_from_personal_plan(p.get_personal_plan())
        assert p.plan_by_tutor == p2.plan_by_tutor
        assert p.plan_by_room == p2.plan_by_room
