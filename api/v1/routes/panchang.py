from fastapi import APIRouter, Depends, HTTPException
from geopy.geocoders import Nominatim
from schemas.panchang import PanchangRequest
import ephem
import swisseph as swe
from datetime import datetime
import pytz

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


swe.set_sid_mode(swe.SIDM_LAHIRI)  # Lahiri is commonly used in Vedic astrology
# Function to get the Sun's longitude
def get_sun_longitude(date):
    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute / 60 + date.second / 3600)
    sun_longitude = swe.calc_ut(jd, swe.SUN,swe.FLG_SIDEREAL)[0][0]
    return sun_longitude

# Function to get the Moon's ecliptic longitude using Swiss Ephemeris
def get_moon_longitude(date):
    
    # Convert datetime to Julian date
    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute / 60 + date.second / 3600)
    
    # Get the Moon's position (longitude in degrees)
    moon_longitude = swe.calc_ut(jd, swe.MOON,swe.FLG_SIDEREAL)[0][0]
    
    return moon_longitude

# List of 27 Yoga names
yoga_names = [
    "Vishkumbha", "Preeti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"
]

# Function to calculate Yoga
def get_yoga(sun_longitude, moon_longitude):
    # Calculate the sum of Sun's and Moon's longitude
    total_longitude = (sun_longitude + moon_longitude) % 360

    # Determine the Yoga index (each Yoga spans 13.3333°)
    yoga_index = int(total_longitude // 13.3333)

    # Return the Yoga name
    return yoga_names[yoga_index]


# Function to calculate Karan
def get_karan(tithi_number):
    karans = [
    # Shukla Paksha (Bright Fortnight)
    ["Kimstughna", "Bava"],  # Pratipada
    ["Baalav", "Kaulav"],    # Dwitiya
    ["Taitil", "Gar"],       # Tritiya
    ["Vanij", "Vishti"],     # Chaturthi
    ["Bava", "Baalav"],      # Panchami
    ["Kaulav", "Taitil"],    # Shashthi
    ["Gar", "Vanij"],        # Saptami
    ["Vishti", "Bava"],      # Ashtami
    ["Baalav", "Kaulav"],    # Navami
    ["Taitil", "Gar"],       # Dashami
    ["Vanij", "Vishti"],     # Ekadashi
    ["Bava", "Baalav"],      # Dwadashi
    ["Kaulav", "Taitil"],    # Trayodashi
    ["Gar", "Vanij"],        # Chaturdashi
    ["Vishti", "Bava"],      # Poornima

    # Krishna Paksha (Dark Fortnight)
    ["Baalav", "Kaulav"],    # Pratipada
    ["Taitil", "Gar"],       # Dwitiya
    ["Vanij", "Vishti"],     # Tritiya
    ["Bava", "Baalav"],      # Chaturthi
    ["Kaulav", "Taitil"],    # Panchami
    ["Gar", "Vanij"],        # Shashthi
    ["Vishti", "Bava"],      # Saptami
    ["Baalav", "Kaulav"],    # Ashtami
    ["Taitil", "Gar"],       # Navami
    ["Vanij", "Vishti"],     # Dashami
    ["Bava", "Baalav"],      # Ekadashi
    ["Kaulav", "Taitil"],    # Dwadashi
    ["Gar", "Vanij"],        # Trayodashi
    ["Vishti", "Shakuni"],   # Chaturdashi
    ["Chatushpada", "Naga"]  # Amavasya
]

    return karans[(tithi_number-1) % len(karans)]


def get_moon_longitude_nakshtra(date):
    # Convert datetime to Julian date
    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute / 60 + date.second / 3600)
    
    # Get the Moon's position (longitude in degrees)
    moon_longitude_nakshtara = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    
    return moon_longitude_nakshtara 



# Set up the observer's location (Delhi)
observer = ephem.Observer()
observer.lat = '28.6139'  # Latitude for Delhi
observer.lon = '77.2090'  # Longitude for Delhi

# Set the local time zone to IST (Indian Standard Time, UTC+5:30)
delhi_tz = pytz.timezone('Asia/Kolkata')

# Get today's date in UTC, then convert to IST
utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)  # Get current UTC time
ist_now = utc_now.astimezone(delhi_tz)  # Convert to IST (Indian Standard Time)

# Set the observer's date to the local IST time
observer.date = ist_now

# Get the Moon's and Sun's longitude using Swiss Ephemeris
moon_longitude = get_moon_longitude(ist_now)
print("moon longitute",moon_longitude)
sun_longitude = get_sun_longitude(ist_now)
print("sun logititude",sun_longitude)
moon_longitude_nakshtra = get_moon_longitude_nakshtra(ist_now)


