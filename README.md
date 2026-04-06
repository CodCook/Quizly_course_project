# Quizly 🎯
> AI-powered study assistant for university students — generate summaries, quizzes, and flashcards from any topic in seconds.

## What is Quizly?

Quizly is a web application that helps university students study smarter. A student enters any topic or pastes a block of text, and Quizly instantly generates an AI-powered summary, a set of quiz questions with answers, and flashcards for active recall practice. All sessions are saved so students can track what they've studied and revisit past quizzes. Quizly is built for students who need to cover material fast and retain it effectively.

---

## Features

| Feature | AI-Powered? | Description |
|---|---|---|
| Topic Summary | ✅ Yes (Gemini) | Enter a topic or paste text — get a clear, concise summary |
| Quiz Generator | ✅ Yes (Gemini) | Auto-generates 5 multiple-choice questions with correct answers |
| Flashcard Generator | ✅ Yes (Gemini) | Generates term/definition flashcard pairs from any topic |
| Study History | No | Saves past sessions to the database for review |
| Health Check Endpoint | No | `/health` endpoint for CI smoke tests and uptime monitoring |

---

## Tech Stack

| Layer | Technology | Justification |
|---|---|---|
| Backend | Python + FastAPI | Lightweight, async-ready, ideal for AI API integration |
| AI / LLM | Google Gemini 2.5 Flash | Provided by instructor; fast and capable for text generation |
| Database | Supabase (PostgreSQL) | Free tier, managed cloud DB, simple REST + Python client |
| Frontend | HTML + CSS + JavaScript | Keeps scope realistic for a 3-week build; no framework overhead |
| Containerization | Docker | Required; single Dockerfile in repo root |
| CI/CD | GitHub Actions | Required; runs on every push and PR to main |
| Cloud Deployment | Render.com | Simple deploy hook integration with GitHub Actions |

---

## Team

| Member | Role | Primary Ownership |
|---|---|---|
| **Mahgoub Mohamed** | AI Engineer + Backend Lead | FastAPI routes, Gemini API integration, prompt design, unit test suite |
| **Mazen** | Frontend Developer + DevOps | HTML/CSS/JS UI, GitHub Actions CI/CD pipeline, Dockerfile, Render deployment |
| **Freddy** | Database Engineer + Full-Stack Support | Supabase schema design, DB read/write integration, documentation, README |

---

## 3-Week Timeline

### Week 11 — Foundation & Proposal
- [ ] Project proposal submitted and approved by instructor
- [ ] Public GitHub repository created with project board and initial issues
- [ ] Supabase project provisioned and database connection tested
- [ ] FastAPI skeleton running locally with `/health` endpoint
- [ ] Dockerfile created — app builds and runs in a container
- [ ] Feature branches created; each member has at least one active branch

### Week 12 — Core Development & CI Pipeline
- [ ] All three AI features implemented end-to-end (summary, quiz, flashcards)
- [ ] Study session data saved to and retrieved from Supabase
- [ ] Unit test suite complete — minimum 12 tests covering routes and logic
- [ ] GitHub Actions CI pipeline running on every push and PR:
  - Installs dependencies
  - Runs linter
  - Runs full test suite
  - Builds Docker image
  - Smoke tests the `/health` endpoint
- [ ] All features merged to `main` via reviewed pull requests

### Week 13 — CD Pipeline, Deployment & Presentation Prep
- [ ] CD pipeline added: push to `main` triggers automatic deploy to Render.com
- [ ] Application live at a publicly accessible URL
- [ ] All AI features verified working on the live deployment
- [ ] Live CI/CD demo rehearsed end-to-end at least twice
- [ ] Presentation slides complete with speaking parts assigned
- [ ] All GitHub Issues closed; README updated with live URL and architecture overview

---

## Live URL

**Render Deployment:** https://quizly-whkk.onrender.com/

---

## Architecture Overview

Quizly uses a lightweight full-stack architecture designed for AI-assisted studying.

### Components

- **Frontend (HTML/CSS/JavaScript)**  
  Provides the user interface for entering topics, uploading study material, viewing generated results, and revisiting saved history.

- **Backend (FastAPI)**  
  Handles routing, request validation, file upload processing, text extraction, Gemini integration, and database communication.

- **AI Layer (Google Gemini 2.5 Flash)**  
  Generates:
  - concise summaries
  - multiple-choice quizzes
  - flashcards for active recall practice

- **Database (Supabase / PostgreSQL)**  
  Stores study sessions, including:
  - input text
  - generated summary
  - quiz data
  - flashcards
  - metadata such as timestamps and filenames

- **Containerization (Docker)**  
  Packages the application so it can run consistently in local development, CI, and deployment environments.

- **CI/CD (GitHub Actions + Render)**  
  GitHub Actions validates the application automatically on push and pull request. Docker build and container smoke tests are included in the pipeline. Render hosts the live deployed application.

### High-Level Flow

1. User enters a topic or uploads a study file  
2. FastAPI receives the request  
3. Text is extracted and processed if needed  
4. Gemini generates summary, quiz, and flashcards  
5. FastAPI saves the session to Supabase  
6. Results are returned to the frontend  
7. User can revisit saved study sessions later

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/CodCook/Quizly_course_project.git
cd Quizly_course_project
```

### 2. Create and activate a virtual environment

Windows (PowerShell):

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```
### 4. Create a .env file
```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY=your_supabase_publishable_key
GEMINI_API_KEY=your_gemini_api_key
```
### 5. Run the app (development)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
---
## Running the Test

Quizly uses pytest for automated testing.
Run the full test suite with:

```bash
python -m pytest
```
Run a specific test file with:

```bash
python -m pytest tests/test_upload.py
```
---
## Docker Instructions

Build the Docker image
```bash
docker build -t quizly .
```
Run the Docker container
```bash
docker run -p 8000:8000 quizly
```
Verify the running container
Open:

http://127.0.0.1:8000/
http://127.0.0.1:8000/health

---
## Docker Instructions
CI/CD Pipeline

Quizly uses GitHub Actions for CI and Render for deployment.

- CI
On every push and pull request, the pipeline:

checks out the code
installs dependencies
runs the full pytest suite
builds the Docker image
starts a container from the built image
performs a smoke test against the /health endpoint

- CD
After successful integration and deployment, the latest version of the application is available on Render at:

https://quizly-whkk.onrender.com/