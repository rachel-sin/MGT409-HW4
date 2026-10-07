"""Password hashing for Campus Customs accounts.

Uses PBKDF2-HMAC-SHA256 with a random per-user salt, matching the format
already used by the seeded users table: "pbkdf2_sha256$<salt>$<hash>".
120,000 iterations follows OWASP's current minimum recommendation for
PBKDF2-SHA256. A memory-hard algorithm like bcrypt or argon2id would be a
stronger choice for a production app, but PBKDF2 keeps this compatible with
the existing seed data without extra dependencies.
"""

import hashlib
import hmac
import os

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000
SALT_BYTES = 16
KEY_LENGTH = 32


def hash_password(password: str) -> str:
    salt = os.urandom(SALT_BYTES).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), ITERATIONS, dklen=KEY_LENGTH
    )
    return f"{ALGORITHM}${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, hex_digest = stored_hash.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), ITERATIONS, dklen=KEY_LENGTH
    )
    return hmac.compare_digest(digest.hex(), hex_digest)
