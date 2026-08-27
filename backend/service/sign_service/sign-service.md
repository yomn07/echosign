# EchoSign Sign Service

## 1. Purpose

The Sign Service is responsible for sign-related machine-learning processing.

It is isolated from authentication and trial management.

---

## 2. Docker

Internal service:

```text
sign-service:8002
```

---

## 3. Mounted Resources

The container receives:

```text
./models:/app/models
./preprocessing:/app/preprocessing
./data:/app/data
```

---

# 4. Architecture

```text
Frontend
   ↓
API Gateway
   ↓
Sign Service
   │
   ├── Models
   ├── Preprocessing
   └── Data
```

---

# 5. Model Loading

Models should be loaded from:

```text
/app/models
```

rather than requiring model files to be hard-coded into application source code.

---

# 6. Preprocessing

Input data can be transformed through:

```text
/app/preprocessing
```

before inference.

---

# 7. Data

Runtime datasets and supporting resources can be stored under:

```text
/app/data
```

---
