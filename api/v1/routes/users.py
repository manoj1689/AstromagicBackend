from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from db.models.user import User
from schemas.user import UserProfile, ResponseModel
from services.auth import get_current_user

router = APIRouter()

@router.put("/updateuser", response_model=ResponseModel)
async def update_user(
    request: UserProfile,  # Non-default argument
    current_user: str = Depends(get_current_user),  # Default argument
    db: Session = Depends(get_db)  # Default argument
):
    user_id = current_user["id"]
    
    # Fetch the existing user from the database
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Update user fields if provided in the request
    if request.name is not None:
        user.name = request.name
    if request.email is not None:
        user.email = request.email
    if request.age is not None:
        user.age = request.age
    if request.date_of_birth is not None:
        user.date_of_birth = request.date_of_birth
    if request.occupation is not None:
        user.occupation = request.occupation
    if request.place_of_birth is not None:
        user.place_of_birth = request.place_of_birth
    if request.time_of_birth is not None:
        user.time_of_birth = request.time_of_birth
    if request.image_link is not None:
        user.image_link = request.image_link
    if request.image_link is None:
        user.image_link = "default_image_link"

    # Save changes to the database
    db.commit()
    db.refresh(user)

    # Convert the updated user to a UserProfile Pydantic model
    updated_user_profile = UserProfile.from_orm(user)  # Correct usage of from_orm

    return {"message": "User information updated successfully", "data": updated_user_profile}

@router.get("/userinfo", response_model=ResponseModel)
async def get_user_info(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("current_user", current_user)

    user_id = current_user["id"]
    
    # Fetch the user from the database
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Convert the user to a UserProfile Pydantic model
    user_profile = UserProfile.from_orm(user)
    
    # Return a message and the user data wrapped in ResponseModel
    return {"message": "User information fetched successfully", "data": user_profile}
