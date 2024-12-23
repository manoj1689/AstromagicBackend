
from pydantic import BaseModel, EmailStr
from typing import Optional,List
from datetime import date, time


class UserProfile(BaseModel):
    device_id: str
    name: Optional[str]
    email: Optional[EmailStr]
    age: Optional[int]
    date_of_birth: Optional[date]
    occupation: Optional[str]
    place_of_birth: Optional[str]
    time_of_birth: Optional[time]
    image_link: Optional[str]

    class Config:
        orm_mode = True
        from_attributes = True

class UserDetails(BaseModel):
    date_of_birth: Optional[str]
    time_of_birth: Optional[str]
    place_of_birth: Optional[str]

class ResponseModel(BaseModel):
    message: str
    data: UserProfile  # This expects a list of strings, not a User object.

