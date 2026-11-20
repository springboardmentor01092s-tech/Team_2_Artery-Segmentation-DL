"""TOTP enrollment and replay protection for production administrators."""

import base64
import hashlib
import hmac
import os
import secrets
import time

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from .models import AdministratorFactor


def required(role: str) -> bool:
    return role == "admin" and os.getenv("COROVISION_ENV") == "production"


def enrollment(db, user_id: str) -> AdministratorFactor:
    factor = db.get(AdministratorFactor, user_id)
    if factor is None:
        secret = base64.b32encode(secrets.token_bytes(20)).decode("ascii")
        try:
            with db.begin_nested():
                db.add(AdministratorFactor(user_id=user_id, secret=secret, last_counter=-1))
                db.flush()
        except IntegrityError:
            pass  # Another login already initialized this account's factor.
        factor = db.get(AdministratorFactor, user_id)
    return factor


def consume(db, factor: AdministratorFactor, code: str) -> bool:
    if len(code) != 6 or not code.isascii() or not code.isdecimal():
        return False
    current = int(time.time()) // 30
    key = base64.b32decode(factor.secret)
    for counter in (current, current - 1, current + 1):
        digest = hmac.digest(key, counter.to_bytes(8, "big"), hashlib.sha1)
        offset = digest[-1] & 15
        value = (int.from_bytes(digest[offset:offset + 4], "big") & 0x7FFFFFFF) % 1_000_000
        if hmac.compare_digest(f"{value:06d}", code):
            result = db.execute(update(AdministratorFactor).where(
                AdministratorFactor.user_id == factor.user_id,
                AdministratorFactor.last_counter < counter,
            ).values(last_counter=counter))
            return result.rowcount == 1
    return False
