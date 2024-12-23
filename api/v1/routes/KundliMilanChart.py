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
from schemas.KundliMilian import KundliMilanRequest

router = APIRouter()


def get_lat_lon(place_of_birth: str):
    geolocator = Nominatim(user_agent="kundli_app")
    location = geolocator.geocode(place_of_birth)
    if location:
        return location.latitude, location.longitude
    else:
        raise HTTPException(status_code=404, detail="Place of birth not found.")


@router.post("/guest/kundli_milan_chart")
async def generate_kundli_milan(
    request: KundliMilanRequest,  # KundliChartRequest should handle two sets of inputs
    current_user: str = Depends(get_current_user)
):
    try:
        # Parse input data
        male_data = request.male_birth_detail  # Assuming person1 is a nested object in the request
        female_data = request.female_birth_detail  # Assuming person2 is a nested object in the request

        name1, birth_date1, birth_time1, place_of_birth1 = (
            male_data.name,
            male_data.date_of_birth,
            male_data.time_of_birth,
            male_data.place_of_birth,
        )
        name2, birth_date2, birth_time2, place_of_birth2 = (
            female_data.name,
            female_data.date_of_birth,
            female_data.time_of_birth,
            female_data.place_of_birth,
        )

        # Get latitude and longitude for both persons
        latitude1, longitude1 = get_lat_lon(place_of_birth1)
        latitude2, longitude2 = get_lat_lon(place_of_birth2)

        # Extract date and time components for both persons
        year1, month1, day1 = birth_date1.year, birth_date1.month, birth_date1.day
        hour1, minute1 = birth_time1.hour, birth_time1.minute

        year2, month2, day2 = birth_date2.year, birth_date2.month, birth_date2.day
        hour2, minute2 = birth_time2.hour, birth_time2.minute

        # Create output directory
        output_directory = "/home/asus-tuf/Documents/Astromazic/Backend/astromagic/astromagic/"
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Create AstrologicalSubjects for both persons
        subject1 = AstrologicalSubject(
            name1,
            year1,
            month1,
            day1,
            hour1,
            minute1,
            lng=longitude1,
            lat=latitude1,
            tz_str="Asia/Kolkata",
            city=place_of_birth1,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )
        subject2 = AstrologicalSubject(
            name2,
            year2,
            month2,
            day2,
            hour2,
            minute2,
            lng=longitude2,
            lat=latitude2,
            tz_str="Asia/Kolkata",
            city=place_of_birth2,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )

        # Create the KerykeionChartSVG object for Synastry chart
        chart = KerykeionChartSVG(
            first_obj=subject1,
            second_obj=subject2,
            chart_type="Synastry",  # This is the chart type for compatibility
            new_output_directory=output_directory,
            theme="dark",  # You can customize the theme
        )

        # Generate the SVG content for the synastry chart
        svg_content = chart.makeSVG()
        svg_file_path = os.path.join(output_directory, f"{name1}_{name2}_synastry_chart.svg")

        # Generate reports for both persons
        report1 = Report(subject1)
        report2 = Report(subject2)
        report1.print_report()
        report2.print_report()

        # Check if SVG content was successfully generated
        if report1 and report2:
            return {
                "message": "Kundli Milan chart generated successfully.",
                "svg_path": output_directory
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate Kundli Milan chart.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Kundli Milan chart: {str(e)}")




# import os
# from kerykeion import AstrologicalSubject, KerykeionChartSVG,Report
# from pathlib import Path

# # Create the output directory if it doesn't exist
# output_directory = "/home/asus-tuf/Documents/Astromazic/Backend/astromagic/astromagic/"
# if not os.path.exists(output_directory):
#     os.makedirs(output_directory)

# # Create an AstrologicalSubject for Delhi, India
# subject1 = AstrologicalSubject(
#     "Manoj", 1989, 9, 10 , 7, 15, lng=77.1716954, lat=28.6273928, tz_str="Asia/Kolkata", city="Delhi",zodiac_type="Sidereal", sidereal_mode="LAHIRI"
# )
# subject2 = AstrologicalSubject(
#     "Rashmi", 1992, 11, 10, 6, 25, lng=77.1025, lat=28.7041, tz_str="Asia/Kolkata", city="Delhi",zodiac_type="Sidereal", sidereal_mode="LAHIRI"
# )

# # Create the KerykeionChartSVG object with ExternalNatal chart type
# chart = KerykeionChartSVG(
#     first_obj= subject1,  # First object (AstrologicalSubject)
#     chart_type= "Synastry",
#     second_obj=subject2, # Chart type
#     new_output_directory=output_directory,  # Ensure the output directory exists
#     theme="dark"  # Theme for the chart
# )



# # Generate the SVG content
# svg_content = chart.makeSVG()  # This generates the SVG content
# report = Report(subject1)
# report.print_report()



# if svg_content:
#     print("SVG content generated successfully.")
# else:
#     print("Failed to generate SVG content.")
