from pydantic import BaseModel

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    full_name: str | None = None
    role: str = "staff"

class UserOut(UserBase):
    id: int
    full_name: str | None = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None
