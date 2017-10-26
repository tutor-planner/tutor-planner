__author__ = "Alexander Elvers <aelvers AT inet.tu-berlin.de>"

import datetime

from tutorplanner.util import converter


def test_date_convert():
    assert converter.day_index_to_date(1) == datetime.date(2016, 10, 17)
    assert converter.day_index_to_date(5) == datetime.date(2016, 10, 21)
    assert converter.day_index_to_date(6) == datetime.date(2016, 10, 24)
    assert converter.day_index_to_date(10) == datetime.date(2016, 10, 28)

    assert converter.date_to_day_index(datetime.date(2016, 10, 17)) == 1
    assert converter.date_to_day_index(datetime.date(2016, 10, 21)) == 5
    assert converter.date_to_day_index(datetime.date(2016, 10, 24)) == 6
    assert converter.date_to_day_index(datetime.date(2016, 10, 28)) == 10
