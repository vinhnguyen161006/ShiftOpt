import hashlib
import hmac
import secrets

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32
SALT_BYTES = 16
SCHEME = "scrypt"


def hash_password(password: str) -> str:
    """Hash with scrypt from the standard library (RFC 7914).

    Stored as scheme$n$r$p$salt_hex$digest_hex so parameters can change without breaking old hashes.
    """
    salt = secrets.token_bytes(SALT_BYTES)
    digest = _derive(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    return f"{SCHEME}${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) != 6 or parts[0] != SCHEME:
        return False
    n, r, p = (int(value) for value in parts[1:4])
    salt = bytes.fromhex(parts[4])
    expected = bytes.fromhex(parts[5])
    return hmac.compare_digest(_derive(password, salt, n, r, p, len(expected)), expected)


def _derive(password: str, salt: bytes, n: int, r: int, p: int, dklen: int = SCRYPT_DKLEN) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=dklen, maxmem=64 * 1024 * 1024
    )
