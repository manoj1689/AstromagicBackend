from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from services.auth import get_current_user
from datetime import datetime
from schemas.KundliMilian import KundliMilanResponse,KundliMilanRequest
from api.v1.routes.Kundli import calculate_kundli
import asyncio

router = APIRouter()

# Mapping for Nakshatra and Koota rules
varna_mapping = {
    "Brahmin": "Brahmin", 
    "Kshatriya": "Kshatriya", 
    "Vaishya": "Vaishya", 
    "Shudra": "Shudra"
}

vashya_rashi_sequence = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Low-Sagittarius","High-Sagittarius", "Low-Capricorn","High-Capricorn", "Aquarius", "Pisces"]

vashya_mapping = {
    "Human": ["Gemini", "Virgo", "Libra","Low-Sagittarius", "Aquarius"],
    "Quadruped": ["Aries", "Taurus", "High-Sagittarius", "Low-Capricorn"],
    "Water": ["Cancer", "Pisces","High-Capricorn"],
    "Wild Animal": ["Leo"],
    "Insect": ["Scorpio"]
}

vashya_scores = {
    ("Human", "Human"): 2,
    ("Human", "Quadruped"): 1,
    ("Human", "Water"): 0.5,
    ("Human", "Wild Animal"): 0,
    ("Human", "Insect"): 1,

    ("Quadruped", "Human"): 0,
    ("Quadruped", "Quadruped"): 2,
    ("Quadruped", "Water"): 1,
    ("Quadruped", "Wild Animal"): 0,
    ("Quadruped", "Insect"): 1,

    ("Water", "Human"): 0,
    ("Water", "Quadruped"): 1,
    ("Water", "Water"): 2,
    ("Water", "Wild Animal"): 0,
    ("Water", "Insect"): 1,
    
    ("Wild Animal", "Human"): 0.5,
    ("Wild Animal", "Quadruped"): 0.5,
    ("Wild Animal", "Water"): 1,
    ("Wild Animal", "Wild Animal"): 2,
    ("Wild Animal", "Insect"): 0,
   
    
    ("Insect", "Human"): 0,
    ("Insect", "Quadruped"): 1,
    ("Insect", "Water"): 1,
    ("Insect", "Wild Animal"): 0,
    ("Insect", "Insect"): 2
}

gana_mapping = {
    "Deva": ["Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Swati", "Anuradha", "Shravana", "Revati"],
    "Manushya": ["Bharani", "Rohini", "Ardra", "Purva Phalguni", "Uttara Phalguni", "Purva Ashadha", "Uttara Ashadha", "Purva Bhadrapada", "Uttara Bhadrapada"],
    "Rakshasa": ["Krittika", "Ashlesha", "Magha", "Chitra", "Vishakha", "Jyeshtha", "Mula", "Dhanishta", "Shatabhisha"]
}

gana_score={
    ("Deva","Deva"):6,
    ("Deva","Manushya"):6,
    ("Deva","Rakshasa"):1,

    ("Manushya","Deva"):5,
    ("Manushya","Manushya"):6,
    ("Manushya","Rakshasa"):0,

    ("Rakshasa","Deva"):1,
    ("Rakshasa","Manushya"):0,
    ("Rakshasa","Rakshasa"):6,


}

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
    "Revati": "Elephant"
}

