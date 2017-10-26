__author__ = "Alexander Elvers <aelvers AT inet.tu-berlin.de>"

import sys
import datetime
import bs4
from tutorplanner.input import lsf_parser
from tutorplanner.input.rooms import Room


def test_parse_lsf_date():
    date = lsf_parser.parse_lsf_date("17.10.2016")
    assert isinstance(date, datetime.date)
    assert str(date) == "2016-10-17"


def test_parse_lsf_time():
    time = lsf_parser.parse_lsf_time("14:00")
    assert isinstance(time, datetime.time)
    assert str(time) == "14:00:00"


def test_parse_lsf_weekday():
    for i, w in enumerate(("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")):
        assert lsf_parser.parse_lsf_weekday(w) == i

    assert lsf_parser.parse_lsf_weekday("-") is None


def test_filter_date_range():
    # test with weekday == None
    start = datetime.date(2016, 10, 17)
    end = datetime.date(2016, 10, 21)
    dates = list(lsf_parser.filter_date_range(start, end))
    assert dates == [
        datetime.date(2016, 10, 17),
        datetime.date(2016, 10, 18),
        datetime.date(2016, 10, 19),
        datetime.date(2016, 10, 20),
        datetime.date(2016, 10, 21),
    ]

    # test with weekday == None, don't include weekend
    start = datetime.date(2016, 10, 21)
    end = datetime.date(2016, 10, 24)
    dates = list(lsf_parser.filter_date_range(start, end))
    assert dates == [datetime.date(2016, 10, 21), datetime.date(2016, 10, 24)]

    # test with weekday == 3
    start = datetime.date(2016, 10, 17)
    end = datetime.date(2016, 10, 28)
    dates = list(lsf_parser.filter_date_range(start, end, 3))
    assert dates == [datetime.date(2016, 10, 20), datetime.date(2016, 10, 27)]

    # test with weekday == 0, first day included
    start = datetime.date(2016, 10, 17)
    end = datetime.date(2016, 10, 28)
    dates = list(lsf_parser.filter_date_range(start, end, 0))
    assert dates == [datetime.date(2016, 10, 17), datetime.date(2016, 10, 24)]

    # test with weekday == 4, last day included
    start = datetime.date(2016, 10, 17)
    end = datetime.date(2016, 10, 28)
    dates = list(lsf_parser.filter_date_range(start, end, 4))
    assert dates == [datetime.date(2016, 10, 21), datetime.date(2016, 10, 28)]


def test_filter_time_range():
    # test with time_range == None, whole day
    start = 0
    end = 24
    times = list(lsf_parser.filter_time_range(start, end))
    assert len(times) == 24
    assert times[0] == 0
    assert times[-1] == 23

    # test with time_range == None, a few hours
    start = 14
    end = 16
    times = list(lsf_parser.filter_time_range(start, end))
    assert times == [14, 15]

    # test with time_range every 2 hours
    start = 12
    end = 16
    time_slots = [10, 12, 14, 16]
    times = list(lsf_parser.filter_time_range(start, end, time_slots))
    assert times == [
        12,
        14,
    ]


def test_get_room_names():
    soup = bs4.BeautifulSoup("""
    <Lecture>
        <Terms><Rooms><RaumBez>MAR 0.003</RaumBez></Rooms></Terms>
        <Terms><Rooms><RaumBez>TEL 109</RaumBez></Rooms></Terms>
    </Lecture>
    """, "lxml-xml")
    assert set(lsf_parser.get_room_names(soup)) == {"MAR 0.003", "TEL 109"}


