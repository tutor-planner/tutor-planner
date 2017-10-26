__author__ = "Alexander Elvers <aelvers AT inet.tu-berlin.de>"

import datetime
import pytest

from tutorplanner.input import tutor
from tutorplanner.util import settings


def csv_line(*args, cols=7):
    return "\t".join(args + ("",) * (cols - len(args)))


test_data = "\n".join([
    csv_line("Name", "Mustermann"),
    csv_line("Vorname", "Erika"),
    csv_line("E-Mail", "erika@mustermann.example"),
    csv_line("Fachgebiet", "INET"),
    csv_line("Mobil", "123456789"),
    csv_line("Monatsstunden", "40"),
    csv_line("max. Arbeitszeit ohne Pause [>=3]", "3"),
    csv_line("max. Anzahl an Tutorien hintereinander [>=2] ", "2"),
    csv_line("C-Kenntnisse", "3"),
    csv_line("Unsicherheit 2. Woche", "2"),
    csv_line(),
    csv_line("", "", "17.10.", "18.10.", "19.10.", "20.10.", "21.10."),
    csv_line("", "Uhrzeit", "Mo.", "Di.", "Mi.", "Do.", "Fr."),
    csv_line("", "10", "X", "0", "1", "2", "3"),
    csv_line("", "12", "X", "X", "0", "2", "1"),
    csv_line("", "14", "X", "1", "X", "1", "X"),
    csv_line("", "16", "X", "0", "3", "X", "2"),
    csv_line(),
    csv_line("", "", "24.10.", "25.10.", "26.10.", "27.10.", "28.10."),
    csv_line("", "Uhrzeit", "Mo.", "Di.", "Mi.", "Do.", "Fr."),
    csv_line("", "10", "1", "2", "3", "1", "1"),
    csv_line("", "12", "1", "X", "2", "0", "0"),
    csv_line("", "14", "3", "3", "X", "3", "X"),
    csv_line("", "16", "X", "3", "2", "X", "3"),
])

test_data_week_2 = "\n".join([
    csv_line("Nachname", "Mustermann"),
    csv_line("", "", "", "", "", "", ""),
    csv_line("", "", "24.10.", "25.10.", "26.10.", "27.10.", "28.10."),
    # "", "Uhrzeit", "Mo.", "Di.", "Mi.", "Do.", "Fr."
    csv_line("", "10", "3", "1", "0", "1", "1"),
    csv_line("", "12", "3", "X", "1", "1", "3"),
    csv_line("", "14", "0", "2", "X", "3", "X"),
    csv_line("", "16", "X", "3", "2", "X", "1"),
])


class TestTutor:
    def test_load_from_file(self, tmpdir):
        directory = tmpdir.mkdir("data")
        f1 = directory.join("C-Kurs-Fragebogen_INET_Mustermann.csv")
        f1.write(test_data)

        t = tutor.Tutor.load_from_file(str(f1))
        assert t.last_name == "Mustermann"
        assert t.first_name == "Erika"
        assert t.email == "erika@mustermann.example"
        assert t.department == "INET"
        assert t.phone == "123456789"
        assert t.monthly_work_hours == 40
        assert t.max_hours_without_break == 3
        assert t.max_tutorials_without_break == 2
        assert t.knowledge == 3
        assert t.unsure_about_second_week == 2

        assert str(t) == "Erika Mustermann"

        assert t.availability == {
            datetime.date(2016, 10, 17): {10: None, 11: None, 12: None, 13: None, 14: None, 15: None, 16: None, 17: None},
            datetime.date(2016, 10, 18): {10: 0,    11: 0,    12: None, 13: None, 14: 1,    15: 1,    16: 0,    17: 0},
            datetime.date(2016, 10, 19): {10: 1,    11: 1,    12: 0,    13: 0,    14: None, 15: None, 16: 3,    17: 3},
            datetime.date(2016, 10, 20): {10: 2,    11: 2,    12: 2,    13: 2,    14: 1,    15: 1,    16: None, 17: None},
            datetime.date(2016, 10, 21): {10: 3,    11: 3,    12: 1,    13: 1,    14: None, 15: None, 16: 2,    17: 2},
            datetime.date(2016, 10, 24): {10: 1,    11: 1,    12: 1,    13: 1,    14: 3,    15: 3,    16: None, 17: None},
            datetime.date(2016, 10, 25): {10: 2,    11: 2,    12: None, 13: None, 14: 3,    15: 3,    16: 3,    17: 3},
            datetime.date(2016, 10, 26): {10: 3,    11: 3,    12: 2,    13: 2,    14: None, 15: None, 16: 2,    17: 2},
            datetime.date(2016, 10, 27): {10: 1,    11: 1,    12: 0,    13: 0,    14: 3,    15: 3,    16: None, 17: None},
            datetime.date(2016, 10, 28): {10: 1,    11: 1,    12: 0,    13: 0,    14: None, 15: None, 16: 3,    17: 3},
        }

        # test ValueError: availability not set but expected
        f2 = directory.join("C-Kurs-Fragebogen_INET_Mustermann2.csv")
        f2.write(test_data.replace("\t10\tX\t0\t1\t2\t3", "\t10\tX\tX\t1\t2\t3"))
        with pytest.raises(ValueError) as e:
            tutor.Tutor.load_from_file(str(f2))
        assert str(e.value) == "invalid availablity (Erika Mustermann): 2016-10-18 at 10: not set where it is expected"

        f3 = directory.join("C-Kurs-Fragebogen_INET_Mustermann3.csv")
        f3.write(test_data.replace("\t10\tX\t0\t1\t2\t3", "\t10\tX\t0\t1\t \t3"))
        with pytest.raises(ValueError) as e:
            tutor.Tutor.load_from_file(str(f3))
        assert str(e.value) == "invalid availablity (Erika Mustermann): 2016-10-20 at 10: not set where it is expected"

        # test ValueError: availability set but not expected
        f4 = directory.join("C-Kurs-Fragebogen_INET_Mustermann4.csv")
        f4.write(test_data.replace("\t12\t1\tX\t2\t0\t0", "\t12\t1\t3\t2\t0\t0"))
        with pytest.raises(ValueError) as e:
            tutor.Tutor.load_from_file(str(f4))
        assert str(e.value) == "invalid availablity (Erika Mustermann): 2016-10-25 at 12: 3 where it is not expected"

        # test ValueError: file too short
        f5 = directory.join("C-Kurs-Fragebogen_INET_Mustermann4.csv")
        f5.write(test_data[:-50])
        with pytest.raises(ValueError) as e:
            tutor.Tutor.load_from_file(str(f5))
        assert "too few lines" in str(e.value)

    def test_load_from_file_second_week(self, tmpdir, monkeypatch):
        directory = tmpdir.mkdir("data")
        f1 = directory.join("C-Kurs_2te_Woche_Fragebogen_Mustermann.csv")
        f1.write(test_data_week_2)

        t = tutor.Tutor.load_from_file_second_week(str(f1))
        assert t.last_name == "Mustermann"
        assert t.availability == {
            datetime.date(2016, 10, 24): {10: 3,    11: 3,    12: 3,    13: 3,    14: 0,    15: 0,    16: None, 17: None},
            datetime.date(2016, 10, 25): {10: 1,    11: 1,    12: None, 13: None, 14: 2,    15: 2,    16: 3,    17: 3},
            datetime.date(2016, 10, 26): {10: 0,    11: 0,    12: 1,    13: 1,    14: None, 15: None, 16: 2,    17: 2},
            datetime.date(2016, 10, 27): {10: 1,    11: 1,    12: 1,    13: 1,    14: 3,    15: 3,    16: None, 17: None},
            datetime.date(2016, 10, 28): {10: 1,    11: 1,    12: 3,    13: 3,    14: None, 15: None, 16: 1,    17: 1},
        }