yoni_score={
    
    ("Horse", "Horse"): 4,
    ("Horse", "Elephant"): 2,
    ("Horse", "Goat"): 2,
    ("Horse", "Serpent"): 3,
    ("Horse", "Dog"): 2,
    ("Horse", "Cat"): 2,
    ("Horse", "Rat"): 2,
    ("Horse", "Cow"): 1,
    ("Horse", "Buffalo"): 0,
    ("Horse", "Tiger"): 1,
    ("Horse", "Peacock"): 3,
    ("Horse", "Monkey"): 3,
    ("Horse", "Mongoose"): 2,
    ("Horse", "Lion"): 1,

    ("Elephant", "Horse"): 2,
    ("Elephant", "Elephant"): 4,
    ("Elephant", "Goat"): 3,
    ("Elephant", "Serpent"): 3,
    ("Elephant", "Dog"): 2,
    ("Elephant", "Cat"): 2,
    ("Elephant", "Rat"): 2,
    ("Elephant", "Cow"): 2,
    ("Elephant", "Buffalo"): 3,
    ("Elephant", "Tiger"): 1,
    ("Elephant", "Peacock"): 3,
    ("Elephant", "Monkey"): 3,
    ("Elephant", "Mongoose"): 2,
    ("Elephant", "Lion"): 0,

    ("Goat", "Horse"): 2,
    ("Goat", "Elephant"): 3,
    ("Goat", "Goat"): 4,
    ("Goat", "Serpent"): 2,
    ("Goat", "Dog"): 1,
    ("Goat", "Cat"): 2,
    ("Goat", "Rat"): 1,
    ("Goat", "Cow"): 3,
    ("Goat", "Buffalo"): 3,
    ("Goat", "Tiger"): 1,
    ("Goat", "Peacock"): 2,
    ("Goat", "Monkey"): 3,
    ("Goat", "Mongoose"): 0,
    ("Goat", "Lion"): 2 ,

    ("Serpent", "Horse"): 3,
    ("Serpent", "Elephant"): 3,
    ("Serpent", "Goat"): 2,
    ("Serpent", "Serpent"): 4,
    ("Serpent", "Dog"): 2,
    ("Serpent", "Cat"): 1,
    ("Serpent", "Rat"): 1,
    ("Serpent", "Cow"): 1,
    ("Serpent", "Buffalo"): 2,
    ("Serpent", "Tiger"): 2,
    ("Serpent", "Peacock"): 1,
    ("Serpent", "Monkey"): 2,
    ("Serpent", "Mongoose"): 2,
    ("Serpent", "Lion"): 1,

    ("Dog", "Horse"): 2,
    ("Dog", "Elephant"): 2,
    ("Dog", "Goat"): 1,
    ("Dog", "Serpent"): 2,
    ("Dog", "Dog"): 4,
    ("Dog", "Cat"): 2,
    ("Dog", "Rat"): 1,
    ("Dog", "Cow"): 2,
    ("Dog", "Buffalo"): 1,
    ("Dog", "Tiger"): 2,
    ("Dog", "Peacock"): 1,
    ("Dog", "Monkey"): 2,
    ("Dog", "Mongoose"): 1,
    ("Dog", "Lion"): 1,

    ("Cat", "Horse"): 2,
    ("Cat", "Elephant"): 2,
    ("Cat", "Goat"): 2,
    ("Cat", "Serpent"): 1,
    ("Cat", "Dog"): 2,
    ("Cat", "Cat"): 4,
    ("Cat", "Rat"): 0,
    ("Cat", "Cow"): 2,
    ("Cat", "Buffalo"): 2,
    ("Cat", "Tiger"): 1,
    ("Cat", "Peacock"): 3,
    ("Cat", "Monkey"): 3,
    ("Cat", "Mongoose"): 2,
    ("Cat", "Lion"): 1,

    ("Rat", "Horse"): 2,
    ("Rat", "Elephant"): 2,
    ("Rat", "Goat"): 1,
    ("Rat", "Serpent"): 1,
    ("Rat", "Dog"): 1,
    ("Rat", "Cat"): 0,
    ("Rat", "Rat"): 4,
    ("Rat", "Cow"): 2,
    ("Rat", "Buffalo"): 2,
    ("Rat", "Tiger"): 1,
    ("Rat", "Peacock"): 2,
    ("Rat", "Monkey"): 2,
    ("Rat", "Mongoose"): 1,
    ("Rat", "Lion"): 2,

    ("Cow", "Horse"): 1,
    ("Cow", "Elephant"): 2,
    ("Cow", "Goat"): 3,
    ("Cow", "Serpent"): 1,
    ("Cow", "Dog"): 2,
    ("Cow", "Cat"): 2,
    ("Cow", "Rat"): 2,
    ("Cow", "Cow"): 4,
    ("Cow", "Buffalo"): 3,
    ("Cow", "Tiger"): 0,
    ("Cow", "Peacock"): 3,
    ("Cow", "Monkey"): 2,
    ("Cow", "Mongoose"): 2,
    ("Cow", "Lion"): 1,

    
    ("Buffalo", "Horse"): 0,
    ("Buffalo", "Elephant"): 3,
    ("Buffalo", "Goat"): 3,
    ("Buffalo", "Serpent"): 2,
    ("Buffalo", "Dog"): 1,
    ("Buffalo", "Cat"): 2,
    ("Buffalo", "Rat"): 2,
    ("Buffalo", "Cow"): 3,
    ("Buffalo", "Buffalo"): 4,
    ("Buffalo", "Tiger"): 1,
    ("Buffalo", "Peacock"): 2,
    ("Buffalo", "Monkey"): 1,
    ("Buffalo", "Mongoose"): 2,
    ("Buffalo", "Lion"): 3,

    ("Tiger", "Horse"): 1,
    ("Tiger", "Elephant"): 1,
    ("Tiger", "Goat"): 1,
    ("Tiger", "Serpent"): 2,
    ("Tiger", "Dog"): 1,
    ("Tiger", "Cat"): 1,
    ("Tiger", "Rat"): 1,
    ("Tiger", "Cow"): 1,
    ("Tiger", "Buffalo"): 4,
    ("Tiger", "Tiger"): 1,
    ("Tiger", "Peacock"): 1,
    ("Tiger", "Monkey"): 1,
    ("Tiger", "Mongoose"): 2,
    ("Tiger", "Lion"): 1,

    ("Peacock", "Horse"): 3,
    ("Peacock", "Elephant"): 3,
    ("Peacock", "Goat"): 2,
    ("Peacock", "Serpent"): 1,
    ("Peacock", "Dog"): 0,
    ("Peacock", "Cat"): 1,
    ("Peacock", "Rat"): 1,
    ("Peacock", "Cow"): 3,
    ("Peacock", "Buffalo"): 2,
    ("Peacock", "Tiger"): 1,
    ("Peacock", "Peacock"): 4,
    ("Peacock", "Monkey"): 2,
    ("Peacock", "Mongoose"): 2,
    ("Peacock", "Lion"): 1,

    ("Monkey", "Horse"): 3,
    ("Monkey", "Elephant"): 3,
    ("Monkey", "Goat"): 3,
    ("Monkey", "Serpent"): 2,
    ("Monkey", "Dog"): 2,
    ("Monkey", "Cat"): 3,
    ("Monkey", "Rat"): 2,
    ("Monkey", "Cow"): 2,
    ("Monkey", "Buffalo"): 2,
    ("Monkey", "Tiger"): 1,
    ("Monkey", "Peacock"): 2,
    ("Monkey", "Monkey"): 4,
    ("Monkey", "Mongoose"): 3,
    ("Monkey", "Lion"): 2,

    ("Mongoose", "Horse"): 2,
    ("Mongoose", "Elephant"): 2,
    ("Mongoose", "Goat"): 0,
    ("Mongoose", "Serpent"): 2,
    ("Mongoose", "Dog"): 1,
    ("Mongoose", "Cat"): 2,
    ("Mongoose", "Rat"): 1,
    ("Mongoose", "Cow"): 2,
    ("Mongoose", "Buffalo"): 2,
    ("Mongoose", "Tiger"): 2,
    ("Mongoose", "Peacock"): 2,
    ("Mongoose", "Monkey"): 3,
    ("Mongoose", "Mongoose"): 4,
    ("Mongoose", "Lion"): 2,

    ("Lion", "Horse"): 1,
    ("Lion", "Elephant"): 0,
    ("Lion", "Goat"): 2,
    ("Lion", "Serpent"): 1,
    ("Lion", "Dog"): 1,
    ("Lion", "Cat"): 1,
    ("Lion", "Rat"): 2,
    ("Lion", "Cow"): 1,
    ("Lion", "Buffalo"): 3,
    ("Lion", "Tiger"): 1,
    ("Lion", "Peacock"): 1,
    ("Lion", "Monkey"): 2,
    ("Lion", "Mongoose"): 2,
    ("Lion", "Lion"): 4





}

