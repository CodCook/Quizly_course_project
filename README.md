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

> _To be added after Week 13 deployment_

## Architecture Overview

> _To be added in Week 13_

---

## Setup Instructions

> _To be added after core development in Week 12_