def test_load_tutors(tmpdir, monkeypatch):
    directory = tmpdir.mkdir("data1")
    directory_week_2 = tmpdir.mkdir("data2")

    monkeypatch.setitem(settings.settings._data, "paths", {
        "tutor_responses": [str(directory), str(directory_week_2)],
    })

    directory.join("C-Kurs-Fragebogen_INET_Mustermann.csv").write(test_data)
    directory_week_2.join("C-Kurs_2te_Woche_Fragebogen_Mustermann.csv").write(test_data_week_2)

    # test second week update
    ts = tutor.load_tutors()
    assert len(ts) == 1
    t = ts[0]
    assert t.last_name == "Mustermann"
    assert t.first_name == "Erika"
    assert t.email == "erika@mustermann.example"
    assert t.department == "INET"
    assert t.phone == "123456789"
    assert t.monthly_work_hours == 40
    assert t.max_hours_without_break == 3
    assert t.max_tutorials_without_break == 2
    assert t.knowledge == 3
    assert t.unsure_about_second_week == 2

    assert t.availability == {
        datetime.date(2016, 10, 17): {10: None, 11: None, 12: None, 13: None, 14: None, 15: None, 16: None, 17: None},
        datetime.date(2016, 10, 18): {10: 0,    11: 0,    12: None, 13: None, 14: 1,    15: 1,    16: 0,    17: 0},
        datetime.date(2016, 10, 19): {10: 1,    11: 1,    12: 0,    13: 0,    14: None, 15: None, 16: 3,    17: 3},
        datetime.date(2016, 10, 20): {10: 2,    11: 2,    12: 2,    13: 2,    14: 1,    15: 1,    16: None, 17: None},
        datetime.date(2016, 10, 21): {10: 3,    11: 3,    12: 1,    13: 1,    14: None, 15: None, 16: 2,    17: 2},
        datetime.date(2016, 10, 24): {10: 3,    11: 3,    12: 3,    13: 3,    14: 0,    15: 0,    16: None, 17: None},
        datetime.date(2016, 10, 25): {10: 1,    11: 1,    12: None, 13: None, 14: 2,    15: 2,    16: 3,    17: 3},
        datetime.date(2016, 10, 26): {10: 0,    11: 0,    12: 1,    13: 1,    14: None, 15: None, 16: 2,    17: 2},
        datetime.date(2016, 10, 27): {10: 1,    11: 1,    12: 1,    13: 1,    14: 3,    15: 3,    16: None, 17: None},
        datetime.date(2016, 10, 28): {10: 1,    11: 1,    12: 3,    13: 3,    14: None, 15: None, 16: 1,    17: 1},
    }
