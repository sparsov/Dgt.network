from pydantic import BaseModel


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    password : str
    #"scopes": request.scopes,
    token    : str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type  : str
