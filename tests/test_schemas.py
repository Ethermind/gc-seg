"""Tests de validadores de api.schemas (pydantic, unidad pura)."""
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

    def test_campos_se_trimean(self):
        c = ContactCreate(nombre="  Juan  ", telefono=" 3415551234 ", mensaje="  hola  ")
        assert c.nombre == "Juan"
        assert c.telefono == "3415551234"
        assert c.mensaje == "hola"

    def test_email_valido_se_normaliza_a_minusculas(self):
        c = self._base(email="  JUAN@Test.COM ")
        assert c.email == "juan@test.com"

    def test_email_vacio_se_convierte_en_none(self):
        assert self._base(email="").email is None

    def test_email_invalido_rechaza(self):
        with pytest.raises(ValidationError):
            self._base(email="no-es-un-email")

    def test_telefono_limpia_caracteres_no_validos(self):
        c = self._base(telefono="+54 (341) 555-1234")
        assert c.telefono == "+54 341 555-1234"

    def test_telefono_muy_corto_rechaza(self):
        with pytest.raises(ValidationError):
            self._base(telefono="123")

    def test_sin_consentimiento_rechaza(self):
        with pytest.raises(ValidationError):
            self._base(aceptarDatos=False)


class TestLeadUpdate:
    def test_estado_valido(self):
        assert LeadUpdate(status="EN_GESTION").status == "en_gestion"

    def test_estado_invalido_rechaza(self):
        with pytest.raises(ValidationError):
            LeadUpdate(status="inventado")

    def test_estado_none_es_valido(self):
        assert LeadUpdate(status=None).status is None


class TestReviewSchemas:
    def test_rating_fuera_de_rango_bajo(self):
        with pytest.raises(ValidationError):
            ReviewCreate(name="A", rating=0, text="texto")

    def test_rating_fuera_de_rango_alto(self):
        with pytest.raises(ValidationError):
            ReviewCreate(name="A", rating=6, text="texto")

    def test_rating_en_rango_y_strip(self):
        r = ReviewCreate(name="  Ana ", rating=5, text="  Genial  ")
        assert r.name == "Ana" and r.text == "Genial" and r.rating == 5

    def test_update_parcial_none_fields(self):
        u = ReviewUpdate()
        assert u.name is None and u.rating is None and u.is_approved is None


class TestAdminUserCreate:
    def test_username_normaliza_y_acepta_formato(self):
        u = AdminUserCreate(username=" Admin.Test-1 ", email="a@b.com", password="secret123")
        assert u.username == "admin.test-1"

    def test_username_con_espacios_internos_rechaza(self):
        with pytest.raises(ValidationError):
            AdminUserCreate(username="con espacio", email="a@b.com", password="secret123")

    def test_rol_invalido_rechaza(self):
        with pytest.raises(ValidationError):
            AdminUserCreate(username="ok", email="a@b.com", password="secret123", role="root")

    def test_rol_superadmin_valido(self):
        u = AdminUserCreate(username="okk", email="a@b.com", password="secret123", role="SUPERADMIN")
        assert u.role == "superadmin"

    def test_email_invalido_rechaza(self):
        with pytest.raises(ValidationError):
            AdminUserCreate(username="okk", email="mal", password="secret123")


class TestCoverageSchemas:
    def test_categoria_valida_normaliza(self):
        c = CoverageBase(categoria=" PERSONAS ", titulo="T", icono="car", descripcion="D")
        assert c.categoria == "personas"

    def test_categoria_invalida_rechaza(self):
        with pytest.raises(ValidationError):
            CoverageBase(categoria="mascotas", titulo="T", icono="car", descripcion="D")

    def test_update_categoria_invalida_rechaza(self):
        with pytest.raises(ValidationError):
            CoverageUpdate(categoria="mascotas")

    def test_update_parcial_ok(self):
        u = CoverageUpdate(titulo="  Nuevo título ")
        assert u.titulo == "Nuevo título"
        assert u.categoria is None


class TestFaqSchemas:
    def test_crea_y_trimea(self):
        f = FAQBase(pregunta="  ¿Pregunta? ", respuesta="  Respuesta ")
        assert f.pregunta == "¿Pregunta?"
        assert f.respuesta == "Respuesta"

    def test_pregunta_vacia_rechaza(self):
        with pytest.raises(ValidationError):
            FAQBase(pregunta="   ", respuesta="R")

    def test_update_parcial(self):
        u = FAQUpdate(activo=False)
        assert u.activo is False
        assert u.pregunta is None
