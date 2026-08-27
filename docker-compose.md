# EchoSign Docker Compose Architecture

## 1. Overview

EchoSign uses Docker Compose to run the application as multiple containers.

Current architecture:

```text
frontend
gateway
auth-service
sign-service
translation-service
trial-service
redis
```

---

# 2. Service Table

| Service             | Internal Port | Function       |
| ------------------- | ------------: | -------------- |
| frontend            |            80 | React + Nginx  |
| gateway             |          8000 | API Gateway    |
| auth-service        |          8001 | Authentication |
| sign-service        |          8002 | Sign/ML        |
| translation-service |          8003 | Translation    |
| trial-service       |          8004 | Trial system   |
| redis               |          6379 | State storage  |

---

# 3. Frontend

The frontend exposes:

```yaml
ports:
  - "8080:80"
```

Therefore:

```text
http://localhost:8080
```

is the browser entry point.

---

# 4. Auth Service

```yaml
auth-service:
  build:
    context: ./backend/service/auth_service
    dockerfile: Dockerfile
```

Internal:

```text
auth-service:8001
```

---

# 5. Sign Service

```yaml
sign-service:
  build:
    context: ./backend/service/sign_service
    dockerfile: Dockerfile
```

Internal:

```text
sign-service:8002
```

Mounted:

```text
./models:/app/models
./preprocessing:/app/preprocessing
./data:/app/data
```

---

# 6. Translation Service

```yaml
translation-service:
  build:
    context: ./backend/service/translation_service
    dockerfile: Dockerfile
```

Internal:

```text
translation-service:8003
```

Mounted:

```text
./models:/app/models
./preprocessing:/app/preprocessing
./data:/app/data
```

---

# 7. Trial Service

```yaml
trial-service:
  build:
    context: ./backend/service/trial_service
    dockerfile: Dockerfile
```

Internal:

```text
trial-service:8004
```

It depends on:

```text
auth-service
redis
```

---

# 8. Redis

```yaml
redis:
  image: redis:7-alpine
```

Internal:

```text
redis:6379
```

Redis stores anonymous trial counters and can also support other temporary application state.

---

# 9. Environment Variables

Services use:

```text
.env
```

Typical variables include:

```text
REDIS_HOST=redis
REDIS_PORT=6379
```

Important:

Inside Docker, the Redis hostname is:

```text
redis
```

not:

```text
localhost
```

because `localhost` inside a container refers to that same container.

---

# 10. Docker Startup

Build and start everything:

```powershell
docker compose up -d --build
```

Check containers:

```powershell
docker compose ps
```

---

# 11. Logs

Frontend:

```powershell
docker compose logs frontend --tail=50
```

Gateway:

```powershell
docker compose logs gateway --tail=100
```

Trial:

```powershell
docker compose logs trial-service --tail=100
```

Translation:

```powershell
docker compose logs translation-service --tail=100
```

---

# 12. Frontend Health

Normal Nginx startup includes:

```text
Configuration complete; ready for start up
```

and:

```text
start worker processes
```

The message:

```text
default.conf differs from the packaged version
```

is expected when the project supplies a custom Nginx configuration.

---

# 13. Docker Network

Containers communicate using service names.

Example:

```text
gateway → trial-service:8004
gateway → translation-service:8003
gateway → auth-service:8001
gateway → sign-service:8002
trial-service → redis:6379
```

---

# 14. Browser vs Docker Networking

The browser sees:

```text
localhost:8080
```

Docker containers see:

```text
frontend
gateway
auth-service
sign-service
translation-service
trial-service
redis
```

Therefore frontend browser code should use:

```text
/api/...
```

and not:

```text
http://translation-service:8003
```

or:

```text
http://127.0.0.1:8000
```

---

# 15. Full Request Example

Translation:

```text
Browser
   │
   │ POST /api/translate
   ▼
Nginx :8080
   │
   ▼
Gateway :8000
   │
   ▼
Translation Service :8003
   │
   ▼
ASL Gloss
   │
   ▼
Gateway
   │
   ▼
Nginx
   │
   ▼
Browser
```

---

# 16. Trial Example

```text
Browser
 │
 │ POST /api/trial/consume
 │ Cookie: echosign_trial_id
 ▼
Nginx
 │
 ▼
Gateway
 │
 ▼
Trial Service
 │
 ▼
Redis
 │
 │ DECR
 ▼
4 trials remaining
 │
 ▼
Browser
```

---

# 17. Authentication Example

```text
Browser
 │
 │ POST /api/auth/login
 ▼
Nginx
 │
 ▼
Gateway
 │
 ▼
Auth Service
 │
 ▼
Authentication
 │
 ▼
Browser
```

---

# 18. Final Architecture

```text
                           INTERNET
                              │
                              ▼
                    ┌───────────────────┐
                    │   Browser / User  │
                    └─────────┬─────────┘
                              │
                         HTTP :8080
                              │
                              ▼
                    ┌───────────────────┐
                    │ Frontend / Nginx  │
                    │ React Application  │
                    └─────────┬─────────┘
                              │
                            /api
                              │
                              ▼
                    ┌───────────────────┐
                    │   API Gateway     │
                    │       :8000       │
                    └────┬───┬───┬─────┘
                         │   │   │
              ┌──────────┘   │   └──────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌──────────────┐
       │Auth :8001  │ │Sign :8002  │ │Translation   │
       │            │ │            │ │   :8003      │
       └────────────┘ └────────────┘ └──────────────┘

                         │
                         ▼
                  ┌──────────────┐
                  │Trial :8004   │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Redis :6379  │
                  └──────────────┘
```

This architecture keeps the **frontend, authentication, trial management, translation, ML processing, gateway, and infrastructure concerns separated**, while Docker Compose provides the networking and deployment layer.
