__author__ = "Alexander Elvers <aelvers AT inet.tu-berlin.de>"

import pytest

from tutorplanner.util import settings


class TestSettings:
    def test_none(self):
        s = settings.Settings()
        assert s._data is None
        assert s() is None
        assert s.foo._data is None
        assert s.foo() is None
        assert s.foo.bar._data is None
        assert s.foo.bar() is None
        assert s[0]._data is None
        assert s[0]() is None
        assert s["foo"]._data is None
        assert s["foo"]() is None

    def test_attribute(self):
        s = settings.Settings({
            "a": {
                "b": "c",
                "d": "e",
            },
            "f": 3,
        })
        assert s.a.b() == "c"
        assert s.a.d() == "e"
        assert s.a() == {"b": "c", "d": "e"}
        assert s.f() == 3
        assert s.g() is None

    def test_item(self):
        s = settings.Settings([
            [
                ["a", "b"],
                ["c"],
            ],
            "d",
        ])
        assert s[0][0][0]() == "a"
        assert s[0][0][1]() == "b"
        assert s[0][0]() == ["a", "b"]
        assert s[0][1]() == ["c"]
        assert s[0]() == [["a", "b"], ["c"]]
        assert s[1]() == "d"
        assert s[2]() is None

        s = settings.Settings({
            "a": {
                "b": "c",
                "d": "e",
            },
            "f": 3,
        })
        assert s["a"]["b"]() == "c"
        assert s["a"]["d"]() == "e"
        assert s["a"]() == {"b": "c", "d": "e"}
        assert s["f"]() == 3
        assert s["g"]() is None

        s = settings.Settings(list(range(10)))
        assert s[-1]() == 9
        assert s[2:8:2]() == [2, 4, 6]

    def test_primitive(self):
        assert settings.Settings(1)() == 1
        assert settings.Settings(None)() is None
        assert settings.Settings("a")() == "a"

    def test_incompatible_types(self):
        s = settings.Settings([1, 2, 3])
        assert s.b() is None
        assert s["b"]() is None
        assert s[0].a() is None
        assert s[0][0]() is None

    def test_or(self):
        assert settings.Settings()._or("DEFAULT")() == "DEFAULT"
        assert settings.Settings(1)._or("DEFAULT")() == 1

        s = settings.Settings({"a": [1]})
        assert s.a._or("DEFAULT")() == [1]
        assert s.a[1]._or("DEFAULT")() == "DEFAULT"
        assert s.b._or("DEFAULT")() == "DEFAULT"
        assert s.a._or([5])[0]() == 1
        assert s.b._or([5])[0]() == 5

    def test_get(self):
        s = settings.Settings({"a": [1]})
        assert s._get("a", "DEFAULT")() == [1]
        assert s.a._get(1, "DEFAULT")() == "DEFAULT"
        assert s._get("b", "DEFAULT")() == "DEFAULT"
        assert s._get("a", [5])[0]() == 1
        assert s._get("b", [5])[0]() == 5

    def test_strict(self):
        s = settings.Settings({
            "a": ["b", "c"],
            "d": 3,
        }, strict=True)
        assert s.a() == ["b", "c"]
        assert s.a[0]() == "b"
        assert s.a[1]() == "c"
        assert s.d() == 3

        with pytest.raises(KeyError) as e:
            s.b()
        assert s._get("b", None)() is None
        with pytest.raises(IndexError) as e:
            s.a[2]()
        assert s.a._get(2, None)() is None
        with pytest.raises(TypeError) as e:
            s.a[0].b()
        assert s.a[0]._get("b", None)() is None


def test_get_room_info(monkeypatch):
    def info(type=None, capacity=None, projector=None, tutorial_size=None):
        return dict(type=type, capacity=capacity, projector=projector, tutorial_size=tutorial_size)

    # empty patterns
    monkeypatch.setitem(settings.settings._data, "room_patterns", [])
    assert settings.get_room_info("MAR 0.001") == info()

    # patterns with concrete rooms
    monkeypatch.setitem(settings.settings._data, "room_patterns", [
        dict(pattern="MAR 0.001", type="tutorial", capacity=30, projector=True),
    ])
    assert settings.get_room_info("MAR 0.001") == info("tutorial", 30, True)
    assert settings.get_room_info("MAR 0.002") == info()

    # patterns with buildings and concrete rooms
    monkeypatch.setitem(settings.settings._data, "room_patterns", [
        dict(pattern="MAR *", type="tutorial", projector=True, tutorial_size=24),
        dict(pattern="MAR 0.001", capacity=30),
    ])
    assert settings.get_room_info("MAR 0.001") == info("tutorial", 30, True, 24)
    assert settings.get_room_info("MAR 0.002") == info("tutorial", None, True, 24)

    # patterns with global info, buildings and concrete rooms
    monkeypatch.setitem(settings.settings._data, "room_patterns", [
        dict(pattern="*", type="tutorial", projector=False),
        dict(pattern="MAR *", projector=True),
        dict(pattern="MAR 6.*", type="exercise"),
        dict(pattern="MAR 0.001", capacity=30),
        dict(pattern="MAR 6.001", capacity=25),
    ])
    assert settings.get_room_info("MAR 0.001") == info("tutorial", 30, True)
    assert settings.get_room_info("MAR 0.002") == info("tutorial", None, True)
    assert settings.get_room_info("MAR 6.001") == info("exercise", 25, True)
    assert settings.get_room_info("HFT-FT 131") == info("tutorial", None, False)
