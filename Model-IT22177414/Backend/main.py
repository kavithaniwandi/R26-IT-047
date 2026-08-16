from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth,
    users,
    disaster_donation_requests,
    donation_history,
    donation_items
)

app = FastAPI(
    title="Disaster Relief & Donation API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(disaster_donation_requests.router)
app.include_router(donation_history.router)
app.include_router(donation_items.router)

@app.get("/")
def root():
    return {"message": "Disaster Relief Backend API is running"}