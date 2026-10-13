"""Tests de generate_avatar_initials (función pura de api.routes.reviews)."""
from api.routes.reviews import generate_avatar_initials


def test_nombre_y_apellido_da_iniciales(self=None):
    assert generate_avatar_initials("Juan Perez") == "JP"


def test_un_solo_nombre_toma_dos_letras():
    assert generate_avatar_initials("Maria") == "MA"


def test_vacio_devuelve_default(self=None):
    assert generate_avatar_initials("   ") == "U"


def test_minusculas_se_normalizan_a_mayusculas():
    assert generate_avatar_initials("sofia giannini") == "SG"


def test_tres_nombres_usa_los_primeros_dos():
    assert generate_avatar_initials("Ana Maria Lopez") == "AM"
