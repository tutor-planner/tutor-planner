__author__ = "Alexander Elvers <aelvers AT inet.tu-berlin.de>"

import datetime
import copy

from tutorplanner.input import rooms


class TestRoom:
    def test_init(self):
        room = rooms.Room("MAR 0.003")
        assert room.name == "MAR 0.003"
        assert room.booked == {}
        assert str(room) == "MAR 0.003"
        assert repr(room) == "Room(MAR 0.003)"

    def test_book(self):
        room = rooms.Room("MAR 0.003")
        assert room.booked == {}
        room.book(datetime.date(2016, 10, 21), 12)
        room.book(datetime.date(2016, 10, 21), 14)
        room.book(datetime.date(2016, 10, 25), 10)
        assert room.booked == {
            datetime.date(2016, 10, 21): {12, 14},
            datetime.date(2016, 10, 25): {10},
        }

    def test_is_booked(self):
        room = rooms.Room("MAR 0.003")
        room.book(datetime.date(2016, 10, 21), 12)
        room.book(datetime.date(2016, 10, 21), 14)
        room.book(datetime.date(2016, 10, 25), 10)
        # is booked
        assert room.is_booked(datetime.date(2016, 10, 21), 12)
        assert room.is_booked(datetime.date(2016, 10, 21), 14)
        assert room.is_booked(datetime.date(2016, 10, 25), 10)
        # is not booked
        assert not room.is_booked(datetime.date(2016, 10, 21), 10)
        assert not room.is_booked(datetime.date(2016, 10, 21), 16)
        assert not room.is_booked(datetime.date(2016, 10, 20), 12)

    def test_get_booked_times(self):
        room = rooms.Room("MAR 0.003")
        room.book(datetime.date(2016, 10, 21), 12)
        room.book(datetime.date(2016, 10, 21), 14)
        room.book(datetime.date(2016, 10, 25), 10)
        # days booked
        assert list(room.get_booked_times(datetime.date(2016, 10, 21))) == [12, 14]
        assert list(room.get_booked_times(datetime.date(2016, 10, 25))) == [10]
        # days not booked
        assert list(room.get_booked_times(datetime.date(2016, 10, 20))) == []
        assert list(room.get_booked_times(datetime.date(2016, 10, 26))) == []


rooms_for_export = [
    rooms.Room("FH 301"),
    rooms.Room("FH 313"),
    rooms.Room("MAR 0.001"),
    rooms.Room("MAR 0.002"),
]
rooms_for_export[0].booked = {
    datetime.date(2016, 10, 18): {14, 16},
    datetime.date(2016, 10, 19): {16},
    datetime.date(2016, 10, 25): {14},
}
rooms_for_export[1].booked = {
    datetime.date(2016, 10, 18): {14, 16},
    datetime.date(2016, 10, 19): {16},
}
rooms_for_export[2].booked = {
    datetime.date(2016, 10, 18): {14},
    datetime.date(2016, 10, 19): {12, 14},
}
rooms_for_export[3].booked = {
    datetime.date(2016, 10, 18): {14, 16},
    datetime.date(2016, 10, 19): {12, 14, 16},
    datetime.date(2016, 10, 25): {12, 14},
}
rooms_for_export_csv = """
2016-10-18\tFH 301\tFH 313\tMAR 0.001\tMAR 0.002
14\tx\tx\tx\tx
16\tx\tx\t\tx

2016-10-19\tFH 301\tFH 313\tMAR 0.001\tMAR 0.002
12\t\t\tx\tx
14\t\t\tx\tx
16\tx\tx\t\tx

2016-10-25\tFH 301\tMAR 0.002
12\t\tx
14\tx\tx
""".strip("\n")


