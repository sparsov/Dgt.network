#import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from typing import Union
from jose import jwt
from app.db  import TokenDatabase, get_token_db
from jose.exceptions import ExpiredSignatureError
from app.utils.logger import logger as LOGGER
# Секретный ключ для подписи JWT токенов
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

# Определение модели для данных токена
class TokenData(BaseModel):
    username: Optional[str] = None

# Создание экземпляра OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")
# Функция для генерации JWT токена
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# База данных пользователей (для примера)
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    }
}

def get_token_sub(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    return username

# Функция для получения пользователя по имени пользователя
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return user_dict


async def get_current_user(token: str = Depends(oauth2_scheme),token_db: TokenDatabase = Depends(get_token_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        username: str = get_token_sub(token)
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(token_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

