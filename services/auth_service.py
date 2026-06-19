from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from config import SECRET_KEY, JWT_ISSUER, JWT_AUDIENCE, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from database import get_db
from sqlalchemy.orm import Session
from models.models import UserModel

# Configures bcrypt as the hashing algorithm for passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    # Encodes the provided data into a signed JWT token with an expiry time
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
    "exp": expire,
    "iss": JWT_ISSUER,
    "aud": JWT_AUDIENCE
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str):
    # Decodes and verifies the token. Returns the payload dict if valid, raises 401 if invalid or expired.
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
    

# Tells FastAPI where the login endpoint is so it can extract bearer tokens from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    current_user_email = payload.get("sub")
    user = db.query(UserModel).filter(UserModel.email == current_user_email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user

def get_current_admin(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user
