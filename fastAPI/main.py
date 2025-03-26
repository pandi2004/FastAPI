from fastapi import FastAPI, Request, Form, HTTPException, Query, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore
import google.auth.transport.requests
import google.oauth2.id_token
from typing import Optional
import os
from google.cloud.firestore_v1 import DELETE_FIELD
import re
from google.cloud import storage
from fastapi import File, UploadFile
import shutil

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

# Initialize Google Cloud Storage
storage_client = storage.Client()
bucket_name = "fastapi-bucket-19c47"  # Replace with your actual bucket name
bucket = storage_client.bucket(bucket_name)

# service_account_path = r"dfsdfd-b738c-firebase-adminsdk-fbsvc-d7e2f0c9f9.json"
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path

# Set your Google Cloud Project ID manually
PROJECT_ID = "fastapiproject-19c47"  # Replace with your actual Project ID

# Initialize Firestore with the correct project ID
db = firestore.Client(project=PROJECT_ID)

# Firestore Database (No need for a service account key)
# db = firestore.Client()

# set GOOGLE_APPLICATION_CREDENTIALS=%APPDATA%\gcloud\application_default_credentials.json


# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# @app.post("/upload/")
# async def upload_file(file: UploadFile = File(...)):
#     """Uploads a file to Google Cloud Storage and returns the public URL."""
#     try:
#         # Read file content
#         file_path = f"uploads/{file.filename}"
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         # Upload to Google Cloud Storage
#         blob = bucket.blob(file.filename)
#         blob.upload_from_filename(file_path)
#         blob.make_public()  # Make file publicly accessible

#         return {"message": "File uploaded successfully!", "file_url": blob.public_url}

#     except Exception as e:
#         return {"error": f"Upload failed: {str(e)}"}
    

#     @app.get("/get-file/{file_name}")
# async def get_file(file_name: str):
#     """Returns the public URL of a file stored in Google Cloud Storage."""
#     blob = bucket.blob(file_name)

#     if not blob.exists():
#         return {"error": "File not found"}

#     return {"file_url": blob.public_url}


# ✅ Verify Firebase Token using Google's API
def verify_firebase_token(token: str):
    try:
        request_adapter = google.auth.transport.requests.Request()
        decoded_token = google.oauth2.id_token.verify_firebase_token(token, request_adapter)
        return decoded_token  # Return user details if valid
    except Exception as e:
        print("Token verification failed:", str(e))
        return None  # Return None if invalid


# ✅ Render Homepage
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})

