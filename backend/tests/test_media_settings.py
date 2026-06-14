from pathlib import Path

from django.conf import settings


def test_media_settings_are_configured():
    assert settings.MEDIA_URL == "/media/"
    assert Path(settings.MEDIA_ROOT) == settings.BASE_DIR / "media"
