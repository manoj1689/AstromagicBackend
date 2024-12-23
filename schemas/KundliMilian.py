from typing import Dict, Any
from pydantic import BaseModel
from datetime import date ,time  # Import date from datetime module

class BirthDateDetails(BaseModel):
    name:str
    date_of_birth: date  # This will validate the date in YYYY-MM-DD format
    time_of_birth: time
    place_of_birth: str

class KundliMilanRequest(BaseModel):
    male_birth_detail: BirthDateDetails
    female_birth_detail: BirthDateDetails

class KundliData(BaseModel):
    varna: str
    rashi: str
    rashi_position: Any  # This can be the degree or position
    nakshatra: str
    nadi: str

class KundliMilanResponse(BaseModel):
    male_data: KundliData  # Structured male data
    female_data: KundliData  # Structured female data
    compatibility_score: Dict[str,Any] # Ashtakoot Milan score