rashi_sequence = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

rashi_lord = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

matri_score = {
    ("Sun", "Sun"): 5,
    ("Sun", "Moon"): 5,
    ("Sun", "Mars"): 5,
    ("Sun", "Mercury"): 4,
    ("Sun", "Jupiter"): 5,
    ("Sun", "Venus"): 0,
    ("Sun", "Saturn"): 0,
    ("Moon", "Sun"): 5,
    ("Moon", "Moon"): 5,
    ("Moon", "Mars"): 4,
    ("Moon", "Mercury"): 1,
    ("Moon", "Jupiter"): 4,
    ("Moon", "Venus"): 0.5,
    ("Moon", "Saturn"): 0.5,
    ("Mars", "Sun"): 5,
    ("Mars", "Moon"): 4,
    ("Mars", "Mars"): 5,
    ("Mars", "Mercury"): 0.5,
    ("Mars", "Jupiter"): 5,
    ("Mars", "Venus"): 3,
    ("Mars", "Saturn"): 0.5,
    ("Mercury", "Sun"): 4,
    ("Mercury", "Moon"): 1,
    ("Mercury", "Mars"): 0.5,
    ("Mercury", "Mercury"): 5,
    ("Mercury", "Jupiter"): 0.5,
    ("Mercury", "Venus"): 5,
    ("Mercury", "Saturn"): 4,
    ("Jupiter", "Sun"): 5,
    ("Jupiter", "Moon"): 4,
    ("Jupiter", "Mars"): 5,
    ("Jupiter", "Mercury"): 0.5,
    ("Jupiter", "Jupiter"): 5,
    ("Jupiter", "Venus"): 0.5,
    ("Jupiter", "Saturn"): 3,
    ("Venus", "Sun"): 0,
    ("Venus", "Moon"): 0.5,
    ("Venus", "Mars"): 3,
    ("Venus", "Mercury"): 5,
    ("Venus", "Jupiter"): 0.5,
    ("Venus", "Venus"): 5,
    ("Venus", "Saturn"): 5,
    ("Saturn", "Sun"): 0,
    ("Saturn", "Moon"): 0.5,
    ("Saturn", "Mars"): 0.5,
    ("Saturn", "Mercury"): 4,
    ("Saturn", "Jupiter"): 3,
    ("Saturn", "Venus"): 5,
    ("Saturn", "Saturn"): 5
}


