"""Tests for generate_avatar_initials (pure function from api.routes.reviews)."""
from api.routes.reviews import generate_avatar_initials


def test_first_and_last_name_give_initials():
    assert generate_avatar_initials("Juan Perez") == "JP"


def test_single_name_takes_two_letters():
    assert generate_avatar_initials("Maria") == "MA"


def test_empty_returns_default():
    assert generate_avatar_initials("   ") == "U"


def test_lowercase_is_normalized_to_uppercase():
    assert generate_avatar_initials("sofia giannini") == "SG"


def test_three_names_uses_the_first_two():
    assert generate_avatar_initials("Ana Maria Lopez") == "AM"