# Calculate Yoga
yoga = get_yoga(sun_longitude, moon_longitude)

# Mapping of Nakshatra names
nakshatra_names = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purvaphalguni", "Uttaphalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purvashada", "Uttashada", "Shravana", "Dhanishta", "Shatabhisha",
    "Purvabhadrapada", "Uttabhadrapada", "Revati"
]

# Function to calculate the Nakshatra from the Moon's longitude
def get_nakshatra(moon_longitude_nakshtra):
    # Each Nakshatra spans 13° 20' (13.3333°)
    nakshatra_index = int(moon_longitude_nakshtra // 13.3333)  # Calculate which Nakshatra the Moon is in
    nakshatra_name = nakshatra_names[nakshatra_index]  # Get Nakshatra name
    return nakshatra_name

# Calculate sunrise and sunset times
sunrise = observer.next_rising(ephem.Sun())
sunset = observer.next_setting(ephem.Sun())


# Calculate the angular difference between the Moon and the Sun for Tithi
angle_difference = moon_longitude - sun_longitude
if angle_difference < 0:
    angle_difference += 360  # Ensure it's a positive angle

# Calculate the Tithi (each Tithi corresponds to 12°)
tithi = angle_difference / 12

# Adjust for the Tithi number (round to nearest whole number)
tithi_number = round(tithi)
# Ensure tithi_number stays within the bounds of 1 to 29
if tithi_number == 0:
    tithi_number = 1  # "Amavasya" corresponds to the last index, which is 29

print("tithi",tithi_number)


# Mapping of Tithi numbers to names
tithi_names = [
    "Pratipada", "Dvitiyā", "Tritiya", "Chaturthi", "Panchami", "Shasthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Purnima", "Pratipada", "Dvitiyā", "Tritiya",
    "Chaturthi", "Panchami", "Shasthi", "Saptami", "Ashtami", "Navami",
    "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
]

# Get the name of the Tithi
tithi_name = tithi_names[tithi_number-1]  # Tithi names are indexed from 0

karan = get_karan(tithi_number)

# Function to get zodiac sign from degree
def get_zodiac_sign(degree):
            signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                     "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
            return signs[int(degree // 30) % 12]
zodiac_sign=get_zodiac_sign(moon_longitude)

# Function to determine Paksha
def get_paksha(moon_longitude, sun_longitude):
    # Calculate angular difference between Moon and Sun
    angle_difference = (moon_longitude - sun_longitude) % 360

    # Determine Paksha
    if 0 <= angle_difference < 180:
        return "Shukla Paksha"  # Bright fortnight
    else:
        return "Krishna Paksha"  # Dark fortnight
paksha = get_paksha(moon_longitude, sun_longitude)

# Print results
print(f"Local Date and Time: {ist_now}")
print(f"Sunrise: {ephem.localtime(sunrise)}")
print(f"Sunset: {ephem.localtime(sunset)}")
print(f"Tithi for today: {tithi_name}")
print(f"Moon Zodiac Sign: {zodiac_sign}")
print(f"Nakshatra for today: {get_nakshatra(moon_longitude_nakshtra)}")
print(f"Yoga for today: {yoga}")
print(f"Karan for today: {karan}")
print(f"Today's Paksha is: {paksha}")


@router.post("/panchang")
async def vedic_details(request: PanchangRequest):
    try:
        # Get latitude and longitude of place
        lat, lon = get_lat_lon(request.place)

        # Parse date
        local_tz = pytz.timezone(request.timezone)
        parsed_date = datetime.strptime(request.date, '%Y-%m-%d').replace(tzinfo=local_tz)

        # Sun and Moon longitudes
        sun_longitude = get_sun_longitude(parsed_date)
        moon_longitude = get_moon_longitude(parsed_date)

        #Sunrise and Sunset
        SunRise=ephem.localtime(sunrise)
        SunSet=ephem.localtime(sunset)

        # Calculate Vedic details
        yoga = get_yoga(sun_longitude, moon_longitude)
        nakshatra = get_nakshatra(moon_longitude_nakshtra)
        tithi_number = round(((moon_longitude - sun_longitude) % 360) / 12) or 1
        tithi_name = tithi_names[tithi_number - 1]
        zodiac_sign = get_zodiac_sign(moon_longitude)
        paksha = get_paksha(moon_longitude, sun_longitude)

        return {
            "Sunrise":SunRise,
            "SunSet":SunSet,
            "date": request.date,
            "place": request.place,
            "location": {"latitude": lat, "longitude": lon},
            "tithi": tithi_name,
            "nakshatra": nakshatra,
            "karan":karan,
            "yoga": yoga,
            "zodiac_sign": zodiac_sign,
            "paksha": paksha
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
