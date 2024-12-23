from sqlalchemy import Column, Integer, String, Text, DateTime
from db.base import Base
from datetime import datetime

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, autoincrement=True) 
    user_id = Column(String, index=True) 
    user = Column(String, index=True)
    bot = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow) 
