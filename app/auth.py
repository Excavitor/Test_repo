from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models  # models will have the single source of Role enum
# from app import schemas # schemas will import Role from models
from app.database import SessionLocal
from typing import List, Optional

# It's crucial to load this from environment variables in production
SECRET_KEY = "shad1234"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2PasswordBearer tokenUrl should point to the relative URL of the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")  # Path relative to server root, matches POST /login in main.py

async def get_db():
    async with SessionLocal() as session:
        yield session

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[models.User]:
    result = await db.execute(select(models.User).where(models.User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        return None  # User not found
    if not verify_password(password, user.hashed_password):
        return None  # Invalid password
    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        # role: Optional[str] = payload.get("role") # Role can also be stored in token if needed for quick checks
        if username is None:
            raise credentials_exception
        # token_data = schemas.TokenData(username=username) # If using a Pydantic model for token payload
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(models.User).where(models.User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


# Type hint for allowed_roles should use models.Role
def has_role(allowed_roles: List[models.Role]):  # models.Role is the enum from models.py
    async def role_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user

    return role_checker


# Create role-based permission dependencies
# Ensure models.Role is the correct enum being used here
has_admin_permission = has_role([models.Role.ADMIN])
has_publisher_permission = has_role([models.Role.ADMIN, models.Role.PUBLISHER])  # Admin can also do publisher actions
has_customer_permission = has_role(
    [models.Role.ADMIN, models.Role.PUBLISHER, models.Role.CUSTOMER])  # Admin/Publisher can also do customer actions