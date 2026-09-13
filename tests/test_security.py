import pytest
from backend.security.redactor import SecretRedactor
from backend.security.command_validator import CommandValidator
from backend.config.settings import settings, AutonomyLevel

def test_secret_redactor():
    redactor = SecretRedactor()
    
    # Test API Key redaction
    text1 = "const apiKey = 'AIzaSyB-1234567890abcdefGHIJKL';"
    assert "[REDACTED]" in redactor.redact(text1)
    assert "AIzaSyB" not in redactor.redact(text1)
    
    # Test Password redaction
    text2 = "db_password: 'super_secret_password_123'"
    assert "[REDACTED]" in redactor.redact(text2)
    assert "super_secret_password_123" not in redactor.redact(text2)

def test_command_validator():
    validator = CommandValidator()
    
    # Absolute blocklist test (testing sudo in isolation)
    allowed, reason = validator.is_command_allowed("sudo ls")
    assert not allowed
    assert "sudo" in reason
    
    # Test Medium Autonomy restrictions
    settings.AUTONOMY_LEVEL = AutonomyLevel.MEDIUM
    allowed, reason = validator.is_command_allowed("git reset --hard HEAD")
    assert not allowed
    
    # Safe command test
    allowed, reason = validator.is_command_allowed("npm run test")
    assert allowed
