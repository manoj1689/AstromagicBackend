from typing import Dict,Any
from pydantic import BaseModel
from datetime import date ,time # Import date from datetime module

class PlanetPosition(BaseModel):
    degree: str
    zodiac_sign: str
    house: str
    nakshatra: str 
    pada: int


class KundliData(BaseModel):
    sun_sign: str
    moon_sign: str
    ascendant: str
    ascendant_pada: int  # Ensure this is a int
    ascendant_nakshatra: str
    varna:str
    yoni:str
    gana:str
    vashya:Any
    nadi:str
    planetary_positions: Dict[str, PlanetPosition]  # Nested structure for planets
    houses: Dict[str, str]  # String representation of house degrees
    nakshatra_load: Dict[str, str]# Nakshatra load for major planets, ensure it's a string

class KundliChartResponse(BaseModel):
    kundli: KundliData


class KundliResponse(BaseModel):
    kundli: KundliData
    insights: str

# Define the input model for the POST request
class KundliChartRequest(BaseModel):
    name: str
    date_of_birth: date # Format: YYYY-MM-DD
    time_of_birth: time  # Format: HH:MM (24-hour format)
    place_of_birth: str

# Request model for the API
class CurrentPlanetPositions(BaseModel):
    date: date  # Format: YYYY/MM/DD
    place: str
    time: time
   


class KundliChartResponse(BaseModel):
    current_planet_data: KundliData