from .base import *  # noqa: F403,F401

DATABASES["default"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": BASE_DIR / "backend" / "test.sqlite3",
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]