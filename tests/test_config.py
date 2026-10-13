"""Tests for api.config: DB URL normalization and CORS parsing.

The pydantic-settings constructor keyword arguments take precedence over env
vars, so each case instantiates Settings directly without mutating the process
environment.
"""
from pathlib import Path

from api.config import Settings


def _settings(db_url: str) -> Settings:
    return Settings(DATABASE_URL=db_url)


class TestDatabaseUrlNormalization:
    def test_legacy_postgres_scheme_is_normalized(self):
        s = _settings("postgres://user:pass@host:5432/db")
        assert s.sqlalchemy_database_url == "postgresql://user:pass@host:5432/db"

    def test_postgresql_scheme_is_untouched(self):
        s = _settings("postgresql://user:pass@host:5432/db")
        assert s.sqlalchemy_database_url == "postgresql://user:pass@host:5432/db"

    def test_psycopg_driver_suffix_is_stripped(self):
        # Regression test for the 2026-10-13 outage: integrations injecting
        # postgresql+psycopg:// must not force a driver that isn't installed.
        s = _settings("postgresql+psycopg://user:pass@host:5432/db?sslmode=require")
        assert s.sqlalchemy_database_url == "postgresql://user:pass@host:5432/db?sslmode=require"

    def test_psycopg2_driver_suffix_is_stripped(self):
        s = _settings("postgresql+psycopg2://user:pass@host:5432/db")
        assert s.sqlalchemy_database_url == "postgresql://user:pass@host:5432/db"

    def test_url_whitespace_is_trimmed(self):
        s = _settings("  postgres://user:pass@host:5432/db  ")
        assert s.sqlalchemy_database_url == "postgresql://user:pass@host:5432/db"

    def test_relative_sqlite_is_anchored_to_repo_root(self):
        s = _settings("sqlite:///local.db")
        url = s.sqlalchemy_database_url
        assert url.startswith("sqlite:////")  # absolute
        assert url.endswith("/local.db")
        # Anchored at THIS repo's root (where .git lives), not at the CWD
        assert str(Path(__file__).resolve().parent.parent) in url

    def test_absolute_sqlite_is_untouched(self):
        s = _settings("sqlite:////tmp/something.db")
        assert s.sqlalchemy_database_url == "sqlite:////tmp/something.db"


class TestCorsOrigins:
    def test_asterisk(self):
        assert Settings(ALLOWED_ORIGINS="*").cors_origins == ["*"]

    def test_comma_separated_list_with_spaces(self):
        s = Settings(ALLOWED_ORIGINS=" https://a.com ,https://b.com ")
        assert s.cors_origins == ["https://a.com", "https://b.com"]

    def test_empty_entries_are_discarded(self):
        s = Settings(ALLOWED_ORIGINS="https://a.com,, ,")
        assert s.cors_origins == ["https://a.com"]
