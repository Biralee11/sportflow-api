from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from config import SECRET_KEY, JWT_ISSUER, JWT_AUDIENCE, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from database import get_db
from sqlalchemy.orm import Session
from models.models import UserModel

# deprecated="auto" lets us migrate to a stronger algorithm later: existing hashes
# keep verifying while any new hashes use the updated scheme, with no forced resets.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Re-hashes the attempt with the salt embedded in the stored hash, then compares.
    # Nothing is ever "unhashed" - hashing is one-way by design.
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    # Caller passes the identity claims (sub, role); this function attaches the
    # standard claims (expiry, issuer, audience) so they are enforced centrally.
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
    "exp": expire,
    "iss": JWT_ISSUER,
    "aud": JWT_AUDIENCE
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str):
    # Raises 401 rather than returning None so every protected endpoint is guarded
    # automatically, without each one having to re-check the result.
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    

# tokenUrl points to the login endpoint so FastAPI knows how to extract the
# bearer token from the Authorization header on protected requests.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    current_user_email = payload.get("sub")
    user = db.query(UserModel).filter(UserModel.email == current_user_email).first()
    # A token can be cryptographically valid but reference a deleted account.
    # 401 (not 403) because we cannot confirm the identity, not because access is denied.
    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user

def get_current_admin(current_user = Depends(get_current_user)):
    # Chains on get_current_user (identity) and adds the role check (authorisation).
    # 403 here means "we know who you are, you are just not allowed".
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user
