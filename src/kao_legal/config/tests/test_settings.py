"""Tests for settings module."""

from kao_legal.config.settings import Settings, get_settings


def test_get_settings_returns_settings_instance():
    """Test that get_settings returns a Settings instance."""
    settings = get_settings()
    assert isinstance(settings, Settings)


def test_get_settings_is_cached():
    """Test that get_settings returns the same instance (cached)."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2
