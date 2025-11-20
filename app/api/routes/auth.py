from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.database import db_dependency, get_db
from app.core.security import verify_password, create_access_token
from app.api.dependencies import get_active_user
from app.schemas.user import Token, UserOut, UserCreate
from app.services.user_services import get_user_by_username, create_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
    response: Response = None,
):
    if response is None:
        response = Response()
        
    user = get_user_by_username(db, form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password")

    token = create_access_token({"sub": user.username})
    
    # ✅ Lưu token vào cookie (30 days)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=30*24*60*60,  # 30 days
        httponly=False,  # Cho phép JavaScript truy cập
        samesite="lax"
    )
    
    return Token(access_token=token)

@router.get("/me", response_model=UserOut)
async def read_users_me(
    current_user: Annotated[User, Depends(get_active_user)],
):
    return current_user

@router.post("/register", response_model=UserOut)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    # Check username existed
    user_exist = get_user_by_username(db, user_in.username)
    if user_exist:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = create_user(
        db = db,
        username=user_in.username,
        password=user_in.password,
        full_name=user_in.full_name,
        role=user_in.role,
    )

    return new_user