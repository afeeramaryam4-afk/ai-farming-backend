from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import random
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Backend running"}

# =============================
# APP CONFIG
# =============================
app = FastAPI(title="AI Farming Backend - Full Version")
@app.get("/")
def home():
    return {"message": "AI Farming Backend is Running"}
@app.post("/register")
def register():
    pass

@app.post("/token")
def login():
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================
# DATABASE CONNECTION
# =============================
client = MongoClient("mongodb://localhost:27017/")
db = client["ai_farming"]
predictions_col = db["predictions"]
disease_col = db["disease_reports"]
soil_col = db["soil_reports"]
weather_col = db["weather_logs"]
model_col = db["model_versions"]
users_col = db["users"]

# =============================
# AUTHENTICATION (JWT)
# =============================
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return username   # return username only

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# =============================
# ALLOWED PLANTS
# =============================
ALLOWED_PLANTS = [
    " Sheesham",
    " Kachnar",
    "Euphorbia ",
    "Guava",
    "Fig",
    "Thuja",
    "Rose"
]

# =============================
# DATA MODELS
# =============================
class UserInput(BaseModel):
    username: str
    password: str

class PredictionInput(BaseModel):
    plant: str
    confidence: float

class DiseaseInput(BaseModel):
    plant: str
    disease: str
    confidence: float

class SoilInput(BaseModel):
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    soil_score: float

class WeatherInput(BaseModel):
    city: str
    temperature: float
    humidity: float
    rainfall: float

class ModelVersionInput(BaseModel):
    model_name: str
    version: str
    accuracy: float

class SoilCheckInput(BaseModel):
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float

class CropProductionInput(BaseModel):
    crop: str
    area_hectare: float
    fertilizer_amount: float
    rainfall: float
    temperature: float

class WeatherPredictInput(BaseModel):
    city: str

