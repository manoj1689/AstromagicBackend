
from pydantic import BaseModel
from typing import List, Optional


class Scenario(BaseModel):
    id: int
    title: str
    description: str
    category: str
    example_questions: List[str]
    astrological_focus: str
    output_format: str

class ChatHistory(BaseModel):
    user: str
    bot: str

class ChatRequest(BaseModel):
    scenario_id: int
    user_query: str

    
class ChatResponse(BaseModel):
    detailed_timeline: Optional[str]
    astrological_insights: Optional[str]
    remedies: Optional[List[str]]
