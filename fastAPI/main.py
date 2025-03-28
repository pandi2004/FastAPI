from fastapi import FastAPI, Request, Form, HTTPException, Query, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore
import google.auth.transport.requests
import google.oauth2.id_token
from typing import List, Optional
import os
from google.cloud.firestore_v1 import DELETE_FIELD
import re

# Initialize FastAPI App
app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service_account_path = "gcloud-key.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path

# Firestore Database
db = firestore.Client()

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Verify Firebase Token using Google's API
def verify_firebase_token(token: str):
    try:
        request_adapter = google.auth.transport.requests.Request()
        decoded_token = google.oauth2.id_token.verify_firebase_token(token, request_adapter)
        return decoded_token  # Return user details if valid
    except Exception as e:
        # print("Token verification failed:", str(e))
        return None  # Return None if invalid


# Render Homepage
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})

@app.get("/driver-profile", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("driver_Profile.html", {"request": request})

@app.get("/team-profile", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("Team_Profile.html", {"request": request})

# Render Login Page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, token: Optional[str] = Query(None)):
    user_token = verify_firebase_token(token) if token else None
    return templates.TemplateResponse("lg.html", {"request": request, "user_token": user_token})





@app.get("/compare-drivers", response_class=HTMLResponse)
async def compare_drivers(request: Request, driver1: str = Query(...), driver2: str = Query(...)):
    """Compare two drivers based on statistics."""
    driver_doc1 = db.collection("Drivers").document(driver1).get()
    driver_doc2 = db.collection("Drivers").document(driver2).get()

    if not driver_doc1.exists or not driver_doc2.exists:
        raise HTTPException(status_code=404, detail="One or both drivers not found")

    d1 = driver_doc1.to_dict()
    d2 = driver_doc2.to_dict()

    stats = ["age", "pole_position", "race_wins", "world_championships", "total_fastest_laps","team"]
    
    comparison = {}
    for stat in stats:
        val1 = d1.get(stat, 0)
        val2 = d2.get(stat, 0)
        better = driver1 if val1 < val2 and stat == "age" else driver1 if val1 > val2 else driver2
        comparison[stat] = {"driver1": val1, "driver2": val2, "better": better}

    return templates.TemplateResponse("Compare_Driver.html", {
        "request": request,
        "comparison": comparison,
        "driver1": d1,
        "driver2": d2
    })



@app.post("/add-driver")
async def add_driver(
    request: Request,
    token: Optional[str] = Cookie(None),  # Get token from cookies
    full_name: str = Form(...),
    driver_id: str = Form(...),
    pole_position: int = Form(...),
    language: str = Form(...),
    age: int = Form(...),
    race_wins: int = Form(...),
    country_titles: int = Form(...),
    team: str = Form(...),
    date_of_birth: str = Form(...),
    nationality: str = Form(...),
    father: str = Form(...),
    mother: str = Form(...),
    world_championships: int = Form(...),
    total_fastest_laps: int = Form(...)
):
    """Handles adding or updating driver profiles."""

    # Validate Firebase token
    if not token:
        return JSONResponse(status_code=401, content={"error": "Token missing. Please log in."})

    user_token = verify_firebase_token(token)
    if not user_token:
        return JSONResponse(status_code=401, content={"error": "Unauthorized user."})

    # Validate driver_id format
    if not re.match(r"^[a-zA-Z0-9_-]+$", driver_id):
        return JSONResponse(status_code=400, content={"error": "Driver ID must be alphanumeric."})

    try:
        driver_ref = db.collection("Drivers").document(full_name)
        driver_exists = driver_ref.get().exists  # Check if driver exists

        driver_data = {
            "full_name": full_name,
            "pole_position": pole_position,
            "language": language,
            "age": age,
            "race_wins": race_wins,
            "country_titles": country_titles,
            "team": team,
            "date_of_birth": date_of_birth,
            "nationality": nationality,
            "father": father,
            "mother": mother,
            "world_championships": world_championships,
            "total_fastest_laps": total_fastest_laps,
        }

        if driver_exists:
            driver_ref.update(driver_data)
            message = "Driver profile updated successfully!"
        else:
            driver_ref.set({"driver_id": driver_id, **driver_data})
            message = "Driver profile created successfully!"

        # Return JSON response for AJAX requests
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JSONResponse(content={"message": message})

        return RedirectResponse(url="/drivers-page", status_code=302)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Server error: {str(e)}"})

#--------------------------------------
@app.get("/driver/{driverName}", response_class=JSONResponse)
async def get_driver(driverName: str):
    # print(f"Checking Firestore for driver: {driverName}")  # Debugging

    driver_ref = db.collection("Drivers").document(driverName).get()

    if not driver_ref.exists:
        # print(f"Driver {driverName} not found in Firestore")  # Debugging
        raise HTTPException(status_code=404, detail="Driver not found")

    # print(f"Found Driver: {driver_ref.to_dict()}")  # Debugging
    return driver_ref.to_dict()


@app.get("/drivers-page", response_class=HTMLResponse)
async def all_drivers(
    request: Request,
    field: Optional[str] = None,
    operator: Optional[str] = None,
    value: Optional[str] = None,
    token: Optional[str] = Cookie(None)
):
    user_token = verify_firebase_token(token) if token else None

    driver_docs = db.collection("Drivers").stream()
    drivers = [doc.to_dict() for doc in driver_docs]

    # Filtering Logic
    filtered_drivers = drivers

    if field and operator and value:
        # Map frontend field names to Firestore keys
        key_map = {
            "driver_id": "driver_id",
            "full_name": "full_name",
            "age": "age",
            "pole_position": "pole_position",
            "race_wins": "race_wins",
            "country_titles": "country_titles",
        }
        key = key_map.get(field)

        if key:
            if key in ["age", "pole_position", "race_wins", "country_titles",]:
                try:
                    num_value = int(value)
                    if operator == "eq":
                        filtered_drivers = [d for d in filtered_drivers if d.get(key) == num_value]
                    elif operator == "lt":
                        filtered_drivers = [d for d in filtered_drivers if d.get(key, 0) < num_value]
                    elif operator == "gt":
                        filtered_drivers = [d for d in filtered_drivers if d.get(key, 0) > num_value]
                except ValueError:
                    filtered_drivers = []
            else:
                if operator == "eq":
                    filtered_drivers = [d for d in filtered_drivers if str(d.get(key, "")).lower() == value.lower()]

    return templates.TemplateResponse("Drivers1.html", {
        "request": request,
        "user_token": user_token,
        "drivers": filtered_drivers,
    })


@app.get("/teams", response_class=HTMLResponse)
async def all_teams(
    request: Request,
    field: Optional[str] = None,
    operator: Optional[str] = None,
    value: Optional[str] = None,
    token: Optional[str] = Cookie(None)
):
    user_token = verify_firebase_token(token) if token else None

    team_docs = db.collection("Teams").stream()
    teams = [doc.to_dict() for doc in team_docs]

    # Filtering Logic
    filtered_teams = teams

    if field and operator and value:
        # Map frontend field names to Firestore keys
        key_map = {
            "tId": "tId",
            "tname": "tname",
            "founded": "founded",
            "pole_position": "pole_position",
            "race_wins": "race_wins",
            "country_titles": "country_titles",
        }
        key = key_map.get(field)

        if key:
            if key in ["founded", "pole_position", "race_wins", "country_titles",]:
                try:
                    num_value = int(value)
                    if operator == "eq":
                        filtered_teams = [d for d in filtered_teams if d.get(key) == num_value]
                    elif operator == "lt":
                        filtered_teams = [d for d in filtered_teams if d.get(key, 0) < num_value]
                    elif operator == "gt":
                        filtered_teams = [d for d in filtered_teams if d.get(key, 0) > num_value]
                except ValueError:
                    filtered_teams = []
            else:
                if operator == "eq":
                    filtered_teams = [d for d in filtered_teams if str(d.get(key, "")).lower() == value.lower()]

    return templates.TemplateResponse("Teams.html", {
        "request": request,
        "user_token": user_token,
        "teams": filtered_teams,
    })

@app.delete("/driver/{driver_name}")
async def delete_driver(driver_name: str, token: Optional[str] = Cookie(None)):
    # Verify user token from the cookie
    user_token = verify_firebase_token(token) if token else None
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Get the driver document (assuming document ID is the driver's identifier)
    driver_ref = db.collection("Drivers").document(driver_name)
    driver_doc = driver_ref.get()
    if not driver_doc.exists:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Delete the driver document
    driver_ref.delete()
    return JSONResponse(content={"message": f"Driver '{driver_name}' deleted successfully"})



# teams------------------------

@app.post("/add-team")
async def add_team(
    request: Request,
    token: Optional[str] = Cookie(None),  # Get token from cookies
    tname: str = Form(...),
    tId: str = Form(...),
    pole_position: int = Form(...),
    founded: int = Form(...),
    race_wins: int = Form(...),
    country_titles: int = Form(...),
    world_championships: int = Form(...),
    tPrincipal:str=Form(...),
    engineSupplier: str=Form(...),
    tCEO: str=Form(...)
):
    """Handles adding or updating team profiles."""

    # Validate Firebase token
    if not token:
        return JSONResponse(status_code=401, content={"error": "Token missing. Please log in."})

    user_token = verify_firebase_token(token)
    if not user_token:
        return JSONResponse(status_code=401, content={"error": "Unauthorized user."})

    # Validate tId format
    if not re.match(r"^[a-zA-Z0-9_-]+$", tId):
        return JSONResponse(status_code=400, content={"error": "Team ID must be alphanumeric."})

    try:
        team_ref = db.collection("Teams").document(tname)
        team_exists = team_ref.get().exists  # Check if team exists

        team_data = {
            "tname": tname,
            "tId":tId,
            "pole_position": pole_position,
            "founded": founded,
            "race_wins": race_wins,
            "country_titles": country_titles,
            "world_championships": world_championships,
            "engineSupplier":engineSupplier,
            "tPrincipal":tPrincipal,
            "tCEO":tCEO
        }

        if team_exists:
            team_ref.update(team_data)
            message = "Team profile updated successfully!"
        else:
            team_ref.set({"tId": tId, **team_data})
            message = "Team profile created successfully!"

        # Return JSON response for AJAX requests
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JSONResponse(content={"message": message})

        return RedirectResponse(url="/teams", status_code=302)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Server error: {str(e)}"})


@app.get("/team/{teamName}", response_class=JSONResponse)
async def get_team(teamName: str):
    teamName = teamName.strip()  # optional
    # print(f"Checking Firestore for team: {teamName}")  # Debugging

    team_doc = db.collection("Teams").document(teamName).get()

    if not team_doc.exists:
        # print(f"Team {teamName} not found in Firestore")  # Debugging
        raise HTTPException(status_code=404, detail="Team not found")

    team_data = team_doc.to_dict()
    # print(f"Found Team: {team_data}")  # Debugging
    return team_data

from fastapi import Request

@app.delete("/team/{team_name}")
async def delete_team(
    team_name: str,
    request: Request,
    token: Optional[str] = Cookie(None)
):
    """Deletes a team document from Firestore if authorized."""

    # Verify Firebase Token
    if not token:
        raise HTTPException(status_code=401, detail="Token missing. Please log in.")

    user_token = verify_firebase_token(token)
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Check if team exists
        team_ref = db.collection("Teams").document(team_name)
        team_doc = team_ref.get()

        if not team_doc.exists:
            raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")

        # Delete team
        team_ref.delete()

        # Return JSON for AJAX requests
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JSONResponse(content={"message": f"Team '{team_name}' deleted successfully"})

        # If normal request
        return RedirectResponse(url="/teams", status_code=302)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting team: {str(e)}")

@app.get("/compare-teams", response_class=HTMLResponse)
async def compare_teams(request: Request, team1: str = Query(...), team2: str = Query(...)):
    """Compare two teams based on statistics."""
    team_doc1 = db.collection("Teams").document(team1).get()
    team_doc2 = db.collection("Teams").document(team2).get()

    if not team_doc1.exists or not team_doc2.exists:
        raise HTTPException(status_code=404, detail="One or both teams not found")

    t1 = team_doc1.to_dict()
    t2 = team_doc2.to_dict()

    stats = ["founded", "pole_position", "race_wins", "world_championships"]
    
    comparison = {}
    for stat in stats:
        val1 = t1.get(stat, 0)
        val2 = t2.get(stat, 0)
        better = team1 if val1 < val2 and stat == "founded" else team1 if val1 > val2 else team2
        comparison[stat] = {"team1": val1, "team2": val2, "better": better}

    return templates.TemplateResponse("Compare_Team.html", {
        "request": request,
        "comparison": comparison,
        "team1": t1,
        "team2": t2
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
