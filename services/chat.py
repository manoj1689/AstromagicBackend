import json
from db.models.chat import ChatHistory
import tiktoken
from typing import List
import openai
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException

# Constants
MAX_HISTORY_TOKENS = 1000
MODEL = "gpt-4"


# Load scenarios from JSON
try:
    with open("api/files/scenarios.json", "r") as f:
        SCENARIOS = json.load(f)["scenarios"]
except FileNotFoundError:
    raise FileNotFoundError("scenarios.json file not found in the current directory.")
except KeyError:
    raise ValueError("The 'scenarios' key is missing in the JSON file.")


# # Token calculation
# def calculate_tokens(text: str, model: str = MODEL) -> int:
#     encoding = tiktoken.encoding_for_model(model)
#     return len(encoding.encode(text))

def calculate_tokens(text, model: str = MODEL) -> int:
    # Ensure text is a string if it's a list of objects
    if isinstance(text, list):
        # If text is a list (e.g., a list of ChatHistory objects), extract the relevant text from each item
        combined_text = " ".join([str(item.text) if hasattr(item, 'text') else str(item) for item in text])
    else:
        # If it's already a string, just use it directly
        combined_text = str(text)
    
    # Now pass the combined text to tiktoken for encoding
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(combined_text))



# Summarize history
def summarize_history(chat_history_context: List[ChatHistory]) -> str:
    full_text = "\n".join([f"User: {m['user']}\nBot: {m['bot']}" for m in chat_history_context])
    prompt = f"Summarize the following conversation for context:\n\n{full_text}\n\nProvide a concise summary:"
    
    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{"role": "system", "content": prompt}],
            max_tokens=200
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error during summarization: {e}")
        return "Summary could not be generated due to an error."

# Truncate history
def truncate_chat_history(chat_history_context: List[ChatHistory], max_tokens: int) -> List[ChatHistory]:
    total_tokens = 0
    truncated_history = []
    for message in reversed(chat_history_context):
        message_tokens = calculate_tokens(message['user'] + message['bot'], model=MODEL)
        if total_tokens + message_tokens > max_tokens:
            break
        truncated_history.insert(0, message)
        total_tokens += message_tokens
    return truncated_history



def save_chat_history(db: Session, user_id: str, user_message: str, bot_response: str):
    new_chat = ChatHistory(
        user_id=user_id,
        user=user_message,
        bot=bot_response
    )
    db.add(new_chat)
    db.commit()

def get_chat_history(db: Session):
    return db.query(ChatHistory).all()

def convert_chat_history_to_dict(chat_history_list):
    # Convert each ChatHistory object into a dictionary
    chat_history_data = [
        {
            "id": chat.id,
            "user_id": chat.user_id,
            "user": chat.user,
            "bot": chat.bot,
            "timestamp": chat.timestamp.isoformat()  # Format the datetime as string
        }
        for chat in chat_history_list
    ]
    return chat_history_data

def validate_user_details(date_of_birth: str, time_of_birth: str, place_of_birth: str):
    # Validate Date of Birth
    try:
        datetime.strptime(date_of_birth, "%d-%m-%Y")  # Ensure DD-MM-YYYY format
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date of birth. Please provide a valid date in DD-MM-YYYY format.")

    # Validate Time of Birth
    try:
        datetime.strptime(time_of_birth, "%I:%M %p")  # Ensure HH:MM AM/PM format
    except ValueError:
        try:
            datetime.strptime(time_of_birth, "%H:%M")  # Check 24-hour format
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time of birth. Please provide time in HH:MM AM/PM or HH:MM (24-hour) format.")
    # Validate Place of Birth
    if not place_of_birth or not isinstance(place_of_birth, str) or len(place_of_birth.strip()) == 0:
        raise HTTPException(status_code=400, detail="Invalid place of birth. Please provide a valid location.")