bhakoot_score = {
    ("Aries", "Aries"): 7,
    ("Aries", "Taurus"): 0,
    ("Aries", "Gemini"): 7,
    ("Aries", "Cancer"): 7,
    ("Aries", "Leo"): 0,
    ("Aries", "Virgo"): 0,
    ("Aries", "Libra"): 7,
    ("Aries", "Scorpio"): 0,
    ("Aries", "Sagittarius"): 0,
    ("Aries", "Capricorn"): 7,
    ("Aries", "Aquarius"): 7,
    ("Aries", "Pisces"): 0,

    ("Taurus", "Aries"): 0,
    ("Taurus", "Taurus"): 7,
    ("Taurus", "Gemini"): 0,
    ("Taurus", "Cancer"): 7,
    ("Taurus", "Leo"): 7,
    ("Taurus", "Virgo"): 0,
    ("Taurus", "Libra"): 0,
    ("Taurus", "Scorpio"): 7,
    ("Taurus", "Sagittarius"): 0,
    ("Taurus", "Capricorn"): 0,
    ("Taurus", "Aquarius"): 7,
    ("Taurus", "Pisces"): 7,

    ("Gemini", "Aries"): 7,
    ("Gemini", "Taurus"): 0,
    ("Gemini", "Gemini"): 7,
    ("Gemini", "Cancer"): 0,
    ("Gemini", "Leo"): 7,
    ("Gemini", "Virgo"): 7,
    ("Gemini", "Libra"): 0,
    ("Gemini", "Scorpio"): 0,
    ("Gemini", "Sagittarius"): 7,
    ("Gemini", "Capricorn"): 0,
    ("Gemini", "Aquarius"): 0,
    ("Gemini", "Pisces"): 7,

    ("Cancer", "Aries"): 7,
    ("Cancer", "Taurus"): 7,
    ("Cancer", "Gemini"): 0,
    ("Cancer", "Cancer"): 7,
    ("Cancer", "Leo"): 0,
    ("Cancer", "Virgo"): 7,
    ("Cancer", "Libra"): 7,
    ("Cancer", "Scorpio"): 0,
    ("Cancer", "Sagittarius"): 0,
    ("Cancer", "Capricorn"): 7,
    ("Cancer", "Aquarius"): 0,
    ("Cancer", "Pisces"): 0,

    ("Leo", "Aries"): 0,
    ("Leo", "Taurus"): 7,
    ("Leo", "Gemini"): 7,
    ("Leo", "Cancer"): 0,
    ("Leo", "Leo"): 7,
    ("Leo", "Virgo"): 0,
    ("Leo", "Libra"): 7,
    ("Leo", "Scorpio"): 7,
    ("Leo", "Sagittarius"): 0,
    ("Leo", "Capricorn"): 0,
    ("Leo", "Aquarius"): 7,
    ("Leo", "Pisces"): 0,

    ("Virgo", "Aries"): 0,
    ("Virgo", "Taurus"): 0,
    ("Virgo", "Gemini"): 7,
    ("Virgo", "Cancer"): 7,
    ("Virgo", "Leo"): 0,
    ("Virgo", "Virgo"): 7,
    ("Virgo", "Libra"): 0,
    ("Virgo", "Scorpio"): 7,
    ("Virgo", "Sagittarius"): 7,
    ("Virgo", "Capricorn"): 0,
    ("Virgo", "Aquarius"): 0,
    ("Virgo", "Pisces"): 7,

    ("Libra", "Aries"): 7,
    ("Libra", "Taurus"): 0,
    ("Libra", "Gemini"): 0,
    ("Libra", "Cancer"): 7,
    ("Libra", "Leo"): 7,
    ("Libra", "Virgo"): 0,
    ("Libra", "Libra"): 7,
    ("Libra", "Scorpio"): 0,
    ("Libra", "Sagittarius"): 7,
    ("Libra", "Capricorn"): 7,
    ("Libra", "Aquarius"): 0,
    ("Libra", "Pisces"): 0,

    ("Scorpio", "Aries"): 0,
    ("Scorpio", "Taurus"): 7,
    ("Scorpio", "Gemini"): 0,
    ("Scorpio", "Cancer"): 0,
    ("Scorpio", "Leo"): 7,
    ("Scorpio", "Virgo"): 7,
    ("Scorpio", "Libra"): 0,
    ("Scorpio", "Scorpio"): 7,
    ("Scorpio", "Sagittarius"): 0,
    ("Scorpio", "Capricorn"): 7,
    ("Scorpio", "Aquarius"): 7,
    ("Scorpio", "Pisces"): 0,

    ("Sagittarius", "Aries"): 0,
    ("Sagittarius", "Taurus"): 0,
    ("Sagittarius", "Gemini"): 7,
    ("Sagittarius", "Cancer"): 0,
    ("Sagittarius", "Leo"): 0,
    ("Sagittarius", "Virgo"): 7,
    ("Sagittarius", "Libra"): 7,
    ("Sagittarius", "Scorpio"): 0,
    ("Sagittarius", "Sagittarius"): 7,
    ("Sagittarius", "Capricorn"): 0,
    ("Sagittarius", "Aquarius"): 7,
    ("Sagittarius", "Pisces"): 7,

    ("Capricorn", "Aries"): 7,
    ("Capricorn", "Taurus"): 0,
    ("Capricorn", "Gemini"): 0,
    ("Capricorn", "Cancer"): 7,
    ("Capricorn", "Leo"):  0,
    ("Capricorn", "Virgo"): 0,
    ("Capricorn", "Libra"): 7,
    ("Capricorn", "Scorpio"): 7,
    ("Capricorn", "Sagittarius"): 0,
    ("Capricorn", "Capricorn"): 7,
    ("Capricorn", "Aquarius"): 0,
    ("Capricorn", "Pisces"): 7,

    ("Aquarius", "Aries"): 7,
    ("Aquarius", "Taurus"): 7,
    ("Aquarius", "Gemini"): 0,
    ("Aquarius", "Cancer"): 0,
    ("Aquarius", "Leo"): 7,
    ("Aquarius", "Virgo"): 0,
    ("Aquarius", "Libra"): 0,
    ("Aquarius", "Scorpio"): 7,
    ("Aquarius", "Sagittarius"): 7,
    ("Aquarius", "Capricorn"): 0,
    ("Aquarius", "Aquarius"): 7,
    ("Aquarius", "Pisces"): 0,

    ("Pisces", "Aries"): 0,
    ("Pisces", "Taurus"): 7,
    ("Pisces", "Gemini"): 7,
    ("Pisces", "Cancer"): 0,
    ("Pisces", "Leo"): 0,
    ("Pisces", "Virgo"): 7,
    ("Pisces", "Libra"): 0,
    ("Pisces", "Scorpio"): 0,
    ("Pisces", "Sagittarius"): 7,
    ("Pisces", "Capricorn"): 7,
    ("Pisces", "Aquarius"): 0,
    ("Pisces", "Pisces"): 7
}