@app.get("/driver-profile", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("driver_Profile.html", {"request": request})

# ✅ Render Login Page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, token: Optional[str] = Query(None)):
    user_token = verify_firebase_token(token) if token else None
    return templates.TemplateResponse("login.html", {"request": request, "user_token": user_token})

# # Page Rendering Route (Returns `drivers.html`)
# @app.get("/drivers-page")
# async def render_drivers_page(request: Request, token: Optional[str] = Cookie(None)):
#     return templates.TemplateResponse("Drivers1.html", {"request": request, "user_token": token})



# # ✅ Add New Driver (Only Logged-in Users)
# @app.post("/add-driver")
# async def add_driver(
#     request: Request,
#     token: str = Form(...),
#     name: str = Form(...),
#     age: int = Form(...),
#     total_pole: int = Form(...),
#     total_wins: int = Form(...),
#     total_points: int = Form(...),
#     total_titles: int = Form(...),
#     total_fastest_laps: int = Form(...),
#     team: str = Form(...),
# ):
#     user_token = verify_firebase_token(token)
#     if not user_token:
#         return JSONResponse(content={"error": "Unauthorized"}, status_code=401)

#     # Prevent duplicate drivers
#     existing = db.collection("drivers").where("name", "==", name).stream()
#     if any(existing):
#         return JSONResponse(content={"error": "Driver already exists"}, status_code=400)

#     driver_data = {
#         "name": name,
#         "age": age,
#         "total_pole": total_pole,
#         "total_wins": total_wins,
#         "total_points": total_points,
#         "total_titles": total_titles,
#         "total_fastest_laps": total_fastest_laps,
#         "team": team,
#     }
#     db.collection("drivers").document(name).set(driver_data)
#     return JSONResponse(content={"message": "Driver added successfully"})


# # ✅ Get Driver Profile
# @app.get("/driver/{driver_name}", response_class=HTMLResponse)
# async def driver_profile(request: Request, driver_name: str, token: Optional[str] = Query(None)):
#     user_token = verify_firebase_token(token) if token else None
#     driver_doc = db.collection("Drivers").document(driver_name).get()

#     if not driver_doc.exists:
#         raise HTTPException(status_code=404, detail="Driver not found")

#     return templates.TemplateResponse("driver_profile.html", {
#         "request": request,
#         "driver": driver_doc.to_dict(),
#         "user_token": user_token,
#     })


# ✅ Get Team Profile
@app.get("/team/{team_name}", response_class=HTMLResponse)
async def team_profile(request: Request, team_name: str, token: Optional[str] = Query(None)):
    user_token = verify_firebase_token(token) if token else None
    team_doc = db.collection("teams").document(team_name).get()

    if not team_doc.exists:
        raise HTTPException(status_code=404, detail="Team not found")

    return templates.TemplateResponse("team_profile.html", {
        "request": request,
        "team": team_doc.to_dict(),
        "user_token": user_token,
    })


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



# @app.post("/compare-drivers", response_class=HTMLResponse)
# async def compare_drivers(request: Request, driver1: str = Form(...), driver2: str = Form(...)):
#     token = request.cookies.get("token")
#     user = verify_firebase_token(token) if token else None
#     driver_doc1 = db.collection("drivers").document(driver1).get()
#     driver_doc2 = db.collection("drivers").document(driver2).get()
#     if not driver_doc1.exists or not driver_doc2.exists:
#         raise HTTPException(status_code=404, detail="One or both drivers not found")
#     d1 = driver_doc1.to_dict()
#     d2 = driver_doc2.to_dict()

#     # For each stat compare and determine which driver is better.
#     # For age, a lower number is better; for all other stats, the higher value is better.
#     comparison = {}
#     stats = ["age", "total_pole", "total_wins", "total_points", "total_titles", "total_fastest_laps"]
#     for stat in stats:
#         val1 = d1.get(stat)
#         val2 = d2.get(stat)
#         if stat == "age":
#             better = driver1 if val1 < val2 else driver2
#         else:
#             better = driver1 if val1 > val2 else driver2
#         comparison[stat] = {"driver1": val1, "driver2": val2, "better": better}

#     return templates.TemplateResponse("Compare_Driver.html", {
#         "request": request,
#         "comparison": comparison,
#         "driver1": d1,
#         "driver2": d2,
#         "user": user
#     })


#-------------------------------
# POST endpoint to add a new driver profile to the "Drivers" collection

# @app.post("/add-driver", response_class=RedirectResponse)
# async def add_driver(
#     request: Request,
#     token: Optional[str] = Cookie(None),  # Get token from cookies
#     full_name: str = Form(...),
#     driver_id: str = Form(...),
#     pole_position: int = Form(...),
#     language: str = Form(...),
#     age: int = Form(...),
#     race_wins: int = Form(...),
#     country_titles: int = Form(...),
#     team: str = Form(...),
#     date_of_birth: str = Form(...),
#     nationality: str = Form(...),
#     father: str = Form(...),
#     mother: str = Form(...),
#     world_championships: int = Form(...),
#     total_fastest_laps: int = Form(...)
# ):
#     if not token:
#         raise HTTPException(status_code=401, detail="Token missing. Please log in.")

#     user_token = verify_firebase_token(token)
#     if not user_token:
#         raise HTTPException(status_code=401, detail="Unauthorized user.")

#     query_fullname = list(db.collection("Drivers").where("full_name", "==", full_name).get())
#     query_driverid = list(db.collection("Drivers").where("driver_id", "==", driver_id).get())
    
#     if query_fullname:
#         raise HTTPException(status_code=400, detail="Driver with this full name already exists")
#     if query_driverid:
#         raise HTTPException(status_code=400, detail="Driver with this driver ID already exists")

#     driver_data = {
#         "full_name": full_name,
#         "driver_id": driver_id,
#         "pole_position": pole_position,
#         "language": language,
#         "age": age,
#         "race_wins": race_wins,
#         "country_titles": country_titles,
#         "team": team,
#         "date_of_birth": date_of_birth,
#         "nationality": nationality,
#         "father": father,
#         "mother": mother,
#         "world_championships": world_championships,
#         "total_fastest_laps": total_fastest_laps
#     }

#     db.collection("Drivers").document(full_name).set(driver_data)

#     return RedirectResponse(url="/drivers-page", status_code=302)


@app.post("/add-driver")
async def add_driver(
    request: Request,
    token: Optional[str] = Cookie(None),  # 🔥 Get token from cookies
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

    # 🔥 Validate Firebase token
    if not token:
        return JSONResponse(status_code=401, content={"error": "Token missing. Please log in."})

    user_token = verify_firebase_token(token)
    if not user_token:
        return JSONResponse(status_code=401, content={"error": "Unauthorized user."})

    # 🔥 Validate driver_id format
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

        # 🔥 Return JSON response for AJAX requests
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JSONResponse(content={"message": message})

        return RedirectResponse(url="/drivers-page", status_code=302)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Server error: {str(e)}"})

#--------------------------------------
@app.get("/driver/{driverName}", response_class=JSONResponse)
async def get_driver(driverName: str):
    print(f"🔍 Checking Firestore for driver: {driverName}")  # Debugging

    driver_ref = db.collection("Drivers").document(driverName).get()

    if not driver_ref.exists:
        print(f"❌ Driver {driverName} not found in Firestore")  # Debugging
        raise HTTPException(status_code=404, detail="Driver not found")

    print(f"✅ Found Driver: {driver_ref.to_dict()}")  # Debugging
    return driver_ref.to_dict()

# Mock Driver Database
# drivers_db = [
#     {"id": 1, "name": "Max Verstappen", "age": 26, "points_scored": 2500, "wins": 60, "poles": 35, "titles": 3, "team": "Red Bull"},
#     {"id": 2, "name": "Lewis Hamilton", "age": 39, "points_scored": 4300, "wins": 103, "poles": 104, "titles": 7, "team": "Mercedes"},
#     {"id": 3, "name": "Charles Leclerc", "age": 26, "points_scored": 1200, "wins": 5, "poles": 20, "titles": 0, "team": "Ferrari"},
#     {"id": 4, "name": "Lando Norris", "age": 24, "points_scored": 800, "wins": 1, "poles": 3, "titles": 0, "team": "McLaren"},
# ]

# @app.get("/drivers", response_class=JSONResponse)
# async def get_drivers(
#     driver_name: str, token: Optional[str] = Query(None),
#     driver_id: Optional[int] = Query(None, description="Filter by driver ID"),
#     attribute: Optional[str] = Query(None, description="Filter attribute (age, wins, points_scored)"),
#     comparison: Optional[str] = Query(None, description="Comparison operator (>, <, =)"),
#     value: Optional[int] = Query(None, description="Value for comparison")
# ):
#     results = drivers_db

#     # Filter by driver ID
#     if driver_id is not None:
#         results = [d for d in results if d["id"] == driver_id]

#     # Apply attribute-based filtering
#     if attribute and comparison and value is not None:
#         if attribute not in ["age", "wins", "points_scored"]:
#             return {"error": "Invalid attribute"}

#         if comparison == ">":
#             results = [d for d in results if d[attribute] > value]
#         elif comparison == "<":
#             results = [d for d in results if d[attribute] < value]
#         elif comparison == "=":
#             results = [d for d in results if d[attribute] == value]
#         else:
#             return {"error": "Invalid comparison operator"}

#     return JSONResponse(content={"data": results})  #Always returns JSON


@app.get("/drivers-page", response_class=HTMLResponse)
async def all_drivers(request: Request, token: Optional[str] = Cookie(None)):
    user_token = verify_firebase_token(token) if token else None
    driver_docs = db.collection("Drivers").stream()
    drivers = [doc.to_dict() for doc in driver_docs]
    print("Loading template: Drivers1.html")  # Debug print
    return templates.TemplateResponse("Drivers.html", {
        "request": request,
        "user_token": user_token,
        "drivers": drivers,
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






#########################################################

# ✅ Verify Firebase Token using Google's API
def verify_firebase_token(token: str):
    try:
        request_adapter = google.auth.transport.requests.Request()
        decoded_token = google.oauth2.id_token.verify_firebase_token(token, request_adapter)
        return decoded_token  # Return user details if valid
    except Exception as e:
        print("Token verification failed:", str(e))
        return None  # Return None if invalid

# ✅ Render the Teams Page with Dynamic Team Names
@app.get("/teams-page", response_class=HTMLResponse)
async def all_teams(request: Request, token: Optional[str] = Cookie(None)):
    user_token = verify_firebase_token(token) if token else None
    team_docs = db.collection("Teams").stream()
    
    teams = [doc.to_dict() for doc in team_docs]  # Extract full team data
    team_names = [doc.id for doc in db.collection("Teams").stream()]  # Extract only team names (Firestore document IDs)

    return templates.TemplateResponse("Teams.html", {
        "request": request,
        "user_token": user_token,
        "teams": teams,
        "team_names": team_names,  # Send only team names for dropdown
    })

# ✅ Get Attributes for a Selected Team
@app.get("/get-team-attributes/{team_name}", response_class=JSONResponse)
async def get_team_attributes(team_name: str):
    team_doc = db.collection("Teams").document(team_name).get()
    if not team_doc.exists:
        return JSONResponse(content={"attributes": []})

    attributes = list(team_doc.to_dict().keys())  # Extract field names
    return {"attributes": attributes}

# ✅ Filter Teams Based on User Selection
@app.get("/teams", response_class=JSONResponse)
async def filter_teams(
    team_name: Optional[str] = Query(None, description="Filter by team"),
    attribute: Optional[str] = Query(None, description="Attribute to filter"),
    comparison: Optional[str] = Query(None, description="Comparison operator (>, <, =)"),
    value: Optional[int] = Query(None, description="Value for comparison")
):
    teams_ref = db.collection("Teams")
    query = teams_ref

    if team_name and team_name != "Select Team Name":
        query = query.where("name", "==", team_name)

    if attribute and comparison and value is not None:
        if comparison == "Greater Than":
            query = query.where(attribute, ">", value)
        elif comparison == "Lesser Than":
            query = query.where(attribute, "<", value)
        elif comparison == "Equal to":
            query = query.where(attribute, "==", value)

    filtered_teams = [doc.to_dict() for doc in query.stream()]

    # Debugging Output
    print(f"Filter Applied: {attribute} {comparison} {value}")
    print("Filtered Results:", filtered_teams)

    return JSONResponse(content={"teams": filtered_teams})



@app.get("/team-profile", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("Team_Profile.html", {"request": request})

# ✅ DELETE endpoint to remove a team by name
@app.delete("/team/{team_name}")
async def delete_team(team_name: str, token: Optional[str] = Query(None)):
    # Verify token; user must be logged in
    user_token = verify_firebase_token(token) if token else None
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    team_ref = db.collection("Teams").document(team_name)
    team_doc = team_ref.get()
    if not team_doc.exists:
        raise HTTPException(status_code=404, detail="Team not found")

    team_ref.delete()
    return JSONResponse(content={"message": f"Team '{team_name}' deleted successfully"})








@app.post("/add-team")
async def add_driver(
    request: Request,
    token: Optional[str] = Cookie(None),  # 🔥 Get token from cookies
    full_name: str = Form(...),
    team_id: str = Form(...),
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

    # 🔥 Validate Firebase token
    if not token:
        return JSONResponse(status_code=401, content={"error": "Token missing. Please log in."})

    user_token = verify_firebase_token(token)
    if not user_token:
        return JSONResponse(status_code=401, content={"error": "Unauthorized user."})

    # 🔥 Validate team_id format
    if not re.match(r"^[a-zA-Z0-9_-]+$", team_id):
        return JSONResponse(status_code=400, content={"error": "Team ID must be alphanumeric."})

    try:
        team_ref = db.collection("Teams").document(full_name)
        team_exists = team_ref.get().exists  # Check if driver exists

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

        if team_exists:
            team_ref.update(team_data)
            message = "Driver profile updated successfully!"
        else:
            team_ref.set({"driver_id": team_id, **team_data})
            message = "Driver profile created successfully!"

        # 🔥 Return JSON response for AJAX requests
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JSONResponse(content={"message": message})

        return RedirectResponse(url="/teams-page", status_code=302)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Server error: {str(e)}"})

#--------------------------------------
@app.get("/team/{driverName}", response_class=JSONResponse)
async def get_driver(driverName: str):
    print(f"🔍 Checking Firestore for team: {driverName}")  # Debugging

    driver_ref = db.collection("Teams").document(driverName).get()

    if not driver_ref.exists:
        print(f"❌ Team {driverName} not found in Firestore")  # Debugging
        raise HTTPException(status_code=404, detail="Team not found")

    print(f"✅ Found Team: {driver_ref.to_dict()}")  # Debugging
    return driver_ref.to_dict()

########################################################


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
