import pytest
from backend.config.settings import settings, AutonomyLevel

def test_settings_loaded():
    assert settings.WORKSPACE_ROOT is not None
    assert settings.AUTONOMY_LEVEL in [AutonomyLevel.LOW, AutonomyLevel.MEDIUM, AutonomyLevel.HIGH]
    assert settings.OLLAMA_BASE_URL.startswith("http")