# Function for Varna Koota
def varna_koota(varna1, varna2):
    if varna1 == varna2:
        return 1.0
    elif varna1 == "Brahmin" or varna2 == "Shudra":
        return 0.0
    return 0.5

# Function to get the vashya category for two Rashis
def vashya_koota(rashi1, rashi1_degree, rashi2, rashi2_degree):
    # Define the function for degree evaluation
    def evaluate_degree(rashi, degree):
        # print("Degree in evaluation function:", degree)
        # Parse the degree by removing the "°" symbol and converting it to float
        degree = float(degree.replace("°", ""))
        
        # Compute the remainder to classify the degree
        remainder = degree % 30
        if 0 <= remainder <= 15:
            return f"Low-{rashi}"
        else:
            return f"High-{rashi}"
    
    # Convert rashi1 if it is Sagittarius or Capricorn
    if rashi1 in ["Sagittarius", "Capricorn"]:
        rashi1 = evaluate_degree(rashi1, rashi1_degree)
    
    # Convert rashi2 if it is Sagittarius or Capricorn
    if rashi2 in ["Sagittarius", "Capricorn"]:
        rashi2 = evaluate_degree(rashi2, rashi2_degree)
    
    # print("Rashi-1:", rashi1, "Rashi-2:", rashi2)

    # Now match the Rashis to their respective Vashya categories
    category1 = category2 = None
    for category, rashis in vashya_mapping.items():
        if rashi1 in rashis:
            category1 = category
        if rashi2 in rashis:
            category2 = category

    # Check if both Rashis match valid categories
    if not category1 or not category2:
        return "Invalid Rashi Input"
    
    # Get the score using the pairwise matrix
    pair = tuple(sorted([category1, category2]))  # Ensure the pair is sorted for consistency
    return vashya_scores.get(pair, 0)



