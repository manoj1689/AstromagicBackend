from sqlalchemy import Column, String, Column, Integer, Date, Time
from db.base import Base



# User model
class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    occupation = Column(String, nullable=True)
    place_of_birth = Column(String, nullable=True)
    time_of_birth = Column(Time, nullable=True)
    image_link = Column(String, nullable=True)
