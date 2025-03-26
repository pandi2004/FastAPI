from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from google.cloud import firestore
# import firebase_admin
# from firebase_admin import credentials, auth
import google.oauth2.id_token
from google.auth.transport import requests

firebase_request_adapter = requests.Request()

# Set paths (Windows specific)
# service_account_path = "firstapp78-firebase-adminsdk-fbsvc-e08994c4fc.json"
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path

# Initialize Firebase
# firebase_cred = credentials.Certificate(service_account_path)
# firebase_admin.initialize_app(firebase_cred)

# Initialize Firestore with explicit project ID
db = firestore.Client(project="firstapp78")

app = FastAPI()

# Mount static files (for CSS and JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# @app.get("/",response_class=HTMLResponse)
# async def root (request: Request):
#     return templates.TemplateResponse('main.html',{'request': request, 'name': 'John Doe', 'number':'12345'})

def verify_firebase_token(token: str):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        return None
    
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("lg.html", {"request": request})

# Route to handle the login logic
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    # Normally, you'd authenticate the user with Firebase, 
    # but for now, let's assume we have the Firebase ID token after successful login.
    # You would get the token using Firebase Authentication client on the frontend.

    # Simulating the token from Firebase (In real-world, you should get it from the frontend)
    token = token

    # Verify the Firebase token
    user = verify_firebase_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Extract email from the decoded token
    user_email = user.get("email")

    # You can fetch user data from Firestore if needed
    user_data = db.collection("users").document(user_email).get()

    if user_data.exists:
        # Create a response and set an HTTP-only cookie with the token for session management
        response = HTMLResponse(f"Welcome, {user_email}! You are now logged in.")
        response.set_cookie(key="token", value=token, httponly=True)  # Store the token in a secure cookie
        return response
    else:
        return JSONResponse({"message": "User not found in Firestore"}, status_code=404)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, email:str = Form(...), password: str = Form(...)):
    token = request.cookies.get("token")
    user = verify_firebase_token(token) if token else None
    if user:
        email = user.get("email")  # Extract email from decoded token
    else:
        email = None

    # Retrieve drivers and teams from Firestore.
    drivers = db.collection("drivers").stream()
    teams = db.collection("teams").stream()
    driver_list = [driver.to_dict() for driver in drivers]
    team_list = [team.to_dict() for team in teams]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "email": email,
        "drivers": driver_list,
        "teams": team_list
    })

@app.get("/add-driver", response_class=HTMLResponse)
async def add_driver_form(request: Request):
    token = request.cookies.get("token")
    user = verify_firebase_token(token) if token else None
    if not user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("add_driver.html", {"request": request})

@app.post("/add-driver")
async def add_driver(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    total_pole: int = Form(...),
    total_wins: int = Form(...),
    total_points: int = Form(...),
    total_titles: int = Form(...),
    total_fastest_laps: int = Form(...),
    team: str = Form(...)
):
    token = request.cookies.get("token")
    user = verify_firebase_token(token) if token else None
    if not user:
        return RedirectResponse("/", status_code=302)

    # Prevent duplicate driver names.
    existing = db.collection("drivers").where("name", "==", name).stream()
    if any(existing):
        raise HTTPException(status_code=400, detail="Driver already exists")

    driver_data = {
        "name": name,
        "age": age,
        "total_pole": total_pole,
        "total_wins": total_wins,
        "total_points": total_points,
        "total_titles": total_titles,
        "total_fastest_laps": total_fastest_laps,
        "team": team
    }
    db.collection("drivers").document(name).set(driver_data)
    return RedirectResponse("/", status_code=302)

@app.get("/add-team", response_class=HTMLResponse)
async def add_team_form(request: Request):
    token = request.cookies.get("token")
    user = verify_firebase_token(token) if token else None
    if not user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("add_team.html", {"request": request})

@app.post("/add-team")
async def add_team(
    request: Request,
    name: str = Form(...),
    year_founded: int = Form(...),
    total_pole: int = Form(...),
    total_wins: int = Form(...),
    total_titles: int = Form(...),
    finishing_position: int = Form(...)
):
    token = request.cookies.get("token")
    user = verify_firebase_token(token) if token else None
    if not user:
        return RedirectResponse("/", status_code=302)

    # Prevent duplicate team names.
    existing = db.collection("teams").where("name", "==", name).stream()
    if any(existing):
        raise HTTPException(status_code=400, detail="Team already exists")

    team_data = {
        "name": name,
        "year_founded": year_founded,
        "total_pole": total_pole,
        "total_wins": total_wins,
        "total_titles": total_titles,
        "finishing_position": finishing_position
    }
    db.collection("teams").document(name).set(team_data)
    return RedirectResponse("/", status_code=302)

@app.get("/driver/{driver_name}", response_class=HTMLResponse)
async def driver_profile(request: Request, driver_name: str):
    token = request.cookies.get("token")
    user = verify_firebase_token(token) if token else None
    driver_doc = db.collection("drivers").document(driver_name).get()
    if not driver_doc.exists:
        raise HTTPException(status_code=404, detail="Driver not found")
    driver_data = driver_doc.to_dict()
    return templates.TemplateResponse("driver_profile.html", {"request": request, "driver": driver_data, "user": user})

@app.get("/team/{team_name}", response_class=HTMLResponse)
async def team_profile(request: Request, team_name: str):
    token = request.cookies.get("token")
    user = verify_firebase_token(token) if token else None
    team_doc = db.collection("teams").document(team_name).get()
    if not team_doc.exists:
        raise HTTPException(status_code=404, detail="Team not found")
    team_data = team_doc.to_dict()
    return templates.TemplateResponse("team_profile.html", {"request": request, "team": team_data, "user": user})

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

    # For each stat compare and determine which driver is better.
    # For age, a lower number is better; for all other stats, the higher value is better.
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