# Function for Tara Koota
def tara_koota(nakshatra1, nakshatra2):
    nakshatra_index1 = list(yoni_mapping.keys()).index(nakshatra1)
    nakshatra_index2 = list(yoni_mapping.keys()).index(nakshatra2)
    diff = abs((nakshatra_index1 - nakshatra_index2)) % 9
    if diff in [3, 5, 7]:
        return 0.0
    elif diff in [1, 6, 8]:
        return 1.5
    return 3.0

# Function for Yoni Koota
def yoni_koota(nakshatra1, nakshatra2):
    yoni1 = yoni_mapping[nakshatra1]
    yoni2 = yoni_mapping[nakshatra2]
    # Validate if both Ganas are valid
    if yoni1 is None or yoni2 is None:
        return "Invalid Nakshatra Input"
    
    # Get the score using the yoni Score Matrix
    pair = (yoni1, yoni2)  
    return yoni_score.get(pair, 0)
   

def find_gana(nakshatra):
    """Find the Gana type for a given nakshatra."""
    for gana, nakshatras in gana_mapping.items():
        if nakshatra in nakshatras:
            return gana
    return None
# Function for Gana Koota
def gana_koota(nakshatra1, nakshatra2):
    # Find Ganas for the given Nakshatras
    gana1 = find_gana(nakshatra1)
    
    gana2 = find_gana(nakshatra2)
    
    # Validate if both Ganas are valid
    if gana1 is None or gana2 is None:
        return "Invalid Nakshatra Input"
    
    # Get the score using the Gana Score Matrix
    pair = (gana1, gana2)  # No need to sort since `gana_score` already accounts for all combinations
    return gana_score.get(pair, 0)



