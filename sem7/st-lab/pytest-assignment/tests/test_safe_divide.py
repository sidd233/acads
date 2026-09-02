import pytest

from app import safe_divide


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (10, 2, 5),
        (9, 3, 3),
        (-8, 4, -2),
        (7, 2, 3.5),
    ],
)
def test_safe_divide(a, b, expected):
    assert safe_divide(a, b) == expected


def test_divide_zero():
    with pytest.raises(ZeroDivisionError):
        safe_divide(10, 0)
