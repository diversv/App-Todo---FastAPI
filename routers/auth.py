from datetime import timedelta, datetime, timezone

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from decouple import config


router = APIRouter(
    prefix = "/auth",
    tags = ["auth"]
)

#for JWT -essential
SECRET_KEY = config('SECRET_KEY')
ALGORITHM = config('ALGORITHM')

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role:str

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

def authenticate_user(username: str, password: str, db ):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    print("Entered:", username, password)
    print("Stored hash:", user.hashed_password)
    print("Verified:", bcrypt_context.verify(password, user.hashed_password))
    return user

def create_access_token(username:str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail = 'Could not validate credentials')
        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail= 'Could not validate credentials')



@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency,
                      create_user_request_: CreateUserRequest):
    create_user_model = Users(
        email = create_user_request_.email,
        username = create_user_request_.username,
        first_name = create_user_request_.first_name,
        last_name = create_user_request_.last_name,
        role = create_user_request_.role,
        hashed_password = bcrypt_context.hash(create_user_request_.password),
        is_active = True
    )
    db.add(create_user_model)
    db.commit()

@router.post("/token", response_model=Token)
async def login_for_access(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                           db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail = "Could not validate user")
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=30))
    return {'access_token': token, 'token_type': 'bearer'}