def test_get_bookings(monkeypatch):
    monkeypatch.setattr(lsf_parser, "time_slots", [10, 12, 14, 16])
    soup = bs4.BeautifulSoup("""
    <Lecture>
        <Terms>
            <TerBeginn>10:00</TerBeginn>
            <TerEnde>14:00</TerEnde>
            <TerBeginDat>17.10.2016</TerBeginDat>
            <TerEndeDat>28.10.2016</TerEndeDat>
            <TerRhyth>wöchentl</TerRhyth>
            <WoTag>Di</WoTag>
            <Rooms><RaumBez>MAR 0.003</RaumBez></Rooms>
        </Terms>
        <Terms>
            <TerBeginn>16:00</TerBeginn>
            <TerEnde>18:00</TerEnde>
            <TerBeginDat>17.10.2016</TerBeginDat>
            <TerEndeDat>28.10.2016</TerEndeDat>
            <TerRhyth>14tägl</TerRhyth>
            <WoTag>Mo</WoTag>
            <Rooms><RaumBez>TEL 206</RaumBez></Rooms>
        </Terms>
    </Lecture>
    """, "lxml-xml")
    assert set(lsf_parser.get_bookings(soup)) == {
        ("MAR 0.003", datetime.date(2016, 10, 18), 10),
        ("MAR 0.003", datetime.date(2016, 10, 18), 12),
        ("MAR 0.003", datetime.date(2016, 10, 25), 10),
        ("MAR 0.003", datetime.date(2016, 10, 25), 12),
        ("TEL 206", datetime.date(2016, 10, 17), 16),
    }


def test_parse_files(tmpdir):
    # test reading from temporary files
    directory = tmpdir.mkdir("data")
    f1 = directory.join("data1.xml")
    f1.write("""
    <Lecture>
        <Terms>
            <TerBeginn>10:00</TerBeginn>
            <TerEnde>14:00</TerEnde>
            <TerBeginDat>17.10.2016</TerBeginDat>
            <TerEndeDat>28.10.2016</TerEndeDat>
            <TerRhyth>wöchentl</TerRhyth>
            <WoTag>Di</WoTag>
            <Rooms><RaumBez>MAR 0.003</RaumBez></Rooms>
        </Terms>
        <Terms>
            <TerBeginn>10:00</TerBeginn>
            <TerEnde>14:00</TerEnde>
            <TerBeginDat>17.10.2016</TerBeginDat>
            <TerEndeDat>28.10.2016</TerEndeDat>
            <TerRhyth>wöchentl</TerRhyth>
            <WoTag>Mi</WoTag>
            <Rooms><RaumBez>TEL 106</RaumBez></Rooms>
        </Terms>
    </Lecture>
    """)
    f2 = directory.join("data2.xml")
    f2.write("""
    <Lecture>
        <Terms>
            <TerBeginn>12:00</TerBeginn>
            <TerEnde>16:00</TerEnde>
            <TerBeginDat>17.10.2016</TerBeginDat>
            <TerEndeDat>28.10.2016</TerEndeDat>
            <TerRhyth>wöchentl</TerRhyth>
            <WoTag>Di</WoTag>
            <Rooms><RaumBez>TEL 206</RaumBez></Rooms>
        </Terms>
    </Lecture>
    """)

    rooms = lsf_parser.parse_files(map(str, [f1, f2]))
    for room in rooms:
        if room.name == "MAR 0.003":
            assert list(room.get_booked_times(datetime.date(2016, 10, 18))) == [10, 12]
        elif room.name == "TEL 106":
            assert list(room.get_booked_times(datetime.date(2016, 10, 19))) == [10, 12]
        elif room.name == "TEL 206":
            assert list(room.get_booked_times(datetime.date(2016, 10, 18))) == [12, 14]
        else:
            assert False
    assert len(rooms) == 3

    # parse with existing rooms
    r1 = Room("MAR 0.003")
    r1.book(datetime.date(2016, 10, 18), 14)
    rooms = lsf_parser.parse_files(map(str, [f1, f2]), initial_rooms=[r1])
    for room in rooms:
        if room.name == "MAR 0.003":
            assert list(room.get_booked_times(datetime.date(2016, 10, 18))) == [10, 12, 14]
        elif room.name == "TEL 106":
            assert list(room.get_booked_times(datetime.date(2016, 10, 19))) == [10, 12]
        elif room.name == "TEL 206":
            assert list(room.get_booked_times(datetime.date(2016, 10, 18))) == [12, 14]
        else:
            assert False
    assert len(rooms) == 3
