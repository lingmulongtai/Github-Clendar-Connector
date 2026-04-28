from app.services.color_mapper import to_color_id, to_level


def test_to_level_boundaries() -> None:
    assert to_level(0) == 0
    assert to_level(1) == 1
    assert to_level(3) == 1
    assert to_level(4) == 2
    assert to_level(7) == 2
    assert to_level(8) == 3
    assert to_level(12) == 3
    assert to_level(13) == 4


def test_to_color_id() -> None:
    assert to_color_id(0) == "8"
    assert to_color_id(2) == "2"
    assert to_color_id(6) == "10"
    assert to_color_id(10) == "9"
    assert to_color_id(20) == "11"
