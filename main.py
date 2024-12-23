from fastapi import FastAPI
from db.session import engine
from db.base import Base
from api.v1.routes import login, users, chat,Kundli,kundliChart,KundliMilanScore,KundliMilanChart,read_palm,panchang,choghadiya,horoscope
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(login.router, prefix="/api/v1/login", tags=["login"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(horoscope.router, prefix="/api/v1/users", tags=["Horoscope"])
app.include_router(Kundli.router, prefix="/api/v1/users", tags=["Kundli"])
app.include_router(kundliChart.router, prefix="/api/v1/users", tags=["Kundli Chart"])
app.include_router(KundliMilanScore.router, prefix="/api/v1/users", tags=["Kundli Milian Score"])
app.include_router(KundliMilanChart.router, prefix="/api/v1/users", tags=["Kundli Milan Chart"])
app.include_router(read_palm.router, prefix="/api/v1/users", tags=["palmistry"])
app.include_router(panchang.router, prefix="/api/v1/users", tags=["Panchang"])
app.include_router(choghadiya.router, prefix="/api/v1/users", tags=["Choghadiya"])



