"""Password based encryption for the hidden payload.

We never hide the plain message. It is first encrypted with Fernet
(AES-128 in CBC mode + HMAC-SHA256 for integrity). The Fernet key is derived
from the user's password with PBKDF2-HMAC-SHA256 and a random 16 byte salt.

Stored blob = salt (16 bytes) + raw Fernet token bytes

Note: a Fernet token is normally base64 text. We store the decoded raw bytes,
because base64 text only uses 64 ASCII characters and that pattern would make
the hidden bits easy to spot (and wastes 25% of the space).
"""
import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_SIZE = 16
PBKDF2_ITERATIONS = 200_000


class WrongPasswordError(Exception):
    """Raised when the password is wrong or the data was tampered with."""


def derive_key(password, salt):
    """Turn a human password into a 32 byte Fernet key (base64 encoded)."""
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=salt, iterations=PBKDF2_ITERATIONS)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def encrypt(data, password):
    """Encrypt bytes with a password. Returns salt + token."""
    salt = os.urandom(SALT_SIZE)
    token = Fernet(derive_key(password, salt)).encrypt(data)
    return salt + base64.urlsafe_b64decode(token)


def decrypt(blob, password):
    """Decrypt salt + token. Raises WrongPasswordError on failure."""
    salt = blob[:SALT_SIZE]
    token = base64.urlsafe_b64encode(blob[SALT_SIZE:])
    try:
        return Fernet(derive_key(password, salt)).decrypt(token)
    except (InvalidToken, ValueError):
        raise WrongPasswordError("Wrong password, or the hidden data is damaged.")
