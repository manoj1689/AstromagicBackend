
from pydantic import BaseModel, EmailStr
from typing import Dict, Optional


class GoogleSignInRequest(BaseModel):
    device_id: str
    email: EmailStr
    name: str

class ResponseModel(BaseModel):
    message: str
    data: Optional[Dict] = None