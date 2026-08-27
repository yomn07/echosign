# EchoSign Translation Service

## 1. Purpose

The Translation Service converts English natural language into ASL Gloss.

It is separate from the frontend and from authentication.

---

## 2. Docker

Internal address:

```text
translation-service:8003
```

---

## 3. API

Main endpoint:

```text
POST /translate
```

Expected request:

```json
{
  "text": "Hello, how are you?"
}
```

Expected response:

```json
{
  "gloss": "HELLO HOW YOU"
}
```

---

# 4. Complete Translation Pipeline

```text
User
 │
 ▼
React Translate Page
 │
 ├── English
 │      ↓
 │   Translation Service
 │
 └── Other language
        ↓
      Puter AI
        ↓
      English
        ↓
 Translation Service
        ↓
     ASL Gloss
```

---

# 5. Frontend Integration

The frontend should call:

```ts
fetch("/api/translate", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    text: englishText,
  }),
});
```

The request goes through:

```text
Browser
 ↓
Nginx
 ↓
Gateway
 ↓
translation-service:8003
```

---

# 6. Models

The service can load model assets from:

```text
/app/models
```

The Docker Compose volume maps:

```text
./models:/app/models
```

---

# 7. Preprocessing

Preprocessing resources are mounted:

```text
./preprocessing:/app/preprocessing
```

This allows preprocessing logic/assets to be managed separately from the container image.

---

# 8. Data

Additional data is mounted:

```text
./data:/app/data
```

---

# 9. Separation of Responsibilities

The Translation Service produces:

```text
ASL Gloss
```

It does not need to manage:

* User accounts.
* Passwords.
* Trial state.
* Browser cookies.

Those concerns belong to other services.

---

# 10. Example

Input:

```text
I want to go home tomorrow.
```

Possible gloss:

```text
TOMORROW HOME I GO
```

The frontend then visualizes the gloss.
