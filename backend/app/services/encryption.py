from cryptography.fernet import Fernet, InvalidToken
from ..config import get_settings
import logging

logger = logging.getLogger(__name__)


def get_fernet() -> Fernet | None:
    key = get_settings().ENCRYPTION_KEY
    if not key:
        return None
    return Fernet(key.encode())


def encrypt_password(plaintext: str) -> str:
    """Encrypt a password. Returns ciphertext or plaintext if no key configured."""
    f = get_fernet()
    if not f:
        logger.warning("ENCRYPTION_KEY not set — storing password in plaintext")
        return plaintext
    return f.encrypt(plaintext.encode()).decode()


def decrypt_password(ciphertext: str) -> str:
    """Decrypt a password. Falls back to returning as-is if decryption fails (legacy plaintext)."""
    f = get_fernet()
    if not f:
        return ciphertext
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception):
        logger.warning("Password decryption failed — treating as plaintext (legacy record)")
        return ciphertext
