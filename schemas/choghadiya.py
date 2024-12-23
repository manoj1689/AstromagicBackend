from pydantic import BaseModel
from typing import List, Optional
from datetime import date ,time  # Import date from datetime module
# Request model for the API
class ChoghadiyaRequest(BaseModel):
    date: str # Format: YYYY-MM-DD
    place:str
    timezone: str