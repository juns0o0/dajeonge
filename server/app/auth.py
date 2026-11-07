"""기본 인증: 가족 코드 + 비밀번호 → 토큰. 보호자/태블릿 역할 구분, 가족별 접근 제한."""
import hashlib, hmac, os, secrets
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session as DbSession
from .db import get_db
from .models import Family, Session

SALT = os.getenv("PASSWORD_SALT", "dajeong-mvp-salt")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin-dev-token")


def hash_pw(pw: str) -> str:
    return hashlib.sha256((SALT + pw).encode()).hexdigest()


def verify_pw(pw: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_pw(pw), hashed)


def login(db: DbSession, code: str, password: str, role: str) -> tuple[str, Family]:
    fam = db.query(Family).filter(Family.code == code.strip().upper()).first()
    if not fam:
        raise HTTPException(401, "가족 코드가 없습니다.")
    hashed = fam.guardian_password if role == "guardian" else fam.tablet_password
    if not verify_pw(password, hashed):
        raise HTTPException(401, "비밀번호가 맞지 않습니다.")
    token = secrets.token_hex(24)
    db.add(Session(token=token, family_id=fam.id, role=role)); db.commit()
    return token, fam


class Auth:
    def __init__(self, session: Session, family: Family):
        self.session = session; self.family = family; self.role = session.role


def current(authorization: str = Header(default=""), db: DbSession = Depends(get_db)) -> Auth:
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "로그인이 필요합니다.")
    s = db.query(Session).filter(Session.token == token).first()
    if not s:
        raise HTTPException(401, "로그인이 만료됐습니다.")
    fam = db.get(Family, s.family_id)
    return Auth(s, fam)


def guardian_only(auth: Auth = Depends(current)) -> Auth:
    if auth.role != "guardian":
        raise HTTPException(403, "보호자만 할 수 있어요.")
    return auth


def admin_only(x_admin_token: str = Header(default="")):
    if not hmac.compare_digest(x_admin_token, ADMIN_TOKEN):
        raise HTTPException(403, "관리자 토큰이 필요합니다.")
    return True
