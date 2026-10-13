"""Tests de api.config: normalización de URL de DB y parsing de CORS.

Los kwargs del constructor de pydantic-settings pisan a las env vars, así que
cada caso instancia Settings directamente sin tocar el entorno del proceso.
"""
from pathlib import Path

from api.config import Settings


def _settings(db_url: str) -> Settings:
    return Settings(DATABASE_URL=db_url)


class TestDatabaseUrlNormalization:
    def test_postgres_legacy_scheme_se_normaliza(self):
        s = _settings("postgres://user:pass@host:5432/db")
        assert s.sqlalchemy_database_url == "postgresql://user:pass@host:5432/db"

    def test_postgresql_scheme_queda_intacto(self):
        s = _settings("postgresql://user:pass@host:5432/db")
        assert s.sqlalchemy_database_url == "postgresql://user:pass@host:5432/db"

    def test_sufijo_driver_psycopg_se_remueve(self):
        # Regresión del outage 13/10/2026: integraciones que inyectan
        # postgresql+psycopg:// no deben forzar un driver distinto al instalado.
        s = _settings("postgresql+psycopg://user:pass@host:5432/db?sslmode=require")
        assert s.sqlalchemy_database_url == "postgresql://user:pass@host:5432/db?sslmode=require"

    def test_sufijo_driver_psycopg2_se_remueve(self):
        s = _settings("postgresql+psycopg2://user:pass@host:5432/db")
        assert s.sqlalchemy_database_url == "postgresql://user:pass@host:5432/db"

    def test_espacios_en_la_url_se_limpian(self):
        s = _settings("  postgres://user:pass@host:5432/db  ")
        assert s.sqlalchemy_database_url == "postgresql://user:pass@host:5432/db"

    def test_sqlite_relativa_se_ancla_a_la_raiz_del_repo(self):
        s = _settings("sqlite:///local.db")
        url = s.sqlalchemy_database_url
        assert url.startswith("sqlite:////")  # absoluta
        assert url.endswith("/local.db")
        # Anclada a la raíz de ESTE repo (donde está .git), no al CWD
        assert str(Path(__file__).resolve().parent.parent) in url

    def test_sqlite_absoluta_no_se_toca(self):
        s = _settings("sqlite:////tmp/algo.db")
        assert s.sqlalchemy_database_url == "sqlite:////tmp/algo.db"


class TestCorsOrigins:
    def test_asterisco(self):
        assert Settings(ALLOWED_ORIGINS="*").cors_origins == ["*"]

    def test_lista_por_comas_con_espacios(self):
        s = Settings(ALLOWED_ORIGINS=" https://a.com ,https://b.com ")
        assert s.cors_origins == ["https://a.com", "https://b.com"]

    def test_entradas_vacias_se_descartan(self):
        s = Settings(ALLOWED_ORIGINS="https://a.com,, ,")
        assert s.cors_origins == ["https://a.com"]
