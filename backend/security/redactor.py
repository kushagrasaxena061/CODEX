import re

class SecretRedactor:
    def __init__(self):
        # Regex patterns for common secrets (API keys, passwords, private keys)
        self.patterns = [
            (r"(?i)(api[_-]?key[\s:=]+)(['\"]?[a-zA-Z0-9_\-]{16,}['\"]?)", r"\1[REDACTED]"),
            (r"(?i)(password[\s:=]+)(['\"]?[^'\"]+['\"]?)", r"\1[REDACTED]"),
            (r"(?i)(secret[\s:=]+)(['\"]?[a-zA-Z0-9_\-]{16,}['\"]?)", r"\1[REDACTED]"),
            (r"(?i)(bearer[\s:=]+)(['\"]?[a-zA-Z0-9_\-\.]{20,}['\"]?)", r"\1[REDACTED]"),
            (r"-----BEGIN [\w\s]+ PRIVATE KEY-----[a-zA-Z0-9\s+/=\n]+-----END [\w\s]+ PRIVATE KEY-----", "[REDACTED PRIVATE KEY]")
        ]

    def redact(self, text: str) -> str:
        """Scans text and masks potential secrets before sending to LLM."""
        if not text:
            return text
        redacted_text = text
        for pattern, replacement in self.patterns:
            redacted_text = re.sub(pattern, replacement, redacted_text)
        return redacted_text