# Function to calculate Matri Score based on Rashi Lords
def maitri_koota(rashi1, rashi2):

    # Find lords of the two Rashis
    lord1 = rashi_lord[rashi1]
    lord2 = rashi_lord[rashi2]
    pair = (lord1, lord2)
    return matri_score.get(pair, 0)  # Default to 0 if not found
   


# Function for Bhakoot Koota score based on zodiac sign pair
def bhakoot_koota(rashi1, rashi2):
    # Check if the pair exists in both (rashi1, rashi2) and (rashi2, rashi1) as pairs are unordered
    score = bhakoot_score.get((rashi1, rashi2)) or bhakoot_score.get((rashi2, rashi1))
    
    if score is None:
        return "Invalid rashi pair"
    
    return score

# Function for Nadi Koota
def nadi_koota(nadi1, nadi2):
    if nadi1 == nadi2:
        return 0.0
    return 8.0

def Kundli_Milan(male_data, female_data):
    # Step 4: Perform Ashtakoot Milan Compatibility Calculation
    print("Ashtakoot Milan Compatibility Scores:\n")
    
    # Individual scores calculation
    varna_score = varna_koota(male_data['varna'], female_data['varna'])
    print(f"1. Varna Koota: {varna_score}/1.0")
    
    vashya_score = vashya_koota(male_data["rashi"],male_data['rashi_position'],female_data["rashi"], female_data['rashi_position'])
    print(f"2. Vashya Koota: {vashya_score}/2.0")
    
    tara_score = tara_koota(male_data['nakshatra'], female_data['nakshatra'])
    print(f"3. Tara Koota: {tara_score}/3.0")
    
    yoni_score = yoni_koota(male_data['nakshatra'], female_data['nakshatra'])
    print(f"4. Yoni Koota: {yoni_score}/4.0")

    matri_score = maitri_koota(male_data['rashi'], female_data['rashi'])
    print(f"5. Maitri Koota: {matri_score}/5.0")
    
    gana_score = gana_koota(male_data['nakshatra'], female_data['nakshatra'])
    print(f"6. Gana Koota: {gana_score}/6.0")
    
    bhakoot_score = bhakoot_koota(male_data['rashi'], female_data['rashi'])
    print(f"7. Bhakoot Koota: {bhakoot_score}/7.0")
    
    nadi_score = nadi_koota(male_data['nadi'], female_data['nadi'])
    print(f"8. Nadi Koota: {nadi_score}/8.0")
    
    # Total score calculation
    total_score = varna_score + vashya_score + tara_score + yoni_score + matri_score + gana_score + bhakoot_score + nadi_score
    print("\n----------------------------------")
    print(f"Total Ashtakoot Score: {round(total_score, 2)}/36")

    # Return all relevant data
    return {
        "compatibility_scores": {
            "varna_score": varna_score,
            "vashya_score": vashya_score,
            "tara_score": tara_score,
            "yoni_score": yoni_score,
            "matri_score": matri_score,
            "gana_score": gana_score,
            "bhakoot_score": bhakoot_score,
            "nadi_score": nadi_score,
            "total_score": round(total_score, 2)
        }
    }



@router.post("/guest/kundli/milan", response_model=KundliMilanResponse)
async def kundli_milan(request: KundliMilanRequest):
    try:
        # Extract data from the request
        male_birth_detail = request.male_birth_detail
        # print(":kundli milian", male_birth_detail.date_of_birth)
        # print(":kundli milian", male_birth_detail.time_of_birth)
        # print(":kundli milian", male_birth_detail.place_of_birth)
        
        female_birth_detail = request.female_birth_detail

        # Calculate Kundlis
        male_kundli = calculate_kundli(
            date_of_birth=male_birth_detail.date_of_birth,  # Use male_birth_detail for male Kundli
            time_of_birth=male_birth_detail.time_of_birth,
            place_of_birth=male_birth_detail.place_of_birth
        )
        
        female_kundli = calculate_kundli(
            date_of_birth=female_birth_detail.date_of_birth,  # Use female_birth_detail for female Kundli
            time_of_birth=female_birth_detail.time_of_birth,
            place_of_birth=female_birth_detail.place_of_birth
        )

        # Extract Male Data for Kundli Milan
        male_data = {
            "varna": male_kundli["varna"],
            "rashi": male_kundli["moon_sign"],
            "rashi_position": male_kundli["planetary_positions"]["Moon"]["degree"],  # Use Moon's degree as rashi position
            "nakshatra": male_kundli["planetary_positions"]["Moon"]["nakshatra"],  # Moon's nakshatra
            "nadi": male_kundli["nadi"]
        }

        # Extract Female Data for Kundli Milan
        female_data = {
            "varna": female_kundli["varna"],
            "rashi": female_kundli["moon_sign"],
            "rashi_position": female_kundli["planetary_positions"]["Moon"]["degree"] ,  # Use Moon's degree as rashi position
            "nakshatra": female_kundli["planetary_positions"]["Moon"]["nakshatra"],  # Moon's nakshatra
            "nadi": female_kundli["nadi"]
        }

        print("male Data", male_data)
        print("female Data", female_data)

        # Calculate compatibility score (ensure Kundli_Milan is awaited if it's async)
        compatibility_score =  Kundli_Milan(male_data, female_data)  # Ensure Kundli_Milan is async or just call it directly if not

        # Return response
        return KundliMilanResponse(
            male_data=male_data,
            female_data=female_data,
            compatibility_score=compatibility_score
        )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



