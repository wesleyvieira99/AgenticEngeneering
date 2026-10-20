"""Local password authentication and short-lived signed bearer tokens.
This explicit demo identity provider is replaceable with an OIDC verifier.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import select, text

from services.api.db import Tenant, User


@dataclass(frozen=True)
class Principal:
    tenant: str
    user_id: str
    role: str


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    derived = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return f"{salt}${derived}"


def verify_password(password, stored):
    return hmac.compare_digest(password_hash(password, stored.split("$")[0]), stored)


def require_role(principal, allowed=("admin", "operator")):
    if principal.role not in allowed:
        raise HTTPException(403, "Ação não autorizada para este papel")


class Auth:
    def __init__(self, db):
        self.db = db
        self.secret = os.getenv("ATLAS_TOKEN_SECRET", "atlas-development-key-change-before-deploy").encode()
        password = os.getenv("ATLAS_DEMO_PASSWORD", "atlas-local-only")
        if os.getenv("ATLAS_ENV", "development") != "development":
            if password == "atlas-local-only" or len(self.secret) < 32 or self.secret.startswith(b"atlas-development"):
                raise RuntimeError("Production requires ATLAS_TOKEN_SECRET >=32 bytes and a non-default ATLAS_DEMO_PASSWORD")
        with db.transaction() as s:
            if db.engine.dialect.name == "postgresql":
                s.execute(text("SELECT pg_advisory_xact_lock(72641531)"))
            for tenant in ("acme", "orbit"):
                if not s.get(Tenant, tenant):
                    s.add(Tenant(id=tenant))
                    s.flush()
                    for name, role in (("admin", "admin"), ("viewer", "viewer"), ("operator", "operator")):
                        s.add(User(tenant=tenant, username=name, password_hash=password_hash(password), role=role))

    def issue(self, principal):
        claims = {"tenant": principal.tenant, "sub": principal.user_id, "role": principal.role,
                  "exp": int(time.time()) + 3600, "aud": "atlas-api", "nonce": secrets.token_hex(8)}
        payload = base64.urlsafe_b64encode(json.dumps(claims, separators=(",", ":")).encode()).decode().rstrip("=")
        signature = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
        return f"{payload}.{signature}"

    def verify(self, token):
        try:
            payload, signature = token.split(".")
            expected = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, signature):
                raise ValueError("signature")
            claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
            if claims["exp"] <= time.time() or claims["aud"] != "atlas-api":
                raise ValueError("expired")
            with self.db.sessions() as s:
                user = s.get(User, claims["sub"])
                if not user or user.tenant != claims["tenant"] or user.role != claims["role"]:
                    raise ValueError("revoked")
            return Principal(claims["tenant"], claims["sub"], claims["role"])
        except (ValueError, KeyError, TypeError):
            raise HTTPException(401, "Token inválido ou expirado") from None

    def login(self, tenant, username, password):
        with self.db.sessions() as s:
            user = s.scalar(select(User).where(User.tenant == tenant, User.username == username))
            # A fixed-cost hash is computed even for unknown identities.
            stored = user.password_hash if user else password_hash("invalid", "0" * 32)
            if not verify_password(password, stored) or not user:
                raise HTTPException(401, "Credenciais inválidas")
            return Principal(user.tenant, user.id, user.role)
