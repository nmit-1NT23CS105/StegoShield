"""StegoShield: Steganography Attack & Forensic Detection Toolkit.

Modules:
    crypto_utils   - password based AES encryption (Fernet + PBKDF2)
    lsb            - hide / extract data in the least significant bits of a PNG
    steganalysis   - forensic detection tests (chi-square, SPA, EOF, metadata)
    forensic_report- HTML/TXT report with SHA-256 chain of custody
"""
__version__ = "1.0"
