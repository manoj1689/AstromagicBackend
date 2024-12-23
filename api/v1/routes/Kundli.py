from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from services.auth import get_current_user
from db.models.user import User
from schemas.Kundli import KundliResponse,KundliChartResponse,CurrentPlanetPositions
import openai
from geopy.geocoders import Nominatim
from datetime import datetime
import pytz
import swisseph as swe

router = APIRouter()
 # Set ayanamsa to Lahiri (Vedic)
# swe.set_sid_mode(swe.SIDM_LAHIRI)  # Use Lahiri Ayanamsa for Vedic astrology
# Function to get the latitude and longitude of the place of birth
def get_lat_lon(place_of_birth: str):
    geolocator = Nominatim(user_agent="kundli_app")
    location = geolocator.geocode(place_of_birth)
    if location:
        return location.latitude, location.longitude
    else:
        raise HTTPException(status_code=404, detail="Place of birth not found.")


def calculate_kundli(date_of_birth: str, time_of_birth: str, place_of_birth: str) -> dict:
    print("kundli date",date_of_birth,"kundli time",time_of_birth,"kundli place",place_of_birth)
    try:
       # Parse datetime from input
        dt = datetime.strptime(f"{date_of_birth} {time_of_birth}", "%Y-%m-%d %H:%M:%S")
        print("dt", dt)

        # Convert to Julian date
        julian_day = swe.julday(
            dt.year, 
            dt.month, 
            dt.day, 
            dt.hour + dt.minute / 60.0 + dt.second /3600.0
        )
        print("julian_day", julian_day)

        # Get latitude and longitude of the place of birth
        latitude, longitude = get_lat_lon(place_of_birth)
        print(latitude, longitude)
        
        # Set Sidereal Mode with Lahiri Ayanamsa (you can replace it with other ayanamsas)
        swe.set_sid_mode(swe.SIDM_LAHIRI)  # Lahiri is commonly used in Vedic astrology

        # Calculate houses using the sidereal zodiac
        cusps, ascmc = swe.houses_ex(julian_day,latitude, longitude , b'P', swe.FLG_SIDEREAL)
        ascendant_position = ascmc[0]
        print("Ascendant (Equal Houses):", ascendant_position)
                    
        # Function to get zodiac sign from degree
        def get_zodiac_sign(degree):
            signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                     "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
            return signs[int(degree // 30) % 12]

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
            
        def get_varna(rashi) -> str:
        # Ensure the input is a string
            if not isinstance(rashi, str):
                return "Invalid input: Rashi must be a string"
    
            varna_mapping = {
                    "Brahmin": ["Cancer", "Scorpio", "Pisces"],
                    "Kshatriya": ["Aries", "Leo", "Sagittarius"],
                    "Vaishya": ["Taurus", "Virgo", "Capricorn"],
                    "Shudra": ["Gemini", "Libra", "Aquarius"]
            }

            for varna, rashis in varna_mapping.items():
                if rashi.capitalize() in rashis:
                    return varna
            return "Invalid Rashi"
        #Nadi on the basis of nakshatra
        def get_nadi(nakshatra: str) -> str:
            nadi_mapping = {
                "Adi": ["Ashwini", "Ardra", "Punarvasu", "Uttara Phalguni", "Hasta", "Jyeshtha", "Mula", "Shatabhisha"],
                "Madhya": ["Bharani", "Mrigashira", "Pushya", "Purva Phalguni", "Chitra", "Anuradha", "Purvashada", "Dhanishta"],
                "Antya": ["Krittika", "Rohini", "Ashlesha", "Magha", "Swati", "Vishakha", "Uttarashada", "Revati"]
            }
            for nadi, nakshatras in nadi_mapping.items():
                if nakshatra.capitalize() in nakshatras:
                    return nadi
            return "Invalid Nakshatra"
        
      


        # Updated Yoni Mapping with only Animal Name
        yoni_mapping = {
            "Ashwini": "Horse",
            "Bharani": "Elephant",
            "Krittika": "Sheep",
            "Rohini": "Serpent",
            "Mrigashira": "Serpent",
            "Ardra": "Dog",
            "Punarvasu": "Cat",
            "Pushya": "Goat",
            "Ashlesha": "Cat",
            "Magha": "Rat",
            "Purva Phalguni": "Rat",
            "Uttara Phalguni": "Cow",
            "Hasta": "Buffalo",
            "Chitra": "Tiger",
            "Swati": "Buffalo",
            "Vishakha": "Tiger",
            "Anuradha": "Deer",
            "Jyeshtha": "Deer",
            "Mula": "Dog",
            "Purva Ashadha": "Monkey",
            "Uttara Ashadha": "Mongoose",
            "Shravana": "Monkey",
            "Dhanishta": "Lion",
            "Shatabhisha": "Horse",
            "Purva Bhadrapada": "Lion",
            "Uttara Bhadrapada": "Cow",
            "Revati": "Elephant",
            "Abhijit": "Mongoose",
        }
        def get_yoni(nakshatra: str):
            """Returns the Yoni Type and Yoni Gender for the given Nakshatra."""
            nakshatra = nakshatra.capitalize()  # Ensure the first letter is capitalized
            if nakshatra in yoni_mapping:
                return yoni_mapping[nakshatra]
            else:
                return "Invalid Nakshatra"
        
        
        gana_mapping = {
                "Deva": ["Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Swati", 
                        "Anuradha", "Shravana", "Revati"],
                "Manushya": ["Bharani", "Rohini", "Ardra", "Purva Phalguni", "Uttara Phalguni", 
                            "Purva Ashadha", "Uttara Ashadha", "Purva Bhadrapada", "Uttara Bhadrapada"],
                "Rakshasa": ["Krittika", "Ashlesha", "Magha", "Chitra", "Vishakha", "Jyeshtha", 
                            "Mula", "Dhanishta", "Shatabhisha"]
            }

        def get_gana(nakshatra):
            for gana, nakshatras in gana_mapping.items():
                if nakshatra.capitalize() in nakshatras:
                    return gana
            return "Invalid Nakshatra"

        

        vashya_mapping = {
            "Human": ["Gemini", "Virgo", "Libra","Low-Sagittarius", "Aquarius"],
            "Quadruped": ["Aries", "Taurus", "High-Sagittarius", "Low-Capricorn"],
            "Water": ["Cancer", "Pisces","High-Capricorn"],
            "Wild Animal": ["Leo"],
            "Insect": ["Scorpio"]
        }


        def get_vashya(rashi_name: str):
            # Normalize input to handle common typos
            if rashi_name in ["Sagittarius", "Capricorn"]:
                position = swe.calc_ut(julian_day, planet_id,swe.FLG_SIDEREAL)[0][0]
                planetary_positions["Moon"] = position

                remainder = position % 30  # Calculate the degree within the rashi
                if 0 <= remainder <= 15:
                    return f"Low-{rashi_name}"  # Low-Sagittarius or Low-Capricorn
                elif 15 < remainder <= 30:
                    return f"High-{rashi_name}"  # High-Sagittarius or High-Capricorn

            # Iterate over the vashya_mapping to find the corresponding vashya type
            for vashya_type, rashis in vashya_mapping.items():
                if rashi_name in rashis:
                    return vashya_type  # Return the vashya type (key)

            # If not found, return the rashi name itself
            return rashi_name
        

      # List of planets in the Swiss Ephemeris
        planets = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mars": swe.MARS,
            "Mercury": swe.MERCURY,
            "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS,
            "Saturn": swe.SATURN,
            "Rahu (North Node)": swe.MEAN_NODE,  # Using TRUE_NODE for Rahu
            "Ketu (South Node)": swe.MEAN_NODE,  # Ketu will be 180° from Rahu
            "Uranus": swe.URANUS,
            "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO,
        }

        # Dictionaries to store planetary positions and nakshatra information
        planetary_positions = {}
        nakshatra_info = {}

       

        # Calculate planetary positions
        for planet_name, planet_id in planets.items():
            if planet_name == "Ketu (South Node)":
                # Ketu is always 180° opposite Rahu
                rahu_position = swe.calc_ut(julian_day, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0] % 360
                position = (rahu_position + 180) % 360
            else:
                # For other planets (including Rahu), calculate normally
                position = swe.calc_ut(julian_day, planet_id, swe.FLG_SIDEREAL)[0][0] % 360

            # Store the calculated position
            planetary_positions[planet_name] = position

            # Get Nakshatra and Pada for the planet's position
            nakshatra, pada = get_nakshatra(position)
            nakshatra_info[planet_name] = {"nakshatra": nakshatra, "pada": pada}
        #print("planetry position of moon",planetary_positions["Moon"])

        # Calculate Sun and Moon signs
        sun_sign = get_zodiac_sign(planetary_positions["Sun"])
        moon_sign = get_zodiac_sign(planetary_positions["Moon"])
        print("moon sign",type(moon_sign))
        
        
          # Dynamically calculate houses
        house_names = [
            "1st House", "2nd House", "3rd House", "4th House", "5th House", "6th House", 
            "7th House", "8th House", "9th House", "10th House", "11th House", "12th House"
        ]
       
        houses = {}
        for i in range(12):
            houses[house_names[i]] = cusps[i]

        # Assign planets to houses
        planet_in_houses = {}
        for planet, degree in planetary_positions.items():
            for i in range(12):
                if cusps[i] <= degree < (cusps[i + 1] if i < 11 else cusps[0] + 360):
                    planet_in_houses[planet] = house_names[i]
                    break

            # Construct output data
            detailed_positions = {}
            for planet, degree in planetary_positions.items():
                nakshatra_data = nakshatra_info.get(planet, {})
                detailed_positions[planet] = {
                    "degree": f"{degree:.2f}°",
                    "zodiac_sign": get_zodiac_sign(degree),
                    "house": planet_in_houses.get(planet, "Unknown"),
                    "nakshatra": nakshatra_data.get("nakshatra", "Unknown"),
                    "pada": nakshatra_data.get("pada", "Unknown"),
                }
             # Print the planet and its degree
            print(f"Planet: {planet}, Degree: {degree:.2f}°")
            # print("detailed Position",detailed_positions)


        # Get Nakshatra and Pada for Ascendant (Lagna)
        ascendant_nakshatra, ascendant_pada = get_nakshatra(ascendant_position)
        print("ascendant_nakshatra", ascendant_nakshatra, "ascendant_pada", type(ascendant_pada))

        #Varna on the basis of moon_sign
        varna= get_varna(moon_sign)
        print("verna",varna)
        
        # nadi on the basis of nakshatra
        moon_nakshatra=get_nakshatra(planetary_positions["Moon"])
        print("moon nakshtra",moon_nakshatra)
        nadi=get_nadi(moon_nakshatra[0])
        print("nadi",nadi)

        #Yoni on the basis of nakshatra
        yoni=get_yoni(moon_nakshatra[0])
        print("yoni",yoni)
        
        #gana on the basis of nakshatra
        gana=get_gana(moon_nakshatra[0])
        print("gana",gana)

        #vashya on the basis of nakshatra
        vashya=get_vashya(moon_sign)
        print("vashya in kundli chart",vashya)

      
            # Add Nakshatra information to the output
        nakshatra_load = {
                        "Sun": f"{nakshatra_info.get('Sun', {}).get('nakshatra', 'Unknown')}-{nakshatra_info.get('Sun', {}).get('pada', 'Unknown')}",
                        "Moon": f"{nakshatra_info.get('Moon', {}).get('nakshatra', 'Unknown')}-{nakshatra_info.get('Moon', {}).get('pada', 'Unknown')}",
                        "Mars": f"{nakshatra_info.get('Mars', {}).get('nakshatra', 'Unknown')}-{nakshatra_info.get('Mars', {}).get('pada', 'Unknown')}",
                        "Mercury": f"{nakshatra_info.get('Mercury', {}).get('nakshatra', 'Unknown')}-{nakshatra_info.get('Mercury', {}).get('pada', 'Unknown')}",
                        "Jupiter": f"{nakshatra_info.get('Jupiter', {}).get('nakshatra', 'Unknown')}-{nakshatra_info.get('Jupiter', {}).get('pada', 'Unknown')}",
                        "Venus": f"{nakshatra_info.get('Venus', {}).get('nakshatra', 'Unknown')}-{nakshatra_info.get('Venus', {}).get('pada', 'Unknown')}",
                        "Saturn": f"{nakshatra_info.get('Saturn', {}).get('nakshatra', 'Unknown')}-{nakshatra_info.get('Saturn', {}).get('pada', 'Unknown')}",
                        "Rahu (North Node)": f"{nakshatra_info.get('Rahu (North Node)', {}).get('nakshatra', 'Unknown')}-{nakshatra_info.get('Rahu (North Node)', {}).get('pada', 'Unknown')}",
                        "Ketu (South Node)": f"{nakshatra_info.get('Ketu (South Node)', {}).get('nakshatra', 'Unknown')}-{nakshatra_info.get('Ketu (South Node)', {}).get('pada', 'Unknown')}",
                        "Uranus": f"{nakshatra_info.get('Uranus', {}).get('nakshatra', 'Unknown')}-{nakshatra_info.get('Uranus', {}).get('pada', 'Unknown')}",
                        "Neptune": f"{nakshatra_info.get('Neptune', {}).get('nakshatra', 'Unknown')}-{nakshatra_info.get('Neptune', {}).get('pada', 'Unknown')}",
                        "Pluto": f"{nakshatra_info.get('Pluto', {}).get('nakshatra', 'Unknown')}-{nakshatra_info.get('Pluto', {}).get('pada', 'Unknown')}"
                    }

    
        return {
            "ascendant": get_zodiac_sign(ascendant_position),
            "ascendant_nakshatra": ascendant_nakshatra,
            "ascendant_pada": ascendant_pada,
            "sun_sign": sun_sign,
            "moon_sign": moon_sign,
            "varna":varna,
            "yoni":yoni,
            "gana":gana,
            "vashya":vashya,
            "nadi":nadi,
            "houses": {name: f"{degree:.2f}°" for name, degree in zip(house_names, cusps)},
            "planetary_positions": detailed_positions,
            "nakshatra_load": nakshatra_load,  # Add Nakshatra load to the output
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kundli", response_model=KundliChartResponse)
async def get_kundli(
    current_user: str = Depends(get_current_user),  # Authenticated user
    db: Session = Depends(get_db)  # Database session
):
    # Fetch user details from the database
    user_id = current_user["id"]
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Generate Kundli chart data
    kundli_data = calculate_kundli(user.date_of_birth, user.time_of_birth, user.place_of_birth)
    return {"kundli": kundli_data}

@router.get("/kundli/ai-response", response_model=KundliResponse)
async def get_user_kundli(
    current_user: str = Depends(get_current_user),  # Authenticated user
    db: Session = Depends(get_db)  # Database session
):
    # Fetch user details from the database
    user_id = current_user["id"]
    user = db.query(User).filter(User.user_id == user_id).first()
   
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Generate Kundli data
    kundli_data = calculate_kundli(user.date_of_birth, user.time_of_birth, user.place_of_birth)
    print("Kundli Data:", kundli_data)
    
    prompt = f"""
    ### Astrological Profile:
    - **Sun Sign:** {kundli_data['sun_sign']}
    - **Moon Sign:** {kundli_data['moon_sign']}
    - **Ascendant (Lagna):** {kundli_data['ascendant']}
    - **Planetary Positions:**
    {"".join([f"  - {planet}: {details}" for planet, details in kundli_data['planetary_positions'].items()])}
    - **Houses:**
    {"".join([f"  - {house}: {degree}" for house, degree in kundli_data['houses'].items()])}

    ### Insights:
    Based on the Kundli data provided, analyze the following:
    1. Key characteristics of the user based on Sun, Moon, and Ascendant signs.
    2. Impact of planetary placements in their respective houses.
    3. Strengths, challenges, and major astrological influences in the user's life.

    ### Remedies:
    Recommend suitable remedies to balance any challenges observed, such as:
    - Gemstones
    - Mantras or chants
    - Lifestyle adjustments
    - Suggested rituals or practices

    ### Actionable Guidance:
    Provide clear next steps for the user to better align with their astrological energies.
    """


    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert astrologer providing detailed insights."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.7,  # Adjust for creativity level
        )
        bot_response = response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

    # Return Kundli data and insights
    return {
        "kundli": kundli_data,
        "insights": bot_response,
    }


@router.post("/current-planet-position", response_model=KundliChartResponse)
async def current_planet_data(request: CurrentPlanetPositions):
    try:
        # Parse input data
        date = request.date
        place = request.place
        time = request.time

      
        # Call the planet position calculation function
        current_planet_data = calculate_kundli(date, time, place)

        # Return the response
        return {"current_planet_data": current_planet_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating planet data: {str(e)}")