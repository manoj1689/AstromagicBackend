from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from kerykeion import AstrologicalSubject, KerykeionChartSVG, Report
from pathlib import Path
import os
from geopy.geocoders import Nominatim
from db.session import get_db
from services.auth import get_current_user
from db.models.user import User
from schemas.Kundli import KundliChartRequest
router = APIRouter()

def get_lat_lon(place_of_birth: str):
    geolocator = Nominatim(user_agent="kundli_app")
    location = geolocator.geocode(place_of_birth)
    if location:
        return location.latitude, location.longitude
    else:
        raise HTTPException(status_code=404, detail="Place of birth not found.")




@router.post("/guest/kundli_chart")
async def generate_kundli_chart(
    request: KundliChartRequest,
    current_user: str = Depends(get_current_user),
):
    try:
        # Parse input data
        name = request.name
        birth_date = request.date_of_birth
        birth_time = request.time_of_birth
        place_of_birth = request.place_of_birth

        # Get latitude and longitude of the place of birth
        try:
            latitude, longitude = get_lat_lon(place_of_birth)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid place of birth: {place_of_birth}. Error: {str(e)}")

        # Extract date and time components
        year, month, day = birth_date.year, birth_date.month, birth_date.day
        hour, minute = birth_time.hour, birth_time.minute

        # Create output directory
        output_directory = "/home/asus-tuf/Documents/Astromazic/Backend/astromagic/astromagic/"
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Create an AstrologicalSubject
        subject = AstrologicalSubject(
            name,
            year,
            month,
            day,
            hour,
            minute,
            lng=longitude,
            lat=latitude,
            tz_str="Asia/Kolkata",
            city=place_of_birth,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )

        # Create the KerykeionChartSVG object
        chart = KerykeionChartSVG(
            subject,
            chart_type="ExternalNatal",
            new_output_directory=output_directory,
            theme="dark",
        )

        # Generate the SVG content
        svg_content = chart.makeSVG()
        svg_file_path = os.path.join(output_directory, f"{name}_kundli.svg")
   
        # Generate the astrological report
        report = Report(subject)
        report.print_report()

        # Return success response
        return {
            "message": "Kundli chart generated successfully.",
            "svg_path": output_directory,
        }
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Failed to generate Kundli image. Error: {str(e)}")



@router.get("/kundli_chart")
async def generate_kundli_chart(
    current_user: dict = Depends(get_current_user),  # Authenticated user
    db: Session = Depends(get_db)  # Database session
):
    
    
    # Fetch user details from the database
    user_id = current_user["id"]
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Extract user's birth details from the database
    if not all([user.date_of_birth, user.time_of_birth, user.place_of_birth]):
        raise HTTPException(status_code=400, detail="Incomplete user birth data.")

    birth_date = user.date_of_birth
    birth_time = user.time_of_birth
    # Get latitude and longitude of the place of birth
    latitude, longitude = get_lat_lon(user.place_of_birth)

    # Extract date and time components
    year, month, day = birth_date.year, birth_date.month, birth_date.day
    hour, minute = birth_time.hour, birth_time.minute

    # Create output directory
    output_directory = "/home/asus-tuf/Documents/Astromazic/Backend/astromagic/astromagic/"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Create an AstrologicalSubject
    subject = AstrologicalSubject(
        f"{user.name}",
        year,
        month,
        day,
        hour,
        minute,
        lng=longitude,
        lat=latitude,
        tz_str="Asia/Kolkata",
        city=user.place_of_birth or "Unknown",
        zodiac_type="Sidereal",
        sidereal_mode="LAHIRI",
    )

    # Create the KerykeionChartSVG object
    chart = KerykeionChartSVG(
        subject,
        chart_type="ExternalNatal",
        new_output_directory=output_directory,
        theme="dark"
    )

    # Generate the SVG content
    svg_content = chart.makeSVG()

    report = Report(subject)
    report.print_report()
    if report:
        return {"message": "Kundli image generated successfully.", "svg_path": output_directory}
    else:
        raise HTTPException(status_code=500, detail="Failed to generate kundli image.")


# import os
# import json
# from kerykeion import AstrologicalSubject, KerykeionChartSVG,Report
# from pathlib import Path

# # Create the output directory if it doesn't exist
# output_directory = "/home/asus-tuf/Documents/Astromazic/Backend/astromagic/astromagic/"
# if not os.path.exists(output_directory):
#     os.makedirs(output_directory)

# # Create an AstrologicalSubject for Delhi, India
# subject = AstrologicalSubject(
#     "Manoj Kaushik", 1989, 9, 10 , 7, 15, lng=77.1716954, lat=28.6273928, tz_str="Asia/Kolkata", city="Delhi",zodiac_type="Sidereal", sidereal_mode="LAHIRI"
# )

# # Create the KerykeionChartSVG object with ExternalNatal chart type
# chart = KerykeionChartSVG(
#     subject,  # First object (AstrologicalSubject)
#     chart_type="ExternalNatal",  # Chart type
#     new_output_directory=output_directory,  # Ensure the output directory exists
#     theme="dark"  # Theme for the chart
# )

# # Generate the SVG content
# svg_content = chart.makeSVG()  # This generates the SVG content

# report = Report(subject)
# report.print_report()

# ## Retrieving Moon Details
# # print(json.dumps(subject.moon, indent=2))

# if svg_content:
#     print("SVG content generated successfully.")
# else:
#     print("Failed to generate SVG content.")