def test_import_rooms_from_csv(tmpdir):
    directory = tmpdir.mkdir("data")

    # exactly as specified
    file1 = directory.join("rooms.csv")
    file1.write(rooms_for_export_csv)

    # as exported by LibreOffice
    file2 = directory.join("rooms2.csv")
    max_tabs = 0
    for line in rooms_for_export_csv.split("\n"):
        max_tabs = max(max_tabs, line.count("\t"))
    for line in rooms_for_export_csv.split("\n"):
        file2.write(line + "\t" * (max_tabs - line.count("\t")) + "\n", "a")

    for file in [file1, file2]:
        rs = rooms.import_rooms_from_csv(str(file))
        rs.sort(key=lambda x: x.name)
        assert rs[0].name == rooms_for_export[0].name
        assert rs[1].name == rooms_for_export[1].name
        assert rs[2].name == rooms_for_export[2].name
        assert rs[3].name == rooms_for_export[3].name
        assert rs[0].booked == rooms_for_export[0].booked
        assert rs[1].booked == rooms_for_export[1].booked
        assert rs[2].booked == rooms_for_export[2].booked
        assert rs[3].booked == rooms_for_export[3].booked

    # import with existing rooms
    r1 = rooms.Room("MAR 0.001")
    r1.book(datetime.date(2016, 10, 19), 16)
    r1_booked = copy.deepcopy(rooms_for_export[2].booked)
    r1_booked[datetime.date(2016, 10, 19)] |= {16}
    for file in [file1, file2]:
        rs = rooms.import_rooms_from_csv(str(file), initial_rooms=[r1])
        rs.sort(key=lambda x: x.name)
        assert rs[0].name == rooms_for_export[0].name
        assert rs[1].name == rooms_for_export[1].name
        assert rs[2].name == rooms_for_export[2].name
        assert rs[3].name == rooms_for_export[3].name
        assert rs[0].booked == rooms_for_export[0].booked
        assert rs[1].booked == rooms_for_export[1].booked
        assert rs[2].booked == r1_booked
        assert rs[3].booked == rooms_for_export[3].booked

    # with 0 instead of empty cell
    file3 = directory.join("rooms3.csv")
    file3.write("\n".join([
        "2016-10-18\tFH 301\tFH 313",
        "14\t0\t1",
        "16\t1\t0",
    ]))
    rs = rooms.import_rooms_from_csv(str(file3))
    assert {r.name: r.booked for r in rs} == {
        "FH 301": {datetime.date(2016, 10, 18): {16}},
        "FH 313": {datetime.date(2016, 10, 18): {14}},
    }

    # with missing rooms in between
    file4 = directory.join("rooms3.csv")
    file4.write("\n".join([
        "2016-10-18\tFH 301\t\tFH 313",
        "14\t\t\tx",
        "16\tx\t\t",
    ]))
    rs = rooms.import_rooms_from_csv(str(file4))
    assert {r.name: r.booked for r in rs} == {
        "FH 301": {datetime.date(2016, 10, 18): {16}},
        "FH 313": {datetime.date(2016, 10, 18): {14}},
    }


def test_export_rooms_to_csv(tmpdir):
    directory = tmpdir.mkdir("data")
    file = directory.join("rooms.csv")
    rooms.export_rooms_to_csv(str(file), rooms_for_export)
    assert file.read().replace("\r", "").rstrip("\n") == rooms_for_export_csv


def test_get_export_day_data():
    lines = rooms.get_export_day_data(datetime.date(2016, 10, 18), rooms_for_export)
    assert "\n".join(["\t".join(map(str, line)) for line in lines]) == rooms_for_export_csv.split("\n\n")[0]

    lines = rooms.get_export_day_data(datetime.date(2016, 10, 19), rooms_for_export)
    assert "\n".join(["\t".join(map(str, line)) for line in lines]) == rooms_for_export_csv.split("\n\n")[1]

    lines = rooms.get_export_day_data(datetime.date(2016, 10, 25), rooms_for_export)
    assert "\n".join(["\t".join(map(str, line)) for line in lines]) == rooms_for_export_csv.split("\n\n")[2]
