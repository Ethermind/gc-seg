"""Tests for api.schemas validators (pure pydantic units)."""
import pytest
from pydantic import ValidationError

from api.schemas import (
    ContactCreate, LeadUpdate, ReviewCreate, ReviewUpdate,
    AdminUserCreate, CoverageBase, CoverageUpdate, FAQBase, FAQUpdate,
)


class TestContactCreate:
    def _base(self, **over):
        data = {
            "nombre": "Juan Perez",
            "telefono": "+54 9 341 555-1234",
            "aceptarDatos": True,
        }
        data.update(over)
        return ContactCreate(**data)

    def test_fields_are_trimmed(self):
        c = ContactCreate(nombre="  Juan  ", telefono=" 3415551234 ", mensaje="  hello  ")
        assert c.nombre == "Juan"
        assert c.telefono == "3415551234"
        assert c.mensaje == "hello"

    def test_valid_email_is_lowercased(self):
        c = self._base(email="  JUAN@Test.COM ")
        assert c.email == "juan@test.com"

    def test_empty_email_becomes_none(self):
        assert self._base(email="").email is None

    def test_invalid_email_is_rejected(self):
        with pytest.raises(ValidationError):
            self._base(email="not-an-email")

    def test_phone_strips_invalid_characters(self):
        c = self._base(telefono="+54 (341) 555-1234")
        assert c.telefono == "+54 341 555-1234"

    def test_phone_too_short_is_rejected(self):
        with pytest.raises(ValidationError):
            self._base(telefono="123")

    def test_without_consent_is_rejected(self):
        with pytest.raises(ValidationError):
            self._base(aceptarDatos=False)


class TestLeadUpdate:
    def test_valid_status(self):
        assert LeadUpdate(status="EN_GESTION").status == "en_gestion"

    def test_invalid_status_is_rejected(self):
        with pytest.raises(ValidationError):
            LeadUpdate(status="invented")

    def test_none_status_is_valid(self):
        assert LeadUpdate(status=None).status is None


class TestReviewSchemas:
    def test_rating_too_low(self):
        with pytest.raises(ValidationError):
            ReviewCreate(name="A", rating=0, text="text")

    def test_rating_too_high(self):
        with pytest.raises(ValidationError):
            ReviewCreate(name="A", rating=6, text="text")

    def test_rating_in_range_and_strip(self):
        r = ReviewCreate(name="  Ana ", rating=5, text="  Great  ")
        assert r.name == "Ana" and r.text == "Great" and r.rating == 5

    def test_update_none_fields(self):
        u = ReviewUpdate()
        assert u.name is None and u.rating is None and u.is_approved is None


class TestAdminUserCreate:
    def test_username_is_normalized_and_valid_format_accepted(self):
        u = AdminUserCreate(username=" Admin.Test-1 ", email="a@b.com", password="secret123")
        assert u.username == "admin.test-1"

    def test_username_with_inner_spaces_is_rejected(self):
        with pytest.raises(ValidationError):
            AdminUserCreate(username="with space", email="a@b.com", password="secret123")

    def test_invalid_role_is_rejected(self):
        with pytest.raises(ValidationError):
            AdminUserCreate(username="okk", email="a@b.com", password="secret123", role="root")

    def test_superadmin_role_is_valid(self):
        u = AdminUserCreate(username="okk", email="a@b.com", password="secret123", role="SUPERADMIN")
        assert u.role == "superadmin"

    def test_invalid_email_is_rejected(self):
        with pytest.raises(ValidationError):
            AdminUserCreate(username="okk", email="mal", password="secret123")


class TestCoverageSchemas:
    def test_valid_category_is_normalized(self):
        c = CoverageBase(categoria=" PERSONAS ", titulo="T", icono="car", descripcion="D")
        assert c.categoria == "personas"

    def test_invalid_category_is_rejected(self):
        with pytest.raises(ValidationError):
            CoverageBase(categoria="mascotas", titulo="T", icono="car", descripcion="D")

    def test_update_invalid_category_is_rejected(self):
        with pytest.raises(ValidationError):
            CoverageUpdate(categoria="mascotas")

    def test_partial_update_ok(self):
        u = CoverageUpdate(titulo="  New title ")
        assert u.titulo == "New title"
        assert u.categoria is None


class TestFaqSchemas:
    def test_create_trims_fields(self):
        f = FAQBase(pregunta="  Question? ", respuesta="  Answer ")
        assert f.pregunta == "Question?"
        assert f.respuesta == "Answer"

    def test_empty_question_is_rejected(self):
        with pytest.raises(ValidationError):
            FAQBase(pregunta="   ", respuesta="R")

    def test_partial_update(self):
        u = FAQUpdate(activo=False)
        assert u.activo is False
        assert u.pregunta is None
