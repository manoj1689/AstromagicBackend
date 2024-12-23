from fastapi import FastAPI, HTTPException,APIRouter
from schemas.choghadiya import ChoghadiyaRequest
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import ephem
import pytz

router = APIRouter()

# Function to get the latitude and longitude of the place of birth
def get_lat_lon(place_of_birth: str):
    geolocator = Nominatim(user_agent="kundli_app")
    location = geolocator.geocode(place_of_birth)
    if location:
        return location.latitude, location.longitude
    else:
        raise HTTPException(status_code=404, detail="Place of birth not found.")


# Function to calculate sunrise and sunset
def calculate_sunrise_sunset(date, lat, lon, timezone):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = date

    sun = ephem.Sun()
    sunrise_utc = observer.next_rising(sun).datetime()
    sunset_utc = observer.next_setting(sun).datetime()

    local_tz = pytz.timezone(timezone)
    sunrise_local = pytz.utc.localize(sunrise_utc).astimezone(local_tz)
    sunset_local = pytz.utc.localize(sunset_utc).astimezone(local_tz)

    return sunrise_local, sunset_local

# Choghadiya sequences
def get_choghadiya_sequences():
    return {
        "Sunday": {
            "Day": ["Udveg", "Chal", "Labh", "Labh", "Kaal", "Shubh", "Rog", "Udveg"],
            "Night": ["Shubh", "Amrit", "Chal", "Rog", "Kaal", "Labh", "Udveg", "Shubh"]
        },
        "Monday": {
            "Day": ["Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Chal", "Labh", "Amrit"],
            "Night": ["Chal", "Rog", "Kaal", "Labh", "Udveg", "Amrit", "Shubh", "Chal"]
        },
        "Tuesday": {
            "Day": ["Rog", "Udveg", "Chal", "Labh", "Amrit", "Kaal", "Shubh", "Rog"],
            "Night": ["Kaal", "Labh", "Udveg", "Amrit", "Rog", "Chal", "Kaal", "Labh"]
        },
        "Wednesday": {
            "Day": ["Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Chal", "Labh"],
            "Night": ["Udveg", "Shubh", "Amrit", "Rog", "Kaal", "Labh", "Shubh", "Udveg"]
        },
        "Thursday": {
            "Day": ["Shubh", "Rog", "Udveg", "Chal", "Labh", "Amrit", "Kaal", "Shubh"],
            "Night": ["Amrit", "Chal", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit"]
        },
        "Friday": {
            "Day": ["Chal", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Chal"],
            "Night": ["Rog", "Kaal", "Labh", "Shubh", "Amrit", "Rog", "Kaal", "Labh"]
        },
        "Saturday": {
            "Day": ["Kaal", "Shubh", "Rog", "Udveg", "Chal", "Labh", "Amrit", "Kaal"],
            "Night": ["Labh", "Udveg", "Shubh", "Amrit", "Chal", "Rog", "Kaal", "Labh"]
        },
    }

# Generate Choghadiya periods
def get_choghadiya_periods(sunrise, sunset, weekday):
    day_duration = sunset - sunrise
    night_duration = timedelta(hours=24) - day_duration

    day_muhurat = day_duration / 8
    night_muhurat = night_duration / 8

    sequences = get_choghadiya_sequences()
    day_sequence = sequences[weekday]["Day"]
    night_sequence = sequences[weekday]["Night"]

    periods = {
        "Day Choghadiya": [],
        "Night Choghadiya": []
    }

    # Generate day Choghadiya periods
    for i, name in enumerate(day_sequence):
        start_time = sunrise + (i * day_muhurat)
        end_time = start_time + day_muhurat
        periods["Day Choghadiya"].append({
            "name": name,
            "time_slot": f"{start_time.strftime('%I:%M %p')} to {end_time.strftime('%I:%M %p')}"
        })

    # Generate night Choghadiya periods
    for i, name in enumerate(night_sequence):
        start_time = sunset + (i * night_muhurat)
        end_time = start_time + night_muhurat
        periods["Night Choghadiya"].append({
            "name": name,
            "time_slot": f"{start_time.strftime('%I:%M %p')} to {end_time.strftime('%I:%M %p')}"
        })

    return periods

@router.post("/choghadiya/")
def calculate_choghadiya(request: ChoghadiyaRequest):
    try:
        # Parse the provided date
        parsed_date = datetime.strptime(request.date, "%Y-%m-%d")
         # Get latitude and longitude of the place of birth
        latitude, longitude = get_lat_lon(request.place)
        # Calculate sunrise and sunset
        sunrise, sunset = calculate_sunrise_sunset(parsed_date,latitude,longitude, request.timezone)

        # Determine weekday
        weekday = parsed_date.strftime("%A")

        # Calculate Choghadiya periods
        periods = get_choghadiya_periods(sunrise, sunset, weekday)

        return {
            "Date": parsed_date.strftime("%Y-%m-%d"),
            "Sunrise": sunrise.strftime("%I:%M %p"),
            "Sunset": sunset.strftime("%I:%M %p"),
            "Choghadiya": periods
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error calculating Choghadiya: {str(e)}")
