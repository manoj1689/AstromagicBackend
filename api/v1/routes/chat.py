from fastapi import FastAPI, HTTPException, APIRouter, Depends, File, UploadFile,status
from datetime import datetime
from typing import List, Optional
from services.chat import SCENARIOS
from schemas.chat import ChatRequest, ChatResponse, Scenario
from services.chat import validate_user_details ,get_chat_history, convert_chat_history_to_dict, truncate_chat_history, summarize_history, calculate_tokens, save_chat_history
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from db.session import get_db
from services.auth import get_current_user
import openai 
import os
from db.models.chat import ChatHistory
from db.models.user import User
from api.v1.routes.Kundli import calculate_kundli

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("Missing OpenAI API key. Ensure it's set in the .env file.")



router = APIRouter()

# Constants
MAX_HISTORY_TOKENS = 1000
MODEL = "gpt-4"

@router.get("/scenarios", response_model=List[Scenario])
async def get_scenarios():
    """Fetch all scenarios."""
    return SCENARIOS



@router.post("/astrology/chat", response_model=ChatResponse)
async def astrology_chat(request: ChatRequest, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["id"]
     # Fetch user details from the database
   
    user = db.query(User).filter(User.user_id == user_id).first()
     # Generate Kundli chart data
    kundli_data = calculate_kundli(user.date_of_birth, user.time_of_birth, user.place_of_birth)
    # Get the current UTC date and time
    current_utc_time = datetime.utcnow()

    # Extract the current date and time separately if needed
    current_date = current_utc_time.date()  # Get the date (YYYY-MM-DD)
    current_time = current_utc_time.time()  # Get the time (HH:MM:SS)

    # Print the current UTC time
    print("current_utc_time:", current_utc_time)

    # Now, pass the current date, time, and user place of birth to the function
    current_data = calculate_kundli(current_date, current_time, user.place_of_birth)
    print ("current Data",current_data)
    existing_chat = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).all()

    # Prepare the context based on the existing history
    if existing_chat:
        chat_history_context = [
            {
                "user": chat.user,
                "bot": chat.bot
            } for chat in existing_chat
        ]
        print("--456--", chat_history_context)

    else:
        chat_history_context = []
    # Find the scenario
    scenario = next((s for s in SCENARIOS if s["id"] == request.scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found.")

 
    # Summarize or truncate chat history if required
    history_tokens = calculate_tokens(chat_history_context, model=MODEL)
    if history_tokens > MAX_HISTORY_TOKENS:
        truncated_history = truncate_chat_history(chat_history_context, MAX_HISTORY_TOKENS)
        # summarized_context = summarize_history(truncated_history)
        # print("-----123-----", summarized_context)
    else:
        summarized_context = chat_history_context
        
    prompt = f"""
    ### Scenario
    **Title:** {scenario['title']}  
    **Description:** {scenario['description']}  
    **Astrological Focus:** {scenario['astrological_focus']}  

    ### User Information
    #### Birth Chart (Kundli):
    **Ascendant:** {kundli_data['ascendant']}  
    **Sun Sign:** {kundli_data['sun_sign']}  
    **Moon Sign:** {kundli_data['moon_sign']}  

    **Planetary Positions in Birth Chart:**
    - **Sun:** {kundli_data['planetary_positions']['Sun']['degree']}° in {kundli_data['planetary_positions']['Sun']['zodiac_sign']} (House: {kundli_data['planetary_positions']['Sun']['house']})
    - **Moon:** {kundli_data['planetary_positions']['Moon']['degree']}° in {kundli_data['planetary_positions']['Moon']['zodiac_sign']} (House: {kundli_data['planetary_positions']['Moon']['house']})
    - **Mars:** {kundli_data['planetary_positions']['Mars']['degree']}° in {kundli_data['planetary_positions']['Mars']['zodiac_sign']} (House: {kundli_data['planetary_positions']['Mars']['house']})
    - **Mercury:** {kundli_data['planetary_positions']['Mercury']['degree']}° in {kundli_data['planetary_positions']['Mercury']['zodiac_sign']} (House: {kundli_data['planetary_positions']['Mercury']['house']})
    - **Jupiter:** {kundli_data['planetary_positions']['Jupiter']['degree']}° in {kundli_data['planetary_positions']['Jupiter']['zodiac_sign']} (House: {kundli_data['planetary_positions']['Jupiter']['house']})
    - **Venus:** {kundli_data['planetary_positions']['Venus']['degree']}° in {kundli_data['planetary_positions']['Venus']['zodiac_sign']} (House: {kundli_data['planetary_positions']['Venus']['house']})
    - **Saturn:** {kundli_data['planetary_positions']['Saturn']['degree']}° in {kundli_data['planetary_positions']['Saturn']['zodiac_sign']} (House: {kundli_data['planetary_positions']['Saturn']['house']})
    - **Rahu (North Node):** {kundli_data['planetary_positions']['Rahu (North Node)']['degree']}° in {kundli_data['planetary_positions']['Rahu (North Node)']['zodiac_sign']} (House: {kundli_data['planetary_positions']['Rahu (North Node)']['house']})
    - **Ketu (South Node):** {kundli_data['planetary_positions']['Ketu (South Node)']['degree']}° in {kundli_data['planetary_positions']['Ketu (South Node)']['zodiac_sign']} (House: {kundli_data['planetary_positions']['Ketu (South Node)']['house']})

    #### Current Planetary Positions:
    **Ascendant:** {current_data['ascendant']}  
    **Sun Sign:** {current_data['sun_sign']}  
    **Moon Sign:** {current_data['moon_sign']}  

    **Planetary Positions in Current Chart:**
    - **Sun:** {current_data['planetary_positions']['Sun']['degree']}° in {current_data['planetary_positions']['Sun']['zodiac_sign']} (House: {current_data['planetary_positions']['Sun']['house']})
    - **Moon:** {current_data['planetary_positions']['Moon']['degree']}° in {current_data['planetary_positions']['Moon']['zodiac_sign']} (House: {current_data['planetary_positions']['Moon']['house']})
    - **Mars:** {current_data['planetary_positions']['Mars']['degree']}° in {current_data['planetary_positions']['Mars']['zodiac_sign']} (House: {current_data['planetary_positions']['Mars']['house']})
    - **Mercury:** {current_data['planetary_positions']['Mercury']['degree']}° in {current_data['planetary_positions']['Mercury']['zodiac_sign']} (House: {current_data['planetary_positions']['Mercury']['house']})
    - **Jupiter:** {current_data['planetary_positions']['Jupiter']['degree']}° in {current_data['planetary_positions']['Jupiter']['zodiac_sign']} (House: {current_data['planetary_positions']['Jupiter']['house']})
    - **Venus:** {current_data['planetary_positions']['Venus']['degree']}° in {current_data['planetary_positions']['Venus']['zodiac_sign']} (House: {current_data['planetary_positions']['Venus']['house']})
    - **Saturn:** {current_data['planetary_positions']['Saturn']['degree']}° in {current_data['planetary_positions']['Saturn']['zodiac_sign']} (House: {current_data['planetary_positions']['Saturn']['house']})
    - **Rahu (North Node):** {current_data['planetary_positions']['Rahu (North Node)']['degree']}° in {current_data['planetary_positions']['Rahu (North Node)']['zodiac_sign']} (House: {current_data['planetary_positions']['Rahu (North Node)']['house']})
    - **Ketu (South Node):** {current_data['planetary_positions']['Ketu (South Node)']['degree']}° in {current_data['planetary_positions']['Ketu (South Node)']['zodiac_sign']} (House: {current_data['planetary_positions']['Ketu (South Node)']['house']})

    ### User Query
    {request.user_query}

    ### Response
    {request.user_query}
    """

    try:
        # Generate response
        response = openai.ChatCompletion.create(
        # response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": prompt}],
            max_tokens=500
        )
        bot = response.choices[0].message.content.strip()
        
        # Save the chat history in the database (for both user query and bot response)
        if not existing_chat:  
            new_chat = ChatHistory(
                user_id=user_id,
                user=request.user_query,  
                bot=bot  
            )
            db.add(new_chat)
            db.commit()

        
        # Save both user query and bot response
        save_chat_history(db, user_id, request.user_query, bot)

        # Return structured response
        return ChatResponse(
            detailed_timeline="Generated based on astrological aspects.",
            astrological_insights=bot,
            remedies=["Parsed remedies from the response."]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {e}")


@router.get("/chat_history")
async def get_chat_history_endpoint(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Extract user_id from the current_user dictionary
    user_id = current_user.get("id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authenticated"
        )

    # Fetch chat history for the authenticated user
    chat_history_list = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).all()
    
    if not chat_history_list:
        return {"chat_history": []}

    # Convert the list of ChatHistory objects to readable Python data (list of dictionaries)
    chat_history_data = [convert_chat_history_to_dict(chat) for chat in chat_history_list]
    
    # Return the chat history data
    return {"chat_history": chat_history_data}

