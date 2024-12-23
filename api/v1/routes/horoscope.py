from fastapi import APIRouter, HTTPException
import swisseph as swe
from datetime import datetime, timedelta, date
from typing import Dict
import json

router = APIRouter()

# Load Nakshatra data from JSON file
try:
    with open("api/files/nakshatra_data.json", "r") as f:
        nakshatra_data: Dict[str, Dict] = json.load(f)
except FileNotFoundError:
    raise RuntimeError("The file 'nakshatra_data.json' is missing.")
except json.JSONDecodeError:
    raise RuntimeError("The file 'nakshatra_data.json' contains invalid JSON.")


def calculate_horoscope(date_of_birth: str, time_of_birth: str, place_of_birth: str) -> dict:
    print("kundli date", date_of_birth, "kundli time", time_of_birth, "kundli place", place_of_birth)
    try:
        # Parse datetime from input
        dt = datetime.strptime(f"{date_of_birth} {time_of_birth}", "%Y-%m-%d %H:%M:%S")
        print("dt", dt)

        # Convert to Julian date
        julian_day = swe.julday(
            dt.year,
            dt.month,
            dt.day,
            dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        )
        print("julian_day", julian_day)

        # Get latitude and longitude of the place of birth
        latitude, longitude = get_lat_lon(place_of_birth)
        print(f"Latitude: {latitude}, Longitude: {longitude}")
        
        # Set Sidereal Mode with Lahiri Ayanamsa
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        # Calculate Moon's position (returns a tuple)
        moon_position = swe.calc_ut(julian_day, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        moon_longitude = moon_position # The first element is the moon's sidereal longitude
        print("Moon Longitude:", moon_longitude)

        # Ensure moon_longitude is a valid number before passing to get_nakshatra
        if not isinstance(moon_longitude, (int, float)):
            raise ValueError(f"Invalid moon longitude: {moon_position}")

        # Function to get Nakshatra from degree
        def get_nakshatra(degree):
            nakshatras = [
                "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
                "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
                "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
                "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
                "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
            ]
            
            nakshatra_index = int((degree % 360) // 13.3333)
            nakshatra = nakshatras[nakshatra_index]

            # Calculate Pada (quarter)
            pada = int(((degree % 13.3333) // 3.3333) + 1)  # Padas are 1 to 4
            return nakshatra, pada

        # Get Moon's Nakshatra and Pada
        moon_nakshatra, moon_pada = get_nakshatra(moon_longitude)
        print(f"Moon Nakshatra: {moon_nakshatra}, Pada: {moon_pada}")

        # Retrieve Nakshatra prediction
        prediction = nakshatra_data.get(moon_nakshatra, {})
        if not prediction:
            raise ValueError(f"No prediction found for Nakshatra: {moon_nakshatra}")

        # Calculate houses (Ascendant, etc.)
        cusps, ascmc = swe.houses_ex(julian_day, latitude, longitude, b'P', swe.FLG_SIDEREAL)
        ascendant_position = ascmc[0]
        print("Ascendant (Equal Houses):", ascendant_position)

        # Get Ascendant's Zodiac Sign
        def get_zodiac_sign(degree):
            signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                     "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
            return signs[int(degree // 30) % 12]

        ascendant_sign = get_zodiac_sign(ascendant_position)
        print(f"Ascendant Sign: {ascendant_sign}")

        # Return the Kundli details
        return {
            "ascendant_sign": ascendant_sign,
            "moon_nakshatra": moon_nakshatra,
            "moon_pada": moon_pada,
            "nakshatra_description": prediction.get("description", "No description available."),
            "lucky_number": prediction.get("lucky_number", None),
            "lucky_color": prediction.get("lucky_color", "Unknown"),
            "advice": prediction.get("advice", "No advice available.")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating horoscope: {str(e)}")


# Example implementation of get_lat_lon
def get_lat_lon(place: str):
    # Mock implementation for testing purposes
    if place.lower() == "delhi":
        return 28.6139, 77.2090  # Coordinates for Delhi, India
    raise ValueError("Place not recognized. Provide valid latitude and longitude.")


# Helper to get yesterday, today, and tomorrow
def get_dates(dob: date):
    today = dob
    return {
        "yesterday": today - timedelta(days=1),
        "today": today,
        "tomorrow": today + timedelta(days=1)
    }


# FastAPI endpoint to handle POST request
@router.post("/horoscope")
async def horoscope_data():
    try:
        # Get yesterday, today, and tomorrow

        # Call the horoscope calculation function
        data = calculate_horoscope("1989-09-10", "01:45:00", "Delhi")
     
        # Return the response with horoscope data
        return {"horoscope_data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating horoscope data: {str(e)}")
