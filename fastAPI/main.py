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


# Initialize FastAPI App
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service_account_path = r"dbcc-adc89-firebase-adminsdk-fbsvc-38636a5989.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path

# Firestore Database
# db = firestore.Client(project="fastapiproject-19c47")
db = firestore.Client()


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Verify Firebase Token using Google API
def verify_firebase_token(token: str):
    try:
        request_adapter = google.auth.transport.requests.Request()
        decoded_token = google.oauth2.id_token.verify_firebase_token(token, request_adapter)
        return decoded_token  # Return user details if valid
    except Exception as e:
        print(" Token verification failed:", str(e))
        return None  # Return None if invalid


#  Render Homepage
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})


# Render Login Page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, token: Optional[str] = Query(None)):
    user_token = verify_firebase_token(token) if token else None
    return templates.TemplateResponse("lg.html", {"request": request, "user_token": user_token})

# Page Rendering Route 
@app.get("/drivers-page")
async def render_drivers_page(request: Request, token: Optional[str] = Cookie(None)):
    return templates.TemplateResponse("Drivers1.html", {"request": request, "user_token": token})



# Add New Driver
@app.post("/add-driver")
async def add_driver(
    request: Request,
    token: str = Form(...),
    name: str = Form(...),
    age: int = Form(...),
    total_pole: int = Form(...),
    total_wins: int = Form(...),
    total_points: int = Form(...),
    total_titles: int = Form(...),
    total_fastest_laps: int = Form(...),
    team: str = Form(...),
):
    user_token = verify_firebase_token(token)
    if not user_token:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)

    # Prevent duplicate drivers
    existing = db.collection("drivers").where("name", "==", name).stream()
    if any(existing):
        return JSONResponse(content={"error": "Driver already exists"}, status_code=400)

    driver_data = {
        "name": name,
        "age": age,
        "total_pole": total_pole,
        "total_wins": total_wins,
        "total_points": total_points,
        "total_titles": total_titles,
        "total_fastest_laps": total_fastest_laps,
        "team": team,
    }
    db.collection("drivers").document(name).set(driver_data)
    return JSONResponse(content={"message": "Driver added successfully"})


# Get Driver Profile
@app.get("/driver/{driver_name}", response_class=HTMLResponse)
async def driver_profile(request: Request, driver_name: str, token: Optional[str] = Query(None)):
    user_token = verify_firebase_token(token) if token else None
    driver_doc = db.collection("drivers").document(driver_name).get()

    if not driver_doc.exists:
        raise HTTPException(status_code=404, detail="Driver not found")

    return templates.TemplateResponse("driver_profile.html", {
        "request": request,
        "driver": driver_doc.to_dict(),
        "user_token": user_token,
    })


#  Get Team Profile
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


# Compare Two Drivers
@app.post("/compare-drivers", response_class=HTMLResponse)
async def compare_drivers(
    request: Request,
    token: str = Form(...),
    driver1: str = Form(...),
    driver2: str = Form(...),
):
    user_token = verify_firebase_token(token)
    if not user_token:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)

    driver_doc1 = db.collection("drivers").document(driver1).get()
    driver_doc2 = db.collection("drivers").document(driver2).get()

    if not driver_doc1.exists or not driver_doc2.exists:
        raise HTTPException(status_code=404, detail="One or both drivers not found")

    d1, d2 = driver_doc1.to_dict(), driver_doc2.to_dict()

    comparison = {}
    stats = ["age", "total_pole", "total_wins", "total_points", "total_titles", "total_fastest_laps"]

    for stat in stats:
        val1, val2 = d1.get(stat), d2.get(stat)
        if stat == "age":
            better = driver1 if val1 < val2 else driver2
        else:
            better = driver1 if val1 > val2 else driver2
        comparison[stat] = {"driver1": val1, "driver2": val2, "better": better}

    return templates.TemplateResponse("compare_drivers.html", {
        "request": request,
        "comparison": comparison,
        "driver1": d1,
        "driver2": d2,
        "user_token": user_token,
    })


@app.get("/compare-drivers", response_class=HTMLResponse)
async def compare_drivers_form(request: Request):
    token = request.cookies.get("token")
    user = verify_firebase_token(token) if token else None
    drivers = db.collection("drivers").stream()
    driver_list = [driver.to_dict() for driver in drivers]
    return templates.TemplateResponse("compare_drivers.html", {"request": request, "drivers": driver_list, "user": user})

@app.post("/compare-drivers", response_class=HTMLResponse)
async def compare_drivers(request: Request, driver1: str = Form(...), driver2: str = Form(...)):
    token = request.cookies.get("token")
    user = verify_firebase_token(token) if token else None
    driver_doc1 = db.collection("drivers").document(driver1).get()
    driver_doc2 = db.collection("drivers").document(driver2).get()
    if not driver_doc1.exists or not driver_doc2.exists:
        raise HTTPException(status_code=404, detail="One or both drivers not found")
    d1 = driver_doc1.to_dict()
    d2 = driver_doc2.to_dict()

   
    comparison = {}
    stats = ["age", "total_pole", "total_wins", "total_points", "total_titles", "total_fastest_laps"]
    for stat in stats:
        val1 = d1.get(stat)
        val2 = d2.get(stat)
        if stat == "age":
            better = driver1 if val1 < val2 else driver2
        else:
            better = driver1 if val1 > val2 else driver2
        comparison[stat] = {"driver1": val1, "driver2": val2, "better": better}

    return templates.TemplateResponse("compare_drivers.html", {
        "request": request,
        "comparison": comparison,
        "driver1": d1,
        "driver2": d2,
        "user": user
    })



# Mock Driver Database
drivers_db = [
    {"id": 1, "name": "Max Verstappen", "age": 26, "points_scored": 2500, "wins": 60, "poles": 35, "titles": 3, "team": "Red Bull"},
    {"id": 2, "name": "Lewis Hamilton", "age": 39, "points_scored": 4300, "wins": 103, "poles": 104, "titles": 7, "team": "Mercedes"},
    {"id": 3, "name": "Charles Leclerc", "age": 26, "points_scored": 1200, "wins": 5, "poles": 20, "titles": 0, "team": "Ferrari"},
    {"id": 4, "name": "Lando Norris", "age": 24, "points_scored": 800, "wins": 1, "poles": 3, "titles": 0, "team": "McLaren"},
]

@app.get("/drivers", response_class=JSONResponse)
async def get_drivers(
    driver_id: Optional[int] = Query(None, description="Filter by driver ID"),
    attribute: Optional[str] = Query(None, description="Filter attribute (age, wins, points_scored)"),
    comparison: Optional[str] = Query(None, description="Comparison operator (>, <, =)"),
    value: Optional[int] = Query(None, description="Value for comparison")
):
    results = drivers_db

    # Filter by driver ID
    if driver_id is not None:
        results = [d for d in results if d["id"] == driver_id]

    # Apply attribute-based filtering
    if attribute and comparison and value is not None:
        if attribute not in ["age", "wins", "points_scored"]:
            return {"error": "Invalid attribute"}

        if comparison == ">":
            results = [d for d in results if d[attribute] > value]
        elif comparison == "<":
            results = [d for d in results if d[attribute] < value]
        elif comparison == "=":
            results = [d for d in results if d[attribute] == value]
        else:
            return {"error": "Invalid comparison operator"}

    return JSONResponse(content={"data": results}) 



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
