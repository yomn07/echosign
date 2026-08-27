# EchoSign Backend

Backend infrastructure for **EchoSign**, an American Sign Language (ASL) translation and recognition platform.

The EchoSign backend is organized as a **Dockerized microservice architecture**. Each major responsibility is isolated into its own FastAPI service, while an API Gateway provides a unified HTTP entry point for the frontend.

The backend currently includes:

* Authentication and user management
* Email verification
* Forgot-password and password-reset flows
* JWT authentication
* Guest trial management
* Redis-backed trial persistence
* English-to-ASL gloss translation
* ASL sign recognition
* ASL alphabet recognition
* MediaPipe landmark extraction
* ML model inference
* PostgreSQL persistence
* WebSocket-based real-time recognition
* Docker-based service orchestration

---

## Table of Contents

* [Overview](#overview)
* [Architecture](#architecture)
* [Services](#services)
* [Technology Stack](#technology-stack)
* [Project Structure](#project-structure)
* [Docker Architecture](#docker-architecture)
* [Authentication](#authentication)
* [Trial System](#trial-system)
* [Translation Service](#translation-service)
* [Sign Recognition Service](#sign-recognition-service)
* [Machine Learning Assets](#machine-learning-assets)
* [Preprocessing](#preprocessing)
* [Data](#data)
* [Database](#database)
* [Redis](#redis)
* [Email](#email)
* [WebSockets](#websockets)
* [Environment Variables](#environment-variables)
* [Running the Backend](#running-the-backend)
* [API Documentation](#api-documentation)
* [Testing](#testing)
* [Troubleshooting](#troubleshooting)

---

# Overview

EchoSign uses a service-oriented backend where each service is responsible for a specific domain.

The frontend does not need to communicate directly with every backend container. Instead, requests are normally sent through the **API Gateway**.

```text
                         ┌─────────────────────┐
                         │   EchoSign Frontend  │
                         │      React/Vite      │
                         └──────────┬──────────┘
                                    │
                                    │ HTTP / WebSocket
                                    ▼
                         ┌─────────────────────┐
                         │     API Gateway     │
                         │       FastAPI       │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
       │ Auth        │       │ Translation │       │ Trial       │
       │ Service     │       │ Service     │       │ Service     │
       │ :8001       │       │ :8003       │       │ :8004       │
       └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
              │                     │                     │
              ▼                     ▼                     ▼
        PostgreSQL             Translation             Redis
              │                   Model
              │
              ▼
       Email / SMTP


                         ┌─────────────────────┐
                         │    Sign Service     │
                         │       :8002         │
                         └──────────┬──────────┘
                                    │
                   ┌────────────────┼────────────────┐
                   │                │                │
                   ▼                ▼                ▼
                Models       Preprocessing         Data
```

---

# Architecture

The backend is divided into five primary application containers:

| Service             |   Port | Responsibility                                         |
| ------------------- | -----: | ------------------------------------------------------ |
| API Gateway         | `8000` | Unified API entry point and request routing            |
| Auth Service        | `8001` | Authentication, users, verification and password reset |
| Sign Service        | `8002` | ASL sign/alphabet recognition and ML inference         |
| Translation Service | `8003` | English → ASL gloss translation                        |
| Trial Service       | `8004` | Guest trial management                                 |
| Redis               | `6379` | Trial state and temporary data                         |
| PostgreSQL          | `5432` | Persistent application data                            |
| Frontend/Nginx      | `8080` | React frontend and reverse proxy                       |

The public browser entry point is:

```text
http://localhost:8080
```

The frontend communicates with the gateway through:

```text
/api/...
```

The gateway then forwards requests to the appropriate internal service.

---

# Services

## API Gateway

The gateway is responsible for routing requests between the frontend and backend services.

Typical responsibilities include:

* Authentication routing
* Trial routing
* Translation routing
* Sign-service routing
* WebSocket routing
* Forwarding HTTP headers
* Forwarding request bodies
* Forwarding query parameters
* Preserving authentication information
* Forwarding cookies and `Set-Cookie` headers

The gateway prevents the browser from needing to know the internal Docker service names.

Example:

```text
Browser
   │
   │ POST /api/trial/consume
   ▼
Gateway :8000
   │
   │ POST /trial/consume
   ▼
Trial Service :8004
```

---

# Auth Service

The authentication service manages user accounts and authentication-related operations.

Responsibilities include:

* User registration
* Login
* Password hashing
* JWT generation
* JWT validation
* Email verification
* Verification-token expiration
* Forgot-password requests
* Password reset
* Password-reset token expiration
* Password-reset token hashing

The authentication service communicates with PostgreSQL for persistent user data and the email service/SMTP provider for verification and password-reset emails.

---

# Sign Service

The sign service performs machine-learning inference for ASL.

It is responsible for:

* ASL alphabet recognition
* Sign recognition
* Landmark processing
* Video/frame processing
* MediaPipe extraction
* TFLite/LiteRT inference
* PyTorch inference
* Confidence calculation
* Prediction results
* WebSocket-based real-time inference

The service uses three external project directories mounted into the container:

```text
models/
preprocessing/
data/
```

These are mounted by Docker Compose.

Inside the container they are available as:

```text
/app/models
/app/preprocessing
/app/data
```

---

# Translation Service

The translation service converts English text into ASL gloss.

The frontend translation pipeline is:

```text
User language
     │
     ▼
Puter AI
     │
     ▼
English
     │
     ▼
Translation Service
     │
     ▼
ASL Gloss
     │
     ▼
LandmarkPlayer
     │
     ▼
ASL Sign / Fingerspelling
```

For English input:

```text
English → ASL Gloss
```

For another supported language:

```text
French / Arabic / Spanish / German / Italian /
Portuguese / Turkish
        │
        ▼
      English
        │
        ▼
      ASL Gloss
```

The frontend currently uses Puter AI to convert non-English input into natural English before sending the English text to the translation service.

The translation service exposes the `/translate` endpoint.

---

# Trial Service

The trial service provides guest users with a limited number of free operations.

The current limit is:

```text
5 trials
```

Trial state is stored in Redis and identified by a secure browser cookie:

```text
echosign_trial_id
```

The trial flow is:

```text
Browser
   │
   │ GET /api/trial/status
   ▼
API Gateway
   │
   ▼
Trial Service
   │
   ├── Read echosign_trial_id
   │
   ▼
Redis
```

When the browser has no trial cookie, the trial service creates one.

Example:

```text
echosign_trial_id = random secure identifier
```

The Redis key is:

```text
echosign:trial:<trial_id>
```

The initial value is:

```text
5
```

Every successful consumption decrements the counter atomically.

Example:

```text
5 → 4 → 3 → 2 → 1 → 0
```

Once the value reaches zero, the API returns:

```json
{
  "requires_login": true
}
```

Authenticated users bypass the guest trial restriction.

---

# Machine Learning Assets

The ML assets used by the sign service are stored outside the service source code.

The project contains:

```text
models/
├── best_asl_mid26_lex_raw_Dis256(3).tflite
├── label_encoder.pkl
└── scaler.pkl
```

These files are mounted into the sign-service container:

```yaml
volumes:
  - ./models:/app/models
```

Therefore:

```text
Host:
./models

Container:
/app/models
```

The model files do not have to be copied into the Docker image during development.

This allows models to be replaced or updated without rebuilding the entire Docker image.

---

# Preprocessing

The preprocessing pipeline is kept separately from the sign-service source code.

Project directory:

```text
preprocessing/
```

Docker mount:

```yaml
volumes:
  - ./preprocessing:/app/preprocessing
```

Container path:

```text
/app/preprocessing
```

Preprocessing may include:

* Landmark normalization
* Coordinate transformation
* Feature extraction
* Frame preparation
* Sequence preparation
* Scaling
* Feature formatting

The exact preprocessing pipeline depends on the model being used.

---

# Data

The project also contains a dedicated data directory:

```text
data/
```

Docker Compose mounts it into the sign service:

```yaml
volumes:
  - ./data:/app/data
```

Inside the container:

```text
/app/data
```

This directory can contain datasets, processed samples, temporary inference data, or other ML-related resources required by the sign service.

The exact contents should be kept separate from the application source code.

---

# Sign Recognition Pipeline

The sign-recognition pipeline can be represented as:

```text
Camera / Video
      │
      ▼
Video Frames
      │
      ▼
OpenCV
      │
      ▼
MediaPipe
      │
      ├── Hands
      │
      └── Pose
      │
      ▼
Landmarks
      │
      ▼
Preprocessing
      │
      ▼
Feature Extraction
      │
      ▼
ML Model
      │
      ▼
Prediction
      │
      ▼
Gloss / Sign Label
      │
      ▼
Frontend
```

Depending on the recognition task, different models and preprocessing pipelines can be used.

---

# ASL Alphabet Recognition

The alphabet recognition pipeline processes individual hand signs.

Typical pipeline:

```text
Camera
  │
  ▼
OpenCV
  │
  ▼
MediaPipe Hands
  │
  ▼
Landmark Extraction
  │
  ▼
Normalization
  │
  ▼
Scaler
  │
  ▼
TFLite / LiteRT Model
  │
  ▼
Label Encoder
  │
  ▼
ASL Letter
```

The resulting letter can be streamed to the frontend through WebSockets.

---

# Sign Language Recognition

Full-sign recognition works with sequences rather than individual letters.

Typical pipeline:

```text
Video Frames
     │
     ▼
MediaPipe Hands + Pose
     │
     ▼
Landmark Sequence
     │
     ▼
Preprocessing
     │
     ▼
Motion / Temporal Features
     │
     ▼
PyTorch Model
     │
     ▼
Prediction
     │
     ▼
Gloss
```

The service can return:

* Predicted sign
* Confidence score
* Top-K predictions
* Landmark information

---

# Database

EchoSign uses PostgreSQL for persistent application data.

The database is intended for data such as:

* Users
* Password hashes
* Email verification state
* Verification tokens
* Password-reset state
* Application metadata
* Stored landmarks where applicable

SQLAlchemy is used as the ORM.

Typical architecture:

```text
Auth Service
     │
     ▼
SQLAlchemy
     │
     ▼
PostgreSQL
```

Redis is deliberately used for temporary/short-lived state such as guest trials rather than replacing PostgreSQL.

---

# Redis

Redis is used primarily by the trial service.

Docker Compose provides Redis as:

```text
redis:7-alpine
```

Container:

```text
echosign-redis
```

Port:

```text
6379
```

The trial service connects to Redis using the Docker service hostname:

```text
redis
```

not:

```text
localhost
```

This distinction is important because `localhost` inside a container refers to that same container.

---

# Email Service

The authentication system uses email delivery for:

* Email verification
* Forgot-password requests
* Password-reset links

The email flow is:

```text
Frontend
   │
   ▼
Auth Service
   │
   ▼
Email Service / SMTP
   │
   ▼
User Email
```

Verification and reset tokens should be short-lived and securely generated.

Sensitive tokens should not be stored in plaintext when persistent token storage is required.

---

# WebSockets

EchoSign uses WebSockets for real-time sign-recognition features.

WebSockets are appropriate for continuous camera/video communication because the frontend can maintain a persistent connection rather than repeatedly creating HTTP requests.

Typical flow:

```text
React Frontend
      │
      │ WebSocket
      ▼
API Gateway
      │
      ▼
Sign Service
      │
      ▼
ML Pipeline
      │
      ▼
Prediction
      │
      ▼
WebSocket
      │
      ▼
React Frontend
```

---

# Project Structure

The backend follows the Dockerized service structure rather than the previous monolithic `backend/main.py` structure.

A simplified project layout is:

```text
EchoSign/
│
├── docker-compose.yml
├── .env
│
├── backend/
│   │
│   ├── gateway/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── ...
│   │
│   └── service/
│       │
│       ├── auth_service/
│       │   ├── Dockerfile
│       │   ├── main.py
│       │   ├── requirements.txt
│       │   └── ...
│       │
│       ├── sign_service/
│       │   ├── Dockerfile
│       │   ├── main.py
│       │   ├── requirements.txt
│       │   └── ...
│       │
│       ├── translation_service/
│       │   ├── Dockerfile
│       │   ├── main.py
│       │   ├── requirements.txt
│       │   └── ...
│       │
│       └── trial_service/
│           ├── Dockerfile
│           ├── main.py
│           ├── trial.py
│           ├── config.py
│           ├── redis_client.py
│           ├── security.py
│           ├── requirements.txt
│           └── ...
│
├── models/
│   ├── *.tflite
│   ├── scaler.pkl
│   └── label_encoder.pkl
│
├── preprocessing/
│   └── ...
│
├── data/
│   └── ...
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── ...
```

The exact files may change as individual services evolve.

---

# Docker Architecture

All backend services run on the Docker Compose network.

Conceptually:

```text
                    Docker Compose Network
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   API Gateway        Auth Service       Trial Service
     :8000               :8001               :8004
        │                  │                  │
        │                  ▼                  ▼
        │              PostgreSQL           Redis
        │
        ├──────────────► Sign Service
        │                   :8002
        │                     │
        │                     ├── /app/models
        │                     ├── /app/preprocessing
        │                     └── /app/data
        │
        └──────────────► Translation Service
                            :8003
```

Docker provides service-to-service DNS automatically.

For example:

```text
http://trial-service:8004
```

is used from the gateway to reach the trial service.

---

# Environment Variables

Configuration should be provided through `.env` and Docker Compose.

Typical variables include:

```text
DATABASE_URL
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD

REDIS_HOST
REDIS_PORT

JWT_SECRET
JWT_ALGORITHM

SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
SMTP_FROM

TRIAL_LIMIT
TRIAL_TTL_SECONDS
```

Secrets should never be committed to Git.

A `.env.example` file should be maintained for development.

---

# Running the Backend

From the project root:

```powershell
docker compose up -d --build
```

Check running containers:

```powershell
docker compose ps
```

View all logs:

```powershell
docker compose logs
```

View a specific service:

```powershell
docker compose logs auth-service
```

```powershell
docker compose logs sign-service
```

```powershell
docker compose logs translation-service
```

```powershell
docker compose logs trial-service
```

Follow logs:

```powershell
docker compose logs -f trial-service
```

Stop the backend:

```powershell
docker compose down
```

Rebuild:

```powershell
docker compose build
```

Restart:

```powershell
docker compose restart
```

---

# API Documentation

FastAPI automatically provides interactive API documentation.

For individual services, when their ports are exposed:

```text
http://localhost:8001/docs
http://localhost:8002/docs
http://localhost:8003/docs
http://localhost:8004/docs
```

The frontend normally communicates through the gateway instead of directly accessing these ports.

---

# Trial API

The gateway exposes:

```text
GET /api/trial/status
POST /api/trial/consume
```

Example status response:

```json
{
  "authenticated": false,
  "trial_used": true,
  "trials_remaining": 4,
  "requires_login": false
}
```

The trial cookie is:

```text
echosign_trial_id
```

The cookie is HTTP-only and persists independently of frontend React state.

This means refreshing the page should **not reset the trial counter**.

The source of truth is Redis, not the frontend.

---

# Translation API

The translation service exposes:

```text
POST /translate
```

Example request:

```json
{
  "text": "HELLO HOW ARE YOU"
}
```

Example response:

```json
{
  "gloss": "HELLO HOW YOU"
}
```

The frontend then converts the gloss into individual words and displays either:

* A complete sign animation when the word exists in the sign dictionary
* Fingerspelling when the word does not have a dedicated sign

---

# Authentication Flow

Registration:

```text
Frontend
   │
   ▼
API Gateway
   │
   ▼
Auth Service
   │
   ▼
PostgreSQL
   │
   ▼
Verification Email
```

Login:

```text
Frontend
   │
   ▼
Auth Service
   │
   ▼
JWT
   │
   ▼
Frontend
```

Authenticated API requests include:

```text
Authorization: Bearer <token>
```

---

# Forgot Password Flow

The password-reset flow is:

```text
User
 │
 │ Forgot password
 ▼
Frontend
 │
 ▼
Auth Service
 │
 ▼
Generate reset token
 │
 ▼
Send email
 │
 ▼
User clicks reset link
 │
 ▼
Frontend reset page
 │
 ▼
Auth Service
 │
 ▼
Update password
```

Reset tokens should be:

* Random
* Short-lived
* Single-use
* Stored securely

---

# Security

Important security practices include:

* Password hashing with bcrypt
* JWT authentication
* Secure random trial identifiers
* HTTP-only trial cookies
* Expiring verification tokens
* Expiring password-reset tokens
* Password-reset token hashing
* Input validation with Pydantic
* CORS configuration
* Environment-based secrets
* No hardcoded production credentials

For production deployments, HTTPS should be used so that cookies and authentication tokens are protected in transit.

---

# Development Notes

## Docker Hostnames

Inside Docker, services should communicate using Compose service names.

Correct:

```text
http://trial-service:8004
```

Incorrect from inside another container:

```text
http://localhost:8004
```

`localhost` refers to the current container.

---

## ML Volume Mounts

The sign service uses:

```yaml
volumes:
  - ./models:/app/models
  - ./preprocessing:/app/preprocessing
  - ./data:/app/data
```

Therefore the ML resources are available at runtime:

```text
/app/models
/app/preprocessing
/app/data
```

They are **not necessarily copied into the Docker image**.

This is intentional and is useful during development because models and datasets can be updated without rebuilding the image.

---

# Troubleshooting

## Trial always starts at 5

Check whether the browser is sending:

```text
echosign_trial_id
```

Then check Redis.

The trial counter should exist under:

```text
echosign:trial:<trial_id>
```

If the cookie is missing, the service creates a new trial identity.

---

## Trial POST returns 500

Check:

```powershell
docker compose logs trial-service --tail=100
```

The trial endpoint must call:

```python
consume_trial(trial_id)
```

rather than passing the FastAPI `Request` and `Response` objects to the lower-level Redis function.

---

## Cookie is not being persisted

The gateway must forward the backend's `Set-Cookie` response header.

The request flow is:

```text
Browser
   │
   ▼
Gateway
   │
   ▼
Trial Service
   │
   │ Set-Cookie: echosign_trial_id=...
   ▼
Gateway
   │
   │ Set-Cookie: echosign_trial_id=...
   ▼
Browser
```

If the gateway consumes the `Set-Cookie` header instead of forwarding it, the browser will never persist the trial identifier.

---

## Check Redis

Enter the Redis container:

```powershell
docker compose exec redis redis-cli
```

Then:

```text
KEYS echosign:trial:*
```

Inspect a trial:

```text
GET echosign:trial:<trial_id>
```

Check expiration:

```text
TTL echosign:trial:<trial_id>
```

---

## Check Sign-Service ML Files

Run:

```powershell
docker compose exec sign-service sh
```

Then:

```sh
ls -lah /app/models
ls -lah /app/preprocessing
ls -lah /app/data
```

The expected structure is:

```text
/app/
├── models/
├── preprocessing/
├── data/
└── sign_service/
```

---

# Backend Request Flow

A normal REST request follows:

```text
React
 │
 ▼
Nginx / Frontend Container
 │
 ▼
API Gateway :8000
 │
 ├── Auth ───────────────► Auth Service :8001
 │
 ├── Translation ────────► Translation Service :8003
 │
 ├── Trial ──────────────► Trial Service :8004
 │
 └── Sign ───────────────► Sign Service :8002
```

Persistent and temporary storage:

```text
Auth Service
     │
     ▼
PostgreSQL

Trial Service
     │
     ▼
Redis

Sign Service
     │
     ├── Models
     ├── Preprocessing
     └── Data
```

---

# Complete Backend Architecture

The complete EchoSign system can therefore be summarized as:

```text
                         ┌─────────────────────┐
                         │      Browser        │
                         │    React Frontend   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Nginx :8080      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  API Gateway :8000  │
                         └──────────┬──────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
 ┌────────────────┐       ┌────────────────┐       ┌────────────────┐
 │ Auth Service   │       │ Sign Service   │       │ Translation    │
 │     :8001      │       │     :8002      │       │ Service :8003  │
 └───────┬────────┘       └───────┬────────┘       └────────────────┘
         │                         │
         ▼                         ├── models/
 ┌────────────────┐                ├── preprocessing/
 │  PostgreSQL    │                └── data/
 └────────────────┘
         
                         ┌────────────────┐
                         │ Trial Service  │
                         │     :8004      │
                         └───────┬────────┘
                                 │
                                 ▼
                         ┌────────────────┐
                         │     Redis      │
                         │     :6379      │
                         └────────────────┘
```

This architecture keeps authentication, ML inference, translation, and guest-trial management independent while allowing the frontend to interact with the backend through a single gateway.

---

# Summary

EchoSign's backend is a Dockerized FastAPI microservice system consisting of:

* **API Gateway** — unified routing and cookie/header forwarding
* **Auth Service** — users, login, verification and password reset
* **Sign Service** — ASL ML inference
* **Translation Service** — English-to-ASL gloss translation
* **Trial Service** — persistent guest trial management
* **PostgreSQL** — persistent application database
* **Redis** — guest-trial state
* **SMTP/Email** — verification and password-reset messages
* **Models** — ML inference assets
* **Preprocessing** — ML feature preparation
* **Data** — ML/data resources

The entire backend can be started through Docker Compose, allowing the individual services and their dependencies to run as one integrated EchoSign platform.
