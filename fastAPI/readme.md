# Formula F1 FastAPI Application

## Overview

The Formula F1 FastAPI Application is a web platform designed to display, search, filter, and compare information about Formula 1 drivers and teams. It leverages FastAPI for backend operations, Firebase (Firestore and Authentication) for secure data storage and user validation, and Google App Engine for hosting.

## Project Structure

- **main.py**: Contain API endpoints for drivers and teams respectively.
- **templates/**: Jinja2 HTML templates for rendering dynamic pages.
- **static/**: Contains CSS, JavaScript, and image assets.
- **app.yaml**: Configuration for Google App Engine.
- **requirements.txt**: Lists project dependencies.

## Key Features

- **Drivers Module**: List, filter, search, compare, and view detailed profiles of drivers.
- **Teams Module**: Similar functionalities for teams, including comparison and detailed profiles.
- **User Authentication**: Secured via Firebase Authentication.
- **Cloud Deployment**: Hosted on Google App Engine for automatic scaling and high availability.

## Installation & Deployment Steps

1. Clone the repository and navigate to the project folder.
   
2. Create and activate a virtual environment:
    ```bash
    python -m venv venv # Create a virtual environment
    venv\Scripts\activate # Activate the virtual environment
    deactivate # Deactivate the virtual environment
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the Firebase JSON file.

5. Run locally with:
    ```bash
    uvicorn main:app --reload
    ```

6. Deploy to Google App Engine using:
    ```bash
    gcloud auth login
    gcloud config set project YOUR_PROJECT_ID
    gcloud app deploy
    gcloud app browse
    ```

## Usage

- **Drivers and Teams Pages**: Use the provided search forms to filter and compare records.
- **Profile Pages**: Click on any record to view detailed information.
- **Reset Functionality**: Reset filters to view all records.

[Google App Engine hosted link](https://fastapiproject-19c47.nw.r.appspot.com/)