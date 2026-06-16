import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if SECRET_KEY is None:
    raise RuntimeError("SECRET_KEY environment variable is not set")

JWT_ISSUER = os.getenv("JWT_ISSUER")
if JWT_ISSUER is None:
    raise RuntimeError("JWT_ISSUER environment variable is not set")

JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")
if JWT_AUDIENCE is None:
    raise RuntimeError("JWT_AUDIENCE environment variable is not set")

ALGORITHM = os.getenv("ALGORITHM")
if ALGORITHM is None:
    raise RuntimeError("ALGORITHM environment variable is not set")

ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
if ACCESS_TOKEN_EXPIRE_MINUTES is None:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES environment variable is not set")
ACCESS_TOKEN_EXPIRE_MINUTES = int(ACCESS_TOKEN_EXPIRE_MINUTES)
    
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL environment variable is not set")