from pydantic import BaseModel
from typing import List, Optional

# Request model for the API
class PanchangRequest(BaseModel):
    date: str  # Format: YYYY/MM/DD
    place:str
    timezone: str