# EchoSign

<p align="center">
  <strong>AI-Powered Multilingual Text-to-ASL Translation Platform</strong>
</p>

<p align="center">
  EchoSign translates natural language into American Sign Language (ASL) gloss
  and presents the result through an interactive signing interface.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Frontend-React%20%2F%20TypeScript-61DAFB?style=for-the-badge" alt="Frontend">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge" alt="Backend">
  <img src="https://img.shields.io/badge/AI-Puter%20AI-6C47FF?style=for-the-badge" alt="AI">
  <img src="https://img.shields.io/badge/Deployment-Docker-2496ED?style=for-the-badge" alt="Docker">
</p>

---

# Table of Contents

* [Overview](#overview)
* [Key Features](#key-features)
* [System Architecture](#system-architecture)
* [Translation Pipeline](#translation-pipeline)
* [Docker Architecture](#docker-architecture)
* [Technology Stack](#technology-stack)
* [Project Structure](#project-structure)
* [Dataset](#dataset)
* [Machine Learning](#machine-learning)
* [Requirements](#requirements)
* [Clone the Repository](#clone-the-repository)
* [Environment Configuration](#environment-configuration)
* [PostgreSQL Configuration](#postgresql-configuration)
* [Docker Setup](#docker-setup)
* [Starting EchoSign](#starting-echosign)
* [Checking Containers](#checking-containers)
* [Accessing the Application](#accessing-the-application)
* [API Gateway](#api-gateway)
* [Authentication](#authentication)
* [Translation Service](#translation-service)
* [ASL Sign Service](#asl-sign-service)
* [Trial Service](#trial-service)
* [Redis](#redis)
* [Database and Landmark Data](#database-and-landmark-data)
* [Docker Volumes](#docker-volumes)
* [Testing](#testing)
* [Useful Docker Commands](#useful-docker-commands)
* [Development Workflow](#development-workflow)
* [Troubleshooting](#troubleshooting)
* [Production Recommendations](#production-recommendations)

---

# Overview

**EchoSign** is an AI-powered web application designed to facilitate communication between spoken/written language and **American Sign Language (ASL)**.

The platform accepts text from the user, supports multiple input languages, translates non-English text into English using AI, converts the English sentence into **ASL gloss**, and displays the corresponding signs through an interactive visualization system.

EchoSign also supports real-time ASL sign classification from a live camera feed.

The application is designed as a modular architecture where the frontend, gateway, authentication, translation, sign-recognition, and trial-management components are separated into independent Docker services.

---

# Key Features

## Multilingual Input

EchoSign supports:

* English
* French
* Arabic
* Spanish
* German
* Italian
* Portuguese
* Turkish

English input is sent directly to the ASL translation service.

Non-English input is first translated into English using Puter AI.

```text
French / Arabic / Spanish / German / ...
                    │
                    ▼
                Puter AI
                    │
                    ▼
                 English
                    │
                    ▼
             ASL Translation
```

---

## AI-Powered Translation

For non-English input, the frontend uses Puter AI to translate the original sentence into natural English.

```text
User Input
    │
    ▼
Selected Language
    │
    ▼
Puter AI
    │
    ▼
English
```

The English result is then sent to the EchoSign translation backend.

---

## English → ASL Gloss

The English sentence is converted into ASL gloss by the translation service.

```text
English Sentence
       │
       ▼
POST /translate
       │
       ▼
Translation Service
       │
       ▼
ASL Gloss
```

Example:

```text
Input:
Hello

Output:
HELLO
```

---

## Interactive ASL Visualization

The frontend receives the ASL gloss and converts it into an interactive signing sequence.

The interface supports:

* Known ASL signs
* Sequential sign playback
* Animation controls
* Playback speed
* Sign reset
* Sign navigation
* Fingerspelling for unknown words
* Letter-by-letter ASL animation

Known signs can be displayed using dedicated landmark animations.

Words that are not available in the sign dictionary can be fingerspelled.

---

## Real-Time ASL Sign Classification

EchoSign also supports the reverse direction:

```text
Camera
   │
   ▼
MediaPipe Landmarks
   │
   ▼
WebSocket
   │
   ▼
Sign Service
   │
   ▼
ML Model
   │
   ▼
Predicted Sign
```

The frontend captures camera input and extracts hand/pose landmarks.

These landmarks are streamed to the backend through WebSockets.

The sign service processes the landmarks using the trained machine-learning model and returns predictions.

---

# System Architecture

```text
                         ┌───────────────────────┐
                         │         USER          │
                         │      Web Browser      │
                         └───────────┬───────────┘
                                     │
                                     ▼
                    ┌────────────────────────────┐
                    │       ECHOSIGN FRONTEND    │
                    │      React + TypeScript     │
                    │          Vite + Nginx      │
                    │          Port 8080          │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │       API GATEWAY           │
                    │          FastAPI             │
                    │          Port 8000           │
                    └─────────────┬──────────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
      ┌─────────────┐     ┌───────────────┐    ┌─────────────┐
      │    AUTH     │     │  TRANSLATION  │    │    TRIAL    │
      │   :8001     │     │     :8003     │    │    :8004    │
      └──────┬──────┘     └───────────────┘    └──────┬──────┘
             │                                         │
             ▼                                         ▼
      ┌─────────────┐                            ┌─────────────┐
      │ PostgreSQL  │                            │    Redis    │
      │ Host System │                            │    :6379    │
      └─────────────┘                            └─────────────┘

                                  │
                                  ▼
                         ┌─────────────────┐
                         │   SIGN SERVICE  │
                         │      :8002      │
                         │   ML Inference  │
                         └─────────────────┘
```

---

# Docker Architecture

EchoSign runs using Docker Compose.

The runtime consists of the following services:

| Service     | Container              |        Port | Purpose                   |
| ----------- | ---------------------- | ----------: | ------------------------- |
| Frontend    | `echosign-frontend`    |      `8080` | React application + Nginx |
| Gateway     | `echosign-gateway`     |      `8000` | API gateway / routing     |
| Auth        | `echosign-auth`        |      `8001` | Authentication and email  |
| Sign        | `echosign-sign`        |      `8002` | ASL sign inference        |
| Translation | `echosign-translation` |      `8003` | English → ASL gloss       |
| Trial       | `echosign-trial`       |      `8004` | Guest trial management    |
| Redis       | `echosign-redis`       |      `6379` | Trial state and caching   |
| PostgreSQL  | Host machine           | `5432/5433` | Persistent database       |

PostgreSQL is currently **not containerized**.

The backend containers access PostgreSQL using:

```text
host.docker.internal
```

---

# Internal Docker Communication

Inside the Docker network, services communicate using their Docker service names.

For example:

```text
http://auth-service:8001
http://sign-service:8002
http://translation-service:8003
http://trial-service:8004
```

The gateway uses these internal addresses to forward requests.

Do not use:

```text
http://localhost:8001
```

from inside another Docker container.

Inside a container, `localhost` refers to the current container.

---

# Translation Pipeline

EchoSign uses a two-stage translation architecture.

## Stage 1 — Language Normalization

```text
English
   │
   └──────────────► Skip Puter AI

French
Arabic
Spanish
German
Italian
Portuguese
Turkish
   │
   ▼
Puter AI
   │
   ▼
English
```

---

## Stage 2 — English → ASL

```text
English
   │
   ▼
API Gateway
   │
   ▼
Translation Service
   │
   ▼
ASL Gloss
   │
   ▼
Frontend
   │
   ▼
LandmarkPlayer
   │
   ▼
ASL Visualization
```

Complete pipeline:

```text
User Input
     │
     ▼
Selected Language
     │
     ▼
Is English?
   ┌─┴─┐
  Yes  No
   │    │
   │    ▼
   │  Puter AI
   │    │
   │    ▼
   └─► English
         │
         ▼
     API Gateway
         │
         ▼
 Translation Service
         │
         ▼
      ASL Gloss
         │
         ▼
 ASL Sign Visualization
```

---

# Technology Stack

## Frontend

| Technology   | Purpose                            |
| ------------ | ---------------------------------- |
| React        | User interface                     |
| TypeScript   | Type-safe frontend                 |
| Vite         | Build/development tooling          |
| Tailwind CSS | Styling                            |
| Motion       | UI animations                      |
| Lucide       | Icons                              |
| MediaPipe    | Landmark extraction                |
| Puter AI     | Multilingual → English translation |

---

## Backend

| Technology   | Purpose             |
| ------------ | ------------------- |
| Python       | Backend language    |
| FastAPI      | REST API            |
| Uvicorn      | ASGI server         |
| Pydantic     | Validation          |
| SQLAlchemy   | Database ORM        |
| PostgreSQL   | Persistent storage  |
| Redis        | Trial tracking      |
| PyTorch      | Machine learning    |
| scikit-learn | ML preprocessing    |
| MediaPipe    | Landmark extraction |
| OpenCV       | Computer vision     |
| WebSockets   | Real-time inference |

---

## Infrastructure

| Technology     | Purpose               |
| -------------- | --------------------- |
| Docker         | Containerization      |
| Docker Compose | Service orchestration |
| Nginx          | Frontend web server   |
| PostgreSQL     | Database              |
| Redis          | Guest trial state     |

---

# Project Structure

```text
EchoSign/
│
├── backend/
│   │
│   ├── service/
│   │   │
│   │   ├── auth_service/
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   └── ...
│   │   │
│   │   ├── sign_service/
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   └── ...
│   │   │
│   │   ├── translation_service/
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   └── ...
│   │   │
│   │   └── trial_service/
│   │       ├── Dockerfile
│   │       ├── requirements.txt
│   │       └── ...
│   │
│   └── gateway/
│       ├── Dockerfile
│       ├── main.py
│       └── ...
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.ts
│   │
│   └── src/
│       ├── main.tsx
│       ├── app/
│       │   ├── App.tsx
│       │   ├── Root.tsx
│       │   ├── routes.tsx
│       │   │
│       │   ├── api/
│       │   │   └── auth.ts
│       │   │
│       │   ├── pages/
│       │   │   ├── HomePage.tsx
│       │   │   ├── AboutPage.tsx
│       │   │   ├── TranslatePage.tsx
│       │   │   ├── SignInPage.tsx
│       │   │   ├── SignUpPage.tsx
│       │   │   ├── ForgotPasswordPage.tsx
│       │   │   ├── ResetPasswordPage.tsx
│       │   │   └── VerifyEmailPage.tsx
│       │   │
│       │   └── components/
│       │       └── ui/
│       │           ├── CameraOverlay.tsx
│       │           ├── LandmarkPlayerV.tsx
│       │           ├── TopFiveList.tsx

│       │
│       ├── styles/
│       ├── types/
│       └── utils/
│
├── Models/
│   ├── conv_transformer_model.py
│   ├── conv_transformer_model_v2.py
│   ├── conv_transformer_model_v3.py
│   ├── dataset_loader.py
│   ├── Dataset_with_motion.py
│   ├── trainer2.py
│   ├── train_conv_transformer_local.py
│   ├── train_conv_transformer_localV1.py
│   ├── Train_conv_transformer_motion1.py
│   ├── Training.ipynb
│   │
│   └── checkpoints/
│
├── Preprocessing/
│   ├── preprocesssing.ipynb
│   ├── extract_landmarks.py
│   ├── create_baseline_dataset.py
│   └── signer_split_and_augment_plan.py
│
├── Data/
│   ├── raw/
│   │   ├── WLASL_v0.3.json
│   │   ├── MSASL_merged.json
│   │   ├── MSASL_synonym.json
│   │   └── metadata_wlasl_msasl_merged.jsonl
│   │
│   └── Processed/
│       ├── metadata.jsonl
│       ├── metadata_filtered.jsonl
│       ├── filtered_remapped.jsonl
│       ├── remapped_train_baseline.jsonl
│       ├── remapped_val_baseline.jsonl
│       ├── remapped_test_baseline.jsonl
│       └── split2/
│
├── models/
│   ├── ...
│   └── runtime model artifacts
│
├── preprocessing/
│   └── runtime preprocessing assets
│
├── data/
│   └── runtime data
│
├── docker-compose.yml
├── .env.example
├── .dockerignore
├── init.sql
└── README.md
```

> The exact filenames may vary depending on the current repository state. The important distinction is between the **training assets** (`Models/`, `Preprocessing/`, `Data/`) and the **runtime assets** mounted into the Docker inference service.

---

# Dataset

EchoSign's sign-recognition system uses a merged dataset based on:

* **WLASL**
* **MS-ASL**

The datasets are merged and processed before model training.

The dataset used by the project is available separately:

[EchoSign Dataset](https://drive.google.com/file/d/1c5OaKmQb4ZvHPRS_wyx-uvmwowBc-J-n/view?usp=sharing)

The processing pipeline is:

```text
WLASL
   │
   ├─────────────┐
   │             │
   ▼             ▼
Cleaning      MS-ASL
   │             │
   └──────┬──────┘
          ▼
      Merging
          │
          ▼
   Landmark Extraction
          │
          ▼
      Preprocessing
          │
          ▼
 Train / Validation / Test
          │
          ▼
    Model Training
          │
          ▼
     Sign Model
```

Large raw datasets should generally **not** be committed to Git.

The dataset should be downloaded separately and placed into the appropriate `Data/` directories.

---

# Machine Learning

The project separates machine-learning development from runtime inference.

## Models

The `Models/` directory contains:

* Model architectures
* Dataset loaders
* Training scripts
* Training notebooks
* Checkpoints
* Experimental model versions

The sign-recognition architecture uses a Conv-Transformer-based approach with motion features.

---

## Preprocessing

The `Preprocessing/` directory contains:

* Landmark extraction
* Dataset preparation
* Filtering
* Splitting
* Augmentation planning

The preprocessing pipeline converts raw dataset information into model-ready features.

---

## Runtime Model

The sign service requires the trained runtime model and its supporting preprocessing artifacts.

A typical Docker Compose configuration mounts:

```yaml
volumes:
  - ./models:/app/models
  - ./preprocessing:/app/preprocessing
  - ./data:/app/data
```

This makes the runtime assets available inside the sign-service container.

The exact mount paths must match the paths expected by the sign-service inference code.

---

# Requirements

Before running EchoSign, install:

* Git
* Docker Desktop
* Docker Compose
* PostgreSQL
* A modern browser

Verify Docker:

```bash
docker --version
docker compose version
```

Verify Git:

```bash
git --version
```

Docker Desktop must be running.

---

# Clone the Repository

Clone the repository:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

Enter the project:

```bash
cd EchoSign
```

---

# Environment Configuration

Create the environment file.

## Windows PowerShell

```powershell
Copy-Item .env.example .env
```

## Linux / macOS

```bash
cp .env.example .env
```

Then edit `.env`.

Example:

```env
# ============================================================
# AUTHENTICATION
# ============================================================

SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

FRONTEND_URL=http://localhost:8080


# ============================================================
# POSTGRESQL
# ============================================================

POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=echosign_db

POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5433


# ============================================================
# SMTP
# ============================================================

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM=your_email@gmail.com


# ============================================================
# HUGGING FACE
# ============================================================

HF_TOKEN=your_huggingface_token
```

Never commit the real `.env` file to Git.

---

# Environment Variables

| Variable                      | Purpose                     |
| ----------------------------- | --------------------------- |
| `SECRET_KEY`                  | JWT signing key             |
| `ALGORITHM`                   | JWT algorithm               |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration              |
| `FRONTEND_URL`                | Frontend URL                |
| `POSTGRES_USER`               | PostgreSQL username         |
| `POSTGRES_PASSWORD`           | PostgreSQL password         |
| `POSTGRES_DB`                 | Database name               |
| `POSTGRES_HOST`               | PostgreSQL hostname         |
| `POSTGRES_PORT`               | PostgreSQL port             |
| `SMTP_HOST`                   | SMTP server                 |
| `SMTP_PORT`                   | SMTP port                   |
| `SMTP_USERNAME`               | SMTP account                |
| `SMTP_PASSWORD`               | SMTP password/app password  |
| `SMTP_FROM`                   | Sender email                |
| `HF_TOKEN`                    | Hugging Face authentication |

---

# PostgreSQL Configuration

The current EchoSign architecture uses PostgreSQL **outside Docker**.

Docker services connect to the PostgreSQL instance installed on the host machine.

The connection is:

```text
Docker Container
      │
      ▼
host.docker.internal
      │
      ▼
PostgreSQL
```

---

## Create the Database

Create:

```sql
CREATE DATABASE echosign_db;
```

Use a dedicated PostgreSQL user for EchoSign.

Example:

```sql
CREATE USER echosign_user WITH PASSWORD 'strong-password';

GRANT ALL PRIVILEGES ON DATABASE echosign_db TO echosign_user;
```

For newer PostgreSQL versions, additional schema privileges may be required:

```sql
GRANT ALL ON SCHEMA public TO echosign_user;
```

---

# PostgreSQL Port

The default PostgreSQL port is:

```text
5432
```

If PostgreSQL is configured to use `5433`, use:

```env
POSTGRES_PORT=5433
```

The port in `.env` must match the actual PostgreSQL server.

Check your PostgreSQL configuration if necessary.

---

# Database Initialization

If the repository contains `init.sql`, run it against the database.

Example:

```bash
psql \
  -h localhost \
  -p 5433 \
  -U echosign_user \
  -d echosign_db \
  -f init.sql
```

On Windows PowerShell:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
  -h localhost `
  -p 5433 `
  -U echosign_user `
  -d echosign_db `
  -f init.sql
```

Adjust the PostgreSQL installation path and port when necessary.

---

# Docker Setup

Build the Docker images:

```bash
docker compose build
```

Or build and start everything together:

```bash
docker compose up -d --build
```

> The correct Docker option is `--build`, not `-build`.

Incorrect:

```bash
docker compose up -d -build
```

Correct:

```bash
docker compose up -d --build
```

---

# Starting EchoSign

Start the complete application:

```bash
docker compose up -d
```

Or:

```bash
docker compose up -d --build
```

Check the services:

```bash
docker compose ps
```

---

# Expected Services

A typical deployment contains:

```text
echosign-frontend
echosign-gateway
echosign-auth
echosign-sign
echosign-translation
echosign-trial
echosign-redis
```

PostgreSQL runs separately on the host machine.

---

# Checking Containers

Show running containers:

```bash
docker compose ps
```

Show all Docker containers:

```bash
docker ps -a
```

---

# Docker Logs

Show all logs:

```bash
docker compose logs
```

Follow all logs:

```bash
docker compose logs -f
```

Frontend:

```bash
docker compose logs frontend --tail=50
```

Gateway:

```bash
docker compose logs gateway --tail=50
```

Authentication:

```bash
docker compose logs auth-service --tail=50
```

Sign service:

```bash
docker compose logs sign-service --tail=50
```

Translation:

```bash
docker compose logs translation-service --tail=50
```

Trial:

```bash
docker compose logs trial-service --tail=50
```

Redis:

```bash
docker compose logs redis --tail=50
```

---

# Accessing the Application

Once all containers are running:

## Frontend

```text
http://localhost:8080
```

## API Gateway

```text
http://localhost:8000
```

## Swagger

```text
http://localhost:8000/docs
```

## ReDoc

```text
http://localhost:8000/redoc
```

Internal service ports should generally not be accessed directly from the browser.

---

# API Gateway

The API gateway acts as the main entry point for backend requests.

The frontend communicates primarily with:

```text
http://localhost:8000
```

The gateway forwards requests internally.

Example:

```text
Frontend
   │
   ▼
Gateway :8000
   │
   ├── /auth/*       → auth-service:8001
   ├── /sign/*       → sign-service:8002
   ├── /translate/*  → translation-service:8003
   └── /trial/*      → trial-service:8004
```

The gateway also handles HTTP request forwarding and preserves authentication-related headers/cookies when required.

---

# Authentication

The authentication service provides:

* Registration
* Login
* JWT authentication
* Email verification
* Verification expiration
* Forgot password
* Password reset
* Password hashing
* Reset-token expiration

---

## Registration Flow

```text
User
 │
 ▼
Frontend
 │
 ▼
Gateway
 │
 ▼
Auth Service
 │
 ├── PostgreSQL
 │
 └── SMTP
       │
       ▼
Verification Email
```

---

## Email Verification

After registration:

```text
Registration
     │
     ▼
Create User
     │
     ▼
Generate Verification Token
     │
     ▼
Send Email
     │
     ▼
User Clicks Link
     │
     ▼
Verify Account
```

---

## Forgot Password

The password-reset process is:

```text
Forgot Password
      │
      ▼
Auth Service
      │
      ▼
Generate Reset Token
      │
      ▼
Store Hashed Token
      │
      ▼
Send Reset Email
      │
      ▼
User Opens Link
      │
      ▼
Reset Password
      │
      ▼
Update PostgreSQL
```

SMTP credentials are required for email verification and password-reset functionality.

For Gmail, use a **Google App Password** rather than the normal Gmail account password.

---

# Translation Service

The translation service handles:

```text
English → ASL Gloss
```

The main endpoint is:

```http
POST /translate
```

Example:

```json
{
  "text": "Hello"
}
```

Response:

```json
{
  "gloss": "HELLO"
}
```

---

# Translation Service Architecture

```text
Frontend
   │
   ▼
Gateway
   │
   ▼
Translation Service
   │
   ▼
ASL Gloss Model
   │
   ▼
ASL Gloss
```

---

# Sign Service

The sign service handles machine-learning inference for live sign recognition.

```text
Camera
   │
   ▼
Frontend
   │
   ▼
MediaPipe
   │
   ▼
Landmarks
   │
   ▼
WebSocket
   │
   ▼
Sign Service
   │
   ▼
ML Model
   │
   ▼
Predictions
```

The sign service runs on:

```text
8002
```

The service uses the model and preprocessing assets required for inference.

---

# Sign Service Docker Image

The sign service uses a Python Docker image.

A typical Dockerfile contains:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/service/sign_service/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/service/sign_service /app/sign_service

WORKDIR /app/sign_service

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

The Dockerfile itself does **not** copy the project's `Models/`, `Preprocessing/`, and `Data/` directories unless explicitly configured to do so.

Instead, Docker Compose can mount them:

```yaml
volumes:
  - ./models:/app/models
  - ./preprocessing:/app/preprocessing
  - ./data:/app/data
```

This distinction is important:

```text
Dockerfile
   │
   ├── Installs dependencies
   ├── Copies sign-service source
   └── Starts FastAPI

Docker Compose volumes
   │
   ├── models
   ├── preprocessing
   └── data
```

Therefore, the ML assets must exist at the expected host paths before starting the sign service.

---

# Trial Service

EchoSign provides a guest trial system.

The trial service manages a limited number of guest requests.

The current system provides:

```text
5 free guest trials
```

The trial service uses Redis to store trial state.

---

## Trial Flow

```text
Guest
  │
  ▼
Frontend
  │
  ▼
Gateway
  │
  ▼
Trial Service
  │
  ▼
Redis
```

The guest trial identifier is persisted using the EchoSign trial cookie.

The gateway must preserve the relevant cookie headers so the browser can continue using the same trial identity.

---

# Redis

Redis is used by the trial service.

The Redis service is available internally as:

```text
redis:6379
```

The Redis container:

```text
echosign-redis
```

should not normally need to be exposed publicly.

Its primary responsibility is temporary trial-state storage.

---

# Database and Landmark Data

PostgreSQL stores persistent application data.

Depending on the current schema, this can include:

* Users
* Authentication information
* Landmark data
* Application metadata

Landmark data can be imported using the backend import script.

Example:

```bash
docker compose exec <backend-service> python -m backend.import_landmarks
```

Replace `<backend-service>` with the actual service containing the import script.

---

# Docker Volumes

The sign and translation services may require access to runtime ML assets.

Typical mounts:

```yaml
volumes:
  - ./models:/app/models
  - ./preprocessing:/app/preprocessing
  - ./data:/app/data
```

Host:

```text
EchoSign/
├── models/
├── preprocessing/
└── data/
```

Container:

```text
/app/
├── models/
├── preprocessing/
└── data/
```

This allows the runtime services to access model and preprocessing assets without embedding large files directly into Docker images.

---

# Testing the Translation API

From Windows PowerShell:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/translate" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"text":"Hello"}'
```

Expected response:

```json
{
  "gloss": "HELLO"
}
```

---

# Testing the Trial API

Check trial status from inside the Docker network:

```bash
docker compose exec frontend wget -S -O- \
  http://echosign-gateway:8000/trial/status
```

Consume a trial:

```bash
docker compose exec frontend wget -S -O- \
  --post-data="" \
  http://echosign-gateway:8000/trial/consume
```

BusyBox `wget` does not support every GNU `wget` option.

For example, options such as:

```text
--save-cookies
--keep-session-cookies
```

may not be available in the minimal BusyBox image.

---

# Rebuilding Services

After changing a service:

```bash
docker compose build <service>
```

Then:

```bash
docker compose up -d <service>
```

For example:

```bash
docker compose build translation-service
docker compose up -d translation-service
```

Frontend:

```bash
docker compose build frontend
docker compose up -d frontend
```

Sign service:

```bash
docker compose build sign-service
docker compose up -d sign-service
```

---

# Complete Rebuild

To completely rebuild all services:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

Or:

```bash
docker compose down
docker compose up -d --build
```

Use `--no-cache` only when a clean image rebuild is actually required because it can significantly increase build time.

---

# Stopping EchoSign

Stop the services:

```bash
docker compose stop
```

Remove the containers:

```bash
docker compose down
```

Remove orphan containers as well:

```bash
docker compose down --remove-orphans
```

> `docker compose down` does not delete a PostgreSQL database installed directly on the host machine.

---

# Useful Docker Commands

## Show containers

```bash
docker compose ps
```

## Show logs

```bash
docker compose logs
```

## Follow logs

```bash
docker compose logs -f
```

## Service logs

```bash
docker compose logs sign-service --tail=100
```

## Enter a container

```bash
docker compose exec sign-service sh
```

## Inspect model files

```bash
docker compose exec sign-service sh
```

Then:

```bash
ls -la /app/models
ls -la /app/preprocessing
ls -la /app/data
```

## Restart a service

```bash
docker compose restart sign-service
```

## Rebuild everything

```bash
docker compose up -d --build
```

---

# Development Workflow

The recommended workflow is:

```text
Clone Repository
       │
       ▼
Configure .env
       │
       ▼
Install / Configure PostgreSQL
       │
       ▼
Create echosign_db
       │
       ▼
Initialize Database
       │
       ▼
Download Required Dataset / ML Assets
       │
       ▼
docker compose up -d --build
       │
       ▼
docker compose ps
       │
       ▼
Check Logs
       │
       ▼
Open Frontend
       │
       ▼
Test Authentication
       │
       ▼
Test Translation
       │
       ▼
Test Sign Recognition
```

---

# Complete First-Time Setup

For a new developer:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd EchoSign
```

Create `.env`.

Windows:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Configure:

```text
.env
PostgreSQL
SMTP
Hugging Face
```

Create PostgreSQL database:

```sql
CREATE DATABASE echosign_db;
```

Initialize the schema:

```bash
psql -h localhost -p 5433 -U echosign_user -d echosign_db -f init.sql
```

Start Docker:

```bash
docker compose up -d --build
```

Check:

```bash
docker compose ps
```

Check logs:

```bash
docker compose logs --tail=50
```

Then open:

```text
http://localhost:8080
```

---

# Troubleshooting

## Docker does not start

Verify Docker Desktop:

```bash
docker info
```

Then:

```bash
docker compose up -d --build
```

---

## `-build` error

Incorrect:

```bash
docker compose up -d -build
```

Correct:

```bash
docker compose up -d --build
```

---

## PostgreSQL connection error

Check `.env`:

```env
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5433
POSTGRES_USER=echosign_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=echosign_db
```

Verify that PostgreSQL is running on the host.

---

## Translation service unavailable

Check:

```bash
docker compose ps
```

Then:

```bash
docker compose logs translation-service --tail=100
```

---

## Sign service cannot find models

Enter the container:

```bash
docker compose exec sign-service sh
```

Check:

```bash
ls -la /app/models
ls -la /app/preprocessing
ls -la /app/data
```

If the directories are empty, check the Docker Compose volume configuration.

---

## Frontend cannot communicate with backend

Check:

```text
Frontend
   │
   ▼
localhost:8000
   │
   ▼
Gateway
```

Verify that the gateway is running:

```bash
docker compose ps
```

Check gateway logs:

```bash
docker compose logs gateway --tail=100
```

Also verify the frontend's API configuration.

---

## Email verification does not work

Check the authentication service:

```bash
docker compose logs auth-service --tail=100
```

Verify:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=your_email@gmail.com
```

For Gmail, use an **App Password**, not the normal Gmail password.

---

## Trial system does not persist

Check Redis:

```bash
docker compose ps redis
```

Then:

```bash
docker compose logs redis --tail=50
```

Check the trial service:

```bash
docker compose logs trial-service --tail=100
```

Also verify that the gateway forwards `Set-Cookie` and `Cookie` headers correctly.

---

# Security Recommendations

For development:

* Never commit `.env`.
* Never commit SMTP passwords.
* Never commit JWT secrets.
* Never expose PostgreSQL publicly.
* Use a dedicated PostgreSQL role.
* Use strong passwords.
* Use HTTPS in production.
* Rotate JWT secrets when necessary.
* Use secure cookies in production.
* Configure appropriate CORS origins.

For production:

```text
Browser
   │
 HTTPS
   ▼
Reverse Proxy
   │
   ▼
Gateway
   │
   ├── Auth
   ├── Translation
   ├── Sign
   └── Trial
          │
          ├── Redis
          └── PostgreSQL
```

---

# Production Recommendations

For production deployment:

### PostgreSQL

Use a dedicated or managed PostgreSQL instance.

Recommended:

* Automated backups
* Point-in-time recovery
* Restricted network access
* Strong credentials
* Connection pooling
* Monitoring
* Database migrations

### Redis

Use persistent or managed Redis if trial state must survive infrastructure failures.

### Docker

Use:

* Separate production environment variables
* Smaller runtime images
* Health checks
* Resource limits
* Restart policies
* Centralized logging

### Security

Use:

* HTTPS
* Secure cookies
* `HttpOnly`
* `SameSite`
* Production CORS configuration
* Strong JWT secrets
* Rate limiting
* SMTP authentication
* Database access restrictions

---

# Architecture Summary

EchoSign is composed of several independent services:

```text
┌─────────────────────────────────────────────┐
│                  FRONTEND                   │
│             React + TypeScript              │
│                  Nginx                      │
│                 :8080                       │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│                 API GATEWAY                 │
│                  FastAPI                    │
│                   :8000                     │
└───────────────┬───────────────┬─────────────┘
                │               │
        ┌───────┼───────┬───────┘
        │       │       │
        ▼       ▼       ▼
      AUTH   SIGN   TRANSLATION
      :8001  :8002     :8003
        │       │         │
        │       │         │
        ▼       │         ▼
   PostgreSQL   │      ASL Gloss
                │
                ▼
          ML Inference

                │
                ▼
              TRIAL
               :8004
                │
                ▼
              Redis
```

Machine-learning resources:

```text
Models/
     │
     ▼
Preprocessing/
     │
     ▼
Data/
     │
     ▼
Sign Service
```

Authentication:

```text
Frontend
   │
   ▼
Gateway
   │
   ▼
Auth Service
   │
   ├── PostgreSQL
   │
   └── SMTP
```

Translation:

```text
Frontend
   │
   ▼
Puter AI
   │
   ▼
English
   │
   ▼
Gateway
   │
   ▼
Translation Service
   │
   ▼
ASL Gloss
```

Trial:

```text
Frontend
   │
   ▼
Gateway
   │
   ▼
Trial Service
   │
   ▼
Redis
```

---

# Quick Start

For developers who already have PostgreSQL and the required environment configured:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd EchoSign
```

Create/configure `.env`.

Then:

```bash
docker compose up -d --build
```

Check:

```bash
docker compose ps
```

Check logs:

```bash
docker compose logs --tail=50
```

Open:

```text
http://localhost:8080
```

API:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

---

# EchoSign

**AI-powered multilingual text-to-ASL translation and real-time sign recognition platform.**