# def Kundli_Milan(male_birth_date, female_birth_date):
#     # Step 1: Calculate Kundlis for both individuals
#     male_kundli = calculate_kundli(male_birth_date["date"], male_birth_date["time"], male_birth_date["location"])
#     female_kundli = calculate_kundli(female_birth_date["date"], female_birth_date["time"], female_birth_date["location"])

#     # Step 2: Extract Male Data for Kundli Milan
#     male_data = {
#         "varna": male_kundli["varna"],
#         "rashi": male_kundli["moon_sign"],
#         "rashi_position": male_kundli["planetary_positions"]["Moon"]["zodiac_sign"],
#         "nakshatra": male_kundli["nakshatra_load"]["Moon"],
#         "nadi": male_kundli["nadi"]
#     }

#     # Step 3: Extract Female Data for Kundli Milan
#     female_data = {
#         "varna": female_kundli["varna"],
#         "rashi": female_kundli["moon_sign"],
#         "rashi_position": female_kundli["planetary_positions"]["Moon"]["zodiac_sign"],
#         "nakshatra": female_kundli["nakshatra_load"]["Moon"],
#         "nadi": female_kundli["nadi"]
#     }

#     # Step 4: Perform Ashtakoot Milan Compatibility Calculation
#     print("Ashtakoot Milan Compatibility Scores:\n")
#     varna_score = varna_koota(male_data['varna'], female_data['varna'])
#     print(f"1. Varna Koota: {varna_score}/1.0")
    
#     vashya_score = vashya_koota(male_data['rashi_position'], female_data['rashi_position'])
#     print(f"2. Vashya Koota: {vashya_score}/2.0")
    
#     tara_score = tara_koota(male_data['nakshatra'], female_data['nakshatra'])
#     print(f"3. Tara Koota: {tara_score}/3.0")
    
#     yoni_score = yoni_koota(male_data['nakshatra'], female_data['nakshatra'])
#     print(f"4. Yoni Koota: {yoni_score}/4.0")

#     matri_score = maitri_koota(male_data['rashi'], female_data['rashi'])
#     print(f"5. Maitri Koota: {matri_score}/5.0")
    
#     gana_score = gana_koota(male_data['nakshatra'], female_data['nakshatra'])
#     print(f"6. Gana Koota: {gana_score}/6.0")
    
#     bhakoot_score = bhakoot_koota(male_data['rashi'], female_data['rashi'])
#     print(f"7. Bhakoot Koota: {bhakoot_score}/7.0")
    
#     nadi_score = nadi_koota(male_data['nadi'], female_data['nadi'])
#     print(f"8. Nadi Koota: {nadi_score}/8.0")
    
#     # Total score calculation
#     total_score = varna_score + vashya_score + tara_score + yoni_score + matri_score + gana_score + bhakoot_score + nadi_score
#     print("\n----------------------------------")
#     print(f"Total Ashtakoot Score: {round(total_score, 2)}/36")

#     return {
#         "male_data": male_data,
#         "female_data": female_data,
#         "ashtakoot_score": round(total_score, 2)
#     }