# =============================
# USER REGISTER / LOGIN
# =============================
@app.post("/register")
def register(user: UserInput):
    if users_col.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = pwd_context.hash(user.password)
    users_col.insert_one({"username": user.username, "password": hashed_password})
    return {"status": "User registered"}

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import status

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db_user = users_col.find_one({"username": form_data.username})

    if not db_user or not pwd_context.verify(form_data.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    token = jwt.encode(
        {"sub": form_data.username, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {"access_token": token, "token_type": "bearer"}

# =============================
# 1️⃣ STORE PREDICTIONS
# =============================
@app.post("/store/prediction")
def store_prediction(data: PredictionInput, username: str = Depends(verify_token)):   
    if data.plant not in ALLOWED_PLANTS:
        return {"error": "Plant not supported"}
    record = {
    "user_id": username,   # from token
    "plant": data.plant,
    "confidence": data.confidence,
    "timestamp": datetime.utcnow()
}
    predictions_col.insert_one(record)
    return {"status": "Prediction stored successfully"}

# =============================
# 2️⃣ STORE DISEASE
# =============================
@app.post("/store/disease")
def store_disease(data: DiseaseInput, username: str = Depends(verify_token)):
    record = {
        "user_id": username,
        "plant": data.plant,
        "disease": data.disease,
        "confidence": data.confidence,
        "timestamp": datetime.utcnow()
    }
    disease_col.insert_one(record)
    return {"status": "Disease report stored"}

# =============================
# 3️⃣ STORE SOIL REPORT
# =============================
@app.post("/store/soil")
def store_soil(data: SoilInput, username: str = Depends(verify_token)):
    record = {
        "user_id": username,
        "nitrogen": data.nitrogen,
        "phosphorus": data.phosphorus,
        "potassium": data.potassium,
        "ph": data.ph,
        "soil_score": data.soil_score,
        "timestamp": datetime.utcnow()
    }
    soil_col.insert_one(record)
    return {"status": "Soil report stored"}

# =============================
# 4️⃣ STORE WEATHER
# =============================
@app.post("/store/weather")
def store_weather(data: WeatherInput, username: str = Depends(verify_token)):
    record = {
        "user_id": username,
        "city": data.city,
        "temperature": data.temperature,
        "humidity": data.humidity,
        "rainfall": data.rainfall,
        "timestamp": datetime.utcnow()
    }
    weather_col.insert_one(record)
    return {"status": "Weather log stored"}
# =============================
# 5️⃣ STORE MODEL VERSION
# =============================
@app.post("/model/version")
def save_model_version(data: ModelVersionInput, username: str = Depends(verify_token)):
    record = {
        "user_id": username,   # 🔥 Added
        "model_name": data.model_name,
        "version": data.version,
        "accuracy": data.accuracy,
        "timestamp": datetime.utcnow()
    }

    model_col.insert_one(record)

    return {"status": "Model version saved"}

# =============================
# 6️⃣ SOIL CONDITION CHECK
# =============================
@app.post("/check/soil", dependencies=[Depends(verify_token)])
def check_soil_condition(data: SoilCheckInput):
    advice = []
    if data.ph < 5.5:
        advice.append("Soil is acidic – consider liming")
    elif data.ph > 7.5:
        advice.append("Soil is alkaline – consider sulfur application")
    else:
        advice.append("Soil pH is optimal")
    if data.nitrogen < 50:
        advice.append("Nitrogen is low – use nitrogen fertilizer")
    if data.phosphorus < 20:
        advice.append("Phosphorus is low – use phosphate fertilizer")
    if data.potassium < 50:
        advice.append("Potassium is low – use potash fertilizer")
    if not advice:
        advice.append("Soil nutrients are optimal")
    return {"soil_advice": advice}

# =============================
# 7️⃣ CROP PRODUCTION RECOMMENDATION
# =============================
@app.post("/recommend/crop-production")
def crop_production_recommendation(
    data: CropProductionInput,
    username: str = Depends(verify_token)
):
    expected_yield = data.area_hectare * 2

    if data.fertilizer_amount > 50:
        expected_yield += 0.5
    if data.rainfall < 20:
        expected_yield -= 0.5
    if data.temperature > 35:
        expected_yield -= 0.3

    advice = f"Expected yield for {data.crop} is ~{round(expected_yield,2)} tons/ha"

    record = {
        "user_id": username,   # 🔥 Added
        "crop": data.crop,
        "area_hectare": data.area_hectare,
        "fertilizer_amount": data.fertilizer_amount,
        "rainfall": data.rainfall,
        "temperature": data.temperature,
        "expected_yield": round(expected_yield, 2),
        "timestamp": datetime.utcnow()
    }

    predictions_col.insert_one(record)

    return {"crop_production_advice": advice}

# =============================
# 8️⃣ WEATHER-BASED PREDICTION
# =============================
@app.post("/predict/weather")
def weather_based_prediction(
    data: WeatherPredictInput,
    username: str = Depends(verify_token)
):
    temp = round(random.uniform(20, 35), 1)
    humidity = round(random.uniform(40, 90), 1)
    rainfall = round(random.uniform(0, 20), 1)

    advice = []

    if rainfall > 10:
        advice.append("High chance of rain – avoid irrigation")
    if temp > 35:
        advice.append("High temperature – risk of heat stress")
    if humidity > 80:
        advice.append("High humidity – pest & disease risk")
    if not advice:
        advice.append("Weather is favorable for farming")

    record = {
        "user_id": username,   # 🔥 Added
        "city": data.city,
        "predicted_temperature": temp,
        "predicted_humidity": humidity,
        "predicted_rainfall": rainfall,
        "timestamp": datetime.utcnow()
    }

    weather_col.insert_one(record)

    return {
        "city": data.city,
        "predicted_temperature": temp,
        "predicted_humidity": humidity,
        "predicted_rainfall": rainfall,
        "farming_advice": advice
    }

# =============================
# 9️⃣ ANALYTICS
# =============================
@app.get("/analytics/top-plant", dependencies=[Depends(verify_token)])
def top_plant():
    pipeline = [
        {"$group": {"_id": "$plant", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    result = list(predictions_col.aggregate(pipeline))
    return result

@app.get("/analytics/top-disease", dependencies=[Depends(verify_token)])
def top_disease():
    pipeline = [
        {"$group": {"_id": "$disease", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    result = list(disease_col.aggregate(pipeline))
    return result

# =============================
# HEALTH CHECK
# =============================
@app.get("/ping")
def ping():
    return {"status": "AI Farming Backend Running"}
# =============================
# 🔟 USER COMPLETE HISTORY
# =============================
@app.get("/user/history")
def user_history(username: str = Depends(verify_token)):

    predictions = list(predictions_col.find(
        {"user_id": username},
        {"_id": 0}
    ))

    diseases = list(disease_col.find(
        {"user_id": username},
        {"_id": 0}
    ))

    soil_reports = list(soil_col.find(
        {"user_id": username},
        {"_id": 0}
    ))

    weather_logs = list(weather_col.find(
        {"user_id": username},
        {"_id": 0}
    ))

    return {
        "predictions": predictions,
        "disease_reports": diseases,
        "soil_reports": soil_reports,
        "weather_logs": weather_logs
    }
# =============================
# 1️⃣1️⃣ USER ANALYTICS
# =============================

@app.get("/analytics/user/top-plant")
def user_top_plant(username: str = Depends(verify_token)):

    pipeline = [
        {"$match": {"user_id": username}},
        {"$group": {"_id": "$plant", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]

    result = list(predictions_col.aggregate(pipeline))
    return result


@app.get("/analytics/user/top-disease")
def user_top_disease(username: str = Depends(verify_token)):

    pipeline = [
        {"$match": {"user_id": username}},
        {"$group": {"_id": "$disease", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]

    result = list(disease_col.aggregate(pipeline))
    return result