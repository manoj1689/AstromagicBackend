from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from services.auth import create_access_token
from db.session import get_db
from db.models.user import User
from schemas.login import GoogleSignInRequest, ResponseModel
from uuid import uuid4

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



# Google Sign-In endpoint
@router.post("/google_signin", response_model=ResponseModel)
async def google_signin(request: GoogleSignInRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.device_id == request.device_id).first()
    
    if existing_user:
        access_token = create_access_token(data={"sub": existing_user.user_id})
        return {"message": "Login successful", "data": {"access_token": access_token, "user_id": existing_user.user_id}}
    
    user_id = str(uuid4())
    new_user = User(
        user_id=user_id,
        device_id=request.device_id,
        name=request.name,
        email=request.email,
       
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.user_id})
    
    return {"message": "User registered and login successful", "data": {"access_token": access_token, "user_id": new_user.user_id}}
