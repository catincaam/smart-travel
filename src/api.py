from typing import Dict, List, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from .data_quality import DataQualityError
    from .recommend import recommend_destinations, season_from_month
except ImportError:
    from data_quality import DataQualityError
    from recommend import recommend_destinations, season_from_month


app = FastAPI(
    title="Smart Travel API",
    description="Recommendation API for the Smart Travel project.",
    version="0.1.0",
)


class RecommendationRequest(BaseModel):
    food: float = Field(ge=0, le=10, description="Food preference from 0 to 10.")
    beach: float = Field(ge=0, le=10, description="Beach preference from 0 to 10.")
    culture: float = Field(ge=0, le=10, description="Culture preference from 0 to 10.")
    nature: float = Field(ge=0, le=10, description="Nature preference from 0 to 10.")
    nightlife: float = Field(
        ge=0, le=10, description="Nightlife preference from 0 to 10."
    )
    month: str = Field(description="Travel month, for example August or October.")
    budget: Literal["Low (Essential)", "Medium (Comfort)", "High (Luxury)"] = Field(
        default="Medium (Comfort)",
        description="Budget preference: Low (Essential), Medium (Comfort), or High (Luxury).",
    )
    weather_preference: Literal["Warm", "Mild", "Cool", "Any"] = Field(
        default="Any",
        description="Preferred weather: Warm, Mild, Cool, or Any.",
    )
    companion: Literal["Solo", "Partner", "Friends", "Family"] = Field(
        default="Partner",
        description="Who the user is travelling with: Solo, Partner, Friends, or Family.",
    )
    top_n: int = Field(default=5, ge=1, le=20, description="Number of results.")


class RecommendationResult(BaseModel):
    destination_name: str
    country: str
    recommendation_score: float
    preference_score: float
    weather_score: float
    cost_score: float
    budget_match_score: float
    companion_match_score: float
    cost_of_living_index: float
    cost_level: str
    cluster_profile: str
    dominant_travel_style: str
    climate_category: str
    travel_season: str
    season_avg_temp: float
    season_avg_daily_rain: float
    explanation: str
    natural_reason: str
    reason: Dict[str, float]


class RecommendationResponse(BaseModel):
    travel_month: str
    season: str
    preferences: dict
    budget: str
    weather_preference: str
    companion: str
    recommendations: List[RecommendationResult]


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "Smart Travel API is running.",
        "docs": "/docs",
    }


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest):
    preferences = {
        "food": request.food,
        "beach": request.beach,
        "culture": request.culture,
        "nature": request.nature,
        "nightlife": request.nightlife,
    }

    try:
        season = season_from_month(request.month)
        recommendations = recommend_destinations(
            preferences=preferences,
            travel_month=request.month,
            top_n=request.top_n,
            budget=request.budget,
            weather_preference=request.weather_preference,
            companion=request.companion,
        )
    except DataQualityError as error:
        raise HTTPException(status_code=503, detail="Destination data is being reviewed. Please try again later.") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "travel_month": request.month,
        "season": season,
        "preferences": preferences,
        "budget": request.budget,
        "weather_preference": request.weather_preference,
        "companion": request.companion,
        "recommendations": recommendations.to_dict(orient="records"),
    }
