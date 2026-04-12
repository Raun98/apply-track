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
    """Encrypt a password. Raises ValueError if ENCRYPTION_KEY is not configured."""
    f = get_fernet()
    if not f:
        raise ValueError(
            "ENCRYPTION_KEY is not set. Refusing to store credentials unencrypted. "
            "Generate a key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
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
